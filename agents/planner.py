"""Planner agent implementation."""

from __future__ import annotations

from typing import Any, Dict

from ollama_client import OllamaClient


class PlannerAgent:
    """Transform summary content into an actionable wiki plan."""

    def __init__(self, config: Dict[str, Any], ollama: OllamaClient) -> None:
        self.name = "Planner"
        self.config = config
        self.ollama = ollama

    def run(self, task: str, summary: str) -> Dict[str, Any]:
        prompt = (
            "You are a planning specialist. Create a publish-ready content plan and execution checklist.\n\n"
            f"Task:\n{task}\n\n"
            f"Summary Input:\n{summary}\n\n"
            "Return markdown with:\n"
            "- Suggested Wiki Title\n"
            "- Section Outline (with subsection bullets)\n"
            "- Drafting Workflow (ordered steps)\n"
            "- Quality Checklist\n"
        )

        plan = self.ollama.generate(
            model=self.config["model"],
            prompt=prompt,
            system_prompt=self.config.get("system_prompt", ""),
            temperature=float(self.config.get("temperature", 0.2)),
        )

        return {
            "agent": self.name,
            "plan": plan,
        }
