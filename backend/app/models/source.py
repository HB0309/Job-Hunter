import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SourceType(str, enum.Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    COMPANY_SITE = "company_site"
    APIFY_LINKEDIN = "apify_linkedin"
    APIFY_INDEED = "apify_indeed"
    WORKDAY = "workday"
    WORKDAY_CSRF = "workday_csrf"
    GOOGLE_CAREERS = "google_careers"
    AMAZON_JOBS = "amazon_jobs"
    APPLE_JOBS = "apple_jobs"
    MICROSOFT_CAREERS = "microsoft_careers"
    META_CAREERS = "meta_careers"
    SMARTRECRUITERS = "smartrecruiters"
    JOBRIGHT = "jobright"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    config: Mapped[str] = mapped_column(String(1024), default="", doc="JSON config blob, e.g. board token")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
