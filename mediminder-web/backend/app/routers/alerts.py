from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models import Alert, Medicine, Session as SessionRow, User
from app.schemas.alert import AlertAckIn, AlertOut
from app.services.alerts import manager
from app.services.security import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def my_alerts(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    """History for the current user.

    Returns every alert row — including those belonging to soft-deleted
    medicines — with a `medicine_deleted` flag so the UI can label them.
    We intentionally keep the history visible because a "medicine deleted"
    row is meaningful audit information ("I stopped taking Metformin last
    Tuesday"). See docs/DECISIONS.md#d-22.
    """
    rows = (
        await db.execute(
            select(Alert, Medicine.name, Medicine.is_deleted)
            .join(Medicine, Alert.medicine_id == Medicine.id)
            .where(Alert.user_id == user.id)
            .order_by(Alert.scheduled_at.desc())
            .limit(limit)
        )
    ).all()
    return [
        AlertOut(
            id=a.id,
            medicine_id=a.medicine_id,
            medicine_name=name,
            medicine_deleted=bool(is_deleted),
            scheduled_at=a.scheduled_at,
            sent_at=a.sent_at,
            status=a.status,
        )
        for a, name, is_deleted in rows
    ]


@router.post("/{alert_id}/ack", response_model=AlertOut)
async def acknowledge(
    alert_id: int,
    body: AlertAckIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    if body.status not in ("acknowledged", "skipped"):
        raise HTTPException(status_code=400, detail="status must be acknowledged|skipped")
    alert = await db.get(Alert, alert_id)
    if not alert or alert.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    alert.status = body.status
    await db.commit()
    med = await db.get(Medicine, alert.medicine_id)
    return AlertOut(
        id=alert.id,
        medicine_id=alert.medicine_id,
        medicine_name=med.name if med else "",
        scheduled_at=alert.scheduled_at,
        sent_at=alert.sent_at,
        status=alert.status,
    )


ws_router = APIRouter()


@ws_router.websocket("/ws/alerts")
async def alerts_ws(websocket: WebSocket) -> None:
    """Browser opens ws://.../ws/alerts?token=<jwt> and stays connected.

    We authenticate manually (WebSocket doesn't run FastAPI's Depends chain
    the same way REST does), then park the connection until the client hangs
    up. Server-initiated pushes go through `manager.push(user_id, ...)` from
    the scheduler.
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
        jti = payload["jti"]
    except (JWTError, KeyError, ValueError):
        await websocket.close(code=4401)
        return

    async with SessionLocal() as db:
        sess = await db.get(SessionRow, jti)
        if sess is None:
            await websocket.close(code=4401)
            return
        exp = sess.expires_at if sess.expires_at.tzinfo else sess.expires_at.replace(tzinfo=timezone.utc)
        if exp < datetime.now(tz=timezone.utc):
            await websocket.close(code=4401)
            return

    await manager.connect(user_id, websocket)
    try:
        while True:
            # We don't need inbound messages; just keep the socket alive.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user_id, websocket)
