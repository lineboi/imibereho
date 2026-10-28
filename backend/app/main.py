"""Application construction.

`create_app(target)` takes an explicit database target (plan §2.3, §2.10). Importing this module
reads no settings and opens no connection. `uvicorn app.main:app` resolves `app` lazily: it uses
target `dev` when ENVIRONMENT=local and `production` when ENVIRONMENT=production, and refuses to
start for any other environment. Tests call `create_app("test", ...)` and never read
DATABASE_URL.

Before the server accepts requests, the lifespan opens one connection: the superuser check runs
on it (fail closed) and the PostgreSQL server version is logged once (plan §2.11).
"""

import logging
import re
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import cache
from typing import Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import iter_route_contexts
from starlette.routing import compile_path

from app.api.router import api_router
from app.core.config import Settings, Target, get_settings
from app.core.constants import OPENAPI_VERSION, REQUEST_ID_HEADER
from app.core.errors import register_exception_handlers
from app.core.logging import RequestContextMiddleware, configure_logging
from app.data import DATASETS
from app.db.migrate import head_revision
from app.db.readiness import Readiness, check_readiness
from app.db.session import Database

logger = logging.getLogger("app.startup")

SECURITY_HEADERS: Final = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}

DESCRIPTION: Final = (
    "Imibereho: an illustrative household financial-resilience demo for Rwanda.\n\n"
    "**Every figure is synthetic demo data under concept methodology v0.1, not official "
    "statistics.** Data responses carry `meta.isIllustrative: true`. No account is needed and no "
    "citizen data is stored: calculation bodies are processed, then discarded, never logged."
)


def create_app(
    target: Target,
    *,
    settings: Settings | None = None,
    database: Database | None = None,
    verify_database_on_startup: bool = True,
) -> FastAPI:
    settings = settings or get_settings()
    database = database or Database.for_target(settings, target)
    if database.target != target:
        raise ValueError("the database was built for a different target")

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        if verify_database_on_startup:
            if database.local_superuser_permitted:
                logger.warning(
                    "ALLOW_LOCAL_SUPERUSER is on: a PostgreSQL superuser is permitted for this "
                    "local dev server only. CI and production run as a NOSUPERUSER role."
                )
            version = database.server_version_num()  # first connection: superuser check runs
            logger.info(
                "database verified",
                extra={
                    "target": target,
                    "database": database.description,
                    "server_version_num": version,
                },
            )
        try:
            yield
        finally:
            database.dispose()

    app = FastAPI(
        title="Imibereho API",
        version=OPENAPI_VERSION,
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    head = head_revision()
    app.state.database = database
    app.state.settings = settings

    def readiness() -> Readiness:
        return check_readiness(database, head, DATASETS)

    app.state.readiness = readiness

    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        # Authorization carries the bearer token (contract §11.8); Idempotency-Key makes a tracker
        # POST safe to retry (§11.10).
        allow_headers=["Content-Type", "Authorization", "Idempotency-Key", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
        allow_credentials=False,
    )
    # Added last, so it is the outermost middleware: every response, including CORS preflights
    # and the last-resort 500, carries X-Request-ID and Content-Language.
    app.add_middleware(
        RequestContextMiddleware,
        extra_headers=SECURITY_HEADERS,
        route_resolver=RouteTemplates(app),
    )
    app.include_router(api_router)
    return app


class RouteTemplates:
    """Maps a request path to its full route template, for privacy-safe access logs.

    Built from the effective (prefixed) paths on first use, after every router is included.
    """

    def __init__(self, app: FastAPI) -> None:
        self._app = app
        self._compiled: list[tuple[re.Pattern[str], str]] | None = None

    def __call__(self, path: str) -> str | None:
        if self._compiled is None:
            self._compiled = [
                (compile_path(context.path)[0], context.path)
                for context in iter_route_contexts(self._app.routes)
                if context.path
            ]
        for pattern, template in self._compiled:
            if pattern.match(path):
                return template
        return None


class StartupRefusedError(RuntimeError):
    pass


@cache
def _server_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    targets: dict[str, Target] = {"local": "dev", "production": "production"}
    target = targets.get(settings.environment)
    if target is None:
        raise StartupRefusedError(
            f"The server does not run with ENVIRONMENT={settings.environment!r}; "
            "use 'local' or 'production'."
        )
    return create_app(target, settings=settings)


def __getattr__(name: str) -> FastAPI:
    if name == "app":
        return _server_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
