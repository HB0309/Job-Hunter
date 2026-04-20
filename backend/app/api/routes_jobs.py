from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.repositories.jobs import get_job_detail, get_jobs, update_job_status
from app.schemas.job import JobDetail, JobRead, JobStatusUpdate

router = APIRouter()

VALID_STATUSES = {"new", "saved", "applied", "dismissed"}


@router.get("/", response_model=list[JobRead])
async def list_jobs(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    status_val = status if status else None
    rows = await get_jobs(session, status=status_val, limit=limit, offset=offset)
    return [JobRead.model_validate(r) for r in rows]


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: int, session: AsyncSession = Depends(get_session)):
    detail = await get_job_detail(session, job_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Job not found")
    return detail


@router.patch("/{job_id}/status", response_model=dict)
async def set_job_status(
    job_id: int,
    body: JobStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {VALID_STATUSES}")
    ok = await update_job_status(session, job_id, body.status)
    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job_id, "status": body.status}
