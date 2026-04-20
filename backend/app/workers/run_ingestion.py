"""CLI entrypoint: run ingestion for all enabled sources.

Usage: python -m app.workers.run_ingestion
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session
from app.core.logging import get_logger, setup_logging
from app.models.source import Source, SourceType
from app.services.connectors.amazon import AmazonJobsConnector
from app.services.connectors.apple import AppleJobsConnector
from app.services.connectors.apify_linkedin import ApifyLinkedInConnector
from app.services.connectors.ashby import AshbyConnector
from app.services.connectors.google import GoogleCareersConnector
from app.services.connectors.greenhouse import GreenhouseConnector
from app.services.connectors.lever import LeverConnector
from app.services.connectors.meta import MetaCareersConnector
from app.services.connectors.microsoft import MicrosoftCareersConnector
from app.services.connectors.workday import WorkdayConnector
from app.services.connectors.jobright import JobrightConnector
from app.services.connectors.smartrecruiters import SmartRecruitersConnector
from app.services.connectors.workday_csrf import WorkdayCsrfConnector
from app.services.ingestion.ingest import run_ingestion_for_connector

logger = get_logger(__name__)

INITIAL_LOOKBACK_DAYS = 5  # how far back to go on first-ever run


def _build_connector(source: Source):
    """Factory: return the right connector for a source type."""
    if source.source_type == SourceType.APIFY_LINKEDIN:
        config = json.loads(source.config) if source.config else {}
        keyword = config.get("keyword", "")
        location = config.get("location", "")

        if not keyword:
            logger.warning("Source %s has no keyword configured, skipping", source.name)
            return None
        if not settings.apify_api_token:
            logger.error("APIFY_API_TOKEN not set — cannot run LinkedIn connector")
            return None

        # Incremental: use last_fetched_at as cutoff.
        # Initial run: use now - 5 days as cutoff.
        if source.last_fetched_at:
            date_from = source.last_fetched_at.replace(tzinfo=timezone.utc) \
                if source.last_fetched_at.tzinfo is None \
                else source.last_fetched_at
            logger.info("Incremental run for '%s': fetching since %s", source.name, date_from.isoformat())
        else:
            date_from = datetime.now(timezone.utc) - timedelta(days=INITIAL_LOOKBACK_DAYS)
            logger.info("Initial run for '%s': fetching last %d days", source.name, INITIAL_LOOKBACK_DAYS)

        return ApifyLinkedInConnector(
            api_token=settings.apify_api_token,
            keyword=keyword,
            location=location,
            date_from=date_from,
        )

    if source.source_type == SourceType.GREENHOUSE:
        config = json.loads(source.config) if source.config else {}
        board_token = config.get("board_token", "")
        if not board_token:
            logger.warning("Source %s has no board_token configured, skipping", source.name)
            return None
        return GreenhouseConnector(board_token=board_token)

    if source.source_type == SourceType.LEVER:
        config = json.loads(source.config) if source.config else {}
        company_slug = config.get("company_slug", "")
        if not company_slug:
            logger.warning("Source %s has no company_slug configured, skipping", source.name)
            return None
        return LeverConnector(company_slug=company_slug)

    if source.source_type == SourceType.ASHBY:
        config = json.loads(source.config) if source.config else {}
        company_slug = config.get("company_slug", "")
        if not company_slug:
            logger.warning("Source %s has no company_slug configured, skipping", source.name)
            return None
        return AshbyConnector(company_slug=company_slug)

    if source.source_type == SourceType.WORKDAY:
        config = json.loads(source.config) if source.config else {}
        tenant = config.get("tenant", "")
        board = config.get("board", "")
        wdhost = config.get("wdhost", "wd1")
        if not tenant or not board:
            logger.warning("Source %s has no tenant/board configured, skipping", source.name)
            return None
        return WorkdayConnector(tenant=tenant, board=board, wdhost=wdhost)

    if source.source_type == SourceType.WORKDAY_CSRF:
        config = json.loads(source.config) if source.config else {}
        tenant = config.get("tenant", "")
        board = config.get("board", "")
        wdhost = config.get("wdhost", "wd1")
        if not tenant or not board:
            logger.warning("Source %s has no tenant/board configured, skipping", source.name)
            return None
        return WorkdayCsrfConnector(tenant=tenant, board=board, wdhost=wdhost)

    if source.source_type == SourceType.GOOGLE_CAREERS:
        config = json.loads(source.config) if source.config else {}
        query = config.get("query", "software engineer")
        location = config.get("location", "United States")
        return GoogleCareersConnector(query=query, location=location)

    if source.source_type == SourceType.AMAZON_JOBS:
        config = json.loads(source.config) if source.config else {}
        query = config.get("query", "")
        categories = config.get("categories", ["software-development"])
        return AmazonJobsConnector(query=query, categories=categories)

    if source.source_type == SourceType.APPLE_JOBS:
        config = json.loads(source.config) if source.config else {}
        query = config.get("query", "software engineer")
        return AppleJobsConnector(query=query)

    if source.source_type == SourceType.MICROSOFT_CAREERS:
        config = json.loads(source.config) if source.config else {}
        query = config.get("query", "software engineer")
        return MicrosoftCareersConnector(query=query)

    if source.source_type == SourceType.META_CAREERS:
        config = json.loads(source.config) if source.config else {}
        query = config.get("query", "software engineer")
        return MetaCareersConnector(query=query)

    if source.source_type == SourceType.JOBRIGHT:
        config = json.loads(source.config) if source.config else {}
        query = config.get("query", "")
        max_pages = config.get("max_pages", settings.jobright_max_pages)
        if not query:
            logger.warning("Source %s has no query configured, skipping", source.name)
            return None
        return JobrightConnector(query=query, max_pages=max_pages)

    if source.source_type == SourceType.SMARTRECRUITERS:
        config = json.loads(source.config) if source.config else {}
        company = config.get("company", "")
        if not company:
            logger.warning("Source %s has no company configured, skipping", source.name)
            return None
        return SmartRecruitersConnector(company=company)

    logger.warning("No connector implemented for source_type=%s", source.source_type)
    return None


async def run_all() -> None:
    setup_logging()
    async with async_session() as session:
        sources = await _get_enabled_sources(session)
        logger.info("Found %d enabled sources", len(sources))

        total_inserted = 0
        for source in sources:
            connector = _build_connector(source)
            if connector is None:
                continue
            try:
                inserted = await run_ingestion_for_connector(connector, source.id, session)
                total_inserted += inserted
                await _mark_fetched(session, source)
            except Exception:
                logger.exception("Ingestion failed for source=%s (id=%d)", source.name, source.id)

        logger.info("Ingestion complete. Total new jobs: %d", total_inserted)


async def _get_enabled_sources(session: AsyncSession) -> list[Source]:
    stmt = select(Source).where(Source.enabled.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _mark_fetched(session: AsyncSession, source: Source) -> None:
    """Stamp last_fetched_at = now so next run knows when this one ran."""
    source.last_fetched_at = datetime.now(timezone.utc)
    await session.commit()


if __name__ == "__main__":
    asyncio.run(run_all())
