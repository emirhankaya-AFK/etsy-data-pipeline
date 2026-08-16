from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Etsy Data Pipeline"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://pipeline:pipeline@localhost:5432/pipeline"
    collector_mode: str = "demo"
    target_url: str | None = None
    allowed_hosts: list[str] = ["www.etsy.com", "etsy.com"]
    schedule_hours: int = 6
    max_listings_per_run: int = 100
    request_timeout_ms: int = 30_000
    headless: bool = True

    @field_validator("collector_mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"demo", "playwright"}:
            raise ValueError("COLLECTOR_MODE must be 'demo' or 'playwright'")
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
