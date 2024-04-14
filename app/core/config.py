from functools import lru_cache
import os
import secrets
from typing import cast, Dict, Optional

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    BaseSettings,
    PostgresDsn,
    SecretStr,
    validator,
)


basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(BaseSettings):
    OPENAPI_URI: Optional[str] = None
    DOC_URL: Optional[str] = None
    REDOC_URL: Optional[str] = None
    API_URL: str = "/api/v1"
    PROJECT_NAME = "FastAPI"
    SERVER_NAME: str = "SERVER_NAME"
    SERVER_HOST: AnyHttpUrl = cast(AnyHttpUrl, "http://localhost")
    SERVER_PORT: int = 5000
    JWT_EXPIRE_MINUTES: int = 180
    JWT_SECRET_KEY: SecretStr = cast(SecretStr, secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_REALM: Optional[str] = None

    @validator("JWT_REALM", pre=True, always=True)
    def validate_realm(
        cls,
        v: str,
        values: Dict[str, str],
    ) -> str:
        return v or values["SERVER_NAME"]

    PG_HOST: str = "localhost"
    PG_PORT: str = "5432"

    @validator("PG_PORT")
    def validate_port(cls, v: str) -> str:
        if v.isdecimal():
            return v
        raise ValueError("DB_PORT must be a decimal")

    PG_USER: str = "test"
    PG_PASS: str = "test"
    PG_DB: str = "test"
    PG_URI: Optional[PostgresDsn] = None

    @validator("PG_URI", pre=True)
    def make_full_uri(
        cls,
        v: str,
        values: Dict[str, str],
    ) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("PG_USER"),
            password=values.get("PG_PASS"),
            host=values.get("PG_HOST"),
            port=values.get("PG_PORT"),
            path=f"/{values.get('PG_DB')}",
        )

    class Config:
        env_prefix = "APP_"
        case_sensitive = True


class Testing(BaseConfig):
    PROJECT_NAME = "Saigo blog API test"
    PG_USER: str = "test"
    PG_PASS: str = "test"
    PG_DB: str = "test"
    JWT_SECRET_KEY: SecretStr = cast(SecretStr, secrets.token_urlsafe(32))


class Development(BaseConfig):
    PROJECT_NAME = "Saigo blog Development"
    OPENAPI_URI = "/api/v1/openapi.json"
    DOC_URL = "/docs"
    REDOC_URL = "/redoc"
    PG_USER: str = "saigo"
    PG_PASS: str = "saigo"
    PG_DB: str = "saigoblog"
    JWT_SECRET_KEY: SecretStr = cast(
        SecretStr,
        "34d6b29a052a8b56ffc870a292f7dd62cda328b26eb440d363595116b17756fe",
    )
    JWT_EXPIRE_MINUTES = 1440


class Production(BaseConfig):
    PROJECT_NAME = "saigo.info"


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
