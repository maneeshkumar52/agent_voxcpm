"""Summarizer agent implementation."""

from __future__ import annotations

from typing import Any, Dict

from ollama_client import OllamaClient


class SummarizerAgent:
    """Condense research notes for planning and publishing."""

    def __init__(self, config: Dict[str, Any], ollama: OllamaClient) -> None:
        self.name = "Summarizer"
        self.config = config
        self.ollama = ollama

    def run(self, task: str, research_notes: str) -> Dict[str, Any]:
        prompt = (
            "You are a summarization specialist. Compress research into high-signal points without losing meaning.\n\n"
            f"Task:\n{task}\n\n"
            f"Research Notes:\n{research_notes}\n\n"
            "Output format:\n"
            "1) Executive Summary (max 140 words)\n"
            "2) Bullet Highlights (6-10 bullets)\n"
            "3) Risks or Uncertainties\n"
        )

        summary = self.ollama.generate(
            model=self.config["model"],
            prompt=prompt,
            system_prompt=self.config.get("system_prompt", ""),
            temperature=float(self.config.get("temperature", 0.2)),
        )

        return {
            "agent": self.name,
            "summary": summary,
        }
