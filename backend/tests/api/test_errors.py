"""RFC 9457 problem details (contract §1.3) and number parsing (contract §1.2).

Exercised on throwaway routes so every error path is covered independently of any endpoint.
"""

from typing import Annotated, Literal

import pytest
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from pydantic import Field, StrictInt

from app.core.errors import DistrictNotFoundError
from app.schemas.common import BodyModel, QueryInt, QueryModel
from tests.helpers import NOT_INTEGER_BODY_VALUES, NOT_INTEGER_QUERY_VALUES, assert_problem

MALFORMED = {
    "type": "https://imibereho.example/errors/malformed-request",
    "title": "Malformed request",
    "status": 400,
    "detail": "The request body is not valid JSON.",
}


class _Query(QueryModel):
    size: Annotated[QueryInt, Field(ge=1, le=20)]
    code: Annotated[str, Field(max_length=8)] = "x"


class _Inner(BodyModel):
    amount: Annotated[StrictInt, Field(ge=0, le=100)]


class _Body(BodyModel):
    inner: _Inner
    kind: Literal["income_fall"]


@pytest.fixture
def test_client(stub_app: FastAPI) -> TestClient:
    @stub_app.get("/_test/query")
    def query_route(q: Annotated[_Query, Query()]) -> dict[str, int]:
        return {"size": q.size}

    @stub_app.post("/_test/body")
    def body_route(body: _Body) -> dict[str, int]:
        return {"amount": body.inner.amount}

    @stub_app.get("/_test/missing-district")
    def missing() -> None:
        raise DistrictNotFoundError

    @stub_app.get("/_test/crash")
    def crash() -> None:
        raise ValueError("internal detail that must not leak")

    return TestClient(stub_app, raise_server_exceptions=False)


def body(amount: object = 5, kind: object = "income_fall") -> dict[str, object]:
    return {"inner": {"amount": amount}, "kind": kind}


def test_malformed_json_returns_the_exact_contract_body(test_client: TestClient) -> None:
    response = test_client.post(
        "/_test/body", content='{"a":', headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == MALFORMED
    assert "errors" not in response.json()


@pytest.mark.parametrize("raw", ["4", "%34", "04"])
def test_query_integer_accepted_forms(test_client: TestClient, raw: str) -> None:
    response = test_client.get(f"/_test/query?size={raw}")
    assert response.status_code == 200 and response.json() == {"size": 4}


@pytest.mark.parametrize("raw", NOT_INTEGER_QUERY_VALUES)
def test_query_integer_rejected_forms(test_client: TestClient, raw: str) -> None:
    response = test_client.get(f"/_test/query?size={raw}")
    assert_problem(response, 422, "validation", ("size", "not_integer"))


@pytest.mark.parametrize("raw", ["21", "0", "9999999999999999999999"])
def test_query_integer_out_of_bounds(test_client: TestClient, raw: str) -> None:
    assert_problem(
        test_client.get(f"/_test/query?size={raw}"), 422, "validation", ("size", "out_of_range")
    )


def test_negative_query_value_is_not_integer_not_out_of_range(test_client: TestClient) -> None:
    assert_problem(
        test_client.get("/_test/query?size=-1"), 422, "validation", ("size", "not_integer")
    )


def test_missing_query_parameter_is_required(test_client: TestClient) -> None:
    assert_problem(test_client.get("/_test/query"), 422, "validation", ("size", "required"))


def test_unknown_query_parameter_is_400(test_client: TestClient) -> None:
    response = test_client.get("/_test/query?size=4&extra=1")
    problem = assert_problem(response, 400, "unknown-parameter", ("extra", "unknown_field"))
    assert problem["errors"][0]["message"]


def test_too_long_string_is_too_long(test_client: TestClient) -> None:
    response = test_client.get("/_test/query?size=4&code=" + "x" * 9)
    assert_problem(response, 422, "validation", ("code", "too_long"))


def test_body_integer_accepted(test_client: TestClient) -> None:
    assert test_client.post("/_test/body", json=body(100)).json() == {"amount": 100}


@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_body_integer_rejected_forms(test_client: TestClient, value: object) -> None:
    response = test_client.post("/_test/body", json=body(value))
    assert_problem(response, 422, "validation", ("inner.amount", "not_integer"))


def test_body_number_with_decimal_point_is_not_integer(test_client: TestClient) -> None:
    response = test_client.post(
        "/_test/body",
        content='{"inner": {"amount": 4.0}, "kind": "income_fall"}',
        headers={"Content-Type": "application/json"},
    )
    assert_problem(response, 422, "validation", ("inner.amount", "not_integer"))


def test_body_null_and_missing_are_required(test_client: TestClient) -> None:
    assert_problem(
        test_client.post("/_test/body", json=body(None)),
        422,
        "validation",
        ("inner.amount", "required"),
    )
    response = test_client.post("/_test/body", json={"inner": {"amount": 1}})
    assert_problem(response, 422, "validation", ("kind", "required"))


@pytest.mark.parametrize(
    ("value", "message"), [(-1, "Must be at least 0."), (101, "Must be at most 100.")]
)
def test_body_out_of_range(test_client: TestClient, value: int, message: str) -> None:
    problem = assert_problem(
        test_client.post("/_test/body", json=body(value)),
        422,
        "validation",
        ("inner.amount", "out_of_range"),
    )
    assert problem["errors"][0]["message"] == message


@pytest.mark.parametrize("kind", ["price_rise", True, 3])
def test_bad_enum_value_is_unknown_value(test_client: TestClient, kind: object) -> None:
    assert_problem(
        test_client.post("/_test/body", json=body(kind=kind)),
        422,
        "validation",
        ("kind", "unknown_value"),
    )


def test_extra_body_field_is_unknown_field(test_client: TestClient) -> None:
    payload = {**body(), "surprise": 1}
    assert_problem(
        test_client.post("/_test/body", json=payload),
        422,
        "validation",
        ("surprise", "unknown_field"),
    )


def test_snake_case_body_field_is_refused(test_client: TestClient) -> None:
    response = test_client.post(
        "/_test/body", json={"inner": {"amount": 1}, "kind": "income_fall", "in_ner": 1}
    )
    assert_problem(response, 422, "validation", ("in_ner", "unknown_field"))


def test_wrong_shape_body_is_a_validation_error(test_client: TestClient) -> None:
    assert_problem(test_client.post("/_test/body", json=[]), 422, "validation")
    assert_problem(
        test_client.post("/_test/body", json={"inner": 5, "kind": "income_fall"}),
        422,
        "validation",
        ("inner", "unknown_value"),
    )


def test_empty_body_is_required(test_client: TestClient) -> None:
    response = test_client.post("/_test/body", headers={"Content-Type": "application/json"})
    assert_problem(response, 422, "validation", ("body", "required"))


def test_domain_404(test_client: TestClient) -> None:
    problem = assert_problem(test_client.get("/_test/missing-district"), 404, "district-not-found")
    assert "errors" not in problem


def test_unknown_route_is_not_found(test_client: TestClient) -> None:
    assert_problem(test_client.get("/api/v1/nowhere"), 404, "not-found")


def test_wrong_method_is_method_not_allowed(test_client: TestClient) -> None:
    response = test_client.delete("/health")
    assert_problem(response, 405, "method-not-allowed")
    assert "GET" in response.headers.get("allow", "")


def test_unhandled_error_is_500_without_internal_detail(test_client: TestClient) -> None:
    response = test_client.get("/_test/crash", headers={"X-Request-ID": "crash-1"})
    problem = assert_problem(response, 500, "internal")
    assert "internal detail" not in response.text and "ValueError" not in response.text
    assert response.headers["X-Request-ID"] == "crash-1"
    assert "X-Request-ID" in problem["detail"]


def test_every_response_carries_content_language_and_security_headers(
    test_client: TestClient,
) -> None:
    for response in (test_client.get("/health"), test_client.get("/nowhere")):
        assert response.headers["content-language"] == "en"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "no-referrer"


def test_post_responses_are_not_cached(test_client: TestClient) -> None:
    assert test_client.post("/_test/body", json=body()).headers["cache-control"] == "no-store"
