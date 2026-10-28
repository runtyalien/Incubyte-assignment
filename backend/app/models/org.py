from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Location(Base):
    """A country we employ people in. One currency each, which is the
    simplification that lets currency hang off location rather than off the
    employee."""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    country_code: Mapped[str] = mapped_column(String(2), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    currency: Mapped[str] = mapped_column(String(3))


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class JobFamily(Base):
    __tablename__ = "job_families"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class JobLevel(Base):
    __tablename__ = "job_levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)

    # Seniority as a number, because "L10" sorts before "L2" as a string and
    # banding needs to compare like with like.
    rank: Mapped[int] = mapped_column(unique=True)
