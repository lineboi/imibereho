"""Database safety guards (implementation plan §2.3).

`assert_safe_target` must pass before any connection is opened for a target. It checks, in order:
the URL parses; the user is not `postgres` (`superuser_name`, before connecting); the target is
known; the database name, host and ENVIRONMENT match the target's row; and the command is
allowed for the target.

Local superuser opt-in (deviation from plan §2.3, chosen by the project owner on 2026-10-25):
with `ALLOW_LOCAL_SUPERUSER=true`, a superuser connection is permitted **only** when the target is
`dev`, ENVIRONMENT is `local` and the host is local (`local_superuser_permitted`). Every other
combination (`test`, `migrations`, `production`, `ci`, a remote host) is still refused, and every
other rule (database name, host, environment, command, no downgrade on `dev`) still applies.

`verify_not_superuser` runs on every new connection (see `app.db.session`), immediately after
connecting: it refuses a role whose `rolsuper` is true (`superuser_role`) and fails closed
(`role_check_failed`) when the check itself cannot be completed.
"""

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final, Protocol, cast

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

from app.core.config import Environment, Target

LOCAL_HOSTS: Final = frozenset({"localhost", "127.0.0.1", "::1"})
ALEMBIC_COMMANDS: Final = frozenset(
    {"upgrade", "downgrade", "check", "current", "heads", "history", "stamp"}
)
SEED_COMMAND: Final = "seed"
KNOWN_COMMANDS: Final = ALEMBIC_COMMANDS | {SEED_COMMAND}
SUPERUSER_NAME: Final = "postgres"


class RefusalReason(StrEnum):
    INVALID_URL = "invalid_url"
    UNKNOWN_TARGET = "unknown_target"
    SUPERUSER_NAME = "superuser_name"
    SUPERUSER_ROLE = "superuser_role"
    ROLE_CHECK_FAILED = "role_check_failed"
    WRONG_DATABASE = "wrong_database"
    HOST_NOT_ALLOWED = "host_not_allowed"
    ENVIRONMENT_NOT_ALLOWED = "environment_not_allowed"
    UNKNOWN_COMMAND = "unknown_command"
    COMMAND_NOT_ALLOWED = "command_not_allowed"


class UnsafeDatabaseTargetError(RuntimeError):
    """The guard refused a database target. `reason` says which check refused it."""

    def __init__(self, reason: RefusalReason, message: str) -> None:
        self.reason = reason
        super().__init__(f"[{reason.value}] {message}")


@dataclass(frozen=True, slots=True)
class TargetRule:
    database: str | None  # None: any name (production)
    local_only: bool
    allowed_environments: frozenset[Environment]
    allowed_commands: frozenset[str]


TARGET_RULES: Final[dict[Target, TargetRule]] = {
    "migrations": TargetRule(
        database="imibereho_migrations",
        local_only=True,
        allowed_environments=frozenset({"local", "ci"}),
        allowed_commands=ALEMBIC_COMMANDS,
    ),
    "test": TargetRule(
        database="imibereho_test",
        local_only=True,
        allowed_environments=frozenset({"local", "ci"}),
        allowed_commands=frozenset({"upgrade", "check", "current", SEED_COMMAND}),
    ),
    "dev": TargetRule(
        database="imibereho",
        local_only=True,
        allowed_environments=frozenset({"local"}),
        allowed_commands=frozenset(
            {"upgrade", "current", "check", "heads", "history", SEED_COMMAND}
        ),
    ),
    "production": TargetRule(
        database=None,
        local_only=False,
        allowed_environments=frozenset({"production"}),
        allowed_commands=frozenset({"upgrade", "current", "check", SEED_COMMAND}),
    ),
}


def describe_url(url: str) -> str:
    """`host/dbname` for logs and CLI output. Never includes the user name or password."""
    try:
        parsed = make_url(url)
    except ArgumentError:
        return "<unparseable URL>"
    return f"{parsed.host}/{parsed.database}"


def _parse(url: str) -> URL:
    try:
        parsed = make_url(url)
    except ArgumentError as exc:
        raise UnsafeDatabaseTargetError(
            RefusalReason.INVALID_URL, "The database URL cannot be parsed."
        ) from exc
    if not parsed.drivername.startswith("postgresql") or not parsed.host or not parsed.database:
        raise UnsafeDatabaseTargetError(
            RefusalReason.INVALID_URL, "The URL must be a PostgreSQL URL with a host and database."
        )
    return parsed


LOCAL_SUPERUSER_TARGET: Final = "dev"
LOCAL_SUPERUSER_ENVIRONMENT: Final = "local"


def _is_local_host(parsed: URL) -> bool:
    return (parsed.host or "").strip("[]").lower() in LOCAL_HOSTS


def local_superuser_permitted(
    parsed: URL, target: str, environment: str, allow_local_superuser: bool
) -> bool:
    """The only case in which a superuser may connect: opted in, `dev`, `local`, local host."""
    return (
        allow_local_superuser
        and target == LOCAL_SUPERUSER_TARGET
        and environment == LOCAL_SUPERUSER_ENVIRONMENT
        and _is_local_host(parsed)
    )


def assert_safe_target(
    url: str,
    target: str,
    environment: str,
    command: str | None = None,
    *,
    allow_local_superuser: bool = False,
) -> URL:
    """Refuse unless every rule for `target` holds. Returns the parsed URL. Never connects.

    `command` is an Alembic command or `seed`; `None` means an ordinary application connection.
    `allow_local_superuser` only has an effect for target `dev` with ENVIRONMENT=local on a
    local host; everywhere else the `postgres` user is refused as before.
    """
    parsed = _parse(url)
    if (parsed.username or "").lower() == SUPERUSER_NAME and not local_superuser_permitted(
        parsed, target, environment, allow_local_superuser
    ):
        raise UnsafeDatabaseTargetError(
            RefusalReason.SUPERUSER_NAME,
            "Connections as the 'postgres' superuser are refused. Use the 'imibereho' role "
            "(ALLOW_LOCAL_SUPERUSER=true permits it only for target 'dev' with "
            "ENVIRONMENT=local on a local host).",
        )
    rule = TARGET_RULES.get(cast(Target, target))
    if rule is None:
        raise UnsafeDatabaseTargetError(RefusalReason.UNKNOWN_TARGET, f"Unknown target {target!r}.")

    if rule.database is not None and parsed.database != rule.database:
        raise UnsafeDatabaseTargetError(
            RefusalReason.WRONG_DATABASE,
            f"Target {target!r} must use database {rule.database!r}, not {parsed.database!r}.",
        )
    is_local = _is_local_host(parsed)
    if rule.local_only and not is_local:
        raise UnsafeDatabaseTargetError(
            RefusalReason.HOST_NOT_ALLOWED, f"Target {target!r} must use a local host."
        )
    if not rule.local_only and is_local:
        raise UnsafeDatabaseTargetError(
            RefusalReason.HOST_NOT_ALLOWED, f"Target {target!r} must not use a local host."
        )
    if environment not in rule.allowed_environments:
        raise UnsafeDatabaseTargetError(
            RefusalReason.ENVIRONMENT_NOT_ALLOWED,
            f"Target {target!r} is not allowed when ENVIRONMENT={environment!r}.",
        )
    if command is not None:
        if command not in KNOWN_COMMANDS:
            raise UnsafeDatabaseTargetError(
                RefusalReason.UNKNOWN_COMMAND, f"Unknown command {command!r}."
            )
        if command not in rule.allowed_commands:
            raise UnsafeDatabaseTargetError(
                RefusalReason.COMMAND_NOT_ALLOWED,
                f"Command {command!r} is not allowed on target {target!r}.",
            )
    return parsed


class _Cursor(Protocol):
    def execute(self, query: str, /) -> Any: ...
    def fetchone(self) -> Any: ...
    def close(self) -> Any: ...


class DbapiConnection(Protocol):
    def cursor(self) -> Any: ...
    def rollback(self) -> Any: ...
    def close(self) -> Any: ...


ROLE_CHECK_SQL: Final = "SELECT rolsuper FROM pg_roles WHERE rolname = current_user"


def verify_not_superuser(connection: DbapiConnection, *, allow_superuser: bool = False) -> bool:
    """Refuse a superuser connection, closing it. Fails closed if the check cannot complete.

    With `allow_superuser` (set only when `local_superuser_permitted` held for the engine), a
    superuser is accepted instead of refused. Returns whether the connected role is a superuser.
    """
    try:
        cursor: _Cursor = connection.cursor()
        try:
            cursor.execute(ROLE_CHECK_SQL)
            row = cursor.fetchone()
        finally:
            cursor.close()
        # The query implicitly opened a transaction on the raw DBAPI connection. End it, so the
        # connection is handed to SQLAlchemy idle (it must be idle to be set READ ONLY).
        connection.rollback()
    except Exception as exc:
        _close_quietly(connection.close)
        raise UnsafeDatabaseTargetError(
            RefusalReason.ROLE_CHECK_FAILED, "The superuser check could not be completed."
        ) from exc
    if row is None or row[0] is None:
        _close_quietly(connection.close)
        raise UnsafeDatabaseTargetError(
            RefusalReason.ROLE_CHECK_FAILED, "The superuser check returned no role."
        )
    is_superuser = row[0] is True
    if is_superuser and not allow_superuser:
        _close_quietly(connection.close)
        raise UnsafeDatabaseTargetError(
            RefusalReason.SUPERUSER_ROLE,
            "The connected role is a PostgreSQL superuser. Use a NOSUPERUSER role.",
        )
    return is_superuser


def _close_quietly(close: Callable[[], Any]) -> None:
    # Already refusing: a failure to close must not mask the refusal reason.
    with contextlib.suppress(Exception):
        close()
