"""Application configuration loaded from environment / .env file.

The project moved away from the Azure-hosted LLM instances to an
OpenAI-compatible endpoint. That endpoint requires an explicit base URL,
which is provided through ``OPENAI_BASE_URL``.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings sourced from the repository ``.env`` file."""

    # OpenAI-compatible endpoint credentials
    openai_api_key: str = ""
    openai_model: str = "gpt-5.5-project"
    openai_embedding_model: str = "text-embedding-3-large-project"
    openai_base_url: str = "https://ai-incubator-api.pnnl.gov"

    # Shared unlock password (previously the per-project access keys).
    im3_access: str = "phase3"

    # Token ceiling used to warn users about oversized documents.
    max_allowable_tokens: int = 150000

    # CORS: comma-separated list of allowed origins for the SPA.
    # Empty string means "allow all" (useful behind a same-origin Nginx proxy).
    cors_allow_origins: str = ""

    model_config = SettingsConfigDict(
        # Look for a .env in the backend dir first, then the repo root.
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_allow_origins.strip():
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
