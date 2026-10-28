from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import CountryRef, LevelRef, Reference
from app.db import get_session
from app.models import Department, JobFamily, JobLevel, Location

router = APIRouter(tags=["reference"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/reference", response_model=Reference)
def reference(session: SessionDep) -> Reference:
    """The values the directory and analytics filters can take.

    Without this the UI would either hardcode the organisation's shape or
    derive it from an aggregate query, and both go stale the moment someone
    opens an office.
    """
    locations = session.scalars(select(Location).order_by(Location.name)).all()
    levels = session.scalars(select(JobLevel).order_by(JobLevel.rank)).all()

    return Reference(
        countries=[
            CountryRef(code=row.country_code, name=row.name, currency=row.currency)
            for row in locations
        ],
        departments=list(session.scalars(select(Department.name).order_by(Department.name))),
        families=list(session.scalars(select(JobFamily.name).order_by(JobFamily.name))),
        levels=[LevelRef(code=row.code, rank=row.rank) for row in levels],
    )
