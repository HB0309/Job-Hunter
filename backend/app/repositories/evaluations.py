import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import JobEvaluation


async def create_evaluation(session: AsyncSession, raw_job_id: int, result: dict) -> JobEvaluation:
    """Persist a Claude scoring result as a JobEvaluation row. Flushes but does not commit."""
    evaluation = JobEvaluation(
        raw_job_id=raw_job_id,
        role_family=result.get("role_family", ""),
        seniority=result.get("seniority", ""),
        early_talent=bool(result.get("early_talent", False)),
        fit_score=float(result.get("fit_score", 0.0)),
        fit_label=result.get("fit_label", ""),
        keep_in_db=bool(result.get("keep_in_db", False)),
        needs_user_feedback=bool(result.get("needs_user_feedback", False)),
        ats_keywords_json=json.dumps(result.get("ats_keywords", [])),
        matched_skills_json=json.dumps(result.get("matched_skills", [])),
        missing_skills_json=json.dumps(result.get("missing_skills", [])),
        reasoning_summary=result.get("reasoning_summary", ""),
    )
    session.add(evaluation)
    await session.flush()
    return evaluation
