"""Top-level API router.

Aggregates the per-resource routers. As subsystems expose read APIs in later
phases (graph queries, trend reports), their routers are included here.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)
