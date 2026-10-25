"""Strict settings (plan §2.10): no defaults for URLs, no fallbacks, env beats .env, no leaks."""

from pathlib import Path

import pytest

from app.core.config import (
    InvalidSettingsError,
    MissingSettingError,
    Settings,
    load_settings,
    normalise_database_url,
)

URL = "postgresql+psycopg://imibereho:secret-password@localhost:5432/imibereho"


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "ENVIRONMENT",
        "DATABASE_URL",
        "TEST_DATABASE_URL",
        "MIGRATIONS_DATABASE_URL",
        "CORS_ORIGINS",
        "LOG_LEVEL",
        "ALLOW_LOCAL_SUPERUSER",
    ):
        monkeypatch.delenv(name, raising=False)


def build(**values: object) -> Settings:
    return load_settings(_env_file=None, **values)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("postgres://u:p@h:5432/d", "postgresql+psycopg://u:p@h:5432/d"),
        ("postgresql://u:p@h:5432/d", "postgresql+psycopg://u:p@h:5432/d"),
        ("postgresql+psycopg://u:p@h:5432/d", "postgresql+psycopg://u:p@h:5432/d"),
    ],
)
def test_render_style_urls_are_normalised_to_psycopg(raw: str, expected: str) -> None:
    assert normalise_database_url(raw) == expected
    assert build(environment="local", database_url=raw).database_url == expected


def test_environment_is_required_and_has_no_default() -> None:
    with pytest.raises(InvalidSettingsError, match="ENVIRONMENT: is not set"):
        build()


def test_unknown_environment_is_rejected() -> None:
    with pytest.raises(InvalidSettingsError, match="ENVIRONMENT: has an invalid value"):
        build(environment="staging")


@pytest.mark.parametrize(
    ("target", "variable"),
    [
        ("dev", "DATABASE_URL"),
        ("production", "DATABASE_URL"),
        ("test", "TEST_DATABASE_URL"),
        ("migrations", "MIGRATIONS_DATABASE_URL"),
    ],
)
def test_missing_url_raises_an_error_naming_the_variable(target: str, variable: str) -> None:
    settings = build(environment="local")
    with pytest.raises(MissingSettingError) as excinfo:
        settings.database_url_for(target)  # type: ignore[arg-type]
    assert excinfo.value.variable == variable
    assert variable in str(excinfo.value)


def test_test_url_is_never_derived_from_database_url() -> None:
    settings = build(environment="local", database_url=URL)
    with pytest.raises(MissingSettingError, match="TEST_DATABASE_URL"):
        settings.database_url_for("test")
    with pytest.raises(MissingSettingError, match="MIGRATIONS_DATABASE_URL"):
        settings.database_url_for("migrations")


def test_blank_url_counts_as_missing() -> None:
    settings = build(environment="local", test_database_url="   ")
    with pytest.raises(MissingSettingError):
        settings.database_url_for("test")


def test_process_environment_beats_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ENVIRONMENT=production\nLOG_LEVEL=DEBUG\n", encoding="utf-8")
    monkeypatch.setenv("ENVIRONMENT", "local")
    settings = load_settings(_env_file=env_file)
    assert settings.environment == "local"  # from the process environment
    assert settings.log_level == "DEBUG"  # from the file, where the environment says nothing


def test_cors_origins_parse_from_a_comma_separated_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, https://demo.example")
    settings = build(environment="local")
    assert settings.cors_origins == ["http://localhost:5173", "https://demo.example"]


def test_cors_defaults_to_the_vite_dev_origin() -> None:
    assert build(environment="local").cors_origins == ["http://localhost:5173"]


def test_cors_wildcard_is_rejected() -> None:
    with pytest.raises(InvalidSettingsError, match="CORS_ORIGINS"):
        build(environment="local", cors_origins="*")


def test_settings_errors_never_echo_secret_values() -> None:
    """Pydantic's own message includes input values; ours must not."""
    with pytest.raises(InvalidSettingsError) as excinfo:
        build(environment="staging", database_url=URL)
    message = str(excinfo.value)
    assert "secret-password" not in message
    assert excinfo.value.__cause__ is None and excinfo.value.__suppress_context__


def test_importing_the_app_needs_no_environment() -> None:
    """`app.main` reads no settings at import time; only `app.main.app` does."""
    import importlib

    import app.main

    importlib.reload(app.main)
    assert callable(app.main.create_app)


def test_local_superuser_opt_in_defaults_to_off() -> None:
    assert build(environment="local").allow_local_superuser is False


def test_local_superuser_opt_in_is_accepted_only_in_local() -> None:
    assert build(environment="local", allow_local_superuser=True).allow_local_superuser is True


@pytest.mark.parametrize("environment", ["production", "ci"])
def test_regression_local_superuser_opt_in_is_rejected_outside_local(environment: str) -> None:
    with pytest.raises(InvalidSettingsError, match="ALLOW_LOCAL_SUPERUSER: has an invalid value"):
        build(environment=environment, allow_local_superuser=True)


def test_settings_repr_never_contains_database_urls() -> None:
    """Regression: a failing test printed `Settings(...)` with full URLs, exposing a password."""
    settings = build(
        environment="local",
        database_url=URL,
        test_database_url=URL.replace("/imibereho", "/imibereho_test"),
        migrations_database_url=URL.replace("/imibereho", "/imibereho_migrations"),
    )
    for text in (repr(settings), str(settings)):
        assert "secret-password" not in text
        assert "postgresql" not in text
    assert settings.database_url_for("dev").endswith("/imibereho")  # still usable
