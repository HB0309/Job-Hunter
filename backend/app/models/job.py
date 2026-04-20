import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class JobStatus(str, enum.Enum):
    NEW = "new"
    SAVED = "saved"
    APPLIED = "applied"
    DISMISSED = "dismissed"
    ARCHIVED = "archived"


class Job(Base):
    """Canonical jobs table — only accepted jobs land here after scoring."""

    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_status", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_job_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_jobs.id"), unique=True, nullable=False)
    evaluation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("job_evaluations.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(512), default="")
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    role_family: Mapped[str] = mapped_column(String(128), default="")
    seniority: Mapped[str] = mapped_column(String(64), default="")
    fit_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default=JobStatus.NEW.value)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # TODO Phase 3: expose status transitions via dashboard API
    # TODO Phase 4: nightly archival worker sets archived_at after 10 days unapplied
