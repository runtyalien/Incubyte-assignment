"""Recording a pay change.

This is the only code that can damage the history, so most of these are about
what it refuses rather than what it writes.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models import PayChangeReason
from app.repository import compensation as comp
from app.repository import fx
from app.services import pay
from app.services.pay import ConflictingPayChange, EmployeeNotFound, InvalidPayChange
from tests.factories import add_employee, add_location, add_pay

TODAY = date(2024, 6, 1)
HIRED = date(2021, 1, 4)


@pytest.fixture
def employee(session, org):
    person = add_employee(session, org, hired_on=HIRED)
    add_pay(session, person, HIRED, "100000", reason=PayChangeReason.HIRE)
    return person


def give_raise(session, employee, amount="110000", on=date(2024, 1, 1), **kwargs):
    kwargs.setdefault("reason", PayChangeReason.MERIT)
    return pay.record_change(
        session, employee.id, effective_from=on, amount=Decimal(amount), today=TODAY, **kwargs
    )


def test_a_raise_becomes_the_current_pay(session, employee):
    give_raise(session, employee, "110000", on=date(2024, 1, 1))

    current = comp.current(session, employee.id, as_of=TODAY)

    assert current.amount_minor == 11_000_000
    assert current.reason is PayChangeReason.MERIT


def test_the_previous_record_is_left_alone(session, employee):
    before = comp.history(session, employee.id)[0]
    original = (before.id, before.amount_minor, before.effective_from)

    give_raise(session, employee)

    after = comp.history(session, employee.id)[0]
    assert (after.id, after.amount_minor, after.effective_from) == original
    assert len(comp.history(session, employee.id)) == 2


def test_currency_defaults_to_what_the_employee_is_paid_in(session, employee):
    record = give_raise(session, employee)

    assert record.currency == "USD"


def test_an_unknown_employee_is_rejected(session, org):
    with pytest.raises(EmployeeNotFound):
        pay.record_change(
            session,
            999,
            effective_from=TODAY,
            amount=Decimal("1000"),
            reason=PayChangeReason.MERIT,
            today=TODAY,
        )


def test_a_date_before_the_hire_date_is_rejected(session, employee):
    with pytest.raises(InvalidPayChange, match="before"):
        give_raise(session, employee, on=date(2020, 12, 31))


def test_the_hire_date_itself_is_allowed_as_a_correction(session, employee):
    record = give_raise(session, employee, on=HIRED, reason=PayChangeReason.CORRECTION)

    assert record.effective_from == HIRED


def test_a_negative_amount_is_rejected(session, employee):
    with pytest.raises(InvalidPayChange, match="greater than zero"):
        give_raise(session, employee, "-5000")


def test_a_zero_amount_is_rejected(session, employee):
    with pytest.raises(InvalidPayChange, match="greater than zero"):
        give_raise(session, employee, "0")

def test_a_fraction_smaller_than_a_cent_is_rejected(session, employee):
    with pytest.raises(InvalidPayChange, match="too many decimal places"):
        give_raise(session, employee, "10000.001")


def test_a_currency_the_employee_is_not_paid_in_is_rejected(session, employee):
    # Changing someone's currency is a relocation, not a pay change.
    with pytest.raises(InvalidPayChange, match="paid in USD"):
        give_raise(session, employee, currency="EUR")


def test_a_change_after_someone_has_left_is_rejected(session, org):
    leaver = add_employee(session, org, hired_on=HIRED, left_on=date(2023, 6, 1))
    add_pay(session, leaver, HIRED, "100000", reason=PayChangeReason.HIRE)

    with pytest.raises(InvalidPayChange, match="left on"):
        give_raise(session, leaver, on=date(2023, 7, 1))


def test_a_change_before_someone_left_is_allowed(session, org):
    leaver = add_employee(session, org, hired_on=HIRED, left_on=date(2023, 6, 1))
    add_pay(session, leaver, HIRED, "100000", reason=PayChangeReason.HIRE)

    record = give_raise(session, leaver, on=date(2023, 1, 1))

    assert record.effective_from == date(2023, 1, 1)


def test_a_date_far_in_the_future_is_rejected(session, employee):
    # 2206 instead of 2026 is a plausible slip and would sit on the record
    # forever without ever taking effect.
    with pytest.raises(InvalidPayChange, match="years ahead"):
        give_raise(session, employee, on=date(2206, 1, 1))


def test_a_raise_dated_next_year_is_allowed_and_not_yet_in_effect(session, employee):
    future = date(2025, 4, 1)

    record = give_raise(session, employee, "130000", on=future)

    assert record.effective_from == future
    assert comp.current(session, employee.id, as_of=TODAY).amount_minor == 10_000_000
    assert comp.current(session, employee.id, as_of=future).amount_minor == 13_000_000


def test_a_second_record_on_the_same_day_is_refused(session, employee):
    give_raise(session, employee, "110000", on=date(2024, 1, 1))

    with pytest.raises(ConflictingPayChange, match="already takes effect"):
        give_raise(session, employee, "110000", on=date(2024, 1, 1))


def test_a_same_day_correction_is_allowed_and_wins(session, employee):
    give_raise(session, employee, "110000", on=date(2024, 1, 1))

    corrected = give_raise(
        session, employee, "112000", on=date(2024, 1, 1), reason=PayChangeReason.CORRECTION
    )

    current = comp.current(session, employee.id, as_of=TODAY)
    assert current.id == corrected.id
    assert current.amount_minor == 11_200_000
    # Both are still on record; the mistake is visible rather than erased.
    assert len(comp.history(session, employee.id)) == 3


def test_the_rate_is_snapshotted_at_the_effective_date(session, org):
    india = add_location(session, "IN", "India", "INR")
    person = add_employee(session, org, hired_on=HIRED, location_id=india.id)
    _rate(session, "INR", date(2021, 1, 1), 14_000)
    _rate(session, "INR", date(2024, 1, 1), 12_000)

    record = pay.record_change(
        session,
        person.id,
        effective_from=date(2022, 1, 1),
        amount=Decimal("2000000"),
        reason=PayChangeReason.MERIT,
        today=TODAY,
    )

    # The 2021 rate was still in force in 2022, so 2,000,000 rupees at 0.014.
    assert record.fx_rate_micros == 14_000
    assert record.base_amount_minor == 2_800_000


def test_a_currency_with_no_rate_on_that_date_is_rejected(session, org):
    india = add_location(session, "IN", "India", "INR")
    person = add_employee(session, org, hired_on=HIRED, location_id=india.id)
    _rate(session, "INR", date(2024, 1, 1), 12_000)

    with pytest.raises(fx.NoRateAvailable):
        pay.record_change(
            session,
            person.id,
            effective_from=date(2022, 1, 1),
            amount=Decimal("2000000"),
            reason=PayChangeReason.MERIT,
            today=TODAY,
        )


def test_the_base_currency_needs_no_rate_row(session, employee):
    record = give_raise(session, employee, "110000")

    assert record.fx_rate_micros == 1_000_000
    assert record.base_amount_minor == 11_000_000


def _rate(session, currency, effective_from, micros):
    from app.models import FxRate

    session.add(FxRate(currency=currency, effective_from=effective_from, rate_micros=micros))
    session.flush()
