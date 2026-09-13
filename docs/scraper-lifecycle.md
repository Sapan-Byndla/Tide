# Scraper Lifecycle

TIDE has **two fundamentally different collection modes**, kept as separate
workflows so they can be executed, scaled, and reasoned about independently.
Both share the `BaseScraper` contract but are driven by different workers.

> Phase 0 implements **no scraper and contacts no source**. The workers plan
> windows and report a plan; with an empty registry, all sources are "skipped".

## A. Historical bootstrap (one-time)

Driven by `workers/bootstrap.py` (`HistoricalBootstrapWorker`), implementing
`contracts.scrapers.HistoricalScraper`.

- Uses a **configurable seed list** (`infrastructure/seeds/seeds.example.yaml`).
- Collects history starting **~2 months before the system start date**
  (`TIDE_HISTORICAL_LOOKBACK_DAYS`, default 60).
- Required properties:
  - **Resumable** — continues from a `CollectionCheckpoint`.
  - **Idempotent** — re-running a completed window creates no duplicates.
  - **Checkpointed** — progress persists per source; a crash loses ≤ one batch.
  - **Rate-limit aware** — honours `TIDE_SCRAPER_RATE_LIMIT_PER_MIN`.
  - **Deduplicating** — keyed by `RawPost.dedup_key` (`source_id:external_id`).
  - **Source-agnostic** — via the common scraper interface + registry.
  - **Separately executable** — its own worker/entrypoint, not daily.

```mermaid
sequenceDiagram
    participant W as Bootstrap worker
    participant R as Scraper registry
    participant S as HistoricalScraper
    participant O as ObjectStorage
    participant I as Intelligence
    W->>R: get(source_id, HISTORICAL_BOOTSTRAP)
    W->>S: bootstrap(source, window, checkpoint?)
    loop batches (rate-limited)
        S-->>W: RawPost (dedup_key)
        S-->>O: store large payload (by key)
        W->>W: persist CollectionCheckpoint
    end
    W->>I: hand off collected posts
```

## B. Daily collection (scheduled, recurring)

Driven by `workers/daily.py` (`DailyCollectionWorker`), implementing
`contracts.scrapers.DailyScraper`.

- Collects **only new posts** for each day from configured sources.
- **Must NOT** re-download the historical dataset.
- Supports **configurable collection windows**, so any date/period can be
  **replayed** simply by supplying a different window (`window_for_day(day)`).

```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant W as Daily worker
    participant S as DailyScraper
    participant I as Intelligence
    Sched->>W: run(sources, window=day)
    W->>S: collect(source, window)
    S-->>W: only NEW RawPosts for the window
    W->>I: hand off collected posts
```

## Shared machinery

`scrapers/base/` is reserved for source-agnostic building blocks (rate limiting,
checkpoint persistence, dedup helpers) so individual source scrapers in
`scrapers/sources/` stay thin. Empty of implementation in Phase 0 by design.
