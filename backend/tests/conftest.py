"""Shared fixtures for the backend test suite.

The app reads its settings and builds its SQLAlchemy engine at import time, so
this module points DATABASE_URL at a dedicated Postgres test database *before*
anything under `app` is imported. Every test process therefore talks only to the
test database; the dev database (DATABASE_URL in the repo-root .env) is never
reachable from here.

Test database URL, in order of precedence:
1. TEST_DATABASE_URL from the environment (CI sets this).
2. Built from the repo-root .env: POSTGRES_USER / POSTGRES_PASSWORD /
   POSTGRES_HOST_PORT on localhost, database `cubetutor_test`.
"""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_DB_NAME = "cubetutor_test"
TEST_SECRET_KEY = "test-secret-key-not-for-production-0123456789"


def _resolve_test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        return url
    env = dotenv_values(REPO_ROOT / ".env")
    user = env.get("POSTGRES_USER")
    password = env.get("POSTGRES_PASSWORD")
    port = env.get("POSTGRES_HOST_PORT") or "5433"
    if not user or not password:
        pytest.exit(
            "Set TEST_DATABASE_URL, or POSTGRES_USER and POSTGRES_PASSWORD in "
            f"{REPO_ROOT / '.env'}, so the tests can reach Postgres.",
            returncode=1,
        )
    return f"postgresql://{user}:{password}@localhost:{port}/{TEST_DB_NAME}"


def _check_is_test_database(url: str) -> None:
    """Refuse to run against anything that might be the dev database."""
    test_db = make_url(url).database or ""
    dev_url = dotenv_values(REPO_ROOT / ".env").get("DATABASE_URL")
    dev_db = make_url(dev_url).database if dev_url else None
    if not test_db.endswith("_test") or test_db == dev_db:
        pytest.exit(
            f"TEST_DATABASE_URL points at database '{test_db}'. Tests truncate "
            "every table, so the database name must end in '_test' and must not "
            "be the dev database.",
            returncode=1,
        )


TEST_DATABASE_URL = _resolve_test_database_url()
_check_is_test_database(TEST_DATABASE_URL)

# Must happen before any `app` import (settings + engine are module-level).
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = TEST_SECRET_KEY

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from app.core import security
from app.core.db import engine
from app.main import app
from app.models import AlgorithmCase, AlgorithmSolution
from tests.helpers import bearer, register


def _ensure_database_exists(url: str) -> None:
    """Create the test database from the `postgres` maintenance DB if missing."""
    parsed = make_url(url)
    admin = create_engine(
        parsed.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": parsed.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{parsed.database}"'))
    except OperationalError as exc:
        reason = str(exc.orig).strip().splitlines()[0] if exc.orig else exc
        pytest.exit(
            "Can't reach the test Postgres at TEST_DATABASE_URL="
            f"{parsed.render_as_string(hide_password=True)}\n"
            f"  {reason}\n"
            "Start it with `docker compose up -d postgres`, or set TEST_DATABASE_URL.",
            returncode=1,
        )
    finally:
        admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def _schema():
    """Fresh schema once per session, built from the SQLModel metadata.

    (4b replaces this with `alembic upgrade head`.)
    """
    _ensure_database_exists(TEST_DATABASE_URL)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables(_schema):
    """Every test starts from empty tables, whatever ran before it."""
    yield
    tables = ", ".join(f'"{t.name}"' for t in SQLModel.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


class _TickingClock(datetime):
    """`datetime` for app.core.security whose now() steps one second per call.

    JWTs here carry only sub/exp/type, and exp has one-second resolution, so two
    tokens for the same user minted in the same second are identical strings.
    Stepping the clock makes every token unique.

    The clock starts on a 10-second boundary so a test's tokens (fewer than ten
    now() calls) share the same 10-second window. bcrypt only reads the first
    72 bytes of a JWT, which covers all but the last digit of `exp`, so tokens in
    one window hash the same. That's the real-world case (refresh a few seconds
    after login), and it keeps the known-bug xfails in test_auth.py
    deterministic. Fixes for both: 4e.
    """

    _start = datetime.now(UTC)
    _ticks = 0

    @classmethod
    def reset(cls):
        now = datetime.now(UTC)
        cls._start = now - timedelta(seconds=now.second % 10, microseconds=now.microsecond)
        cls._ticks = 0

    @classmethod
    def now(cls, tz=None):
        cls._ticks += 1
        return (cls._start + timedelta(seconds=cls._ticks)).astimezone(tz)


@pytest.fixture(autouse=True)
def _unique_token_times(monkeypatch):
    _TickingClock.reset()
    monkeypatch.setattr(security, "datetime", _TickingClock)


@pytest.fixture
def client() -> TestClient:
    # No `with`: the app lifespan (create_all on the configured engine) isn't
    # needed, since the session fixture already built the schema.
    return TestClient(app)


@pytest.fixture
def session():
    with Session(engine) as s:
        yield s


@pytest.fixture
def tokens(client) -> dict:
    """Tokens for a freshly registered user `alice`."""
    return register(client, "alice")


@pytest.fixture
def auth_headers(tokens) -> dict:
    return bearer(tokens["access_token"])


@pytest.fixture
def algs(session) -> dict:
    """Two cases, three solutions: OLL 1 has two solutions, PLL Ua has one."""
    oll = AlgorithmCase(subset="OLL", name="OLL 1", subgroup="Dot", setup="R U2 R'")
    pll = AlgorithmCase(subset="PLL", name="Ua", subgroup="Edges", setup="M2 U M")
    session.add_all([oll, pll])
    session.commit()
    s1 = AlgorithmSolution(case_id=oll.id, solution="R U2 R2 F R F'", orientation=0)
    s2 = AlgorithmSolution(case_id=oll.id, solution="r U r' U2", orientation=1)
    s3 = AlgorithmSolution(case_id=pll.id, solution="M2 U M U2 M' U M2", orientation=0)
    session.add_all([s1, s2, s3])
    session.commit()
    return {
        "oll": oll.id,
        "pll": pll.id,
        "oll_a": s1.id,
        "oll_b": s2.id,
        "pll_a": s3.id,
    }
