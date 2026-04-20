"""Claude batch scorer: sends N jobs per API call, gets back a JSON array of scores."""

import json
import re
from pathlib import Path

from anthropic import Anthropic

from app.core.config import settings
from app.core.logging import get_logger
from app.models.raw_job import RawJob

logger = get_logger(__name__)

BATCH_SIZE = 15
MODEL = "claude-haiku-4-5-20251001"


def _load_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("Prompt file not found: %s", path)
        return ""


def _build_system_prompt() -> str:
    profile = _load_file("/app/PROFILE_MATCH.md")
    rules = _load_file("/app/SCORING_RULES.md")
    return f"""You are a job fit scorer. Evaluate each job against the candidate profile below.

{profile}

{rules}

## Output instructions
- Return ONLY a valid JSON array — no markdown, no explanation, no extra text.
- One object per job, indexed from 0.
- fit_label must match the score band: "excellent fit" (90-100), "strong fit" (75-89),
  "stretch" (60-74), "weak fit" (40-59), "reject" (0-39).
- keep_in_db must be true if and only if fit_score >= 60.
- needs_user_feedback = true if fit_score is 60-74 (borderline).
"""


_SYSTEM_PROMPT: str | None = None


def _get_system_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        _SYSTEM_PROMPT = _build_system_prompt()
    return _SYSTEM_PROMPT


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _snippet(job: RawJob) -> str:
    return _strip_html(job.description_raw or "")[:400]


def score_batch(jobs: list[RawJob]) -> list[dict]:
    """Send one batch of jobs to Claude, return list of result dicts (one per job).

    Each dict has keys matching EvaluationResult fields plus 'index'.
    Returns empty list on failure.
    """
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in .env")

    client = Anthropic(api_key=settings.anthropic_api_key)

    lines = []
    for i, job in enumerate(jobs):
        lines.append(f"[{i}] Title: {job.title}")
        lines.append(f"    Company: {job.company}")
        lines.append(f"    Location: {job.location or 'Unknown'}")
        lines.append(f"    Description: {_snippet(job)}")
        lines.append("")

    user_message = (
        f"Score these {len(jobs)} jobs. Return ONLY a JSON array.\n\n"
        + "\n".join(lines)
        + '\nRequired fields per object: index, fit_score, keep_in_db, role_family, '
        'seniority, early_talent, fit_label, matched_skills, missing_skills, '
        'ats_keywords, reasoning_summary, needs_user_feedback'
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=_get_system_prompt(),
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text
    except Exception:
        logger.exception("Claude API call failed for batch of %d jobs", len(jobs))
        return []

    # Extract JSON array from response (handles any stray markdown)
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        logger.error("No JSON array found in Claude response. Raw: %s", text[:200])
        return []

    try:
        results = json.loads(match.group())
    except json.JSONDecodeError:
        logger.error("JSON parse failed. Raw: %s", text[:200])
        return []

    if not isinstance(results, list):
        logger.error("Expected list, got %s", type(results))
        return []

    return results
