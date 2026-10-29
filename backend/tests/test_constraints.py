"""What the database refuses on its own.

The service layer checks these too, and in normal use that is what the API
hits. These are the backstop for everything that does not go through it: a
seed run, a migration, a correction applied by hand against the file. A rule
that only lives in Python is a rule that holds until someone opens a shell.
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import CompensationRecord, PayChangeReason, SalaryBand
from tests.factories import PAR, add_employee

HIRED = date(2021, 1, 4)


def comp(employee, **overrides):
    values = {
        "employee_id": employee.id,
        "effective_from": date(2022, 1, 3),
        "amount_minor": 10_000_000,
        "currency": "USD",
        "base_amount_minor": 10_000_000,
        "fx_rate_micros": PAR,
        "reason": PayChangeReason.MERIT,
    }
    return CompensationRecord(**{**values, **overrides})


def band(org, **overrides):
    values = {
        "location_id": org.location.id,
        "job_family_id": org.family.id,
        "job_level_id": org.level.id,
        "currency": "USD",
        "min_minor": 8_000_000,
        "mid_minor": 10_000_000,
        "max_minor": 12_000_000,
    }
    return SalaryBand(**{**values, **overrides})


def test_leaving_before_being_hired_is_refused(session, org):
    with pytest.raises(IntegrityError, match="ck_employee_left_on_after_hired_on"):
        add_employee(session, org, hired_on=HIRED, left_on=date(2020, 12, 31))


def test_leaving_on_the_hire_date_is_allowed(session, org):
    # Someone who starts and leaves the same day is odd but not corrupt data.
    person = add_employee(session, org, hired_on=HIRED, left_on=HIRED)

    assert person.left_on == HIRED


def test_a_salary_of_zero_is_refused(session, org):
    person = add_employee(session, org, hired_on=HIRED)
    session.add(comp(person, amount_minor=0))

    with pytest.raises(IntegrityError, match="ck_compensation_amount_positive"):
        session.flush()


def test_a_negative_salary_is_refused(session, org):
    person = add_employee(session, org, hired_on=HIRED)
    session.add(comp(person, amount_minor=-1))

    with pytest.raises(IntegrityError, match="ck_compensation_amount_positive"):
        session.flush()


def test_a_non_positive_converted_amount_is_refused(session, org):
    # A zero here would quietly drop someone out of every total in USD while
    # their local salary still looked right.
    person = add_employee(session, org, hired_on=HIRED)
    session.add(comp(person, base_amount_minor=0))

    with pytest.raises(IntegrityError, match="ck_compensation_base_amount_positive"):
        session.flush()


def test_a_zero_fx_rate_is_refused(session, org):
    person = add_employee(session, org, hired_on=HIRED)
    session.add(comp(person, fx_rate_micros=0))

    with pytest.raises(IntegrityError, match="ck_compensation_fx_rate_positive"):
        session.flush()


def test_a_band_floor_of_zero_is_refused(session, org):
    session.add(band(org, min_minor=0))

    with pytest.raises(IntegrityError, match="ck_salary_band_ordered_positive"):
        session.flush()


def test_a_band_midpoint_below_its_floor_is_refused(session, org):
    session.add(band(org, min_minor=10_000_000, mid_minor=9_000_000))

    with pytest.raises(IntegrityError, match="ck_salary_band_ordered_positive"):
        session.flush()


def test_a_band_ceiling_below_its_midpoint_is_refused(session, org):
    # Compa-ratio divides by the midpoint, so an inverted band does not fail
    # loudly -- it just reports everyone as underpaid.
    session.add(band(org, mid_minor=10_000_000, max_minor=9_000_000))

    with pytest.raises(IntegrityError, match="ck_salary_band_ordered_positive"):
        session.flush()


def test_a_band_with_no_width_is_allowed(session, org):
    # A single-point band is legitimate for a fixed-rate role.
    flat = band(org, min_minor=10_000_000, mid_minor=10_000_000, max_minor=10_000_000)
    session.add(flat)
    session.flush()

    assert flat.id is not None
