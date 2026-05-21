from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    local_site_url: str = "http://localhost:3001"
    local_api_url: str = "http://localhost:8001"
    app_env: str = "local"
    database_url: str = "sqlite:///./arvexo_study.db"
    redis_url: str = "redis://localhost:6379/0"
    backend_cors_origins: str = "http://localhost:3001,http://127.0.0.1:3001"
    public_site_url: str = "http://localhost:3001"
    public_api_url: str = "http://localhost:8001"
    ai_provider: str = "stub"
    ai_model: str = "stub-hint-v1"
    telegram_bot_token: str = ""
    telegram_login_max_age_seconds: int = 60 * 60 * 24
    google_client_id: str = ""
    google_client_secret: str = ""
    yandex_client_id: str = ""
    yandex_client_secret: str = ""
    jwt_secret: str = Field(default="change-me", min_length=8)
    access_token_expire_minutes: int = 60 * 24 * 7

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    def public_site_origin(self) -> str:
        return self._public_origin(self.public_site_url, self.local_site_url, "PUBLIC_SITE_URL")

    def public_api_origin(self) -> str:
        return self._public_origin(self.public_api_url, self.local_api_url, "PUBLIC_API_URL")

    def _public_origin(self, value: str, fallback: str, env_name: str) -> str:
        origin = value.strip() or fallback
        if self.app_env == "production" and ("localhost" in origin or "127.0.0.1" in origin):
            raise ValueError(f"{env_name} must be a public HTTPS URL in production")
        return origin.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
