from abc import ABC, abstractmethod

from app.schemas.raw_job import RawJobCreate


class BaseConnector(ABC):
    """Interface that every job source connector must implement."""

    @abstractmethod
    async def fetch_jobs(self, source_id: int) -> list[RawJobCreate]:
        """Fetch jobs from the source and return normalized RawJobCreate objects."""
        ...

    # TODO Phase 2+: add methods for incremental fetch / last-seen tracking
