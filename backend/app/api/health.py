from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: str
    service: str
    environment: str


@router.get("/health", response_model=Health)
def health() -> Health:
    settings = get_settings()
    return Health(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
    )
