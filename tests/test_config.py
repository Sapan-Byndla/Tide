"""Configuration loads, types, and composes correctly."""

from __future__ import annotations

import pytest
from backend.core.config import AppEnv, Settings, get_settings


def test_defaults_load() -> None:
    settings = Settings()
    assert isinstance(settings.api_port, int)
    assert settings.historical_lookback_days >= 1
    assert settings.llm_provider  # default provided, no lock-in


def test_env_prefix_is_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TIDE_API_PORT", "9999")
    monkeypatch.setenv("TIDE_ENV", "test")
    settings = Settings()
    assert settings.api_port == 9999
    assert settings.env is AppEnv.TEST


def test_database_url_is_composed_when_absent() -> None:
    settings = Settings(database_url=None, postgres_host="db", postgres_port=5432)
    url = settings.sqlalchemy_url
    assert url.startswith("postgresql+psycopg://")
    assert "@db:5432/" in url


def test_explicit_database_url_wins() -> None:
    settings = Settings(database_url="postgresql+psycopg://u:p@host:1/db")
    assert settings.sqlalchemy_url == "postgresql+psycopg://u:p@host:1/db"


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()
