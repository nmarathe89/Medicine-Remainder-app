from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    dosage_mg: Mapped[int] = mapped_column(Integer, default=0)
    medicine_type: Mapped[str] = mapped_column(String(16))  # Bottle|Pill|Syringe|Tablet
    interval_hours: Mapped[int] = mapped_column(Integer)  # 6|8|12|24
    start_time: Mapped[str] = mapped_column(String(4))  # HHMM (local wall clock)
    # IANA timezone name (e.g. "Asia/Kolkata"). Interpreted as the user's local
    # timezone for the purpose of scheduling alerts. Kept per-medicine so a
    # single user can have reminders on trips without moving everything.
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", server_default="Asia/Kolkata")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="medicines")
    alerts = relationship("Alert", back_populates="medicine", cascade="all, delete-orphan")
