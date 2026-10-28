"""Query parameters shared by the directory and the analytics endpoints.

Both answer questions about the same population, so they take the same filters.
Declaring them once keeps them from drifting apart — a filter the directory
honours and the analytics quietly ignores would make the two disagree about
the same organisation.
"""

from typing import Annotated

from fastapi import Depends, Query

from app.repository.directory import Filters, Position, Status


def filter_params(
    q: Annotated[str | None, Query(description="name, staff number or email")] = None,
    country: Annotated[list[str], Query()] = [],  # noqa: B006 — FastAPI reads the default
    department: Annotated[list[str], Query()] = [],  # noqa: B006
    family: Annotated[list[str], Query()] = [],  # noqa: B006
    level: Annotated[list[str], Query()] = [],  # noqa: B006
    position: Position | None = None,
    status: Status = Status.ACTIVE,
) -> Filters:
    return Filters(
        search=q,
        countries=tuple(country),
        departments=tuple(department),
        families=tuple(family),
        levels=tuple(level),
        position=position,
        status=status,
    )


FilterDep = Annotated[Filters, Depends(filter_params)]
