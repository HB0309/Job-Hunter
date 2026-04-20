import asyncio
import json
from datetime import datetime, timezone
from urllib.parse import urlencode

from apify_client import ApifyClient

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

ACTOR_ID = "curious_coder~linkedin-jobs-scraper"
LINKEDIN_JOBS_BASE = "https://www.linkedin.com/jobs/search/"


def _build_linkedin_url(keyword: str, location: str) -> str:
    # sortBy=DD = sort by date descending (most recent first)
    # f_E=2,3 = Entry level + Associate (covers new grad / early career roles)
    params = {"keywords": keyword, "location": location, "sortBy": "DD", "f_E": "2,3"}
    return LINKEDIN_JOBS_BASE + "?" + urlencode(params)


def _parse_posted_at(posted_at_str: str) -> datetime:
    """Parse LinkedIn postedAt ISO string into a timezone-aware UTC datetime."""
    if not posted_at_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(posted_at_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return datetime.min.replace(tzinfo=timezone.utc)


class ApifyLinkedInConnector(BaseConnector):
    """Fetches LinkedIn job listings via the Apify curious_coder/linkedin-jobs-scraper actor.

    date_from controls the cutoff:
      - None (never run before): kept by caller, connector accepts all items
      - datetime: only jobs posted at or after this time are kept
    """

    def __init__(
        self,
        api_token: str,
        keyword: str,
        location: str,
        date_from: datetime | None = None,
    ) -> None:
        self.api_token = api_token
        self.keyword = keyword
        self.location = location
        self.date_from = date_from  # tz-aware UTC datetime

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        return await asyncio.to_thread(self._fetch_sync, source_id)

    def _fetch_sync(self, source_id: int) -> list[RawJobCreate]:
        client = ApifyClient(self.api_token)
        search_url = _build_linkedin_url(self.keyword, self.location)

        mode = "initial (5-day window)" if self.date_from else "unconstrained"
        logger.info(
            "Running Apify actor: keyword=%s location=%s mode=%s date_from=%s",
            self.keyword, self.location, mode,
            self.date_from.isoformat() if self.date_from else "none",
        )

        run = client.actor(ACTOR_ID).call(run_input={"urls": [search_url]})

        if not run:
            logger.warning("Actor run returned None for keyword=%s", self.keyword)
            return []

        items = client.dataset(run["defaultDatasetId"]).list_items().items
        logger.info("Apify returned %d raw items for keyword=%s", len(items), self.keyword)

        results: list[RawJobCreate] = []
        skipped_old = 0

        for item in items:
            job_id = str(item.get("id", ""))
            if not job_id:
                continue

            # Date filter: drop jobs older than the cutoff
            if self.date_from:
                posted_at = _parse_posted_at(item.get("postedAt", ""))
                if posted_at < self.date_from:
                    skipped_old += 1
                    continue

            description = item.get("descriptionText", "") or item.get("descriptionHtml", "")
            results.append(RawJobCreate(
                source_id=source_id,
                external_id=job_id,
                title=item.get("title", ""),
                company=item.get("companyName", ""),
                location=item.get("location", ""),
                url=item.get("link", ""),
                description_raw=description,
                metadata_json=json.dumps({
                    "employment_type": item.get("employmentType", ""),
                    "seniority_level": item.get("seniorityLevel", ""),
                    "is_remote": item.get("workRemoteAllowed", False),
                    "posted_at": item.get("postedAt", ""),
                    "company_url": item.get("companyLinkedinUrl", ""),
                    "industries": item.get("industries", []),
                    "salary": item.get("salary", ""),
                    "search_keyword": self.keyword,
                }),
            ))

        if skipped_old:
            logger.info("Skipped %d jobs older than cutoff date", skipped_old)
        logger.info("Keeping %d jobs within date window for keyword=%s", len(results), self.keyword)
        return results
