"""Phase 1 configuration: unprefixed external names load via aliases."""

from __future__ import annotations

import pytest
from backend.core.config import Settings, StorageBackend


def test_database_url_reads_unprefixed_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TIDE_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/db")
    settings = Settings()
    assert settings.database_url == "postgresql+psycopg://u:p@h:5432/db"
    assert settings.sqlalchemy_url == "postgresql+psycopg://u:p@h:5432/db"


def test_r2_settings_read_unprefixed_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://example.r2.cloudflarestorage.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "sk")
    monkeypatch.setenv("R2_BUCKET_NAME", "tide-raw")
    settings = Settings()
    assert settings.r2_endpoint_url.endswith("cloudflarestorage.com")
    assert settings.r2_bucket_name == "tide-raw"
    assert settings.r2_region == "auto"  # default


def test_storage_backend_defaults_to_memory() -> None:
    assert Settings().storage_backend is StorageBackend.MEMORY


def test_supabase_secrets_are_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    # With no env and no .env file, the Supabase fields default to empty and are
    # not required (the app runs locally without them).
    for key in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"):
        monkeypatch.delenv(key, raising=False)
    settings = Settings(_env_file=None)  # ignore any real local .env
    assert settings.supabase_url == ""
    assert settings.supabase_service_role_key == ""
