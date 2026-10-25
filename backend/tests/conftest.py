"""Shared fixtures.

Two kinds of tests:
- DB-free tests build the app with `stub_app`: a guarded `test` URL whose database is never
  contacted (startup verification off). Endpoints that need data are not exercised this way.
- DB tests use `test_database` / `db_client` and are marked `db` automatically. At session start,
  in order (plan §2.2): resolve TEST_DATABASE_URL and run the `test` guard, migrate to head through
  `app.db.migrate`, seed every dataset, then run the seed check. A missing variable or a guard
  refusal stops the run with exit code 2; it never skips silently.

Run only the DB-free tests with `uv run pytest -m "not db"`.
"""

from collections.abc import Iterator
from typing import Final

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import InvalidSettingsError, MissingSettingError, Settings, load_settings
from app.db import migrate
from app.db.guards import UnsafeDatabaseTargetError
from app.db.seed import check, seed
from app.db.session import Database
from app.main import create_app

STUB_TEST_URL: Final = (
    "postgresql+psycopg://imibereho:not-a-real-password@localhost:5432/imibereho_test"
)
DB_FIXTURES: Final = frozenset({"db_settings", "test_database", "db_client", "db_app"})


def make_settings(**overrides: object) -> Settings:
    """Settings that ignore the process environment's database URLs and `backend/.env`."""
    values: dict[str, object] = {
        "environment": "local",
        "database_url": None,
        "test_database_url": STUB_TEST_URL,
        "migrations_database_url": None,
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        fixtures = set(getattr(item, "fixturenames", ()))
        if fixtures & DB_FIXTURES or "integration" in item.path.parts:
            item.add_marker(pytest.mark.db)


@pytest.fixture
def stub_settings() -> Settings:
    return make_settings()


@pytest.fixture
def stub_app(stub_settings: Settings) -> FastAPI:
    return create_app("test", settings=stub_settings, verify_database_on_startup=False)


@pytest.fixture
def client(stub_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(stub_app, raise_server_exceptions=False) as test_client:
        yield test_client


# --- Database fixtures (marked `db`) ---


def _exit(message: str) -> None:
    pytest.exit(f"Database tests cannot run: {message}", returncode=2)


@pytest.fixture(scope="session")
def db_settings() -> Settings:
    try:
        settings = load_settings()
        settings.database_url_for("test")
    except (InvalidSettingsError, MissingSettingError) as exc:
        _exit(f"{exc}. See backend/README.md, 'Database setup'.")
        raise  # unreachable: pytest.exit raises
    return settings


@pytest.fixture(scope="session")
def test_database(db_settings: Settings) -> Iterator[Database]:
    try:
        database = Database.for_target(db_settings, "test")
        migrate.run(db_settings, "test", "upgrade", "head")
    except UnsafeDatabaseTargetError as exc:
        _exit(str(exc))
        raise
    seed(database)
    mismatched = check(database)
    if mismatched:
        _exit(f"seed check failed for {mismatched}")
    yield database
    database.dispose()


@pytest.fixture(scope="session")
def db_app(db_settings: Settings, test_database: Database) -> FastAPI:
    return create_app("test", settings=db_settings, database=test_database)


@pytest.fixture(scope="session")
def db_client(db_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(db_app, raise_server_exceptions=False) as test_client:
        yield test_client
