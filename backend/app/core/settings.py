import json
import re
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


# Every environment-specific value comes from the environment (or a .env file in
# the working directory). Required fields have no default, so a missing one fails
# at startup instead of falling back to a dev value. Defaults: docs/backend.md.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str
    SQL_ECHO: bool = False  # log every SQL statement

    # JWT
    SECRET_KEY: str

    # Browser origins allowed by CORS. Empty means no cross-origin browser access.
    # Env: comma-separated (`http://a,http://b`) or a JSON list (`["http://a"]`).
    CORS_ORIGINS: Annotated[list[str], NoDecode] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip()
        if value.startswith("["):
            return json.loads(value)
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    # Extra origins allowed by a regular expression (Starlette full-matches it).
    # Set only in dev on Azure, for the Static Web App's PR preview hosts, whose
    # PR number can't be listed ahead of time. Unset or empty = exact list only.
    CORS_ORIGIN_REGEX: str | None = None

    @field_validator("CORS_ORIGIN_REGEX")
    @classmethod
    def _check_regex(cls, value: str | None) -> str | None:
        if not value:
            return None
        try:
            re.compile(value)  # a bad pattern stops the process at startup
        except re.error as exc:
            raise ValueError(f"invalid regex: {exc}") from exc
        return value

    # Azure Monitor (App Insights). Unset = no telemetry (local, tests).
    # Sampling, service name etc. use the standard OTEL_* env vars (docs/backend.md).
    APPLICATIONINSIGHTS_CONNECTION_STRING: str | None = None


settings = Settings()
