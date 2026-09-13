"""Shared, source-agnostic scraper machinery (Phase 0 placeholder).

Later phases add reusable building blocks here so individual source scrapers stay
thin and consistent:

* rate limiting (token bucket) honouring ``TIDE_SCRAPER_RATE_LIMIT_PER_MIN``
* checkpoint persistence for resumable, idempotent historical bootstrap
* dedup helpers built on :attr:`contracts.models.RawPost.dedup_key`

Intentionally empty of implementation in Phase 0 — it defines *where* this code
will live, not the code itself. This is scraper-specific infrastructure, not a
general dumping ground.
"""

from __future__ import annotations

__all__: list[str] = []
