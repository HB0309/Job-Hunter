"""Jobright.ai connector — scrapes job listings via Next.js SSR __NEXT_DATA__ block.

Jobright embeds job data in a <script id="__NEXT_DATA__"> tag on every page.
We paginate using the `start` query parameter (16 jobs per page).

We filter client-side to keep only entry-level / new grad jobs:
  - jobSeniority contains "Entry" or "New Grad" or "Junior"
  - OR minYearsOfExperience is null or <= 2

URL pattern:
  https://jobright.ai/jobs/software-engineer?query={query}&location=United+States&start={offset}
"""

import asyncio
import json
import re

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

JOBRIGHT_BASE_URL = "https://jobright.ai/jobs/software-engineer"
PAGE_SIZE = 16

_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.DOTALL,
)

_ENTRY_SENIORITY_ACCEPT = {"entry level", "new grad", "junior", "associate", "entry-level"}
_SENIOR_SENIORITY_REJECT = {"senior", "staff", "lead", "principal", "manager", "director", "vp", "head"}


def _is_entry_level(job: dict) -> bool:
    """Return True if the job appears to be entry-level.

    Logic:
    1. If seniority explicitly contains a senior/staff/lead tier → reject
    2. If seniority explicitly contains an entry-level tier → accept
    3. If YOE is set and > 2 → reject
    4. Otherwise (no seniority, YOE null/≤2) → accept
    """
    seniority = (job.get("jobSeniority") or "").lower()

    # Explicit senior reject (takes priority)
    if any(s in seniority for s in _SENIOR_SENIORITY_REJECT):
        return False

    # Explicit entry accept
    if any(s in seniority for s in _ENTRY_SENIORITY_ACCEPT):
        return True

    # Fall back to YOE
    yoe = job.get("minYearsOfExperience")
    if yoe is not None and yoe > 2:
        return False

    return True


def _build_description(job: dict) -> str:
    """Combine jobSummary, requirements, and coreResponsibilities into a single text."""
    parts: list[str] = []

    summary = job.get("jobSummary") or ""
    if summary:
        parts.append(summary)

    responsibilities = job.get("coreResponsibilities")
    if isinstance(responsibilities, list) and responsibilities:
        parts.append("Core Responsibilities:\n" + "\n".join(f"- {r}" for r in responsibilities if r))
    elif isinstance(responsibilities, str) and responsibilities:
        parts.append("Core Responsibilities:\n" + responsibilities)

    requirements = job.get("requirements")
    if isinstance(requirements, list) and requirements:
        parts.append("Requirements:\n" + "\n".join(f"- {r}" for r in requirements if r))
    elif isinstance(requirements, str) and requirements:
        parts.append("Requirements:\n" + requirements)

    return "\n\n".join(parts)


class JobrightConnector(BaseConnector):
    """Fetches jobs from Jobright.ai by scraping the Next.js SSR page."""

    def __init__(self, query: str, max_pages: int = 15) -> None:
        self.query = query
        self.max_pages = max_pages

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        results: list[RawJobCreate] = []
        total: int | None = None
        page = 0  # 0-indexed page counter

        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            while page < self.max_pages:
                offset = page * PAGE_SIZE
                params = {
                    "query": self.query,
                    "location": "United States",
                    "start": offset,
                }
                try:
                    resp = await client.get(JOBRIGHT_BASE_URL, params=params)
                    resp.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        "Jobright HTTP %s on page %d (query=%r) — aborting",
                        exc.response.status_code, page, self.query,
                    )
                    break
                except httpx.RequestError as exc:
                    logger.warning("Jobright request error: %s — aborting", exc)
                    break

                match = _NEXT_DATA_RE.search(resp.text)
                if not match:
                    logger.warning(
                        "Jobright page %d (query=%r): no __NEXT_DATA__ found — aborting",
                        page, self.query,
                    )
                    break

                try:
                    next_data = json.loads(match.group(1))
                except (json.JSONDecodeError, ValueError) as exc:
                    logger.warning("Jobright __NEXT_DATA__ parse error on page %d: %s", page, exc)
                    break

                page_props = next_data.get("props", {}).get("pageProps", {})
                job_list = page_props.get("jobList") or []

                if total is None:
                    total = page_props.get("totalJobs", 0)
                    logger.info("Jobright query=%r total=%d", self.query, total)

                if not job_list:
                    logger.info("Jobright query=%r page %d: empty job list — done", self.query, page)
                    break

                page_kept = 0
                for item in job_list:
                    # Each item has jobResult + companyResult
                    job = item.get("jobResult") or item
                    company_data = item.get("companyResult") or {}

                    if not _is_entry_level(job):
                        continue

                    job_id = str(job.get("jobId") or "")
                    title = job.get("jobTitle") or ""
                    company = company_data.get("companyName") or job.get("companyName") or ""
                    location = job.get("jobLocation") or "United States"
                    # applyLink is the direct apply URL; url is the Jobright detail page
                    apply_link = job.get("applyLink") or job.get("url") or ""
                    publish_time = job.get("publishTime") or ""
                    seniority = job.get("jobSeniority") or ""
                    yoe = job.get("minYearsOfExperience")

                    description = _build_description(job)

                    results.append(
                        RawJobCreate(
                            source_id=source_id,
                            external_id=job_id or f"{company}:{title}",
                            title=title,
                            company=company,
                            location=location,
                            url=apply_link,
                            description_raw=description,
                            metadata_json=json.dumps({
                                "publish_time": publish_time,
                                "seniority": seniority,
                                "min_yoe": yoe,
                                "query": self.query,
                            }),
                        )
                    )
                    page_kept += 1

                logger.info(
                    "Jobright query=%r page %d: %d/%d kept (entry-level)",
                    self.query, page, page_kept, len(job_list),
                )

                page += 1

                # Stop if we've seen all jobs
                if total and offset + PAGE_SIZE >= total:
                    break

                # Polite delay
                await asyncio.sleep(1.5)

        logger.info("Jobright query=%r fetched %d entry-level jobs total", self.query, len(results))
        return results
