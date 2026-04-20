from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.source import Source

router = APIRouter()


@router.get("/")
async def list_sources(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Source).order_by(Source.id))
    sources = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "enabled": s.enabled,
            "last_fetched_at": s.last_fetched_at,
        }
        for s in sources
    ]

# TODO Phase 2: POST /sources for adding new sources via dashboard
