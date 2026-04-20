from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class JobEvaluation(Base):
    """Stores Claude scoring output for a raw job. Created in Phase 2."""

    __tablename__ = "job_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_job_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_jobs.id"), unique=True, nullable=False)
    role_family: Mapped[str] = mapped_column(String(128), default="")
    seniority: Mapped[str] = mapped_column(String(64), default="")
    early_talent: Mapped[bool] = mapped_column(Boolean, default=False)
    fit_score: Mapped[float] = mapped_column(Float, default=0.0)
    fit_label: Mapped[str] = mapped_column(String(32), default="")
    keep_in_db: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_user_feedback: Mapped[bool] = mapped_column(Boolean, default=False)
    ats_keywords_json: Mapped[str] = mapped_column(Text, default="[]")
    matched_skills_json: Mapped[str] = mapped_column(Text, default="[]")
    missing_skills_json: Mapped[str] = mapped_column(Text, default="[]")
    reasoning_summary: Mapped[str] = mapped_column(Text, default="")
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # TODO Phase 2: populate this table via scoring worker + Claude structured output
