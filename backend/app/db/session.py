"""Engines and sessions, built only from a guarded URL for an explicit target.

Every new DBAPI connection runs the superuser check (`verify_not_superuser`) before SQLAlchemy
hands it out, so no code path (app, migrations, seed, tests) can use a superuser connection.
"""

import logging
import weakref
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Final

from fastapi import Request
from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, Target
from app.db.guards import (
    assert_safe_target,
    describe_url,
    local_superuser_permitted,
    verify_not_superuser,
)

CONNECT_TIMEOUT_SECONDS: Final = 5


logger = logging.getLogger("app.db")
# Engines built under the dev-only ALLOW_LOCAL_SUPERUSER exception.
_LOCAL_SUPERUSER_ENGINES: "weakref.WeakSet[Engine]" = weakref.WeakSet()


def _on_connect(dbapi_connection: Any, _record: Any) -> None:
    verify_not_superuser(dbapi_connection)


def _on_connect_local_superuser_permitted(dbapi_connection: Any, _record: Any) -> None:
    # Still fails closed if the role check cannot run; a superuser is accepted, with a warning.
    if verify_not_superuser(dbapi_connection, allow_superuser=True):
        logger.warning(
            "connected as a PostgreSQL superuser under ALLOW_LOCAL_SUPERUSER (local dev only)"
        )


def create_guarded_engine(
    url: str,
    target: Target,
    environment: str,
    command: str | None = None,
    *,
    allow_local_superuser: bool = False,
) -> Engine:
    """Guard `url` for `target` (no connection yet), then build an engine with the role check."""
    parsed = assert_safe_target(
        url, target, environment, command, allow_local_superuser=allow_local_superuser
    )
    permitted = local_superuser_permitted(parsed, target, environment, allow_local_superuser)
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_timeout=10,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS, "application_name": "imibereho"},
    )
    if permitted:
        _LOCAL_SUPERUSER_ENGINES.add(engine)
    listener = _on_connect_local_superuser_permitted if permitted else _on_connect
    event.listen(engine, "connect", listener)
    return engine


class Database:
    """One engine and session factory for one guarded target."""

    def __init__(self, engine: Engine, target: Target) -> None:
        self.engine = engine
        self.target = target
        self.description = describe_url(engine.url.render_as_string(hide_password=True))
        self.local_superuser_permitted = engine in _LOCAL_SUPERUSER_ENGINES
        self._sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        # psycopg opens every transaction on this engine as READ ONLY. Unlike an eager
        # `SET TRANSACTION`, it connects lazily, on the first query, so a request that fails
        # validation never opens a connection (contract §1.3: validation before lookup).
        self._read_only_sessions = sessionmaker(
            bind=engine.execution_options(postgresql_readonly=True),
            autoflush=False,
            expire_on_commit=False,
        )

    @classmethod
    def for_target(cls, settings: Settings, target: Target) -> "Database":
        url = settings.database_url_for(target)
        engine = create_guarded_engine(
            url,
            target,
            settings.environment,
            allow_local_superuser=settings.allow_local_superuser,
        )
        return cls(engine, target)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """A session that rolls back on error and is always closed."""
        with self._managed(self._sessions) as session:
            yield session

    @staticmethod
    @contextmanager
    def _managed(factory: sessionmaker[Session]) -> Iterator[Session]:
        session = factory()
        try:
            yield session
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def read_only_session(self) -> Iterator[Session]:
        """A session whose transaction PostgreSQL itself refuses to write in.

        Every API request uses this except the two account endpoints (`get_write_session`),
        which are the only ones that store data a person sends (contract §11.8).
        """
        with self._managed(self._read_only_sessions) as session:
            try:
                yield session
            finally:
                session.rollback()

    def server_version_num(self) -> int:
        with self.engine.connect() as connection:
            value = connection.execute(text("SHOW server_version_num")).scalar_one()
        return int(value)

    def dispose(self) -> None:
        self.engine.dispose()


def get_database(request: Request) -> Database:
    database = request.app.state.database
    if not isinstance(database, Database):
        raise RuntimeError("app.state.database is not configured")
    return database


def get_read_session(request: Request) -> Iterator[Session]:
    """FastAPI dependency: one read-only session per request, closed afterwards."""
    with get_database(request).read_only_session() as session:
        yield session


def get_write_session(request: Request) -> Iterator[Session]:
    """FastAPI dependency for the account endpoints only (contract §11.8): one writable session.

    The service commits explicitly; anything not committed is rolled back when it closes. Every
    other endpoint keeps `get_read_session`.
    """
    with get_database(request).session() as session:
        yield session
