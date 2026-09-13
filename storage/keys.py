"""Stable object-key construction for raw/large payloads.

Keys are deterministic and use logical prefixes so payloads are easy to browse,
lifecycle, and reprocess. Different sources may have different payload shapes, so
the ``ext`` is explicit rather than assumed.

Layout::

    raw/<source>/<YYYY>/<MM>/<DD>/<identifier>.<ext>
    archives/<source>/<YYYY>/<MM>/<DD>/<identifier>.<ext>
    failed/<source>/<YYYY>/<MM>/<DD>/<identifier>.<ext>
    snapshots/<name>/<YYYY>/<MM>/<DD>/<identifier>.<ext>
"""

from __future__ import annotations

import re
from datetime import datetime

RAW_PREFIX = "raw"
ARCHIVES_PREFIX = "archives"
FAILED_PREFIX = "failed"
SNAPSHOTS_PREFIX = "snapshots"

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize(segment: str) -> str:
    """Make a path segment safe and stable (no slashes/spaces/oddities)."""
    cleaned = _SAFE.sub("-", segment.strip()).strip("-")
    return cleaned or "unknown"


def _dated_key(prefix: str, scope: str, when: datetime, identifier: str, ext: str) -> str:
    return f"{prefix}/{sanitize(scope)}/{when:%Y/%m/%d}/{sanitize(identifier)}.{sanitize(ext)}"


def build_raw_key(source: str, when: datetime, identifier: str, ext: str = "json") -> str:
    """Key for a raw collected payload."""
    return _dated_key(RAW_PREFIX, source, when, identifier, ext)


def build_archive_key(source: str, when: datetime, identifier: str, ext: str = "json") -> str:
    """Key for an archived payload."""
    return _dated_key(ARCHIVES_PREFIX, source, when, identifier, ext)


def build_failed_key(source: str, when: datetime, identifier: str, ext: str = "json") -> str:
    """Key for a payload that failed processing (kept for debugging)."""
    return _dated_key(FAILED_PREFIX, source, when, identifier, ext)


def build_snapshot_key(name: str, when: datetime, identifier: str, ext: str = "json") -> str:
    """Key for a periodic snapshot."""
    return _dated_key(SNAPSHOTS_PREFIX, name, when, identifier, ext)
