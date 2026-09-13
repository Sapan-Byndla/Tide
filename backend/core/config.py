"""Typed application configuration.

All configuration comes from environment variables (12-factor). Secrets are never
hardcoded — see ``.env.example`` for the documented surface.

Most TIDE settings use the ``TIDE_`` prefix so they don't collide with unrelated
env vars. A few well-known, conventionally-named variables are read *without* the
prefix via explicit aliases: ``DATABASE_URL``, the ``SUPABASE_*`` keys, and the
``R2_*`` object-storage keys. ``populate_by_name=True`` keeps the plain field
names usable in code and tests.

Nothing here opens a connection or contacts a service; values are read, typed,
and validated for adapters (DB engine, R2 storage) to consume.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class StorageBackend(StrEnum):
    """Which object-storage adapter the factory should construct."""

    MEMORY = "memory"  # in-process fake (local dev / tests)
    FILESYSTEM = "filesystem"  # local directory (local dev)
    R2 = "r2"  # Cloudflare R2 (S3-compatible; staging/prod)


class Settings(BaseSettings):
    """Root settings object, populated from the environment / ``.env``."""

    model_config = SettingsConfigDict(
        env_prefix="TIDE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # ---- Application ----
    env: AppEnv = AppEnv.LOCAL
    debug: bool = True
    log_level: str = "INFO"
    log_json: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ---- PostgreSQL (system of record) ----
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "tide"
    postgres_password: str = "tide_local_password"
    postgres_db: str = "tide"
    # `DATABASE_URL` (unprefixed, conventional) wins; falls back to TIDE_DATABASE_URL,
    # then to a URL composed from the discrete POSTGRES_* fields.
    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "TIDE_DATABASE_URL"),
    )

    # ---- Supabase (managed Postgres in staging/prod; secrets) ----
    supabase_url: str = Field(default="", validation_alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", validation_alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", validation_alias="SUPABASE_SERVICE_ROLE_KEY")

    # ---- Object storage (raw/large payloads) ----
    storage_backend: StorageBackend = StorageBackend.MEMORY
    filesystem_storage_path: str = ".tide/objectstore"
    # Cloudflare R2 (S3-compatible). Unprefixed, conventional names. Secrets stay
    # empty by default and are never printed.
    r2_endpoint_url: str = Field(default="", validation_alias="R2_ENDPOINT_URL")
    r2_access_key_id: str = Field(default="", validation_alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(default="", validation_alias="R2_SECRET_ACCESS_KEY")
    r2_bucket_name: str = Field(default="", validation_alias="R2_BUCKET_NAME")
    r2_region: str = Field(default="auto", validation_alias="R2_REGION")

    # ---- Redis (optional future queue/cache) ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- Embedding provider (model + dimension chosen in a LATER phase) ----
    embedding_provider: str = "noop"
    embedding_model: str = "none"

    # ---- LLM provider (replaceable; no vendor lock-in) ----
    llm_provider: str = "noop"
    llm_model: str = "none"
    llm_api_key: str = ""

    # ---- Seed configuration / collection ----
    seed_list_path: str = "seed_list.yaml"
    historical_lookback_days: int = Field(default=60, ge=1)
    scraper_rate_limit_per_min: int = Field(default=60, ge=1)
    scraper_checkpoint_dir: str = ".tide/checkpoints"

    @property
    def sqlalchemy_url(self) -> str:
        """Return the DB URL, composing one from parts if not explicitly set.

        Uses the ``psycopg`` (v3) driver name; no connection is opened here.
        """
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.env is AppEnv.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (dependency-injection friendly)."""
    return Settings()
