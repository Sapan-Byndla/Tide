"""In-memory object storage — local dev & tests, no external service.

Implements the ``contracts.ObjectStorage`` port with a plain dict. Fully
satisfies the abstraction so the rest of the system can run and be tested without
real R2 credentials.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from contracts.storage import ObjectStorage


class InMemoryObjectStorage(ObjectStorage):
    """A dict-backed blob store."""

    def __init__(self, *, uri_scheme: str = "memory") -> None:
        self._data: dict[str, bytes] = {}
        self._content_types: dict[str, str | None] = {}
        self._uri_scheme = uri_scheme

    async def put(self, key: str, data: bytes, content_type: str | None = None) -> str:
        self._data[key] = bytes(data)
        self._content_types[key] = content_type
        return f"{self._uri_scheme}://{key}"

    async def get(self, key: str) -> bytes:
        try:
            return self._data[key]
        except KeyError as exc:
            raise KeyError(f"object not found: {key}") from exc

    async def exists(self, key: str) -> bool:
        return key in self._data

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)
        self._content_types.pop(key, None)

    async def list_prefix(self, prefix: str) -> AsyncIterator[str]:
        for key in sorted(self._data):
            if key.startswith(prefix):
                yield key
