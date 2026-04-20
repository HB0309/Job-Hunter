"""Workday connector variant for boards that require a CSRF token.

Some Workday boards (Nvidia, Salesforce, Qualcomm, etc.) return 403 if you
hit the /wday/cxs/ listing API without a valid CSRF token.

Strategy:
1. GET the public careers page HTML to extract the CSRF token from cookies or
   the HTML body (Workday typically embeds it as 'wd-csrf-token').
2. Use that token in subsequent POST requests via the X-CSRF-Token header.
"""

import asyncio
import json
import re

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

WORKDAY_LIST_URL = "https://{tenant}.{wdhost}.myworkdayjobs.com/wday/cxs/{tenant}/{board}/jobs"
WORKDAY_DETAIL_URL = "https://{tenant}.{wdhost}.myworkdayjobs.com/wday/cxs/{tenant}/{board}{path}"
WORKDAY_CAREERS_URL = "https://{tenant}.{wdhost}.myworkdayjobs.com/en-US/{board}"

PAGE_SIZE = 20
DETAIL_CONCURRENCY = 5

# Workday embeds CSRF tokens in several different ways depending on the tenant/version.
# Try all known patterns before giving up.
_CSRF_PATTERNS = [
    re.compile(r'"wd-csrf-token"\s*:\s*"([^"]+)"'),          # JSON key (most common)
    re.compile(r"'wd-csrf-token'\s*:\s*'([^']+)'"),           # single-quoted JSON
    re.compile(r'name="wd-csrf-token"\s+content="([^"]+)"'),  # meta tag
    re.compile(r'content="([^"]+)"\s+name="wd-csrf-token"'),  # meta tag (reversed)
    re.compile(r'"CSRF_TOKEN"\s*:\s*"([^"]+)"'),               # uppercase variant
    re.compile(r'"csrfToken"\s*:\s*"([^"]+)"'),                # camelCase variant
    re.compile(r'csrfToken["\s:=]+([A-Za-z0-9_\-]{20,})'),   # loose match
]


class WorkdayCsrfConnector(BaseConnector):
    """Workday connector that fetches CSRF token before listing jobs.

    Identical to WorkdayConnector but does an initial GET to the careers
    page to extract the CSRF token needed for the JSON API.
    """

    def __init__(self, tenant: str, board: str, wdhost: str = "wd1") -> None:
        self.tenant = tenant
        self.board = board
        self.wdhost = wdhost
        self.list_url = WORKDAY_LIST_URL.format(tenant=tenant, board=board, wdhost=wdhost)
        self.careers_url = WORKDAY_CAREERS_URL.format(tenant=tenant, board=board, wdhost=wdhost)

    def _detail_url(self, external_path: str) -> str:
        return WORKDAY_DETAIL_URL.format(
            tenant=self.tenant, board=self.board,
            wdhost=self.wdhost, path=external_path,
        )

    async def _get_csrf_token(self, client: httpx.AsyncClient) -> str | None:
        """Fetch the careers page and extract the CSRF token.

        Tries multiple URL patterns and extraction strategies because Workday
        embeds CSRF tokens differently depending on the tenant/version.
        """
        urls_to_try = [
            self.careers_url,
            f"https://{self.tenant}.{self.wdhost}.myworkdayjobs.com/{self.board}",
            f"https://{self.tenant}.{self.wdhost}.myworkdayjobs.com/en-US/{self.board}/",
        ]
        for url in urls_to_try:
            try:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code not in (200, 301, 302):
                    continue
                html = resp.text
                # Try all regex patterns against the HTML body
                for pattern in _CSRF_PATTERNS:
                    m = pattern.search(html)
                    if m:
                        token = m.group(1).strip()
                        if len(token) >= 10:
                            logger.debug(
                                "WorkdayCsrf tenant=%s CSRF found via pattern %s",
                                self.tenant, pattern.pattern[:40],
                            )
                            return token
                # Try cookies
                for name, value in resp.cookies.items():
                    if "csrf" in name.lower() and len(value) >= 10:
                        return value
                # Try headers
                for hdr in ("wd-csrf-token", "x-csrf-token", "csrf-token"):
                    val = resp.headers.get(hdr, "")
                    if val and len(val) >= 10:
                        return val
            except Exception as exc:
                logger.warning(
                    "WorkdayCsrf tenant=%s board=%s CSRF fetch failed for %s: %s",
                    self.tenant, self.board, url, exc,
                )
        logger.warning(
            "WorkdayCsrf tenant=%s board=%s no CSRF token found in any pattern",
            self.tenant, self.board,
        )
        return None

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            csrf_token = await self._get_csrf_token(client)
            if not csrf_token:
                logger.warning(
                    "WorkdayCsrf tenant=%s board=%s no CSRF token — trying without",
                    self.tenant, self.board,
                )

            stubs = await self._fetch_all_stubs(client, csrf_token)

        logger.info(
            "WorkdayCsrf tenant=%s board=%s fetching descriptions for %d jobs",
            self.tenant, self.board, len(stubs),
        )
        results = await self._fetch_details(source_id, stubs, csrf_token)
        logger.info(
            "WorkdayCsrf tenant=%s board=%s done — %d jobs ingested",
            self.tenant, self.board, len(results),
        )
        return results

    async def _fetch_all_stubs(
        self, client: httpx.AsyncClient, csrf_token: str | None
    ) -> list[dict]:
        stubs: list[dict] = []
        offset = 0
        total: int | None = None
        headers = {"X-Csrf-Token": csrf_token} if csrf_token else {}

        while True:
            payload = {
                "limit": PAGE_SIZE,
                "offset": offset,
                "searchText": "",
                "appliedFacets": {},
            }
            try:
                resp = await client.post(self.list_url, json=payload, headers=headers)
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "WorkdayCsrf tenant=%s board=%s listing HTTP %s — aborting",
                    self.tenant, self.board, exc.response.status_code,
                )
                break
            except httpx.RequestError as exc:
                logger.warning(
                    "WorkdayCsrf tenant=%s board=%s listing error: %s — aborting",
                    self.tenant, self.board, exc,
                )
                break

            data = resp.json()
            postings = data.get("jobPostings", [])

            if total is None:
                total = data.get("total", 0)
                logger.info(
                    "WorkdayCsrf tenant=%s board=%s total=%d",
                    self.tenant, self.board, total,
                )

            stubs.extend(postings)
            offset += len(postings)
            if not postings or offset >= (total or 0):
                break

        return stubs

    async def _fetch_details(
        self, source_id: int, stubs: list[dict], csrf_token: str | None
    ) -> list[RawJobCreate]:
        sem = asyncio.Semaphore(DETAIL_CONCURRENCY)
        results: list[RawJobCreate | None] = [None] * len(stubs)
        headers = {"X-Csrf-Token": csrf_token} if csrf_token else {}

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
                        r = await client.get(
                            self._detail_url(external_path), headers=headers
                        )
                        if r.status_code == 200:
                            detail = r.json().get("jobPostingInfo", {})
                            description = detail.get("jobDescription", "")
                            time_type = detail.get("timeType", "")
                    except Exception:
                        pass

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

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            await asyncio.gather(*[fetch_one(i, stub, client) for i, stub in enumerate(stubs)])

        return [r for r in results if r is not None]
