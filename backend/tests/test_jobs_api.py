"""AC1–AC4 through the API: POST /v1/jobs and GET /v1/jobs/{id}."""

from uuid import UUID, uuid4

import jwt
import pytest
from sqlmodel import select

from app.jobs.deps import get_job_queue
from app.jobs.memory import InMemoryJobQueue
from app.jobs.queue import JobMessage
from app.main import app
from app.models import Job
from tests.helpers import RecordingQueue, bearer, register

ECHO = {"type": "diagnostic.echo", "payload": {"message": "hi"}}


@pytest.fixture
def queue():
    q = RecordingQueue()
    app.dependency_overrides[get_job_queue] = lambda: q
    yield q
    app.dependency_overrides.pop(get_job_queue, None)


@pytest.fixture
def bob_headers(client) -> dict:
    return bearer(register(client, "bob")["access_token"])


def _jobs(session) -> list[Job]:
    session.expire_all()
    return list(session.exec(select(Job)).all())


def _user_id(headers) -> int:
    # No /me endpoint; the access token's `sub` is the user id.
    token = headers["Authorization"].removeprefix("Bearer ")
    return int(jwt.decode(token, options={"verify_signature": False})["sub"])


# --- AC1 -------------------------------------------------------------------


def test_post_echo_creates_pending_job_and_one_message(
    client, auth_headers, queue, session
):
    resp = client.post("/v1/jobs/", json=ECHO, headers=auth_headers)

    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    job_id = UUID(body["id"])

    [job] = _jobs(session)
    assert job.id == job_id
    assert job.attempts == 0
    assert job.user_id == _user_id(auth_headers)
    assert job.payload == {"message": "hi"}
    assert queue.sent == [JobMessage(job_id=job_id, type="diagnostic.echo")]


def test_post_with_the_in_memory_queue_leaves_one_message(client, auth_headers):
    q = InMemoryJobQueue()
    app.dependency_overrides[get_job_queue] = lambda: q
    try:
        resp = client.post("/v1/jobs/", json=ECHO, headers=auth_headers)
    finally:
        app.dependency_overrides.pop(get_job_queue, None)

    got = q.receive()
    assert got.message == JobMessage(
        job_id=UUID(resp.json()["id"]), type="diagnostic.echo"
    )
    assert q.receive() is None


def test_post_keeps_the_fail_flag_in_the_payload(client, auth_headers, queue, session):
    body = {"type": "diagnostic.echo", "payload": {"message": "x", "fail": "transient"}}
    assert client.post("/v1/jobs/", json=body, headers=auth_headers).status_code == 202
    [job] = _jobs(session)
    assert job.payload == {"message": "x", "fail": "transient"}


# --- AC2 -------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        {"type": "diagnostic.nope", "payload": {"message": "hi"}},
        {"type": "solver.cfop", "payload": {"message": "hi"}},
        {"payload": {"message": "hi"}},
        {"type": "diagnostic.echo"},
        {"type": "diagnostic.echo", "payload": {}},
        {"type": "diagnostic.echo", "payload": {"message": 5}},
        {"type": "diagnostic.echo", "payload": {"message": "hi", "fail": "sometimes"}},
        {"type": "diagnostic.echo", "payload": {"message": "hi", "extra": 1}},
        {"type": "diagnostic.echo", "payload": {"message": "hi"}, "user_id": 99},
    ],
    ids=[
        "unknown-type",
        "not-submittable-type",
        "no-type",
        "no-payload",
        "no-message",
        "message-not-string",
        "bad-fail",
        "extra-payload-key",
        "extra-top-level-key",
    ],
)
def test_invalid_request_is_422_with_no_row_and_no_message(
    client, auth_headers, queue, session, body
):
    resp = client.post("/v1/jobs/", json=body, headers=auth_headers)
    assert resp.status_code == 422, resp.text
    assert _jobs(session) == []
    assert queue.sent == []


def test_post_without_token_is_401(client, queue, session):
    resp = client.post("/v1/jobs/", json=ECHO)
    assert resp.status_code == 401
    assert _jobs(session) == []
    assert queue.sent == []


def test_get_without_token_is_401(client):
    assert client.get(f"/v1/jobs/{uuid4()}").status_code == 401


# --- AC3 -------------------------------------------------------------------


def test_owner_can_read_their_job(client, auth_headers, queue):
    job_id = client.post("/v1/jobs/", json=ECHO, headers=auth_headers).json()["id"]

    resp = client.get(f"/v1/jobs/{job_id}", headers=auth_headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == job_id
    assert body["type"] == "diagnostic.echo"
    assert body["status"] == "pending"
    assert body["result"] is None
    assert body["error"] is None
    assert body["attempts"] == 0


def test_another_users_job_is_404(client, auth_headers, bob_headers, queue):
    job_id = client.post("/v1/jobs/", json=ECHO, headers=auth_headers).json()["id"]

    resp = client.get(f"/v1/jobs/{job_id}", headers=bob_headers)

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Job not found"}


def test_unknown_job_is_404_with_the_same_body(client, auth_headers):
    resp = client.get(f"/v1/jobs/{uuid4()}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Job not found"}


def test_malformed_job_id_is_422(client, auth_headers):
    assert client.get("/v1/jobs/not-a-uuid", headers=auth_headers).status_code == 422


# --- AC4 -------------------------------------------------------------------


def test_post_when_send_fails_still_202_and_pending(client, auth_headers, session):
    failing = RecordingQueue(fail=True)
    app.dependency_overrides[get_job_queue] = lambda: failing
    try:
        resp = client.post("/v1/jobs/", json=ECHO, headers=auth_headers)
    finally:
        app.dependency_overrides.pop(get_job_queue, None)

    assert resp.status_code == 202, resp.text
    assert resp.json()["status"] == "pending"
    [job] = _jobs(session)
    assert str(job.id) == resp.json()["id"]
    assert job.status == "pending"
