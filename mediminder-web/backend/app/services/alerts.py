"""Alert generation and WebSocket fan-out."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.models import Alert, Medicine

log = logging.getLogger(__name__)


class ConnectionManager:
    """Keeps live WebSocket connections keyed by user id.

    A single user may have multiple sessions/tabs open; every one of them
    receives every alert broadcast for that user.
    """

    def __init__(self) -> None:
        self._conns: dict[int, set] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, ws) -> None:
        await ws.accept()
        async with self._lock:
            self._conns[user_id].add(ws)

    async def disconnect(self, user_id: int, ws) -> None:
        async with self._lock:
            self._conns[user_id].discard(ws)
            if not self._conns[user_id]:
                self._conns.pop(user_id, None)

    async def push(self, user_id: int, payload: dict) -> None:
        dead = []
        for ws in list(self._conns.get(user_id, set())):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)


manager = ConnectionManager()


def compute_alert_times(medicine: Medicine, horizon_hours: int) -> list[datetime]:
    """Return every alert time in [now, now+horizon) for the given medicine.

    Mirrors the Flutter app's daily-repeat semantics: N slots per day
    (24 / interval), starting at `start_time`, repeating each day.
    """
    now = datetime.now(tz=timezone.utc)
    horizon_end = now + timedelta(hours=horizon_hours)
    hh = int(medicine.start_time[:2])
    mm = int(medicine.start_time[2:])
    slots_per_day = max(1, 24 // medicine.interval_hours)

    out: list[datetime] = []
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Look at today, tomorrow, and the day after (covers up to a 48h horizon).
    for day_off in range((horizon_hours // 24) + 2):
        base = day + timedelta(days=day_off)
        for i in range(slots_per_day):
            slot_hour = (hh + i * medicine.interval_hours) % 24
            candidate = base.replace(hour=slot_hour, minute=mm)
            if now <= candidate < horizon_end:
                out.append(candidate)
    return out


async def materialize_alerts_for_medicine(db: AsyncSession, medicine: Medicine, horizon_hours: int) -> int:
    """Ensure alert rows exist for every slot in the horizon. Idempotent."""
    times = compute_alert_times(medicine, horizon_hours)
    if not times:
        return 0

    result = await db.execute(
        select(Alert.scheduled_at).where(
            Alert.medicine_id == medicine.id,
            Alert.scheduled_at.in_(times),
        )
    )
    existing = {row[0] for row in result.all()}
    created = 0
    for t in times:
        if t in existing:
            continue
        db.add(Alert(user_id=medicine.user_id, medicine_id=medicine.id, scheduled_at=t, status="pending"))
        created += 1
    if created:
        await db.commit()
    return created


async def scheduler_tick(horizon_hours: int) -> None:
    """One iteration of the periodic scheduler."""
    async with SessionLocal() as db:
        # 1. Refresh future alerts for every active medicine.
        meds = (await db.execute(select(Medicine).where(Medicine.is_deleted.is_(False)))).scalars().all()
        for m in meds:
            await materialize_alerts_for_medicine(db, m, horizon_hours)

        # 2. Deliver pending alerts whose time has come.
        now = datetime.now(tz=timezone.utc)
        due = (
            await db.execute(
                select(Alert).where(Alert.status == "pending", Alert.scheduled_at <= now)
            )
        ).scalars().all()
        for alert in due:
            med = await db.get(Medicine, alert.medicine_id)
            alert.status = "sent"
            alert.sent_at = now
            await manager.push(
                alert.user_id,
                {
                    "type": "alert",
                    "alert_id": alert.id,
                    "medicine_id": alert.medicine_id,
                    "medicine_name": med.name if med else "",
                    "scheduled_at": alert.scheduled_at.isoformat(),
                },
            )
        if due:
            await db.commit()
            log.info("Delivered %d alerts", len(due))
