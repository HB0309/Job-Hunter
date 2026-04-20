from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_job import RawJob, ProcessingStatus
from app.schemas.raw_job import RawJobCreate


async def upsert_raw_jobs(session: AsyncSession, jobs: list[RawJobCreate]) -> int:
    """Insert raw jobs, skipping duplicates on (source_id, external_id). Returns inserted count."""
    if not jobs:
        return 0

    inserted = 0
    for job in jobs:
        stmt = (
            pg_insert(RawJob)
            .values(**job.model_dump())
            .on_conflict_do_nothing(index_elements=["source_id", "external_id"])
        )
        result = await session.execute(stmt)
        inserted += result.rowcount
    await session.commit()
    return inserted


async def get_queued_raw_jobs(session: AsyncSession, limit: int = 50) -> list[RawJob]:
    """Fetch raw jobs in QUEUED state for processing."""
    stmt = (
        select(RawJob)
        .where(RawJob.processing_status == ProcessingStatus.QUEUED)
        .order_by(RawJob.fetched_at)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_processing_status(session: AsyncSession, raw_job_id: int, status: str) -> None:
    """Update the processing_status of a single raw_job. Does not commit."""
    stmt = update(RawJob).where(RawJob.id == raw_job_id).values(processing_status=status)
    await session.execute(stmt)
