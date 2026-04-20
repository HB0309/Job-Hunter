import json
import re

import httpx

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)

LEVER_API_URL = "https://api.lever.co/v0/postings/{company}"

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", text or "")).strip()


def _build_full_description(job: dict) -> str:
    """Concatenate all Lever text sections into one description.

    Lever splits job content across several fields:
      - descriptionPlain / description  — main body
      - opening / openingPlain          — intro paragraph
      - lists                           — bullet sections ("What We Value", "What We Require", etc.)
      - additional / additionalPlain    — footer / extra requirements

    The clearance requirement often appears in a `lists` section rather than
    the main description, so we must include all sections.
    """
    parts: list[str] = []

    opening = job.get("openingPlain") or _strip_html(job.get("opening", ""))
    if opening:
        parts.append(opening)

    main = job.get("descriptionPlain") or _strip_html(job.get("description", ""))
    if main:
        parts.append(main)

    for section in job.get("lists", []):
        header = section.get("text", "")
        content = _strip_html(section.get("content", ""))
        if header:
            parts.append(f"{header}: {content}")
        elif content:
            parts.append(content)

    additional = job.get("additionalPlain") or _strip_html(job.get("additional", ""))
    if additional:
        parts.append(additional)

    return "\n\n".join(parts)


class LeverConnector(BaseConnector):
    """Fetches jobs from Lever's public postings API (no auth needed)."""

    def __init__(self, company_slug: str) -> None:
        self.company_slug = company_slug

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        url = LEVER_API_URL.format(company=self.company_slug)
        results: list[RawJobCreate] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params={"mode": "json"})
            resp.raise_for_status()
            jobs = resp.json()

        logger.info("Lever company=%s returned %d jobs", self.company_slug, len(jobs))

        for job in jobs:
            categories = job.get("categories", {})
            location = categories.get("location", "") or categories.get("allLocations", [""])[0] if isinstance(categories.get("allLocations"), list) else ""
            results.append(
                RawJobCreate(
                    source_id=source_id,
                    external_id=job.get("id", ""),
                    title=job.get("text", ""),
                    company=self.company_slug,
                    location=location,
                    url=job.get("hostedUrl", "") or job.get("applyUrl", ""),
                    description_raw=_build_full_description(job),
                    metadata_json=json.dumps(
                        {
                            "team": categories.get("team", ""),
                            "commitment": categories.get("commitment", ""),
                            "level": categories.get("level", ""),
                            "created_at": job.get("createdAt", ""),
                        }
                    ),
                )
            )
        return results
