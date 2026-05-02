"""Application configuration using pydantic-settings."""

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database (SQLite for local dev, PostgreSQL for production)
    DATABASE_URL: str = "sqlite+aiosqlite:///./milk_tracking.db"

    # JWT Authentication
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @field_validator("DATABASE_URL")
    @classmethod
    def _coerce_async_postgres(cls, v: str) -> str:
        # Render and most managed Postgres providers expose `postgres://` or
        # `postgresql://` URIs; SQLAlchemy's async stack needs the asyncpg driver.
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]

        # asyncpg rejects psycopg2-only query params. Strip them — asyncpg
        # negotiates SSL automatically when the server requires it (e.g. Neon).
        psycopg2_only = {
            "sslmode",
            "channel_binding",
            "gssencmode",
            "sslcert",
            "sslkey",
            "sslrootcert",
            "sslcrl",
        }
        if "+asyncpg" in v and any(p in v for p in psycopg2_only):
            parsed = urlparse(v)
            kept = [
                (k, val) for k, val in parse_qsl(parsed.query)
                if k not in psycopg2_only
            ]
            v = urlunparse(parsed._replace(query=urlencode(kept)))

        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
