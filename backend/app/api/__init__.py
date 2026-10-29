from fastapi import APIRouter, Depends

from app.api import analytics, employees, health, reference
from app.api.security import require_api_key

api_router = APIRouter()

# Health stays open: whatever is watching the service has no key, and all it
# learns is whether the process can reach its database.
api_router.include_router(health.router)

guarded = [Depends(require_api_key)]
api_router.include_router(employees.router, dependencies=guarded)
api_router.include_router(analytics.router, dependencies=guarded)
api_router.include_router(reference.router, dependencies=guarded)
