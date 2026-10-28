from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.models import Base

BACKEND = Path(__file__).resolve().parents[1]


def test_migrations_produce_the_models_schema(tmp_path):
    """Catches a model changed without a matching migration, which otherwise
    only surfaces on deploy against a real database."""
    url = f"sqlite:///{tmp_path / 'drift.db'}"

    # Built by hand rather than from alembic.ini so this does not reconfigure
    # logging out from under pytest.
    config = Config()
    config.set_main_option("script_location", str(BACKEND / "migrations"))
    config.set_main_option("sqlalchemy.url", url)

    command.upgrade(config, "head")

    engine = create_engine(url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        drift = compare_metadata(context, Base.metadata)
    engine.dispose()

    assert drift == []
