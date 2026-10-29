"""Strict application settings (implementation plan §2.10).

Rules:
- `ENVIRONMENT` has no default.
- Each database target reads exactly one variable. No variable falls back to another and none
  has a default URL; asking for a missing one raises an error naming the variable.
- Process environment variables take precedence over `backend/.env`.
- Nothing is read at import time: call `get_settings()` (or build `Settings(...)` in tests).
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Final, Literal

from pydantic import Field, SecretStr, ValidationError, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR: Final = Path(__file__).resolve().parents[2]
ENV_FILE: Final = BACKEND_DIR / ".env"
JWT_SECRET_MIN_LENGTH: Final = 32  # 256 bits of key material for HS256 (RFC 7518 §3.2)
# Request bodies (contract §1.3, 413 `request-too-large`). The largest legitimate body is about
# 5 KB (a tracker POST whose 240-character title and 560-character note are all JSON surrogate
# escapes); 64 KiB leaves room for whitespace and new fields. The bounds stop a typo from
# disabling the limit (0) or making it meaningless.
MAX_REQUEST_BODY_BYTES_DEFAULT: Final = 65_536
MAX_REQUEST_BODY_BYTES_MIN: Final = 1_024
MAX_REQUEST_BODY_BYTES_MAX: Final = 1_048_576

Environment = Literal["local", "ci", "production"]
Target = Literal["dev", "test", "migrations", "production"]

TARGET_VARIABLES: Final[dict[Target, str]] = {
    "dev": "DATABASE_URL",
    "production": "DATABASE_URL",
    "test": "TEST_DATABASE_URL",
    "migrations": "MIGRATIONS_DATABASE_URL",
}


class MissingSettingError(RuntimeError):
    """A required setting is absent. The message names the variable, never a value."""

    def __init__(self, variable: str) -> None:
        self.variable = variable
        super().__init__(f"{variable} is not set. Add it to the environment or backend/.env.")


def normalise_database_url(url: str) -> str:
    """Normalise Render-style `postgres://` / `postgresql://` URLs to the psycopg 3 driver.

    This is the only transformation applied to a database URL.
    """
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Environment
    # repr=False: the URLs carry passwords, so they never appear in a repr (e.g. pytest
    # tracebacks, logs or error messages). Read them only through `database_url_for`.
    database_url: str | None = Field(default=None, repr=False)
    test_database_url: str | None = Field(default=None, repr=False)
    migrations_database_url: str | None = Field(default=None, repr=False)
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    max_request_body_bytes: int = Field(
        default=MAX_REQUEST_BODY_BYTES_DEFAULT,
        ge=MAX_REQUEST_BODY_BYTES_MIN,
        le=MAX_REQUEST_BODY_BYTES_MAX,
    )
    # Local development only: permits a PostgreSQL superuser for target `dev` with
    # ENVIRONMENT=local on a local host (see app/db/guards.py). Refused outright elsewhere.
    allow_local_superuser: bool = False
    # Signs the bearer tokens of /auth/register and /auth/login (HS256, contract §11.8). Without
    # it those two endpoints answer 503 `auth-not-configured`; nothing else needs it.
    jwt_secret_key: SecretStr | None = Field(default=None, repr=False)

    @field_validator("jwt_secret_key", mode="before")
    @classmethod
    def _blank_secret_is_unset(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("jwt_secret_key")
    @classmethod
    def _secret_is_long_enough(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and len(value.get_secret_value()) < JWT_SECRET_MIN_LENGTH:
            raise ValueError(f"JWT_SECRET_KEY must be at least {JWT_SECRET_MIN_LENGTH} characters")
        return value

    @field_validator("database_url", "test_database_url", "migrations_database_url")
    @classmethod
    def _normalise_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return normalise_database_url(value.strip())

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def _reject_wildcard(cls, value: list[str]) -> list[str]:
        if "*" in value:
            raise ValueError("CORS_ORIGINS must list explicit origins; '*' is not allowed.")
        return value

    @field_validator("allow_local_superuser")
    @classmethod
    def _local_superuser_only_in_local(cls, value: bool, info: ValidationInfo) -> bool:
        if value and info.data.get("environment") != "local":
            raise ValueError("ALLOW_LOCAL_SUPERUSER may only be true when ENVIRONMENT=local")
        return value

    def database_url_for(self, target: Target) -> str:
        """Return the URL for `target`, reading only that target's variable."""
        variable = TARGET_VARIABLES[target]
        value = getattr(self, variable.lower())
        if not isinstance(value, str):
            raise MissingSettingError(variable)
        return value


class InvalidSettingsError(RuntimeError):
    """Settings failed validation. The message names variables and problems, never values."""


def load_settings(**overrides: object) -> Settings:
    """Build `Settings`, turning a validation error into one that cannot echo secret values.

    Pydantic's own error text includes the input values (which can be database URLs with
    passwords), so it is never printed or chained.
    """
    try:
        return Settings(**overrides)  # type: ignore[arg-type]
    except ValidationError as exc:
        problems = []
        for error in exc.errors(include_url=False):
            unset = error["type"] == "missing" or error.get("input") == ""  # blank means unset
            name = ".".join(str(part) for part in error["loc"]).upper() or "SETTINGS"
            problems.append(f"{name}: {'is not set' if unset else 'has an invalid value'}")
        raise InvalidSettingsError("Invalid configuration: " + "; ".join(problems)) from None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings from the process environment, then `backend/.env`."""
    return load_settings()
