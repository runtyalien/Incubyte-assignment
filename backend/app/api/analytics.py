from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.filters import FilterDep
from app.api.schemas import BandCounts, Distribution, GroupStats, Money, Overview, Spread
from app.db import get_session
from app.domain.money import to_major
from app.repository import analytics
from app.repository.analytics import Dimension
from app.repository.directory import Filters

router = APIRouter(prefix="/analytics", tags=["analytics"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/overview", response_model=Overview)
def overview(
    session: SessionDep,
    filters: FilterDep,
    local: Annotated[bool, Query(description="report in local currency")] = False,
    as_of: Annotated[date | None, Query()] = None,
) -> Overview:
    _check_currency(filters, by=None, local=local)
    as_of = as_of or date.today()

    totals = analytics.overview(session, filters=filters, as_of=as_of, local=local)

    return Overview(
        headcount=totals.headcount,
        payroll=_money(totals.payroll_minor, totals.currency),
        pay=_spread(totals.pay, totals.currency),
        compa_median=totals.compa_median,
        band=BandCounts(below=totals.below, within=totals.within, above=totals.above),
        unmeasured=totals.unmeasured,
        as_of=as_of,
    )


@router.get("/distribution", response_model=Distribution)
def distribution(
    session: SessionDep,
    filters: FilterDep,
    by: Dimension,
    local: Annotated[bool, Query(description="report in local currency")] = False,
    as_of: Annotated[date | None, Query()] = None,
) -> Distribution:
    _check_currency(filters, by=by, local=local)
    as_of = as_of or date.today()

    groups = analytics.distribution(session, by, filters=filters, as_of=as_of, local=local)

    return Distribution(
        dimension=by.value,
        basis="local" if local else "base",
        as_of=as_of,
        groups=[
            GroupStats(
                key=group.key,
                label=group.label,
                headcount=group.headcount,
                pay=_spread(group.pay, group.currency),
                compa_median=group.compa_median,
                band=BandCounts(below=group.below, within=group.within, above=group.above),
            )
            for group in groups
        ],
    )


def _check_currency(filters: Filters, *, by: Dimension | None, local: bool) -> None:
    """Local currency only means something when every row in a group shares one.

    Grouped by country each group does. Filtered to a single country the whole
    result does. Anything else would put rupees and dollars in the same median,
    so it is refused rather than quietly answered in a currency that is not
    named anywhere.
    """
    if not local:
        return
    if by is Dimension.COUNTRY or len(filters.countries) == 1:
        return

    raise HTTPException(
        status_code=400,
        detail=(
            "local currency needs a single currency per group: either group by "
            "country, or filter to one country"
        ),
    )


def _money(minor: int, currency: str) -> Money:
    return Money(amount=to_major(minor, currency), currency=currency)


def _spread(spread: analytics.Spread, currency: str) -> Spread:
    return Spread(
        lowest=_money(spread.lowest, currency),
        p25=_money(spread.p25, currency),
        median=_money(spread.median, currency),
        p75=_money(spread.p75, currency),
        highest=_money(spread.highest, currency),
    )
