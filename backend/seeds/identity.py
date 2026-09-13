"""Deterministic, stable identifiers for seeds and sources.

Seed identity must NOT depend on DB-generated values: re-importing
``seed_list.yaml`` must land on the same rows. We derive:

* a human-readable, stable ``key`` string from the seed's identity, and
* a deterministic ``UUID`` via ``uuid5`` over that key (so even primary keys are
  reproducible for seed/demo data).

Changing a seed's identity (its type/source/canonical value) intentionally
produces a new key — that is a *different* seed, not an edit of the old one.
"""

from __future__ import annotations

import re
import uuid

# Fixed application namespace (randomly chosen once; never change it).
TIDE_NAMESPACE = uuid.UUID("6f8d2a1e-4c3b-5e7a-9b0c-1d2e3f4a5b6c")
SEED_NAMESPACE = uuid.uuid5(TIDE_NAMESPACE, "tide:seed")
SOURCE_NAMESPACE = uuid.uuid5(TIDE_NAMESPACE, "tide:source")

_SLUG_STRIP = re.compile(r"[^a-z0-9._-]+")


def slugify(value: str) -> str:
    """Lowercase, collapse unsafe chars to ``-``; keep ``. _ -`` (e.g. ``cs.AI``→``cs.ai``)."""
    lowered = value.strip().lower().replace(" ", "_")
    slug = _SLUG_STRIP.sub("-", lowered).strip("-_")
    return slug or "unknown"


def seed_key(seed_type: str, source_key: str | None, canonical_value: str) -> str:
    """Build the stable seed key.

    * topics (no source):        ``topic:<value>``
    * source-specific targets:   ``<source>:<seed_type>:<slug(value)>``
    """
    if source_key is None:
        return f"{seed_type}:{slugify(canonical_value)}"
    return f"{source_key}:{seed_type}:{slugify(canonical_value)}"


def seed_uuid(key: str) -> uuid.UUID:
    """Deterministic UUID for a seed, derived from its stable key."""
    return uuid.uuid5(SEED_NAMESPACE, key)


def source_uuid(source_key: str) -> uuid.UUID:
    """Deterministic UUID for a source, derived from its source key."""
    return uuid.uuid5(SOURCE_NAMESPACE, source_key)
