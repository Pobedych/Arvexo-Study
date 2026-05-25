import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from app.core.config import Settings


def test_production_rejects_default_sqlite_database_url(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="DATABASE_URL must be set explicitly"):
        Settings(
            _env_file=None,
            app_env="production",
            public_site_url="https://study.example.com",
            public_api_url="https://api.study.example.com",
        )


def test_production_rejects_explicit_sqlite_database_url() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL must not use SQLite"):
        Settings(
            _env_file=None,
            app_env="production",
            database_url="sqlite:////tmp/arvexo.db",
            public_site_url="https://study.example.com",
            public_api_url="https://api.study.example.com",
        )


def test_production_accepts_postgres_database_url() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        database_url="postgresql+psycopg://arvexo:secret@postgres:5432/arvexo_study",
        public_site_url="https://study.example.com",
        public_api_url="https://api.study.example.com",
    )

    assert settings.database_url.startswith("postgresql")
