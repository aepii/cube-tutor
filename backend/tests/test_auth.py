"""Auth flow: register, login, refresh rotation, logout, protected routes.

These pin today's behavior ahead of the 4e auth rework.
"""

from datetime import UTC, datetime

import pytest

from app.core import security
from tests.helpers import PASSWORD, bearer, register

PROTECTED = "/v1/algs/"


# --- register -------------------------------------------------------------


def test_register_returns_both_tokens(client):
    body = register(client, "alice")
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert client.get(PROTECTED, headers=bearer(body["access_token"])).status_code == 200


def test_register_duplicate_email_is_400(client):
    register(client, "alice", email="same@example.com")
    resp = client.post(
        "/v1/auth/register",
        json={"email": "same@example.com", "username": "bob", "password": PASSWORD},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Email already registered"


def test_register_duplicate_username_is_400(client):
    register(client, "alice")
    resp = client.post(
        "/v1/auth/register",
        json={"email": "other@example.com", "username": "alice", "password": PASSWORD},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Username already registered"


# --- login ----------------------------------------------------------------


def test_login_returns_working_tokens(client):
    register(client, "alice")
    resp = client.post(
        "/v1/auth/login", json={"username": "alice", "password": PASSWORD}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["refresh_token"]
    assert client.get(PROTECTED, headers=bearer(body["access_token"])).status_code == 200


def test_login_wrong_password_is_401(client):
    register(client, "alice")
    resp = client.post(
        "/v1/auth/login", json={"username": "alice", "password": "wrong-password"}
    )
    assert resp.status_code == 401


def test_login_unknown_user_is_401(client):
    resp = client.post(
        "/v1/auth/login", json={"username": "nobody", "password": PASSWORD}
    )
    assert resp.status_code == 401


# --- refresh --------------------------------------------------------------


def test_refresh_rotates_the_pair(client, tokens):
    resp = client.post(
        "/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    new = resp.json()
    assert new["access_token"] != tokens["access_token"]
    assert new["refresh_token"] != tokens["refresh_token"]
    assert client.get(PROTECTED, headers=bearer(new["access_token"])).status_code == 200


@pytest.mark.xfail(
    strict=True,
    reason=(
        "4e: bcrypt reads only the first 72 bytes of the JWT (header + start of "
        "payload), so a rotated token still matches the user's newer row"
    ),
)
def test_reusing_a_rotated_refresh_token_is_401(client, tokens):
    old = tokens["refresh_token"]
    assert client.post("/v1/auth/refresh", json={"refresh_token": old}).status_code == 200
    assert client.post("/v1/auth/refresh", json={"refresh_token": old}).status_code == 401


def test_refresh_with_garbage_is_401(client):
    resp = client.post("/v1/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert resp.status_code == 401


def test_refresh_with_an_access_token_is_401(client, tokens):
    resp = client.post(
        "/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert resp.status_code == 401


# --- logout ---------------------------------------------------------------


def test_logout_revokes_the_refresh_token(client, tokens):
    rt = tokens["refresh_token"]
    resp = client.post("/v1/auth/logout", json={"refresh_token": rt})
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Logged out"
    assert client.post("/v1/auth/refresh", json={"refresh_token": rt}).status_code == 401


def test_logout_with_garbage_is_already_logged_out(client):
    resp = client.post("/v1/auth/logout", json={"refresh_token": "not-a-jwt"})
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Already logged out"


# --- protected routes -----------------------------------------------------


def test_protected_route_without_token_is_401(client):
    assert client.get(PROTECTED).status_code == 401


def test_protected_route_with_malformed_token_is_401(client):
    assert client.get(PROTECTED, headers=bearer("not-a-jwt")).status_code == 401


def test_protected_route_with_refresh_token_is_401(client, tokens):
    resp = client.get(PROTECTED, headers=bearer(tokens["refresh_token"]))
    assert resp.status_code == 401


# --- known bugs -----------------------------------------------------------


class _FrozenClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 1, 1, tzinfo=tz or UTC)


@pytest.mark.xfail(
    strict=True,
    reason="4e: tokens carry no jti, so same-second tokens for a user are identical",
)
def test_refresh_tokens_minted_in_the_same_second_are_distinct(monkeypatch):
    monkeypatch.setattr(security, "datetime", _FrozenClock)
    first, _ = security.create_refresh_token(subject="1")
    second, _ = security.create_refresh_token(subject="1")
    assert first != second
