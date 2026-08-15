"""FastAPI application entrypoint.

Wires routers, creates tables at startup, and starts the background mail
polling scheduler when MAIL_INGESTION_MODE=background.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, engine
from app.jobs import start_scheduler, stop_scheduler
from app.routers.tasks import router as tasks_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # NOTE: dev convenience only; use Alembic migrations in production.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    settings = get_settings()
    if settings.polling_enabled:
        start_scheduler()

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
