"""Settings parsing: everything environment-specific comes from env vars."""

import pytest

from app.core.db import engine
from app.core.settings import Settings


def _settings(**env) -> Settings:
    # The required vars come from conftest; ignore any local .env file.
    return Settings(_env_file=None, **env)


@pytest.mark.parametrize(
    "raw",
    [
        "http://a.test,http://b.test",
        " http://a.test , http://b.test ,",
        '["http://a.test", "http://b.test"]',
    ],
)
def test_cors_origins_parse_comma_separated_and_json(monkeypatch, raw):
    monkeypatch.setenv("CORS_ORIGINS", raw)
    assert _settings().CORS_ORIGINS == ["http://a.test", "http://b.test"]


def test_cors_origins_default_to_none_allowed(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert _settings().CORS_ORIGINS == []


def test_sql_echo_defaults_off(monkeypatch):
    monkeypatch.delenv("SQL_ECHO", raising=False)
    assert _settings().SQL_ECHO is False


def test_sql_echo_from_env(monkeypatch):
    monkeypatch.setenv("SQL_ECHO", "true")
    assert _settings().SQL_ECHO is True


def test_app_engine_does_not_echo_by_default():
    assert engine.echo is False

