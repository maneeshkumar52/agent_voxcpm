"""Shared smoke-test runner for UI and CLI validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from orchestrator import VoxCPMOrchestrator
from speech import DependencyStatus, SpeechServiceError, VoxSpeechService
from utils import load_config


def run_workspace_smoke_test(
    *,
    config_path: str = "config.yaml",
    task: str,
    speech_text: str,
    language: str = "auto",
    snapshot_path: str = "docs/snapshots/09_ui_smoke_test.json",
) -> Dict[str, Any]:
    """Run a full workspace smoke test and persist summary JSON."""

    config = load_config(config_path)
    orchestrator = VoxCPMOrchestrator(config_path)
    speech_service = VoxSpeechService(config)
    dependency_status: DependencyStatus = speech_service.dependency_status()

    result = orchestrator.run(task)
    summary: Dict[str, Any] = {
        "task": task,
        "language": language,
        "orchestrator": {
            "backend": result.backend,
            "messages": len(result.messages),
            "output_file": result.output_file,
        },
        "speech_dependency_status": {
            "voxcpm": dependency_status.voxcpm_available,
            "funasr": dependency_status.funasr_available,
            "soundfile": dependency_status.soundfile_available,
            "tts_ready": dependency_status.ready_for_tts,
            "stt_ready": dependency_status.ready_for_stt,
        },
    }

    if dependency_status.ready_for_tts:
        try:
            tts_result = speech_service.synthesize(text=speech_text, language=language)
            summary["speech_tts"] = {"status": "ok", **tts_result}

            if dependency_status.ready_for_stt:
                stt_result = speech_service.transcribe(tts_result["audio_path"], language=language)
                summary["speech_stt"] = {
                    "status": "ok",
                    "transcript": stt_result.get("transcript", ""),
                    "model": stt_result.get("model", ""),
                }
            else:
                summary["speech_stt"] = {
                    "status": "skipped",
                    "reason": "funasr dependency not available",
                }
        except SpeechServiceError as exc:
            summary["speech_tts"] = {"status": "error", "error": str(exc)}
    else:
        summary["speech_tts"] = {
            "status": "skipped",
            "reason": "voxcpm/soundfile dependency not available",
        }

    snapshot = Path(snapshot_path)
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
