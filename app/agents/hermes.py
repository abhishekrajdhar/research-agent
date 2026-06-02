from typing import Any, Protocol

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


class GeminiClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def complete(self, system: str, prompt: str) -> str:
        if not self.settings.gemini_api_key:
            return self._offline_completion(system, prompt)
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        url = (
            f"{self.settings.gemini_base_url.rstrip('/')}/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
        )
        headers = {"x-goog-api-key": self.settings.gemini_api_key}
        with httpx.Client(timeout=30) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return self._extract_text(response.json())

    def _extract_text(self, data: dict[str, Any]) -> str:
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "\n".join(str(part.get("text", "")) for part in parts if part.get("text")).strip()

    def _offline_completion(self, system: str, prompt: str) -> str:
        return (
            "Offline Gemini adapter response.\n"
            f"System role: {system[:160]}\n"
            f"Prompt summary: {prompt[:800]}\n"
            "Set LLM_PROVIDER=gemini and configure GEMINI_API_KEY to call the Gemini API."
        )


def create_llm_client(settings: Settings | None = None) -> LLMClient:
    active_settings = settings or get_settings()
    provider = active_settings.llm_provider.strip().lower()
    if provider == "gemini":
        return GeminiClient(active_settings)
    if provider == "hermes":
        return HermesClient(active_settings)
    raise ValueError(f"Unsupported LLM_PROVIDER: {active_settings.llm_provider}")
