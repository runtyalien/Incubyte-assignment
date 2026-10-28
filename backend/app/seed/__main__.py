import argparse
from time import perf_counter

from app.db import SessionFactory
from app.seed import shape
from app.seed.run import DatabaseNotEmpty, seed_database


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m app.seed",
        description="Fill the database with a synthetic organisation.",
    )
    parser.add_argument(
        "--employees", type=int, default=shape.DEFAULT_HEADCOUNT, help="how many people to create"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=shape.DEFAULT_SEED,
        dest="rng_seed",
        help="random seed; the same value always produces the same organisation",
    )
    parser.add_argument("--reset", action="store_true", help="delete existing data before seeding")
    parser.add_argument(
        "--if-empty",
        action="store_true",
        dest="if_empty",
        help=(
            "do nothing, successfully, when the database already has people in it. "
            "For container start-up, where seeding should fill a fresh disk but a "
            "warm restart must not fail."
        ),
    )
    args = parser.parse_args()

    started = perf_counter()
    with SessionFactory() as session:
        try:
            summary = seed_database(
                session,
                headcount=args.employees,
                rng_seed=args.rng_seed,
                reset=args.reset,
            )
        except DatabaseNotEmpty as err:
            if args.if_empty:
                print("Database already has employees; leaving it as it is.")
                return
            raise SystemExit(str(err)) from None

    print(f"{summary} in {perf_counter() - started:.1f}s")


if __name__ == "__main__":
    main()
