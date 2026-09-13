"""Object-storage factory — pick an adapter from configuration.

Keeps call sites decoupled from concrete adapters: they depend on the
``ObjectStorage`` port and let the factory choose ``memory`` (default, local dev /
tests), ``filesystem`` (durable local), or ``r2`` (staging/prod).
"""

from __future__ import annotations

from backend.core.config import Settings, StorageBackend, get_settings
from contracts.storage import ObjectStorage

from storage.filesystem import LocalFileSystemObjectStorage
from storage.memory import InMemoryObjectStorage


def get_object_storage(settings: Settings | None = None) -> ObjectStorage:
    """Construct the configured ``ObjectStorage`` adapter."""
    settings = settings or get_settings()
    backend = settings.storage_backend

    if backend is StorageBackend.MEMORY:
        return InMemoryObjectStorage()
    if backend is StorageBackend.FILESYSTEM:
        return LocalFileSystemObjectStorage(settings.filesystem_storage_path)
    if backend is StorageBackend.R2:
        # Imported here so local/dev runs never require boto3 to be importable.
        from storage.r2 import R2ObjectStorage

        return R2ObjectStorage.from_settings(settings)

    raise ValueError(f"unknown storage backend: {backend!r}")
