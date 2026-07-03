"""Application configuration.

Reads settings from environment variables so the SAME code runs unchanged
locally (Docker Compose) and on GCP (Cloud Run). The only behavioural switch
is APP_ENV: when set to "cloud" the JWT secret is pulled from GCP Secret
Manager instead of the environment.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "local" or "cloud" — governs where secrets come from.
    app_env: str = "local"

    # SQLAlchemy URL. Local compose points at the "postgres" service; on Cloud
    # Run this points at Cloud SQL. SQLite is used as a fallback for tests.
    database_url: str = "postgresql+psycopg://mediminder:mediminder@localhost:5432/mediminder"

    # JWT signing. In cloud, secret is overridden from Secret Manager.
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 720  # 12h

    # GCP Secret Manager resource used only when app_env == "cloud".
    gcp_secret_resource: str = "projects/645869155931/secrets/serviceaccount"

    # CORS origins for the React frontend (comma-separated).
    cors_origins: str = "http://localhost:3000"

    # Seed synthetic data on startup (safe/idempotent).
    seed_on_startup: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # In cloud, resolve the JWT secret from Secret Manager, keeping secrets
    # out of the environment and out of the repository.
    if settings.app_env == "cloud":
        from .secrets_provider import load_jwt_secret

        resolved = load_jwt_secret(settings.gcp_secret_resource)
        if resolved:
            settings.jwt_secret = resolved
    return settings
