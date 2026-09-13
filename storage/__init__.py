"""TIDE object-storage adapters (implementations of ``contracts.ObjectStorage``).

Raw and large payloads live in object storage — never in PostgreSQL, which stores
only the normalized row plus a ``raw_payload_uri`` reference. Adapters:

* ``InMemoryObjectStorage``       — local dev / tests (no external service)
* ``LocalFileSystemObjectStorage``— durable local development
* ``R2ObjectStorage``             — Cloudflare R2 (S3-compatible), staging/prod

Use :func:`storage.factory.get_object_storage` to select one from settings, and
:mod:`storage.keys` to build stable object keys.
"""

from __future__ import annotations

from storage.factory import get_object_storage
from storage.filesystem import LocalFileSystemObjectStorage
from storage.memory import InMemoryObjectStorage

__all__ = [
    "InMemoryObjectStorage",
    "LocalFileSystemObjectStorage",
    "get_object_storage",
]
