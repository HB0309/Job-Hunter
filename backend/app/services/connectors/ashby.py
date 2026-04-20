import json

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

ASHBY_API_URL = "https://api.ashbyhq.com/posting-api/job-board/{company}"


class AshbyConnector(BaseConnector):
    """Fetches jobs from Ashby's public job board API (no auth needed)."""

    def __init__(self, company_slug: str) -> None:
        self.company_slug = company_slug

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        url = ASHBY_API_URL.format(company=self.company_slug)
        results: list[RawJobCreate] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params={"includeCompensation": "true"})
            resp.raise_for_status()
            data = resp.json()

        jobs = data if isinstance(data, list) else data.get("jobs", [])
        logger.info("Ashby company=%s returned %d jobs", self.company_slug, len(jobs))

        for job in jobs:
            results.append(
                RawJobCreate(
                    source_id=source_id,
                    external_id=job.get("id", ""),
                    title=job.get("title", ""),
                    company=self.company_slug,
                    location=job.get("locationName", "") or ("Remote" if job.get("isRemote") else ""),
                    url=job.get("applicationLink", "") or job.get("jobUrl", ""),
                    description_raw=job.get("descriptionHtml", "") or job.get("descriptionPlain", ""),
                    metadata_json=json.dumps(
                        {
                            "employment_type": job.get("employmentType", ""),
                            "department": job.get("department", ""),
                            "published_at": job.get("publishedAt", ""),
                            "is_remote": job.get("isRemote", False),
                        }
                    ),
                )
            )
        return results
