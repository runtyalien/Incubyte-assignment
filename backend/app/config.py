from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ACME Salary Management API"
    environment: str = "development"

    database_url: str = "sqlite:///./salary.db"

    # Shared between this service and whatever is allowed to call it. Empty
    # means unauthenticated, which the validator below only tolerates outside
    # production.
    api_key: str = ""

    # Comma-separated, because env vars can't hold a list.
    cors_origins: str = "http://localhost:3000"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _refuse_to_serve_production_unguarded(self) -> "Settings":
        """Fail at start-up rather than at the first request.

        A missing key is a deployment mistake, and the failure mode without
        this is the worst one available: the service comes up looking healthy
        and serves every salary in the organisation to anyone who asks.
        """
        if not self.is_production:
            return self

        if not self.api_key:
            raise ValueError(
                "API_KEY must be set when ENVIRONMENT=production. "
                "Refusing to serve salary data unauthenticated."
            )

        if "*" in self.allowed_origins:
            raise ValueError(
                "CORS_ORIGINS cannot be '*' when ENVIRONMENT=production. "
                "Name the frontend origin explicitly."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
