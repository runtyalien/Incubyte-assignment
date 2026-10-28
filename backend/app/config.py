"""Application settings, loaded from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Values come from the environment or a local `.env` file. See `.env.example`
    for the supported keys.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ACME Salary Management API"
    environment: str = "development"

    # Comma-separated list of origins allowed to call the API from a browser.
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, built once and reused."""
    return Settings()
