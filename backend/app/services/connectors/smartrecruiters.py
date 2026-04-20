"""SmartRecruiters connector — public posting API, no auth required.

API:
  GET https://api.smartrecruiters.com/v1/companies/{company}/postings
      ?status=PUBLISHED&limit=100&offset=0&country=us
  GET https://api.smartrecruiters.com/v1/companies/{company}/postings/{jobId}
      -> jobAd.sections.{jobDescription,qualifications,additionalInformation}.text (HTML)

Only US jobs are fetched (country=us filter in listing).
"""

import asyncio
import json

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

SR_LIST_URL = "https://api.smartrecruiters.com/v1/companies/{company}/postings"
SR_DETAIL_URL = "https://api.smartrecruiters.com/v1/companies/{company}/postings/{job_id}"

PAGE_SIZE = 100
DETAIL_CONCURRENCY = 8


class SmartRecruitersConnector(BaseConnector):
    """Fetches US jobs from a SmartRecruiters company board (public API, no auth)."""

    def __init__(self, company: str) -> None:
        self.company = company

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            stubs = await self._fetch_all_stubs(client)

        logger.info(
            "SmartRecruiters company=%s fetching descriptions for %d US jobs",
            self.company, len(stubs),
        )
        results = await self._fetch_details(source_id, stubs)
        logger.info(
            "SmartRecruiters company=%s done — %d jobs ingested",
            self.company, len(results),
        )
        return results

    async def _fetch_all_stubs(self, client: httpx.AsyncClient) -> list[dict]:
        stubs: list[dict] = []
        offset = 0
        total: int | None = None

        while True:
            params = {
                "status": "PUBLISHED",
                "limit": PAGE_SIZE,
                "offset": offset,
                "country": "us",
            }
            try:
                resp = await client.get(
                    SR_LIST_URL.format(company=self.company), params=params
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "SmartRecruiters company=%s listing HTTP %s — aborting",
                    self.company, exc.response.status_code,
                )
                break
            except httpx.RequestError as exc:
                logger.warning(
                    "SmartRecruiters company=%s listing error: %s — aborting",
                    self.company, exc,
                )
                break

            data = resp.json()
            if total is None:
                total = data.get("totalFound", 0)
                logger.info(
                    "SmartRecruiters company=%s total US jobs=%d",
                    self.company, total,
                )

            batch = data.get("content", [])
            stubs.extend(batch)
            offset += len(batch)
            if not batch or offset >= (total or 0):
                break

        return stubs

    async def _fetch_details(
        self, source_id: int, stubs: list[dict]
    ) -> list[RawJobCreate]:
        sem = asyncio.Semaphore(DETAIL_CONCURRENCY)
        results: list[RawJobCreate | None] = [None] * len(stubs)

        async def fetch_one(idx: int, stub: dict, client: httpx.AsyncClient) -> None:
            job_id = stub["id"]
            async with sem:
                try:
                    r = await client.get(
                        SR_DETAIL_URL.format(company=self.company, job_id=job_id)
                    )
                    detail = r.json() if r.status_code == 200 else {}
                except Exception:
                    detail = {}

            job_ad = detail.get("jobAd", {}).get("sections", {})
            description_html = "\n".join(filter(None, [
                (job_ad.get("jobDescription") or {}).get("text", ""),
                (job_ad.get("qualifications") or {}).get("text", ""),
                (job_ad.get("additionalInformation") or {}).get("text", ""),
            ]))

            loc = stub.get("location", {})
            location_str = loc.get("fullLocation") or loc.get("city") or ""

            results[idx] = RawJobCreate(
                source_id=source_id,
                external_id=job_id,
                title=stub.get("name", ""),
                company=self.company,
                location=location_str,
                url=detail.get("postingUrl") or f"https://jobs.smartrecruiters.com/{self.company}/{job_id}",
                description_raw=description_html.strip(),
                metadata_json=json.dumps({
                    "ref_number": stub.get("refNumber", ""),
                    "type_of_employment": (stub.get("typeOfEmployment") or {}).get("id", ""),
                    "experience_level": (stub.get("experienceLevel") or {}).get("id", ""),
                    "department": (stub.get("department") or {}).get("label", ""),
                    "released_date": stub.get("releasedDate", ""),
                }),
            )

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            await asyncio.gather(*[fetch_one(i, s, client) for i, s in enumerate(stubs)])

        return [r for r in results if r is not None]
