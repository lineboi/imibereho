"""BodySizeLimitMiddleware at the ASGI level (audit finding H-1, contract §1.3).

Scripted `receive` messages stand in for the server, so these tests can show exactly how much is
read before a refusal, which a client library cannot: chunked bodies, a Content-Length that
understates the body, and a client that disconnects mid-body.
"""

import asyncio
import json
from collections.abc import Sequence
from typing import Any

import pytest
from starlette.types import Message, Receive, Scope, Send

from app.core.body_limit import BodySizeLimitMiddleware

LIMIT = 100


class Recorder:
    """The wrapped app: records whether it ran and the body it was given."""

    def __init__(self) -> None:
        self.called = False
        self.body: bytes | None = None
        self.after: Message | None = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.called = True
        parts = []
        while True:
            message = await receive()
            parts.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        self.body = b"".join(parts)
        self.after = await receive()  # the next message comes from the server again
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


def run(
    messages: Sequence[Message], headers: Sequence[tuple[bytes, bytes]] = ()
) -> tuple[Recorder, list[Message], int]:
    """Run one request; returns the app recorder, what was sent and how many receives ran."""
    app = Recorder()
    middleware = BodySizeLimitMiddleware(app, limit=LIMIT)
    queue = [*messages, {"type": "http.disconnect"}]
    received = 0
    sent: list[Message] = []

    async def receive() -> Message:
        nonlocal received
        received += 1
        return queue.pop(0) if queue else {"type": "http.disconnect"}

    async def send(message: Message) -> None:
        sent.append(message)

    scope: dict[str, Any] = {
        "type": "http", "method": "POST", "path": "/x", "headers": list(headers),
    }  # fmt: skip
    asyncio.run(middleware(scope, receive, send))
    return app, sent, received


def body(data: bytes, more: bool = False) -> Message:
    return {"type": "http.request", "body": data, "more_body": more}


def status_and_problem(sent: list[Message]) -> tuple[int, dict[str, Any]]:
    start = next(m for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return start["status"], json.loads(payload)


def test_a_body_within_the_limit_reaches_the_app_unchanged() -> None:
    app, sent, _ = run([body(b"a" * 40, more=True), body(b"b" * 60)])
    assert app.called and app.body == b"a" * 40 + b"b" * 60  # exactly the limit
    assert app.after == {"type": "http.disconnect"}  # later receives go to the server
    assert next(m for m in sent if m["type"] == "http.response.start")["status"] == 200


def test_an_empty_body_passes() -> None:
    app, _, _ = run([body(b"")])
    assert app.called and app.body == b""


def test_a_declared_length_over_the_limit_is_refused_before_reading() -> None:
    app, sent, received = run([body(b"x" * 500)], headers=[(b"content-length", b"500")])
    assert not app.called and received == 0  # nothing of the body was read
    status, problem = status_and_problem(sent)
    assert status == 413 and problem["type"].endswith("/request-too-large")
    assert problem == {
        "type": "https://imibereho.example/errors/request-too-large",
        "title": "Request body too large",
        "status": 413,
        "detail": "The request body is larger than the 100-byte limit.",
    }


def test_a_chunked_body_is_refused_as_soon_as_it_passes_the_limit() -> None:
    # 1,000 chunks of 30 bytes, no Content-Length: refused on the 4th (120 > 100).
    app, sent, received = run([body(b"y" * 30, more=True) for _ in range(1_000)])
    assert not app.called and received == 4
    assert status_and_problem(sent)[0] == 413


def test_an_understated_content_length_is_not_trusted() -> None:
    app, sent, _ = run([body(b"z" * 101)], headers=[(b"content-length", b"10")])
    assert not app.called and status_and_problem(sent)[0] == 413


def test_one_byte_over_the_limit_is_refused() -> None:
    app, sent, _ = run([body(b"z" * 101)])
    assert not app.called and status_and_problem(sent)[0] == 413


@pytest.mark.parametrize(
    "headers",
    [
        [(b"content-length", b"abc")],
        [(b"content-length", b"-1")],
        [(b"content-length", b"")],
        [(b"content-length", b"1e3")],
        [(b"content-length", b"5"), (b"content-length", b"6")],  # conflicting
        [(b"content-length", b"5, 6")],
    ],
)
def test_malformed_or_conflicting_content_length_is_400(
    headers: list[tuple[bytes, bytes]],
) -> None:
    app, sent, received = run([body(b"hello")], headers=headers)
    assert not app.called and received == 0
    status, problem = status_and_problem(sent)
    assert status == 400 and problem["type"].endswith("/malformed-request")
    assert problem["detail"] == "The Content-Length header is not valid."


def test_a_repeated_identical_content_length_is_accepted() -> None:
    app, _, _ = run([body(b"hello")], headers=[(b"Content-Length", b"5, 5")])
    assert app.called and app.body == b"hello"


def test_an_absurdly_long_content_length_is_413_not_a_crash() -> None:
    app, sent, received = run([body(b"")], headers=[(b"content-length", b"9" * 5_000)])
    assert not app.called and received == 0 and status_and_problem(sent)[0] == 413


def test_a_client_that_disconnects_mid_body_gets_nothing() -> None:
    app, sent, _ = run([body(b"a" * 10, more=True), {"type": "http.disconnect"}])
    assert not app.called and sent == []


def test_the_refusal_is_small() -> None:
    _, sent, _ = run([body(b"x" * 10_000)])
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    assert len(payload) < 300


def test_other_scopes_pass_through() -> None:
    seen: list[str] = []

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        seen.append(scope["type"])

    async def receive() -> Message:  # pragma: no cover - never called for lifespan
        raise AssertionError

    async def send(message: Message) -> None:  # pragma: no cover
        raise AssertionError

    asyncio.run(BodySizeLimitMiddleware(app, limit=LIMIT)({"type": "lifespan"}, receive, send))
    assert seen == ["lifespan"]


def test_the_limit_must_be_positive() -> None:
    with pytest.raises(ValueError, match="limit"):
        BodySizeLimitMiddleware(Recorder(), limit=0)
