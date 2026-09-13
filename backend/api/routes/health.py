"""Health & readiness endpoints.

``/health`` is a pure liveness check: it must succeed with no external
dependency (no DB, no Redis, no network), so it can gate container startup and
smoke tests even in Phase 0.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.config import Settings, get_settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    env: str
    version: str


class InfoResponse(BaseModel):
    name: str
    phase: str
    description: str


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    """Return process liveness. Never touches an external service."""
    settings: Settings = get_settings()
    return HealthResponse(status="ok", env=settings.env.value, version="0.0.0")


@router.get("/", response_model=InfoResponse, summary="Service info")
async def info() -> InfoResponse:
    return InfoResponse(
        name="TIDE",
        phase="0",
        description="Concept Graph and Trend Intelligence System — scaffold.",
    )
