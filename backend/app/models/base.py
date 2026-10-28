from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CreatedAt:
    """When the row was written, as opposed to when it takes effect."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
