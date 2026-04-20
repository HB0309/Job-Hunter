"""Interactive scoring session helper for Claude Code.

Usage:
  # Fetch next batch to score (prints JSON for Claude to read):
  python scripts/scoring_session.py fetch --batch 30

  # Write Claude's scored results back to DB:
  python scripts/scoring_session.py write --results '[{"external_id": ..., ...}]'

  # Check scoring progress:
  python scripts/scoring_session.py status
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.db import async_session
from app.core.logging import setup_logging
from app.models.job import JobStatus


async def fetch_batch(batch_size: int = 30):
    """Fetch next batch of queued jobs and print as JSON for Claude to score."""
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT r.id, r.external_id, r.title, r.company, r.location, r.url,
                   LEFT(regexp_replace(r.description_raw, '<[^>]+>', ' ', 'g'), 600) as snippet,
                   s.name as source
            FROM raw_jobs r
            JOIN sources s ON r.source_id = s.id
            WHERE r.processing_status = 'queued'
            ORDER BY s.name, r.id
            LIMIT :limit
        """), {"limit": batch_size})
        rows = result.mappings().all()

    jobs = [dict(r) for r in rows]
    print(json.dumps(jobs, indent=2, default=str))
    print(f"\n-- {len(jobs)} jobs fetched for scoring --", file=sys.stderr)


async def write_results(results: list[dict]):
    """Write Claude's scoring results to job_evaluations and jobs tables."""
    async with async_session() as session:
        accepted = 0
        for r in results:
            raw_job_id = r["raw_job_id"]

            # Insert evaluation
            await session.execute(text("""
                INSERT INTO job_evaluations
                    (raw_job_id, role_family, seniority, early_talent, fit_score,
                     fit_label, keep_in_db, needs_user_feedback,
                     ats_keywords_json, matched_skills_json, missing_skills_json, reasoning_summary)
                VALUES
                    (:raw_job_id, :role_family, :seniority, :early_talent, :fit_score,
                     :fit_label, :keep_in_db, :needs_user_feedback,
                     :ats_keywords_json, :matched_skills_json, :missing_skills_json, :reasoning_summary)
                ON CONFLICT (raw_job_id) DO NOTHING
            """), {
                "raw_job_id": raw_job_id,
                "role_family": r.get("role_family", ""),
                "seniority": r.get("seniority", ""),
                "early_talent": r.get("early_talent", False),
                "fit_score": r.get("fit_score", 0.0),
                "fit_label": r.get("fit_label", ""),
                "keep_in_db": r.get("keep_in_db", False),
                "needs_user_feedback": r.get("needs_user_feedback", False),
                "ats_keywords_json": json.dumps(r.get("ats_keywords", [])),
                "matched_skills_json": json.dumps(r.get("matched_skills", [])),
                "missing_skills_json": json.dumps(r.get("missing_skills", [])),
                "reasoning_summary": r.get("reasoning_summary", ""),
            })

            # If accepted, insert into canonical jobs
            if r.get("keep_in_db") and r.get("fit_score", 0) >= 60:
                eval_row = await session.execute(text(
                    "SELECT id FROM job_evaluations WHERE raw_job_id = :id"
                ), {"id": raw_job_id})
                eval_id = eval_row.scalar()

                raw = await session.execute(text(
                    "SELECT title, company, location, url, description_raw FROM raw_jobs WHERE id = :id"
                ), {"id": raw_job_id})
                job = raw.mappings().one()

                await session.execute(text("""
                    INSERT INTO jobs
                        (raw_job_id, evaluation_id, title, company, location, url,
                         description, role_family, seniority, fit_score, status)
                    VALUES
                        (:raw_job_id, :evaluation_id, :title, :company, :location, :url,
                         :description, :role_family, :seniority, :fit_score, :status)
                    ON CONFLICT (raw_job_id) DO NOTHING
                """), {
                    "raw_job_id": raw_job_id,
                    "evaluation_id": eval_id,
                    "title": job["title"],
                    "company": job["company"],
                    "location": job["location"] or "",
                    "url": job["url"],
                    "description": (job["description_raw"] or "")[:5000],
                    "role_family": r.get("role_family", ""),
                    "seniority": r.get("seniority", ""),
                    "fit_score": r.get("fit_score", 0.0),
                    "status": JobStatus.NEW.value,
                })
                accepted += 1

            # Mark raw job as processed
            await session.execute(text(
                "UPDATE raw_jobs SET processing_status = 'processed' WHERE id = :id"
            ), {"id": raw_job_id})

        await session.commit()
        print(f"Written {len(results)} evaluations, {accepted} accepted into jobs table.")


async def status():
    async with async_session() as session:
        counts = await session.execute(text(
            "SELECT processing_status, COUNT(*) FROM raw_jobs GROUP BY processing_status ORDER BY processing_status"
        ))
        print("\n--- raw_jobs status ---")
        for row in counts:
            print(f"  {row[0]:12s}: {row[1]}")

        jobs_count = await session.execute(text("SELECT COUNT(*) FROM jobs"))
        print(f"\n  jobs table   : {jobs_count.scalar()} accepted jobs")

        top = await session.execute(text("""
            SELECT company, title, fit_score, role_family
            FROM jobs ORDER BY fit_score DESC LIMIT 10
        """))
        rows = top.mappings().all()
        if rows:
            print("\n--- Top 10 scored jobs ---")
            for r in rows:
                print(f"  [{r['fit_score']:5.1f}] {r['company']:20s} | {r['title']}")


if __name__ == "__main__":
    setup_logging()
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    fetch_p = sub.add_parser("fetch")
    fetch_p.add_argument("--batch", type=int, default=30)

    write_p = sub.add_parser("write")
    write_p.add_argument("--results", type=str, required=True)

    sub.add_parser("status")

    args = parser.parse_args()

    if args.cmd == "fetch":
        asyncio.run(fetch_batch(args.batch))
    elif args.cmd == "write":
        results = json.loads(args.results)
        asyncio.run(write_results(results))
    elif args.cmd == "status":
        asyncio.run(status())
    else:
        parser.print_help()
