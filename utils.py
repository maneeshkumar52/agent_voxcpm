"""Utility helpers for configuration, logging, and local persistence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml


@dataclass
class Message:
    """A message exchanged between agents during orchestration."""

    sender: str
    recipient: str
    content: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "metadata": self.metadata,
        }


def load_config(config_path: str | Path) -> Dict[str, Any]:
    """Load YAML configuration as a dictionary."""

    with Path(config_path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def ensure_directories(paths: Iterable[str | Path]) -> None:
    """Create directories if they do not already exist."""

    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def utc_timestamp() -> str:
    """Return UTC timestamp in ISO-like format without punctuation unsafe for filenames."""

    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def slugify(value: str, max_len: int = 60) -> str:
    """Convert arbitrary text into a filesystem-safe slug."""

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value).strip("-")
    if not value:
        value = "task"
    return value[:max_len]


def save_markdown_output(content: str, output_dir: str | Path, base_name: str) -> Path:
    """Persist markdown content in the output directory and return the saved path."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"{slugify(base_name)}-{utc_timestamp()}.md"
    destination = output_path / filename
    destination.write_text(content, encoding="utf-8")
    return destination


def append_jsonl_log(log_path: str | Path, messages: List[Message], extra: Dict[str, Any] | None = None) -> None:
    """Append a single run record to JSONL logs."""

    record: Dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "messages": [message.to_dict() for message in messages],
    }
    if extra:
        record.update(extra)

    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=True) + "\n")
