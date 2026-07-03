from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    sentiment: Literal["positive", "negative"]
    message: str = Field(min_length=1, max_length=1024)


class FeedbackOut(FeedbackIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
