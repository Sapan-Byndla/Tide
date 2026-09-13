"""FastAPI application factory — the TIDE composition root.

This is where the otherwise-decoupled subsystems are wired together behind the
HTTP surface. In Phase 0 the app only serves system endpoints (health/info); it
starts cleanly with no external service available.

Run locally::

    uvicorn backend.main:app --reload

or ``make dev``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.router import api_router
from backend.core.config import Settings, get_settings
from backend.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks. No external connections are opened in Phase 0."""
    settings: Settings = app.state.settings
    log = get_logger("tide.startup")
    log.info("tide.starting", env=settings.env.value, phase="0")
    yield
    log.info("tide.stopping")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return the FastAPI application.

    Accepting ``settings`` makes the app easy to construct with overrides in
    tests (dependency injection at the composition root).
    """
    settings = settings or get_settings()
    configure_logging(level=settings.log_level, json_logs=settings.log_json)

    app = FastAPI(
        title="TIDE API",
        version="0.0.0",
        description="Concept Graph and Trend Intelligence System (Phase 0 scaffold).",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.include_router(api_router)
    return app


#: ASGI application instance used by uvicorn / docker.
app = create_app()
