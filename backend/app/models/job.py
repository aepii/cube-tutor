from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


# Naive UTC, like every other timestamp column (sqlmodel <0.0.32 maps datetime
# to a column without a time zone; see the pin in pyproject.toml).
def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


# pending → running → done | failed. A transient failure in the worker (24b)
# puts the job back to pending for the next delivery.
class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


# One background job. The row is the source of truth for its status; the queue
# only carries {job_id, type} (ROADMAP §3.10, ADR 0008).
class Job(SQLModel, table=True):
    __table_args__ = (
        # VARCHAR + CHECK instead of a Postgres ENUM: adding a status later is
        # one ALTER of the constraint, not an enum migration.
        CheckConstraint(
            "status IN ('pending', 'running', 'done', 'failed')", name="ck_job_status"
        ),
        # The sweeper's query: pending jobs not touched for a while.
        Index("ix_job_status_updated_at", "status", "updated_at"),
    )

    # Set by the app, so the id exists before the insert and is the same in the
    # row, the queue message and the logs.
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: str = Field(max_length=100)
    status: str = Field(default=JobStatus.PENDING, max_length=20)

    payload: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    result: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    error: str | None = None
    attempts: int = 0

    user_id: int = Field(foreign_key="user.id", index=True)

    created_at: datetime = Field(default_factory=utcnow)
    # Bumped on every ORM update; the sweeper keys on it.
    updated_at: datetime = Field(
        default_factory=utcnow, sa_column_kwargs={"onupdate": utcnow}
    )
    finished_at: datetime | None = None
