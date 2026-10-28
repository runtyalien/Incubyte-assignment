from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAt
from app.models.org import Department, JobFamily, JobLevel, Location

if TYPE_CHECKING:
    from app.models.compensation import CompensationRecord


class Gender(StrEnum):
    FEMALE = "female"
    MALE = "male"
    NON_BINARY = "non_binary"
    UNDISCLOSED = "undisclosed"


class Employee(Base, CreatedAt):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_number: Mapped[str] = mapped_column(String(12), unique=True)

    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(160), unique=True)

    # Special category data under GDPR Art. 9. Optional, kept out of the
    # directory and search, and only ever read in aggregate.
    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, native_enum=False, length=16), default=None
    )

    hired_on: Mapped[date] = mapped_column(Date)
    left_on: Mapped[date | None] = mapped_column(Date, default=None)

    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    job_family_id: Mapped[int] = mapped_column(ForeignKey("job_families.id"))
    job_level_id: Mapped[int] = mapped_column(ForeignKey("job_levels.id"))

    location: Mapped[Location] = relationship(lazy="joined")
    department: Mapped[Department] = relationship(lazy="joined")
    job_family: Mapped[JobFamily] = relationship(lazy="joined")
    job_level: Mapped[JobLevel] = relationship(lazy="joined")

    compensation: Mapped[list["CompensationRecord"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="CompensationRecord.effective_from",
    )

    __table_args__ = (
        # The directory filters on these constantly and sorts by name.
        Index("ix_employees_location", "location_id"),
        Index("ix_employees_department", "department_id"),
        Index("ix_employees_level", "job_level_id"),
        Index("ix_employees_name", "last_name", "first_name"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_active(self, on: date) -> bool:
        if self.hired_on > on:
            return False
        return self.left_on is None or self.left_on > on
