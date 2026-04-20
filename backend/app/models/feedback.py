import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class FeedbackDecision(str, enum.Enum):
    KEEP = "keep"
    REJECT = "reject"
    SKIP = "skip"


class UserFeedback(Base):
    """Human feedback on borderline jobs flagged by scoring."""

    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_job_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_jobs.id"), nullable=False)
    decision: Mapped[FeedbackDecision] = mapped_column(Enum(FeedbackDecision), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # TODO Phase 2: wire into scoring worker feedback loop
