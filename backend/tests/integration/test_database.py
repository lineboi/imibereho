"""Real-database behaviour: sessions, read-only enforcement, failures, version evidence."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError

from app.core.config import Settings
from app.data import DATASETS
from app.db.migrate import head_revision
from app.db.readiness import check_readiness
from app.db.session import Database, create_guarded_engine


def test_server_version_is_recorded(test_database: Database) -> None:
    """Plan §2.11 evidence: the suite runs on PostgreSQL 16+ (18 locally, 16 in CI)."""
    version = test_database.server_version_num()
    assert version >= 160000
    with test_database.session() as session:
        print("SELECT version():", session.execute(text("SELECT version()")).scalar_one())


def test_application_role_is_not_a_superuser(test_database: Database) -> None:
    with test_database.session() as session:
        is_super = session.execute(
            text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
        ).scalar_one()
    assert is_super is False


def test_read_only_session_refuses_writes(test_database: Database) -> None:
    """API sessions cannot write, so no request can persist citizen data (Q-02)."""
    with test_database.read_only_session() as session, pytest.raises(DBAPIError) as excinfo:
        session.execute(text("UPDATE districts SET name_rw = 'x' WHERE code = 'gasabo'"))
    assert "read-only" in str(excinfo.value.orig).lower()


def test_session_rolls_back_on_error_and_is_closed(test_database: Database) -> None:
    pool = test_database.engine.pool
    checked_out_before = pool.checkedout()  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError), test_database.session() as session:
        session.execute(text("SELECT 1"))
        raise RuntimeError("boom")
    assert pool.checkedout() == checked_out_before  # type: ignore[attr-defined]


def test_read_only_session_returns_its_connection(test_database: Database) -> None:
    pool = test_database.engine.pool
    before = pool.checkedout()  # type: ignore[attr-defined]
    with test_database.read_only_session() as session:
        session.execute(text("SELECT 1"))
        assert pool.checkedout() == before + 1  # type: ignore[attr-defined]
    assert pool.checkedout() == before  # type: ignore[attr-defined]


def test_unreachable_database_fails_fast_and_readiness_reports_it(db_settings: Settings) -> None:
    url = db_settings.database_url_for("test").replace(":5432/", ":1/")  # nothing listens on port 1
    database = Database(create_guarded_engine(url, "test", db_settings.environment), "test")
    try:
        with pytest.raises(OperationalError):
            database.server_version_num()
        readiness = check_readiness(database, head_revision(), DATASETS)
        assert readiness.as_checks() == {
            "database": "failed",
            "migrations": "failed",
            "seed": "failed",
        }
    finally:
        database.dispose()


def test_readiness_on_the_seeded_database(test_database: Database) -> None:
    assert check_readiness(test_database, head_revision(), DATASETS).ready


def test_readiness_detects_a_stale_migration(test_database: Database) -> None:
    readiness = check_readiness(test_database, "not-the-head", DATASETS)
    assert readiness.as_checks() == {"database": "ok", "migrations": "failed", "seed": "failed"}
