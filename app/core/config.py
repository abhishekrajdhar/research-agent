from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+psycopg://research:research@localhost:5432/research_lab",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="research_memories", alias="QDRANT_COLLECTION")
    hermes_base_url: str = Field(default="http://localhost:8080", alias="HERMES_BASE_URL")
    hermes_api_key: str | None = Field(default=None, alias="HERMES_API_KEY")
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com", alias="GEMINI_BASE_URL"
    )
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gbrain_base_url: str | None = Field(default=None, alias="GBRAIN_BASE_URL")
    gbrain_api_key: str | None = Field(default=None, alias="GBRAIN_API_KEY")
    llm_provider: str = Field(default="hermes", alias="LLM_PROVIDER")
    llm_model: str = Field(default="hermes-default", alias="LLM_MODEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
