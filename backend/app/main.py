"""FastAPI application entrypoint.

Wires routers, creates tables at startup, and starts the background mail
poller from persisted ingestion settings.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import configure_logging

configure_logging()

from app.db import Base, SessionLocal, engine
from app.jobs import apply_scheduler_settings, stop_scheduler
from app.routers.settings import router as settings_router
from app.routers.tasks import router as tasks_router
from app.services.ingestion_settings import get_ingestion_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # NOTE: dev convenience only; use Alembic migrations in production.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        ingestion = await get_ingestion_settings(session)
        apply_scheduler_settings(ingestion.mode, ingestion.poll_hours)

    yield

    stop_scheduler()
    await engine.dispose()


app = FastAPI(title="Office Task Tracker API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
