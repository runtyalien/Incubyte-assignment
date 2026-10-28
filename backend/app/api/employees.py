from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.filters import FilterDep
from app.api.schemas import Band, EmployeeDetail, EmployeeSummary, Money, Page, PayEntry
from app.db import get_session
from app.domain.money import BASE_CURRENCY, to_major
from app.models import CompensationRecord
from app.repository import compensation as comp
from app.repository import directory
from app.repository.directory import MAX_PAGE_SIZE, Position, Row, Sort

router = APIRouter(tags=["employees"])

SessionDep = Annotated[Session, Depends(get_session)]

THREE_PLACES = Decimal("0.001")


@router.get("/employees", response_model=Page[EmployeeSummary])
def list_employees(
    session: SessionDep,
    filters: FilterDep,
    sort: Sort = Sort.NAME,
    order: Literal["asc", "desc"] = "asc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 50,
    as_of: Annotated[date | None, Query(description="defaults to today")] = None,
) -> Page[EmployeeSummary]:
    total, rows = directory.search(
        session,
        filters=filters,
        page=page,
        page_size=page_size,
        sort=sort,
        descending=order == "desc",
        as_of=as_of,
    )

    return Page(
        items=[_summary(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/employees/{employee_id}", response_model=EmployeeDetail)
def get_employee(
    employee_id: int,
    session: SessionDep,
    as_of: Annotated[date | None, Query()] = None,
) -> EmployeeDetail:
    row = directory.get(session, employee_id, as_of)
    if row is None:
        raise HTTPException(status_code=404, detail="No such employee")

    return EmployeeDetail(
        **_summary(row).model_dump(),
        band=_band(row),
        history=[_entry(record) for record in comp.history(session, employee_id)],
    )


def _summary(row: Row) -> EmployeeSummary:
    return EmployeeSummary(
        id=row.id,
        staff_number=row.staff_number,
        name=f"{row.first_name} {row.last_name}",
        email=row.email,
        country=row.country,
        location=row.location,
        department=row.department,
        job_family=row.job_family,
        level=row.level,
        hired_on=row.hired_on,
        left_on=row.left_on,
        pay=_money(row.amount_minor, row.pay_currency),
        base_pay=_money(row.base_amount_minor, BASE_CURRENCY),
        pay_effective_from=row.pay_effective_from,
        compa_ratio=_compa_ratio(row),
        band_position=_position(row),
    )


def _band(row: Row) -> Band | None:
    if row.band_mid_minor is None:
        return None
    return Band(
        low=Money(amount=to_major(row.band_min_minor, row.currency), currency=row.currency),
        mid=Money(amount=to_major(row.band_mid_minor, row.currency), currency=row.currency),
        high=Money(amount=to_major(row.band_max_minor, row.currency), currency=row.currency),
    )


def _entry(record: CompensationRecord) -> PayEntry:
    return PayEntry(
        effective_from=record.effective_from,
        amount=Money(
            amount=to_major(record.amount_minor, record.currency), currency=record.currency
        ),
        base_amount=Money(
            amount=to_major(record.base_amount_minor, BASE_CURRENCY), currency=BASE_CURRENCY
        ),
        reason=record.reason,
        note=record.note,
    )


def _money(minor: int | None, currency: str | None) -> Money | None:
    if minor is None or currency is None:
        return None
    return Money(amount=to_major(minor, currency), currency=currency)


def _compa_ratio(row: Row) -> Decimal | None:
    """Worked out here in Decimal rather than read back from SQL, where the
    ordering expression is deliberately integer arithmetic."""
    if row.amount_minor is None or not row.band_mid_minor:
        return None
    return (Decimal(row.amount_minor) / Decimal(row.band_mid_minor)).quantize(THREE_PLACES)


def _position(row: Row) -> Position | None:
    if row.amount_minor is None or row.band_min_minor is None:
        return None
    if row.amount_minor < row.band_min_minor:
        return Position.BELOW
    if row.amount_minor > row.band_max_minor:
        return Position.ABOVE
    return Position.WITHIN
