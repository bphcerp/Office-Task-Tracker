"""Task endpoints: list tasks, fetch a single task, trigger manual ingestion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Task
from app.schemas import IngestRequest, IngestResult, TaskOut, TaskStatusUpdate
from app.services.mail import ingest_emails

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _get_task_or_404(task_id: int, session: AsyncSession) -> Task:
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
    return await _get_task_or_404(task_id, session)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    payload: TaskStatusUpdate,
    session: AsyncSession = Depends(get_session),
) -> Task:
    task = await _get_task_or_404(task_id, session)
    task.status = payload.status
    await session.commit()
    await session.refresh(task)
    return task


@router.post("/ingest", response_model=IngestResult)
async def ingest(
    payload: IngestRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> IngestResult:
    """Scrape emails and classify them into tasks (manual trigger)."""
    limit = None if payload is None else payload.limit
    return await ingest_emails(session, limit=limit)
