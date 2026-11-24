from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Payload of `diagnostic.echo`: the worker (24b) echoes `message` back, or fails
# on purpose with `fail` to exercise retries and dead-lettering.
class EchoPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., max_length=1000)
    fail: Literal["transient", "permanent"] | None = None


# Request body for POST /v1/jobs. This schema *is* the allowlist of types a
# client may submit: anything else is a 422 before any DB work. A second type
# turns this into a discriminated union on `type`; worker-only types stay out.
class JobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["diagnostic.echo"]
    payload: EchoPayload


# 202 response to POST /v1/jobs
class JobAccepted(BaseModel):
    id: UUID
    status: str


# Response to GET /v1/jobs/{id}
class JobRead(BaseModel):
    id: UUID
    type: str
    status: str
    result: dict[str, Any] | None
    error: str | None
    attempts: int
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None
