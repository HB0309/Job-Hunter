from datetime import datetime

from pydantic import BaseModel


class JobRead(BaseModel):
    id: int
    title: str
    company: str
    location: str
    url: str
    role_family: str
    seniority: str
    fit_score: float
    status: str
    first_seen_at: datetime
    posted_at: datetime | None = None

    model_config = {"from_attributes": True}


class JobDetail(JobRead):
    description: str
    fit_label: str
    early_talent: bool
    reasoning_summary: str
    ats_keywords: list[str]
    matched_skills: list[str]
    missing_skills: list[str]


class JobStatusUpdate(BaseModel):
    status: str
