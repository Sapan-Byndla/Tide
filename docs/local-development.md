# Local Development & Testing

Covers running the project locally and the testing foundation.

## Prerequisites

- Python **3.11+**
- Node **20+** (22 recommended) for the frontend
- Docker + Docker Compose (optional, for the full environment)

## Option 1 — Run natively (fastest for the backend)

```bash
# 1. Configure environment
cp .env.example .env

# 2. Backend: create venv + install (editable, with dev deps)
make install          # or: python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# 3. Run the API (health at http://localhost:8000/health, docs at /docs)
make dev              # uvicorn backend.main:app --reload
```

Frontend:

```bash
make frontend-install # cd frontend && npm install
make frontend-dev     # cd frontend && npm run dev  -> http://localhost:3000
```

## Option 2 — Full environment with Docker Compose

Brings up Postgres (with pgvector), Redis, the backend, and the frontend:

```bash
cp .env.example .env
make up               # docker compose up --build
make ps               # service status
make logs             # tail backend logs
make down             # stop
```

> Phase 0 note: the backend does **not** connect to Postgres/Redis yet. They run
> so the local environment matches the target architecture; adapters plug in
> later without changing compose.

## Common developer commands (`make help`)

| Command | Does |
| --- | --- |
| `make install` | Create `.venv`, install backend + dev deps (editable). |
| `make dev` | Run FastAPI with autoreload. |
| `make test` | Run the pytest suite. |
| `make cov` | Tests with coverage. |
| `make lint` / `make format` | Ruff lint / format. |
| `make typecheck` | mypy. |
| `make check` | lint + typecheck + tests. |
| `make up` / `make down` | Start / stop docker compose. |
| `make migrate` | Apply Alembic migrations (no-op until models exist). |
| `make frontend-*` | Frontend install/dev/test. |

## Testing

The Phase 0 test suite verifies the scaffold is sound, not features.

**Backend (pytest):**

- `tests/test_imports.py` — every subsystem package imports cleanly.
- `tests/test_config.py` — configuration loads, types, composes the DB URL.
- `tests/test_contracts.py` — all ports exist, are abstract, are implementable.
- `tests/test_health.py` — the app starts and `/health` works with no external
  service.
- `tests/test_workers.py` — historical vs. daily windowing is correct & separate.
- `tests/test_graph_repositories.py` — the in-memory reference adapters behave.

Run:

```bash
make test             # or: .venv/bin/pytest
```

Tests never touch an external service: the DB engine is lazy, `/health` has no
dependencies, and `TIDE_ENV=test` is set in `tests/conftest.py`.

**Frontend (Vitest):**

```bash
make frontend-test    # cd frontend && npm test
```

`frontend/__tests__/api.test.ts` unit-tests pure client helpers without a running
backend.

See [phases](phases.md) for what is intentionally out of scope.
