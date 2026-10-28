from datetime import date
from enum import StrEnum

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAt
from app.models.employee import Employee
from app.models.org import JobFamily, JobLevel, Location


class PayChangeReason(StrEnum):
    HIRE = "hire"
    MERIT = "merit"
    PROMOTION = "promotion"
    MARKET_ADJUSTMENT = "market_adjustment"
    CORRECTION = "correction"


class CompensationRecord(Base, CreatedAt):
    """One salary, from `effective_from` onwards. Never updated — a change is
    another row, and today's salary is the latest row that has come into
    effect. See docs/adr/0001."""

    __tablename__ = "compensation_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))

    effective_from: Mapped[date] = mapped_column(Date)

    amount_minor: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3))

    # The same amount in the base currency, converted at the rate in force on
    # effective_from and kept so historical reports stay put. See docs/adr/0003.
    base_amount_minor: Mapped[int]
    fx_rate_micros: Mapped[int]

    reason: Mapped[PayChangeReason] = mapped_column(
        Enum(PayChangeReason, native_enum=False, length=20)
    )
    note: Mapped[str | None] = mapped_column(String(500), default=None)

    employee: Mapped[Employee] = relationship(back_populates="compensation")

    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="ck_compensation_amount_positive"),
        CheckConstraint("base_amount_minor > 0", name="ck_compensation_base_amount_positive"),
        CheckConstraint("fx_rate_micros > 0", name="ck_compensation_fx_rate_positive"),
        # Every current-salary lookup walks this, descending.
        Index("ix_comp_employee_effective", "employee_id", "effective_from"),
    )


class SalaryBand(Base):
    """What a role should pay in a given country. Bands are what turn a salary
    into a judgement rather than just a number."""

    __tablename__ = "salary_bands"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    job_family_id: Mapped[int] = mapped_column(ForeignKey("job_families.id"))
    job_level_id: Mapped[int] = mapped_column(ForeignKey("job_levels.id"))

    currency: Mapped[str] = mapped_column(String(3))
    min_minor: Mapped[int]
    mid_minor: Mapped[int]
    max_minor: Mapped[int]

    location: Mapped[Location] = relationship(lazy="joined")
    job_family: Mapped[JobFamily] = relationship(lazy="joined")
    job_level: Mapped[JobLevel] = relationship(lazy="joined")

    __table_args__ = (
        CheckConstraint("min_minor > 0 AND min_minor <= mid_minor AND mid_minor <= max_minor",
        name="ck_salary_band_ordered_positive"),
        UniqueConstraint(
            "location_id", "job_family_id", "job_level_id", name="uq_band_location_family_level"
        ),
    )
