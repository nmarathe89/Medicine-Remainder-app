"""SQLAlchemy async engine and session factory."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


_settings = get_settings()
engine = create_async_engine(_settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create tables on startup. Idempotent — safe to call every boot.

    Also runs a couple of light additive migrations so pre-existing local
    databases pick up new columns without needing Alembic. All statements
    are guarded (IF NOT EXISTS) and no-op on a fresh install.
    """
    # Import models so the declarative base sees them.
    from app import models  # noqa: F401
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # medicines.timezone was added later; back-fill on existing DBs.
        # Only Postgres supports IF NOT EXISTS on ADD COLUMN — SQLite (used
        # in tests) always creates fresh tables via metadata.create_all so
        # the migration is unnecessary there.
        if engine.dialect.name == "postgresql":
            await conn.execute(
                text(
                    "ALTER TABLE medicines ADD COLUMN IF NOT EXISTS "
                    "timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Kolkata'"
                )
            )
