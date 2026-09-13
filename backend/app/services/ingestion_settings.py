"""Load and persist runtime ingestion settings (singleton row)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import IngestionSettings
from app.schemas import IngestionSettingsUpdate

_SETTINGS_ID = 1


def _env_defaults() -> dict[str, object]:
    env = get_settings()
    return {
        "mode": env.mail_ingestion_mode,
        "mark_as_read": env.mail_mark_as_read,
        "poll_hours": env.mail_poll_hours,
        "batch_limit": env.mail_batch_limit,
    }


async def get_ingestion_settings(session: AsyncSession) -> IngestionSettings:
    """Return the singleton settings row, creating it from env defaults if missing."""
    row = (
        await session.execute(
            select(IngestionSettings).where(IngestionSettings.id == _SETTINGS_ID)
        )
    ).scalar_one_or_none()
    if row is not None:
        return row

    row = IngestionSettings(id=_SETTINGS_ID, **_env_defaults())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_ingestion_settings(
    session: AsyncSession, payload: IngestionSettingsUpdate
) -> IngestionSettings:
    row = await get_ingestion_settings(session)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return row
