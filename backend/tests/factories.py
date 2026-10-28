from datetime import date
from itertools import count

from sqlalchemy.orm import Session

from app.domain.money import to_base, to_minor
from app.models import (
    CompensationRecord,
    Department,
    Employee,
    JobFamily,
    JobLevel,
    Location,
    PayChangeReason,
)

_serial = count(1)

PAR = 1_000_000  # an FX rate of exactly 1.0, in micros


class Org:
    """The reference rows every employee needs before it can exist."""

    def __init__(self, session: Session):
        self.location = Location(country_code="US", name="United States", currency="USD")
        self.department = Department(name="Engineering")
        self.family = JobFamily(name="Software")
        self.level = JobLevel(code="L4", rank=4)

        session.add_all([self.location, self.department, self.family, self.level])
        session.flush()


def add_employee(session: Session, org: Org, **overrides) -> Employee:
    n = next(_serial)
    employee = Employee(
        staff_number=f"E{n:05d}",
        first_name="Test",
        last_name=f"Person{n}",
        email=f"person{n}@acme.test",
        hired_on=date(2020, 1, 6),
        location_id=org.location.id,
        department_id=org.department.id,
        job_family_id=org.family.id,
        job_level_id=org.level.id,
    )
    for field, value in overrides.items():
        setattr(employee, field, value)

    session.add(employee)
    session.flush()
    return employee


def add_pay(
    session: Session,
    employee: Employee,
    effective_from: date,
    amount: str,
    *,
    currency: str = "USD",
    rate_micros: int = PAR,
    reason: PayChangeReason = PayChangeReason.MERIT,
) -> CompensationRecord:
    minor = to_minor(amount, currency)
    record = CompensationRecord(
        employee_id=employee.id,
        effective_from=effective_from,
        amount_minor=minor,
        currency=currency,
        base_amount_minor=to_base(minor, currency, rate_micros),
        fx_rate_micros=rate_micros,
        reason=reason,
    )
    session.add(record)
    session.flush()
    return record
