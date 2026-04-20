"""Scoring worker: reads QUEUED raw_jobs, scores via Claude, writes results.

Pipeline per run:
  1. Fetch up to FETCH_LIMIT queued raw_jobs
  2. Pre-filter by title keyword (free — no API call)
  3. Batch remaining into groups of BATCH_SIZE
  4. Score each batch via Claude Haiku
  5. Write job_evaluation + canonical job (if accepted) + update processing_status
  6. Repeat until no QUEUED jobs remain

Usage: python -m app.workers.run_scoring
"""

import argparse
import asyncio

from app.core.config import settings
from app.core.db import async_session
from app.core.logging import get_logger, setup_logging
from app.repositories.evaluations import create_evaluation
from app.repositories.jobs import insert_from_evaluation
from app.repositories.raw_jobs import get_queued_raw_jobs, update_processing_status
from app.services.scoring.prefilter import prefilter
from app.services.scoring.scorer import BATCH_SIZE, score_batch

logger = get_logger(__name__)

FETCH_LIMIT = 500  # how many queued jobs to pull per outer loop iteration


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def run_scoring(limit: int | None = None) -> None:
    setup_logging()

    if not settings.anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY not set in .env — cannot run scoring worker")
        return

    if limit:
        logger.info("Running in controlled mode: will score at most %d jobs", limit)

    total_scored = total_accepted = total_prerejected = 0

    async with async_session() as session:
        while True:
            remaining = (limit - total_scored - total_prerejected) if limit else FETCH_LIMIT
            if limit and remaining <= 0:
                logger.info("Reached --limit of %d. Stopping.", limit)
                break

            fetch = min(FETCH_LIMIT, remaining) if limit else FETCH_LIMIT
            jobs = await get_queued_raw_jobs(session, limit=fetch)
            if not jobs:
                logger.info("No more QUEUED jobs. Done.")
                break

            logger.info("Fetched %d queued jobs", len(jobs))

            # Step 1: title pre-filter
            tech_jobs, rejected_jobs = prefilter(jobs)
            logger.info(
                "Pre-filter: %d pass, %d rejected by title", len(tech_jobs), len(rejected_jobs)
            )

            # Mark pre-rejected jobs
            for job in rejected_jobs:
                await update_processing_status(session, job.id, "rejected")
            if rejected_jobs:
                await session.commit()
            total_prerejected += len(rejected_jobs)

            # Step 2: batch score
            consecutive_failures = 0
            for batch in _chunks(tech_jobs, BATCH_SIZE):
                logger.info("Scoring batch of %d jobs via Claude...", len(batch))
                results = score_batch(batch)

                if not results:
                    consecutive_failures += 1
                    # Mark as error so they can be retried later
                    for job in batch:
                        await update_processing_status(session, job.id, "error")
                    await session.commit()
                    if consecutive_failures >= 3:
                        logger.error("3 consecutive batch failures — aborting. Check API key/credits.")
                        return
                    continue
                consecutive_failures = 0

                # Map index → result dict for safe lookup
                result_by_index = {r["index"]: r for r in results if isinstance(r, dict)}

                for i, job in enumerate(batch):
                    result = result_by_index.get(i)
                    if result is None:
                        logger.warning("No result for job id=%d (index %d), marking error", job.id, i)
                        await update_processing_status(session, job.id, "error")
                        continue

                    try:
                        evaluation = await create_evaluation(session, job.id, result)

                        if result.get("keep_in_db") and result.get("fit_score", 0) >= 60:
                            await insert_from_evaluation(session, job, evaluation)
                            total_accepted += 1
                            logger.info(
                                "Accepted: [%s] %s @ %s — score=%s",
                                result.get("fit_label", "?"),
                                job.title,
                                job.company,
                                result.get("fit_score", "?"),
                            )

                        await update_processing_status(session, job.id, "processed")
                        total_scored += 1

                    except Exception:
                        logger.exception("Failed to save result for job id=%d", job.id)
                        await update_processing_status(session, job.id, "error")

                await session.commit()
                logger.info("Batch done. Running totals: scored=%d accepted=%d", total_scored, total_accepted)

    logger.info(
        "Scoring complete. scored=%d accepted=%d pre-rejected=%d",
        total_scored, total_accepted, total_prerejected,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job scoring worker")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max number of jobs to process (pre-filter + scored). Omit for full run."
    )
    args = parser.parse_args()
    asyncio.run(run_scoring(limit=args.limit))
