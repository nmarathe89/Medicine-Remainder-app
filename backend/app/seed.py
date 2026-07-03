"""Idempotent synthetic-data seeder.

Loads a small (KB-sized) synthetic dataset from seed_data/seed.json so the
admin dashboard renders meaningful charts (users pie, feedback, 3-year trend,
alert counts) out of the box. Safe to run on every startup — it no-ops if the
seed admin already exists.

Deterministic (no randomness) so the committed footprint stays stable and the
data spread is reproducible for demos and tests.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from .alerts import generate_alerts_for_medicine
from .models import Alert, Feedback, Medicine, User
from .security import hash_password

SEED_DIR = Path(__file__).resolve().parent.parent / "seed_data"
SEED_FILE = SEED_DIR / "seed.json"


def _dt_months_ago(months: int) -> datetime:
    now = datetime.now(timezone.utc)
    y, m = now.year, now.month - months
    while m <= 0:
        m += 12
        y -= 1
    return now.replace(year=y, month=m)


def seed(db: Session) -> bool:
    """Populate synthetic data. Returns True if seeding ran, False if skipped."""
    if not SEED_FILE.exists():
        return False
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))

    # Idempotency guard: if the seed admin exists, assume already seeded.
    if db.query(User).filter(User.username == data["admin"]["username"]).first():
        return False

    # Admin account
    admin = User(
        username=data["admin"]["username"],
        password_hash=hash_password(data["admin"]["password"]),
        role="admin",
        is_active=True,
        created_at=_dt_months_ago(30),
    )
    db.add(admin)

    # Regular users spread across the last 3 years for the trend chart.
    users: list[User] = []
    for u in data["users"]:
        user = User(
            username=u["username"],
            password_hash=hash_password(u["password"]),
            role="user",
            is_active=u.get("is_active", True),
            created_at=_dt_months_ago(u["created_months_ago"]),
        )
        db.add(user)
        users.append(user)
    db.flush()

    # Feedback in the last 12 months.
    for fb in data["feedback"]:
        target = users[fb["user_index"] % len(users)]
        db.add(
            Feedback(
                user_id=target.id,
                sentiment=fb["sentiment"],
                message=fb.get("message", ""),
                created_at=_dt_months_ago(fb["months_ago"]),
            )
        )

    # Medicines + generated upcoming alerts for a couple of users.
    for med in data["medicines"]:
        target = users[med["user_index"] % len(users)]
        medicine = Medicine(
            user_id=target.id,
            name=med["name"],
            dosage=med.get("dosage", 0),
            medicine_type=med.get("medicine_type", "None"),
            interval_hours=med["interval_hours"],
            start_time=med["start_time"],
        )
        db.add(medicine)
        db.flush()
        generate_alerts_for_medicine(db, medicine)

    # Historical "sent" alerts so the dashboard shows a non-zero sent count.
    if users:
        first_med = db.query(Medicine).first()
        if first_med:
            base = datetime.now(timezone.utc) - timedelta(days=10)
            for i in range(data.get("historical_sent_alerts", 0)):
                db.add(
                    Alert(
                        medicine_id=first_med.id,
                        user_id=first_med.user_id,
                        scheduled_at=base + timedelta(hours=6 * i),
                        status="taken",
                        sent_at=base + timedelta(hours=6 * i),
                    )
                )

    db.commit()
    return True
