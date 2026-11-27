"""The job worker: receive a message, run its handler, record the outcome.

Rules (ROADMAP §3.10, ADR 0008, docs/backend.md § Jobs):
- The job row is the source of truth. Every outcome is committed to the row
  **before** the message is settled, so a redelivery after a crash or a lost
  lock sees `done`/`failed` and is simply completed (idempotent).
- No DB transaction is held open while a handler runs.
- The message's lock is renewed while the handler runs (`LockRenewer`).

24c adds the `python -m app.worker` entry point, which wires SIGTERM to `stop`.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from types import TracebackType
from typing import Self

from sqlmodel import Session

from app.jobs import service
from app.jobs.drain import drain_dead_letters
from app.jobs.errors import (
    JOB_NOT_FOUND,
    PERMANENT_ERROR,
    UNKNOWN_JOB_TYPE,
    PermanentJobError,
)
from app.jobs.handlers import Handler
from app.jobs.queue import JobQueue, LockLostError, ReceivedMessage
from app.models import Job, JobStatus
from app.models.job import utcnow

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]


@dataclass(frozen=True)
class WorkerConfig:
    """Timing knobs for `process_one` and `run`. 24c fills it from settings."""

    # Monotonic seconds, on the same clock as the queue's `locked_until`.
    clock: Callable[[], float] = time.monotonic
    # How long `receive` may wait for a message (the in-memory queue ignores it).
    max_wait: float = 5.0
    # Renew the lock once it has this many seconds or fewer left...
    renew_before: float = 10.0
    # ...checking every `renew_poll` real seconds.
    renew_poll: float = 0.5
    # `run`: real seconds to wait after an empty receive.
    idle_wait: float = 1.0
    # `run`: seconds (on `clock`) between housekeeping passes (drain, then sweep).
    housekeeping_every: float = 60.0
    # `run`: the sweeper re-sends `pending` jobs not updated for this long.
    stale_after: timedelta = timedelta(minutes=5)


class LockRenewer:
    """Keeps a received message's lock alive while its handler runs.

    `with LockRenewer(queue, msg, config): handler(payload)`

    On enter, starts a daemon thread that every `config.renew_poll` real seconds
    checks `msg.locked_until - config.clock()` and calls `queue.renew_lock(msg)`
    when that is `<= config.renew_before`. On exit, stops the thread at once
    (not after the next poll) and joins it. A `LockLostError` from `renew_lock`
    is logged and ends the thread; it is never raised to the caller.
    """

    def __init__(
        self, queue: JobQueue, msg: ReceivedMessage, config: WorkerConfig
    ) -> None:
        self._queue = queue
        self._msg = msg
        self._config = config

        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="lock-renewer"
        )

    def __enter__(self) -> Self:
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._stop.set()
        self._thread.join()

    def _loop(self) -> None:
        while not self._stop.wait(self._config.renew_poll):
            if (
                self._msg.locked_until - self._config.clock()
                <= self._config.renew_before
            ):
                try:
                    self._queue.renew_lock(self._msg)
                except LockLostError:
                    logger.warning(
                        "lock lost for job %s; stopping renewal",
                        self._msg.message.job_id,
                    )
                    return
                except Exception:
                    logger.exception(
                        "unexpected error renewing lock for job %s",
                        self._msg.message.job_id,
                    )


def _describe(exc: BaseException) -> str:
    """What goes in `job.error`: the exception's type and message."""
    return f"{type(exc).__name__}: {exc}"


def _settle(action: Callable[..., None], msg: ReceivedMessage, *args: str) -> None:
    """Complete / abandon / dead-letter `msg`, logging a lost lock instead of
    raising it. The row is already committed, so the redelivery is a no-op."""
    try:
        action(msg, *args)
    except LockLostError:
        logger.warning(
            "lock lost before settling job %s; it will be redelivered",
            msg.message.job_id,
        )


def process_one(
    queue: JobQueue,
    session_factory: SessionFactory,
    handlers: dict[str, Handler],
    config: WorkerConfig = WorkerConfig(),  # frozen, so a shared default is safe
) -> bool:
    """Receive one message and handle it. Returns False if there was none.

    - Job missing → dead-letter (`JOB_NOT_FOUND`).
    - Job `done` or `failed` → complete (a duplicate; the handler doesn't run).
    - No handler for the type → job `failed` (error names the type),
      `finished_at`; dead-letter (`UNKNOWN_JOB_TYPE`). `attempts` is unchanged.
    - Otherwise: job `running`, `attempts += 1`, commit; run the handler inside
      `LockRenewer`, with no transaction open; then
      - success → `result`, `error = None`, `done`, `finished_at`; complete.
      - `PermanentJobError` → `error`, `failed`, `finished_at`; dead-letter
        (`PERMANENT_ERROR`).
      - `TransientJobError` or any other exception → `error`, `pending`; abandon.

    Always commit the row first, then settle. A `LockLostError` while settling is
    logged, not raised: the redelivery will find the row already finished.
    """
    received_message = queue.receive(config.max_wait)

    if received_message is None:
        return False

    with session_factory() as session:
        job = session.get(Job, received_message.message.job_id)

        if job is None:
            _settle(queue.dead_letter, received_message, JOB_NOT_FOUND)
            return True

        if job.status in (JobStatus.DONE, JobStatus.FAILED):
            _settle(queue.complete, received_message)
            return True

        handler = handlers.get(job.type)
        if handler is None:
            job.status = JobStatus.FAILED
            job.error = f"no handler for job type {job.type!r}"
            job.finished_at = utcnow()
            session.commit()
            _settle(queue.dead_letter, received_message, UNKNOWN_JOB_TYPE)
            return True

        job.status = JobStatus.RUNNING
        job.attempts += 1
        session.commit()

        payload = dict(job.payload)
        try:
            with LockRenewer(queue, received_message, config):
                result = handler(payload)
        except PermanentJobError as exc:
            job.status = JobStatus.FAILED
            job.error = _describe(exc)
            job.finished_at = utcnow()
            session.commit()
            _settle(queue.dead_letter, received_message, PERMANENT_ERROR)
        except Exception as exc:
            # Transient, or a bug in the handler: retried, then dead-lettered.
            logger.exception("job %s failed; it will be retried", job.id)
            job.status = JobStatus.PENDING
            job.error = _describe(exc)
            session.commit()
            _settle(queue.abandon, received_message)
        else:
            job.result = result
            job.error = None
            job.status = JobStatus.DONE
            job.finished_at = utcnow()
            session.commit()
            _settle(queue.complete, received_message)

        return True


def run(
    queue: JobQueue,
    session_factory: SessionFactory,
    handlers: dict[str, Handler],
    stop: threading.Event,
    config: WorkerConfig = WorkerConfig(),
) -> None:
    """Process messages until `stop` is set.

    - Housekeeping is due at start and then every `config.housekeeping_every`
      seconds on `config.clock`: `drain_dead_letters` first, then
      `service.resend_stale_pending(session, queue, config.stale_after)`.
    - Then `process_one`; if it found nothing, `stop.wait(config.idle_wait)`.
    - `stop` is checked between messages only: the current message always
      finishes and is settled before `run` returns.
    - One failing iteration (e.g. the DB is down) is logged; the loop goes on.
    """
    next_housekeeping = config.clock()  # due at once
    while not stop.is_set():
        try:
            if config.clock() >= next_housekeeping:
                # Scheduled before it runs, so a failing pass (DB down) waits a
                # full interval instead of retrying on every iteration.
                next_housekeeping = config.clock() + config.housekeeping_every
                _housekeeping(queue, session_factory, config)
            if not process_one(queue, session_factory, handlers, config):
                stop.wait(config.idle_wait)
        except Exception:
            logger.exception("worker iteration failed; continuing")
            stop.wait(config.idle_wait)


def _housekeeping(
    queue: JobQueue, session_factory: SessionFactory, config: WorkerConfig
) -> None:
    """Drain, then sweep. In this order: a job whose last transient attempt was
    dead-lettered is still `pending` until the drain fails it, and sweeping
    first would re-send it and run it again."""
    drained = drain_dead_letters(queue, session_factory)
    with session_factory() as session:
        resent = service.resend_stale_pending(session, queue, config.stale_after)
    if drained or resent:
        logger.info("housekeeping: drained %d, re-sent %d", drained, resent)
