"""TIDE Workers — background job orchestration.

Responsibility
--------------
Drive long-running and scheduled work by composing the other subsystems through
their ports. Workers own *workflow* concerns (windows, checkpoints, scheduling,
retries); they do not contain scraping, extraction, or reasoning logic
themselves.

Two collection workflows are deliberately separate and separately executable:

* ``workers.bootstrap`` — one-time historical bootstrap (resumable, idempotent,
  checkpointed, rate-limit aware, deduplicating).
* ``workers.daily``     — scheduled incremental collection over configurable
  windows; must NOT re-download the historical dataset.

Phase 0 status: workflow skeletons that define entrypoints and windowing but do
no real collection (no scraper is registered, no network call is made). A queue
(Redis) is introduced only if/when a workflow actually needs one.
"""

from __future__ import annotations

from workers.bootstrap import HistoricalBootstrapWorker
from workers.daily import DailyCollectionWorker

__all__ = ["DailyCollectionWorker", "HistoricalBootstrapWorker"]
