from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# Settings for the application
class Settings(BaseSettings):
    # Core
    ENV: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # JWT
    SECRET_KEY: str = Field(..., env="SECRET_KEY")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
