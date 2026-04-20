"""Write a batch results JSON file to the DB. Usage: python write_batch.py <path>"""
import asyncio, json, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.db import async_session
from app.core.logging import setup_logging
from app.models.job import JobStatus


async def write_results(results):
    async with async_session() as session:
        accepted = 0
        for r in results:
            raw_job_id = r["raw_job_id"]
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
            if r.get("keep_in_db") and r.get("fit_score", 0) >= 60:
                eval_row = await session.execute(
                    text("SELECT id FROM job_evaluations WHERE raw_job_id = :id"), {"id": raw_job_id}
                )
                eval_id = eval_row.scalar()
                raw = await session.execute(
                    text("SELECT title, company, location, url, description_raw FROM raw_jobs WHERE id = :id"),
                    {"id": raw_job_id},
                )
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
            await session.execute(
                text("UPDATE raw_jobs SET processing_status = 'processed' WHERE id = :id"),
                {"id": raw_job_id},
            )
        await session.commit()
        print(f"Written {len(results)} evaluations, {accepted} accepted into jobs table.")


if __name__ == "__main__":
    setup_logging()
    path = sys.argv[1]
    results = json.load(open(path))
    asyncio.run(write_results(results))
