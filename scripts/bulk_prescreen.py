"""Bulk pre-screen queued raw_jobs — 2-stage pipeline.

Stage 1 (title + location): fast, no DB description read.
  - Auto-rejects senior/manager titles, non-US locations, non-tech roles.

Stage 2 (description analysis): reads description_raw for surviving jobs.
  - Extracts years-of-experience requirement, entry-level signals,
    tech keyword overlap with user profile, and domain mismatch signals.
  - Output buckets:
      score  — strong match, ready for Claude scoring
      review — ambiguous, print for manual check
      (auto_reject from Stage 2 is also applied silently)

Usage:
  python scripts/bulk_prescreen.py --dry-run    # preview without writing
  python scripts/bulk_prescreen.py --execute    # apply rejections, print shortlist
"""

import asyncio
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.db import async_session
from app.core.logging import setup_logging
from skill_match import analyze_description

# ── Stage 1 patterns ─────────────────────────────────────────────────────────

REJECT_TITLE_PATTERNS = [
    r"\bsenior\b", r"\bsr\b\.?", r"\bstaff\b", r"\bprincipal\b", r"\blead\b",
    r"\bdirector\b", r"\bvp\b", r"\bvice president\b", r"\bchief\b", r"\bhead of\b",
    r"\bmanager\b",
    r"\barchitect\b",
    r"\baccounting\b", r"\blegal\b", r"\bcounsel\b", r"\battorney\b",
    r"\bmarketing\b", r"\bbrand\b", r"\bcommunications?\b",
    r"\bfinance\b", r"\bfinancial\b", r"\baccountant\b", r"\bsox\b",
    r"\bsales\b",
    r"\brecruiting\b", r"\brecruiter\b", r"\bhr\b", r"\bhuman resources\b",
    r"\bpolicy\b", r"\bpublic affairs\b",
    r"\boperations?\b",
    r"\bparaleg\b", r"\bcompliance manager\b",
    r"\bsox analytics\b", r"\badvanced analytics\b",
    r"\bdata analyst\b",
    r"\(\d+\+?\s*(?:yoe|years?)\)",
    r"\d+-\d+\s*yoe\b",
    r"\bengineer\s+ii\b", r"\bii[,\s]", r"\bswe\s*ii\b",
    r"\bsoftware engineer 2\b", r"\bengineer 2\b",
    # Level III = senior (Google L5, Amazon SDE-III, etc.)
    r"\bengineer\s+iii\b", r"\bengineer\s+3\b", r"\bswe\s*iii\b", r"\bsoftware engineer 3\b",
    r"\bengineer,?\s+iii\b",
    r"\bresearch scientist\b",
    r"\bforward deployed\b",
    r"\bapplied ai\b",
    r"\bincentive compensation\b",
    r"\binsider risk investigator\b",
    r"\bbiological safety\b",
    r"\bprompt engineer\b",
    r"\bmid.level\b", r"\bmidlevel\b",
    r"\bfull performance\b",
    r"\bskill level [3-9]\b", r"\bskill level [1-9][0-9]\b",
    # Data center / facilities — physical/manual roles not SWE
    r"\btechnician\b",
    # Hardware chip / semiconductor domain titles
    r"\bphysical design\b",
    r"\bsilicon validation\b",
    r"\bcpu\s+(?:design|implementation|microarchitect|silicon|processor\s+(?:power|performance|verification))\b",
    r"\bgpu\s+(?:design|physical|power)\b",
    r"\bsoc\s+(?:physical|validation|dft)\b",
    r"\bserdes\b",
    r"\bpll\s+design\b",
    r"\brfic\b",
    r"\basic\s+design\s+engineer\b",
    r"\boptical\s+network\s+engineer\b",
    r"\bcalibration\s+engineer\b",
    r"\bdesign\s+verification\s+engineer\b",
    r"\bhardware\s+(?:architecture|test|validation|systems)\b",
    r"\bmechanical\s+(?:engineer|test)\b",
    r"\bdisplay\s+electrical\b",
    r"\bemulation\s+verification\b",
    r"\bpower\s+system\s+design\b",
    r"\bgraphics\s+fe\s+integration\b",
    r"\bgraphics\s+(?:gpu\s+)?architectural\s+modeling\b",
    r"\bimaging\s+systems\s+validation\b",
    r"\banalog\s+layout\b",
    r"\bvirtualoso\b",
    r"\btiming\s+design\b",
]

REJECT_LOCATION_PATTERNS = [
    r"\bindia\b", r"\buk\b", r"\bunited kingdom\b", r"\bbangalore\b", r"\bmumbai\b",
    r"\bcanada\b", r"\bbrazil\b", r"\bchina\b", r"\bsingapore\b", r"\baustralia\b",
    r"\bmexico\b", r"\bfrance\b", r"\bgermany\b", r"\beurope\b", r"\bluxembourg\b",
    r"\bgurugram\b", r"\bhyderabad\b", r"\bpune\b", r"\bchennai\b",
    r"\bsao paulo\b", r"\bsão paulo\b", r"\bunited arab\b", r"\bjapan\b",
    r"\bkorea\b", r"\bapac\b", r"\bnorthern europe\b",
    r"\bremote - uk\b", r"\bremote - canada\b", r"\bremote, brazil\b",
    r"\bhybrid - bangalore\b", r"\bhybrid - india\b",
    r"\bparis\b", r"\blondon\b", r"\bswitzerland\b", r"\bnetherlands\b",
    r"\bspain\b", r"\bmadrid\b", r"\bberlin\b", r"\bamsterdam\b",
    r"\bstockholm\b", r"\bwarsaw\b", r"\bpoland\b", r"\bisrael\b",
    r"\btel aviv\b", r"\bdubai\b", r"\buae\b", r"\bireland\b",
    r"\bremote - ireland\b", r"\bremote - germany\b",
    r"\bpenang\b", r"\bmalaysia\b", r"\bslovakia\b", r"\bsaudi\b",
    r"\bportugal\b", r"\bsydney\b", r"\bfrankfurt\b", r"\bmontreal\b",
    r"\bslough\b", r"\baubervilliers\b", r"\bbogot\b", r"\bcork\b",
    r"\bapodaca\b", r"\bchennai\b", r"\btaiwan\b", r"\btaipei\b",
    r"\bcosta rica\b", r"\bdresden\b",
    r"\bprc\b", r"\bshanghai\b", r"\bbeijing\b", r"\bshenzhen\b",
    r"\bphilippines\b", r"\bmanila\b", r"\bcavite\b",
    r"\bvietnam\b", r"\bhanoi\b", r"\bho chi minh\b",
    r"\bthailand\b", r"\bbangkok\b", r"\bindonesia\b", r"\bjakarta\b",
]

ENTRY_TITLE_SIGNALS = [
    r"\bintern\b", r"\bapprenticeship?\b", r"\bjunior\b", r"\bentry.level\b",
    r"\bnew grad\b", r"\bnewgrad\b", r"\bassociate engineer\b",
    r"\bengineer 1\b", r"\bengineer i\b", r"\bswe i\b", r"\bswe 1\b",
    r"\bsoftware engineer 1\b", r"\bsoftware engineer i\b",
    r"\blevel 1\b", r"\blevel i\b", r"\bjr\.\b", r"\bjr\b",
    r"\bconnect program\b", r"\buniversity\b", r"\bcampus\b",
    r"\brecent grad\b", r"\bgraduate\b",
]

# Titles that strongly indicate a target role — promote from review to score
# if YOE ≤ 3 and at least 1 skill matches, even without explicit entry-level language
SECURITY_TARGET_TITLE_PATTERNS = [
    r"\bsecurity engineer\b",
    r"\bsecurity analyst\b",
    r"\bsoc analyst\b",
    r"\bdetection engineer\b",
    r"\bapplication security\b",
    r"\bappsec\b",
    r"\bai security\b",
    r"\boffensive security\b",
    r"\bred team\b",
    r"\bpenetration test\b",
    r"\bsecurity software engineer\b",
    r"\bsecurity observ\b",
]

NON_TECH_TITLE_PATTERNS = [
    r"\banalyst\b(?!.*engineer)",
    r"\bproduct manager\b", r"\bprogram manager\b",
    r"\bproject manager\b", r"\btechnical program manager\b",
    r"\bcustomer success\b", r"\bcustomer support\b", r"\bsupport engineer\b",
    r"\btechnical support\b", r"\bsolutions engineer\b(?!.*security)",
    r"\bpresales\b", r"\bpre-sales\b",
    r"\bbusiness development\b", r"\bbusiness analyst\b",
    r"\bdata protection operations\b",
    # Apple retail / customer-facing (not SWE)
    r"\btechnical\s+specialist\b",
    r"\btechnical\s+expert\b",
]

US_LOCATION_SIGNALS = [
    "usa", "united states", "remote - usa", "remote, usa", "usa - remote",
    "san francisco", "new york", "seattle", "austin", "boston", "chicago",
    "los angeles", "denver", "atlanta", "washington", "virginia", "california",
    "texas", "nyc", "bay area", "remote",
]


def _matches_any(text_lower: str, patterns: list[str]) -> bool:
    return any(re.search(p, text_lower) for p in patterns)


def stage1_classify(title: str, location: str) -> str:
    """Stage 1: title + location only. Returns reject reason or 'pass'."""
    title_lower = (title or "").lower()
    loc_lower = (location or "").lower()

    if _matches_any(loc_lower, REJECT_LOCATION_PATTERNS):
        return "reject_location"
    if _matches_any(title_lower, REJECT_TITLE_PATTERNS):
        return "reject_title"
    if _matches_any(title_lower, NON_TECH_TITLE_PATTERNS):
        return "reject_nontechnical"
    return "pass"


def has_entry_title_signal(title: str) -> bool:
    return _matches_any((title or "").lower(), ENTRY_TITLE_SIGNALS)


# ── Prescreen pipeline ────────────────────────────────────────────────────────

async def bulk_prescreen(execute: bool = False) -> None:
    # Load all queued jobs (including description_raw for Stage 2)
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT r.id, r.title, r.company, r.location, r.url,
                   r.description_raw, s.name as source
            FROM raw_jobs r
            JOIN sources s ON r.source_id = s.id
            WHERE r.processing_status = 'queued'
            ORDER BY s.name, r.id
        """))
        jobs = [dict(r) for r in result.mappings().all()]

    total = len(jobs)
    print(f"Total queued: {total}", file=sys.stderr)

    # Stage 1 buckets
    s1_reject_location = []
    s1_reject_title    = []
    s1_reject_nontech  = []
    s1_pass            = []

    for job in jobs:
        verdict = stage1_classify(job["title"], job["location"])
        if verdict == "reject_location":
            s1_reject_location.append(job)
        elif verdict == "reject_title":
            s1_reject_title.append(job)
        elif verdict == "reject_nontechnical":
            s1_reject_nontech.append(job)
        else:
            s1_pass.append(job)

    s1_rejects = s1_reject_location + s1_reject_title + s1_reject_nontech

    print(f"\n── Stage 1 (title + location) ──────────────────────────────", file=sys.stderr)
    print(f"  Auto-reject: {len(s1_rejects)}", file=sys.stderr)
    print(f"    Location:     {len(s1_reject_location)}", file=sys.stderr)
    print(f"    Senior/mgr:   {len(s1_reject_title)}", file=sys.stderr)
    print(f"    Non-tech:     {len(s1_reject_nontech)}", file=sys.stderr)
    print(f"  Passed to Stage 2: {len(s1_pass)}", file=sys.stderr)

    # Stage 2: description analysis
    s2_auto_reject  = []   # (job, verdict)
    s2_score_queue  = []   # (job, verdict) — good match, ready for Claude
    s2_review_queue = []   # (job, verdict) — ambiguous

    for job in s1_pass:
        desc = job.get("description_raw") or ""
        dv = analyze_description(desc)
        title_lower = (job["title"] or "").lower()

        if dv.verdict == "auto_reject":
            s2_auto_reject.append((job, dv))
        elif dv.verdict == "score":
            # Interns pass description stage but shouldn't be in scoring queue
            if _matches_any(title_lower, [r"\bintern\b", r"\bapprenticeship?\b"]):
                s2_review_queue.append((job, dv))
            else:
                s2_score_queue.append((job, dv))
        else:
            # Promote security-titled roles from review → score if YOE is reasonable
            # and description has at least 1 skill match
            is_security_title = _matches_any(title_lower, SECURITY_TARGET_TITLE_PATTERNS)
            yoe_ok = dv.yoe_required is None or dv.yoe_required <= 3
            if is_security_title and yoe_ok and len(dv.matched_skills) >= 1:
                s2_score_queue.append((job, dv))
            else:
                s2_review_queue.append((job, dv))

    all_rejects = s1_rejects + [j for j, _ in s2_auto_reject]

    print(f"\n── Stage 2 (description analysis) ─────────────────────────", file=sys.stderr)
    print(f"  Auto-reject (domain / YOE): {len(s2_auto_reject)}", file=sys.stderr)
    print(f"  Score queue (strong match): {len(s2_score_queue)}", file=sys.stderr)
    print(f"  Review queue (ambiguous):   {len(s2_review_queue)}", file=sys.stderr)
    print(f"\n── Summary ─────────────────────────────────────────────────", file=sys.stderr)
    print(f"  Total auto-reject: {len(all_rejects)} / {total}", file=sys.stderr)
    print(f"  Needs scoring:     {len(s2_score_queue)}", file=sys.stderr)
    print(f"  Needs review:      {len(s2_review_queue)}", file=sys.stderr)

    if execute:
        print("\nApplying all rejections...", file=sys.stderr)
        reject_jobs_with_reason = (
            [(j, "Auto-rejected: non-US location")        for j in s1_reject_location] +
            [(j, "Auto-rejected: senior/manager title")   for j in s1_reject_title]    +
            [(j, "Auto-rejected: non-technical role")     for j in s1_reject_nontech]  +
            [(j, f"Auto-rejected: {dv.reason}")           for j, dv in s2_auto_reject]
        )
        review_jobs = [j for j, _ in s2_review_queue]

        async with async_session() as session:
            # Apply hard rejections
            batch_size = 100
            for i in range(0, len(reject_jobs_with_reason), batch_size):
                batch = reject_jobs_with_reason[i:i + batch_size]
                for job, reason in batch:
                    await session.execute(text("""
                        INSERT INTO job_evaluations
                            (raw_job_id, role_family, seniority, early_talent, fit_score,
                             fit_label, keep_in_db, needs_user_feedback,
                             ats_keywords_json, matched_skills_json, missing_skills_json,
                             reasoning_summary)
                        VALUES
                            (:raw_job_id, 'unknown', 'unknown', false, 5.0,
                             'poor_fit', false, false,
                             '[]', '[]', '[]', :reason)
                        ON CONFLICT (raw_job_id) DO NOTHING
                    """), {"raw_job_id": job["id"], "reason": reason})
                    await session.execute(
                        text("UPDATE raw_jobs SET processing_status = 'processed' WHERE id = :id"),
                        {"id": job["id"]},
                    )
                await session.commit()
                print(f"  Committed batch {i // batch_size + 1}", file=sys.stderr)
            print(f"\nDone. {len(reject_jobs_with_reason)} jobs rejected.", file=sys.stderr)

            # Mark review-queue jobs as 'review' status (separate from score queue 'queued')
            if review_jobs:
                print(f"\nMarking {len(review_jobs)} ambiguous jobs as 'review'...", file=sys.stderr)
                for i in range(0, len(review_jobs), batch_size):
                    batch = review_jobs[i:i + batch_size]
                    ids = [j["id"] for j in batch]
                    await session.execute(
                        text("UPDATE raw_jobs SET processing_status = 'review' WHERE id = ANY(:ids)"),
                        {"ids": ids},
                    )
                    await session.commit()
                print(f"Done. {len(review_jobs)} jobs in review queue.", file=sys.stderr)

    # ── Print scoring queue ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"SCORE QUEUE ({len(s2_score_queue)} jobs) — strong profile match, ready for Claude")
    print(f"{'='*70}")
    for job, dv in sorted(s2_score_queue, key=lambda x: -len(x[1].matched_skills)):
        yoe_str = f"{dv.yoe_required}yr" if dv.yoe_required else "no-yoe"
        entry_str = "✓entry" if dv.entry_level_in_desc else ""
        skills_str = ", ".join(dv.matched_skills[:5])
        print(f"  [{job['id']}] {job['company']:20s} | {job['title']}")
        print(f"         {job['location']}")
        print(f"         skills: {skills_str}  [{yoe_str}{' ' + entry_str if entry_str else ''}]")
        print(f"         {job['url']}")

    # ── Print review queue ────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"REVIEW QUEUE ({len(s2_review_queue)} jobs) — ambiguous, check manually")
    print(f"{'='*70}")
    for job, dv in s2_review_queue:
        yoe_str = f"{dv.yoe_required}yr" if dv.yoe_required else "?"
        print(f"  [{job['id']}] {job['company']:20s} | {job['title']} | {job['location']}")
        print(f"         {dv.reason}")


if __name__ == "__main__":
    setup_logging()
    if "--dry-run" not in sys.argv and "--execute" not in sys.argv:
        print("Usage: python bulk_prescreen.py --dry-run | --execute")
        sys.exit(1)
    execute = "--execute" in sys.argv
    asyncio.run(bulk_prescreen(execute=execute))
