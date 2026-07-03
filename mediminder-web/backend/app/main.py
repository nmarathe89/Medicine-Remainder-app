"""FastAPI entry point.

Composes the routers, starts an APScheduler tick to materialize + broadcast
alerts, and bootstraps the admin user on first run. `ENVIRONMENT` drives the
config source (see `app.config`).
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal, init_models
from app.models import User
from app.routers import admin, alerts, auth, feedback, medicines
from app.services.alerts import scheduler_tick
from app.services.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="Mediminder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(medicines.router)
app.include_router(alerts.router)
app.include_router(alerts.ws_router)
app.include_router(feedback.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "environment": settings.environment}


scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def on_startup() -> None:
    await init_models()
    await _bootstrap_admin()
    scheduler.add_job(
        scheduler_tick,
        "interval",
        seconds=settings.scheduler_tick_seconds,
        kwargs={"horizon_hours": settings.alert_lookahead_hours},
        id="mediminder_tick",
        replace_existing=True,
    )
    scheduler.start()
    log.info("Startup complete; environment=%s", settings.environment)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    scheduler.shutdown(wait=False)


async def _bootstrap_admin() -> None:
    """Create the built-in admin user if it doesn't exist yet."""
    async with SessionLocal() as db:
        existing = (
            await db.execute(select(User).where(User.username == settings.admin_username))
        ).scalar_one_or_none()
        if existing:
            return
        db.add(
            User(
                username=settings.admin_username,
                email=f"{settings.admin_username}@mediminder.local",
                password_hash=hash_password(settings.admin_password),
                is_active=True,
                is_admin=True,
            )
        )
        await db.commit()
        log.info("Bootstrapped admin user '%s'", settings.admin_username)
