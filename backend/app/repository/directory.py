"""The employee directory: filtering, sorting and paging over current pay.

Current pay is derived rather than stored, so everything here works against a
joined lookup rather than a column. The alternative — read all 10,000 people
and sort them in Python — is what this module exists to avoid.
"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models import (
    CompensationRecord,
    Department,
    Employee,
    JobFamily,
    JobLevel,
    Location,
    SalaryBand,
)

MAX_PAGE_SIZE = 200

# Compa-ratio for ordering only, scaled to stay in integer arithmetic. The
# value returned to callers is worked out in Decimal from the same two numbers.
COMPA_SCALE = 10_000


class Sort(StrEnum):
    NAME = "name"
    SALARY = "salary"
    LEVEL = "level"
    HIRED = "hired"
    COMPA = "compa"


class Status(StrEnum):
    ACTIVE = "active"
    LEFT = "left"
    ALL = "all"


class Position(StrEnum):
    BELOW = "below"
    WITHIN = "within"
    ABOVE = "above"


@dataclass(frozen=True)
class Filters:
    search: str | None = None
    countries: tuple[str, ...] = ()
    departments: tuple[str, ...] = ()
    families: tuple[str, ...] = ()
    levels: tuple[str, ...] = ()
    position: Position | None = None
    status: Status = Status.ACTIVE


@dataclass(frozen=True)
class Row:
    id: int
    staff_number: str
    first_name: str
    last_name: str
    email: str
    hired_on: date
    left_on: date | None
    country: str
    location: str
    currency: str
    department: str
    job_family: str
    level: str
    level_rank: int
    amount_minor: int | None
    pay_currency: str | None
    base_amount_minor: int | None
    pay_effective_from: date | None
    band_min_minor: int | None
    band_mid_minor: int | None
    band_max_minor: int | None


def latest_pay_id(as_of: date):
    """The id of the record in force for whichever employee row we are on.

    A correlated lookup rather than ranking every record in a subquery. Ranking
    materialises all 50,000 rows before the limit applies, which costs the same
    whether the caller wants fifty rows or all of them; this runs per employee
    row and rides the (employee_id, effective_from) index, so sorting by name
    only ever resolves pay for the page being returned.
    """
    return (
        select(CompensationRecord.id)
        .where(
            CompensationRecord.employee_id == Employee.id,
            CompensationRecord.effective_from <= as_of,
        )
        .order_by(CompensationRecord.effective_from.desc(), CompensationRecord.id.desc())
        .limit(1)
        .correlate(Employee)
        .scalar_subquery()
    )


def _columns(pay) -> list:
    return [
        Employee.id.label("id"),
        Employee.staff_number.label("staff_number"),
        Employee.first_name.label("first_name"),
        Employee.last_name.label("last_name"),
        Employee.email.label("email"),
        Employee.hired_on.label("hired_on"),
        Employee.left_on.label("left_on"),
        Location.country_code.label("country"),
        Location.name.label("location"),
        Location.currency.label("currency"),
        Department.name.label("department"),
        JobFamily.name.label("job_family"),
        JobLevel.code.label("level"),
        JobLevel.rank.label("level_rank"),
        pay.amount_minor.label("amount_minor"),
        pay.currency.label("pay_currency"),
        pay.base_amount_minor.label("base_amount_minor"),
        pay.effective_from.label("pay_effective_from"),
        SalaryBand.min_minor.label("band_min_minor"),
        SalaryBand.mid_minor.label("band_mid_minor"),
        SalaryBand.max_minor.label("band_max_minor"),
    ]


def with_dimensions(statement: Select, pay, as_of: date, *, with_pay: bool = True) -> Select:
    """Employees joined to their location, department, family, level, current
    pay and band. Shared with the analytics queries, which group over the same
    shape."""
    joined = (
        statement.select_from(Employee)
        .join(Location, Location.id == Employee.location_id)
        .join(Department, Department.id == Employee.department_id)
        .join(JobFamily, JobFamily.id == Employee.job_family_id)
        .join(JobLevel, JobLevel.id == Employee.job_level_id)
    )

    if not with_pay:
        return joined

    return joined.outerjoin(pay, pay.id == latest_pay_id(as_of)).outerjoin(
        SalaryBand,
        and_(
            SalaryBand.location_id == Employee.location_id,
            SalaryBand.job_family_id == Employee.job_family_id,
            SalaryBand.job_level_id == Employee.job_level_id,
        ),
    )


def conditions_for(filters: Filters, pay, as_of: date) -> list:
    conditions = []

    if filters.search:
        like = f"%{filters.search.strip()}%"
        conditions.append(
            or_(
                Employee.first_name.ilike(like),
                Employee.last_name.ilike(like),
                Employee.staff_number.ilike(like),
                Employee.email.ilike(like),
            )
        )

    if filters.countries:
        conditions.append(Location.country_code.in_(filters.countries))
    if filters.departments:
        conditions.append(Department.name.in_(filters.departments))
    if filters.families:
        conditions.append(JobFamily.name.in_(filters.families))
    if filters.levels:
        conditions.append(JobLevel.code.in_(filters.levels))

    if filters.status is Status.ACTIVE:
        conditions.append(Employee.hired_on <= as_of)
        conditions.append(or_(Employee.left_on.is_(None), Employee.left_on > as_of))
    elif filters.status is Status.LEFT:
        conditions.append(and_(Employee.left_on.is_not(None), Employee.left_on <= as_of))

    if filters.position is Position.BELOW:
        conditions.append(pay.amount_minor < SalaryBand.min_minor)
    elif filters.position is Position.ABOVE:
        conditions.append(pay.amount_minor > SalaryBand.max_minor)
    elif filters.position is Position.WITHIN:
        conditions.append(
            and_(
                pay.amount_minor >= SalaryBand.min_minor,
                pay.amount_minor <= SalaryBand.max_minor,
            )
        )

    return conditions


def _ordering(sort: Sort, descending: bool, pay) -> list:
    if sort is Sort.SALARY:
        keys = [pay.base_amount_minor]
    elif sort is Sort.LEVEL:
        keys = [JobLevel.rank]
    elif sort is Sort.HIRED:
        keys = [Employee.hired_on]
    elif sort is Sort.COMPA:
        keys = [pay.amount_minor * COMPA_SCALE / SalaryBand.mid_minor]
    else:
        keys = [Employee.last_name, Employee.first_name]

    ordered = [key.desc() if descending else key.asc() for key in keys]
    # Without a tiebreak, equal keys can shuffle between pages and a row is
    # seen twice or not at all.
    ordered.append(Employee.id.asc())
    return ordered


def search(
    session: Session,
    *,
    filters: Filters | None = None,
    page: int = 1,
    page_size: int = 50,
    sort: Sort = Sort.NAME,
    descending: bool = False,
    as_of: date | None = None,
) -> tuple[int, list[Row]]:
    filters = filters or Filters()
    as_of = as_of or date.today()
    page_size = min(page_size, MAX_PAGE_SIZE)

    pay = aliased(CompensationRecord, name="pay")
    conditions = conditions_for(filters, pay, as_of)

    # Only the band filter looks at pay, and both joins are outer joins that
    # cannot change the row count, so the count query leaves them out unless
    # it needs them.
    counting_needs_pay = filters.position is not None
    counted = with_dimensions(
        select(func.count(Employee.id)), pay, as_of, with_pay=counting_needs_pay
    )
    total = session.scalar(counted.where(*conditions))

    rows = (
        session.execute(
            with_dimensions(select(*_columns(pay)), pay, as_of)
            .where(*conditions)
            .order_by(*_ordering(sort, descending, pay))
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        .mappings()
        .all()
    )

    return total or 0, [Row(**row) for row in rows]


def get(session: Session, employee_id: int, as_of: date | None = None) -> Row | None:
    as_of = as_of or date.today()
    pay = aliased(CompensationRecord, name="pay")

    row = (
        session.execute(
            with_dimensions(select(*_columns(pay)), pay, as_of).where(Employee.id == employee_id)
        )
        .mappings()
        .one_or_none()
    )

    return Row(**row) if row else None
