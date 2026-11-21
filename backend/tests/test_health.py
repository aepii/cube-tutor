"""Liveness and readiness probes (Container Apps, Compose healthcheck, deploy smoke test)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from app.api.routes.health import get_probe_engine
from app.main import app

# Nothing listens on port 1, so connecting fails fast with "connection refused".
UNREACHABLE_URL = "postgresql://nobody:nothing@127.0.0.1:1/nowhere"


@pytest.fixture
def db_down():
    dead = create_engine(
        UNREACHABLE_URL, poolclass=NullPool, connect_args={"connect_timeout": 2}
    )
    app.dependency_overrides[get_probe_engine] = lambda: dead
    yield
    app.dependency_overrides.pop(get_probe_engine, None)
    dead.dispose()


def test_live_is_ok(client):
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_live_is_ok_with_the_database_down(client, db_down):
    assert client.get("/health/live").status_code == 200


def test_ready_is_ok_with_the_database_up(client):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_is_503_with_the_database_down(client, db_down):
    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json() == {"status": "unavailable"}


def test_probes_are_unversioned_and_need_no_auth(client):
    paths = client.get("/openapi.json").json()["paths"]
    for path in ("/health/live", "/health/ready"):
        assert "security" not in paths[path]["get"]
