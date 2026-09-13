"""Historical bootstrap worker (Phase 0 skeleton).

A one-time operation that backfills ~2 months of history for each seed source.
Kept entirely separate from daily collection so the two can be executed, scaled,
and reasoned about independently.

Design guarantees this skeleton is built to honour in later phases:

* **Resumable / checkpointed** — progress is persisted per source as a
  ``CollectionCheckpoint`` so a crash resumes rather than restarts.
* **Idempotent / deduplicating** — re-running a completed window produces no
  duplicates (keyed by ``RawPost.dedup_key``).
* **Rate-limit aware** — respects ``TIDE_SCRAPER_RATE_LIMIT_PER_MIN``.

Phase 0 performs no collection: with an empty registry, ``run`` computes windows
and reports a plan without contacting any source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from contracts.enums import CollectionMode
from contracts.models import ScrapeWindow, SeedSource
from scrapers.registry import ScraperRegistry, registry


@dataclass
class BootstrapPlan:
    """The set of per-source windows a bootstrap run intends to cover."""

    windows: dict[str, ScrapeWindow] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)


class HistoricalBootstrapWorker:
    """Plans and (later) executes the one-time historical backfill."""

    def __init__(
        self,
        *,
        lookback_days: int,
        scraper_registry: ScraperRegistry | None = None,
    ) -> None:
        self._lookback_days = lookback_days
        self._registry = scraper_registry or registry

    def plan(self, sources: list[SeedSource], now: datetime) -> BootstrapPlan:
        """Compute the historical window for each enabled, registered source.

        ``now`` is passed in (never read from the clock here) so the plan is
        deterministic and testable.
        """
        plan = BootstrapPlan()
        start = now - timedelta(days=self._lookback_days)
        for source in sources:
            if not source.enabled:
                plan.skipped.append(source.id)
                continue
            if self._registry.get(source.id, CollectionMode.HISTORICAL_BOOTSTRAP) is None:
                plan.skipped.append(source.id)
                continue
            plan.windows[source.id] = ScrapeWindow(
                start=start, end=now, mode=CollectionMode.HISTORICAL_BOOTSTRAP
            )
        return plan

    async def run(self, sources: list[SeedSource], now: datetime) -> BootstrapPlan:
        """Entry point for the bootstrap workflow.

        Phase 0: returns the plan only. Actual resumable collection is added when
        concrete historical scrapers are registered.
        """
        return self.plan(sources, now)
