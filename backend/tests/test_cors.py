"""CORS origins come from settings (CORS_ORIGINS), not code."""

from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


def _preflight(client: TestClient, origin: str):
    return client.options(
        "/health/live",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )


def test_preflight_allows_only_configured_origins():
    settings = Settings(_env_file=None, CORS_ORIGINS=["http://a.test"])
    client = TestClient(create_app(settings))

    allowed = _preflight(client, "http://a.test")
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://a.test"

    denied = _preflight(client, "http://b.test")
    assert "access-control-allow-origin" not in denied.headers
