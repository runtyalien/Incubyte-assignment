"""The seed is a fixture the rest of the product is built on, so these check
the properties later phases rely on rather than just counting rows."""

from datetime import date

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import Base, CompensationRecord, Employee, FxRate, Location, SalaryBand
from app.repository import compensation as comp
from app.seed.run import DatabaseNotEmpty, seed_database

TODAY = date(2026, 1, 15)
SMALL = 200


def seeded(session, headcount=SMALL, rng_seed=1234):
    return seed_database(session, headcount=headcount, rng_seed=rng_seed, today=TODAY)


def new_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_creates_the_requested_headcount(session):
    summary = seeded(session)

    assert summary.employees == SMALL
    assert session.scalar(select(func.count()).select_from(Employee)) == SMALL


def test_everyone_has_pay_starting_on_their_hire_date(session):
    seeded(session)

    first_record = (
        select(
            CompensationRecord.employee_id,
            func.min(CompensationRecord.effective_from).label("starts"),
        )
        .group_by(CompensationRecord.employee_id)
        .subquery()
    )
    mismatches = session.execute(
        select(Employee.id)
        .join(first_record, first_record.c.employee_id == Employee.id, isouter=True)
        .where((first_record.c.starts.is_(None)) | (first_record.c.starts != Employee.hired_on))
    ).all()

    assert mismatches == []


def test_nobody_is_paid_in_a_currency_their_country_does_not_use(session):
    seeded(session)

    wrong = session.execute(
        select(CompensationRecord.id)
        .join(Employee, Employee.id == CompensationRecord.employee_id)
        .join(Location, Location.id == Employee.location_id)
        .where(CompensationRecord.currency != Location.currency)
    ).all()

    assert wrong == []


def test_every_role_an_employee_holds_has_a_band(session):
    seeded(session)

    unbanded = session.execute(
        select(Employee.id)
        .outerjoin(
            SalaryBand,
            (SalaryBand.location_id == Employee.location_id)
            & (SalaryBand.job_family_id == Employee.job_family_id)
            & (SalaryBand.job_level_id == Employee.job_level_id),
        )
        .where(SalaryBand.id.is_(None))
    ).all()

    assert unbanded == []


def test_an_fx_rate_is_in_force_before_the_earliest_pay_record(session):
    seeded(session)

    earliest_pay = session.scalar(select(func.min(CompensationRecord.effective_from)))
    earliest_rate = session.scalar(select(func.min(FxRate.effective_from)))

    # Conversion falls back to the opening rate otherwise, which would silently
    # price a 2017 salary at a 2016 rate.
    assert earliest_rate <= earliest_pay


def test_the_same_seed_rebuilds_the_same_organisation():
    with new_session() as first, new_session() as second:
        seeded(first)
        seeded(second)

        assert _fingerprint(first) == _fingerprint(second)


def test_a_different_seed_builds_a_different_organisation():
    with new_session() as first, new_session() as second:
        seeded(first, rng_seed=1234)
        seeded(second, rng_seed=9999)

        assert _fingerprint(first) != _fingerprint(second)


def test_seeding_twice_is_refused(session):
    seeded(session)

    with pytest.raises(DatabaseNotEmpty):
        seeded(session)


def test_reset_replaces_rather_than_appends(session):
    seeded(session)
    seed_database(session, headcount=50, rng_seed=1234, reset=True, today=TODAY)

    assert session.scalar(select(func.count()).select_from(Employee)) == 50


def test_pay_is_spread_wide_enough_to_produce_band_outliers(session):
    # The outlier view has nothing to show against uniform data, so the spread
    # is part of the contract. Nothing here is planted; this is the tail of the
    # distribution in shape.py.
    seeded(session, headcount=500)

    employees = session.scalars(select(Employee)).all()
    bands = {
        (b.location_id, b.job_family_id, b.job_level_id): b
        for b in session.scalars(select(SalaryBand)).all()
    }
    current = comp.current_many(session, [e.id for e in employees], as_of=TODAY)

    below = above = 0
    for employee in employees:
        pay = current.get(employee.id)
        if pay is None:
            continue
        band = bands[(employee.location_id, employee.job_family_id, employee.job_level_id)]
        if pay.amount_minor < band.min_minor:
            below += 1
        elif pay.amount_minor > band.max_minor:
            above += 1

    assert below > 0
    assert above > 0
    # If either tail dominates, the distribution has drifted and the band view
    # would be noise rather than signal.
    assert below < len(employees) * 0.20
    assert above < len(employees) * 0.20


def _fingerprint(session) -> list[tuple]:
    return session.execute(
        select(Employee.staff_number, Employee.hired_on, CompensationRecord.amount_minor)
        .join(CompensationRecord, CompensationRecord.employee_id == Employee.id)
        .order_by(Employee.id, CompensationRecord.id)
        .limit(200)
    ).all()
