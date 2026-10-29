from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_session
from app.main import create_app


def test_health_reports_ok(client):
    res = client.get("/api/health")

    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["database"] == "up"


def test_health_route_is_published(client):
    # A router that fails to mount otherwise only shows up as a 404 somewhere else.
    res = client.get("/openapi.json")

    assert res.status_code == 200
    assert "/api/health" in res.json()["paths"]


def test_health_asks_the_database_rather_than_assuming(client, count_queries):
    # Without this, "up" could be a constant and the check would pass forever.
    with count_queries() as counted:
        client.get("/api/health")

    assert counted["queries"] >= 1


class Unreachable:
    """Stands in for a session whose database has gone away."""

    def execute(self, *_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def test_health_reports_503_when_the_database_is_unreachable():
    api = create_app()
    api.dependency_overrides[get_session] = Unreachable

    with TestClient(api) as unhealthy:
        res = unhealthy.get("/api/health")

    assert res.status_code == 503
    assert res.json()["status"] == "degraded"
    assert res.json()["database"] == "down"
