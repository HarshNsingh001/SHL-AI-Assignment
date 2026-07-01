import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):

    app_name: str = Field(default="SHL Assessment Agent")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    api_prefix: str = Field(default="")


def read_environment_value(name: str, default: str) -> str:
    return os.getenv(name, default)


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        app_name=read_environment_value("APP_NAME", "SHL Assessment Agent"),
        app_env=read_environment_value("APP_ENV", "development"),
        log_level=read_environment_value("LOG_LEVEL", "INFO"),
        api_prefix=read_environment_value("API_PREFIX", ""),
    )
