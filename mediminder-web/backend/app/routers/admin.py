from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Alert, Feedback, User
from app.services.security import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
async def dashboard(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    now = datetime.now(tz=timezone.utc)
    one_year_ago = now - timedelta(days=365)
    three_years_ago = now - timedelta(days=365 * 3)
    lookahead = now + timedelta(hours=48)

    # --- Users: active / inactive counts for the pie chart ------------------
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    active_users = (
        await db.execute(select(func.count(User.id)).where(User.is_active.is_(True)))
    ).scalar_one()
    inactive_users = total_users - active_users

    # --- Feedback in the last one year (positive / negative) ----------------
    fb_pos = (
        await db.execute(
            select(func.count(Feedback.id)).where(
                Feedback.sentiment == "positive",
                Feedback.created_at >= one_year_ago,
            )
        )
    ).scalar_one()
    fb_neg = (
        await db.execute(
            select(func.count(Feedback.id)).where(
                Feedback.sentiment == "negative",
                Feedback.created_at >= one_year_ago,
            )
        )
    ).scalar_one()

    # --- User signups per month for the last 3 years ------------------------
    # Do bucketing in Python so the query works on both Postgres and SQLite
    # (SQLite has no date_trunc). Cheap on our data volumes.
    rows = (
        await db.execute(
            select(User.created_at).where(User.created_at >= three_years_ago)
        )
    ).all()
    buckets: dict[str, int] = {}
    for (ts,) in rows:
        if ts is None:
            continue
        key = ts.strftime("%Y-%m")
        buckets[key] = buckets.get(key, 0) + 1
    user_trend = [{"month": k, "count": v} for k, v in sorted(buckets.items())]

    # --- Alerts: total sent so far, and upcoming in the next 48 hours ------
    alerts_sent = (
        await db.execute(select(func.count(Alert.id)).where(Alert.status.in_(["sent", "acknowledged", "skipped"])))
    ).scalar_one()
    alerts_upcoming = (
        await db.execute(
            select(func.count(Alert.id)).where(
                Alert.status == "pending",
                Alert.scheduled_at >= now,
                Alert.scheduled_at <= lookahead,
            )
        )
    ).scalar_one()

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
        },
        "feedback_last_year": {
            "positive": fb_pos,
            "negative": fb_neg,
        },
        "user_trend_3y": user_trend,
        "alerts": {
            "sent_total": alerts_sent,
            "upcoming_48h": alerts_upcoming,
        },
        "generated_at": now.isoformat(),
    }
