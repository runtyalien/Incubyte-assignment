from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import (
    CompensationRecord,
    Department,
    Employee,
    FxRate,
    JobFamily,
    JobLevel,
    Location,
    SalaryBand,
)
from app.seed import shape
from app.seed.generate import Summary, build


class DatabaseNotEmpty(RuntimeError):
    pass


# Children before parents, so the foreign keys hold at every step.
WIPE_ORDER = [
    CompensationRecord,
    SalaryBand,
    Employee,
    FxRate,
    Location,
    Department,
    JobFamily,
    JobLevel,
]


def seed_database(
    session: Session,
    *,
    headcount: int = shape.DEFAULT_HEADCOUNT,
    rng_seed: int = shape.DEFAULT_SEED,
    reset: bool = False,
    today: date | None = None,
) -> Summary:
    """Populate an empty database.

    Refuses a database that already has people in it. Running the seed twice
    and silently ending up with 20,000 employees is a bad afternoon, so
    replacing them has to be asked for.
    """
    if session.scalar(select(func.count()).select_from(Employee)):
        if not reset:
            raise DatabaseNotEmpty(
                "Database already contains employees. Re-run with --reset to replace them."
            )
        wipe(session)

    return build(session, headcount, rng_seed, today)


def wipe(session: Session) -> None:
    for model in WIPE_ORDER:
        session.execute(delete(model))
    session.commit()
