"""The backend starts and its health endpoint works — with no external service."""

from __future__ import annotations


def test_app_factory_builds(app) -> None:  # type: ignore[no-untyped-def]
    assert app.title == "TIDE API"


def test_health_endpoint(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "env" in body
    assert "version" in body


def test_info_endpoint(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["name"] == "TIDE"


def test_openapi_available(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert "/health" in resp.json()["paths"]
