"""End-to-end validator for orchestrator and optional speech features."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smoke_test import run_workspace_smoke_test


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
    summary = run_workspace_smoke_test(
        config_path="config.yaml",
        task=args.task,
        speech_text=args.speech_text,
        language=args.language,
        snapshot_path=args.snapshot,
    )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
