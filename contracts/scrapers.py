"""Scraper contracts.

Two fundamentally separate collection workflows share a common base so the rest
of TIDE stays source-agnostic:

* ``HistoricalScraper`` — one-time, resumable, idempotent, checkpointed backfill
  starting ~2 months before the system start date.
* ``DailyScraper`` — scheduled, windowed, incremental collection that must never
  re-download the historical dataset.

No implementation lives here. Concrete, source-specific scrapers arrive later in
``scrapers/sources/`` and are wired in via the registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from contracts.enums import CollectionMode, SourceType
from contracts.models import (
    CollectionCheckpoint,
    RawPost,
    ScrapeWindow,
    SeedSource,
)


class BaseScraper(ABC):
    """Common contract for every source-specific scraper.

    A scraper is responsible only for *collection* — turning an external source
    into :class:`RawPost` objects. Normalization, storage, and graph work belong
    to other subsystems.
    """

    #: Which source type this scraper handles; used by the registry.
    source_type: SourceType

    @property
    @abstractmethod
    def mode(self) -> CollectionMode:
        """The collection workflow this scraper participates in."""

    @abstractmethod
    async def healthcheck(self) -> bool:
        """Return ``True`` if the source is reachable and the scraper is usable."""

    @abstractmethod
    def dedup_key(self, post: RawPost) -> str:
        """Return the stable identity used to deduplicate a post.

        Enables idempotent collection: re-collecting the same item yields the
        same key so downstream storage can upsert rather than duplicate.
        """


class HistoricalScraper(BaseScraper):
    """One-time historical bootstrap for a single source.

    Implementations MUST be resumable and idempotent: given a checkpoint they
    continue where they left off, and re-running a completed window produces no
    duplicates. They MUST respect rate limits and periodically emit updated
    checkpoints so a crash loses at most one batch.
    """

    @property
    def mode(self) -> CollectionMode:
        return CollectionMode.HISTORICAL_BOOTSTRAP

    @abstractmethod
    async def bootstrap(
        self,
        source: SeedSource,
        window: ScrapeWindow,
        checkpoint: CollectionCheckpoint | None = None,
    ) -> AsyncIterator[RawPost]:
        """Yield historical posts for ``source`` within ``window``.

        Args:
            source: The seed source to backfill.
            window: The (historical) time range to cover.
            checkpoint: Prior progress to resume from, if any.

        Yields:
            Raw posts in collection order.
        """
        raise NotImplementedError

    @abstractmethod
    async def checkpoint(self) -> CollectionCheckpoint:
        """Return the current resumable checkpoint for persistence."""


class DailyScraper(BaseScraper):
    """Scheduled, incremental collection for a single source.

    Implementations collect only new posts for a given window and MUST NOT
    re-download the historical dataset. Windows are configurable so a specific
    date or period can be replayed.
    """

    @property
    def mode(self) -> CollectionMode:
        return CollectionMode.DAILY

    @abstractmethod
    async def collect(
        self,
        source: SeedSource,
        window: ScrapeWindow,
    ) -> AsyncIterator[RawPost]:
        """Yield new posts for ``source`` within the daily ``window``."""
        raise NotImplementedError
