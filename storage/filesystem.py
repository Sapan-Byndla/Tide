"""Local-filesystem object storage — durable local development option.

Implements ``contracts.ObjectStorage`` by mapping object keys to files under a
base directory. Useful when you want raw payloads to persist across restarts
locally without R2. Blocking file I/O is offloaded with ``asyncio.to_thread``.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from contracts.storage import ObjectStorage


class LocalFileSystemObjectStorage(ObjectStorage):
    """Stores objects as files under ``base_path`` (keys become relative paths)."""

    def __init__(self, base_path: str | Path) -> None:
        self._base = Path(base_path)

    def _resolve(self, key: str) -> Path:
        # Prevent path escapes; keys are always treated as relative.
        target = (self._base / key).resolve()
        base = self._base.resolve()
        if not str(target).startswith(str(base)):
            raise ValueError(f"invalid object key escapes storage root: {key!r}")
        return target

    async def put(self, key: str, data: bytes, content_type: str | None = None) -> str:
        path = self._resolve(key)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bytes(data))

        await asyncio.to_thread(_write)
        return f"file://{path}"

    async def get(self, key: str) -> bytes:
        path = self._resolve(key)

        def _read() -> bytes:
            if not path.exists():
                raise KeyError(f"object not found: {key}")
            return path.read_bytes()

        return await asyncio.to_thread(_read)

    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(self._resolve(key).exists)

    async def delete(self, key: str) -> None:
        path = self._resolve(key)

        def _delete() -> None:
            path.unlink(missing_ok=True)

        await asyncio.to_thread(_delete)

    async def list_prefix(self, prefix: str) -> AsyncIterator[str]:
        base = self._base.resolve()

        def _list() -> list[str]:
            if not base.exists():
                return []
            keys = [str(p.resolve().relative_to(base)) for p in base.rglob("*") if p.is_file()]
            return sorted(k for k in keys if k.startswith(prefix))

        for key in await asyncio.to_thread(_list):
            yield key
