"""
Recover similar jobs from the recently user-rejected pool.

After a bulk review session where the user manually kept a small set and
rejected the rest, this script:

  1. Finds all raw_jobs whose evaluation reads "Manually approved from review queue"
     (the anchor set the user explicitly kept).
  2. Extracts skill categories from each anchor job's description.
  3. Finds all raw_jobs whose evaluation reads "Rejected by user review" that do NOT
     yet have a corresponding entry in the jobs table.
  4. For each rejected job, counts the skill overlap with the anchor set.
  5. Jobs with overlap >= SIMILARITY_THRESHOLD are recovered into the jobs table
     (fit_score=70, "Recovered: similar skill profile to manually-kept jobs").

Usage (inside Docker):
    # Dry run — shows counts, does not modify DB
    MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/recover_similar.py --dry-run

    # Execute
    MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/recover_similar.py --execute
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.job import Job, JobStatus
from app.models.evaluation import JobEvaluation
from app.models.raw_job import RawJob
from skill_match import extract_matched_skills  # in same /app/scripts/ folder

SIMILARITY_THRESHOLD = 2      # minimum overlapping skill categories to recover
REASON_KEPT = "Manually approved from review queue"
REASON_REJECTED = "Rejected by user review"
REASON_RECOVERED = "Recovered: similar skill profile to manually-kept jobs"

# Title fragments that disqualify a job regardless of skill overlap
_REJECT_TITLE_WORDS = [
    "intern", "internship", "co-op", "coop", "co op",
    "phd", "apprentice", "fellowship", "fellow",
    "part-time", "part time",
]

# Location strings that indicate non-US (cheap check before DB query)
_NON_US_LOCATION_SIGNALS = [
    "canada", "toronto", "vancouver", "india", "bangalore", "hyderabad",
    "uk", "london", "germany", "berlin", "australia", "sydney",
    "ireland", "dublin", "singapore", "japan", "tokyo",
    "china", "beijing", "shanghai", "france", "paris",
    "netherlands", "amsterdam", "sweden", "stockholm",
]


def _is_title_ok(title: str) -> bool:
    t = title.lower()
    return not any(w in t for w in _REJECT_TITLE_WORDS)


def _is_location_ok(location: str) -> bool:
    if not location:
        return True  # no location data — don't reject
    loc = location.lower()
    return not any(s in loc for s in _NON_US_LOCATION_SIGNALS)

DRY_RUN = "--execute" not in sys.argv


async def main() -> None:
    mode = "DRY RUN" if DRY_RUN else "EXECUTE"
    print(f"\nRecover Similar Jobs — {mode}")
    print(f"Similarity threshold: ≥{SIMILARITY_THRESHOLD} matching skill categories\n")

    engine = create_async_engine(settings.database_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        # ── 1. Load anchor jobs (manually kept) ──────────────────────────────
        r = await session.execute(
            text("""
                SELECT rj.id, rj.description_raw, rj.title, rj.company
                FROM raw_jobs rj
                JOIN job_evaluations je ON je.raw_job_id = rj.id
                WHERE je.reasoning_summary = :reason
            """),
            {"reason": REASON_KEPT},
        )
        anchors = r.all()
        print(f"Anchor jobs (manually kept): {len(anchors)}")
        for row in anchors:
            print(f"  [{row[0]}] {row[3]} — {row[2]}")

        if not anchors:
            print("\nNo anchor jobs found. Nothing to do.")
            return

        # ── 2. Build reference skill set ──────────────────────────────────────
        reference_skills: set[str] = set()
        for row in anchors:
            skills = set(extract_matched_skills(row[1] or ""))
            reference_skills |= skills

        print(f"\nReference skill set ({len(reference_skills)} categories):")
        print(f"  {', '.join(sorted(reference_skills))}\n")

        # ── 3. Load rejected jobs that aren't already in jobs table ──────────
        r2 = await session.execute(
            text("""
                SELECT rj.id, rj.description_raw, rj.title, rj.company,
                       rj.location, rj.url, je.id as eval_id
                FROM raw_jobs rj
                JOIN job_evaluations je ON je.raw_job_id = rj.id
                WHERE je.reasoning_summary = :reason
                  AND NOT EXISTS (
                      SELECT 1 FROM jobs j WHERE j.raw_job_id = rj.id
                  )
            """),
            {"reason": REASON_REJECTED},
        )
        rejected = r2.all()
        print(f"Rejected jobs to scan: {len(rejected)}")

        if not rejected:
            print("No rejected jobs found. Nothing to recover.")
            return

        # ── 4. Score each rejected job by skill overlap ───────────────────────
        to_recover = []
        skill_dist: dict[int, int] = {}  # overlap_count → number of jobs
        skipped_title = 0
        skipped_location = 0

        for row in rejected:
            raw_job_id, desc, title, company, location, url, eval_id = row

            # Hard filters before skill matching
            if not _is_title_ok(title or ""):
                skipped_title += 1
                continue
            if not _is_location_ok(location or ""):
                skipped_location += 1
                continue

            job_skills = set(extract_matched_skills(desc or ""))
            overlap = len(reference_skills & job_skills)
            skill_dist[overlap] = skill_dist.get(overlap, 0) + 1
            if overlap >= SIMILARITY_THRESHOLD:
                to_recover.append(row)

        print(f"  (skipped {skipped_title} intern/part-time titles, {skipped_location} non-US locations)")

        print("\nSkill overlap distribution:")
        for k in sorted(skill_dist.keys(), reverse=True):
            bar = "█" * min(k, 20)
            marker = " ← will recover" if k >= SIMILARITY_THRESHOLD else ""
            print(f"  {k:2d} skills: {skill_dist[k]:5d} jobs  {bar}{marker}")

        print(f"\nJobs to recover (overlap ≥ {SIMILARITY_THRESHOLD}): {len(to_recover)}")

        if DRY_RUN:
            print("\n[DRY RUN] Re-run with --execute to write to DB.")
            # Show a sample
            print("\nSample recovered jobs (first 20):")
            for row in to_recover[:20]:
                skills = set(extract_matched_skills(row[1] or ""))
                overlap = len(reference_skills & skills)
                print(f"  [{row[0]}] {row[3]} — {row[2]} ({overlap} skills: {', '.join(sorted(reference_skills & skills))})")
            return

        # ── 5. Write recovered jobs to DB ─────────────────────────────────────
        print("\nWriting to DB…")
        recovered = 0

        for i, row in enumerate(to_recover):
            raw_job_id, desc, title, company, location, url, eval_id = (
                row[0], row[1], row[2], row[3], row[4], row[5], row[6]
            )

            job_skills = set(extract_matched_skills(desc or ""))
            overlap_skills = sorted(reference_skills & job_skills)

            # Update existing evaluation (was poor_fit → good_fit)
            await session.execute(
                text("""
                    UPDATE job_evaluations
                    SET fit_score      = 70.0,
                        fit_label      = 'good_fit',
                        keep_in_db     = true,
                        reasoning_summary = :reason,
                        matched_skills_json = :skills
                    WHERE id = :eval_id
                """),
                {
                    "reason": REASON_RECOVERED,
                    "skills": str(overlap_skills).replace("'", '"'),
                    "eval_id": eval_id,
                },
            )

            # Insert job record
            job = Job(
                raw_job_id=raw_job_id,
                evaluation_id=eval_id,
                title=title,
                company=company,
                location=location or "",
                url=url,
                description=desc or "",
                role_family="software_engineer",
                seniority="entry",
                fit_score=70.0,
                status=JobStatus.NEW.value,
            )
            session.add(job)

            # Mark raw_job processed (already is, but ensure it)
            await session.execute(
                text("UPDATE raw_jobs SET processing_status = 'processed' WHERE id = :id"),
                {"id": raw_job_id},
            )
            recovered += 1

            if recovered % 200 == 0:
                await session.commit()
                print(f"  … {recovered}/{len(to_recover)} committed")

        await session.commit()
        print(f"\nDone. Recovered {recovered} jobs into jobs table.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
