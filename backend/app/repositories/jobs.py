import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import JobEvaluation
from app.models.job import Job, JobStatus
from app.models.raw_job import RawJob


def _extract_posted_at(metadata_json: str | None, source_type: str) -> datetime | None:
    """Parse posted/published date from raw_job metadata_json."""
    if not metadata_json:
        return None
    try:
        meta = json.loads(metadata_json)
    except Exception:
        return None
    try:
        if source_type == "ashby":
            raw = meta.get("published_at")
        elif source_type == "greenhouse":
            raw = meta.get("updated_at")
        elif source_type == "lever":
            val = meta.get("created_at")
            if val:
                ts = int(val)
                # Lever returns Unix seconds (10-digit) not milliseconds (13-digit).
                # Divide by 1000 only if clearly in milliseconds range.
                if ts > 1_000_000_000_000:
                    ts = ts // 1000
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            return None
        elif source_type == "workday":
            raw = meta.get("posted_on")  # "Posted Today", "Posted 3 Days Ago" — not a timestamp
            return None  # Workday gives human-readable strings, not ISO dates; treat as recent
        elif source_type == "linkedin":
            raw = meta.get("posted_at")
        else:
            return None
        if raw:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        pass
    return None


async def get_jobs(
    session: AsyncSession,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    where = "WHERE j.status = :status" if status else ""
    # Filter by first_seen_at (when WE discovered the job) not posted_at.
    # posted_at is just a display label — it reflects when the company originally
    # listed the role, which can be months ago for evergreen positions.
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)
    where_parts = [where.replace("WHERE ", "")] if where else []
    where_parts.append("j.first_seen_at >= :cutoff")
    where_clause = "WHERE " + " AND ".join(where_parts)

    rows = await session.execute(text(f"""
        SELECT j.id, j.title, j.company, j.location, j.url,
               j.role_family, j.seniority, j.fit_score, j.status, j.first_seen_at,
               r.metadata_json, s.source_type
        FROM jobs j
        JOIN raw_jobs r ON j.raw_job_id = r.id
        JOIN sources s ON r.source_id = s.id
        {where_clause}
        ORDER BY j.fit_score DESC
        LIMIT :limit OFFSET :offset
    """), {"status": status, "cutoff": cutoff, "limit": limit, "offset": offset}
         if status else {"cutoff": cutoff, "limit": limit, "offset": offset})

    results = []
    for r in rows.mappings():
        d = dict(r)
        posted_at = _extract_posted_at(d.pop("metadata_json"), d.pop("source_type"))
        d["posted_at"] = posted_at
        results.append(d)
    return results


async def get_job_detail(session: AsyncSession, job_id: int) -> dict | None:
    row = await session.execute(text("""
        SELECT j.id, j.title, j.company, j.location, j.url, j.description,
               j.role_family, j.seniority, j.fit_score, j.status, j.first_seen_at,
               e.fit_label, e.early_talent, e.reasoning_summary,
               e.ats_keywords_json, e.matched_skills_json, e.missing_skills_json
        FROM jobs j
        JOIN job_evaluations e ON j.evaluation_id = e.id
        WHERE j.id = :id
    """), {"id": job_id})
    r = row.mappings().first()
    if not r:
        return None
    d = dict(r)
    d["ats_keywords"] = json.loads(d.pop("ats_keywords_json") or "[]")
    d["matched_skills"] = json.loads(d.pop("matched_skills_json") or "[]")
    d["missing_skills"] = json.loads(d.pop("missing_skills_json") or "[]")
    return d


async def update_job_status(session: AsyncSession, job_id: int, status: str) -> bool:
    result = await session.execute(
        text("UPDATE jobs SET status = :status WHERE id = :id RETURNING id"),
        {"id": job_id, "status": status},
    )
    await session.commit()
    return result.first() is not None


async def insert_from_evaluation(
    session: AsyncSession,
    raw_job: RawJob,
    evaluation: JobEvaluation,
) -> Job:
    """Create a canonical Job row from a scored raw_job. Flushes but does not commit."""
    job = Job(
        raw_job_id=raw_job.id,
        evaluation_id=evaluation.id,
        title=raw_job.title,
        company=raw_job.company,
        location=raw_job.location or "",
        url=raw_job.url,
        description=raw_job.description_raw or "",
        role_family=evaluation.role_family,
        seniority=evaluation.seniority,
        fit_score=evaluation.fit_score,
        status=JobStatus.NEW.value,
    )
    session.add(job)
    await session.flush()
    return job
