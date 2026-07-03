"""Admin dashboard analytics.

All grouping is done in Python (not DB-specific SQL) so the same code works on
Postgres (local/cloud) and SQLite (tests).
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Alert, Feedback, User
from ..schemas import AlertStats, SentimentCount, TrendPoint, UserStats

router = APIRouter(prefix="/api/admin/stats", tags=["admin"])


def _as_utc(dt: datetime) -> datetime:
    """Normalize possibly-naive DB timestamps (SQLite) to aware UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.get("/users", response_model=UserStats)
def user_stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    active = sum(1 for u in users if u.is_active)
    return UserStats(total=len(users), active=active, inactive=len(users) - active)


@router.get("/feedback", response_model=SentimentCount)
def feedback_stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Positive vs negative feedback counts in the last 12 months."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    rows = db.query(Feedback).all()
    pos = neg = 0
    for f in rows:
        if _as_utc(f.created_at) < cutoff:
            continue
        if f.sentiment == "positive":
            pos += 1
        elif f.sentiment == "negative":
            neg += 1
    return SentimentCount(positive=pos, negative=neg)


@router.get("/user-trend", response_model=list[TrendPoint])
def user_trend(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Monthly new-user counts over the last 3 years (36 buckets)."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=365 * 3)
    buckets: dict[str, int] = {}
    # Pre-seed 36 months so the chart has continuous points.
    y, m = start.year, start.month
    for _i in range(37):
        buckets[f"{y:04d}-{m:02d}"] = 0
        m += 1
        if m > 12:
            m = 1
            y += 1
    for u in db.query(User).all():
        created = _as_utc(u.created_at)
        if created < start:
            continue
        key = f"{created.year:04d}-{created.month:02d}"
        if key in buckets:
            buckets[key] += 1
    return [TrendPoint(period=k, count=v) for k, v in sorted(buckets.items())]


@router.get("/alerts", response_model=AlertStats)
def alert_stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=48)
    alerts = db.query(Alert).all()
    total_sent = sum(1 for a in alerts if a.status in ("sent", "taken", "skipped"))
    upcoming = sum(
        1
        for a in alerts
        if a.status == "pending" and now <= _as_utc(a.scheduled_at) <= horizon
    )
    return AlertStats(total_sent=total_sent, upcoming_48h=upcoming)
