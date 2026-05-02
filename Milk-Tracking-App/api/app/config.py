"""Application configuration using pydantic-settings."""

from functools import lru_cache

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
            return "postgresql+asyncpg://" + v[len("postgres://"):]
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
