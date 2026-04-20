"""Microsoft Careers connector.

Microsoft uses Eightfold AI at jobs.careers.microsoft.com. The Eightfold API
at apply.careers.microsoft.com requires authentication (returns 403 for public
requests — "Not authorized for PCSX").

Status: API is locked behind auth. This connector returns empty results and
logs a warning. Phase D (automated scoring) could use Playwright to render the
SPA, but that is out of scope for now.

Left in place so the source type and seeding infrastructure is ready when/if
a public API endpoint becomes available.
"""

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)


class MicrosoftCareersConnector(BaseConnector):
    """Placeholder: Microsoft Careers (Eightfold) API requires authentication.

    The Eightfold endpoint at apply.careers.microsoft.com returns 403 for
    unauthenticated requests. Browser automation (Playwright) would be needed
    to render the SPA and scrape job listings — out of scope for Phase A.
    """

    def __init__(self, query: str = "software engineer") -> None:
        self.query = query

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        logger.warning(
            "MicrosoftCareersConnector: API locked (Eightfold requires auth) — "
            "returning 0 jobs for query=%r. Use LinkedIn source for Microsoft jobs.",
            self.query,
        )
        return []
