"""Local object-storage adapters behave per the ObjectStorage contract."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from storage.filesystem import LocalFileSystemObjectStorage
from storage.keys import build_failed_key, build_raw_key
from storage.memory import InMemoryObjectStorage


def test_key_builders_are_stable() -> None:
    when = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    assert build_raw_key("reddit", when, "ext_1") == "raw/reddit/2026/07/01/ext_1.json"
    assert build_failed_key("rss", when, "a b/c", "xml").startswith("failed/rss/2026/07/01/")


@pytest.mark.parametrize(
    "make",
    [
        lambda tmp: InMemoryObjectStorage(),
        lambda tmp: LocalFileSystemObjectStorage(tmp),
    ],
)
async def test_roundtrip(make, tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = make(tmp_path)
    key = "raw/reddit/2026/07/01/post-1.json"

    assert await store.exists(key) is False
    ref = await store.put(key, b'{"hello":"world"}', content_type="application/json")
    assert isinstance(ref, str) and ref

    assert await store.exists(key) is True
    assert await store.get(key) == b'{"hello":"world"}'

    keys = [k async for k in store.list_prefix("raw/reddit/")]
    assert key in keys

    await store.delete(key)
    assert await store.exists(key) is False


@pytest.mark.parametrize(
    "make",
    [
        lambda tmp: InMemoryObjectStorage(),
        lambda tmp: LocalFileSystemObjectStorage(tmp),
    ],
)
async def test_get_missing_raises_keyerror(make, tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = make(tmp_path)
    with pytest.raises(KeyError):
        await store.get("does/not/exist.json")


def test_factory_defaults_to_memory() -> None:
    from backend.core.config import Settings
    from storage.factory import get_object_storage

    store = get_object_storage(Settings())
    assert isinstance(store, InMemoryObjectStorage)
