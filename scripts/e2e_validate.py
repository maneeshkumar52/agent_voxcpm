"""End-to-end validator for orchestrator and optional speech features."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator import VoxCPMOrchestrator
from speech import SpeechServiceError, VoxSpeechService
from utils import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate multi-agent and speech features.")
    parser.add_argument(
        "--task",
        default="Create a concise wiki page on renewable energy in 5 sections.",
        help="Task for the multi-agent orchestrator.",
    )
    parser.add_argument(
        "--speech-text",
        default="Hello. This is a multilingual speech validation run.",
        help="Input text for TTS validation.",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="Language hint for speech operations (auto, en, zh, etc.).",
    )
    parser.add_argument(
        "--snapshot",
        default="docs/snapshots/08_e2e_speech_validation.json",
        help="Path to write validation summary JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_config("config.yaml")

    summary: dict[str, object] = {
        "task": args.task,
        "language": args.language,
    }

    orchestrator = VoxCPMOrchestrator("config.yaml")
    result = orchestrator.run(args.task)
    summary["orchestrator"] = {
        "backend": result.backend,
        "messages": len(result.messages),
        "output_file": result.output_file,
    }

    speech = VoxSpeechService(cfg)
    dep = speech.dependency_status()
    summary["speech_dependency_status"] = {
        "voxcpm": dep.voxcpm_available,
        "funasr": dep.funasr_available,
        "soundfile": dep.soundfile_available,
        "tts_ready": dep.ready_for_tts,
        "stt_ready": dep.ready_for_stt,
    }

    if dep.ready_for_tts:
        try:
            tts = speech.synthesize(text=args.speech_text, language=args.language)
            summary["speech_tts"] = {"status": "ok", **tts}

            if dep.ready_for_stt:
                stt = speech.transcribe(tts["audio_path"], language=args.language)
                summary["speech_stt"] = {
                    "status": "ok",
                    "transcript": stt.get("transcript", ""),
                    "model": stt.get("model", ""),
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

    snapshot_path = Path(args.snapshot)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
