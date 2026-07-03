"""Pydantic request/response schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_INTERVALS = {6, 8, 12, 24}
VALID_TYPES = {"Bottle", "Pill", "Syringe", "Tablet", "None"}


# ---- Auth ----
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=4, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    token_id: str
    created_at: datetime
    expires_at: datetime
    revoked: bool


# ---- Medicine ----
class MedicineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    dosage: int = Field(default=0, ge=0)
    medicine_type: str = "None"
    interval_hours: int
    start_time: str = Field(min_length=4, max_length=4)  # "HHMM"

    @field_validator("interval_hours")
    @classmethod
    def _interval(cls, v: int) -> int:
        if v not in VALID_INTERVALS:
            raise ValueError(f"interval_hours must be one of {sorted(VALID_INTERVALS)}")
        return v

    @field_validator("medicine_type")
    @classmethod
    def _type(cls, v: str) -> str:
        if v not in VALID_TYPES:
            raise ValueError(f"medicine_type must be one of {sorted(VALID_TYPES)}")
        return v

    @field_validator("start_time")
    @classmethod
    def _start(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("start_time must be HHMM digits")
        hh, mm = int(v[:2]), int(v[2:])
        if hh > 23 or mm > 59:
            raise ValueError("start_time is not a valid time")
        return v


class MedicineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    dosage: int
    medicine_type: str
    interval_hours: int
    start_time: str
    created_at: datetime
    doses_per_day: int = 0


# ---- Alert ----
class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    medicine_id: int
    scheduled_at: datetime
    status: str
    medicine_name: str = ""


class AlertAck(BaseModel):
    action: str  # taken | skipped

    @field_validator("action")
    @classmethod
    def _action(cls, v: str) -> str:
        if v not in {"taken", "skipped"}:
            raise ValueError("action must be 'taken' or 'skipped'")
        return v


# ---- Feedback ----
class FeedbackCreate(BaseModel):
    sentiment: str
    message: str = Field(default="", max_length=500)

    @field_validator("sentiment")
    @classmethod
    def _sentiment(cls, v: str) -> str:
        if v not in {"positive", "negative"}:
            raise ValueError("sentiment must be 'positive' or 'negative'")
        return v


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sentiment: str
    message: str
    created_at: datetime


# ---- Admin analytics ----
class UserStats(BaseModel):
    total: int
    active: int
    inactive: int


class SentimentCount(BaseModel):
    positive: int
    negative: int


class TrendPoint(BaseModel):
    period: str  # "YYYY-MM"
    count: int


class AlertStats(BaseModel):
    total_sent: int
    upcoming_48h: int
