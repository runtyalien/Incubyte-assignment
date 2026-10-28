from datetime import date

from sqlalchemy import Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FxRate(Base):
    """Rate from `currency` into the base currency, from `effective_from`
    until a later row supersedes it."""

    __tablename__ = "fx_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    currency: Mapped[str] = mapped_column(String(3))
    effective_from: Mapped[date] = mapped_column(Date)

    # Scaled by a million rather than stored as a float, for the same reason
    # salaries are. See docs/adr/0002.
    rate_micros: Mapped[int]

    __table_args__ = (UniqueConstraint("currency", "effective_from", name="uq_fx_currency_date"),)
