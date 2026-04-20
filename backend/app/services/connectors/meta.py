"""Meta Careers connector.

Meta's careers site (metacareers.com) uses a GraphQL API with a doc_id that
changes on each deployment. The public GraphQL endpoint at
https://www.metacareers.com/graphql returns 400 for invalid/stale doc_ids,
and there is no stable public REST API.

Status: API is locked. This connector returns empty results and logs a warning.

Left in place so the source type and seeding infrastructure is ready when/if
a stable public endpoint becomes available, or for future browser-automation work.
"""

from app.core.logging import get_logger
from app.schemas.raw_job import RawJobCreate
from app.services.connectors.base import BaseConnector

logger = get_logger(__name__)


class MetaCareersConnector(BaseConnector):
    """Placeholder: Meta Careers GraphQL API requires stable doc_id.

    The doc_id embedded in the metacareers.com SPA changes on each deploy.
    Without a stable public REST API, scraping would require browser automation.
    Out of scope for Phase A.
    """

    def __init__(self, query: str = "software engineer") -> None:
        self.query = query

    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        logger.warning(
            "MetaCareersConnector: API locked (GraphQL doc_id unstable) — "
            "returning 0 jobs for query=%r. Use LinkedIn source for Meta jobs.",
            self.query,
        )
        return []
