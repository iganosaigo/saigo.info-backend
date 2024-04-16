from functools import lru_cache
import os
import secrets
from typing import cast, Optional

from pydantic import (
    BaseModel,
    HttpUrl,
    PostgresDsn,
    SecretStr,
    ValidationInfo,
    field_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


basedir = os.path.abspath(os.path.dirname(__file__))


class UrlParse(BaseModel):
    host: HttpUrl


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", case_sensitive=True)

    OPENAPI_URI: Optional[str] = None
    DOC_URL: Optional[str] = None
    REDOC_URL: Optional[str] = None
    API_URL: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI"
    SERVER_NAME: str = "SERVER_NAME"
    SERVER_PORT: int = 5000
    SERVER_HOST: str = "http://localhost"

    JWT_EXPIRE_MINUTES: int = 180
    JWT_SECRET_KEY: SecretStr = cast(SecretStr, secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_REALM: Optional[str] = None

    @field_validator("JWT_REALM", mode="before")
    @classmethod
    def validate_realm(cls, v: str, info: ValidationInfo) -> str:
        return v or info.data["SERVER_NAME"]

    PG_HOST: str = "localhost"
    PG_PORT: str = "5432"

    @field_validator("PG_PORT")
    @classmethod
    def validate_port(cls, v: str, info: ValidationInfo) -> str:
        if v.isdecimal():
            return v
        raise ValueError(f"{info.field_name} must be a decimal")

    PG_USER: str = "test"
    PG_PASS: str = "test"
    PG_DB: str = "test"
    PG_URI: Optional[PostgresDsn] = None

    @field_validator("PG_URI", mode="before")
    @classmethod
    def make_full_uri(cls, v: str, info: ValidationInfo) -> PostgresDsn:
        if v:
            return MultiHostUrl(v)
        values = info.data
        pg_dsn = MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=values.get("PG_USER"),
            password=values.get("PG_PASS"),
            host=values.get("PG_HOST"),
            port=int(values.get("PG_PORT", 5432)),
            path=values.get("PG_DB"),
        )
        return pg_dsn


class Testing(BaseConfig):
    PROJECT_NAME: str = "Saigo blog API test"
    PG_USER: str = "test"
    PG_PASS: str = "test"
    PG_DB: str = "test"
    JWT_SECRET_KEY: SecretStr = cast(SecretStr, secrets.token_urlsafe(32))


class Development(BaseConfig):
    PROJECT_NAME: str = "Saigo blog Development"
    OPENAPI_URI: str = "/api/v1/openapi.json"  # type: ignore
    DOC_URL: str = "/docs"  # type: ignore
    REDOC_URL: str = "/redoc"  # type: ignore
    PG_USER: str = "saigo"
    PG_PASS: str = "saigo"
    PG_DB: str = "saigoblog"
    JWT_SECRET_KEY: SecretStr = cast(
        SecretStr,
        "34d6b29a052a8b56ffc870a292f7dd62cda328b26eb440d363595116b17756fe",
    )
    JWT_EXPIRE_MINUTES: int = 1440


class Production(BaseConfig):
    PROJECT_NAME: str = "saigo.info"


class PgConnectParams(BaseModel):
    pool_pre_ping: bool = False
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 5
    future: bool = True


CONFIG = {
    "prod": Production,
    "dev": Development,
    "test": Testing,
    "default": Development,
}


@lru_cache()
def get_settings(app_mode: str) -> BaseConfig:
    return CONFIG[app_mode]()


app_mode = os.environ.get("APP_MODE", "default")
settings = get_settings(app_mode)
