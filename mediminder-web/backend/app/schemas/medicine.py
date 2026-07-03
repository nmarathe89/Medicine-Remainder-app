from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MedicineIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    dosage_mg: int = Field(ge=0, le=10000, default=0)
    medicine_type: Literal["Bottle", "Pill", "Syringe", "Tablet"]
    interval_hours: Literal[6, 8, 12, 24]
    start_time: str = Field(pattern=r"^\d{4}$")  # HHMM in the user's timezone
    timezone: str = Field(default="Asia/Kolkata", max_length=64)


class MedicineOut(MedicineIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
