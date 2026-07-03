"""User feedback submission and listing."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Feedback, User
from ..schemas import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=201)
def submit_feedback(
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fb = Feedback(user_id=user.id, sentiment=payload.sentiment, message=payload.message)
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


@router.get("", response_model=list[FeedbackOut])
def my_feedback(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Feedback)
        .filter(Feedback.user_id == user.id)
        .order_by(Feedback.created_at.desc())
        .all()
    )
