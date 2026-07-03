"""Alert generation and WebSocket fan-out."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


def _tz(name: str | None) -> ZoneInfo:
    """Look up an IANA timezone, defaulting to Asia/Kolkata if unknown."""
    try:
        return ZoneInfo(name or "Asia/Kolkata")
    except ZoneInfoNotFoundError:
        log.warning("Unknown timezone %r; defaulting to Asia/Kolkata", name)
        return ZoneInfo("Asia/Kolkata")


def compute_alert_times(medicine: Medicine, horizon_hours: int) -> list[datetime]:
    """Return every alert time in [now, now+horizon) for the given medicine.

    Semantics: `start_time` is a wall-clock HHMM in the medicine's local
    timezone. Slots repeat every `interval_hours` starting from that time.
    A slot whose local hour rolls past 24 belongs to the next day — the
    (hour + i*interval) // 24 term carries the day forward. Everything is
    then converted to UTC for storage and comparison.
    """
    tz = _tz(medicine.timezone)
    now_utc = datetime.now(tz=timezone.utc)
    now_local = now_utc.astimezone(tz)
    horizon_end = now_utc + timedelta(hours=horizon_hours)

    hh = int(medicine.start_time[:2])
    mm = int(medicine.start_time[2:])
    slots_per_day = max(1, 24 // medicine.interval_hours)

    out: list[datetime] = []
    day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    # Walk enough local days that the horizon is fully covered even when
    # `now` lands late in a day and the horizon spills two calendar days.
    days_to_walk = (horizon_hours // 24) + 2
    for day_off in range(days_to_walk):
        base = day + timedelta(days=day_off)
        for i in range(slots_per_day):
            slot_offset = i * medicine.interval_hours  # hours past midnight
            slot_dt_local = base.replace(hour=hh, minute=mm) + timedelta(hours=slot_offset)
            slot_dt_utc = slot_dt_local.astimezone(timezone.utc)
            if now_utc <= slot_dt_utc < horizon_end:
                out.append(slot_dt_utc)
    return sorted(out)


async def materialize_alerts_for_medicine(db: AsyncSession, medicine: Medicine, horizon_hours: int) -> int:
    """Ensure alert rows exist for every slot in the horizon. Idempotent.

    Also self-heals: any pending future alert that doesn't match a currently
    computed slot is deleted, so timezone/schedule fixes take effect on the
    next scheduler tick without leaving stale rows behind. History rows
    (sent/acknowledged/skipped) are never touched.
    """
    from sqlalchemy import delete  # local import — sqlalchemy import kept minimal in the module

    times = compute_alert_times(medicine, horizon_hours)
    times_set = set(times)
    now_utc = datetime.now(tz=timezone.utc)

    # Fetch pending future rows so we can decide which to keep vs delete.
    existing_rows = (
        await db.execute(
            select(Alert).where(
                Alert.medicine_id == medicine.id,
                Alert.status == "pending",
                Alert.scheduled_at >= now_utc,
            )
        )
    ).scalars().all()

    stale_ids = [
        row.id for row in existing_rows
        # DB returns tz-aware; compare against tz-aware `times`.
        if (row.scheduled_at if row.scheduled_at.tzinfo else row.scheduled_at.replace(tzinfo=timezone.utc))
        not in times_set
    ]
    if stale_ids:
        await db.execute(delete(Alert).where(Alert.id.in_(stale_ids)))
        log.info("Removed %d stale future alerts for medicine %s", len(stale_ids), medicine.id)

    existing = {
        (row.scheduled_at if row.scheduled_at.tzinfo else row.scheduled_at.replace(tzinfo=timezone.utc))
        for row in existing_rows
        if row.id not in set(stale_ids)
    }

    created = 0
    for t in times:
        if t in existing:
            continue
        db.add(Alert(user_id=medicine.user_id, medicine_id=medicine.id, scheduled_at=t, status="pending"))
        created += 1
    if created or stale_ids:
        await db.commit()
    return created


async def scheduler_tick(horizon_hours: int) -> None:
    """One iteration of the periodic scheduler."""
    async with SessionLocal() as db:
        # 1. Refresh future alerts for every active medicine.
        meds = (await db.execute(select(Medicine).where(Medicine.is_deleted.is_(False)))).scalars().all()
        for m in meds:
            await materialize_alerts_for_medicine(db, m, horizon_hours)

        # 2. Deliver pending alerts whose time has come, but ONLY for
        # medicines that are still active. If a medicine was soft-deleted
        # after alerts were materialized, its orphaned rows must not fire.
        now = datetime.now(tz=timezone.utc)
        due = (
            await db.execute(
                select(Alert, Medicine)
                .join(Medicine, Alert.medicine_id == Medicine.id)
                .where(
                    Alert.status == "pending",
                    Alert.scheduled_at <= now,
                    Medicine.is_deleted.is_(False),
                )
            )
        ).all()
        for alert, med in due:
            alert.status = "sent"
            alert.sent_at = now
            await manager.push(
                alert.user_id,
                {
                    "type": "alert",
                    "alert_id": alert.id,
                    "medicine_id": alert.medicine_id,
                    "medicine_name": med.name,
                    "scheduled_at": alert.scheduled_at.isoformat(),
                },
            )
        if due:
            await db.commit()
            log.info("Delivered %d alerts", len(due))
