from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.filters import FilterDep
from app.api.schemas import (
    Band,
    EmployeeDetail,
    EmployeeSummary,
    Money,
    Page,
    PayChange,
    PayChangeResult,
    PayEntry,
)
from app.db import get_session
from app.domain.money import BASE_CURRENCY, to_major
from app.models import CompensationRecord
from app.repository import compensation as comp
from app.repository import directory, fx
from app.repository.directory import MAX_PAGE_SIZE, Position, Row, Sort
from app.services import pay

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


@router.post(
    "/employees/{employee_id}/compensation",
    response_model=PayChangeResult,
    status_code=201,
)
def record_pay_change(
    employee_id: int,
    change: PayChange,
    session: SessionDep,
) -> PayChangeResult:
    """Append a pay change. Nothing already on record is touched."""
    try:
        record = pay.record_change(
            session,
            employee_id,
            effective_from=change.effective_from,
            amount=change.amount,
            currency=change.currency,
            reason=change.reason,
            note=change.note,
        )
    except pay.EmployeeNotFound as err:
        raise HTTPException(status_code=404, detail=str(err)) from None
    except pay.ConflictingPayChange as err:
        raise HTTPException(status_code=409, detail=str(err)) from None
    except (pay.InvalidPayChange, fx.NoRateAvailable) as err:
        raise HTTPException(status_code=422, detail=str(err)) from None

    row = directory.get(session, employee_id)
    band_mid = row.band_mid_minor if row else None
    band_low = row.band_min_minor if row else None
    band_high = row.band_max_minor if row else None

    # Whether this record is the pay now in force, which is not the same as
    # its date having arrived: back-dating a change behind an existing later
    # record files it correctly and leaves current pay alone.
    in_force = comp.current(session, employee_id)

    return PayChangeResult(
        employee_id=employee_id,
        entry=_entry(record),
        # Against the new amount rather than today's pay, so a change dated
        # ahead still answers "does this put them outside their band".
        compa_ratio=_ratio_for(record.amount_minor, band_mid),
        band_position=_position_for(record.amount_minor, band_low, band_high),
        in_effect=in_force is not None and in_force.id == record.id,
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


def _ratio_for(amount_minor: int | None, mid_minor: int | None) -> Decimal | None:
    """Worked out here in Decimal rather than read back from SQL, where the
    ordering expression is deliberately integer arithmetic."""
    if amount_minor is None or not mid_minor:
        return None
    return (Decimal(amount_minor) / Decimal(mid_minor)).quantize(THREE_PLACES)


def _position_for(amount_minor: int | None, low: int | None, high: int | None) -> Position | None:
    if amount_minor is None or low is None or high is None:
        return None
    if amount_minor < low:
        return Position.BELOW
    if amount_minor > high:
        return Position.ABOVE
    return Position.WITHIN


def _compa_ratio(row: Row) -> Decimal | None:
    return _ratio_for(row.amount_minor, row.band_mid_minor)


def _position(row: Row) -> Position | None:
    return _position_for(row.amount_minor, row.band_min_minor, row.band_max_minor)
