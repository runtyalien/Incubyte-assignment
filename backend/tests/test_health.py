from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health_reports_ok():
    res = client.get("/api/health")

    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_health_route_is_published():
    # A router that fails to mount otherwise only shows up as a 404 somewhere else.
    res = client.get("/openapi.json")

    assert res.status_code == 200
    assert "/api/health" in res.json()["paths"]
