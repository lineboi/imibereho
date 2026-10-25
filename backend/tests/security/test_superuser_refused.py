"""Superuser rejection against a real PostgreSQL server (plan §2.3, v2.3.1).

Three cases, each with its own variable:
1. `postgres` user name: refused by name before connecting (`superuser_name`).
2. A superuser with another name (CI creates `imibereho_ci_superuser`): refused by the `rolsuper`
   check after connecting (`superuser_role`), with the session closed and the database unchanged.
3. The application role `imibereho`: accepted.

In CI all three always run. Locally, the two superuser cases are skipped with the reason printed
when their variable is absent; a local skip is not evidence (the CI run is).
These variables are read here only; they are never targets and never `Settings` fields.
"""

import os
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import Settings
from app.db import migrate
from app.db.guards import RefusalReason, UnsafeDatabaseTargetError
from app.db.seed import seed
from app.db.session import Database, create_guarded_engine
from app.main import create_app

POSTGRES_URL = os.environ.get("SUPERUSER_POSTGRES_DATABASE_URL")
ALT_URL = os.environ.get("SUPERUSER_ALT_DATABASE_URL")
IN_CI = os.environ.get("CI") == "true"


def require(url: str | None, name: str) -> str:
    if url:
        return url
    if IN_CI:
        pytest.fail(f"{name} must be set in CI; a skip here would hide a missing check")
    pytest.skip(f"{name} is not set (optional locally; CI always runs this case)")


def settings_with(db_settings: Settings, url: str) -> Settings:
    return db_settings.model_copy(update={"test_database_url": url})


def attempts(settings: Settings, url: str) -> dict[str, Callable[[], object]]:
    """The three entry points that must each refuse: migrations, seeding and the app."""

    def run_migrate() -> object:
        migrate.run(settings, "test", "upgrade", "head")
        return None

    def run_seed() -> object:
        engine = create_guarded_engine(url, "test", settings.environment, "seed")
        try:
            return seed(Database(engine, "test"))
        finally:
            engine.dispose()

    def run_app() -> object:
        with TestClient(create_app("test", settings=settings)):
            return None

    return {"migrate": run_migrate, "seed": run_seed, "create_app": run_app}


def database_state(database: Database) -> tuple[object, ...]:
    with database.read_only_session() as session:
        return (
            session.execute(text("SELECT version_num FROM alembic_version")).scalar(),
            tuple(session.execute(text("SELECT dataset, content_hash FROM seed_state ORDER BY 1"))),
        )


def sessions_for(database: Database, user: str) -> int:
    with database.read_only_session() as session:
        return int(
            session.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE usename = :user"),
                {"user": user},
            ).scalar_one()
        )


def test_postgres_username_refused_before_connect(
    db_settings: Settings, test_database: Database
) -> None:
    url = require(POSTGRES_URL, "SUPERUSER_POSTGRES_DATABASE_URL")
    before = database_state(test_database)
    for name, attempt in attempts(settings_with(db_settings, url), url).items():
        with pytest.raises(UnsafeDatabaseTargetError) as excinfo:
            attempt()
        # `superuser_name` is raised by the URL check, which runs before any connection opens
        # (pgAdmin may hold its own `postgres` sessions, so pg_stat_activity cannot prove it).
        assert excinfo.value.reason is RefusalReason.SUPERUSER_NAME, name
    assert database_state(test_database) == before


def test_non_postgres_superuser_refused_by_rolsuper(
    db_settings: Settings, test_database: Database
) -> None:
    url = require(ALT_URL, "SUPERUSER_ALT_DATABASE_URL")
    user = url.split("://", 1)[1].split(":", 1)[0]
    before = database_state(test_database)
    for name, attempt in attempts(settings_with(db_settings, url), url).items():
        with pytest.raises(UnsafeDatabaseTargetError) as excinfo:
            attempt()
        assert excinfo.value.reason is RefusalReason.SUPERUSER_ROLE, name
    assert sessions_for(test_database, user) == 0, "the refused session must be closed"
    assert database_state(test_database) == before


def test_application_role_accepted(test_database: Database) -> None:
    with test_database.session() as session:
        assert (
            session.execute(
                text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
            ).scalar_one()
            is False
        )
        assert session.execute(text("SELECT current_user")).scalar_one() != "postgres"
