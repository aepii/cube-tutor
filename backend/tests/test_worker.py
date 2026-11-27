"""#55 (24b): the worker (`process_one`, `LockRenewer`, `run`) and the dead-letter
drain, against `InMemoryJobQueue` and a FakeClock.

AC1–AC6 are marked below. The queue never sleeps; the only real waiting is
bounded `Event.wait(timeout)` calls for the threaded tests (AC5, AC6, `run`).
"""

import threading
import time
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlmodel import Session

from app.core.db import engine
from app.jobs.deps import get_job_queue
from app.jobs.drain import drain_dead_letters
from app.jobs.errors import (
    JOB_NOT_FOUND,
    PERMANENT_ERROR,
    UNKNOWN_JOB_TYPE,
    PermanentJobError,
    TransientJobError,
)
from app.jobs.handlers import HANDLERS
from app.jobs.memory import InMemoryJobQueue
from app.jobs.queue import MAX_DELIVERY_COUNT_EXCEEDED, JobMessage
from app.jobs.worker import WorkerConfig, process_one, run
from app.main import app
from app.models import Job, JobStatus, User
from app.models.job import utcnow
from tests.helpers import FakeClock

LOCK = 30.0
MAX_DELIVERIES = 3
WAIT = 5.0  # real seconds a threaded test waits before it calls it a failure


class SpyQueue(InMemoryJobQueue):
    """InMemoryJobQueue that records sends and renewals."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sent: list[JobMessage] = []
        self.renewals = 0
        self.renewed = threading.Event()

    def send(self, message: JobMessage) -> None:
        super().send(message)
        self.sent.append(message)

    def renew_lock(self, msg) -> None:
        super().renew_lock(msg)
        self.renewals += 1
        self.renewed.set()


class SpyHandler:
    """Records each payload; returns the echo result, or raises `errors[i]`."""

    def __init__(self, *errors: Exception | None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._errors = list(errors)

    def __call__(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(payload)
        if self._errors:
            error = self._errors.pop(0)
            if error is not None:
                raise error
        return {"message": payload["message"]}


def sessions() -> Session:
    return Session(engine)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def queue(clock) -> SpyQueue:
    return SpyQueue(lock_duration=LOCK, max_delivery_count=MAX_DELIVERIES, clock=clock)


@pytest.fixture
def config(clock) -> WorkerConfig:
    return WorkerConfig(
        clock=clock,
        max_wait=0,
        renew_before=15.0,
        renew_poll=0.005,
        idle_wait=0.01,
        housekeeping_every=3600.0,  # on the fake clock: once, at start
        stale_after=timedelta(minutes=5),
    )


@pytest.fixture
def user_id(session) -> int:
    user = User(username="alice", email="alice@example.com", hashed_password="x")
    session.add(user)
    session.commit()
    return user.id


def add_job(
    user_id: int,
    *,
    type: str = "diagnostic.echo",
    payload: dict[str, Any] | None = None,
    status: str = JobStatus.PENDING,
    attempts: int = 0,
    error: str | None = None,
    age: timedelta = timedelta(0),
) -> UUID:
    """Insert a job row directly (no message). `age` backdates updated_at."""
    stamp = utcnow() - age
    job = Job(
        type=type,
        payload=payload if payload is not None else {"message": "hi"},
        status=status,
        attempts=attempts,
        error=error,
        user_id=user_id,
        created_at=stamp,
        updated_at=stamp,
    )
    with sessions() as s:
        s.add(job)
        s.commit()
        return job.id


def enqueue(queue, user_id: int, **kwargs) -> UUID:
    """A job row plus its message on the queue."""
    job_id = add_job(user_id, **kwargs)
    queue.send(JobMessage(job_id=job_id, type=kwargs.get("type", "diagnostic.echo")))
    return job_id


def dead_letter(queue, job_id: UUID, reason: str) -> None:
    """Put a message for `job_id` straight into the dead-letter queue."""
    queue.send(JobMessage(job_id=job_id, type="diagnostic.echo"))
    queue.dead_letter(queue.receive(), reason)


def load(job_id: UUID) -> Job:
    with sessions() as s:
        return s.get(Job, job_id)


def assert_queues_empty(queue) -> None:
    assert queue.receive() is None, "a message is still on the main queue"
    assert queue.receive_dead_lettered() is None, "a message is still dead-lettered"


def start_run(queue, handlers, config) -> tuple[threading.Thread, threading.Event]:
    stop = threading.Event()
    thread = threading.Thread(
        target=run, args=(queue, sessions, handlers, stop, config), daemon=True
    )
    thread.start()
    return thread, stop


def wait_for(condition, timeout: float = WAIT) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        threading.Event().wait(0.01)
    return False


# --- process_one basics ----------------------------------------------------


def test_process_one_on_an_empty_queue_returns_false(queue, config):
    assert process_one(queue, sessions, HANDLERS, config) is False


# --- AC1 -------------------------------------------------------------------


def test_echo_job_posted_through_the_api_ends_done(client, auth_headers, queue, config):
    app.dependency_overrides[get_job_queue] = lambda: queue
    try:
        resp = client.post(
            "/v1/jobs/",
            json={"type": "diagnostic.echo", "payload": {"message": "hi"}},
            headers=auth_headers,
        )
    finally:
        app.dependency_overrides.pop(get_job_queue, None)
    assert resp.status_code == 202, resp.text
    job_id = resp.json()["id"]

    assert process_one(queue, sessions, HANDLERS, config) is True

    body = client.get(f"/v1/jobs/{job_id}", headers=auth_headers).json()
    assert body["status"] == "done"
    assert body["result"] == {"message": "hi"}
    assert body["attempts"] == 1
    assert body["error"] is None
    assert body["finished_at"] is not None
    assert_queues_empty(queue)  # completed: not redelivered, not dead-lettered


# --- AC2 -------------------------------------------------------------------


def test_permanent_failure_is_dead_lettered_after_one_attempt(queue, config, user_id):
    job_id = enqueue(queue, user_id, payload={"message": "hi", "fail": "permanent"})

    assert process_one(queue, sessions, HANDLERS, config) is True

    job = load(job_id)
    assert job.status == "failed"
    assert job.attempts == 1
    assert job.error
    assert job.finished_at is not None
    assert queue.receive() is None  # no retry
    dlq = queue.receive_dead_lettered()
    assert dlq.message.job_id == job_id
    assert dlq.dead_letter_reason == PERMANENT_ERROR


def test_permanent_failure_stores_the_handlers_message(queue, config, user_id):
    job_id = enqueue(queue, user_id)
    handler = SpyHandler(PermanentJobError("bad input"))

    process_one(queue, sessions, {"diagnostic.echo": handler}, config)

    assert "bad input" in load(job_id).error


def test_drain_keeps_the_error_of_a_permanent_failure(queue, config, user_id):
    # D1: the drain doesn't overwrite a job that's already failed.
    job_id = enqueue(queue, user_id)
    handler = SpyHandler(PermanentJobError("bad input"))
    process_one(queue, sessions, {"diagnostic.echo": handler}, config)

    assert drain_dead_letters(queue, sessions) == 1

    job = load(job_id)
    assert job.status == "failed"
    assert "bad input" in job.error
    assert_queues_empty(queue)


# --- AC3 -------------------------------------------------------------------


def test_transient_failure_retries_then_drain_marks_failed(queue, config, user_id):
    job_id = enqueue(queue, user_id, payload={"message": "hi", "fail": "transient"})

    for attempt in range(1, MAX_DELIVERIES + 1):
        assert process_one(queue, sessions, HANDLERS, config) is True
        job = load(job_id)
        assert job.attempts == attempt
        assert job.status == "pending"
        assert job.error

    # The last abandon sent it to the DLQ: nothing left to receive.
    assert process_one(queue, sessions, HANDLERS, config) is False
    assert load(job_id).status == "pending"  # until the drain runs

    assert drain_dead_letters(queue, sessions) == 1

    job = load(job_id)
    assert job.status == "failed"
    assert job.error.startswith(MAX_DELIVERY_COUNT_EXCEEDED)
    assert job.attempts == MAX_DELIVERIES
    assert job.finished_at is not None
    assert_queues_empty(queue)


def test_unexpected_exception_counts_as_transient(queue, config, user_id):
    job_id = enqueue(queue, user_id)
    handler = SpyHandler(ValueError("boom"))

    assert process_one(queue, sessions, {"diagnostic.echo": handler}, config)

    job = load(job_id)
    assert job.status == "pending"
    assert "boom" in job.error
    assert queue.receive_dead_lettered() is None
    redelivery = queue.receive()
    assert redelivery.message.job_id == job_id
    assert redelivery.delivery_count == 2


def test_success_after_a_transient_failure_clears_the_error(queue, config, user_id):
    job_id = enqueue(queue, user_id)
    handler = SpyHandler(TransientJobError("busy"), None)
    handlers = {"diagnostic.echo": handler}

    process_one(queue, sessions, handlers, config)
    process_one(queue, sessions, handlers, config)

    job = load(job_id)
    assert job.status == "done"
    assert job.attempts == 2
    assert job.error is None
    assert job.result == {"message": "hi"}


# --- AC4 -------------------------------------------------------------------


def test_redelivered_done_job_is_completed_without_running_the_handler(
    queue, config, user_id
):
    job_id = enqueue(queue, user_id)
    handler = SpyHandler()
    handlers = {"diagnostic.echo": handler}
    process_one(queue, sessions, handlers, config)

    queue.send(JobMessage(job_id=job_id, type="diagnostic.echo"))  # duplicate
    assert process_one(queue, sessions, handlers, config) is True

    assert len(handler.calls) == 1
    job = load(job_id)
    assert job.status == "done"
    assert job.attempts == 1
    assert_queues_empty(queue)


def test_redelivered_failed_job_is_completed_without_running_the_handler(
    queue, config, user_id
):
    job_id = enqueue(
        queue, user_id, status=JobStatus.FAILED, attempts=1, error="bad input"
    )
    handler = SpyHandler()

    assert process_one(queue, sessions, {"diagnostic.echo": handler}, config)

    assert handler.calls == []
    job = load(job_id)
    assert job.status == "failed"
    assert job.error == "bad input"
    assert_queues_empty(queue)


def test_redelivered_running_job_runs_again(queue, config, user_id):
    # A worker crashed mid-job: the row says running, the lock expired.
    job_id = enqueue(queue, user_id, status=JobStatus.RUNNING, attempts=1)
    handler = SpyHandler()

    process_one(queue, sessions, {"diagnostic.echo": handler}, config)

    assert len(handler.calls) == 1
    job = load(job_id)
    assert job.status == "done"
    assert job.attempts == 2
    assert_queues_empty(queue)


# --- missing job / unknown type -------------------------------------------


def test_missing_job_is_dead_lettered(queue, config):
    ghost = uuid4()
    queue.send(JobMessage(job_id=ghost, type="diagnostic.echo"))

    assert process_one(queue, sessions, HANDLERS, config) is True

    assert queue.receive() is None
    dlq = queue.receive_dead_lettered()
    assert dlq.message.job_id == ghost
    assert dlq.dead_letter_reason == JOB_NOT_FOUND


def test_unknown_type_fails_and_is_dead_lettered(queue, config, user_id):
    job_id = enqueue(queue, user_id, type="diagnostic.nope")

    assert process_one(queue, sessions, HANDLERS, config) is True

    job = load(job_id)
    assert job.status == "failed"
    assert "diagnostic.nope" in job.error
    assert job.attempts == 0  # nothing was attempted
    assert job.finished_at is not None
    assert queue.receive() is None
    assert queue.receive_dead_lettered().dead_letter_reason == UNKNOWN_JOB_TYPE


# --- AC5 -------------------------------------------------------------------


def test_long_handler_keeps_its_lock(queue, clock, config, user_id):
    job_id = enqueue(queue, user_id)
    missed: list[int] = []

    def slow(payload):
        # 3 × 20 s = 60 s of "work" against a 30 s lock. renew_before is 15 s,
        # so each step leaves 10 s and the renewer must renew before the next.
        for step in range(3):
            queue.renewed.clear()
            clock.advance(20)
            if not queue.renewed.wait(WAIT):
                missed.append(step)
        return {"message": payload["message"]}

    assert process_one(queue, sessions, {"diagnostic.echo": slow}, config)

    assert missed == [], f"no renewal after steps {missed}"
    assert queue.renewals >= 3
    job = load(job_id)
    assert job.status == "done"
    assert job.attempts == 1
    assert_queues_empty(queue)  # completed under a live lock: not redelivered


def test_lost_lock_is_logged_not_raised_and_redelivery_is_a_no_op(
    queue, clock, config, user_id
):
    # A renewer that never gets to run (huge poll), and a handler that outlives
    # the lock: the settle hits LockLostError after the row is already done.
    lazy = WorkerConfig(
        clock=clock, max_wait=0, renew_before=15.0, renew_poll=60.0, idle_wait=0.01
    )
    job_id = enqueue(queue, user_id)
    calls: list[dict] = []

    def outlives_lock(payload):
        calls.append(payload)
        clock.advance(LOCK + 1)
        return {"message": payload["message"]}

    handlers = {"diagnostic.echo": outlives_lock}
    started = time.monotonic()
    assert process_one(queue, sessions, handlers, lazy) is True  # no raise
    # The renewer stopped at once on exit; it didn't wait out its 60 s poll.
    assert time.monotonic() - started < WAIT

    assert load(job_id).status == "done"

    # The message came back (its lock expired); the redelivery just completes it.
    assert process_one(queue, sessions, handlers, lazy) is True
    assert len(calls) == 1
    job = load(job_id)
    assert job.status == "done"
    assert job.attempts == 1
    assert_queues_empty(queue)


# --- AC6 -------------------------------------------------------------------


def test_stop_during_a_handler_finishes_that_message_and_exits(queue, config, user_id):
    first = enqueue(queue, user_id, payload={"message": "first"})
    second = enqueue(queue, user_id, payload={"message": "second"})
    started, release = threading.Event(), threading.Event()
    calls: list[dict] = []

    def blocking(payload):
        calls.append(payload)
        started.set()
        release.wait(WAIT)
        return {"message": payload["message"]}

    thread, stop = start_run(queue, {"diagnostic.echo": blocking}, config)
    assert started.wait(WAIT), "run never started the first job"
    stop.set()
    release.set()
    thread.join(WAIT)

    assert not thread.is_alive(), "run didn't return after stop"
    assert calls == [{"message": "first"}]
    assert load(first).status == "done"
    pending = load(second)
    assert pending.status == "pending"
    assert pending.attempts == 0
    untouched = queue.receive()
    assert untouched.message.job_id == second
    assert untouched.delivery_count == 1  # never received by run
    assert queue.receive() is None  # and the first was completed


def test_run_exits_promptly_when_idle(queue, config):
    thread, stop = start_run(queue, HANDLERS, config)
    threading.Event().wait(0.05)  # let it loop on the empty queue a few times
    stop.set()
    thread.join(WAIT)
    assert not thread.is_alive()


# --- run: housekeeping -----------------------------------------------------


def test_run_drains_then_sweeps(queue, config, user_id):
    old = timedelta(hours=1)
    # Lost send: pending, stale, no message → the sweeper re-sends it.
    lost = add_job(user_id, payload={"message": "lost"}, age=old)
    # Ran out of retries: pending, stale, its message dead-lettered → the
    # drain must fail it before the sweeper sees it, so it's never re-sent.
    exhausted = add_job(user_id, payload={"message": "exhausted"}, age=old)
    dead_letter(queue, exhausted, MAX_DELIVERY_COUNT_EXCEEDED)
    queue.sent.clear()
    handler = SpyHandler()

    thread, stop = start_run(queue, {"diagnostic.echo": handler}, config)
    try:
        assert wait_for(lambda: load(lost).status == "done"), "lost job not run"
    finally:
        stop.set()
        thread.join(WAIT)

    assert not thread.is_alive()
    assert handler.calls == [{"message": "lost"}]
    job = load(exhausted)
    assert job.status == "failed"
    assert job.error.startswith(MAX_DELIVERY_COUNT_EXCEEDED)
    assert [m.job_id for m in queue.sent] == [lost]  # drain ran before the sweep
    assert_queues_empty(queue)


# --- drain -----------------------------------------------------------------


def test_drain_on_an_empty_dead_letter_queue_returns_zero(queue):
    assert drain_dead_letters(queue, sessions) == 0


def test_drain_marks_failed_with_the_reason(queue, user_id):
    job_id = add_job(user_id, attempts=2, error="busy")
    dead_letter(queue, job_id, "SomeReason")

    assert drain_dead_letters(queue, sessions) == 1

    job = load(job_id)
    assert job.status == "failed"
    assert job.error.startswith("SomeReason")
    assert job.finished_at is not None
    assert_queues_empty(queue)


def test_drain_leaves_done_jobs_alone(queue, user_id):
    job_id = add_job(user_id, status=JobStatus.DONE, attempts=1)
    dead_letter(queue, job_id, MAX_DELIVERY_COUNT_EXCEEDED)

    assert drain_dead_letters(queue, sessions) == 1

    job = load(job_id)
    assert job.status == "done"
    assert job.error is None
    assert_queues_empty(queue)


def test_drain_completes_messages_for_missing_jobs(queue):
    dead_letter(queue, uuid4(), JOB_NOT_FOUND)

    assert drain_dead_letters(queue, sessions) == 1

    assert_queues_empty(queue)
