"""Azure Monitor OpenTelemetry (App Insights) for the API.

Only when APPLICATIONINSIGHTS_CONNECTION_STRING is set (on Azure); locally and in
pytest this is a no-op and the SDK isn't even imported. The distro instruments
FastAPI requests, psycopg2 queries (as dependencies) and unhandled exceptions.
Cloud role name = OTEL_SERVICE_NAME, sampling = OTEL_TRACES_SAMPLER(_ARG), both
set by infra/modules/containerApps.bicep. See docs/backend.md.
"""

import os

from app.core.settings import Settings

# The probes (/health/live, /health/ready) run every few seconds; tracing them
# would fill the Log Analytics daily cap with noise.
DEFAULT_EXCLUDED_URLS = "health/.*"

_configured = False


def configure_telemetry(s: Settings) -> bool:
    """Configure Azure Monitor once per process. Returns True if it did so now."""
    global _configured
    if _configured or not s.APPLICATIONINSIGHTS_CONNECTION_STRING:
        return False

    # Read by the FastAPI instrumentation when it's enabled below.
    os.environ.setdefault("OTEL_PYTHON_FASTAPI_EXCLUDED_URLS", DEFAULT_EXCLUDED_URLS)

    from azure.monitor.opentelemetry import configure_azure_monitor

    configure_azure_monitor(connection_string=s.APPLICATIONINSIGHTS_CONNECTION_STRING)
    _configured = True
    return True
