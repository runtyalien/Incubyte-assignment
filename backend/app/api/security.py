"""Who is allowed to ask.

One shared key, checked on every salary route. That is deliberately not an
identity system: there are no users, no roles and no sessions here, because
the thing being protected is a demonstration dataset and anything more would
be scaffolding nobody asked for. What it does buy is that the deployed API is
not an open endpoint serving ten thousand salaries to whoever finds the URL.

See docs/adr/0005 for what this gives up.
"""

import hmac
import logging
import time
from collections import OrderedDict, deque
from typing import Annotated

from fastapi import Header, HTTPException, Request, status

from app.config import get_settings

log = logging.getLogger(__name__)

API_KEY_HEADER = "X-API-Key"

# Ten wrong keys inside a minute is nobody's typo.
MAX_FAILURES = 10
WINDOW_SECONDS = 60.0

# A cap so a flood of distinct addresses cannot grow this without limit.
MAX_TRACKED_CLIENTS = 1024


class FailedAttempts:
    """Failed key attempts per client, in this process and nowhere else.

    Enough to make guessing a key over the network pointless against a single
    instance, which is what this deployment is. It is explicitly not a
    distributed rate limiter: a second instance would count separately and a
    restart forgets everything. Doing better needs shared state, and shared
    state is infrastructure this does not otherwise need.
    """

    def __init__(self) -> None:
        self._by_client: OrderedDict[str, deque[float]] = OrderedDict()

    def record(self, client: str, now: float) -> None:
        attempts = self._by_client.setdefault(client, deque())
        attempts.append(now)
        self._by_client.move_to_end(client)

        while len(self._by_client) > MAX_TRACKED_CLIENTS:
            self._by_client.popitem(last=False)

    def blocked(self, client: str, now: float) -> bool:
        attempts = self._by_client.get(client)
        if not attempts:
            return False

        cutoff = now - WINDOW_SECONDS
        while attempts and attempts[0] < cutoff:
            attempts.popleft()

        return len(attempts) >= MAX_FAILURES

    def forget(self) -> None:
        self._by_client.clear()


failures = FailedAttempts()


def require_api_key(
    request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    expected = get_settings().api_key

    # No key configured means local development. Config refuses this in
    # production, so there is no path where this quietly opens a deployment.
    if not expected:
        return

    client = _caller(request)
    now = time.monotonic()

    if failures.blocked(client, now):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again shortly.",
        )

    if x_api_key is None or not _matches(x_api_key, expected):
        failures.record(client, now)
        log.warning("rejected a request to %s with no valid key", request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"A valid {API_KEY_HEADER} header is required.",
            headers={"WWW-Authenticate": API_KEY_HEADER},
        )


def _caller(request: Request) -> str:
    """Who to count this against.

    Behind a proxy the peer address is the proxy's, not the caller's, and on
    Render it varies between requests -- which scattered attempts across
    separate counters and meant the limit never bit. X-Forwarded-For is the
    caller as the proxy saw them.

    Trusting that header is only defensible because the container is not
    reachable except through the proxy. Exposed directly, a caller could set
    it per request and never be counted twice.
    """
    first_hop = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if first_hop:
        return first_hop

    return request.client.host if request.client else "unknown"


def _matches(offered: str, expected: str) -> bool:
    # Bytes rather than str: compare_digest raises on non-ASCII strings, and a
    # header is whatever the caller sent.
    return hmac.compare_digest(offered.encode("utf-8"), expected.encode("utf-8"))
