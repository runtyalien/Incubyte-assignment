from app.models.base import Base
from app.models.compensation import CompensationRecord, PayChangeReason, SalaryBand
from app.models.employee import Employee
from app.models.fx import FxRate
from app.models.org import Department, JobFamily, JobLevel, Location

# Alembic autogenerate only sees tables that have been imported.
__all__ = [
    "Base",
    "CompensationRecord",
    "Department",
    "Employee",
    "FxRate",
    "JobFamily",
    "JobLevel",
    "Location",
    "PayChangeReason",
    "SalaryBand",
]
