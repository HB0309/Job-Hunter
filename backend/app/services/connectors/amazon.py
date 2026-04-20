"""Amazon Jobs connector — uses the public amazon.jobs JSON search API."""

import json

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

AMAZON_API_URL = "https://www.amazon.jobs/en/search.json"
RESULT_LIMIT = 10  # Amazon's API max per page is 10


class AmazonJobsConnector(BaseConnector):
    """Fetches jobs from Amazon Jobs public search API.

    Amazon Jobs uses a paginated JSON API with offset-based pagination.
    Filters to US Software Development category by default.
    """

    def __init__(self, query: str = "", categories: list[str] | None = None) -> None:
        self.query = query
        self.categories = categories or ["software-development"]

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        results: list[RawJobCreate] = []
        offset = 0

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            while True:
                # Build query params — Amazon uses repeated params for arrays
                params = [
                    ("result_limit", RESULT_LIMIT),
                    ("offset", offset),
                    ("sort", "recent"),
                    ("base_query", self.query),
                    ("loc_query", "united states"),
                    ("latitude", ""),
                    ("longitude", ""),
                    ("loc_group_id", ""),
                    ("country", "USA"),
                    ("region", ""),
                    ("city", ""),
                    ("county", ""),
                ]
                for cat in self.categories:
                    params.append(("category[]", cat))
                # Add location facets
                params.extend([
                    ("facets[]", "normalized_location"),
                    ("facets[]", "country"),
                    ("facets[]", "category"),
                    ("facets[]", "schedule_type_id"),
                    ("facets[]", "employee_class"),
                ])

                try:
                    resp = await client.get(AMAZON_API_URL, params=params)
                    resp.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        "Amazon Jobs HTTP %s at offset %d — aborting",
                        exc.response.status_code, offset,
                    )
                    break
                except httpx.RequestError as exc:
                    logger.warning("Amazon Jobs request error: %s — aborting", exc)
                    break

                data = resp.json()
                jobs = data.get("jobs", [])
                hits = data.get("hits", 0)

                if offset == 0:
                    logger.info("Amazon Jobs query=%r total hits=%d", self.query, hits)

                if not jobs:
                    break

                for job in jobs:
                    job_id = str(job.get("id_icims", job.get("id", "")))
                    title = job.get("title", "")

                    # Location
                    city = job.get("city", "")
                    state = job.get("state", "")
                    country = job.get("country_code", "US")
                    if city and state:
                        location_str = f"{city}, {state}"
                    elif city:
                        location_str = city
                    else:
                        location_str = job.get("normalized_location", "") or country

                    job_path = job.get("job_path", "")
                    url = f"https://www.amazon.jobs{job_path}" if job_path else ""

                    description = job.get("description", "") or job.get("description_short", "")

                    results.append(
                        RawJobCreate(
                            source_id=source_id,
                            external_id=job_id or title,
                            title=title,
                            company="amazon",
                            location=location_str,
                            url=url,
                            description_raw=description,
                            metadata_json=json.dumps({
                                "category": job.get("category", ""),
                                "business_category": job.get("business_category", ""),
                                "schedule_type": job.get("schedule_type_id", ""),
                                "employee_class": job.get("employee_class", ""),
                                "posted_date": job.get("posted_date", ""),
                                "updated_time": job.get("updated_time", ""),
                            }),
                        )
                    )

                offset += len(jobs)
                if offset >= hits or len(jobs) < RESULT_LIMIT:
                    break

        logger.info("Amazon Jobs query=%r fetched %d jobs", self.query, len(results))
        return results
