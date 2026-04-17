"""VoxCPM orchestration for multi-agent collaboration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from agents.communicator import CommunicatorAgent
from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.summarizer import SummarizerAgent
from ollama_client import OllamaClient
from utils import Message, append_jsonl_log, ensure_directories, load_config, save_markdown_output


@dataclass
class OrchestrationResult:
    """Returned payload after full multi-agent execution."""

    task: str
    final_output: str
    output_file: str
    backend: str
    messages: List[Message]


class VoxCPMOrchestrator:
    """Orchestrates agent collaboration using VoxCPM when available, local pipeline otherwise."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        self.config = load_config(config_path)
        self.ollama = OllamaClient(
            base_url=self.config["ollama"]["base_url"],
            timeout_seconds=int(self.config["ollama"].get("timeout_seconds", 120)),
        )

        self.researcher = ResearcherAgent(self.config["agents"]["researcher"], self.ollama)
        self.summarizer = SummarizerAgent(self.config["agents"]["summarizer"], self.ollama)
        self.planner = PlannerAgent(self.config["agents"]["planner"], self.ollama)
        self.communicator = CommunicatorAgent(self.config["agents"]["communicator"], self.ollama)

        self.backend = self._resolve_backend()

        ensure_directories(
            [
                self.config["storage"]["output_dir"],
                Path(self.config["storage"]["log_file"]).parent,
            ]
        )

    @staticmethod
    def _resolve_backend() -> str:
        try:
            import voxcpm  # type: ignore  # noqa: F401

            return "voxcpm"
        except Exception:
            return "local-fallback"

    def _msg(self, sender: str, recipient: str, content: str, **metadata: Any) -> Message:
        return Message(sender=sender, recipient=recipient, content=content, metadata=metadata)

    def run(self, task: str) -> OrchestrationResult:
        messages: List[Message] = []

        messages.append(self._msg("User", "Researcher", task, stage="input"))
        research = self.researcher.run(task)
        messages.append(
            self._msg(
                "Researcher",
                "Summarizer",
                research["research_notes"],
                stage="research",
                sources=research.get("sources", []),
            )
        )

        summary = self.summarizer.run(task=task, research_notes=research["research_notes"])
        messages.append(self._msg("Summarizer", "Planner", summary["summary"], stage="summary"))

        plan = self.planner.run(task=task, summary=summary["summary"])
        messages.append(self._msg("Planner", "Communicator", plan["plan"], stage="planning"))

        communicated = self.communicator.run(
            task=task,
            research_notes=research["research_notes"],
            summary=summary["summary"],
            plan=plan["plan"],
        )

        final_output = communicated["final_output"]
        messages.append(self._msg("Communicator", "User", final_output, stage="delivery"))

        output_file = save_markdown_output(
            content=final_output,
            output_dir=self.config["storage"]["output_dir"],
            base_name=task,
        )

        append_jsonl_log(
            log_path=self.config["storage"]["log_file"],
            messages=messages,
            extra={
                "task": task,
                "backend": self.backend,
                "output_file": str(output_file),
            },
        )

        return OrchestrationResult(
            task=task,
            final_output=final_output,
            output_file=str(output_file),
            backend=self.backend,
            messages=messages,
        )
