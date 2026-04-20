"""Apple Jobs connector — scrapes server-rendered hydration data from jobs.apple.com.

Apple's jobs site uses Remix with server-side rendering. Job search results are
embedded in the page HTML inside window.__staticRouterHydrationData as JSON.

The search URL format:
  https://jobs.apple.com/en-us/search?search={query}&location=united-states-USA&page={n}
"""

import asyncio
import json
import re

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

APPLE_SEARCH_URL = "https://jobs.apple.com/en-us/search"
PAGE_SIZE = 20

_HYDRATION_RE = re.compile(
    r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\("(.*?)"\);',
    re.DOTALL,
)


def _extract_search_data(text: str) -> dict | None:
    """Extract and parse the Remix hydration JSON from the page."""
    m = _HYDRATION_RE.search(text)
    if not m:
        return None
    try:
        raw = m.group(1).encode("raw_unicode_escape").decode("unicode_escape")
        hydration = json.loads(raw)
        return hydration.get("loaderData", {}).get("search")
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return None


class AppleJobsConnector(BaseConnector):
    """Fetches jobs from Apple Jobs by scraping the SSR search page.

    Apple's Remix-based site embeds all search results in window.__staticRouterHydrationData.
    We parse this data and paginate via the `page` query parameter.
    """

    def __init__(self, query: str = "software engineer") -> None:
        self.query = query

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        results: list[RawJobCreate] = []
        page = 1
        total: int | None = None

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            while True:
                params = {
                    "search": self.query,
                    "location": "united-states-USA",
                    "page": page,
                }
                try:
                    resp = await client.get(
                        APPLE_SEARCH_URL,
                        params=params,
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    resp.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        "Apple Jobs HTTP %s on page %d — aborting",
                        exc.response.status_code, page,
                    )
                    break
                except httpx.RequestError as exc:
                    logger.warning("Apple Jobs request error: %s — aborting", exc)
                    break

                search_data = _extract_search_data(resp.text)
                if search_data is None:
                    logger.warning(
                        "Apple Jobs page %d: no hydration data found — aborting", page
                    )
                    break

                jobs = search_data.get("searchResults", [])
                if total is None:
                    total = search_data.get("totalRecords", 0)
                    logger.info("Apple Jobs query=%r total=%d", self.query, total)

                if not jobs:
                    break

                for job in jobs:
                    pos_id = job.get("positionId", "")
                    job_id = str(pos_id) if pos_id else str(job.get("id", ""))
                    title = job.get("postingTitle", job.get("title", ""))

                    # Locations
                    locs = job.get("locations", [])
                    if isinstance(locs, list):
                        loc_parts = []
                        for loc in locs:
                            if isinstance(loc, dict):
                                city = loc.get("name", loc.get("city", ""))
                                country = loc.get("countryName", "")
                                if city:
                                    loc_parts.append(city)
                                elif country:
                                    loc_parts.append(country)
                            else:
                                loc_parts.append(str(loc))
                        location_str = "; ".join(filter(None, loc_parts))
                    else:
                        location_str = ""

                    # URL
                    slug = job.get("transformedPostingTitle", "")
                    url = (
                        f"https://jobs.apple.com/en-us/details/{pos_id}/{slug}"
                        if pos_id else ""
                    )

                    description = job.get("jobSummary", "")

                    team_info = job.get("team", {})
                    team_name = team_info.get("teamName", "") if isinstance(team_info, dict) else ""

                    results.append(
                        RawJobCreate(
                            source_id=source_id,
                            external_id=job_id or title,
                            title=title,
                            company="apple",
                            location=location_str,
                            url=url,
                            description_raw=description,
                            metadata_json=json.dumps({
                                "team": team_name,
                                "home_office": job.get("homeOffice", ""),
                                "posted_date": job.get("postDateInGMT", ""),
                                "req_id": job.get("reqId", ""),
                            }),
                        )
                    )

                if len(jobs) < PAGE_SIZE or (total and page * PAGE_SIZE >= total):
                    break

                page += 1
                await asyncio.sleep(0.5)

        logger.info("Apple Jobs query=%r fetched %d jobs", self.query, len(results))
        return results
