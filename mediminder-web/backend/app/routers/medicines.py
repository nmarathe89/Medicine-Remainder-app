from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from datetime import datetime, timezone

from fastapi import Response
from sqlalchemy import delete as sql_delete

from app.database import get_db
from app.models import Alert, Medicine, User
from app.schemas.medicine import MedicineIn, MedicineOut
from app.services.alerts import materialize_alerts_for_medicine
from app.services.security import get_current_user

router = APIRouter(prefix="/api/medicines", tags=["medicines"])


@router.get("", response_model=list[MedicineOut])
async def list_mine(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MedicineOut]:
    rows = (
        await db.execute(
            select(Medicine).where(Medicine.user_id == user.id, Medicine.is_deleted.is_(False))
        )
    ).scalars().all()
    return [MedicineOut.model_validate(m) for m in rows]


@router.post("", response_model=MedicineOut, status_code=201)
async def create(
    body: MedicineIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MedicineOut:
    dup = (
        await db.execute(
            select(Medicine).where(
                Medicine.user_id == user.id,
                Medicine.name == body.name,
                Medicine.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status_code=409, detail="Medicine name already exists")

    m = Medicine(user_id=user.id, **body.model_dump())
    db.add(m)
    await db.commit()
    await db.refresh(m)

    # Pre-materialize alerts for the lookahead window so the admin dashboard
    # can show "next 48h" immediately.
    await materialize_alerts_for_medicine(db, m, get_settings().alert_lookahead_hours)
    return MedicineOut.model_validate(m)


@router.delete("/{med_id}", status_code=204, response_class=Response)
async def delete(
    med_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Soft-delete a medicine and cancel its future pending alerts.

    Past alerts (sent / acknowledged / skipped) are retained as history so
    the user can still audit what happened. Future pending rows are purged
    so no zombie notification fires after the user tapped Delete.
    """
    m = await db.get(Medicine, med_id)
    if not m or m.user_id != user.id or m.is_deleted:
        raise HTTPException(status_code=404, detail="Not found")
    m.is_deleted = True
    now = datetime.now(tz=timezone.utc)
    await db.execute(
        sql_delete(Alert).where(
            Alert.medicine_id == m.id,
            Alert.status == "pending",
            Alert.scheduled_at >= now,
        )
    )
    await db.commit()
    return Response(status_code=204)
