"""Scraper registry.

A tiny, dependency-free lookup that maps a source id to the scraper classes that
handle it, for each collection mode. Workers use this to stay source-agnostic:
they ask the registry for "the daily scraper for source X" rather than importing
concrete classes.

Phase 0: the registry exists and is exercised by tests, but ships empty — no
concrete scrapers are registered yet.
"""

from __future__ import annotations

from contracts.enums import CollectionMode
from contracts.scrapers import DailyScraper, HistoricalScraper

# A factory takes no args here and returns a scraper instance. Later phases may
# inject dependencies (http client, rate limiter) via partials/DI.
HistoricalFactory = type[HistoricalScraper]
DailyFactory = type[DailyScraper]


class ScraperRegistry:
    """Maps ``source_id`` -> scraper classes per collection mode."""

    def __init__(self) -> None:
        self._historical: dict[str, HistoricalFactory] = {}
        self._daily: dict[str, DailyFactory] = {}

    def register_historical(self, source_id: str, factory: HistoricalFactory) -> None:
        self._historical[source_id] = factory

    def register_daily(self, source_id: str, factory: DailyFactory) -> None:
        self._daily[source_id] = factory

    def get(self, source_id: str, mode: CollectionMode) -> type | None:
        if mode is CollectionMode.HISTORICAL_BOOTSTRAP:
            return self._historical.get(source_id)
        return self._daily.get(source_id)

    def registered_sources(self, mode: CollectionMode) -> list[str]:
        table = self._historical if mode is CollectionMode.HISTORICAL_BOOTSTRAP else self._daily
        return sorted(table)


#: Process-wide default registry. Concrete scrapers register onto this in later
#: phases (typically at import time in ``scrapers.sources``).
registry = ScraperRegistry()
