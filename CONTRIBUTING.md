# Contributing to TIDE

## Development conventions

**Architecture rule (most important):** dependencies point *into* `contracts/`.
Subsystems (`scrapers`, `intelligence`, `graph`, `agent`, `workers`) and the
`backend` host depend on `contracts`; `contracts` depends on nothing but the
standard library and Pydantic. Never create a circular or reverse dependency.

- **One responsibility per subsystem.** If you're unsure where code goes, re-read
  [`docs/architecture.md`](docs/architecture.md). Do **not** create a shared
  "utils" dumping ground — domain-neutral shared types go in `contracts`,
  cross-cutting host concerns in `backend/core`.
- **Program to interfaces.** New external capability = a new port in `contracts`
  plus an adapter in the owning subsystem. Inject dependencies (constructor
  injection) so implementations — including test stubs — swap freely.
- **No provider lock-in.** Anything that touches an LLM or embeddings must go
  through `LLMProvider` / `EmbeddingProvider`.

## Code quality

- **Type hints everywhere** (`mypy` is configured; run `make typecheck`).
- **Lint & format with Ruff:** `make lint`, `make format`.
- **Structured logging** via `backend.core.logging.get_logger` — no bare `print`.
- **Never hardcode secrets.** All config via env vars / `.env` (git-ignored).
  Add new settings to `backend/core/config.py` **and** `.env.example`.

Run everything at once:

```bash
make check   # ruff + mypy + pytest
```

## Tests

- Add tests under `tests/` (backend) or `frontend/__tests__/` (frontend).
- Tests must **not** require an external service. Use the in-memory reference
  adapters (`graph/repositories.py`) or your own stubs.
- Keep `/health` dependency-free.

## Commits & branches

- Work on a feature branch; keep `main` releasable.
- Reference the phase you're working in (see [`docs/phases.md`](docs/phases.md)).
  Do not implement work from a later phase without agreement.

## Adding a subsystem implementation (later phases)

1. Define/confirm the port in `contracts/`.
2. Implement the adapter in the owning subsystem package.
3. Register it where applicable (e.g. `scrapers/registry.py`).
4. Wire it at the composition root (`backend/main.py`) via settings.
5. Add tests and update the relevant doc in `docs/`.
