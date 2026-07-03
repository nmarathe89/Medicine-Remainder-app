"""FastAPI application entrypoint.

Same code runs locally (Docker Compose) and on GCP Cloud Run. Environment-
specific behaviour is confined to config.py / secrets_provider.py.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import SessionLocal, init_db
from .routers import admin, alerts, auth, feedback, medicines

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    if settings.seed_on_startup:
        from .seed import seed

        db = SessionLocal()
        try:
            if seed(db):
                logger.info("Synthetic seed data loaded.")
        except Exception as exc:  # don't block startup on seed issues
            logger.warning("Seeding skipped/failed: %s", exc)
        finally:
            db.close()
    yield


app = FastAPI(title="Mediminder API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(medicines.router)
app.include_router(alerts.router)
app.include_router(feedback.router)
app.include_router(admin.router)


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
