"""The R2 adapter is exercised THROUGH its ObjectStorage abstraction.

A fake S3 client stands in for boto3 so no network or real credentials are used.
The fake mimics the boto3 method surface and error shape (a botocore-style 404).
"""

from __future__ import annotations

from typing import Any

import pytest
from contracts.storage import ObjectStorage
from storage.r2 import R2ObjectStorage


class _NotFound(Exception):
    """Mimics botocore ClientError for a missing key."""

    def __init__(self) -> None:
        super().__init__("Not Found")
        self.response = {"Error": {"Code": "404"}, "ResponseMetadata": {"HTTPStatusCode": 404}}


class FakeS3Client:
    """A minimal in-memory stand-in for a boto3 S3 client."""

    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}

    def put_object(self, Bucket: str, Key: str, Body: bytes, **kw: Any) -> dict:  # noqa: N803
        self.store[Key] = bytes(Body)
        return {}

    def get_object(self, Bucket: str, Key: str) -> dict:  # noqa: N803
        if Key not in self.store:
            raise _NotFound()

        class _Body:
            def __init__(self, data: bytes) -> None:
                self._data = data

            def read(self) -> bytes:
                return self._data

        return {"Body": _Body(self.store[Key])}

    def head_object(self, Bucket: str, Key: str) -> dict:  # noqa: N803
        if Key not in self.store:
            raise _NotFound()
        return {}

    def delete_object(self, Bucket: str, Key: str) -> dict:  # noqa: N803
        self.store.pop(Key, None)
        return {}

    def list_objects_v2(self, Bucket: str, Prefix: str = "", **kw: Any) -> dict:  # noqa: N803
        keys = sorted(k for k in self.store if k.startswith(Prefix))
        return {"Contents": [{"Key": k} for k in keys], "IsTruncated": False}


def test_r2_implements_the_abstraction() -> None:
    adapter = R2ObjectStorage(bucket="tide-raw", client=FakeS3Client())
    assert isinstance(adapter, ObjectStorage)


async def test_r2_roundtrip_through_abstraction() -> None:
    adapter: ObjectStorage = R2ObjectStorage(bucket="tide-raw", client=FakeS3Client())
    key = "raw/reddit/2026/07/01/post-1.json"

    assert await adapter.exists(key) is False
    ref = await adapter.put(key, b"payload", content_type="application/json")
    assert ref == "r2://tide-raw/raw/reddit/2026/07/01/post-1.json"
    assert await adapter.exists(key) is True
    assert await adapter.get(key) == b"payload"
    assert key in [k async for k in adapter.list_prefix("raw/")]
    await adapter.delete(key)
    assert await adapter.exists(key) is False


async def test_r2_get_missing_raises_keyerror() -> None:
    adapter = R2ObjectStorage(bucket="b", client=FakeS3Client())
    with pytest.raises(KeyError):
        await adapter.get("nope.json")


def test_r2_requires_bucket() -> None:
    with pytest.raises(ValueError):
        R2ObjectStorage(bucket="", client=FakeS3Client())


def test_from_settings_requires_full_config() -> None:
    from backend.core.config import Settings

    # No R2_* configured -> fail fast, and never leak secret values.
    with pytest.raises(ValueError) as exc:
        R2ObjectStorage.from_settings(Settings(storage_backend="r2"))
    assert "R2_ENDPOINT_URL" in str(exc.value)
