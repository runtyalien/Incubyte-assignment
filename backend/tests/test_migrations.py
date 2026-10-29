from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text

from app.models import Base

BACKEND = Path(__file__).resolve().parents[1]

# Keyed by table, because a constraint is only ever reported inside the SQL of
# the table it guards.
CHECKS = {
    "employees": ["ck_employee_left_on_after_hired_on"],
    "compensation_records": [
        "ck_compensation_amount_positive",
        "ck_compensation_base_amount_positive",
        "ck_compensation_fx_rate_positive",
    ],
    "salary_bands": ["ck_salary_band_ordered_positive"],
}


def migrated(tmp_path, name):
    url = f"sqlite:///{tmp_path / name}"

    # Built by hand rather than from alembic.ini so this does not reconfigure
    # logging out from under pytest.
    config = Config()
    config.set_main_option("script_location", str(BACKEND / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")

    return url


def test_migrations_produce_the_models_schema(tmp_path):
    """Catches a model changed without a matching migration, which otherwise
    only surfaces on deploy against a real database."""
    url = migrated(tmp_path, "drift.db")

    engine = create_engine(url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        drift = compare_metadata(context, Base.metadata)
    engine.dispose()

    assert drift == []


def test_migrations_create_the_check_constraints(tmp_path):
    """The drift test above cannot see these.

    Alembic's metadata comparison ignores CHECK constraints entirely, so one
    added to a model and forgotten in a migration passes that test and is then
    absent from every database that was built by migrating rather than by
    create_all -- which means every deployed one.
    """
    url = migrated(tmp_path, "checks.db")

    engine = create_engine(url)
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT name, sql FROM sqlite_master WHERE type = 'table'")
        ).all()
    engine.dispose()

    schema = {name: sql or "" for name, sql in rows}
    missing = [
        f"{table}.{check}"
        for table, checks in CHECKS.items()
        for check in checks
        if check not in schema.get(table, "")
    ]

    assert missing == []
