"""Request limits through the whole app (audit finding H-1, contract §1.3).

1. `activeCopingLevers` holds at most 3 entries (the catalogue's size), for the resilience
   simulation and, through the same request model, the saved resilience plan.
2. Every request body is capped (`MAX_REQUEST_BODY_BYTES`, default 65,536): a larger body gets
   413 `request-too-large` before FastAPI parses it. Tests use a small limit so the payloads stay
   small; `tests/unit/test_body_limit.py` covers the ASGI details (chunks, disconnects).

All of this runs on the DB-free stub app: the simulation is stateless.
"""

import copy
import json
from collections.abc import Iterator
from typing import Any, Final

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import MAX_REQUEST_BODY_BYTES_DEFAULT
from app.main import create_app
from app.schemas.resilience import COPING_LEVERS_MAX
from tests.conftest import make_settings
from tests.helpers import assert_problem, raw_json

URL: Final = "/api/v1/calculations/resilience-simulation"
PLAN_URL: Final = "/api/v1/user/resilience-plan"
LEVERS: Final = ["trim_non_essentials", "seasonal_agro_swaps", "ibimina_tontine"]
PDF_REQUEST: Final[dict[str, Any]] = {
    "baseline": {"monthlyIncome": 180_000, "monthlyEssentials": 150_000, "savings": 60_000},
    "shock": {"type": "income_drop", "incomeReductionPct": 20, "durationMonths": 3},
    "activeCopingLevers": LEVERS,
}
SMALL_LIMIT: Final = 2_048
JSON: Final = {"content-type": "application/json"}


def with_levers(levers: object) -> dict[str, Any]:
    body = copy.deepcopy(PDF_REQUEST)
    body["activeCopingLevers"] = levers
    return body


def client_with(**settings: object) -> Iterator[TestClient]:
    app = create_app("test", settings=make_settings(**settings), verify_database_on_startup=False)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def small(client: TestClient) -> Iterator[TestClient]:
    """The stub app with a 2,048-byte body limit."""
    yield from client_with(max_request_body_bytes=SMALL_LIMIT)


# --- 1. activeCopingLevers holds at most 3 entries ---


def test_the_bound_is_the_catalogue_size(client: TestClient) -> None:
    catalog = raw_json(client.get("/api/v1/shocks/catalog"))
    assert COPING_LEVERS_MAX == len(catalog["copingLevers"]) == 3


@pytest.mark.parametrize("count", [0, 1, 3])
def test_zero_to_three_levers_are_accepted(client: TestClient, count: int) -> None:
    response = client.post(URL, json=with_levers(LEVERS[:count]))
    assert response.status_code == 200, response.text


def test_the_pdf_example_is_unchanged(client: TestClient) -> None:
    data = raw_json(client.post(URL, json=PDF_REQUEST))
    assert {k: data[k] for k in ("rawMonthlyGap", "copingReliefMonthly", "lumpSumSupport",
                                 "netMonthlyGap", "totalEffectiveBuffer")} == {
        "rawMonthlyGap": 6_000, "copingReliefMonthly": 17_200, "lumpSumSupport": 25_000,
        "netMonthlyGap": 0, "totalEffectiveBuffer": 85_000,
    }  # fmt: skip
    assert (data["runwayMonths"], data["resilienceScore"], data["scoreChange"]) == (14.2, 95, 28)


@pytest.mark.parametrize(
    "levers",
    [
        [*LEVERS, "trim_non_essentials"],  # 4 entries, one a duplicate
        ["ibimina_tontine"] * 4,
        ["not_a_lever"] * 4,
    ],
)
def test_four_entries_are_one_too_long_error(client: TestClient, levers: list[str]) -> None:
    response = client.post(URL, json=with_levers(levers))
    assert_problem(response, 422, "validation", ("activeCopingLevers", "too_long"))
    assert len(raw_json(response)["errors"]) == 1


def test_a_huge_list_is_one_bounded_error(client: TestClient) -> None:
    """The audit's case: 100,000 levers gave 99,999 errors and a 10 MB response."""
    for large in client_with(max_request_body_bytes=1_048_576):  # let the body through
        body = json.dumps(with_levers(["ibimina_tontine"] * 40_000))
        assert len(body) > 500_000
        response = large.post(URL, content=body, headers=JSON)
        assert_problem(response, 422, "validation", ("activeCopingLevers", "too_long"))
        assert len(raw_json(response)["errors"]) == 1 and len(response.content) < 2_000


def test_entry_rules_are_unchanged(client: TestClient) -> None:
    assert_problem(client.post(URL, json=with_levers(["not_a_lever"])), 422, "validation",
                   ("activeCopingLevers.0", "unknown_value"))  # fmt: skip
    assert_problem(client.post(URL, json=with_levers([7])), 422, "validation",
                   ("activeCopingLevers.0", "unknown_value"))  # fmt: skip
    duplicate = client.post(URL, json=with_levers(["ibimina_tontine", "ibimina_tontine"]))
    assert_problem(duplicate, 422, "validation", ("activeCopingLevers.1", "unknown_value"))
    assert_problem(client.post(URL, json=with_levers("ibimina_tontine")), 422, "validation",
                   ("activeCopingLevers", "unknown_value"))  # fmt: skip


def test_the_saved_plan_shares_the_bound() -> None:
    schema = create_app(
        "test", settings=make_settings(), verify_database_on_startup=False
    ).openapi()["components"]["schemas"]["ResilienceSimulationRequest"]
    assert schema["properties"]["activeCopingLevers"]["maxItems"] == 3


# --- 2. Request-body size limit ---


def test_the_default_limit(client: TestClient) -> None:
    assert make_settings().max_request_body_bytes == MAX_REQUEST_BODY_BYTES_DEFAULT == 65_536


@pytest.mark.parametrize("value", [0, 1_023, 1_048_577])
def test_the_limit_is_bounded(value: int) -> None:
    with pytest.raises(ValidationError):
        make_settings(max_request_body_bytes=value)


def padded(size: int) -> bytes:
    """The PDF request, valid JSON padded with trailing whitespace to exactly `size` bytes."""
    body = json.dumps(PDF_REQUEST).encode()
    assert len(body) <= size
    return body + b" " * (size - len(body))


def test_a_normal_request_below_the_limit(small: TestClient) -> None:
    assert small.post(URL, json=PDF_REQUEST).status_code == 200


def test_a_body_exactly_at_the_limit_is_accepted(small: TestClient) -> None:
    response = small.post(URL, content=padded(SMALL_LIMIT), headers=JSON)
    assert response.status_code == 200, response.text
    assert raw_json(response)["rawMonthlyGap"] == 6_000  # parsed intact


def test_one_byte_over_with_a_content_length_is_413(small: TestClient) -> None:
    response = small.post(URL, content=padded(SMALL_LIMIT + 1), headers=JSON)
    assert_problem(response, 413, "request-too-large")
    assert raw_json(response)["detail"] == "The request body is larger than the 2048-byte limit."
    assert len(response.content) < 300  # no validation-error listing
    assert response.headers["X-Request-ID"] and response.headers["Content-Language"] == "en"


def test_an_oversized_chunked_body_is_413(small: TestClient) -> None:
    def chunks() -> Iterator[bytes]:
        yield padded(SMALL_LIMIT)
        yield b" "

    response = small.post(URL, content=chunks(), headers=JSON)  # no Content-Length
    assert "content-length" not in {k.lower() for k in response.request.headers}
    assert_problem(response, 413, "request-too-large")


def test_a_malformed_content_length_is_400(small: TestClient) -> None:
    response = small.post(URL, content=b"{}", headers={**JSON, "Content-Length": "abc"})
    assert_problem(response, 400, "malformed-request")
    assert raw_json(response)["detail"] == "The Content-Length header is not valid."


def test_the_413_is_readable_by_an_allowed_browser_origin(small: TestClient) -> None:
    origin = "http://localhost:5173"  # the default CORS origin
    response = small.post(URL, content=padded(SMALL_LIMIT + 1),
                          headers={**JSON, "Origin": origin})  # fmt: skip
    assert response.status_code == 413
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize("path", ["/health", "/api/v1/shocks/catalog"])
def test_bodyless_requests_are_unaffected(small: TestClient, path: str) -> None:
    assert small.get(path).status_code == 200


def test_the_limit_applies_before_authentication(small: TestClient) -> None:
    """An oversized body never reaches a route, even a protected one (no token is checked)."""
    response = small.post(PLAN_URL, content=padded(SMALL_LIMIT + 1), headers=JSON)
    assert_problem(response, 413, "request-too-large")


def test_every_legitimate_body_fits_the_default_limit() -> None:
    """The largest body the schemas allow (a tracker POST whose title and note are all JSON
    surrogate escapes) is about 5 KB, an order of magnitude under 64 KiB."""
    pair = chr(92) + "ud83d" + chr(92) + "ude00"  # one character as a 12-byte JSON escape

    def escaped(chars: int) -> str:
        return '"' + pair * (chars // 2 + 1) + '"'

    tracker = (
        f'{{"type":"expense","title":{escaped(240)},"category":"utilities",'
        f'"note":{escaped(560)},"amount":100000000,"date":"2026-10-26T14:30:00.123456+02:00"}}'
    )
    assert len(tracker.encode()) * 10 < MAX_REQUEST_BODY_BYTES_DEFAULT
