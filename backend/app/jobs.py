"""APScheduler background job that ingests emails on an interval.

Started from `app.main` via a FastAPI lifespan when `MAIL_INGESTION_MODE`
is "background".
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.db import SessionLocal
from app.services.mail import ingest_emails

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _poll() -> None:
    """Single ingestion pass, run on the scheduler interval."""
    async with SessionLocal() as session:
        result = await ingest_emails(session)
        if result.scraped:
            logger.info(
                "Ingested %d emails (%d tasks created)",
                result.scraped,
                result.created_tasks,
            )


def start_scheduler() -> AsyncIOScheduler:
    """Start the background scheduler (idempotent)."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    settings = get_settings()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _poll,
        IntervalTrigger(seconds=settings.mail_poll_seconds),
        id="mail_poll",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Mail polling scheduler started (every %ds)", settings.mail_poll_seconds)
    return scheduler


def stop_scheduler() -> None:
    """Shut down the scheduler if running."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
