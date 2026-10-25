"""Database safety guards (plan §2.3): every rule and every refusal.

The post-connect role check is exercised with stubbed DBAPI connections.
"""

from typing import Any

import pytest

from app.db.guards import (
    ROLE_CHECK_SQL,
    RefusalReason,
    UnsafeDatabaseTargetError,
    assert_safe_target,
    describe_url,
    verify_not_superuser,
)

BASE = "postgresql+psycopg://imibereho:pw@{host}:5432/{db}"
TARGET_DB = {
    "migrations": "imibereho_migrations",
    "test": "imibereho_test",
    "dev": "imibereho",
}


def url(db: str, host: str = "localhost", user: str = "imibereho") -> str:
    return f"postgresql+psycopg://{user}:pw@{host}:5432/{db}"


def refused(reason: RefusalReason, *args: Any) -> None:
    with pytest.raises(UnsafeDatabaseTargetError) as excinfo:
        assert_safe_target(*args)
    assert excinfo.value.reason is reason, excinfo.value


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
@pytest.mark.parametrize("target", ["migrations", "test", "dev"])
def test_local_targets_accept_their_own_database_on_local_hosts(target: str, host: str) -> None:
    assert_safe_target(url(TARGET_DB[target], host), target, "local")


def test_production_accepts_a_remote_host() -> None:
    assert_safe_target(
        url("anything_render_assigns", "db.render.example"), "production", "production"
    )


@pytest.mark.parametrize(
    ("target", "wrong_db"),
    [
        ("migrations", "imibereho"),
        ("migrations", "imibereho_test"),
        ("test", "imibereho"),
        ("test", "imibereho_migrations"),
        ("dev", "imibereho_test"),
        ("dev", "postgres"),
    ],
)
def test_wrong_database_name_is_refused(target: str, wrong_db: str) -> None:
    refused(RefusalReason.WRONG_DATABASE, url(wrong_db), target, "local")


@pytest.mark.parametrize("target", ["migrations", "test", "dev"])
def test_non_local_host_is_refused_for_local_targets(target: str) -> None:
    refused(
        RefusalReason.HOST_NOT_ALLOWED, url(TARGET_DB[target], "db.render.example"), target, "local"
    )


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
def test_local_host_is_refused_for_production(host: str) -> None:
    refused(RefusalReason.HOST_NOT_ALLOWED, url("imibereho", host), "production", "production")


@pytest.mark.parametrize("target", ["migrations", "test", "dev"])
def test_production_environment_refuses_non_production_targets(target: str) -> None:
    refused(RefusalReason.ENVIRONMENT_NOT_ALLOWED, url(TARGET_DB[target]), target, "production")


def test_dev_requires_the_local_environment() -> None:
    refused(RefusalReason.ENVIRONMENT_NOT_ALLOWED, url("imibereho"), "dev", "ci")


def test_production_target_requires_the_production_environment() -> None:
    refused(
        RefusalReason.ENVIRONMENT_NOT_ALLOWED, url("x", "db.render.example"), "production", "local"
    )


@pytest.mark.parametrize("target", ["dev", "test", "production"])
def test_downgrade_is_refused_except_on_migrations(target: str) -> None:
    db_url = (
        url("imibereho", "db.render.example") if target == "production" else url(TARGET_DB[target])
    )
    env = "production" if target == "production" else "local"
    refused(RefusalReason.COMMAND_NOT_ALLOWED, db_url, target, env, "downgrade")
    refused(RefusalReason.COMMAND_NOT_ALLOWED, db_url, target, env, "stamp")


def test_downgrade_is_allowed_on_migrations() -> None:
    assert_safe_target(url("imibereho_migrations"), "migrations", "ci", "downgrade")


def test_seeding_the_migrations_database_is_refused() -> None:
    refused(
        RefusalReason.COMMAND_NOT_ALLOWED,
        url("imibereho_migrations"),
        "migrations",
        "local",
        "seed",
    )


def test_unknown_command_is_refused() -> None:
    refused(RefusalReason.UNKNOWN_COMMAND, url("imibereho_test"), "test", "local", "drop")


def test_unknown_target_is_refused() -> None:
    refused(RefusalReason.UNKNOWN_TARGET, url("imibereho"), "staging", "local")


@pytest.mark.parametrize("bad", ["not a url", "sqlite:///x.db", "postgresql+psycopg://u:p@/db"])
def test_invalid_urls_are_refused(bad: str) -> None:
    refused(RefusalReason.INVALID_URL, bad, "test", "local")


@pytest.mark.parametrize(
    ("target", "env", "db_url"),
    [
        ("dev", "local", url("imibereho", user="postgres")),
        ("test", "local", url("imibereho_test", user="postgres")),
        ("migrations", "local", url("imibereho_migrations", user="postgres")),
        ("production", "production", url("x", "db.render.example", user="postgres")),
        ("test", "local", url("imibereho_test", user="Postgres")),
    ],
)
def test_postgres_user_name_is_refused_before_any_other_rule(
    target: str, env: str, db_url: str
) -> None:
    """Proves the name check runs first: it is a pure URL check and opens no connection."""
    refused(RefusalReason.SUPERUSER_NAME, db_url, target, env, "upgrade")


def test_describe_url_never_includes_credentials() -> None:
    described = describe_url(
        "postgresql+psycopg://imibereho:topsecret@localhost:5432/imibereho_test"
    )
    assert described == "localhost/imibereho_test"
    assert describe_url("::::") == "<unparseable URL>"


# --- Role check after connecting (stubbed DBAPI connections) ---


class StubCursor:
    def __init__(self, row: Any, fail: bool) -> None:
        self.row, self.fail, self.queries = row, fail, []  # type: ignore[var-annotated]

    def execute(self, query: str) -> None:
        self.queries.append(query)
        if self.fail:
            raise RuntimeError("permission denied")

    def fetchone(self) -> Any:
        return self.row

    def close(self) -> None:
        pass


class StubConnection:
    def __init__(self, row: Any = (False,), fail: bool = False) -> None:
        self.cursor_obj = StubCursor(row, fail)
        self.closed = False
        self.rolled_back = False

    def cursor(self) -> StubCursor:
        return self.cursor_obj

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


def test_non_superuser_role_is_accepted() -> None:
    """Proves the check is not over-broad."""
    connection = StubConnection((False,))
    verify_not_superuser(connection)
    assert not connection.closed
    assert connection.cursor_obj.queries == [ROLE_CHECK_SQL]


def test_accepted_connection_is_left_idle_for_sqlalchemy() -> None:
    """Regression: the check's implicit transaction must end, or SQLAlchemy cannot set the
    connection READ ONLY ("can't change 'read_only' now: connection in transaction status
    INTRANS"), which broke every API read and /ready on a real database."""
    connection = StubConnection((False,))
    verify_not_superuser(connection)
    assert connection.rolled_back


def test_superuser_role_is_refused_and_the_connection_closed() -> None:
    """Proves the rolsuper check catches a superuser under any name and closes what it opened."""
    connection = StubConnection((True,))
    with pytest.raises(UnsafeDatabaseTargetError) as excinfo:
        verify_not_superuser(connection)
    assert excinfo.value.reason is RefusalReason.SUPERUSER_ROLE
    assert connection.closed


@pytest.mark.parametrize(
    "connection", [StubConnection(fail=True), StubConnection(row=None), StubConnection(row=(None,))]
)
def test_role_check_fails_closed(connection: StubConnection) -> None:
    """Error paths a real database cannot easily produce still refuse."""
    with pytest.raises(UnsafeDatabaseTargetError) as excinfo:
        verify_not_superuser(connection)
    assert excinfo.value.reason is RefusalReason.ROLE_CHECK_FAILED
    assert connection.closed


def test_engine_runs_the_role_check_on_every_new_connection() -> None:
    """The guarded engine registers the check as a `connect` listener, so no path skips it."""
    from sqlalchemy import event

    from app.db.session import _on_connect, create_guarded_engine

    engine = create_guarded_engine(url("imibereho_test"), "test", "local")
    try:
        assert event.contains(engine, "connect", _on_connect)
    finally:
        engine.dispose()


def test_guarded_engine_refuses_before_building_an_engine() -> None:
    from app.db.session import create_guarded_engine

    with pytest.raises(UnsafeDatabaseTargetError) as excinfo:
        create_guarded_engine(url("imibereho"), "test", "local")
    assert excinfo.value.reason is RefusalReason.WRONG_DATABASE


# --- ALLOW_LOCAL_SUPERUSER: dev-only opt-in (project-owner decision, 2026-10-25) ---

PG_DEV = "postgresql+psycopg://postgres:pw@{host}:5432/imibereho"


def opt_in_refused(reason: RefusalReason, *args: Any, **kwargs: Any) -> None:
    with pytest.raises(UnsafeDatabaseTargetError) as excinfo:
        assert_safe_target(*args, allow_local_superuser=True, **kwargs)
    assert excinfo.value.reason is reason, excinfo.value


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
@pytest.mark.parametrize("command", [None, "upgrade", "seed", "current"])
def test_opt_in_permits_postgres_only_for_local_dev(host: str, command: str | None) -> None:
    assert_safe_target(
        PG_DEV.format(host=host), "dev", "local", command, allow_local_superuser=True
    )


def test_without_the_opt_in_dev_still_refuses_postgres() -> None:
    refused(RefusalReason.SUPERUSER_NAME, PG_DEV.format(host="localhost"), "dev", "local")


@pytest.mark.parametrize("command", [None, "upgrade", "seed"])
def test_regression_production_rejects_postgres_even_with_the_opt_in(command: str | None) -> None:
    production_url = url("render_db", "db.render.example", user="postgres")
    refused(RefusalReason.SUPERUSER_NAME, production_url, "production", "production", command)
    opt_in_refused(
        RefusalReason.SUPERUSER_NAME, production_url, "production", "production", command
    )


@pytest.mark.parametrize(
    ("target", "environment", "db_url"),
    [
        ("test", "local", url("imibereho_test", user="postgres")),
        ("migrations", "local", url("imibereho_migrations", user="postgres")),
        ("test", "ci", url("imibereho_test", user="postgres")),
        ("dev", "ci", url("imibereho", user="postgres")),
        ("dev", "production", url("imibereho", user="postgres")),
        ("dev", "local", url("imibereho", "db.remote.example", user="postgres")),
    ],
)
def test_opt_in_never_applies_outside_local_dev(target: str, environment: str, db_url: str) -> None:
    """Test isolation and CI keep a non-superuser; only `dev` + `local` + local host qualifies."""
    opt_in_refused(RefusalReason.SUPERUSER_NAME, db_url, target, environment, "upgrade")


def test_opt_in_does_not_relax_any_other_rule() -> None:
    opt_in_refused(
        RefusalReason.WRONG_DATABASE, url("imibereho_test", user="postgres"), "dev", "local"
    )
    opt_in_refused(
        RefusalReason.COMMAND_NOT_ALLOWED,
        PG_DEV.format(host="localhost"),
        "dev",
        "local",
        "downgrade",
    )
    opt_in_refused(
        RefusalReason.COMMAND_NOT_ALLOWED, PG_DEV.format(host="localhost"), "dev", "local", "stamp"
    )


def test_role_check_accepts_a_superuser_only_when_allowed() -> None:
    connection = StubConnection((True,))
    assert verify_not_superuser(connection, allow_superuser=True) is True
    assert not connection.closed
    assert verify_not_superuser(StubConnection((False,)), allow_superuser=True) is False


@pytest.mark.parametrize("connection", [StubConnection(fail=True), StubConnection(row=None)])
def test_role_check_still_fails_closed_under_the_opt_in(connection: StubConnection) -> None:
    with pytest.raises(UnsafeDatabaseTargetError) as excinfo:
        verify_not_superuser(connection, allow_superuser=True)
    assert excinfo.value.reason is RefusalReason.ROLE_CHECK_FAILED
    assert connection.closed


def test_engine_wiring_follows_the_opt_in() -> None:
    from sqlalchemy import event

    from app.db.session import (
        _on_connect,
        _on_connect_local_superuser_permitted,
        create_guarded_engine,
    )

    permitted = create_guarded_engine(
        PG_DEV.format(host="localhost"), "dev", "local", allow_local_superuser=True
    )
    ordinary = create_guarded_engine(url("imibereho"), "dev", "local", allow_local_superuser=True)
    try:
        assert event.contains(permitted, "connect", _on_connect_local_superuser_permitted)
        assert not event.contains(permitted, "connect", _on_connect)
        # The flag alone changes nothing for a non-`postgres` URL's name check, but the engine
        # is still opted in for dev/local, so a superuser under another name is warned, not refused.
        assert event.contains(ordinary, "connect", _on_connect_local_superuser_permitted)
    finally:
        permitted.dispose()
        ordinary.dispose()

    with pytest.raises(UnsafeDatabaseTargetError):
        create_guarded_engine(
            url("imibereho_test", user="postgres"), "test", "local", allow_local_superuser=True
        )
