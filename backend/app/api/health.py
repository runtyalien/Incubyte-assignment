import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session

log = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

SessionDep = Annotated[Session, Depends(get_session)]


class Health(BaseModel):
    status: str
    service: str
    environment: str
    database: str


@router.get("/health", response_model=Health, responses={503: {"model": Health}})
def health(session: SessionDep, response: Response) -> Health:
    # A process that is up but cannot read is no use to whatever is watching
    # this, so the database gets the final say on the status code. The body
    # keeps the same shape either way, so a monitor can read one without
    # branching on the status first.
    reachable = _database_answers(session)
    if not reachable:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    settings = get_settings()
    return Health(
        status="ok" if reachable else "degraded",
        service=settings.app_name,
        environment=settings.environment,
        database="up" if reachable else "down",
    )


def _database_answers(session: Session) -> bool:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        # Anything the driver raises means we cannot serve. The reason goes to
        # the log rather than into a public response, where it would hand out
        # the connection string to anyone who asked.
        log.exception("health check could not reach the database")
        return False
    return True
