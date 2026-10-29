"""Shared fixtures.

Two kinds of tests:
- DB-free tests build the app with `stub_app`: a guarded `test` URL whose database is never
  contacted (startup verification off). Endpoints that need data are not exercised this way.
- DB tests use `test_database` / `db_client` and are marked `db` automatically. At session start,
  in order (plan §2.2): resolve TEST_DATABASE_URL and run the `test` guard, migrate to head through
  `app.db.migrate`, seed every dataset, then run the seed check. A missing variable or a guard
  refusal stops the run with exit code 2; it never skips silently.
- Every DB test (the migrations round trip included) first takes `exclusive_db_run`: a
  PostgreSQL advisory lock held on the test database for the whole session. Two pytest runs at
  once would otherwise delete each other's accounts, reseed or downgrade under each other; the
  second run waits for the first instead (and stops with exit code 2 after the wait limit).

Run only the DB-free tests with `uv run pytest -m "not db"`.
"""

import time
from collections.abc import Iterator
from typing import Final

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import InvalidSettingsError, MissingSettingError, Settings, load_settings
from app.db import migrate
from app.db.guards import UnsafeDatabaseTargetError
from app.db.seed import check, seed
from app.db.session import Database
from app.main import create_app

STUB_TEST_URL: Final = (
    "postgresql+psycopg://imibereho:not-a-real-password@localhost:5432/imibereho_test"
)
DB_FIXTURES: Final = frozenset(
    {"db_settings", "exclusive_db_run", "test_database", "db_client", "db_app"}
)
# Any fixed 64-bit key, unique to this suite: one pytest session at a time holds it.
DB_RUN_LOCK_KEY: Final = 0x1B1BE7E0_7E57
DB_RUN_LOCK_WAIT_SECONDS: Final = 900


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
def exclusive_db_run(db_settings: Settings) -> Iterator[None]:
    """Hold the suite's advisory lock for the session, so DB test runs never overlap.

    A session-level lock on its own connection: it lasts until the session ends and PostgreSQL
    releases it if the process dies, so a crashed run never leaves it held.
    """
    try:
        database = Database.for_target(db_settings, "test")
    except UnsafeDatabaseTargetError as exc:
        _exit(str(exc))
        raise
    connection = database.engine.connect()
    lock = text("SELECT pg_try_advisory_lock(:key)").bindparams(key=DB_RUN_LOCK_KEY)
    deadline = time.monotonic() + DB_RUN_LOCK_WAIT_SECONDS
    waiting = False
    while not connection.execute(lock).scalar():
        connection.commit()
        if time.monotonic() > deadline:
            connection.close()
            database.dispose()
            _exit(f"another test run held the database lock for {DB_RUN_LOCK_WAIT_SECONDS} s")
        if not waiting:
            print("\n[tests] another test run is using the test databases; waiting for it")
            waiting = True
        time.sleep(2)
    connection.commit()
    try:
        yield
    finally:
        unlock = text("SELECT pg_advisory_unlock(:key)").bindparams(key=DB_RUN_LOCK_KEY)
        connection.execute(unlock)
        connection.commit()
        connection.close()
        database.dispose()


@pytest.fixture(scope="session")
def test_database(db_settings: Settings, exclusive_db_run: None) -> Iterator[Database]:
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
