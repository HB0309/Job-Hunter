from pydantic import BaseModel


class EvaluationResult(BaseModel):
    """Expected structured output from Claude scoring. Phase 2."""
    role_family: str
    seniority: str
    early_talent: bool
    fit_score: float
    fit_label: str
    keep_in_db: bool
    needs_user_feedback: bool
    ats_keywords: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    reasoning_summary: str

# TODO Phase 2: implement Claude structured JSON output using this schema
