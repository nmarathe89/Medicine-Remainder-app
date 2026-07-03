"""Application settings.

One entry point, two environments. `ENVIRONMENT=local` reads from process
environment (populated from `.env` by docker-compose); `ENVIRONMENT=cloud`
pulls a JSON blob from GCP Secret Manager and overlays it. Everything else
in the app calls `get_settings()` and doesn't care which path was taken.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["local", "cloud", "test"] = "local"

    # database
    database_url: str = "postgresql+asyncpg://mediminder:mediminder@db:5432/mediminder"

    # auth
    jwt_secret: str = "change-me-in-.env-or-secret-manager"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60 * 24  # one day

    # admin bootstrap
    admin_username: str = "admin"
    admin_password: str = "admin123"  # overridden by Secret Manager in cloud

    # gcp
    gcp_project: str = "645869155931"
    secret_name: str = "projects/645869155931/secrets/serviceaccount"

    # scheduler / alerts
    alert_lookahead_hours: int = 48
    scheduler_tick_seconds: int = 30

    # cors
    frontend_origin: str = "http://localhost:3000"


def _load_from_secret_manager(settings: Settings) -> Settings:
    """Overlay cloud secrets. Kept out of the hot path — called once."""
    try:
        from google.cloud import secretmanager  # type: ignore

        client = secretmanager.SecretManagerServiceClient()
        name = f"{settings.secret_name}/versions/latest"
        resp = client.access_secret_version(request={"name": name})
        payload = json.loads(resp.payload.data.decode("utf-8"))
        # Expected JSON keys mirror Settings field names; unknown keys ignored.
        for key, value in payload.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)
        log.info("Loaded %d overrides from Secret Manager", len(payload))
    except Exception as exc:  # pragma: no cover — cloud-only path
        log.warning("Secret Manager fetch failed (%s); using env defaults", exc)
    return settings


@lru_cache
def get_settings() -> Settings:
    env = os.getenv("ENVIRONMENT", "local").lower()
    settings = Settings(environment=env)  # type: ignore[arg-type]
    if settings.environment == "cloud":
        settings = _load_from_secret_manager(settings)
    return settings
