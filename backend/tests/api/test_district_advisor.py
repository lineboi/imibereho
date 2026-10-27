"""District Budget Advisor endpoints (contract v0.4 §11.3 and §11.7, MISSING_APIS.pdf pages 7-8).

Gasabo and Musanze use the PDF's example baskets (owner-approved illustrative data, labelled
with `meta.provenance`). Every other district uses the seeded benchmark, one illustrative basket
(65,000 / 40,000 / 20,000 / 10,000 / 15,000 = 150,000, equal to Gasabo's), so two such districts
never differ.
"""

from typing import Any, Final

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.helpers import (
    EXAMPLE_META,
    NO_EXAMPLE_META,
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
MUSANZE: Final = {
    "food": 50_000, "housing": 28_000, "transport": 14_000, "utilities": 9_000, "other": 14_000,
}  # fmt: skip
EXAMPLE: Final = "gasabo_and_musanze_baskets_are_missing_apis_pdf_examples"
UNIFORM: Final = "benchmark_is_one_illustrative_basket_for_every_district"
NOT_OBSERVED: Final = "not_observed_district_data"
SCALED: Final = "household_size_scaled_from_size_4_by_square_root_equivalence"


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
    # BR-22 gives −0.8. The PDF's −1.2 is not produced by any formula it states (contract §11.3).
    assert_number(data["bufferImpactMonths"], -0.8, integer=False)
    assert data["assumptions"] == [
        EXAMPLE, NOT_OBSERVED, SCALED, "scenario_is_illustrative_not_a_forecast",
        "buffer_impact_is_a_year_of_the_increase_in_months_of_the_baseline_basket",
        "buffer_impact_is_br_22_the_pdf_example_figure_is_not_derivable",
    ]  # fmt: skip
    assert data["meta"] == EXAMPLE_META


def test_stress_test_uses_the_musanze_example_basket(db_client: TestClient) -> None:
    data = raw_json(db_client.post(STRESS, json=stress(district="musanze")))
    assert (data["baselineTotal"], data["stressedTotal"], data["monthlyIncrease"]) == (
        115_000, 122_500, 7_500,
    )  # fmt: skip
    assert_number(data["bufferImpactMonths"], -0.8, integer=False)  # −(12 × 7,500 ÷ 115,000)
    body = stress(district="musanze", scenario="rent_surge_10")
    rent = raw_json(db_client.post(STRESS, json=body))
    assert (rent["monthlyIncrease"], rent["stressedTotal"]) == (2_800, 117_800)


def test_stress_test_elsewhere_uses_the_shared_benchmark(db_client: TestClient) -> None:
    data = raw_json(db_client.post(STRESS, json=stress(district="huye")))
    assert (data["baselineTotal"], data["monthlyIncrease"]) == (150_000, 9_750)
    assert data["assumptions"][:2] == [UNIFORM, NOT_OBSERVED]
    assert EXAMPLE not in data["assumptions"]
    assert data["meta"] == NO_EXAMPLE_META


def test_rent_surge(db_client: TestClient) -> None:
    data = raw_json(db_client.post(STRESS, json=stress(scenario="rent_surge_10")))
    assert (data["stressedTotal"], data["monthlyIncrease"]) == (154_000, 4_000)
    assert_number(data["bufferImpactMonths"], -0.3, integer=False)


def test_stress_test_errors(db_client: TestClient) -> None:
    assert_problem(db_client.post(STRESS, json=stress(scenario="fuel_spike")), 422, "validation",
                   ("scenario", "unknown_value"))  # fmt: skip
    assert_problem(db_client.post(STRESS, json=stress(district="atlantis")), 404,
                   "district-not-found")  # fmt: skip
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


def test_comparison_pdf_example(db_client: TestClient) -> None:
    response = db_client.get(COMPARE + "?district_a=gasabo&district_b=musanze&household_size=4")
    assert response.status_code == 200
    data = raw_json(response)
    assert data["districtA"] == {"code": "gasabo", "name": "Gasabo", "total": 150_000,
                                 "breakdown": BREAKDOWN}  # fmt: skip
    assert data["districtB"] == {"code": "musanze", "name": "Musanze", "total": 115_000,
                                 "breakdown": MUSANZE}  # fmt: skip
    assert data["variance"]["netDifference"] == -35_000
    assert_number(data["variance"]["percentageDifference"], -23.3, integer=False)
    # The PDF lists food, housing and transport; utilities and other are also returned.
    assert data["variance"]["categoryDifferences"] == {
        "food": -15_000, "housing": -12_000, "transport": -6_000, "utilities": -1_000,
        "other": -1_000,
    }  # fmt: skip
    assert_number(data["costOfLivingMultiplier"], 0.767, integer=False)
    assert data["assumptions"] == [EXAMPLE, NOT_OBSERVED, SCALED]
    assert data["meta"] == EXAMPLE_META


def test_comparison_reversed_inverts_the_variance(db_client: TestClient) -> None:
    data = raw_json(
        db_client.get(COMPARE + "?district_a=musanze&district_b=gasabo&household_size=4")
    )
    assert data["variance"]["netDifference"] == 35_000
    assert_number(data["variance"]["percentageDifference"], 30.4, integer=False)  # 35 ÷ 115
    assert_number(data["costOfLivingMultiplier"], 1.304, integer=False)


def test_districts_without_an_example_show_no_difference(db_client: TestClient) -> None:
    data = raw_json(
        db_client.get(COMPARE + "?district_a=huye&district_b=nyagatare&household_size=4")
    )
    assert data["districtA"]["breakdown"] == BREAKDOWN == data["districtB"]["breakdown"]
    assert data["variance"]["netDifference"] == 0
    assert data["variance"]["categoryDifferences"] == dict.fromkeys(BREAKDOWN, 0)
    assert_number(data["costOfLivingMultiplier"], 1.0, integer=False)
    assert data["assumptions"] == [UNIFORM, NOT_OBSERVED, SCALED]
    assert data["meta"] == NO_EXAMPLE_META


def test_example_and_benchmark_district_together(db_client: TestClient) -> None:
    data = raw_json(db_client.get(COMPARE + "?district_a=huye&district_b=musanze&household_size=4"))
    assert data["variance"]["netDifference"] == -35_000
    assert data["assumptions"] == [EXAMPLE, UNIFORM, NOT_OBSERVED, SCALED]
    assert data["meta"] == EXAMPLE_META


def test_comparison_errors(db_client: TestClient) -> None:
    ok = "district_a=gasabo&district_b=musanze&household_size=4"
    unknown = "?district_a=gasabo&district_b=atlantis&household_size=4"
    assert_problem(db_client.get(COMPARE + unknown), 404, "district-not-found")
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


RENT_AND_TRANSIT: Final = "rent_and_transit_are_the_basket_housing_and_transport_lines"
NO_STAPLES: Final = "no_staple_prices_or_market_hub_in_the_pdf_for_this_district"
NULL_STAPLES: Final = dict.fromkeys(("irishPotatoesPerKg", "sweetPotatoesPerKg", "redBeansPerKg"))


def test_basket_details_pdf_example(db_client: TestClient) -> None:
    response = db_client.get(BASKET.format(code="gasabo"))
    assert response.status_code == 200
    data = raw_json(response)
    assert data == {
        "status": "available",
        "districtCode": "gasabo",
        "householdSize": 4,
        "referenceRentIndex": 40_000,
        "referenceTransitPass": 20_000,
        "staplePriceIndex": {
            "irishPotatoesPerKg": 750, "sweetPotatoesPerKg": 800, "redBeansPerKg": 850,
        },
        "primaryMarketHub": "Kimironko Market",
        "unavailableFields": [],
        "assumptions": [EXAMPLE, NOT_OBSERVED, RENT_AND_TRANSIT],
        "meta": EXAMPLE_META,
    }  # fmt: skip
    for value in data["staplePriceIndex"].values():
        assert_number(value, value, integer=True)


def test_basket_details_musanze_has_no_staples_in_the_pdf(db_client: TestClient) -> None:
    data = raw_json(db_client.get(BASKET.format(code="musanze")))
    assert data["status"] == "awaiting_validated_data"
    assert (data["referenceRentIndex"], data["referenceTransitPass"]) == (28_000, 14_000)
    assert data["staplePriceIndex"] == NULL_STAPLES and data["primaryMarketHub"] is None
    assert data["unavailableFields"] == ["staplePriceIndex", "primaryMarketHub"]
    assert data["assumptions"] == [EXAMPLE, NOT_OBSERVED, NO_STAPLES, RENT_AND_TRANSIT]
    assert data["meta"] == EXAMPLE_META


def test_basket_details_elsewhere(db_client: TestClient) -> None:
    response = db_client.get(BASKET.format(code="huye"))
    data = raw_json(response)
    assert data["status"] == "awaiting_validated_data"
    assert (data["referenceRentIndex"], data["referenceTransitPass"]) == (40_000, 20_000)
    assert data["staplePriceIndex"] == NULL_STAPLES
    assert data["unavailableFields"] == ["staplePriceIndex", "primaryMarketHub"]
    assert data["assumptions"] == [UNIFORM, NOT_OBSERVED, NO_STAPLES, RENT_AND_TRANSIT]
    assert data["meta"] == NO_EXAMPLE_META
    assert '"primaryMarketHub":null' in response.text


def test_only_gasabo_has_staple_prices_and_a_market_hub(db_client: TestClient) -> None:
    """Every other district is explicitly awaiting data, with nulls (never 0) and no invention."""
    codes = [d["code"] for d in raw_json(db_client.get("/api/v1/districts"))["items"]]
    assert len(codes) == 30
    for code in codes:
        data = raw_json(db_client.get(BASKET.format(code=code)))
        if code == "gasabo":
            assert data["status"] == "available" and data["unavailableFields"] == []
            continue
        assert data["status"] == "awaiting_validated_data", code
        assert data["staplePriceIndex"] == NULL_STAPLES and data["primaryMarketHub"] is None
        assert data["unavailableFields"] == ["staplePriceIndex", "primaryMarketHub"]
        assert data["meta"]["isIllustrative"] is True
        assert data["meta"]["provenance"] == (EXAMPLE_META["provenance"] if code == "musanze"
                                              else None)  # fmt: skip


def test_basket_details_errors(db_client: TestClient) -> None:
    assert_problem(db_client.get(BASKET.format(code="atlantis")), 404, "district-not-found")
    # District codes are case-sensitive (contract §5).
    assert_problem(db_client.get(BASKET.format(code="GASABO")), 404, "district-not-found")
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
    status = schemas["BasketDetailsResponse"]["properties"]["status"]
    assert set(status["enum"]) == {"available", "awaiting_validated_data"}
    assert "status" in schemas["BasketDetailsResponse"]["required"]
    provenance = schemas["ExampleMeta"]["properties"]["provenance"]["anyOf"]
    assert {"const": "MISSING_APIS.pdf example, owner-approved", "type": "string"} in provenance


# --- Household sizes other than 4: BR-24 square-root scaling (owner-approved 2026-10-27) ---

SIZE_5: Final = {
    "food": 72_672, "housing": 44_721, "transport": 22_361, "utilities": 11_180, "other": 16_771,
}  # fmt: skip


MUSANZE_SIZE_5: Final = {
    "food": 55_902, "housing": 31_305, "transport": 15_652, "utilities": 10_062, "other": 15_652,
}  # fmt: skip


def test_comparison_scales_to_any_household_size(db_client: TestClient) -> None:
    data = raw_json(
        db_client.get(COMPARE + "?district_a=gasabo&district_b=musanze&household_size=5")
    )
    assert data["districtA"]["breakdown"] == SIZE_5
    assert data["districtA"]["total"] == sum(SIZE_5.values()) == 167_705  # sum of scaled lines
    assert data["districtB"]["breakdown"] == MUSANZE_SIZE_5
    assert data["districtB"]["total"] == sum(MUSANZE_SIZE_5.values()) == 128_573
    assert data["variance"]["netDifference"] == 128_573 - 167_705
    one = raw_json(
        db_client.get(COMPARE + "?district_a=huye&district_b=nyagatare&household_size=1")
    )
    assert one["districtA"]["total"] == 75_000  # half of 150,000


@pytest.mark.parametrize(
    ("size", "baseline", "increase"),
    [(1, 75_000, 4_875), (5, 167_705, 10_901), (20, 335_410, 21_802)],
)
def test_stress_test_scales_to_any_household_size(
    db_client: TestClient, size: int, baseline: int, increase: int
) -> None:
    data = raw_json(db_client.post(STRESS, json=stress(householdSize=size)))
    assert (data["baselineTotal"], data["monthlyIncrease"]) == (baseline, increase)
    assert data["stressedTotal"] == baseline + increase
    assert "household_size_scaled_from_size_4_by_square_root_equivalence" in data["assumptions"]


def test_budget_benchmarks_keep_their_size_4_contract(db_client: TestClient) -> None:
    """BR-24 applies to the v0.4 advisor endpoints only; /budget-benchmarks is unchanged."""
    response = db_client.get("/api/v1/budget-benchmarks?district=gasabo&householdSize=5")
    assert_problem(response, 404, "benchmark-not-available")


def test_gasabo_example_equals_the_seeded_benchmark(db_client: TestClient) -> None:
    """The PDF's Gasabo basket is the seeded benchmark, so both data paths agree for Gasabo."""
    seeded = raw_json(db_client.get("/api/v1/budget-benchmarks?district=gasabo&householdSize=4"))
    lines = {line["categoryCode"]: line["monthlyAmount"] for line in seeded["lines"]}
    assert lines == {**{k: v for k, v in BREAKDOWN.items() if k != "other"},
                     "other_essentials": 15_000}  # fmt: skip


def test_budget_benchmarks_do_not_use_the_musanze_example(db_client: TestClient) -> None:
    """Known difference (contract §11.7): the example basket is for the v0.4 advisor only."""
    seeded = raw_json(db_client.get("/api/v1/budget-benchmarks?district=musanze&householdSize=4"))
    assert seeded["total"] == 150_000
