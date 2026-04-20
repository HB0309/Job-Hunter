from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    yield


app = FastAPI(
    title="Job Hunter",
    description="Local-first job discovery and ranking system",
    version="0.1.0",
    lifespan=lifespan,
)

# Import and register routers
from app.api.routes_health import router as health_router  # noqa: E402
from app.api.routes_sources import router as sources_router  # noqa: E402
from app.api.routes_jobs import router as jobs_router  # noqa: E402
from app.api.routes_raw_jobs import router as raw_jobs_router  # noqa: E402

app.include_router(health_router)
app.include_router(sources_router, prefix="/api/sources", tags=["sources"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(raw_jobs_router, prefix="/api/raw-jobs", tags=["raw-jobs"])

# Dashboard UI — served from /frontend mounted into container at /app/frontend
import os  # noqa: E402
_frontend = "/app/frontend"
if os.path.isdir(_frontend):
    app.mount("/static", StaticFiles(directory=_frontend), name="static")

    @app.get("/", include_in_schema=False)
    async def dashboard():
        return FileResponse(f"{_frontend}/index.html")
