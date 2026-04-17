"""Communicator agent implementation."""

from __future__ import annotations

from typing import Any, Dict

from ollama_client import OllamaClient


class CommunicatorAgent:
    """Compose final user-facing output from all prior artifacts."""

    def __init__(self, config: Dict[str, Any], ollama: OllamaClient) -> None:
        self.name = "Communicator"
        self.config = config
        self.ollama = ollama

    def run(self, task: str, research_notes: str, summary: str, plan: str) -> Dict[str, Any]:
        prompt = (
            "You are a communication specialist writing a polished wiki page.\n"
            "Use the plan and summary as source-of-truth, and weave in useful details from research notes.\n\n"
            f"Task:\n{task}\n\n"
            f"Research Notes:\n{research_notes}\n\n"
            f"Summary:\n{summary}\n\n"
            f"Plan:\n{plan}\n\n"
            "Write final output in markdown with: title, short intro, clear sections, and a concise conclusion."
        )

        final_markdown = self.ollama.generate(
            model=self.config["model"],
            prompt=prompt,
            system_prompt=self.config.get("system_prompt", ""),
            temperature=float(self.config.get("temperature", 0.15)),
        )

        return {
            "agent": self.name,
            "final_output": final_markdown,
        }
