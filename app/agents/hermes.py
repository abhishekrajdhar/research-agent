from typing import Any, Protocol

import logging
import httpx
import time

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

    class FallbackLLMClient:
        """LLM client wrapper that always tries Gemini first, then Hermes on failure.

        - If Gemini is configured, it will call GeminiClient.complete(). If the request
          raises an exception (HTTP error, network, etc.), it will log a warning and
          fall back to HermesClient.complete().
        - HermesClient will itself return an offline stub when no HERMES_API_KEY is set.
        """

        def __init__(self, settings: Settings) -> None:
            self.settings = settings
            self.gemini = GeminiClient(settings)
            self.hermes = HermesClient(settings)
            self.logger = logging.getLogger("llm.fallback")
            self.last_provider: str | None = None
        def complete(self, system: str, prompt: str) -> str:
            # Try Gemini first with a small retry/backoff loop. If all attempts fail,
            # fall back to Hermes. This ensures transient Gemini errors (rate limits,
            # transient 5xx) don't immediately force a fallback and gives Gemini a
            # chance to serve every agent.
            max_attempts = 3
            backoff_base = 0.8
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    self.logger.debug("gemini_attempt %s/%s", attempt, max_attempts)
                    resp = self.gemini.complete(system, prompt)
                    self.last_provider = "gemini"
                    return resp
                except Exception as e:
                    last_exc = e
                    # If Gemini is not configured and raises immediately (offline stub),
                    # don't sleep needlessly; break and fall back.
                    if "Offline Gemini adapter response" in str(getattr(e, "args", [""])[0]):
                        self.logger.warning("gemini_offline_stub_detected, falling back to Hermes")
                        break
                    # log and backoff before retrying
                    self.logger.warning("gemini_attempt_failed attempt=%s error=%s", attempt, str(e))
                    if attempt < max_attempts:
                        sleep_for = backoff_base * (2 ** (attempt - 1))
                        try:
                            time.sleep(sleep_for)
                        except Exception:
                            pass

            # All Gemini attempts failed — try Hermes as a fallback
            self.logger.warning("gemini_all_attempts_failed_falling_back_to_hermes error=%s", str(last_exc))
            try:
                resp = self.hermes.complete(system, prompt)
                self.last_provider = "hermes"
                return resp
            except Exception as e2:
                self.logger.error("hermes_fallback_failed error=%s", str(e2))
                # If Hermes also fails, propagate the original Gemini exception if available
                raise last_exc or e2

    return FallbackLLMClient(active_settings)
