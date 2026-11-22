"""Azure Monitor telemetry is configured only when a connection string is set, and only once."""

import os
import sys
import types

import pytest
from fastapi.testclient import TestClient

from app.core import telemetry
from app.core.settings import Settings
from app.main import create_app

CONN = "InstrumentationKey=00000000-0000-0000-0000-000000000000;IngestionEndpoint=https://x.test/"


@pytest.fixture
def fake_distro(monkeypatch):
    """Replace the distro module with a recorder and reset the once-only flag."""
    calls = []
    module = types.ModuleType("azure.monitor.opentelemetry")
    module.configure_azure_monitor = lambda **kwargs: calls.append(kwargs)
    monkeypatch.setitem(sys.modules, "azure.monitor.opentelemetry", module)
    monkeypatch.setattr(telemetry, "_configured", False)
    monkeypatch.delenv("OTEL_PYTHON_FASTAPI_EXCLUDED_URLS", raising=False)
    return calls


def test_no_connection_string_does_nothing_and_app_starts(fake_distro, monkeypatch):
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)
    s = Settings(_env_file=None)
    assert s.APPLICATIONINSIGHTS_CONNECTION_STRING is None

    assert telemetry.configure_telemetry(s) is False
    assert fake_distro == []
    assert TestClient(create_app(s)).get("/health/live").status_code == 200


def test_connection_string_configures_once(fake_distro):
    s = Settings(_env_file=None, APPLICATIONINSIGHTS_CONNECTION_STRING=CONN)

    assert telemetry.configure_telemetry(s) is True
    assert telemetry.configure_telemetry(s) is False  # second call: no-op
    assert fake_distro == [{"connection_string": CONN}]


def test_health_endpoints_excluded_by_default(fake_distro, monkeypatch):
    telemetry.configure_telemetry(
        Settings(_env_file=None, APPLICATIONINSIGHTS_CONNECTION_STRING=CONN)
    )
    assert os.environ["OTEL_PYTHON_FASTAPI_EXCLUDED_URLS"] == "health/.*"


def test_excluded_urls_env_wins(fake_distro, monkeypatch):
    monkeypatch.setenv("OTEL_PYTHON_FASTAPI_EXCLUDED_URLS", "custom")
    telemetry.configure_telemetry(
        Settings(_env_file=None, APPLICATIONINSIGHTS_CONNECTION_STRING=CONN)
    )
    assert os.environ["OTEL_PYTHON_FASTAPI_EXCLUDED_URLS"] == "custom"


def test_create_app_uses_the_patched_fastapi_class(monkeypatch):
    # The FastAPI instrumentation works by replacing `fastapi.FastAPI` with a
    # subclass. An app built from a `from fastapi import FastAPI` bound before
    # that would silently not be traced.
    import fastapi

    class Instrumented(fastapi.FastAPI):
        pass

    monkeypatch.setattr(fastapi, "FastAPI", Instrumented)
    assert isinstance(create_app(Settings(_env_file=None)), Instrumented)
