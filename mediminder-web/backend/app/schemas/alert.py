from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    medicine_id: int
    medicine_name: str
    scheduled_at: datetime
    sent_at: datetime | None
    status: str


class AlertAckIn(BaseModel):
    status: str  # acknowledged | skipped
