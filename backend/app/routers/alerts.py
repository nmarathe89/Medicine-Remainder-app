"""Alert endpoints — browser polling for reminders (no email/SMS)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..alerts import _naive, mark_due_as_sent
from ..database import get_db
from ..deps import get_current_user
from ..models import Alert, User
from ..schemas import AlertAck, AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _to_out(a: Alert) -> AlertOut:
    out = AlertOut.model_validate(a)
    out.medicine_name = a.medicine.name if a.medicine else ""
    return out


@router.get("/due", response_model=list[AlertOut])
def due_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Called by the React client on a poll interval.

    Transitions any now-due pending alerts to 'sent' and returns the alerts
    that should be shown as browser toasts (status sent, not yet acknowledged).
    """
    mark_due_as_sent(db, user.id)
    db.commit()
    rows = (
        db.query(Alert)
        .filter(Alert.user_id == user.id, Alert.status == "sent")
        .order_by(Alert.scheduled_at)
        .all()
    )
    return [_to_out(a) for a in rows]


@router.get("/upcoming", response_model=list[AlertOut])
def upcoming_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now_cmp = _naive(datetime.now(timezone.utc))
    rows = (
        db.query(Alert)
        .filter(Alert.user_id == user.id, Alert.status == "pending")
        .order_by(Alert.scheduled_at)
        .all()
    )
    upcoming = [a for a in rows if _naive(a.scheduled_at) > now_cmp]
    return [_to_out(a) for a in upcoming[:50]]


@router.post("/{alert_id}/ack", response_model=AlertOut)
def acknowledge(
    alert_id: int,
    payload: AlertAck,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.get(Alert, alert_id)
    if a is None or a.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    a.status = payload.action  # taken | skipped
    db.commit()
    db.refresh(a)
    return _to_out(a)
