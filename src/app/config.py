"""Application configuration via pydantic-settings.

All configuration comes from environment variables (with `.env` fallback in dev).
No secrets are ever hardcoded — the .env.example file documents supported knobs.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are loaded (in order of precedence):
      1. Environment variables
      2. Values in a `.env` file at the project root (dev only)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Identification
    app_name: str = "queue-storm-warmup"
    app_version: str = "0.1.0"
    app_env: str = "development"

    # Behavior knobs
    log_level: str = "INFO"
    summary_max_chars: int = 280

    # Operational limits (latency SLAs in seconds — purely informational,
    # surfaced via /health for monitoring)
    health_sla_seconds: float = 10.0
    sort_ticket_sla_seconds: float = 30.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so we only read env once per process. Override via
    `app.dependency_overrides[get_settings]` in tests.
    """
    return Settings()