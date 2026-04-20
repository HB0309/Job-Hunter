from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    raw_job_id: int
    decision: str  # keep | reject | skip
    notes: str = ""

# TODO Phase 2: wire into routes_feedback
