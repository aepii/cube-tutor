"""FastAPI dependency for the job queue.

One process-wide `InMemoryJobQueue` for now; 24c switches to `ServiceBusJobQueue`
when the connection settings are present. Tests replace it with
`app.dependency_overrides[get_job_queue]`.

Until 24c nothing consumes this queue, so a job posted to a running API stays
`pending` (expected; see #54).
"""

from functools import cache

from app.jobs.memory import InMemoryJobQueue
from app.jobs.queue import JobQueue


@cache  # built on first use, not at import (the class may raise until it's written)
def _process_queue() -> InMemoryJobQueue:
    return InMemoryJobQueue()


def get_job_queue() -> JobQueue:
    return _process_queue()
