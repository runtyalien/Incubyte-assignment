"""Aggregates over current pay: spreads, compa-ratio and band position.

SQLite has no percentile function, so ranks are computed with window functions
and the wanted rows picked out by rank. Everything is aggregated in the
database; pulling 10,000 salaries into Python to take a median would work at
this size and stop working at the next one.

Two conventions, stated because reasonable people pick differently:

- Quartiles use nearest rank — the value at `ceil(p x n)`, no interpolation.
  For [10, 20, 30, 40] the lower quartile is 10, not 15 or 17.5.
- The median is the conventional one: the middle value, or the mean of the two
  middle values when the count is even.

Both are tested against numbers worked out by hand.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

from sqlalchemy import Integer, case, cast, func, literal, or_, select
from sqlalchemy.orm import Session, aliased

from app.domain.money import BASE_CURRENCY
from app.models import (
    CompensationRecord,
    Department,
    Employee,
    JobFamily,
    JobLevel,
    Location,
    SalaryBand,
)
from app.repository import directory
from app.repository.directory import Filters

COMPA_SCALE = 10_000
FOUR_PLACES = Decimal("0.0001")


class Dimension(StrEnum):
    COUNTRY = "country"
    DEPARTMENT = "department"
    FAMILY = "family"
    LEVEL = "level"


# key, label, and what to order groups by
DIMENSIONS = {
    Dimension.COUNTRY: (Location.country_code, Location.name, Location.country_code),
    Dimension.DEPARTMENT: (Department.name, Department.name, Department.name),
    Dimension.FAMILY: (JobFamily.name, JobFamily.name, JobFamily.name),
    Dimension.LEVEL: (JobLevel.code, JobLevel.code, JobLevel.rank),
}


@dataclass(frozen=True)
class Spread:
    lowest: int
    p25: int
    median: int
    p75: int
    highest: int


@dataclass(frozen=True)
class Group:
    key: str
    label: str
    currency: str
    headcount: int
    pay: Spread
    compa_median: Decimal
    below: int
    within: int
    above: int


@dataclass(frozen=True)
class Overview:
    headcount: int
    payroll_minor: int
    currency: str
    pay: Spread
    compa_median: Decimal
    below: int
    within: int
    above: int
    unmeasured: int


def _ranked(by: Dimension | None, filters: Filters, as_of: date, local: bool):
    """Every employee in scope, with their rank inside their group.

    Anyone without pay in effect or without a band for their role is left out:
    a joiner whose start date has not arrived has no salary to average, and a
    role with no band has no compa-ratio. The counts are reported separately
    rather than being swallowed.
    """
    pay = aliased(CompensationRecord, name="pay")

    if by is None:
        key_col, label_col, sort_col = literal("all"), literal("All"), literal(0)
    else:
        key_col, label_col, sort_col = DIMENSIONS[by]

    amount = pay.amount_minor if local else pay.base_amount_minor
    compa = pay.amount_minor * COMPA_SCALE / SalaryBand.mid_minor

    conditions = directory.conditions_for(filters, pay, as_of)
    conditions.append(pay.id.is_not(None))
    conditions.append(SalaryBand.id.is_not(None))

    partition = key_col

    return directory.with_dimensions(
        select(
            key_col.label("key"),
            label_col.label("label"),
            sort_col.label("sort_key"),
            Location.currency.label("currency"),
            amount.label("amount"),
            pay.base_amount_minor.label("base_amount"),
            pay.amount_minor.label("local_amount"),
            compa.label("compa"),
            SalaryBand.min_minor.label("band_min"),
            SalaryBand.max_minor.label("band_max"),
            func.row_number().over(partition_by=partition, order_by=amount).label("pay_rank"),
            func.row_number().over(partition_by=partition, order_by=compa).label("compa_rank"),
            func.count().over(partition_by=partition).label("n"),
        ),
        pay,
        as_of,
    ).where(*conditions)


def _aggregates(ranked):
    """The select list shared by the grouped and overall queries."""
    n = ranked.c.n

    # Every division here has to floor. SQLAlchemy renders `/` as true
    # division, so without the cast (n + 1) / 2 is 1.5 for a pair and matches
    # no rank at all -- quartiles come back empty and an even median silently
    # becomes the upper of the two middle values.
    def floor_div(expression):
        return cast(expression, Integer)

    # ceil(n x p), via truncation: adding 99 before dividing by 100 rounds up.
    p25_rank = floor_div((n * 25 + 99) / 100)
    p75_rank = floor_div((n * 75 + 99) / 100)

    # Odd counts make these the same row; even counts straddle the middle.
    lower_middle = floor_div((n + 1) / 2)
    upper_middle = floor_div((n + 2) / 2)
    middle = or_(ranked.c.pay_rank == lower_middle, ranked.c.pay_rank == upper_middle)
    compa_middle = or_(ranked.c.compa_rank == lower_middle, ranked.c.compa_rank == upper_middle)

    return [
        func.count().label("headcount"),
        func.min(ranked.c.currency).label("currency"),
        func.sum(ranked.c.base_amount).label("payroll"),
        func.min(ranked.c.amount).label("lowest"),
        func.max(ranked.c.amount).label("highest"),
        func.sum(case((ranked.c.pay_rank == p25_rank, ranked.c.amount))).label("p25"),
        func.sum(case((ranked.c.pay_rank == p75_rank, ranked.c.amount))).label("p75"),
        func.sum(case((middle, ranked.c.amount))).label("median_sum"),
        func.count(case((middle, ranked.c.amount))).label("median_n"),
        func.sum(case((compa_middle, ranked.c.compa))).label("compa_sum"),
        func.count(case((compa_middle, ranked.c.compa))).label("compa_n"),
        func.sum(case((ranked.c.local_amount < ranked.c.band_min, 1), else_=0)).label("below"),
        func.sum(case((ranked.c.local_amount > ranked.c.band_max, 1), else_=0)).label("above"),
    ]


def _mean_of(total: int | None, count: int | None) -> int:
    """Divide in Decimal, not SQL. Averaging two middle values is the one place
    a median can land on half a minor unit."""
    if not count:
        return 0
    return int((Decimal(total) / Decimal(count)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _spread(row) -> Spread:
    return Spread(
        lowest=row.lowest or 0,
        p25=row.p25 or 0,
        median=_mean_of(row.median_sum, row.median_n),
        p75=row.p75 or 0,
        highest=row.highest or 0,
    )


def _compa_median(row) -> Decimal:
    if not row.compa_n:
        return Decimal(0)
    raw = Decimal(row.compa_sum) / Decimal(row.compa_n) / COMPA_SCALE
    return raw.quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)


def distribution(
    session: Session,
    by: Dimension,
    *,
    filters: Filters | None = None,
    as_of: date | None = None,
    local: bool = False,
) -> list[Group]:
    filters = filters or Filters()
    as_of = as_of or date.today()

    ranked = _ranked(by, filters, as_of, local).subquery()

    rows = session.execute(
        select(
            ranked.c.key,
            func.min(ranked.c.label).label("label"),
            func.min(ranked.c.sort_key).label("sort_key"),
            *_aggregates(ranked),
        )
        .group_by(ranked.c.key)
        .order_by(func.min(ranked.c.sort_key), ranked.c.key)
    ).all()

    return [
        Group(
            key=str(row.key),
            label=str(row.label),
            currency=row.currency if local else BASE_CURRENCY,
            headcount=row.headcount,
            pay=_spread(row),
            compa_median=_compa_median(row),
            below=row.below or 0,
            within=row.headcount - (row.below or 0) - (row.above or 0),
            above=row.above or 0,
        )
        for row in rows
    ]


def overview(
    session: Session,
    *,
    filters: Filters | None = None,
    as_of: date | None = None,
    local: bool = False,
) -> Overview:
    filters = filters or Filters()
    as_of = as_of or date.today()

    ranked = _ranked(None, filters, as_of, local).subquery()
    row = session.execute(select(*_aggregates(ranked))).one()

    return Overview(
        headcount=row.headcount,
        payroll_minor=row.payroll or 0,
        currency=row.currency if local else BASE_CURRENCY,
        pay=_spread(row),
        compa_median=_compa_median(row),
        below=row.below or 0,
        within=row.headcount - (row.below or 0) - (row.above or 0),
        above=row.above or 0,
        unmeasured=unmeasured(session, filters=filters, as_of=as_of),
    )


def unmeasured(session: Session, *, filters: Filters, as_of: date) -> int:
    """People in scope who have no pay in effect or no band for their role.

    They are excluded from every statistic above, so the number is reported
    rather than left for someone to notice the totals not adding up.
    """
    pay = aliased(CompensationRecord, name="pay")
    conditions = directory.conditions_for(filters, pay, as_of)

    return (
        session.scalar(
            directory.with_dimensions(select(func.count(Employee.id)), pay, as_of)
            .where(*conditions)
            .where(or_(pay.id.is_(None), SalaryBand.id.is_(None)))
        )
        or 0
    )
