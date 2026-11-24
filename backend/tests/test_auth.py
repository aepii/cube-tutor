"""Auth flow: register, login, refresh rotation, logout, protected routes."""

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import event
from sqlmodel import Session, select

from app.core import security
from app.core.db import engine, get_session
from app.main import app
from app.models import RefreshToken, User
from tests.helpers import PASSWORD, bearer, register

PROTECTED = "/v1/algs/"


# --- register -------------------------------------------------------------


def test_register_returns_both_tokens(client):
    body = register(client, "alice")
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert (
        client.get(PROTECTED, headers=bearer(body["access_token"])).status_code == 200
    )


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
    assert (
        client.get(PROTECTED, headers=bearer(body["access_token"])).status_code == 200
    )


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


def test_reusing_a_rotated_refresh_token_is_401(client, tokens):
    old = tokens["refresh_token"]
    assert (
        client.post("/v1/auth/refresh", json={"refresh_token": old}).status_code == 200
    )
    assert (
        client.post("/v1/auth/refresh", json={"refresh_token": old}).status_code == 401
    )


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
    assert (
        client.post("/v1/auth/refresh", json={"refresh_token": rt}).status_code == 401
    )


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


# --- token storage --------------------------------------------------------


def _rows(session, user_id: int = 1) -> list[RefreshToken]:
    return list(
        session.exec(select(RefreshToken).where(RefreshToken.user_id == user_id))
    )


def test_stored_hash_is_sha256_of_the_token(client, session, tokens):
    [row] = _rows(session)
    expected = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
    assert row.hashed_token == expected


def test_refresh_does_one_token_lookup(client, tokens):
    selects: list[str] = []

    def count(conn, cursor, statement, *args):
        sql = statement.lower()
        if sql.lstrip().startswith("select") and "from refreshtoken" in sql:
            selects.append(statement)

    event.listen(engine, "before_cursor_execute", count)
    try:
        resp = client.post(
            "/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
    finally:
        event.remove(engine, "before_cursor_execute", count)
    assert resp.status_code == 200
    assert len(selects) == 1, selects


def _insert_token(session, user_id: int, expires_at: datetime, revoked=False) -> str:
    """A validly signed refresh JWT whose DB row has the given expiry."""
    token, _ = security.create_refresh_token(subject=str(user_id))
    session.add(
        RefreshToken(
            user_id=user_id,
            hashed_token=security.hash_token(token),
            expires_at=expires_at,
            is_revoked=revoked,
        )
    )
    session.commit()
    return token


def test_refresh_with_an_expired_row_is_401(client, session, tokens):
    past = datetime.now(UTC) - timedelta(minutes=1)
    token = _insert_token(session, 1, past)
    resp = client.post("/v1/auth/refresh", json={"refresh_token": token})
    assert resp.status_code == 401


def test_login_deletes_expired_rows(client, session, tokens):
    past = datetime.now(UTC) - timedelta(minutes=1)
    _insert_token(session, 1, past)
    _insert_token(session, 1, past, revoked=True)
    assert len(_rows(session)) == 3

    resp = client.post(
        "/v1/auth/login", json={"username": "alice", "password": PASSWORD}
    )
    assert resp.status_code == 200
    session.expire_all()
    rows = _rows(session)
    # The register token and the new login token survive; both expired rows go.
    assert len(rows) == 2
    assert all(r.expires_at.replace(tzinfo=UTC) > datetime.now(UTC) for r in rows)


# --- register race --------------------------------------------------------


class _NoDupeCheckSession(Session):
    """Session whose `select(User)` finds nothing, so the pre-check is bypassed.

    This simulates a concurrent registration that passed the pre-check before
    the other request committed.
    """

    def exec(self, statement, *args, **kwargs):
        result = super().exec(statement, *args, **kwargs)
        if statement.column_descriptions[0].get("entity") is User:
            return _Empty()
        return result


class _Empty:
    def first(self):
        return None


def _register_bypassing_precheck(client, email, username):
    def override():
        with _NoDupeCheckSession(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    try:
        return client.post(
            "/v1/auth/register",
            json={"email": email, "username": username, "password": PASSWORD},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_register_race_on_username_is_400(client):
    register(client, "alice")
    resp = _register_bypassing_precheck(client, "other@example.com", "alice")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Username already registered"


def test_register_race_on_email_is_400(client):
    register(client, "alice", email="same@example.com")
    resp = _register_bypassing_precheck(client, "same@example.com", "bob")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Email already registered"


# --- same-second tokens ---------------------------------------------------


class _FrozenClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 1, 1, tzinfo=tz or UTC)


def test_refresh_tokens_minted_in_the_same_second_are_distinct(monkeypatch):
    monkeypatch.setattr(security, "datetime", _FrozenClock)
    first, _ = security.create_refresh_token(subject="1")
    second, _ = security.create_refresh_token(subject="1")
    assert first != second


class _FrozenNow(datetime):
    """Clock stuck at one real instant, so minted tokens are live but same-second."""

    _at = datetime.now(UTC).replace(microsecond=0)

    @classmethod
    def now(cls, tz=None):
        return cls._at.astimezone(tz)


def test_two_logins_in_the_same_second_both_succeed(client, session, monkeypatch):
    register(client, "alice")
    _FrozenNow._at = datetime.now(UTC).replace(microsecond=0)
    monkeypatch.setattr(security, "datetime", _FrozenNow)
    for _ in range(2):
        resp = client.post(
            "/v1/auth/login", json={"username": "alice", "password": PASSWORD}
        )
        assert resp.status_code == 200
    assert len(_rows(session)) == 3
