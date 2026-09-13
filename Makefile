# TIDE developer commands.
# Run `make help` for a list.

SHELL := /bin/bash
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---- Python backend ----
.PHONY: venv
venv: ## Create the Python virtualenv
	python3 -m venv $(VENV)

.PHONY: install
install: venv ## Install backend + dev dependencies (editable)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

.PHONY: env
env: ## Create .env from .env.example if missing
	@test -f .env || (cp .env.example .env && echo "created .env from .env.example")

.PHONY: dev
dev: ## Run the FastAPI backend with autoreload
	$(VENV)/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Dedicated, DISPOSABLE local test database (never a real/remote DB).
TEST_DATABASE_URL ?= postgresql+psycopg://tide:tide_local_password@localhost:55432/tide

.PHONY: test
test: ## Run the test suite (DB tests skip unless TIDE_TEST_DATABASE_URL is set)
	$(VENV)/bin/pytest

.PHONY: test-db
test-db: ## Run the full suite against the local test database (docker: db-up-test)
	TIDE_TEST_DATABASE_URL=$(TEST_DATABASE_URL) $(VENV)/bin/pytest

.PHONY: db-up-test
db-up-test: ## Start a disposable local Postgres for tests on port 55432
	TIDE_POSTGRES_PORT=55432 docker compose up -d postgres

.PHONY: cov
cov: ## Run tests with coverage
	$(VENV)/bin/pytest --cov=contracts --cov=backend --cov=scrapers \
		--cov=intelligence --cov=graph --cov=agent --cov=workers

.PHONY: lint
lint: ## Lint with ruff
	$(VENV)/bin/ruff check .

.PHONY: format
format: ## Format with ruff
	$(VENV)/bin/ruff format .

.PHONY: typecheck
typecheck: ## Static type check with mypy
	$(VENV)/bin/mypy

.PHONY: check
check: lint typecheck test ## Run lint + typecheck + tests

# ---- Database ----
.PHONY: db-up
db-up: ## Start only the local PostgreSQL (pgvector) container
	docker compose up -d postgres

.PHONY: db-down
db-down: ## Stop the local PostgreSQL container
	docker compose stop postgres

.PHONY: migrate
migrate: ## Apply Alembic migrations to head (empty DB -> full schema)
	$(VENV)/bin/alembic upgrade head

.PHONY: downgrade
downgrade: ## Roll back the last migration
	$(VENV)/bin/alembic downgrade -1

.PHONY: revision
revision: ## Autogenerate an Alembic migration (msg="...")
	$(VENV)/bin/alembic revision --autogenerate -m "$(msg)"

.PHONY: import-seeds
import-seeds: ## Import curated seed_list.yaml into the database (idempotent)
	$(VENV)/bin/python -m scripts.import_seeds

.PHONY: load-demo
load-demo: ## Load deterministic development/demo data
	$(VENV)/bin/python -m scripts.load_demo

.PHONY: db-bootstrap
db-bootstrap: migrate import-seeds load-demo ## Migrate + import seeds + load demo

# ---- Frontend ----
.PHONY: frontend-install
frontend-install: ## Install frontend dependencies
	cd frontend && npm install

.PHONY: frontend-dev
frontend-dev: ## Run the Next.js dev server
	cd frontend && npm run dev

.PHONY: frontend-test
frontend-test: ## Run frontend tests
	cd frontend && npm test

# ---- Docker ----
.PHONY: up
up: ## Start the full local environment (docker compose)
	docker compose up --build

.PHONY: down
down: ## Stop the local environment
	docker compose down

.PHONY: ps
ps: ## Show compose service status
	docker compose ps

.PHONY: logs
logs: ## Tail backend logs
	docker compose logs -f backend

.PHONY: clean
clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache **/__pycache__ *.egg-info build dist
