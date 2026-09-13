# TIDE Documentation

Phase 0 documentation index. Start with the architecture, then dive into the
subsystem you care about.

| Doc | Covers |
| --- | --- |
| [architecture.md](architecture.md) | Overall architecture, subsystem responsibilities, data flow, **Mermaid diagram**. |
| [data-model.md](data-model.md) | **Phase 1** — the complete database schema (ER diagram + every table). |
| [seeds-vs-concepts.md](seeds-vs-concepts.md) | **Phase 1** — curated seeds vs. discovered concepts (a core rule). |
| [agent-memory.md](agent-memory.md) | **Phase 1** — the persistent agent-memory data model. |
| [storage.md](storage.md) | Storage architecture (Postgres, pgvector, R2, Redis) + post storage strategy. |
| [supabase-r2-setup.md](supabase-r2-setup.md) | **Phase 1** — manual Supabase/R2 steps for staging/prod. |
| [scraper-lifecycle.md](scraper-lifecycle.md) | Historical bootstrap vs. daily collection lifecycle. |
| [agent-lifecycle.md](agent-lifecycle.md) | AI Crawler conceptual lifecycle & the five memory classes. |
| [environment.md](environment.md) | Every environment variable. |
| [local-development.md](local-development.md) | Local development **and** testing. |
| [phases.md](phases.md) | Planned phase boundaries. |

See also the top-level [`README.md`](../README.md) and
[`CONTRIBUTING.md`](../CONTRIBUTING.md).
