import json
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

    # Celery (Redis today)
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip()
        if value.startswith("["):
            return json.loads(value)
        return [origin.strip() for origin in value.split(",") if origin.strip()]


settings = Settings()
