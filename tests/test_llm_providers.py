from app.agents.hermes import GeminiClient, HermesClient, create_llm_client
from app.core.config import Settings


def test_llm_factory_selects_gemini() -> None:
    settings = Settings(LLM_PROVIDER="gemini", GEMINI_API_KEY=None)

    client = create_llm_client(settings)

    assert isinstance(client, GeminiClient)


def test_llm_factory_selects_hermes_by_default() -> None:
    settings = Settings()

    client = create_llm_client(settings)

    assert isinstance(client, HermesClient)


def test_gemini_offline_completion_mentions_configuration() -> None:
    client = GeminiClient(Settings(LLM_PROVIDER="gemini", GEMINI_API_KEY=None))

    text = client.complete("system", "prompt")

    assert "Offline Gemini adapter response" in text
    assert "GEMINI_API_KEY" in text


def test_gemini_extracts_generate_content_text() -> None:
    client = GeminiClient(Settings(LLM_PROVIDER="gemini", GEMINI_API_KEY=None))
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "first"},
                        {"text": "second"},
                    ]
                }
            }
        ]
    }

    assert client._extract_text(payload) == "first\nsecond"
