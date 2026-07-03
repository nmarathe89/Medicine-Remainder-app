"""Test fixtures.

Uses a throwaway SQLite database (DATABASE_URL override) so tests run anywhere
without Postgres, while the SAME application code exercises Postgres in
compose/cloud. Seeding on startup is disabled for deterministic tests.
"""
import os

os.environ.setdefault("APP_ENV", "local")
# In-memory SQLite shared across connections (StaticPool) — no file locks,
# works identically on Windows/Linux. Real deployments use Postgres.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["SEED_ON_STARTUP"] = "false"
os.environ["JWT_SECRET"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client():
    # Recreate the schema in the shared in-memory DB for each test.
    from app import models  # noqa: F401
    from app.database import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.main import app

    with TestClient(app) as c:
        yield c


def register_and_login(client, username="user1", password="pass1234"):
    client.post("/api/auth/register", json={"username": username, "password": password})
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_admin(client, username="admin1", password="admin123"):
    """Create a user then promote to admin directly in the DB."""
    client.post("/api/auth/register", json={"username": username, "password": password})
    from app.database import SessionLocal
    from app.models import User

    db = SessionLocal()
    u = db.query(User).filter(User.username == username).first()
    u.role = "admin"
    db.commit()
    db.close()
    resp = client.post("/api/auth/admin/login", json={"username": username, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
