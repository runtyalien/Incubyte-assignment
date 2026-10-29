"""Who gets in, and who does not.

The interesting cases are the refusals. A gate that lets the right request
through is easy to get right by accident; one that reliably turns the wrong
one away is the part worth pinning down.
"""

from datetime import date

import pytest

from app.api.security import MAX_FAILURES, failures
from app.config import get_settings
from app.models import PayChangeReason
from app.repository import compensation as comp
from tests.factories import add_employee, add_pay

KEY = "test-key-not-a-real-one"
WRONG = "test-key-not-a-real-onf"  # one character out, same length

HIRED = date(2021, 1, 4)

SALARY_ROUTES = [
    "/api/employees",
    "/api/employees/1",
    "/api/analytics/overview",
    "/api/analytics/distribution?by=country",
    "/api/reference",
]


@pytest.fixture
def guarded(monkeypatch):
    """The service as deployed: a key is configured and therefore required."""
    monkeypatch.setenv("API_KEY", KEY)
    get_settings.cache_clear()
    failures.forget()
    yield
    get_settings.cache_clear()
    failures.forget()


@pytest.fixture
def person(session, org):
    employee = add_employee(session, org, hired_on=HIRED)
    add_pay(session, employee, HIRED, "100000", reason=PayChangeReason.HIRE)
    return employee


@pytest.mark.parametrize("route", SALARY_ROUTES)
def test_salary_routes_refuse_an_anonymous_caller(client, guarded, route):
    res = client.get(route)

    assert res.status_code == 401


@pytest.mark.parametrize("route", SALARY_ROUTES)
def test_salary_routes_refuse_the_wrong_key(client, guarded, route):
    res = client.get(route, headers={"X-API-Key": WRONG})

    assert res.status_code == 401


def test_the_right_key_gets_through(client, guarded, person):
    res = client.get("/api/employees", headers={"X-API-Key": KEY})

    assert res.status_code == 200
    assert res.json()["items"]


def test_a_refusal_does_not_describe_the_key(client, guarded):
    res = client.get("/api/employees")

    # Saying how long it is, or what it starts with, is free help.
    assert KEY not in res.text
    assert res.json()["detail"] == "A valid X-API-Key header is required."


def test_health_stays_open(client, guarded):
    # Whatever is watching the service has no key, and this tells it nothing
    # about anybody's pay.
    res = client.get("/api/health")

    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_an_anonymous_pay_change_is_refused_and_writes_nothing(client, guarded, session, person):
    before = len(comp.history(session, person.id))

    res = client.post(
        f"/api/employees/{person.id}/compensation",
        json={
            "amount": "120000",
            "currency": "USD",
            "effective_from": "2024-01-01",
            "reason": "merit",
        },
    )

    assert res.status_code == 401
    assert len(comp.history(session, person.id)) == before


def test_repeated_wrong_keys_are_throttled(client, guarded):
    for _ in range(MAX_FAILURES):
        assert client.get("/api/employees", headers={"X-API-Key": WRONG}).status_code == 401

    res = client.get("/api/employees", headers={"X-API-Key": WRONG})

    assert res.status_code == 429


def test_throttling_does_not_spare_the_right_key(client, guarded, person):
    # The limit is on the caller, not on the guess. Someone who has just made
    # ten wrong attempts does not get a free pass by finally getting it right,
    # which is the whole point of slowing them down.
    for _ in range(MAX_FAILURES):
        client.get("/api/employees", headers={"X-API-Key": WRONG})

    res = client.get("/api/employees", headers={"X-API-Key": KEY})

    assert res.status_code == 429


def test_without_a_key_configured_the_api_is_open(client, person):
    # Local development. The config refuses this combination in production,
    # which is what stops it reaching a deployment.
    assert get_settings().api_key == ""

    assert client.get("/api/employees").status_code == 200


def wrong(client, forwarded=None):
    headers = {"X-API-Key": WRONG}
    if forwarded:
        headers["X-Forwarded-For"] = forwarded
    return client.get("/api/employees", headers=headers)


def test_a_caller_is_blocked_after_enough_wrong_keys(client, guarded):
    for _ in range(MAX_FAILURES):
        assert wrong(client, "203.0.113.5").status_code == 401

    assert wrong(client, "203.0.113.5").status_code == 429


def test_two_callers_attempts_do_not_combine(client, guarded):
    """The bug this exists for.

    Behind a proxy every request arrives from the proxy's address, so counting
    that address pools unrelated callers together. On Render the address also
    varied between requests, which scattered one caller across several
    counters and meant the limit never bit at all. Half the budget each must
    leave both of them free.
    """
    for _ in range(MAX_FAILURES // 2):
        wrong(client, "203.0.113.5")
        wrong(client, "198.51.100.7")

    assert wrong(client, "203.0.113.5").status_code == 401
    assert wrong(client, "198.51.100.7").status_code == 401


def test_one_caller_cannot_lock_out_another_behind_the_same_proxy(client, guarded):
    for _ in range(MAX_FAILURES):
        wrong(client, "203.0.113.5")

    assert wrong(client, "198.51.100.7").status_code == 401


def test_the_first_hop_identifies_the_caller_not_the_last(client, guarded):
    # A chained header lists the original caller first and the proxies after,
    # so reading the wrong end pools everyone behind one proxy again.
    for _ in range(MAX_FAILURES // 2):
        wrong(client, "203.0.113.5, 10.0.0.1")
        wrong(client, "198.51.100.7, 10.0.0.1")

    assert wrong(client, "203.0.113.5, 10.0.0.1").status_code == 401


def test_an_empty_forwarded_header_falls_back_to_the_peer(client, guarded):
    # Not a proxy at all, so there is nothing better to count than the peer.
    for _ in range(MAX_FAILURES):
        assert wrong(client, "   ").status_code == 401

    assert wrong(client).status_code == 429
