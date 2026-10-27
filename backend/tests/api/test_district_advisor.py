"""District Budget Advisor endpoints (contract v0.4 §11.3, MISSING_APIS.pdf pages 7-8).

The seeded benchmark is one illustrative basket for every district at household size 4
(65,000 / 40,000 / 20,000 / 10,000 / 15,000 = 150,000), so two districts never differ.
"""

from typing import Any, Final

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.helpers import (
    META,
    NOT_INTEGER_BODY_VALUES,
    NOT_INTEGER_QUERY_VALUES,
    assert_number,
    assert_problem,
    raw_json,
)

STRESS: Final = "/api/v1/calculations/stress-test"
COMPARE: Final = "/api/v1/calculations/district-comparison"
BASKET: Final = "/api/v1/districts/{code}/basket-details"
BREAKDOWN: Final = {
    "food": 65_000, "housing": 40_000, "transport": 20_000, "utilities": 10_000, "other": 15_000,
}  # fmt: skip


def stress(**changes: Any) -> dict[str, Any]:
    return {"district": "gasabo", "householdSize": 4, "scenario": "food_inflation_15", **changes}


# --- POST /calculations/stress-test ---


def test_stress_test_pdf_example(db_client: TestClient) -> None:
    response = db_client.post(STRESS, json=stress())
    assert response.status_code == 200
    data = raw_json(response)
    assert {k: data[k] for k in ("baselineTotal", "stressedTotal", "monthlyIncrease")} == {
        "baselineTotal": 150_000, "stressedTotal": 159_750, "monthlyIncrease": 9_750,
    }  # fmt: skip
    assert_number(data["bufferImpactMonths"], -0.8, integer=False)  # PDF: −1.2 (not derivable)
    assert "benchmark_is_one_illustrative_basket_for_every_district" in data["assumptions"]
    assert data["meta"] == META


def test_rent_surge(db_client: TestClient) -> None:
    data = raw_json(db_client.post(STRESS, json=stress(scenario="rent_surge_10")))
    assert (data["stressedTotal"], data["monthlyIncrease"]) == (154_000, 4_000)
    assert_number(data["bufferImpactMonths"], -0.3, integer=False)


def test_stress_test_errors(db_client: TestClient) -> None:
    assert_problem(db_client.post(STRESS, json=stress(scenario="fuel_spike")), 422, "validation",
                   ("scenario", "unknown_value"))  # fmt: skip
    assert_problem(db_client.post(STRESS, json=stress(district="atlantis")), 404,
                   "district-not-found")  # fmt: skip
    assert_problem(db_client.post(STRESS, json=stress(householdSize=5)), 404,
                   "benchmark-not-available")  # fmt: skip
    assert_problem(db_client.post(STRESS, json=stress(householdSize=21)), 422, "validation",
                   ("householdSize", "out_of_range"))  # fmt: skip
    # Validation before lookup: an invalid size with an unknown district is still a 422.
    assert_problem(db_client.post(STRESS, json=stress(district="atlantis", householdSize=0)),
                   422, "validation", ("householdSize", "out_of_range"))  # fmt: skip
    assert_problem(db_client.post(STRESS, json=stress(baselineTotal=1)), 422, "validation",
                   ("baselineTotal", "unknown_field"))  # fmt: skip
    assert_problem(db_client.get(STRESS), 405, "method-not-allowed")


@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_stress_household_size_must_be_an_integer(db_client: TestClient, value: object) -> None:
    assert_problem(db_client.post(STRESS, json=stress(householdSize=value)), 422, "validation",
                   ("householdSize", "not_integer"))  # fmt: skip


# --- GET /calculations/district-comparison ---


def test_comparison_of_two_districts_shows_no_difference(db_client: TestClient) -> None:
    response = db_client.get(COMPARE + "?district_a=gasabo&district_b=musanze&household_size=4")
    assert response.status_code == 200
    data = raw_json(response)
    assert data["districtA"] == {"code": "gasabo", "name": "Gasabo", "total": 150_000,
                                 "breakdown": BREAKDOWN}  # fmt: skip
    assert data["districtB"] == {"code": "musanze", "name": "Musanze", "total": 150_000,
                                 "breakdown": BREAKDOWN}  # fmt: skip
    assert data["variance"]["netDifference"] == 0
    assert_number(data["variance"]["percentageDifference"], 0.0, integer=False)
    assert data["variance"]["categoryDifferences"] == dict.fromkeys(BREAKDOWN, 0)
    assert_number(data["costOfLivingMultiplier"], 1.0, integer=False)
    assert data["assumptions"] == [
        "benchmark_is_one_illustrative_basket_for_every_district", "not_observed_district_data",
    ]  # fmt: skip
    assert data["meta"] == META


def test_comparison_errors(db_client: TestClient) -> None:
    ok = "district_a=gasabo&district_b=musanze&household_size=4"
    unknown = "?district_a=gasabo&district_b=atlantis&household_size=4"
    assert_problem(db_client.get(COMPARE + unknown), 404, "district-not-found")
    no_benchmark = "?district_a=gasabo&district_b=musanze&household_size=3"
    assert_problem(db_client.get(COMPARE + no_benchmark), 404, "benchmark-not-available")
    assert_problem(db_client.get(COMPARE + "?district_a=gasabo&household_size=4"), 422,
                   "validation", ("district_b", "required"))  # fmt: skip
    # The PDF's names are snake_case; the camelCase spelling is an unknown parameter.
    assert_problem(db_client.get(COMPARE + "?districtA=gasabo&district_b=musanze&household_size=4"),
                   400, "unknown-parameter", ("districtA", "unknown_field"))  # fmt: skip
    assert_problem(db_client.post(COMPARE + "?" + ok), 405, "method-not-allowed")


@pytest.mark.parametrize("raw", NOT_INTEGER_QUERY_VALUES)
def test_comparison_household_size_must_be_digits(db_client: TestClient, raw: str) -> None:
    response = db_client.get(COMPARE + f"?district_a=gasabo&district_b=huye&household_size={raw}")
    assert_problem(response, 422, "validation", ("household_size", "not_integer"))


# --- GET /districts/{code}/basket-details ---


def test_basket_details(db_client: TestClient) -> None:
    response = db_client.get(BASKET.format(code="gasabo"))
    assert response.status_code == 200
    data = raw_json(response)
    assert data == {
        "districtCode": "gasabo",
        "householdSize": 4,
        "referenceRentIndex": 40_000,
        "referenceTransitPass": 20_000,
        "staplePriceIndex": {
            "irishPotatoesPerKg": None, "sweetPotatoesPerKg": None, "redBeansPerKg": None,
        },
        "primaryMarketHub": None,
        "unavailableFields": ["staplePriceIndex", "primaryMarketHub"],
        "assumptions": [
            "benchmark_is_one_illustrative_basket_for_every_district",
            "not_observed_district_data",
            "rent_and_transit_are_the_benchmark_housing_and_transport_lines",
            "no_sourced_staple_prices_or_market_hubs",
        ],
        "meta": META,
    }  # fmt: skip
    assert '"primaryMarketHub":null' in response.text


def test_basket_details_errors(db_client: TestClient) -> None:
    assert_problem(db_client.get(BASKET.format(code="atlantis")), 404, "district-not-found")
    assert_problem(db_client.get(BASKET.format(code="gasabo") + "?householdSize=4"), 400,
                   "unknown-parameter", ("householdSize", "unknown_field"))  # fmt: skip
    assert_problem(db_client.post(BASKET.format(code="gasabo")), 405, "method-not-allowed")


def test_openapi(stub_app: FastAPI) -> None:
    spec = stub_app.openapi()
    assert "post" in spec["paths"][STRESS] and "get" in spec["paths"][COMPARE]
    assert "get" in spec["paths"]["/api/v1/districts/{code}/basket-details"]
    params = {p["name"] for p in spec["paths"][COMPARE]["get"]["parameters"]}
    assert params == {"district_a", "district_b", "household_size"}
    schemas = spec["components"]["schemas"]
    assert {
        o.get("type") for o in schemas["StaplePriceIndex"]["properties"]["redBeansPerKg"]["anyOf"]
    } == {"integer", "null"}
