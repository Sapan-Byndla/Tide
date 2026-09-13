"""Cloudflare R2 object storage adapter (S3-compatible, via boto3).

Implements ``contracts.ObjectStorage`` against R2. Credentials come exclusively
from configuration/environment (``R2_*``) — never hard-coded. The underlying
boto3 S3 client is injectable so the adapter can be exercised through its
abstraction in tests without any network or real credentials.

boto3 is synchronous; blocking calls are offloaded with ``asyncio.to_thread`` to
honour the async ``ObjectStorage`` contract.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from contracts.storage import ObjectStorage

if TYPE_CHECKING:
    from backend.core.config import Settings


def _is_not_found(exc: Exception) -> bool:
    """True if a boto3/botocore error represents a missing key."""
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return False
    code = str(response.get("Error", {}).get("Code", ""))
    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return code in {"404", "NoSuchKey", "NotFound"} or status == 404


class R2ObjectStorage(ObjectStorage):
    """S3-compatible object storage backed by Cloudflare R2."""

    def __init__(self, bucket: str, client: Any) -> None:
        if not bucket:
            raise ValueError("R2ObjectStorage requires a non-empty bucket name")
        self._bucket = bucket
        self._client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> R2ObjectStorage:
        """Build an adapter with a boto3 S3 client from ``R2_*`` settings.

        Raises ``ValueError`` if required configuration is missing so
        misconfiguration fails fast and loudly (without printing secrets).
        """
        missing = [
            name
            for name, value in {
                "R2_ENDPOINT_URL": settings.r2_endpoint_url,
                "R2_ACCESS_KEY_ID": settings.r2_access_key_id,
                "R2_SECRET_ACCESS_KEY": settings.r2_secret_access_key,
                "R2_BUCKET_NAME": settings.r2_bucket_name,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"missing R2 configuration: {', '.join(missing)}")

        import boto3  # imported lazily so non-R2 runs don't need boto3 loaded

        client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name=settings.r2_region,
        )
        return cls(bucket=settings.r2_bucket_name, client=client)

    async def put(self, key: str, data: bytes, content_type: str | None = None) -> str:
        kwargs: dict[str, Any] = {"Bucket": self._bucket, "Key": key, "Body": bytes(data)}
        if content_type:
            kwargs["ContentType"] = content_type
        await asyncio.to_thread(lambda: self._client.put_object(**kwargs))
        return f"r2://{self._bucket}/{key}"

    async def get(self, key: str) -> bytes:
        def _get() -> bytes:
            try:
                resp = self._client.get_object(Bucket=self._bucket, Key=key)
            except Exception as exc:  # noqa: BLE001 - normalize to KeyError
                if _is_not_found(exc):
                    raise KeyError(f"object not found: {key}") from exc
                raise
            return resp["Body"].read()

        return await asyncio.to_thread(_get)

    async def exists(self, key: str) -> bool:
        def _head() -> bool:
            try:
                self._client.head_object(Bucket=self._bucket, Key=key)
            except Exception as exc:  # noqa: BLE001
                if _is_not_found(exc):
                    return False
                raise
            return True

        return await asyncio.to_thread(_head)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(lambda: self._client.delete_object(Bucket=self._bucket, Key=key))

    async def list_prefix(self, prefix: str) -> AsyncIterator[str]:
        token: str | None = None
        while True:
            kwargs: dict[str, Any] = {"Bucket": self._bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            resp = await asyncio.to_thread(
                functools.partial(self._client.list_objects_v2, **kwargs)
            )
            for obj in resp.get("Contents", []) or []:
                yield obj["Key"]
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
