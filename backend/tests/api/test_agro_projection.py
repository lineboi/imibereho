"""`POST /api/v1/calculations/agro-savings-projection` (contract v0.4 §11.2, PDF page 10).

Reads the seeded `rice-to-sweet-potato` swap (2,000 → 1,600 RWF, invented in the design).
Purchasing-power equivalents use the unit costs implied by the PDF's example (2,600 RWF a week of
water, 650 a bus ride, 200 an egg; owner-approved illustrative data, contract §11.7).
"""

from typing import Any, Final

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.helpers import (
    EXAMPLE_META,
    NOT_INTEGER_BODY_VALUES,
    assert_number,
    assert_problem,
    raw_json,
)

URL: Final = "/api/v1/calculations/agro-savings-projection"


def equivalents(weeks: int, rides: int, eggs: int) -> list[dict[str, object]]:
    """Each item sets only its own PDF count key; the other two are null."""
    empty = dict.fromkeys(("coversWeeks", "ridesCount", "quantity"))
    return [
        {"item": "WASAC Clean Water", **empty, "coversWeeks": weeks},
        {"item": "Kigali City Bus Rides", **empty, "ridesCount": rides},
        {"item": "Fresh Farm Eggs", **empty, "quantity": eggs},
    ]


def payload(**changes: Any) -> dict[str, Any]:
    return {"swapId": "rice-to-sweet-potato", "mealsPerWeek": 3, "householdSize": 4, **changes}


def test_pdf_example(db_client: TestClient) -> None:
    response = db_client.post(URL, json=payload())
    assert response.status_code == 200
    data = raw_json(response)
    assert data == {
        "swapId": "rice-to-sweet-potato",
        "perMealSavings": 400,
        "monthlyProjectedSavings": 5_200,  # 400 × 3 × 52 ÷ 12, exactly the PDF's value
        "purchasingPowerEquivalents": equivalents(2, 8, 26),  # exactly the PDF's example
        "purchasingPowerStatus": "available",
        "assumptions": [
            "illustrative_prices_not_market_observations",
            "weeks_per_month_52_over_12",
            "priced_per_household_meal_household_size_does_not_scale",
            "swap_applies_whatever_the_month",
            "purchasing_power_unit_costs_implied_by_the_pdf_example_not_market_prices",
            "purchasing_power_counts_are_whole_units_rounded_down",
        ],
        "meta": EXAMPLE_META,
    }
    for key in ("perMealSavings", "monthlyProjectedSavings"):
        assert_number(data[key], data[key], integer=True)


@pytest.mark.parametrize(
    ("meals", "expected", "counts"),
    [(1, 1_733, (0, 2, 8)), (7, 12_133, (4, 18, 60)), (21, 36_400, (14, 56, 182))],
)
def test_meals_per_week_scale_the_projection(
    db_client: TestClient, meals: int, expected: int, counts: tuple[int, int, int]
) -> None:
    data = raw_json(db_client.post(URL, json=payload(mealsPerWeek=meals)))
    assert data["monthlyProjectedSavings"] == expected
    # Whole units, rounded down: 1,733 ÷ 2,600 buys no full week of water.
    assert data["purchasingPowerEquivalents"] == equivalents(*counts)


def test_household_size_does_not_change_the_result(db_client: TestClient) -> None:
    results = {
        size: raw_json(db_client.post(URL, json=payload(householdSize=size))) for size in (1, 4, 20)
    }
    assert {r["monthlyProjectedSavings"] for r in results.values()} == {5_200}


def test_matches_the_seasonal_agro_swaps_lever(db_client: TestClient) -> None:
    """The resilience lever's 5,200 is this endpoint's answer at 3 meals a week."""
    projected = raw_json(db_client.post(URL, json=payload()))["monthlyProjectedSavings"]
    levers = raw_json(db_client.get("/api/v1/shocks/catalog"))["copingLevers"]
    assert {lever["id"]: lever["amount"] for lever in levers}["seasonal_agro_swaps"] == projected


def test_unknown_swap_is_404(db_client: TestClient) -> None:
    assert_problem(db_client.post(URL, json=payload(swapId="beans-to-rice")), 404, "swap-not-found")


def test_validation_precedes_lookup(db_client: TestClient) -> None:
    response = db_client.post(URL, json=payload(swapId="beans-to-rice", mealsPerWeek=0))
    assert_problem(response, 422, "validation", ("mealsPerWeek", "out_of_range"))


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"mealsPerWeek": 0}, "mealsPerWeek"),
        ({"mealsPerWeek": 22}, "mealsPerWeek"),
        ({"householdSize": 0}, "householdSize"),
        ({"householdSize": 21}, "householdSize"),
    ],
)
def test_out_of_range(db_client: TestClient, change: dict[str, int], field: str) -> None:
    assert_problem(db_client.post(URL, json=payload(**change)), 422, "validation",
                   (field, "out_of_range"))  # fmt: skip


@pytest.mark.parametrize("field", ["mealsPerWeek", "householdSize"])
@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_integer_fields(db_client: TestClient, field: str, value: object) -> None:
    assert_problem(db_client.post(URL, json=payload(**{field: value})), 422, "validation",
                   (field, "not_integer"))  # fmt: skip


@pytest.mark.parametrize("field", ["swapId", "mealsPerWeek", "householdSize"])
def test_every_field_is_required(db_client: TestClient, field: str) -> None:
    body = payload()
    del body[field]
    assert_problem(db_client.post(URL, json=body), 422, "validation", (field, "required"))


def test_client_supplied_savings_are_refused(db_client: TestClient) -> None:
    body = payload(monthlyProjectedSavings=99_999)
    assert_problem(db_client.post(URL, json=body), 422, "validation",
                   ("monthlyProjectedSavings", "unknown_field"))  # fmt: skip


def test_malformed_json_query_and_method(db_client: TestClient) -> None:
    response = db_client.post(URL, content="{", headers={"Content-Type": "application/json"})
    assert_problem(response, 400, "malformed-request")
    assert_problem(db_client.post(URL + "?month=10", json=payload()), 400, "unknown-parameter",
                   ("month", "unknown_field"))  # fmt: skip
    assert_problem(db_client.get(URL), 405, "method-not-allowed")


def test_openapi(stub_app: FastAPI) -> None:
    spec = stub_app.openapi()
    operation = spec["paths"][URL]["post"]
    assert {"200", "400", "404", "422"} <= set(operation["responses"])
    props = spec["components"]["schemas"]["AgroSavingsProjectionResponse"]["properties"]
    assert props["monthlyProjectedSavings"]["type"] == "integer"
    assert set(props["purchasingPowerStatus"]["enum"]) == {"available", "awaiting_validated_data"}
    item = spec["components"]["schemas"]["PurchasingPowerEquivalent"]["properties"]
    assert set(item) == {"item", "coversWeeks", "ridesCount", "quantity"}
