"""Test scaffolding.

Tests hit an in-memory SQLite database (via aiosqlite) instead of Postgres so
they can run anywhere without docker. The app code doesn't know or care:
SQLAlchemy's async engine handles both.
"""

from __future__ import annotations

import os

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123"

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Import AFTER env vars are set so config picks them up.
from app.config import get_settings
get_settings.cache_clear()  # type: ignore[attr-defined]

from app.database import Base, engine, init_models
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _fresh_db() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    # Bootstrap admin (mirrors main._bootstrap_admin without triggering startup event).
    from app.database import SessionLocal
    from app.models import User
    from app.services.security import hash_password
    async with SessionLocal() as db:
        db.add(
            User(
                username="admin",
                email="admin@mediminder.local",
                password_hash=hash_password("admin123"),
                is_active=True,
                is_admin=True,
            )
        )
        await db.commit()
    yield


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
