# TIDE backend image (Phase 0).
#
# Builds the FastAPI host with all subsystem packages installed as one editable
# distribution. Kept intentionally simple — no external service SDKs are baked in
# yet. Build context is the repository root.

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps kept minimal; build tools only where needed for wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better layer caching.
COPY pyproject.toml README.md ./
# Copy the package sources needed for an editable install.
COPY contracts ./contracts
COPY scrapers ./scrapers
COPY intelligence ./intelligence
COPY graph ./graph
COPY agent ./agent
COPY workers ./workers
COPY backend ./backend
COPY alembic.ini ./alembic.ini

RUN pip install --upgrade pip && pip install -e ".[dev]"

EXPOSE 8000

# A non-root user for runtime.
RUN useradd --create-home --uid 10001 tide
USER tide

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
