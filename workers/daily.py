"""Daily collection worker (Phase 0 skeleton).

A scheduled, recurring operation that collects only *new* posts for each day from
configured sources. It must never re-download the historical dataset, and it
supports configurable windows so a specific date or period can be replayed.

Phase 0 performs no collection: with an empty registry, ``run`` resolves the
target window and reports a plan without contacting any source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from contracts.enums import CollectionMode
from contracts.models import ScrapeWindow, SeedSource
from scrapers.registry import ScraperRegistry, registry


@dataclass
class DailyPlan:
    """The window and eligible sources for a daily run."""

    window: ScrapeWindow
    source_ids: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class DailyCollectionWorker:
    """Plans and (later) executes incremental daily collection."""

    def __init__(self, *, scraper_registry: ScraperRegistry | None = None) -> None:
        self._registry = scraper_registry or registry

    @staticmethod
    def window_for_day(day: datetime) -> ScrapeWindow:
        """A single-day collection window [00:00, 24:00) for ``day``.

        Windows are explicit and passed around so any date can be replayed simply
        by supplying a different ``day``.
        """
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        return ScrapeWindow(
            start=start,
            end=start + timedelta(days=1),
            mode=CollectionMode.DAILY,
        )

    def plan(self, sources: list[SeedSource], window: ScrapeWindow) -> DailyPlan:
        plan = DailyPlan(window=window)
        for source in sources:
            if not source.enabled:
                plan.skipped.append(source.id)
                continue
            if self._registry.get(source.id, CollectionMode.DAILY) is None:
                plan.skipped.append(source.id)
                continue
            plan.source_ids.append(source.id)
        return plan

    async def run(self, sources: list[SeedSource], window: ScrapeWindow) -> DailyPlan:
        """Entry point for the daily workflow. Phase 0: returns the plan only."""
        return self.plan(sources, window)
