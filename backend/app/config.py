"""Application settings loaded from the root .env via pydantic-settings.

Every value maps to a variable in the root `.env` (injected by docker-compose
through `env_file`), but standard pydantic-settings defaults apply so the app
also runs bare on a host for local dev.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the backend."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    postgres_user: str = "tracker"
    postgres_password: str = "change-me"
    postgres_db: str = "task_tracker"
    postgres_host: str = "postgres"  # compose service name
    postgres_port: int = 5432
    database_url: str | None = None  # override to bypass derivation

    # --- API / scheduling ---
    backend_port: int = 8000
    mail_poll_hours: int = 1
    mail_ingestion_mode: str = "background"  # "background" | "manual"
    mail_mark_as_read: bool = True
    mail_batch_limit: int = 25

    # --- IMAP ---
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    imap_folder: str = "INBOX"

    # --- LLM agent ---
    litellm_model: str = "openai/gpt-4o-mini"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None

    @property
    def sqlalchemy_url(self) -> str:
        """Return the SQLAlchemy async connection string.

        If DATABASE_URL is provided explicitly it is used as-is; otherwise it
        is derived from the individual Postgres variables. Plain `postgres://`
        URLs are rewritten to the async `postgresql+asyncpg://` dialect.
        """
        if self.database_url:
            url = self.database_url
        else:
            url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return url.replace("postgres://", "postgresql+asyncpg://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
