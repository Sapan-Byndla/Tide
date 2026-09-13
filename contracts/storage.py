"""Object storage contract.

Raw and large payloads (full HTML, media, big JSON blobs) live in object storage
such as Cloudflare R2, referenced from relational rows by key. This interface is
S3/R2-agnostic; a local-filesystem or in-memory adapter satisfies it for tests.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class ObjectStorage(ABC):
    """Key/value blob storage for raw and large payloads."""

    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str | None = None) -> str:
        """Store ``data`` under ``key``; return the canonical storage reference."""

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """Retrieve a stored payload. Raises ``KeyError`` if absent."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Return whether ``key`` exists."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a stored payload (no error if absent)."""

    @abstractmethod
    def list_prefix(self, prefix: str) -> AsyncIterator[str]:
        """Return an async iterator of keys beginning with ``prefix``.

        Declared as a plain method returning ``AsyncIterator`` (not ``async def``)
        so async-generator implementations (``async def`` with ``yield``) satisfy
        the signature — the standard typing shape for an async iterator port.
        """
