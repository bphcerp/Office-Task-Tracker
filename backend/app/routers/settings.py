"""Runtime settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.jobs import apply_scheduler_settings
from app.schemas import IngestionSettingsOut, IngestionSettingsUpdate
from app.services.ingestion_settings import get_ingestion_settings, update_ingestion_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/ingestion", response_model=IngestionSettingsOut)
async def read_ingestion_settings(
    session: AsyncSession = Depends(get_session),
) -> IngestionSettingsOut:
    return await get_ingestion_settings(session)


@router.patch("/ingestion", response_model=IngestionSettingsOut)
async def patch_ingestion_settings(
    payload: IngestionSettingsUpdate,
    session: AsyncSession = Depends(get_session),
) -> IngestionSettingsOut:
    row = await update_ingestion_settings(session, payload)
    apply_scheduler_settings(row.mode, row.poll_hours)
    return row
