from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "sqlite:///./arvexo_study.db"
    redis_url: str = "redis://localhost:6379/0"
    backend_cors_origins: str = "http://localhost:3001,http://127.0.0.1:3001"
    ai_provider: str = "stub"
    ai_model: str = "stub-hint-v1"
    telegram_bot_token: str = ""
    telegram_login_max_age_seconds: int = 60 * 60 * 24
    jwt_secret: str = Field(default="change-me", min_length=8)
    access_token_expire_minutes: int = 60 * 24 * 7

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
