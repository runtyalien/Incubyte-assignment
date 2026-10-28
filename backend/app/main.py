"""Application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings


def create_app() -> FastAPI:
    """Build the FastAPI application.

    Kept as a factory so tests can construct an isolated instance.
    """
    settings = get_settings()

    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
