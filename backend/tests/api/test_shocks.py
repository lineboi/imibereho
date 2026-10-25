"""`POST /api/v1/calculations/household-shock` (contract §4). Needs no database."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.helpers import META, NOT_INTEGER_BODY_VALUES, assert_number, assert_problem, raw_json

URL = "/api/v1/calculations/household-shock"
INTEGER_FIELDS = [
    ("baseline", "monthlyIncome"),
    ("baseline", "monthlyEssentials"),
    ("baseline", "savings"),
    ("shock", "incomeReductionPct"),
    ("shock", "durationMonths"),
]


def payload(**changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "baseline": {"monthlyIncome": 180_000, "monthlyEssentials": 150_000, "savings": 60_000},
        "shock": {"type": "income_fall", "incomeReductionPct": 20, "durationMonths": 3},
    }
    for path, value in changes.items():
        section, field = path.split("__")
        body[section][field] = value
    return body


def test_design_values(client: TestClient) -> None:
    response = client.post(URL, json=payload())
    assert response.status_code == 200
    data = raw_json(response)
    assert data == {
        "baselineMonthlyBalance": 30_000,
        "shockedMonthlyIncome": 144_000,
        "monthlyGap": 6_000,
        "savingsUsed": 18_000,
        "savingsRemaining": 42_000,
        "savingsExhausted": False,
        "runwayMonths": 10.0,
        "assumptions": ["expenses_held_constant", "no_new_borrowing", "no_additional_shocks"],
        "meta": META,
    }
    assert '"runwayMonths":10.0' in response.text  # a JSON number with one decimal place
    for field in ("baselineMonthlyBalance", "shockedMonthlyIncome", "monthlyGap", "savingsUsed"):
        assert_number(data[field], data[field], integer=True)
    assert_number(data["runwayMonths"], 10.0, integer=False)


def test_zero_reduction_gives_no_gap_and_null_runway(client: TestClient) -> None:
    data = client.post(URL, json=payload(shock__incomeReductionPct=0)).json()
    assert data["monthlyGap"] == 0 and data["runwayMonths"] is None


def test_zero_savings_is_exhausted_with_zero_runway(client: TestClient) -> None:
    data = raw_json(client.post(URL, json=payload(baseline__savings=0)))
    assert data["savingsExhausted"] is True
    assert_number(data["runwayMonths"], 0.0, integer=False)


@pytest.mark.parametrize(("section", "field"), INTEGER_FIELDS)
@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_body_integer_matrix(client: TestClient, section: str, field: str, value: object) -> None:
    response = client.post(URL, json=payload(**{f"{section}__{field}": value}))
    assert_problem(response, 422, "validation", (f"{section}.{field}", "not_integer"))


@pytest.mark.parametrize(("section", "field"), INTEGER_FIELDS)
def test_body_null_is_required(client: TestClient, section: str, field: str) -> None:
    response = client.post(URL, json=payload(**{f"{section}__{field}": None}))
    assert_problem(response, 422, "validation", (f"{section}.{field}", "required"))


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"shock__incomeReductionPct": 101}, "shock.incomeReductionPct"),
        ({"shock__durationMonths": 0}, "shock.durationMonths"),
        ({"shock__durationMonths": 25}, "shock.durationMonths"),
        ({"baseline__monthlyIncome": 100_000_001}, "baseline.monthlyIncome"),
        ({"baseline__savings": -1}, "baseline.savings"),
    ],
)
def test_out_of_range(client: TestClient, change: dict[str, int], field: str) -> None:
    assert_problem(
        client.post(URL, json=payload(**change)), 422, "validation", (field, "out_of_range")
    )


def test_maximum_inputs_are_accepted(client: TestClient) -> None:
    body = payload(
        baseline__monthlyIncome=100_000_000,
        baseline__monthlyEssentials=100_000_000,
        baseline__savings=100_000_000,
        shock__incomeReductionPct=100,
        shock__durationMonths=24,
    )
    data = client.post(URL, json=body).json()
    assert data["monthlyGap"] == 100_000_000 and data["savingsExhausted"] is True


def test_other_shock_type_is_unknown_value(client: TestClient) -> None:
    response = client.post(URL, json=payload(shock__type="price_rise"))
    assert_problem(response, 422, "validation", ("shock.type", "unknown_value"))


def test_extra_body_field_is_unknown_field(client: TestClient) -> None:
    body = payload()
    body["baseline"]["name"] = "Someone"
    assert_problem(
        client.post(URL, json=body), 422, "validation", ("baseline.name", "unknown_field")
    )


def test_malformed_json(client: TestClient) -> None:
    response = client.post(URL, content="{not json", headers={"Content-Type": "application/json"})
    assert_problem(response, 400, "malformed-request")


def test_query_parameters_are_refused(client: TestClient) -> None:
    response = client.post(URL + "?monthlyIncome=180000", json=payload())
    assert_problem(response, 400, "unknown-parameter", ("monthlyIncome", "unknown_field"))


def test_get_is_method_not_allowed(client: TestClient) -> None:
    assert_problem(client.get(URL), 405, "method-not-allowed")
