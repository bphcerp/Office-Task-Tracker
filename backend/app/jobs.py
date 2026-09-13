"""APScheduler background job that ingests emails on an interval."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db import SessionLocal
from app.services.ingestion_settings import get_ingestion_settings
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


def apply_scheduler_settings(mode: str, poll_hours: int) -> None:
    """Start, stop, or reschedule the background poller from runtime settings."""
    if mode != "background":
        stop_scheduler()
        return

    interval_seconds = poll_hours * 3600
    global _scheduler
    if _scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _poll,
            IntervalTrigger(seconds=interval_seconds),
            id="mail_poll",
            replace_existing=True,
        )
        scheduler.start()
        _scheduler = scheduler
        logger.info("Mail polling scheduler started (every %dh)", poll_hours)
        return

    _scheduler.reschedule_job("mail_poll", trigger=IntervalTrigger(seconds=interval_seconds))
    logger.info("Mail polling scheduler rescheduled (every %dh)", poll_hours)


def stop_scheduler() -> None:
    """Shut down the scheduler if running."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Mail polling scheduler stopped")
