from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db  # noqa: F401  — importing registers the SQLite foreign-key pragma
from app.models import Base
from tests.factories import Org


@pytest.fixture
def engine():
    # StaticPool keeps every connection pointed at the same in-memory database;
    # without it each checkout gets a fresh, empty one.
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine, expire_on_commit=False) as s:
        yield s


@pytest.fixture
def org(session):
    return Org(session)


@pytest.fixture
def count_queries(engine):
    """Guards against N+1s, which only show up as slowness at 10,000 rows."""

    @contextmanager
    def counter():
        seen = {"queries": 0}

        def tick(*_args, **_kwargs):
            seen["queries"] += 1

        event.listen(engine, "before_cursor_execute", tick)
        try:
            yield seen
        finally:
            event.remove(engine, "before_cursor_execute", tick)

    return counter
