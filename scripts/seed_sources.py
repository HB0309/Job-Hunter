"""Seed the sources table with LinkedIn search configurations.

Usage: python scripts/seed_sources.py
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.config import settings
from app.core.db import async_session
from app.core.logging import setup_logging, get_logger
from app.models.source import Source, SourceType

logger = get_logger(__name__)


async def seed():
    setup_logging()

    async with async_session() as session:
        # Seed LinkedIn sources
        for search in settings.linkedin_search_list:
            name = f"linkedin:{search['keyword']}:{search['location']}"
            existing = await session.execute(
                select(Source).where(Source.name == name)
            )
            if existing.scalar_one_or_none():
                logger.info("Source '%s' already exists, skipping", name)
                continue
            source = Source(
                name=name,
                source_type=SourceType.APIFY_LINKEDIN,
                config=json.dumps({
                    "keyword": search["keyword"],
                    "location": search["location"],
                    "pages": settings.linkedin_pages_per_search,
                }),
            )
            session.add(source)
            logger.info("Added source '%s'", name)

        # Seed Greenhouse sources
        for token in settings.greenhouse_token_list:
            name = f"greenhouse:{token}"
            existing = await session.execute(
                select(Source).where(Source.name == name)
            )
            if existing.scalar_one_or_none():
                logger.info("Source '%s' already exists, skipping", name)
                continue
            source = Source(
                name=name,
                source_type=SourceType.GREENHOUSE,
                config=json.dumps({"board_token": token}),
            )
            session.add(source)
            logger.info("Added source '%s'", name)

        # Seed Lever sources
        for slug in settings.lever_slug_list:
            name = f"lever:{slug}"
            existing = await session.execute(
                select(Source).where(Source.name == name)
            )
            if existing.scalar_one_or_none():
                logger.info("Source '%s' already exists, skipping", name)
                continue
            source = Source(
                name=name,
                source_type=SourceType.LEVER,
                config=json.dumps({"company_slug": slug}),
            )
            session.add(source)
            logger.info("Added source '%s'", name)

        # Seed Ashby sources
        for slug in settings.ashby_slug_list:
            name = f"ashby:{slug}"
            existing = await session.execute(
                select(Source).where(Source.name == name)
            )
            if existing.scalar_one_or_none():
                logger.info("Source '%s' already exists, skipping", name)
                continue
            source = Source(
                name=name,
                source_type=SourceType.ASHBY,
                config=json.dumps({"company_slug": slug}),
            )
            session.add(source)
            logger.info("Added source '%s'", name)

        # Seed Workday sources
        for company in settings.workday_company_list:
            tenant = company["tenant"]
            board = company["board"]
            wdhost = company["wdhost"]
            name = f"workday:{tenant}:{board}"
            existing = await session.execute(
                select(Source).where(Source.name == name)
            )
            if existing.scalar_one_or_none():
                logger.info("Source '%s' already exists, skipping", name)
                continue
            source = Source(
                name=name,
                source_type=SourceType.WORKDAY,
                config=json.dumps({"tenant": tenant, "board": board, "wdhost": wdhost}),
            )
            session.add(source)
            logger.info("Added source '%s'", name)

        # Seed Workday CSRF sources
        for company in settings.workday_csrf_company_list:
            tenant = company["tenant"]
            board = company["board"]
            wdhost = company["wdhost"]
            name = f"workday_csrf:{tenant}:{board}"
            existing = await session.execute(
                select(Source).where(Source.name == name)
            )
            if existing.scalar_one_or_none():
                logger.info("Source '%s' already exists, skipping", name)
                continue
            source = Source(
                name=name,
                source_type=SourceType.WORKDAY_CSRF,
                config=json.dumps({"tenant": tenant, "board": board, "wdhost": wdhost}),
            )
            session.add(source)
            logger.info("Added source '%s'", name)

        # Seed Google Careers sources
        if settings.google_enabled.lower() == "true":
            for query in settings.google_query_list:
                name = f"google_careers:{query}"
                existing = await session.execute(
                    select(Source).where(Source.name == name)
                )
                if existing.scalar_one_or_none():
                    logger.info("Source '%s' already exists, skipping", name)
                    continue
                source = Source(
                    name=name,
                    source_type=SourceType.GOOGLE_CAREERS,
                    config=json.dumps({"query": query, "location": "United States"}),
                )
                session.add(source)
                logger.info("Added source '%s'", name)

        # Seed Amazon Jobs sources
        if settings.amazon_enabled.lower() == "true":
            for query in settings.amazon_query_list:
                name = f"amazon_jobs:{query}"
                existing = await session.execute(
                    select(Source).where(Source.name == name)
                )
                if existing.scalar_one_or_none():
                    logger.info("Source '%s' already exists, skipping", name)
                    continue
                source = Source(
                    name=name,
                    source_type=SourceType.AMAZON_JOBS,
                    config=json.dumps({"query": query, "categories": ["software-development"]}),
                )
                session.add(source)
                logger.info("Added source '%s'", name)

        # Seed Apple Jobs sources
        if settings.apple_enabled.lower() == "true":
            for query in settings.apple_query_list:
                name = f"apple_jobs:{query}"
                existing = await session.execute(
                    select(Source).where(Source.name == name)
                )
                if existing.scalar_one_or_none():
                    logger.info("Source '%s' already exists, skipping", name)
                    continue
                source = Source(
                    name=name,
                    source_type=SourceType.APPLE_JOBS,
                    config=json.dumps({"query": query}),
                )
                session.add(source)
                logger.info("Added source '%s'", name)

        # Seed Microsoft Careers sources
        if settings.microsoft_enabled.lower() == "true":
            for query in settings.microsoft_query_list:
                name = f"microsoft_careers:{query}"
                existing = await session.execute(
                    select(Source).where(Source.name == name)
                )
                if existing.scalar_one_or_none():
                    logger.info("Source '%s' already exists, skipping", name)
                    continue
                source = Source(
                    name=name,
                    source_type=SourceType.MICROSOFT_CAREERS,
                    config=json.dumps({"query": query}),
                )
                session.add(source)
                logger.info("Added source '%s'", name)

        # Seed Meta Careers sources
        if settings.meta_enabled.lower() == "true":
            for query in settings.meta_query_list:
                name = f"meta_careers:{query}"
                existing = await session.execute(
                    select(Source).where(Source.name == name)
                )
                if existing.scalar_one_or_none():
                    logger.info("Source '%s' already exists, skipping", name)
                    continue
                source = Source(
                    name=name,
                    source_type=SourceType.META_CAREERS,
                    config=json.dumps({"query": query}),
                )
                session.add(source)
                logger.info("Added source '%s'", name)

        # Seed SmartRecruiters sources
        for company in settings.smartrecruiters_company_list:
            name = f"smartrecruiters:{company}"
            existing = await session.execute(
                select(Source).where(Source.name == name)
            )
            if existing.scalar_one_or_none():
                logger.info("Source '%s' already exists, skipping", name)
                continue
            source = Source(
                name=name,
                source_type=SourceType.SMARTRECRUITERS,
                config=json.dumps({"company": company}),
            )
            session.add(source)
            logger.info("Added source '%s'", name)

        # Seed Jobright sources
        jobright_queries = [q.strip() for q in settings.jobright_queries.split(",") if q.strip()]
        for query in jobright_queries:
            name = f"jobright:{query}"
            existing = await session.execute(
                select(Source).where(Source.name == name)
            )
            if existing.scalar_one_or_none():
                logger.info("Source '%s' already exists, skipping", name)
                continue
            source = Source(
                name=name,
                source_type=SourceType.JOBRIGHT,
                config=json.dumps({"query": query, "max_pages": settings.jobright_max_pages}),
            )
            session.add(source)
            logger.info("Added source '%s'", name)

        await session.commit()
    logger.info("Seeding complete")


if __name__ == "__main__":
    asyncio.run(seed())
