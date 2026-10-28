from datetime import date
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel

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
