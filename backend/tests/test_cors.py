"""CORS origins come from settings (CORS_ORIGINS, CORS_ORIGIN_REGEX), not code."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

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


# Real SWA preview hosts: <default subdomain>-<PR#>.<region>.<partition>.azurestaticapps.net
# The regex is the shape infra/main.bicep builds for dev from the default hostname.
SWA_SUB = "gentle-sea-0abc12345"
PREVIEW_REGEX = rf"^https://{SWA_SUB}-[0-9]+\.[a-z0-9]+\.2\.azurestaticapps\.net$"
PREVIEW_ORIGIN = f"https://{SWA_SUB}-1.centralus.2.azurestaticapps.net"


def _client(**settings) -> TestClient:
    return TestClient(create_app(Settings(_env_file=None, **settings)))


def test_preview_origin_rejected_without_regex():
    # Prod and local: exact origins only.
    client = _client(CORS_ORIGINS=["http://a.test"])
    assert "access-control-allow-origin" not in _preflight(client, PREVIEW_ORIGIN).headers


def test_preview_origin_allowed_by_regex():
    client = _client(CORS_ORIGINS=["http://a.test"], CORS_ORIGIN_REGEX=PREVIEW_REGEX)
    response = _preflight(client, PREVIEW_ORIGIN)
    assert response.headers["access-control-allow-origin"] == PREVIEW_ORIGIN
    # The exact list still works alongside the regex.
    exact = _preflight(client, "http://a.test")
    assert exact.headers["access-control-allow-origin"] == "http://a.test"


@pytest.mark.parametrize(
    "origin",
    [
        f"https://{SWA_SUB}-1.centralus.2.azurestaticapps.net.evil.test",
        f"https://evil-{SWA_SUB}-1.centralus.2.azurestaticapps.net",
        f"https://{SWA_SUB}-1.centralus.2xazurestaticapps.net",
        f"http://{SWA_SUB}-1.centralus.2.azurestaticapps.net",
        f"https://{SWA_SUB}-main.centralus.2.azurestaticapps.net",
        "https://other-site-0abc12345-1.centralus.2.azurestaticapps.net",
    ],
)
def test_look_alike_origins_rejected_by_regex(origin):
    client = _client(CORS_ORIGIN_REGEX=PREVIEW_REGEX)
    assert "access-control-allow-origin" not in _preflight(client, origin).headers


def test_invalid_regex_fails_at_startup():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, CORS_ORIGIN_REGEX="^https://(unclosed$")


def test_empty_regex_means_unset():
    assert Settings(_env_file=None, CORS_ORIGIN_REGEX="").CORS_ORIGIN_REGEX is None
