"""Secret resolution.

Local: secrets come from environment variables (see config.py).
Cloud: the service-account credential / JWT secret is stored in GCP Secret
Manager at projects/645869155931/secrets/serviceaccount and fetched at
runtime. This module is only invoked when APP_ENV=cloud, so the google
dependency is imported lazily and failures degrade gracefully.
"""
import json
import logging

logger = logging.getLogger(__name__)


def load_jwt_secret(secret_resource: str) -> str | None:
    """Fetch the JWT signing secret from GCP Secret Manager.

    The secret payload may be a raw string or a JSON blob containing a
    "jwt_secret" key; both are supported. Returns None on any failure so the
    caller can fall back to the environment-provided default.
    """
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = f"{secret_resource}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("utf-8").strip()
        try:
            data = json.loads(payload)
            if isinstance(data, dict) and "jwt_secret" in data:
                return str(data["jwt_secret"])
        except json.JSONDecodeError:
            pass
        return payload
    except Exception as exc:  # pragma: no cover - cloud-only path
        logger.warning("Could not load secret from Secret Manager: %s", exc)
        return None
