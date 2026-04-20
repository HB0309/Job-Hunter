from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.raw_jobs import upsert_raw_jobs
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector
from app.services.ingestion.dedup import deduplicate_batch
from app.services.ingestion.normalize import normalize_raw_job

logger = get_logger(__name__)

# Only jobs whose title contains at least one of these keywords get stored.
# This keeps raw_jobs lean so Claude Code scoring stays manageable.
_RELEVANT_TITLE_KEYWORDS = frozenset({
    "engineer", "developer", "security", "software", "devops", "sre",
    "platform", "infrastructure", "cloud", "detection", "soc", "cyber",
    "researcher", "scientist", "architect", "analyst", "data", "network",
    "systems", "backend", "frontend", "fullstack", "ml", "reliability",
    "intern", "associate", "junior", "programmer", "kubernetes", "python",
    "golang", "rust", "infosec", "appsec", "pentester", "red team",
    "blue team", "threat", "vulnerability", "compliance", "risk",
    "technical", "it specialist", "it analyst",
})


def _is_relevant(job: RawJobCreate) -> bool:
    title = (job.title or "").lower()
    return any(kw in title for kw in _RELEVANT_TITLE_KEYWORDS)


async def run_ingestion_for_connector(
    connector: BaseConnector,
    source_id: int,
    session: AsyncSession,
) -> int:
    """Fetch jobs via connector, filter by title, normalize, dedup, upsert into raw_jobs.

    Returns the number of newly inserted rows.
    """
    logger.info("Fetching jobs for source_id=%d", source_id)
    raw_jobs: list[RawJobCreate] = await connector.fetch_jobs(source_id)
    logger.info("Fetched %d jobs from source_id=%d", len(raw_jobs), source_id)

    # Title filter — drop clearly irrelevant roles before they hit the DB
    relevant = [j for j in raw_jobs if _is_relevant(j)]
    dropped = len(raw_jobs) - len(relevant)
    if dropped:
        logger.info("Title filter dropped %d irrelevant jobs, keeping %d", dropped, len(relevant))

    # Normalize
    normalized = [normalize_raw_job(j) for j in relevant]

    # In-batch dedup
    deduped = deduplicate_batch(normalized)
    logger.info("After dedup: %d unique jobs", len(deduped))

    # Upsert (DB-level dedup via unique index handles cross-run duplicates)
    inserted = await upsert_raw_jobs(session, deduped)
    logger.info("Inserted %d new raw jobs for source_id=%d", inserted, source_id)

    return inserted
