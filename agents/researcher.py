"""Researcher agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import requests

from ollama_client import OllamaClient


class ResearcherAgent:
    """Collect context from local files and optional public APIs."""

    def __init__(self, config: Dict[str, Any], ollama: OllamaClient) -> None:
        self.name = "Researcher"
        self.config = config
        self.ollama = ollama

    def _search_local_documents(self, task: str, docs_dir: Path, max_docs: int = 4) -> List[Dict[str, str]]:
        keywords = [token.lower() for token in task.split() if len(token) > 2]
        ranked: List[tuple[int, Path, str]] = []

        for path in docs_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".txt", ".md"}:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            score = sum(content.lower().count(keyword) for keyword in keywords)
            if score > 0:
                ranked.append((score, path, content[:2200]))

        ranked.sort(key=lambda item: item[0], reverse=True)

        results: List[Dict[str, str]] = []
        for score, path, snippet in ranked[:max_docs]:
            results.append(
                {
                    "source": str(path),
                    "score": str(score),
                    "snippet": snippet,
                }
            )
        return results

    def _fetch_wikipedia_summary(self, task: str) -> str:
        query = task.split(" on ")[-1].strip().replace(" ", "_")
        if not query:
            return ""

        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            data = response.json()
            extract = data.get("extract", "")
            return str(extract).strip()
        except Exception:
            return ""

    def run(self, task: str) -> Dict[str, Any]:
        docs_dir = Path(self.config.get("documents_dir", "sample_tasks"))
        local_results = self._search_local_documents(task=task, docs_dir=docs_dir)
        wiki_summary = self._fetch_wikipedia_summary(task)

        context_blocks: List[str] = []
        for item in local_results:
            context_blocks.append(
                f"Source: {item['source']}\nRelevance Score: {item['score']}\nSnippet:\n{item['snippet']}"
            )

        if wiki_summary:
            context_blocks.append(f"Source: Wikipedia REST summary\nSnippet:\n{wiki_summary}")

        joined_context = "\n\n---\n\n".join(context_blocks) if context_blocks else "No external context found."

        prompt = (
            "You are a research specialist. Build concise research notes from the provided task and context.\n"
            "Focus on factual information, key concepts, and reliable framing for downstream agents.\n\n"
            f"Task:\n{task}\n\n"
            f"Available Context:\n{joined_context}\n\n"
            "Return in markdown with sections: Key Facts, Important Terms, Potential Angles, and Source Notes."
        )

        notes = self.ollama.generate(
            model=self.config["model"],
            prompt=prompt,
            system_prompt=self.config.get("system_prompt", ""),
            temperature=float(self.config.get("temperature", 0.2)),
        )

        return {
            "agent": self.name,
            "research_notes": notes,
            "raw_context": joined_context,
            "sources": [item["source"] for item in local_results] + (["Wikipedia"] if wiki_summary else []),
        }
