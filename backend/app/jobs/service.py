"""Job producer side: enqueue, the stale-pending sweeper, the owner lookup.

Enqueue commits the row, *then* sends. If the send fails the job stays
`pending` and the request still succeeds; `resend_stale_pending` closes that gap
(ROADMAP §3.10, ADR 0008: a transactional outbox would be the fully correct fix).
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.jobs.queue import JobMessage, JobQueue
from app.models import Job, JobStatus
from app.models.job import utcnow

logger = logging.getLogger(__name__)


def enqueue(
    session: Session,
    queue: JobQueue,
    *,
    user_id: int,
    type: str,
    payload: dict[str, Any],
) -> Job:
    """Insert a `pending` job (attempts 0), commit, then send `{job_id, type}`.

    A send error is logged, not raised: the job stays `pending` for the sweeper.
    Returns the committed job.
    """
    job = Job(
        type=type,
        payload=payload,
        user_id=user_id,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    job_message = JobMessage(job_id=job.id, type=job.type)
    try:
        queue.send(job_message)
    except Exception:
        logger.exception("send failed for %s", job.id)

    return job


def resend_stale_pending(
    session: Session,
    queue: JobQueue,
    older_than: timedelta,
    now: datetime | None = None,
) -> int:
    """Re-send every `pending` job whose `updated_at` is strictly older than
    `now - older_than`, and touch its `updated_at` so the next sweep waits again.

    `now` is naive UTC (defaults to the current time). Other statuses are never
    re-sent. One failed send doesn't stop the rest. Returns how many were sent.
    """
    if now is None:
        now = utcnow()

    statement = select(Job).where(
        Job.updated_at < now - older_than, Job.status == JobStatus.PENDING
    )
    stale_pending = session.exec(statement).all()

    resends = 0
    for job in stale_pending:
        job_message = JobMessage(job_id=job.id, type=job.type)
        try:
            queue.send(job_message)
            job.updated_at = now
            resends += 1
        except Exception:
            logger.exception("resend failed for %s", job.id)

    session.commit()

    return resends


def get_job_for_user(session: Session, job_id: UUID, user_id: int) -> Job | None:
    """The job if it exists *and* belongs to `user_id`, else None.

    One query with both conditions, so "not yours" and "doesn't exist" look the
    same to the caller (the route turns both into 404).
    """
    statement = select(Job).where(Job.id == job_id, Job.user_id == user_id)
    job = session.exec(statement).first()

    return job
