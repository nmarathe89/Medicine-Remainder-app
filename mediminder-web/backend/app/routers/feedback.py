from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Feedback, User
from app.schemas.feedback import FeedbackIn, FeedbackOut
from app.services.security import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=201)
async def submit(
    body: FeedbackIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackOut:
    fb = Feedback(user_id=user.id, **body.model_dump())
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return FeedbackOut.model_validate(fb)


@router.get("/mine", response_model=list[FeedbackOut])
async def mine(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FeedbackOut]:
    rows = (
        await db.execute(select(Feedback).where(Feedback.user_id == user.id).order_by(Feedback.created_at.desc()))
    ).scalars().all()
    return [FeedbackOut.model_validate(f) for f in rows]
