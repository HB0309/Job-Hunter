"""Google Careers connector — scrapes AF_initDataCallback data from the SSR page.

Google's careers site embeds job listings in the page HTML via AF_initDataCallback
callbacks. We parse the ds:1 callback which contains the paginated job list.

Data structure (each job is a list of 21 fields):
  [0]  job ID
  [1]  title
  [2]  apply URL (signin redirect — we reconstruct the direct URL)
  [3]  responsibilities HTML
  [4]  minimum qualifications HTML
  [7]  company name
  [9]  locations: [[display_name, [street], city, zip, state, country], ...]
  [10] job overview HTML
  [19] preferred qualifications HTML
"""

import asyncio
import json
import re

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

GOOGLE_SEARCH_URL = "https://www.google.com/about/careers/applications/jobs/results/"
PAGE_SIZE = 20

_TITLE_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _make_slug(title: str) -> str:
    return _TITLE_SLUG_RE.sub("-", title.lower()).strip("-")


def _extract_ds1_data(text: str) -> list | None:
    """Parse the ds:1 AF_initDataCallback block and return the data array."""
    idx = text.find("key: 'ds:1'")
    if idx < 0:
        return None
    data_start = text.find("[[", text.find("data:", idx))
    if data_start < 0:
        return None
    # Walk brackets to find the end of the data array
    depth = 0
    i = data_start
    while i < len(text):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                break
        i += 1
    try:
        return json.loads(text[data_start : i + 1])
    except (json.JSONDecodeError, ValueError):
        return None


class GoogleCareersConnector(BaseConnector):
    """Fetches jobs from Google Careers by scraping the server-rendered search page.

    Google embeds job data in AF_initDataCallback blocks in the HTML response.
    Paginates through search results using the `page` query parameter.
    """

    def __init__(
        self,
        query: str = "software engineer entry level",
        location: str = "United States",
        target_level: str = "TARGET_LEVEL_EARLY",
    ) -> None:
        self.query = query
        self.location = location
        self.target_level = target_level

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        results: list[RawJobCreate] = []
        page = 1
        total: int | None = None

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            while True:
                params = {
                    "q": self.query,
                    "location": self.location,
                    "target_level": self.target_level,
                    "jlo": "en_US",
                    "page": page,
                }
                try:
                    resp = await client.get(
                        GOOGLE_SEARCH_URL,
                        params=params,
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    resp.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        "Google Careers HTTP %s on page %d — aborting",
                        exc.response.status_code, page,
                    )
                    break
                except httpx.RequestError as exc:
                    logger.warning("Google Careers request error: %s — aborting", exc)
                    break

                data = _extract_ds1_data(resp.text)
                if data is None:
                    logger.warning(
                        "Google Careers page %d: no ds:1 data block found — aborting",
                        page,
                    )
                    break

                jobs_raw = data[0]  # list of job arrays
                if total is None:
                    total = data[2] if len(data) > 2 and isinstance(data[2], int) else 0
                    logger.info(
                        "Google Careers query=%r total=%d",
                        self.query, total,
                    )

                if not jobs_raw:
                    break

                for job in jobs_raw:
                    if not isinstance(job, list) or len(job) < 10:
                        continue

                    job_id = str(job[0]) if job[0] else ""
                    title = job[1] or ""
                    company = job[7] if len(job) > 7 and job[7] else "google"

                    # Build direct URL from job_id + title slug
                    slug = _make_slug(title)
                    url = (
                        f"https://careers.google.com/jobs/results/{job_id}-{slug}/"
                        if job_id else ""
                    )

                    # Locations: [[display_name, [addresses], city, zip, state, country], ...]
                    loc_data = job[9] if len(job) > 9 and isinstance(job[9], list) else []
                    location_str = "; ".join(
                        loc[0] for loc in loc_data
                        if isinstance(loc, list) and loc and loc[0]
                    )

                    # Description: combine overview + responsibilities + qualifications
                    overview = (job[10][1] if len(job) > 10 and isinstance(job[10], list) and len(job[10]) > 1 else "") or ""
                    responsibilities = (job[3][1] if isinstance(job[3], list) and len(job[3]) > 1 else "") or ""
                    min_quals = (job[4][1] if isinstance(job[4], list) and len(job[4]) > 1 else "") or ""
                    pref_quals = (job[19][1] if len(job) > 19 and isinstance(job[19], list) and len(job[19]) > 1 else "") or ""

                    description = "\n".join(filter(None, [overview, responsibilities, min_quals, pref_quals]))

                    results.append(
                        RawJobCreate(
                            source_id=source_id,
                            external_id=job_id or title,
                            title=title,
                            company=company,
                            location=location_str,
                            url=url,
                            description_raw=description,
                            metadata_json=json.dumps({
                                "resource_path": job[5] if len(job) > 5 else "",
                                "page": page,
                            }),
                        )
                    )

                if len(jobs_raw) < PAGE_SIZE or (total and page * PAGE_SIZE >= total):
                    break

                page += 1
                # Polite delay between pages
                await asyncio.sleep(1)

        logger.info("Google Careers query=%r fetched %d jobs", self.query, len(results))
        return results
