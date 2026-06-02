from typing import Protocol

import httpx

from app.core.config import Settings, get_settings


class LLMClient(Protocol):
    def complete(self, system: str, prompt: str) -> str:
        ...


class HermesClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def complete(self, system: str, prompt: str) -> str:
        if not self.settings.hermes_api_key:
            return self._offline_completion(system, prompt)
        headers = {"Authorization": f"Bearer {self.settings.hermes_api_key}"}
        payload = {
            "model": self.settings.llm_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{self.settings.hermes_base_url.rstrip('/')}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return str(data["choices"][0]["message"]["content"])

    def _offline_completion(self, system: str, prompt: str) -> str:
        return (
            "Offline Hermes adapter response.\n"
            f"System role: {system[:160]}\n"
            f"Prompt summary: {prompt[:800]}\n"
            "Configure HERMES_API_KEY to delegate this step to Hermes Agent."
        )
