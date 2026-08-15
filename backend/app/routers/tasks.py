"""Task endpoints: list tasks, fetch a single task, trigger manual ingestion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Task
from app.schemas import IngestRequest, IngestResult, TaskOut
from app.services.mail import ingest_emails

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(session: AsyncSession = Depends(get_session)) -> list[Task]:
    stmt = (
        select(Task)
        .options(
            selectinload(Task.person),
            selectinload(Task.summary),
        )
        .order_by(Task.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)) -> Task:
    stmt = (
        select(Task)
        .where(Task.id == task_id)
        .options(
            selectinload(Task.person),
            selectinload(Task.summary),
        )
    )
    task = (await session.execute(stmt)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/ingest", response_model=IngestResult)
async def ingest(
    payload: IngestRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> IngestResult:
    """Scrape emails and classify them into tasks (manual trigger)."""
    limit = payload.limit if payload else 25
    result = await ingest_emails(session, limit=limit)
    return result
