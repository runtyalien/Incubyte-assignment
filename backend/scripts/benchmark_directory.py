"""Time the directory queries against whatever is in the database.

    python scripts/benchmark_directory.py

Seed first; the numbers mean nothing against an empty table. Takes the best of
five runs after a warm-up, so it reports the query cost rather than the cost of
reading pages off disk for the first time.
"""

import sys
from datetime import date
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import engine  # noqa: E402
from app.models import Employee  # noqa: E402
from app.repository import directory  # noqa: E402
from app.repository.directory import Filters, Position, Sort  # noqa: E402

ROUNDS = 5


def best(fn) -> float:
    fn()
    return min(_once(fn) for _ in range(ROUNDS))


def _once(fn) -> float:
    start = perf_counter()
    fn()
    return perf_counter() - start


def main() -> None:
    today = date.today()

    with Session(engine) as session:
        total = session.scalar(select(func.count()).select_from(Employee))
        if not total:
            raise SystemExit("No employees. Run `python -m app.seed` first.")

        print(f"{total:,} employees\n")

        cases = {
            "first page, by name": lambda: directory.search(session, page_size=50, as_of=today),
            "first page, by salary": lambda: directory.search(
                session, page_size=50, sort=Sort.SALARY, as_of=today
            ),
            "first page, by compa-ratio": lambda: directory.search(
                session, page_size=50, sort=Sort.COMPA, as_of=today
            ),
            "page 150, deep offset": lambda: directory.search(
                session, page=150, page_size=50, as_of=today
            ),
            "filtered to below band": lambda: directory.search(
                session, filters=Filters(position=Position.BELOW), page_size=50, as_of=today
            ),
            "search by surname": lambda: directory.search(
                session, filters=Filters(search="Sharma"), as_of=today
            ),
            "one employee": lambda: directory.get(session, 1, as_of=today),
        }

        for label, case in cases.items():
            print(f"  {label:<30} {best(case) * 1000:7.1f} ms")


if __name__ == "__main__":
    main()
