"""Simple Ollama client wrapper for local LLM calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import requests


class OllamaClientError(RuntimeError):
    """Raised when Ollama API interaction fails."""


@dataclass
class OllamaClient:
    """Client for the Ollama `/api/generate` endpoint."""

    base_url: str
    timeout_seconds: int = 120

    def generate(self, model: str, prompt: str, system_prompt: str | None = None, temperature: float = 0.2) -> str:
        """Generate text from a local Ollama model."""

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        url = f"{self.base_url.rstrip('/')}/api/generate"
        try:
            response = requests.post(url, json=payload, timeout=self.timeout_seconds)
            if response.status_code >= 400:
                body = response.text.strip()
                raise OllamaClientError(
                    f"Ollama API error {response.status_code} at {url}. Response: {body}"
                )
            data = response.json()
        except requests.RequestException as exc:
            raise OllamaClientError(
                "Failed to connect to Ollama. Ensure Ollama is running and accessible."
            ) from exc
        except ValueError as exc:
            raise OllamaClientError("Ollama returned a non-JSON response.") from exc

        generated = data.get("response")
        if not generated:
            raise OllamaClientError("Ollama response did not include generated text.")

        return str(generated).strip()
