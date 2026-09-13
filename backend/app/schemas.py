"""Pydantic schemas for API request/response bodies."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TaskStatus = Literal["todo", "in_progress", "done"]


IngestionMode = Literal["background", "manual"]


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
    """Optional overrides for a manual ingestion trigger."""

    limit: int | None = Field(default=None, ge=1, le=100)


class IngestResult(BaseModel):
    scraped: int
    classified: int
    created_tasks: int


class IngestionSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mode: IngestionMode
    mark_as_read: bool
    poll_hours: int
    batch_limit: int
    updated_at: datetime


class IngestionSettingsUpdate(BaseModel):
    mode: IngestionMode | None = None
    mark_as_read: bool | None = None
    poll_hours: int | None = Field(default=None, ge=1, le=168)
    batch_limit: int | None = Field(default=None, ge=1, le=100)
