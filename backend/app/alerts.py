"""Dose-schedule / alert generation.

Ported from the Flutter app's scheduleNotification() in
lib/src/ui/new_entry/new_entry.dart: given a start time and an interval, the
app fired (24 / interval) reminders per day. Here we materialize those dose
times into Alert rows so the browser can poll for due reminders and the admin
dashboard can count sent/upcoming alerts.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .models import Alert, Medicine


def _naive(dt: datetime) -> datetime:
    """Drop tzinfo for stable cross-backend comparison/dedup.

    SQLite stores naive datetimes while Postgres stores aware ones; comparing
    the two raises. We normalize to naive-UTC for internal set membership and
    filtering so the same code path works on both backends.
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def doses_per_day(interval_hours: int) -> int:
    return max(1, 24 // interval_hours)


def dose_times_for_day(medicine: Medicine, day: datetime) -> list[datetime]:
    """Return the scheduled datetimes for `medicine` on the given day (UTC)."""
    hour = int(medicine.start_time[:2])
    minute = int(medicine.start_time[2:])
    base = day.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=timezone.utc)
    times = []
    for i in range(doses_per_day(medicine.interval_hours)):
        times.append(base + timedelta(hours=medicine.interval_hours * i))
    return times


def generate_alerts_for_medicine(
    db: Session, medicine: Medicine, days_ahead: int = 3
) -> list[Alert]:
    """Create pending Alert rows for the next `days_ahead` days (idempotent)."""
    now = datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    created: list[Alert] = []
    existing = {
        _naive(a.scheduled_at).replace(microsecond=0)
        for a in db.query(Alert).filter(Alert.medicine_id == medicine.id).all()
    }
    for d in range(days_ahead + 1):
        day = now + timedelta(days=d)
        for t in dose_times_for_day(medicine, day):
            # Include doses already elapsed *today* (so they surface as due),
            # but never materialize doses from before today.
            if t < start_of_today:
                continue
            if _naive(t).replace(microsecond=0) in existing:
                continue
            alert = Alert(
                medicine_id=medicine.id,
                user_id=medicine.user_id,
                scheduled_at=t,
                status="pending",
            )
            db.add(alert)
            created.append(alert)
    db.flush()
    return created


def mark_due_as_sent(db: Session, user_id: int) -> list[Alert]:
    """Transition pending alerts whose time has arrived to 'sent'.

    Returns the alerts that are now due (browser will display them). This is
    what the polling endpoint calls.
    """
    now = datetime.now(timezone.utc)
    # Filter in Python against a normalized value so the comparison works on
    # both SQLite (naive columns) and Postgres (aware columns).
    now_cmp = _naive(now)
    pending = (
        db.query(Alert)
        .filter(Alert.user_id == user_id, Alert.status == "pending")
        .all()
    )
    due = [a for a in pending if _naive(a.scheduled_at) <= now_cmp]
    for a in due:
        a.status = "sent"
        a.sent_at = now
    db.flush()
    return due
