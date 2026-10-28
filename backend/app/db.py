from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

engine = create_engine(get_settings().database_url)
SessionFactory = sessionmaker(engine, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(connection, _record):
    # SQLite ships with foreign keys disabled, so without this the schema's
    # relationships are decorative and orphans go in quietly.
    if connection.__class__.__module__.startswith("sqlite3"):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_session() -> Iterator[Session]:
    with SessionFactory() as session:
        yield session
