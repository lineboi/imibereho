"""Optional `POST /api/v1/calculations/budget-comparison` (contract §6, BR-13). DB-backed."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.helpers import META, NOT_INTEGER_BODY_VALUES, assert_problem, raw_json

URL = "/api/v1/calculations/budget-comparison"
DESIGN_PLAN = [  # C3 "You" column, [E] 2:6533
    {"categoryCode": "food", "plannedAmount": 60_000},
    {"categoryCode": "housing", "plannedAmount": 45_000},
    {"categoryCode": "transport", "plannedAmount": 18_000},
    {"categoryCode": "utilities", "plannedAmount": 12_000},
    {"categoryCode": "other_essentials", "plannedAmount": 15_000},
]


def payload(**changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "district": "gasabo",
        "householdSize": 4,
        "plan": [dict(line) for line in DESIGN_PLAN],
    }
    body.update(changes)
    return body


def test_design_values(db_client: TestClient) -> None:
    data = raw_json(db_client.post(URL, json=payload()))
    assert data["largestAbove"] == {"categoryCode": "housing", "difference": 5_000}
    assert data["largestBelow"] == {"categoryCode": "food", "difference": -5_000}
    assert data["totals"] == {"planned": 150_000, "reference": 150_000, "difference": 0}
    assert data["lines"][0] == {
        "categoryCode": "food",
        "planned": 60_000,
        "reference": 65_000,
        "difference": -5_000,
    }
    assert data["meta"] == META


def test_missing_category_is_required(db_client: TestClient) -> None:
    response = db_client.post(URL, json=payload(plan=DESIGN_PLAN[:4]))
    assert_problem(response, 422, "validation", ("plan", "required"))


def test_duplicate_category_is_unknown_value(db_client: TestClient) -> None:
    plan = [*DESIGN_PLAN[:4], {"categoryCode": "food", "plannedAmount": 1}]
    assert_problem(
        db_client.post(URL, json=payload(plan=plan)),
        422,
        "validation",
        ("plan.4.categoryCode", "unknown_value"),
        ("plan", "required"),
    )


def test_unknown_district_is_404(db_client: TestClient) -> None:
    assert_problem(
        db_client.post(URL, json=payload(district="atlantis")), 404, "district-not-found"
    )


def test_other_household_size_is_benchmark_not_available(db_client: TestClient) -> None:
    assert_problem(
        db_client.post(URL, json=payload(householdSize=3)), 404, "benchmark-not-available"
    )


@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_planned_amount_must_be_an_integer(db_client: TestClient, value: object) -> None:
    plan = [dict(line) for line in DESIGN_PLAN]
    plan[1]["plannedAmount"] = value
    assert_problem(
        db_client.post(URL, json=payload(plan=plan)),
        422,
        "validation",
        ("plan.1.plannedAmount", "not_integer"),
    )


@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_household_size_must_be_an_integer(db_client: TestClient, value: object) -> None:
    assert_problem(
        db_client.post(URL, json=payload(householdSize=value)),
        422,
        "validation",
        ("householdSize", "not_integer"),
    )


def test_more_than_five_lines_is_out_of_range(db_client: TestClient) -> None:
    plan = [*DESIGN_PLAN, DESIGN_PLAN[0]]
    response = db_client.post(URL, json=payload(plan=plan))
    assert response.status_code == 422
