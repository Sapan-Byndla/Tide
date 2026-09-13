"""The two collection workflows plan windows correctly and stay separate.

No collection happens (the registry is empty), but we verify the windowing logic
that makes historical bootstrap and daily collection distinct and replayable.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from contracts.enums import CollectionMode, SourceType
from contracts.models import SeedSource
from workers.bootstrap import HistoricalBootstrapWorker
from workers.daily import DailyCollectionWorker

NOW = datetime(2026, 9, 13, 12, 0, 0)


def _source(sid: str, enabled: bool = True) -> SeedSource:
    return SeedSource(
        id=sid,
        name=sid,
        source_type=SourceType.RSS,
        url="https://example.com/feed.xml",
        enabled=enabled,
    )


def test_bootstrap_window_uses_lookback() -> None:
    worker = HistoricalBootstrapWorker(lookback_days=60)
    # With an empty registry, sources are skipped (nothing to collect from yet).
    plan = worker.plan([_source("a")], NOW)
    assert plan.windows == {}
    assert plan.skipped == ["a"]


def test_bootstrap_computes_two_month_window_when_registered() -> None:
    from contracts.scrapers import HistoricalScraper
    from scrapers.registry import ScraperRegistry

    reg = ScraperRegistry()
    reg.register_historical("a", HistoricalScraper)  # type: ignore[arg-type]
    worker = HistoricalBootstrapWorker(lookback_days=60, scraper_registry=reg)

    plan = worker.plan([_source("a")], NOW)
    window = plan.windows["a"]
    assert window.mode is CollectionMode.HISTORICAL_BOOTSTRAP
    assert window.end == NOW
    assert window.start == NOW - timedelta(days=60)


def test_daily_window_is_single_day() -> None:
    window = DailyCollectionWorker.window_for_day(NOW)
    assert window.mode is CollectionMode.DAILY
    assert window.start == datetime(2026, 9, 13, 0, 0, 0)
    assert window.end == datetime(2026, 9, 14, 0, 0, 0)


def test_daily_skips_disabled_sources() -> None:
    worker = DailyCollectionWorker()
    window = DailyCollectionWorker.window_for_day(NOW)
    plan = worker.plan([_source("a", enabled=False)], window)
    assert plan.source_ids == []
    assert plan.skipped == ["a"]
