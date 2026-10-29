"""Request-body size limit (contract §1.3: 413 `request-too-large`; audit finding H-1).

A pure ASGI middleware, so it runs before FastAPI buffers or parses anything:

- A declared `Content-Length` above the limit is refused at once, before any body is read.
- Malformed or conflicting `Content-Length` values (not digits, or several different values)
  are refused with 400 `malformed-request`.
- The header is never trusted: the body is read here, counting bytes, and the request is refused
  as soon as the count passes the limit. That covers chunked bodies and a `Content-Length` that
  understates the body. At most `limit` bytes are ever held.
- An accepted body is handed to the app unchanged, as one `http.request` message; later
  `receive()` calls (for example `http.disconnect`) go to the server as usual.
- A client that disconnects mid-body gets no response, and the app is not called.

Nothing about the body is logged.
"""

from collections.abc import Iterable
from typing import Final

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import problem_response

_CONTENT_LENGTH: Final = b"content-length"
_DIGITS: Final = frozenset(b"0123456789")
_MAX_LENGTH_DIGITS: Final = 18  # 10^18 bytes: any longer Content-Length is "too large"
_HUGE: Final = 10**18


class _Malformed(Exception):
    pass


def _declared_length(headers: Iterable[tuple[bytes, bytes]]) -> int | None:
    """The request's Content-Length, `None` without one; `_Malformed` if it cannot be trusted."""
    values = {
        value.strip()
        for name, value in headers
        if name.lower() == _CONTENT_LENGTH
        for value in value.split(b",")  # "5, 5" is one header repeated (RFC 9110 §8.6)
    }
    if not values:
        return None
    if len(values) != 1:
        raise _Malformed
    (value,) = values
    if not value or not set(value) <= _DIGITS:
        raise _Malformed
    if len(value) > _MAX_LENGTH_DIGITS:
        return _HUGE  # far beyond any limit; never handed to int() (Python caps digit strings)
    return int(value)


def _too_large(limit: int) -> JSONResponse:
    return problem_response(
        "request-too-large",
        "Request body too large",
        413,
        f"The request body is larger than the {limit}-byte limit.",
        headers={"Connection": "close"},
    )


def _malformed_length() -> JSONResponse:
    return problem_response(
        "malformed-request",
        "Malformed request",
        400,
        "The Content-Length header is not valid.",
        headers={"Connection": "close"},
    )


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, *, limit: int) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1 byte")
        self.app = app
        self.limit = limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            declared = _declared_length(scope.get("headers", ()))
        except _Malformed:
            await _malformed_length()(scope, receive, send)
            return
        if declared is not None and declared > self.limit:
            await _too_large(self.limit)(scope, receive, send)
            return

        chunks: list[bytes] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return  # the client left before the body ended: nobody to answer
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.limit:
                await _too_large(self.limit)(scope, receive, send)
                return
            chunks.append(chunk)
            if not message.get("more_body", False):
                break

        body = b"".join(chunks)
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
