"""Logging privacy (plan §2.8) and request IDs (contract §1)."""

import json
import logging
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.logging import JsonFormatter, configure_logging, request_id_var

SECRET_INCOME = 987654321
SECRET_QUERY = "householdSize=17&district=secretville"


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.setFormatter(JsonFormatter())

    def emit(self, record: logging.LogRecord) -> None:
        # The test client's own `httpx2` logger records the URL it *sends*. That is the caller
        # (a browser in production), not the server, so it is not part of the app's logs.
        if not record.name.startswith("httpx"):
            self.lines.append(self.format(record))


@pytest.fixture
def captured() -> Iterator[_Capture]:
    handler = _Capture()
    root = logging.getLogger()
    previous = root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    yield handler
    root.removeHandler(handler)
    root.setLevel(previous)


@pytest.fixture
def boom_app(stub_app: FastAPI) -> FastAPI:
    @stub_app.post("/_test/boom")
    def boom() -> None:
        raise RuntimeError(f"income {SECRET_INCOME} leaked")

    return stub_app


def test_formatter_emits_json_with_request_id() -> None:
    token = request_id_var.set("abc123")
    try:
        record = logging.LogRecord("x", logging.INFO, __file__, 1, "hello", None, None)
        record.__dict__.update({"status": 200, "body": "SECRET", "path": "/health"})
        entry = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert entry["request_id"] == "abc123"
    assert entry["message"] == "hello" and entry["status"] == 200 and entry["path"] == "/health"
    assert "body" not in entry, "only allow-listed extra fields are logged"


def test_body_and_query_string_never_appear_in_logs(client: TestClient, captured: _Capture) -> None:
    body = {
        "baseline": {"monthlyIncome": SECRET_INCOME, "monthlyEssentials": 1, "savings": 2},
        "shock": {"type": "income_fall", "incomeReductionPct": 20, "durationMonths": 3},
    }
    response = client.post(f"/api/v1/calculations/household-shock?{SECRET_QUERY}", json=body)
    assert response.status_code == 400  # the query parameters are unknown to this endpoint
    client.post("/api/v1/calculations/household-shock", json=body)
    text = "\n".join(captured.lines)
    assert captured.lines, "requests must be logged"
    assert str(SECRET_INCOME) not in text
    assert "secretville" not in text and "householdSize" not in text


def test_access_line_has_route_status_duration_and_request_id(
    client: TestClient, captured: _Capture
) -> None:
    response = client.get("/health", headers={"X-Request-ID": "req-42"})
    entries = [json.loads(line) for line in captured.lines]
    access = [e for e in entries if e["logger"] == "app.request"]
    assert access, entries
    line = access[-1]
    assert line["request_id"] == "req-42" == response.headers["X-Request-ID"]
    assert (line["method"], line["path"], line["status"]) == ("GET", "/health", 200)
    assert isinstance(line["duration_ms"], float)


def test_route_template_is_logged_not_the_concrete_path(
    client: TestClient, captured: _Capture
) -> None:
    client.get("/api/v1/district-vulnerability/gasabo?unknown=1")  # 400 before any lookup
    access = [json.loads(line) for line in captured.lines if '"app.request"' in line]
    assert access[-1]["path"] == "/api/v1/district-vulnerability/{districtCode}"


def test_unhandled_error_logs_type_and_frames_but_not_the_message(
    boom_app: FastAPI, captured: _Capture
) -> None:
    with TestClient(boom_app, raise_server_exceptions=False) as test_client:
        response = test_client.post("/_test/boom", headers={"X-Request-ID": "trace-me"})
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "trace-me"
    assert str(SECRET_INCOME) not in response.text
    errors = [json.loads(line) for line in captured.lines if '"exc_type"' in line]
    assert errors and errors[0]["exc_type"] == "RuntimeError"
    assert errors[0]["request_id"] == "trace-me"
    assert any("boom" in frame for frame in errors[0]["traceback"])
    assert str(SECRET_INCOME) not in "\n".join(captured.lines)


@pytest.mark.parametrize("supplied", ["abc-123", "A.B_C-9", "x" * 128])
def test_safe_client_request_id_is_echoed(client: TestClient, supplied: str) -> None:
    assert (
        client.get("/health", headers={"X-Request-ID": supplied}).headers["X-Request-ID"]
        == supplied
    )


@pytest.mark.parametrize("supplied", ["has space", "x" * 129, "<script>", "a\tb"])
def test_unsafe_client_request_id_is_replaced(client: TestClient, supplied: str) -> None:
    echoed = client.get("/health", headers={"X-Request-ID": supplied}).headers["X-Request-ID"]
    assert echoed != supplied and len(echoed) == 32


def test_request_id_is_generated_when_absent_and_unique(client: TestClient) -> None:
    first = client.get("/health").headers["X-Request-ID"]
    second = client.get("/health").headers["X-Request-ID"]
    assert first != second and len(first) == 32


def test_configure_logging_disables_the_uvicorn_access_log() -> None:
    root = logging.getLogger()
    saved = (root.handlers[:], root.level)
    try:
        configure_logging("INFO")
        access = logging.getLogger("uvicorn.access")
        assert access.disabled and not access.propagate
        assert isinstance(root.handlers[0].formatter, JsonFormatter)
        assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING
    finally:
        root.handlers, _ = saved
        root.setLevel(saved[1])
        logging.getLogger("uvicorn.access").disabled = False
