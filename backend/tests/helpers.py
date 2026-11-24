"""Plain helpers for tests (fixtures live in conftest.py)."""

from fastapi.testclient import TestClient

PASSWORD = "correct-horse-battery"


def register(client: TestClient, username: str, email: str | None = None) -> dict:
    """Register a user and return the token response body."""
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": email or f"{username}@example.com",
            "username": username,
            "password": PASSWORD,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class FakeClock:
    """Monotonic seconds that only move when a test says so (no sleeping).

    Pass the instance as a queue's `clock`: it's callable.
    """

    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class RecordingQueue:
    """A `JobQueue` stand-in that records sends (and can fail them).

    Only `send` is used by the producer side; the rest isn't needed here.
    """

    def __init__(self, fail: bool = False) -> None:
        self.sent: list = []
        self.fail = fail

    def send(self, message) -> None:
        if self.fail:
            raise ConnectionError("queue unavailable")
        self.sent.append(message)
