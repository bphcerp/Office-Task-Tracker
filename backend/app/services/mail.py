"""IMAP mail scraping.

Boilerplate only. `scrape_emails` is a stub returning an empty list so the
pipeline runs end-to-end before the real IMAP integration is implemented.
Wire up `imapclient.IMAPClient` (or similar) against `settings.imap_*` here.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import IngestResult


@dataclass
class ScrapedEmail:
    """A raw email fetched from the mailbox."""

    message_id: str
    subject: str
    body: str
    sender: str


async def scrape_emails(limit: int = 25) -> list[ScrapedEmail]:
    """Fetch up to `limit` unread emails from the configured mailbox.

    TODO(integration): connect via IMAP, list unseen messages, fetch
    RFC822 parts, and map them onto `ScrapedEmail`.
    """
    await asyncio.sleep(0)
    return []


async def ingest_emails(session: AsyncSession, limit: int = 25) -> IngestResult:
    """Scrape -> classify -> persist a batch of emails as tasks.

    Classification and persistence are stubbed; see `app/services/agent.py`
    and `app/routers/tasks.py` for the intended flow.
    """
    emails = await scrape_emails(limit=limit)
    created = 0
    for email in emails:
        # Lazy import avoids the mail <-> agent circular import.
        from app.services.agent import classify_email

        result = await classify_email(email)
        if result is None:
            continue
        created += 1
    return IngestResult(scraped=len(emails), classified=len(emails), created_tasks=created)
