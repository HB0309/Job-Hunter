import asyncio
import json

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

# Workday public API — works without CSRF for companies that allow unauthenticated access.
# Listing: POST https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{board}/jobs
# Detail:  GET  https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{board}{externalPath}
# Note: Workday only populates `total` on the first listing page (returns 0 on subsequent pages).
WORKDAY_LIST_URL = "https://{tenant}.{wdhost}.myworkdayjobs.com/wday/cxs/{tenant}/{board}/jobs"
WORKDAY_DETAIL_URL = "https://{tenant}.{wdhost}.myworkdayjobs.com/wday/cxs/{tenant}/{board}{path}"

PAGE_SIZE = 20
DETAIL_CONCURRENCY = 8  # max simultaneous detail requests per company


class WorkdayConnector(BaseConnector):
    """Fetches jobs from Workday's public job board API (no auth for open boards).

    Two-phase fetch:
    1. Paginate the listing endpoint to collect all job stubs (title, location, path).
    2. Fetch each job's detail page concurrently to get the full description.
    """

    def __init__(self, tenant: str, board: str, wdhost: str = "wd1") -> None:
        self.tenant = tenant
        self.board = board
        self.wdhost = wdhost
        self.list_url = WORKDAY_LIST_URL.format(tenant=tenant, board=board, wdhost=wdhost)

    def _detail_url(self, external_path: str) -> str:
        return WORKDAY_DETAIL_URL.format(
            tenant=self.tenant, board=self.board, wdhost=self.wdhost, path=external_path
        )

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        stubs = await self._fetch_all_stubs()
        logger.info(
            "Workday tenant=%s board=%s fetching descriptions for %d jobs",
            self.tenant, self.board, len(stubs),
        )
        results = await self._fetch_details(source_id, stubs)
        logger.info(
            "Workday tenant=%s board=%s done — %d jobs ingested",
            self.tenant, self.board, len(results),
        )
        return results

    async def _fetch_all_stubs(self) -> list[dict]:
        """Paginate listing endpoint, return list of raw job stub dicts."""
        stubs: list[dict] = []
        offset = 0
        total: int | None = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                payload = {
                    "limit": PAGE_SIZE,
                    "offset": offset,
                    "searchText": "",
                    "appliedFacets": {},
                }
                try:
                    resp = await client.post(self.list_url, json=payload)
                    resp.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        "Workday tenant=%s board=%s listing HTTP %s — aborting",
                        self.tenant, self.board, exc.response.status_code,
                    )
                    break
                except httpx.RequestError as exc:
                    logger.warning(
                        "Workday tenant=%s board=%s listing error: %s — aborting",
                        self.tenant, self.board, exc,
                    )
                    break

                data = resp.json()
                postings = data.get("jobPostings", [])

                if total is None:
                    total = data.get("total", 0)
                    logger.info(
                        "Workday tenant=%s board=%s total=%d",
                        self.tenant, self.board, total,
                    )

                stubs.extend(postings)
                offset += len(postings)
                if not postings or offset >= (total or 0):
                    break

        return stubs

    async def _fetch_details(self, source_id: int, stubs: list[dict]) -> list[RawJobCreate]:
        """Fetch individual job detail pages concurrently and build RawJobCreate list."""
        sem = asyncio.Semaphore(DETAIL_CONCURRENCY)
        results: list[RawJobCreate | None] = [None] * len(stubs)

        async def fetch_one(idx: int, stub: dict, client: httpx.AsyncClient) -> None:
            external_path = stub.get("externalPath", "")
            external_id = external_path.lstrip("/").split("/")[-1] if external_path else ""
            apply_url = (
                f"https://{self.tenant}.{self.wdhost}.myworkdayjobs.com/en-US/{self.board}{external_path}"
                if external_path else ""
            )
            description = ""
            posted_on = stub.get("postedOn", "")
            time_type = ""

            if external_path:
                async with sem:
                    try:
                        r = await client.get(self._detail_url(external_path))
                        if r.status_code == 200:
                            detail = r.json().get("jobPostingInfo", {})
                            description = detail.get("jobDescription", "")
                            time_type = detail.get("timeType", "")
                    except Exception:
                        pass  # fall back to empty description

            results[idx] = RawJobCreate(
                source_id=source_id,
                external_id=external_id or str((stub.get("bulletFields") or [""])[0]),
                title=stub.get("title", ""),
                company=self.tenant,
                location=stub.get("locationsText", ""),
                url=apply_url,
                description_raw=description,
                metadata_json=json.dumps({
                    "external_path": external_path,
                    "posted_on": posted_on,
                    "time_type": time_type,
                }),
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            await asyncio.gather(*[fetch_one(i, stub, client) for i, stub in enumerate(stubs)])

        return [r for r in results if r is not None]
