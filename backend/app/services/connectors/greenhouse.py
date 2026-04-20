import json

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

GREENHOUSE_API_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"


class GreenhouseConnector(BaseConnector):
    """Fetches jobs from Greenhouse board API (public, no auth needed)."""

    def __init__(self, board_token: str) -> None:
        self.board_token = board_token

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        url = GREENHOUSE_API_URL.format(board_token=self.board_token)
        results: list[RawJobCreate] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params={"content": "true"})
            resp.raise_for_status()
            data = resp.json()

        jobs = data.get("jobs", [])
        logger.info("Greenhouse board=%s returned %d jobs", self.board_token, len(jobs))

        for job in jobs:
            location = self._extract_location(job)
            results.append(
                RawJobCreate(
                    source_id=source_id,
                    external_id=str(job["id"]),
                    title=job.get("title", ""),
                    company=self.board_token,  # board token is typically the company slug
                    location=location,
                    url=job.get("absolute_url", ""),
                    description_raw=job.get("content", ""),
                    metadata_json=json.dumps(
                        {
                            "departments": [d.get("name", "") for d in job.get("departments", [])],
                            "offices": [o.get("name", "") for o in job.get("offices", [])],
                            "updated_at": job.get("updated_at", ""),
                        }
                    ),
                )
            )
        return results

    @staticmethod
    def _extract_location(job: dict) -> str:
        loc = job.get("location", {})
        if isinstance(loc, dict):
            return loc.get("name", "")
        return str(loc) if loc else ""
