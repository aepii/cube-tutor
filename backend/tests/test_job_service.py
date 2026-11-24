"""AC4 (service side): enqueue's commit-then-send and the stale-pending sweeper."""

from datetime import timedelta

import pytest

from app.jobs import service
from app.jobs.queue import JobMessage
from app.models import Job, JobStatus, User
from app.models.job import utcnow
from tests.helpers import RecordingQueue

THRESHOLD = timedelta(minutes=5)


@pytest.fixture
def user_id(session) -> int:
    user = User(username="alice", email="alice@example.com", hashed_password="x")
    session.add(user)
    session.commit()
    return user.id


def _job(session, user_id, *, status=JobStatus.PENDING, age: timedelta, now) -> Job:
    """A job whose updated_at is `age` before `now`."""
    stamp = now - age
    job = Job(
        type="diagnostic.echo",
        payload={"message": "hi"},
        status=status,
        user_id=user_id,
        created_at=stamp,
        updated_at=stamp,
    )
    session.add(job)
    session.commit()
    return job


# --- enqueue ---------------------------------------------------------------


def test_enqueue_commits_a_pending_row_then_sends(session, user_id):
    queue = RecordingQueue()
    job = service.enqueue(
        session,
        queue,
        user_id=user_id,
        type="diagnostic.echo",
        payload={"message": "hi"},
    )
    session.expire_all()
    row = session.get(Job, job.id)
    assert row.status == JobStatus.PENDING
    assert row.attempts == 0
    assert row.user_id == user_id
    assert row.payload == {"message": "hi"}
    assert queue.sent == [JobMessage(job_id=job.id, type="diagnostic.echo")]


def test_enqueue_keeps_the_job_when_send_fails(session, user_id):
    job = service.enqueue(
        session,
        RecordingQueue(fail=True),
        user_id=user_id,
        type="diagnostic.echo",
        payload={"message": "hi"},
    )
    session.expire_all()
    assert session.get(Job, job.id).status == JobStatus.PENDING


# --- resend_stale_pending --------------------------------------------------


def test_resends_only_pending_jobs_older_than_the_threshold(session, user_id):
    now = utcnow()
    stale = _job(session, user_id, age=THRESHOLD + timedelta(seconds=1), now=now)
    _job(session, user_id, age=THRESHOLD - timedelta(seconds=1), now=now)  # fresh
    _job(session, user_id, age=THRESHOLD, now=now)  # exactly at it: not older
    queue = RecordingQueue()

    sent = service.resend_stale_pending(session, queue, THRESHOLD, now=now)

    assert sent == 1
    assert queue.sent == [JobMessage(job_id=stale.id, type="diagnostic.echo")]


@pytest.mark.parametrize(
    "status", [JobStatus.RUNNING, JobStatus.DONE, JobStatus.FAILED]
)
def test_never_resends_non_pending_jobs(session, user_id, status):
    now = utcnow()
    _job(session, user_id, status=status, age=timedelta(days=1), now=now)
    queue = RecordingQueue()

    assert service.resend_stale_pending(session, queue, THRESHOLD, now=now) == 0
    assert queue.sent == []


def test_resend_touches_updated_at_so_the_next_sweep_skips_it(session, user_id):
    now = utcnow()
    job = _job(session, user_id, age=timedelta(hours=1), now=now)
    queue = RecordingQueue()

    assert service.resend_stale_pending(session, queue, THRESHOLD, now=now) == 1
    assert service.resend_stale_pending(session, queue, THRESHOLD, now=now) == 0

    session.expire_all()
    assert session.get(Job, job.id).updated_at == now
    assert session.get(Job, job.id).status == JobStatus.PENDING


def test_resend_is_due_again_after_another_threshold(session, user_id):
    now = utcnow()
    _job(session, user_id, age=timedelta(hours=1), now=now)
    queue = RecordingQueue()
    service.resend_stale_pending(session, queue, THRESHOLD, now=now)

    later = now + THRESHOLD + timedelta(seconds=1)
    assert service.resend_stale_pending(session, queue, THRESHOLD, now=later) == 1
    assert len(queue.sent) == 2


def test_one_failed_send_does_not_stop_the_sweep(session, user_id):
    now = utcnow()
    a = _job(session, user_id, age=timedelta(hours=2), now=now)
    b = _job(session, user_id, age=timedelta(hours=1), now=now)

    class FailFirst(RecordingQueue):
        def send(self, message):
            if message.job_id == a.id:
                raise ConnectionError("blip")
            super().send(message)

    queue = FailFirst()
    assert service.resend_stale_pending(session, queue, THRESHOLD, now=now) == 1
    assert [m.job_id for m in queue.sent] == [b.id]
