import json
import re
import sys
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.evaluation import JobEvaluation
from app.models.job import Job, JobStatus
from app.models.raw_job import RawJob

_TAG_RE = re.compile(r"<[^>]+>")

MAX_JOB_AGE_DAYS = 20       # auto-reject jobs older than this (if date is known)
SIMILARITY_THRESHOLD = 2    # auto-keep remaining jobs with ≥ N skill matches to kept set


def _strip_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _get_job_age_days(metadata_json: str) -> int | None:
    """Parse job age in days from metadata_json.

    Returns None if the posting date is unknown — those are kept by default.
    Handles four source date formats:
      - Workday:     {"posted_on": "Posted 5 Days Ago"}
      - Apple:       {"posted_date": "2025-03-10"}
      - Lever:       {"created_at": 1700000000000}  (ms timestamp)
      - Greenhouse:  {"updated_at": "2025-03-10T00:00:00Z"}
    """
    if not metadata_json:
        return None
    try:
        meta = json.loads(metadata_json)
    except (json.JSONDecodeError, TypeError):
        return None

    now = datetime.now(timezone.utc)

    # Workday: "Posted X Days Ago" / "Posted X+ Days Ago"
    posted_on = meta.get("posted_on", "")
    if posted_on:
        m = re.search(r"(\d+)\+?\s*Days?\s+Ago", posted_on, re.IGNORECASE)
        if m:
            return int(m.group(1))

    # Apple: ISO date string (may lack timezone)
    posted_date = meta.get("posted_date", "")
    if posted_date:
        try:
            dt = datetime.fromisoformat(posted_date.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (now - dt).days
        except ValueError:
            pass

    # Lever: millisecond Unix timestamp
    created_at = meta.get("created_at")
    if created_at and isinstance(created_at, (int, float)) and created_at > 1_000_000_000_000:
        dt = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
        return (now - dt).days

    # Greenhouse / SmartRecruiters: ISO datetime string
    for key in ("updated_at", "posted_at", "created_at"):
        val = meta.get(key, "")
        if val and isinstance(val, str):
            try:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return (now - dt).days
            except ValueError:
                continue

    return None


def _extract_skills(description: str) -> set[str]:
    """Extract matched skill categories from a job description."""
    try:
        # scripts/ lives at /app/scripts/ inside Docker; /app is the WORKDIR
        if "/app/scripts" not in sys.path and "/app" not in sys.path:
            sys.path.insert(0, "/app")
        from scripts.skill_match import extract_matched_skills  # type: ignore[import]
        return set(extract_matched_skills(description or ""))
    except ImportError:
        return set()


router = APIRouter()


@router.get("/")
async def list_raw_jobs(
    status: str | None = Query(None, description="Filter by processing_status: queued, processing, processed, rejected, error"),
    search: str | None = Query(None, description="Search title or company"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(RawJob).order_by(RawJob.fetched_at.desc())
    if status:
        stmt = stmt.where(RawJob.processing_status == status)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            RawJob.title.ilike(pattern) | RawJob.company.ilike(pattern)
        )
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "url": j.url,
            "processing_status": j.processing_status,
            "fetched_at": j.fetched_at,
        }
        for j in jobs
    ]


@router.get("/count")
async def count_raw_jobs(
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(RawJob.processing_status, func.count()).group_by(RawJob.processing_status)
    )
    return {row[0]: row[1] for row in result.all()}


@router.get("/review")
async def list_review_jobs(
    search: str | None = Query(None),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Return jobs awaiting user decision.

    Before returning, auto-rejects any job whose known posting date is older
    than MAX_JOB_AGE_DAYS days. Jobs with no date info are kept.
    """
    result = await session.execute(
        select(RawJob).where(RawJob.processing_status.in_(["queued", "review"]))
    )
    all_pending = result.scalars().all()

    # ── Auto-expire stale jobs ────────────────────────────────────────────────
    expired_ids: list[int] = []
    fresh_jobs: list[RawJob] = []
    for job in all_pending:
        age = _get_job_age_days(job.metadata_json or "")
        if age is not None and age > MAX_JOB_AGE_DAYS:
            expired_ids.append(job.id)
        else:
            fresh_jobs.append(job)

    if expired_ids:
        for job_id in expired_ids:
            await session.execute(text("""
                INSERT INTO job_evaluations
                    (raw_job_id, role_family, seniority, early_talent, fit_score,
                     fit_label, keep_in_db, needs_user_feedback,
                     ats_keywords_json, matched_skills_json, missing_skills_json,
                     reasoning_summary)
                VALUES
                    (:raw_job_id, 'unknown', 'unknown', false, 5.0,
                     'poor_fit', false, false,
                     '[]', '[]', '[]', 'Auto-rejected: posting > 20 days old')
                ON CONFLICT (raw_job_id) DO NOTHING
            """), {"raw_job_id": job_id})
            await session.execute(
                text("UPDATE raw_jobs SET processing_status = 'processed' WHERE id = :id"),
                {"id": job_id},
            )
        await session.commit()

    # ── Apply search + pagination to fresh jobs ───────────────────────────────
    if search:
        pattern = search.lower()
        fresh_jobs = [
            j for j in fresh_jobs
            if pattern in (j.title or "").lower() or pattern in (j.company or "").lower()
        ]

    fresh_jobs.sort(key=lambda j: (j.processing_status or "", j.company or "", j.title or ""), reverse=False)
    paginated = fresh_jobs[offset: offset + limit]

    return {
        "auto_expired": len(expired_ids),
        "total": len(fresh_jobs),
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "url": j.url,
                "fetched_at": j.fetched_at,
                "processing_status": j.processing_status,
                "description_snippet": _strip_html(j.description_raw or "")[:300],
            }
            for j in paginated
        ],
    }


class ReviewDecision(BaseModel):
    keep_ids: list[int]


@router.post("/review/decide")
async def decide_review_jobs(
    body: ReviewDecision,
    session: AsyncSession = Depends(get_session),
):
    """Keep selected jobs and auto-keep similar ones, reject the rest.

    Similarity logic: extract skill categories from each manually-kept job's
    description, union them into a reference set, then auto-keep any pending
    job with ≥ SIMILARITY_THRESHOLD skills in common with that reference set.
    Jobs that are neither manually kept nor similar are rejected.
    """
    manual_keep_set = set(body.keep_ids)

    # Get all pending jobs
    result = await session.execute(
        select(RawJob).where(RawJob.processing_status.in_(["queued", "review"]))
    )
    all_raw = result.scalars().all()
    all_ids = {r.id for r in all_raw}

    # ── Build reference skill set from manually-kept jobs ─────────────────────
    kept_raw = [r for r in all_raw if r.id in manual_keep_set]
    reference_skills: set[str] = set()
    for raw in kept_raw:
        reference_skills |= _extract_skills(raw.description_raw or "")

    # ── Expand: auto-keep pending jobs similar to the manual selection ────────
    auto_keep_ids: set[int] = set()
    if reference_skills:
        for raw in all_raw:
            if raw.id in manual_keep_set:
                continue
            job_skills = _extract_skills(raw.description_raw or "")
            overlap = len(reference_skills & job_skills)
            if overlap >= SIMILARITY_THRESHOLD:
                auto_keep_ids.add(raw.id)

    final_keep_ids = manual_keep_set | auto_keep_ids
    reject_ids = [r.id for r in all_raw if r.id not in final_keep_ids]

    # ── Keep: create evaluation + job record ──────────────────────────────────
    kept_count = 0
    for raw in all_raw:
        if raw.id not in final_keep_ids:
            continue
        existing = await session.execute(
            select(JobEvaluation.id).where(JobEvaluation.raw_job_id == raw.id)
        )
        if existing.scalar_one_or_none():
            continue

        is_auto = raw.id in auto_keep_ids
        reason = "Auto-kept: similar skill requirements to user selection" if is_auto else "Manually approved from review queue"

        evaluation = JobEvaluation(
            raw_job_id=raw.id,
            role_family="software_engineer",
            seniority="entry",
            early_talent=True,
            fit_score=70.0,
            fit_label="good_fit",
            keep_in_db=True,
            needs_user_feedback=False,
            ats_keywords_json="[]",
            matched_skills_json="[]",
            missing_skills_json="[]",
            reasoning_summary=reason,
        )
        session.add(evaluation)
        await session.flush()

        job = Job(
            raw_job_id=raw.id,
            evaluation_id=evaluation.id,
            title=raw.title,
            company=raw.company,
            location=raw.location or "",
            url=raw.url,
            description=raw.description_raw or "",
            role_family="software_engineer",
            seniority="entry",
            fit_score=70.0,
            status=JobStatus.NEW.value,
        )
        session.add(job)
        await session.execute(
            text("UPDATE raw_jobs SET processing_status = 'processed' WHERE id = :id"),
            {"id": raw.id},
        )
        kept_count += 1

    await session.commit()

    # ── Reject the rest ───────────────────────────────────────────────────────
    batch_size = 100
    for i in range(0, len(reject_ids), batch_size):
        batch = reject_ids[i:i + batch_size]
        for job_id in batch:
            await session.execute(text("""
                INSERT INTO job_evaluations
                    (raw_job_id, role_family, seniority, early_talent, fit_score,
                     fit_label, keep_in_db, needs_user_feedback,
                     ats_keywords_json, matched_skills_json, missing_skills_json,
                     reasoning_summary)
                VALUES
                    (:raw_job_id, 'unknown', 'unknown', false, 5.0,
                     'poor_fit', false, false,
                     '[]', '[]', '[]', 'Rejected by user review')
                ON CONFLICT (raw_job_id) DO NOTHING
            """), {"raw_job_id": job_id})
            await session.execute(
                text("UPDATE raw_jobs SET processing_status = 'processed' WHERE id = :id"),
                {"id": job_id},
            )
        await session.commit()

    return {
        "manually_kept": len(manual_keep_set & all_ids),
        "auto_kept": len(auto_keep_ids & all_ids),
        "total_kept": kept_count,
        "rejected": len(reject_ids),
        "reference_skills": sorted(reference_skills),
    }


@router.get("/{job_id}")
async def get_raw_job(
    job_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(RawJob).where(RawJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "source_id": job.source_id,
        "external_id": job.external_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "url": job.url,
        "description_raw": job.description_raw,
        "processing_status": job.processing_status,
        "fetched_at": job.fetched_at,
    }
