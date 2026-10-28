from fastapi import APIRouter

from app.api import analytics, employees, health, reference

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(employees.router)
api_router.include_router(analytics.router)
api_router.include_router(reference.router)
