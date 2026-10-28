"""Smoke test proving the app boots and the router is mounted."""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_schema_is_served() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/health" in response.json()["paths"]
