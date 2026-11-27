"""Dead-letter drain: turns dead-lettered messages into `failed` jobs.

A message lands in the dead-letter queue when the worker dead-letters it
(permanent error, unknown type, missing job) or when the queue gives up after
`max_delivery_count` deliveries (`MaxDeliveryCountExceeded`). In that last case
the job is still `pending`; the drain is what marks it `failed`.
"""

import logging
from collections.abc import Callable

from sqlmodel import Session

from app.jobs.queue import JobQueue, LockLostError
from app.models import Job, JobStatus
from app.models.job import utcnow

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]


def drain_dead_letters(queue: JobQueue, session_factory: SessionFactory) -> int:
    """Settle every message currently in the dead-letter queue.

    For each one (`queue.receive_dead_lettered()` until it returns None):
    - if the job exists and isn't already `done` or `failed`: set it `failed`,
      `error` = the message's `dead_letter_reason` (it may append the last
      error), `finished_at` = now; commit.
    - then `complete` the dead-letter message, also when the job is missing or
      already finished (otherwise it would come back when its lock expires).

    Returns how many dead-letter messages were completed.
    """
    drained = 0
    while (msg := queue.receive_dead_lettered()) is not None:
        with session_factory() as session:
            job = session.get(Job, msg.message.job_id)
            if job is not None and job.status not in (
                JobStatus.DONE,
                JobStatus.FAILED,
            ):
                reason = msg.dead_letter_reason or "DeadLettered"
                # Keep the last transient error: it says *why* it ran out of tries.
                job.error = (
                    f"{reason} (last error: {job.error})" if job.error else reason
                )
                job.status = JobStatus.FAILED
                job.finished_at = utcnow()
                session.commit()
                logger.warning("job %s failed: %s", job.id, job.error)

        try:
            queue.complete(msg)
        except LockLostError:
            # The lock ran out mid-drain; it's back in the DLQ for the next pass,
            # which finds the row already failed and just completes it.
            logger.warning("lock lost draining job %s", msg.message.job_id)
            continue
        drained += 1

    return drained
