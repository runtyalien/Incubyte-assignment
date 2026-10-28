"""Recording a pay change.

This is the only code in the system that can damage the compensation history,
so the rules live here rather than in a route handler, and they are the point
of the module. Records are appended and never updated: a mistake is corrected
by another record, which the timeline then shows honestly instead of pretending
it never happened.
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.money import has_valid_precision, to_base, to_minor
from app.models import CompensationRecord, Employee, PayChangeReason
from app.repository import fx

# A date typed as 2206 instead of 2026 is a plausible slip, and an effective
# date two centuries out would sit in the history forever without ever taking
# effect. Entering a raise a year or two ahead is legitimate; this is not.
MAX_YEARS_AHEAD = 2


class PayChangeRejected(Exception):
    """Base for everything the caller could have got right."""


class EmployeeNotFound(PayChangeRejected):
    def __init__(self, employee_id: int):
        super().__init__(f"No employee with id {employee_id}")


class InvalidPayChange(PayChangeRejected):
    pass


class ConflictingPayChange(PayChangeRejected):
    pass


def record_change(
    session: Session,
    employee_id: int,
    *,
    effective_from: date,
    amount: Decimal,
    reason: PayChangeReason,
    currency: str | None = None,
    note: str | None = None,
    today: date | None = None,
) -> CompensationRecord:
    today = today or date.today()

    employee = session.get(Employee, employee_id)
    if employee is None:
        raise EmployeeNotFound(employee_id)

    currency = currency or employee.location.currency
    _check(employee, effective_from, amount, currency, today)
    _check_not_a_duplicate(session, employee_id, effective_from, reason)

    minor = to_minor(amount, currency)
    rate = fx.rate_on(session, currency, effective_from)

    record = CompensationRecord(
        employee_id=employee_id,
        effective_from=effective_from,
        amount_minor=minor,
        currency=currency,
        # Snapshotted at the effective date, not today's rate, so a report
        # about this change says the same thing next year. See docs/adr/0003.
        base_amount_minor=to_base(minor, currency, rate),
        fx_rate_micros=rate,
        reason=reason,
        note=note,
    )

    session.add(record)
    session.commit()
    return record


def _check(
    employee: Employee, effective_from: date, amount: Decimal, currency: str, today: date
) -> None:
    if amount <= 0:
        raise InvalidPayChange("Amount must be greater than zero")

    paid_in = employee.location.currency
    if currency != paid_in:
        raise InvalidPayChange(
            f"{employee.staff_number} is paid in {paid_in}, not {currency}. "
            "Moving someone to another currency means moving their location."
        )
    
    if not has_valid_precision(amount, currency):
        raise InvalidPayChange(
            f"Amount has too many decimal places for {currency}"
        )

    if effective_from < employee.hired_on:
        raise InvalidPayChange(
            f"Effective date {effective_from} is before {employee.staff_number} "
            f"was hired on {employee.hired_on}"
        )

    if employee.left_on and effective_from > employee.left_on:
        raise InvalidPayChange(
            f"{employee.staff_number} left on {employee.left_on}; "
            f"a change cannot take effect after that"
        )

    horizon = today + timedelta(days=365 * MAX_YEARS_AHEAD)
    if effective_from > horizon:
        raise InvalidPayChange(
            f"Effective date {effective_from} is more than {MAX_YEARS_AHEAD} years ahead"
        )


def _check_not_a_duplicate(
    session: Session, employee_id: int, effective_from: date, reason: PayChangeReason
) -> None:
    """Two records on one day are allowed, but only deliberately.

    The later row wins, so a same-day correction does what it should. An
    accidental resubmission would silently do the same thing, which is why it
    has to say it is a correction.
    """
    if reason is PayChangeReason.CORRECTION:
        return

    clash = session.scalar(
        select(CompensationRecord.id)
        .where(
            CompensationRecord.employee_id == employee_id,
            CompensationRecord.effective_from == effective_from,
        )
        .limit(1)
    )

    if clash is not None:
        raise ConflictingPayChange(
            f"A pay record already takes effect on {effective_from}. "
            "Record it as a correction if that is deliberate."
        )
