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
