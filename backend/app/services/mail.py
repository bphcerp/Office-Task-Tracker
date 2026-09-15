"""IMAP mail scraping and ingestion pipeline."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime

import imapclient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Person, Summary, Task
from app.schemas import IngestResult
from app.services.ingestion_settings import get_ingestion_settings

logger = logging.getLogger(__name__)


@dataclass
class ScrapedEmail:
    """A raw email fetched from the mailbox."""

    message_id: str
    subject: str
    body: str
    sender: str
    received_at: datetime | None = None


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except (UnicodeError, ValueError):
        return value


def _extract_body(message) -> str:
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace").strip()
        for part in message.walk():
            if part.get_content_type() == "text/html" and not part.get_filename():
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace").strip()
        return ""

    payload = message.get_payload(decode=True)
    if not payload:
        return ""
    charset = message.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace").strip()


def _imap_host(host: str) -> str:
    return host.removeprefix("imaps://").removeprefix("imap://").rstrip("/")


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_received_at(
    message,
    *,
    internal_date: datetime | None = None,
    envelope_date: datetime | None = None,
) -> datetime | None:
    # Prefer the sender's Date header; fall back to IMAP server timestamps.
    date_header = message.get("Date")
    if date_header:
        try:
            return _as_utc(parsedate_to_datetime(date_header))
        except (TypeError, ValueError):
            pass
    if internal_date:
        return _as_utc(internal_date)
    if envelope_date:
        return _as_utc(envelope_date)
    return None


def _scrape_emails_sync(limit: int, mark_as_read: bool) -> list[ScrapedEmail]:
    settings = get_settings()
    if not settings.imap_host or not settings.imap_user or not settings.imap_password:
        logger.warning("IMAP is not configured; skipping mail scrape")
        return []

    host = _imap_host(settings.imap_host)
    emails: list[ScrapedEmail] = []
    fetch_parts = (
        ["RFC822", "ENVELOPE", "INTERNALDATE"]
        if mark_as_read
        else ["BODY.PEEK[]", "ENVELOPE", "INTERNALDATE"]
    )
    body_key = b"RFC822" if mark_as_read else b"BODY[]"

    with imapclient.IMAPClient(host, port=settings.imap_port, ssl=True) as client:
        client.login(settings.imap_user, settings.imap_password)
        client.select_folder(settings.imap_folder)
        uids = client.search(["UNSEEN"])
        if not uids:
            return []

        for uid in sorted(uids)[-limit:]:
            fetched = client.fetch([uid], fetch_parts)
            data = fetched[uid]
            raw = data[body_key]
            message = message_from_bytes(raw)
            envelope = data.get(b"ENVELOPE")

            message_id = message.get("Message-ID") or f"uid:{uid}"
            subject = _decode_header_value(message.get("Subject"))
            sender = _decode_header_value(message.get("From"))
            body = _extract_body(message)
            received_at = _parse_received_at(
                message,
                internal_date=data.get(b"INTERNALDATE"),
                envelope_date=envelope.date if envelope else None,
            )

            emails.append(
                ScrapedEmail(
                    message_id=message_id,
                    subject=subject,
                    body=body,
                    sender=sender,
                    received_at=received_at,
                )
            )

    return emails


async def scrape_emails(limit: int = 25, mark_as_read: bool = True) -> list[ScrapedEmail]:
    """Fetch up to `limit` unread emails from the configured mailbox."""
    try:
        return await asyncio.to_thread(_scrape_emails_sync, limit, mark_as_read)
    except imapclient.exceptions.IMAPClientError:
        logger.exception("IMAP scrape failed")
        return []


async def _get_or_create_person(
    session: AsyncSession, name: str, email: str | None
) -> Person | None:
    if email:
        result = await session.execute(select(Person).where(Person.email == email))
        person = result.scalar_one_or_none()
        if person:
            return person
        person = Person(name=name, email=email)
        session.add(person)
        await session.flush()
        return person

    if name:
        person = Person(name=name)
        session.add(person)
        await session.flush()
        return person

    return None


async def ingest_emails(session: AsyncSession, limit: int | None = None) -> IngestResult:
    """Scrape -> classify -> persist a batch of emails as tasks."""
    settings = await get_ingestion_settings(session)
    effective_limit = limit if limit is not None else settings.batch_limit
    emails = await scrape_emails(
        limit=effective_limit,
        mark_as_read=settings.mark_as_read,
    )
    classified = 0
    created = 0

    for email in emails:
        existing = await session.execute(
            select(Task).where(Task.source_email_id == email.message_id)
        )
        if existing.scalar_one_or_none():
            continue

        # Lazy import avoids the mail <-> agent circular import.
        from app.services.agent import classify_email

        result = await classify_email(email)
        if result is None:
            continue
        classified += 1

        person = await _get_or_create_person(
            session, result.person_name, result.person_email
        )
        task = Task(
            title=result.task_title,
            person_id=person.id if person else None,
            source_email_id=email.message_id,
            source_email_received_at=email.received_at,
        )
        session.add(task)
        await session.flush()
        session.add(Summary(task_id=task.id, body=result.summary))
        created += 1

    if created:
        await session.commit()

    return IngestResult(scraped=len(emails), classified=classified, created_tasks=created)
