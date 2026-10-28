"""Reading pay out of an append-only history.

There is no current-salary column, so "what does this person earn" is the most
recent record that has already taken effect. See docs/adr/0001.
"""

from collections.abc import Iterable
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.models import CompensationRecord

# Later rows win on a shared effective date, so a same-day correction beats the
# record it corrects instead of the result being down to row order.
_LATEST_FIRST = (CompensationRecord.effective_from.desc(), CompensationRecord.id.desc())


def current(
    session: Session, employee_id: int, as_of: date | None = None
) -> CompensationRecord | None:
    as_of = as_of or date.today()

    stmt = (
        select(CompensationRecord)
        .where(
            CompensationRecord.employee_id == employee_id,
            CompensationRecord.effective_from <= as_of,
        )
        .order_by(*_LATEST_FIRST)
        .limit(1)
    )
    return session.scalars(stmt).first()


def current_many(
    session: Session, employee_ids: Iterable[int], as_of: date | None = None
) -> dict[int, CompensationRecord]:
    """The same lookup for a page of employees, in one round trip.

    Doing this per employee is the obvious N+1 in this codebase, so the rank is
    computed in SQL and only the winners come back. Employees with nothing in
    effect are absent rather than mapped to None — a new joiner whose start date
    has not arrived has no salary, which is different from a salary of zero.
    """
    ids = list(employee_ids)
    if not ids:
        return {}

    as_of = as_of or date.today()

    ranked = (
        select(
            CompensationRecord,
            func.row_number()
            .over(partition_by=CompensationRecord.employee_id, order_by=_LATEST_FIRST)
            .label("rank"),
        )
        .where(
            CompensationRecord.employee_id.in_(ids),
            CompensationRecord.effective_from <= as_of,
        )
        .subquery()
    )

    latest = aliased(CompensationRecord, ranked)
    rows = session.scalars(select(latest).where(ranked.c.rank == 1))

    return {row.employee_id: row for row in rows}


def history(session: Session, employee_id: int) -> list[CompensationRecord]:
    """Everything on record, oldest first, including changes dated ahead."""
    stmt = (
        select(CompensationRecord)
        .where(CompensationRecord.employee_id == employee_id)
        .order_by(CompensationRecord.effective_from, CompensationRecord.id)
    )
    return list(session.scalars(stmt))
