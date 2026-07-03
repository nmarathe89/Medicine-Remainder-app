"""Synthetic data seeder.

Idempotent: safe to run multiple times. Produces a small, kilobyte-scale
dataset that populates every dashboard panel:

  * 24 users (18 active / 6 inactive), spread across the last 3 years
  * 3-4 medicines per active user
  * Feedback records (positive + negative) in the last year
  * Alerts: some in the past (status=sent) so "sent so far" > 0, and some
    pending in the next 48h so "upcoming" > 0.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal, init_models
from app.models import Alert, Feedback, Medicine, User
from app.services.security import hash_password

random.seed(42)

MEDICINE_TYPES = ["Bottle", "Pill", "Syringe", "Tablet"]
INTERVALS = [6, 8, 12, 24]
START_TIMES = ["0800", "0900", "1200", "1800", "2100"]
MED_NAMES = [
    "Paracetamol", "Ibuprofen", "Aspirin", "Amoxicillin", "Metformin",
    "Atorvastatin", "Cetirizine", "Omeprazole", "Vitamin D", "Insulin",
    "Losartan", "Ranitidine", "Salbutamol", "Levothyroxine", "Loratadine",
]
POS_FEEDBACK = [
    "The reminders are on time, thank you!",
    "Great UX, kept me on schedule.",
    "Love the browser notifications.",
    "Simple and works. Recommended.",
]
NEG_FEEDBACK = [
    "Missed a reminder once.",
    "The dashboard could show more history.",
    "Wish there was a snooze button.",
]


async def seed() -> None:
    await init_models()
    settings = get_settings()

    async with SessionLocal() as db:
        # Skip if we've already seeded (idempotency check).
        existing_users = (await db.execute(select(User))).scalars().all()
        # The bootstrap admin created by main.py counts as 1. Seed only if we
        # haven't added synthetic accounts on top of it.
        if len(existing_users) > 5:
            print("Seed already applied; skipping.")
            return

        now = datetime.now(tz=timezone.utc)
        users: list[User] = []
        for i in range(24):
            # Spread signups over the last 3 years to populate the trend chart.
            days_ago = random.randint(0, 365 * 3)
            created = now - timedelta(days=days_ago)
            is_active = i < 18  # 18 active, 6 inactive
            u = User(
                username=f"user{i+1:02d}",
                email=f"user{i+1:02d}@mediminder.local",
                password_hash=hash_password("password123"),
                is_active=is_active,
                is_admin=False,
                created_at=created,
                last_login_at=(created + timedelta(days=random.randint(0, 30))) if is_active else None,
            )
            db.add(u)
            users.append(u)
        await db.commit()
        for u in users:
            await db.refresh(u)

        # Medicines for active users only.
        meds: list[Medicine] = []
        for u in users:
            if not u.is_active:
                continue
            for _ in range(random.randint(2, 4)):
                m = Medicine(
                    user_id=u.id,
                    name=random.choice(MED_NAMES) + f"-{random.randint(1,999)}",
                    dosage_mg=random.choice([0, 50, 100, 250, 500]),
                    medicine_type=random.choice(MEDICINE_TYPES),
                    interval_hours=random.choice(INTERVALS),
                    start_time=random.choice(START_TIMES),
                    created_at=now - timedelta(days=random.randint(0, 90)),
                )
                db.add(m)
                meds.append(m)
        await db.commit()
        for m in meds:
            await db.refresh(m)

        # Feedback in the last year: mix of positive and negative.
        for u in users[:20]:
            for _ in range(random.randint(1, 3)):
                sentiment = "positive" if random.random() < 0.7 else "negative"
                msg = random.choice(POS_FEEDBACK if sentiment == "positive" else NEG_FEEDBACK)
                db.add(
                    Feedback(
                        user_id=u.id,
                        sentiment=sentiment,
                        message=msg,
                        created_at=now - timedelta(days=random.randint(0, 365)),
                    )
                )
        await db.commit()

        # Past alerts (delivered) — to make "sent so far" meaningful.
        for m in meds:
            for d in range(1, random.randint(2, 8)):
                past = now - timedelta(days=d, hours=random.randint(0, 10))
                db.add(
                    Alert(
                        user_id=m.user_id,
                        medicine_id=m.id,
                        scheduled_at=past,
                        sent_at=past,
                        status=random.choice(["sent", "acknowledged", "skipped"]),
                    )
                )
        # Upcoming alerts in the next 48h.
        for m in meds[:15]:
            for h in [4, 10, 18, 28, 40]:
                db.add(
                    Alert(
                        user_id=m.user_id,
                        medicine_id=m.id,
                        scheduled_at=now + timedelta(hours=h),
                        status="pending",
                    )
                )
        await db.commit()

        print(f"Seeded {len(users)} users, {len(meds)} medicines, and alerts.")


if __name__ == "__main__":
    asyncio.run(seed())
