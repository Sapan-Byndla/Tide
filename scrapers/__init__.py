"""TIDE Scrapers — source-specific data collection.

Responsibility
--------------
Turn external sources into :class:`contracts.models.RawPost` objects, and nothing
more. Scrapers do not normalize, embed, store to the graph, or reason — those are
other subsystems' jobs.

Structure
---------
* ``scrapers.base``    — shared, source-agnostic scraper machinery that later
  phases will fill in (rate limiting, checkpoint persistence, dedup helpers).
* ``scrapers.sources`` — one module per concrete source (added in later phases).
* ``scrapers.registry`` — maps a source to its historical/daily scraper class.

Two collection workflows are kept strictly separate (see
``contracts.scrapers``): historical bootstrap vs. daily collection. They share
the ``BaseScraper`` contract but are executed by different workers.

Phase 0 status: interfaces + registry skeleton only. No source is implemented and
no website is contacted.
"""

from __future__ import annotations

from scrapers.registry import ScraperRegistry, registry

__all__ = ["ScraperRegistry", "registry"]
