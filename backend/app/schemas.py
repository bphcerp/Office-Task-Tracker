"""Pydantic schemas for API request/response bodies."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

TaskStatus = Literal["todo", "in_progress", "done"]


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None = None


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: TaskStatus
    source_email_id: str | None = None
    source_email_received_at: datetime | None = None
    person: PersonOut | None = None
    summary: SummaryOut | None = None
    created_at: datetime
    updated_at: datetime


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class IngestRequest(BaseModel):
    """Optional filters for a manual ingestion trigger."""

    limit: int = 25


class IngestResult(BaseModel):
    scraped: int
    classified: int
    created_tasks: int
