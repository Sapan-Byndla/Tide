"""TIDE backend — the API host and composition root.

The backend does not own domain logic. It configures the process (settings,
logging, DB session), exposes the HTTP surface, and wires the subsystem ports
(``scrapers``, ``intelligence``, ``graph``, ``agent``, ``workers``) together.
Domain contracts live in ``contracts``; implementations live in their subsystem
packages. This keeps the dependency direction pointing *into* the stable core.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

__all__ = ["create_app"]


def create_app() -> FastAPI:
    """Lazy re-export of the app factory to avoid importing FastAPI eagerly."""
    from backend.main import create_app as _create_app

    return _create_app()
