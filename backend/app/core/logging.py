"""Privacy-safe JSON logging (implementation plan §2.8).

App logs may contain: ts, level, request_id, method, route path (never the query string),
status, duration_ms and, on a 500, the exception type and traceback.
They never contain request bodies, query strings or headers other than X-Request-ID.
"""

import json
import logging
import re
import sys
import time
import traceback
import uuid
from collections.abc import Callable, Mapping
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Final

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.constants import CONTENT_LANGUAGE, REQUEST_ID_HEADER
from app.core.errors import internal_error_response

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Only these `extra=` keys are copied into a log line. Anything else passed by a caller is dropped,
# so a careless `extra={"body": ...}` can never leak into the logs.
ALLOWED_EXTRA_FIELDS: Final = frozenset(
    {"method", "path", "status", "duration_ms", "target", "database", "server_version_num"}
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        for key in ALLOWED_EXTRA_FIELDS:
            if key in record.__dict__:
                entry[key] = record.__dict__[key]
        if record.exc_info and record.exc_info[0] is not None:
            exc_type, exc_value, exc_tb = record.exc_info
            entry["exc_type"] = exc_type.__name__
            # Frames only: file, line and function names. Neither the exception message (which
            # can echo input) nor local variable values are included.
            entry["traceback"] = [
                f"{frame.filename}:{frame.lineno} in {frame.name}"
                for frame in traceback.extract_tb(exc_tb)
            ]
            del exc_value
        return json.dumps(entry, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Send JSON lines to stdout and silence loggers that could record URLs."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    # The uvicorn access log records full URLs (query strings). It is disabled here as well as
    # with `--no-access-log`, so forgetting the flag cannot leak query strings.
    access = logging.getLogger("uvicorn.access")
    access.handlers = []
    access.propagate = False
    access.disabled = True
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    # SQL statements may carry parameters; never log them.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


_REQUEST_ID_PATTERN: Final = re.compile(r"[A-Za-z0-9._\-]{1,128}")
_REQUEST_ID_HEADER_BYTES: Final = REQUEST_ID_HEADER.lower().encode("latin-1")
_access_logger = logging.getLogger("app.request")


def _resolve_request_id(scope: Scope) -> str:
    """Echo a client-supplied X-Request-ID when it is a safe token; otherwise generate one."""
    for name, value in scope.get("headers", []):
        if name == _REQUEST_ID_HEADER_BYTES:
            candidate: str = value.decode("latin-1")
            if _REQUEST_ID_PATTERN.fullmatch(candidate):
                return candidate
            break
    return uuid.uuid4().hex


RouteResolver = Callable[[str], str | None]


def _route_path(scope: Scope, resolve: RouteResolver | None) -> str:
    """The route template (e.g. `/api/v1/district-vulnerability/{districtCode}`) for logs.

    Unmatched requests log the raw path, truncated. `scope["path"]` never holds the query string.
    """
    path = str(scope.get("path", ""))
    template = resolve(path) if resolve is not None else None
    return template if template is not None else path[:200]


class RequestContextMiddleware:
    """Outermost middleware: request ID, response headers, one access line, last-resort 500.

    It is a pure ASGI middleware so the 500 problem response still carries X-Request-ID.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        extra_headers: Mapping[str, str] | None = None,
        route_resolver: RouteResolver | None = None,
    ) -> None:
        self.app = app
        self.route_resolver = route_resolver
        self.extra_headers = [
            (name.lower().encode("latin-1"), value.encode("latin-1"))
            for name, value in (extra_headers or {}).items()
        ]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _resolve_request_id(scope)
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_holder = {"status": 500, "started": False}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                status_holder["started"] = True
                headers = MutableHeaders(scope=message)
                headers[REQUEST_ID_HEADER] = request_id
                headers["Content-Language"] = CONTENT_LANGUAGE
                for name, value in self.extra_headers:
                    headers.append(name.decode("latin-1"), value.decode("latin-1"))
                if scope.get("method") == "POST":
                    headers["Cache-Control"] = "no-store"
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            _access_logger.exception(
                "unhandled exception",
                extra={
                    "method": scope.get("method"),
                    "path": _route_path(scope, self.route_resolver),
                },
            )
            if status_holder["started"]:
                raise
            await internal_error_response()(scope, receive, send_wrapper)
        finally:
            _access_logger.info(
                "request",
                extra={
                    "method": scope.get("method"),
                    "path": _route_path(scope, self.route_resolver),
                    "status": status_holder["status"],
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            request_id_var.reset(token)
