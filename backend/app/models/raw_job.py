import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ProcessingStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    REJECTED = "rejected"
    ERROR = "error"


class RawJob(Base):
    __tablename__ = "raw_jobs"
    __table_args__ = (
        Index("ix_raw_jobs_dedup", "source_id", "external_id", unique=True),
        Index("ix_raw_jobs_status", "processing_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(512), nullable=False, doc="ID from the source system")
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(512), default="")
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    description_raw: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", doc="Extra fields as JSON")
    processing_status: Mapped[str] = mapped_column(
        String(32), default=ProcessingStatus.QUEUED.value
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
