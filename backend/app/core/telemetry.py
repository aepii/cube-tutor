"""Azure Monitor OpenTelemetry (App Insights) for the API.

Only when APPLICATIONINSIGHTS_CONNECTION_STRING is set (on Azure); locally and in
pytest this is a no-op and the SDK isn't even imported. Records FastAPI requests,
psycopg2 queries (as dependencies) and unhandled exceptions.
Cloud role name = OTEL_SERVICE_NAME, sampling = OTEL_TRACES_SAMPLER(_ARG), both
set by infra/modules/containerApps.bicep. See docs/backend.md.
"""

import os

from app.core.settings import Settings

# The probes (/health/live, /health/ready) run every few seconds; tracing them
# would fill the Log Analytics daily cap with noise.
DEFAULT_EXCLUDED_URLS = "health/.*"

# Instrumentations the distro would enable that we turn off:
#  - fastapi: the distro can't pass options to it; we instrument it ourselves
#    below so the ASGI `send`/`receive` steps aren't recorded as extra spans.
#  - the HTTP clients: the app makes no outbound HTTP calls, so all they'd
#    record is the SDK's own config polling (`/AzMonSDKDynamicConfiguration`).
#    Turn them back on when a feature adds outbound HTTP.
DISABLED_INSTRUMENTATIONS = (
    "fastapi",
    "requests",
    "urllib",
    "urllib3",
    "httpx",
    "httpx2",
)

_configured = False


def _instrument_fastapi(**kwargs) -> None:
    """Patch `fastapi.FastAPI` with the traced subclass, without send/receive spans."""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor().instrument(exclude_spans=["receive", "send"], **kwargs)


def configure_telemetry(s: Settings) -> bool:
    """Configure Azure Monitor once per process. Returns True if it did so now."""
    global _configured
    if _configured or not s.APPLICATIONINSIGHTS_CONNECTION_STRING:
        return False

    # Read by the FastAPI instrumentation below.
    os.environ.setdefault("OTEL_PYTHON_FASTAPI_EXCLUDED_URLS", DEFAULT_EXCLUDED_URLS)

    from azure.monitor.opentelemetry import configure_azure_monitor

    configure_azure_monitor(
        connection_string=s.APPLICATIONINSIGHTS_CONNECTION_STRING,
        instrumentation_options={
            lib: {"enabled": False} for lib in DISABLED_INSTRUMENTATIONS
        },
    )
    # After the distro, so it uses the tracer provider the distro set up.
    _instrument_fastapi()
    _configured = True
    return True
