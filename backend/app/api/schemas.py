from datetime import date
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.models import PayChangeReason
from app.repository.directory import Position

T = TypeVar("T")


class Money(BaseModel):
    """Pydantic renders Decimal as a JSON string, which is what we want —
    a JSON number would be a float by the time JavaScript sees it."""

    amount: Decimal
    currency: str


class Band(BaseModel):
    low: Money
    mid: Money
    high: Money


class PayEntry(BaseModel):
    effective_from: date
    amount: Money
    base_amount: Money
    reason: PayChangeReason
    note: str | None


class EmployeeSummary(BaseModel):
    id: int
    staff_number: str
    name: str
    email: str
    country: str
    location: str
    department: str
    job_family: str
    level: str
    hired_on: date
    left_on: date | None

    pay: Money | None
    base_pay: Money | None
    pay_effective_from: date | None

    compa_ratio: Decimal | None
    band_position: Position | None


class EmployeeDetail(EmployeeSummary):
    band: Band | None
    history: list[PayEntry]


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        return -(-self.total // self.page_size) if self.page_size else 0


class Spread(BaseModel):
    lowest: Money
    p25: Money
    median: Money
    p75: Money
    highest: Money


class BandCounts(BaseModel):
    below: int
    within: int
    above: int


class GroupStats(BaseModel):
    key: str
    label: str
    headcount: int
    pay: Spread
    compa_median: Decimal
    band: BandCounts


class Distribution(BaseModel):
    dimension: str
    as_of: date

    # "base" means every group is in one currency and can be compared across
    # countries. "local" means each group is in its own, and comparing them
    # would be meaningless.
    basis: str

    groups: list[GroupStats]


class Overview(BaseModel):
    headcount: int
    payroll: Money
    pay: Spread
    compa_median: Decimal
    band: BandCounts
    as_of: date

    # People in scope with no pay in effect or no band for their role. They are
    # in none of the figures above, so the number is shown rather than leaving
    # someone to notice the totals not adding up.
    unmeasured: int


class PayChange(BaseModel):
    effective_from: date
    amount: Decimal = Field(gt=0)
    reason: PayChangeReason

    # Defaults to whatever the employee's location is paid in. Supplying a
    # different one is an error rather than a conversion.
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    note: str | None = Field(default=None, max_length=500)


class PayChangeResult(BaseModel):
    employee_id: int
    entry: PayEntry
    compa_ratio: Decimal | None
    band_position: Position | None

    # Whether this record is the pay now in force. False for a change dated
    # ahead, and also false for one back-dated behind an existing later
    # record -- filed correctly, but not what the employee is paid today.
    in_effect: bool


class CountryRef(BaseModel):
    code: str
    name: str
    currency: str


class LevelRef(BaseModel):
    code: str
    rank: int


class Reference(BaseModel):
    countries: list[CountryRef]
    departments: list[str]
    families: list[str]
    levels: list[LevelRef]
