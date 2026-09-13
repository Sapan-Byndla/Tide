"""Concrete, source-specific scrapers (added in later phases).

Each source gets its own module implementing ``HistoricalScraper`` and/or
``DailyScraper`` and registering itself on ``scrapers.registry.registry``.

Phase 0: empty by design — no external source is implemented and no website is
scraped.
"""

from __future__ import annotations

__all__: list[str] = []
