"""ORM models for the task tracker.

The LLM agent classifies each scraped email into a Person, a Task, and a
Summary. A Person may be linked to many Tasks; each Task carries one Summary.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Person(Base):
    """An individual referenced by an email (sender / assignee)."""

    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tasks: Mapped[list[Task]] = relationship(back_populates="person")


class Task(Base):
    """A classified task extracted from an email."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="todo")
    source_email_id: Mapped[str | None] = mapped_column(String(320), unique=True)
    source_email_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    person_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    person: Mapped[Person | None] = relationship(back_populates="tasks")
    summary: Mapped[Summary | None] = relationship(
        back_populates="task", uselist=False, cascade="all, delete-orphan"
    )


class Summary(Base):
    """Concise summary of an email/task."""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), unique=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[Task] = relationship(back_populates="summary")
