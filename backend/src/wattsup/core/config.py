from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "WattsUp"
    api_prefix: str = "/api"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./data/wattsup.db"

    nut_host: str = "127.0.0.1"
    nut_port: int = Field(default=3493, ge=1, le=65535)
    ups_name: str = "ups"
    nut_username: str | None = None
    nut_password: str | None = None
    nut_timeout_seconds: float = Field(default=5.0, gt=0)
    poll_interval_seconds: int = Field(default=30, ge=5)

    admin_username: str = "admin"
    admin_password: str = Field(min_length=12)
    jwt_secret: str = Field(min_length=32)
    jwt_expiry_hours: int = Field(default=12, ge=1, le=24 * 30)

    frontend_dist: Path = Path("frontend/dist")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
