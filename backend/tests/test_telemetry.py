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
    """Replace the distro module with a recorder and reset the once-only flag.

    Also records the FastAPI instrumentation call instead of patching the real
    `fastapi.FastAPI` class for the rest of the test session.
    """
    calls = []
    module = types.ModuleType("azure.monitor.opentelemetry")
    module.configure_azure_monitor = lambda **kwargs: calls.append(kwargs)
    monkeypatch.setitem(sys.modules, "azure.monitor.opentelemetry", module)
    monkeypatch.setattr(telemetry, "_configured", False)
    monkeypatch.setattr(
        telemetry, "_instrument_fastapi", lambda **kw: calls.append({"fastapi": kw})
    )
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
    distro_call, fastapi_call = fake_distro  # exactly one of each
    assert distro_call["connection_string"] == CONN
    assert fastapi_call == {"fastapi": {}}


def test_distro_skips_fastapi_and_http_clients(fake_distro):
    # The distro instruments FastAPI without options (so send/receive spans
    # can't be excluded) and instruments `requests`, which records the SDK's
    # own config polling as dependencies. The app makes no outbound HTTP calls.
    telemetry.configure_telemetry(
        Settings(_env_file=None, APPLICATIONINSIGHTS_CONNECTION_STRING=CONN)
    )
    options = fake_distro[0]["instrumentation_options"]
    for lib in ("fastapi", "requests", "urllib", "urllib3", "httpx", "httpx2"):
        assert options[lib] == {"enabled": False}, lib
    assert "psycopg2" not in options  # SQL dependencies stay on


def test_request_has_no_send_receive_spans(monkeypatch):
    # The real FastAPI instrumentation, as configure_telemetry applies it, with
    # an in-memory exporter instead of App Insights.
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setenv("OTEL_PYTHON_FASTAPI_EXCLUDED_URLS", telemetry.DEFAULT_EXCLUDED_URLS)
    telemetry._instrument_fastapi(tracer_provider=provider)
    try:
        client = TestClient(create_app(Settings(_env_file=None)))
        client.get("/openapi.json")
        assert [(s.name, s.kind.name) for s in exporter.get_finished_spans()] == [
            ("GET /openapi.json", "SERVER")
        ]

        exporter.clear()
        client.get("/health/live")
        assert exporter.get_finished_spans() == ()
    finally:
        FastAPIInstrumentor().uninstrument()


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
