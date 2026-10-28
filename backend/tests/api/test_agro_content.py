"""Nutrition and shopping checklist (contract v0.4 §11.5 and §11.7, PDF pages 10-11).

Both serve the PDF's example values, approved by the project owner as illustrative data and
labelled with `meta.provenance`. They are not official guidance or market prices. The checklist
example is Gasabo's for household size 4; every other district and size is modelled from it
(BR-28 by the district's food line, BR-24 by household size) and says so in `valueBasis`. The
total is the sum of the items (owner decision 2026-10-28; the PDF prints 6,250 for 4,750). The
harvest calendar is sourced from NISR and tested in `test_harvest_calendar.py`.
"""

from typing import Final

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.helpers import (
    EXAMPLE_META,
    NOT_INTEGER_QUERY_VALUES,
    assert_number,
    assert_problem,
    raw_json,
)

PLATE: Final = "/api/v1/nutrition/indyo-yuzuye"
CALENDAR: Final = "/api/v1/agro/harvest-calendar"
CHECKLIST: Final = "/api/v1/market/shopping-checklist"
EXAMPLE_ONLY: Final = "the_pdf_example_covers_only_gasabo_for_household_size_4"


def test_balanced_plate_pdf_example(db_client: TestClient) -> None:
    response = db_client.get(PLATE)
    assert response.status_code == 200
    data = raw_json(response)
    assert data == {
        "status": "available",
        "standard": "Indyo Yuzuye",
        "plateComponents": [
            {"code": "energy", "name": "Energy Staples", "proportionPct": 50,
             "examples": ["Sweet potatoes", "Cassava"]},
            {"code": "protective", "name": "Protective Greens", "proportionPct": 25,
             "examples": ["Dodo amaranth", "Isombe"]},
            {"code": "protein", "name": "Plant Protein", "proportionPct": 25,
             "examples": ["Red beans", "Groundnuts"]},
        ],
        "energyTip": "Boiling sweet potatoes alongside beans saves 35% charcoal fuel.",
        "assumptions": [
            "missing_apis_pdf_example_not_an_official_minagri_or_minisante_guideline",
            "energy_tip_figure_is_from_the_pdf_and_not_verified",
        ],
        "meta": EXAMPLE_META,
    }  # fmt: skip
    assert sum(part["proportionPct"] for part in data["plateComponents"]) == 100
    for part in data["plateComponents"]:
        assert_number(part["proportionPct"], part["proportionPct"], integer=True)


def test_shopping_checklist_pdf_example(db_client: TestClient) -> None:
    response = db_client.get(CHECKLIST + "?district=gasabo&household_size=4")
    assert response.status_code == 200
    data = raw_json(response)
    assert data == {
        "status": "available",
        "valueBasis": "pdf_example",
        "district": "gasabo",
        "items": [
            {"name": "Fresh Sweet Potatoes", "quantity": "3 kg", "estPrice": 2_400},
            {"name": "Local Red Kidney Beans", "quantity": "2 kg", "estPrice": 1_700},
            {"name": "Fresh Amaranth Greens (Dodo)", "quantity": "3 bundles", "estPrice": 650},
        ],
        "totalEstimatedBasket": 4_750,
        "unoptimizedBasket": 8_650,
        "estimatedSavings": 3_900,
        "assumptions": BASE_ASSUMPTIONS,
        "meta": EXAMPLE_META,
    }
    # The PDF prints 6,250 and 2,400; the owner chose the items' sum (contract §11.5).
    assert data["unoptimizedBasket"] - data["totalEstimatedBasket"] == data["estimatedSavings"]
    assert sum(item["estPrice"] for item in data["items"]) == data["totalEstimatedBasket"]


BASE_ASSUMPTIONS: Final = [
    EXAMPLE_ONLY,
    "illustrative_prices_not_market_observations",
    "total_is_the_sum_of_the_listed_items_not_the_pdf_printed_6250",
    "estimated_savings_is_the_unoptimized_basket_minus_the_total",
]
MODELLED_DISTRICT: Final = [
    "modelled_br_28_prices_scaled_from_gasabo_by_the_district_food_line_not_observed",
    "quantities_are_gasabo_s_for_the_same_household_size",
]
UNIFORM: Final = "benchmark_is_one_illustrative_basket_for_every_district"
MODELLED_SIZE: Final = [
    "modelled_br_24_square_root_scaling_from_household_size_4_not_observed",
    "prices_rounded_half_up_to_whole_rwf_quantities_to_0_1_unit",
    "item_prices_scaled_from_the_pdf_price_not_recomputed_from_rounded_quantities",
]


# BR-24 by hand: size 1 is × √(1/4) = 0.5 and size 9 is × √(9/4) = 1.5, both exact; size 5 is
# × √1.25 ≈ 1.118034, so 3 kg → 3.354 → 3.4 kg and 2,400 → 2,683.28 → 2,683 (half up).
# Totals are (Σ items, scaled 8,650, the difference).
@pytest.mark.parametrize(
    ("size", "items", "totals"),
    [
        (1, [("1.5 kg", 1_200), ("1 kg", 850), ("1.5 bundles", 325)], (2_375, 4_325, 1_950)),
        (9, [("4.5 kg", 3_600), ("3 kg", 2_550), ("4.5 bundles", 975)], (7_125, 12_975, 5_850)),
        (5, [("3.4 kg", 2_683), ("2.2 kg", 1_901), ("3.4 bundles", 727)], (5_311, 9_671, 4_360)),
        (20, [("6.7 kg", 5_367), ("4.5 kg", 3_801), ("6.7 bundles", 1_453)],
         (10_621, 19_342, 8_721)),
    ],
)  # fmt: skip
def test_shopping_checklist_other_gasabo_sizes_are_modelled(
    db_client: TestClient, size: int, items: list[tuple[str, int]], totals: tuple[int, int, int]
) -> None:
    """The owner-approved BR-24 scaling of the size-4 example, labelled as a model output."""
    data = raw_json(db_client.get(CHECKLIST + f"?district=gasabo&household_size={size}"))
    assert data["status"] == "available" and data["valueBasis"] == "modelled_from_pdf_example"
    assert [(item["quantity"], item["estPrice"]) for item in data["items"]] == items
    assert [item["name"] for item in data["items"]] == [
        "Fresh Sweet Potatoes", "Local Red Kidney Beans", "Fresh Amaranth Greens (Dodo)",
    ]  # fmt: skip
    assert (
        data["totalEstimatedBasket"], data["unoptimizedBasket"], data["estimatedSavings"]
    ) == totals  # fmt: skip
    assert data["assumptions"] == [*BASE_ASSUMPTIONS, *MODELLED_SIZE]
    assert data["meta"] == EXAMPLE_META


# BR-28 by hand, × 50,000 ÷ 65,000 (the PDF's Musanze and Gasabo food lines): 2,400 → 1,846.15,
# 1,700 → 1,307.69, 650 → 500, 8,650 → 6,653.85; then BR-24 for size 9 (× 1.5).
@pytest.mark.parametrize(
    ("size", "items", "totals"),
    [
        (4, [("3 kg", 1_846), ("2 kg", 1_308), ("3 bundles", 500)], (3_654, 6_654, 3_000)),
        (9, [("4.5 kg", 2_769), ("3 kg", 1_962), ("4.5 bundles", 750)], (5_481, 9_981, 4_500)),
    ],
)  # fmt: skip
def test_shopping_checklist_musanze_is_modelled_by_its_food_line(
    db_client: TestClient, size: int, items: list[tuple[str, int]], totals: tuple[int, int, int]
) -> None:
    data = raw_json(db_client.get(CHECKLIST + f"?district=musanze&household_size={size}"))
    assert data["status"] == "available" and data["valueBasis"] == "modelled_from_pdf_example"
    assert data["district"] == "musanze"
    assert [(item["quantity"], item["estPrice"]) for item in data["items"]] == items
    assert (
        data["totalEstimatedBasket"], data["unoptimizedBasket"], data["estimatedSavings"]
    ) == totals  # fmt: skip
    assert data["assumptions"] == [
        *BASE_ASSUMPTIONS, *MODELLED_DISTRICT, *([] if size == 4 else MODELLED_SIZE),
    ]  # fmt: skip
    assert data["meta"] == EXAMPLE_META


def test_shopping_checklist_benchmark_district_equals_gasabo(db_client: TestClient) -> None:
    """A benchmark district's food line is Gasabo's, so BR-28 leaves the prices unchanged."""
    huye = raw_json(db_client.get(CHECKLIST + "?district=huye&household_size=5"))
    gasabo = raw_json(db_client.get(CHECKLIST + "?district=gasabo&household_size=5"))
    fields = ("items", "totalEstimatedBasket", "unoptimizedBasket", "estimatedSavings")
    assert {k: huye[k] for k in fields} == {k: gasabo[k] for k in fields}
    assert huye["valueBasis"] == "modelled_from_pdf_example" and huye["district"] == "huye"
    assert huye["assumptions"] == [
        *BASE_ASSUMPTIONS, *MODELLED_DISTRICT, UNIFORM, *MODELLED_SIZE,
    ]  # fmt: skip


def test_shopping_checklist_is_available_for_every_district(db_client: TestClient) -> None:
    codes = [d["code"] for d in raw_json(db_client.get("/api/v1/districts"))["items"]]
    assert len(codes) == 30
    for code in codes:
        data = raw_json(db_client.get(CHECKLIST + f"?district={code}&household_size=4"))
        assert data["status"] == "available", code
        assert data["valueBasis"] == ("pdf_example" if code == "gasabo"
                                      else "modelled_from_pdf_example")  # fmt: skip
        assert len(data["items"]) == 3
        items_total = sum(item["estPrice"] for item in data["items"])
        assert items_total == data["totalEstimatedBasket"]
        savings = data["unoptimizedBasket"] - data["totalEstimatedBasket"]
        assert savings == data["estimatedSavings"]
        assert data["meta"] == EXAMPLE_META


def test_shopping_checklist_validates_its_query(db_client: TestClient) -> None:
    assert_problem(db_client.get(CHECKLIST + "?district=atlantis&household_size=4"), 404,
                   "district-not-found")  # fmt: skip
    assert_problem(db_client.get(CHECKLIST + "?district=GASABO&household_size=4"), 404,
                   "district-not-found")  # fmt: skip
    # Validation runs before the district lookup.
    assert_problem(db_client.get(CHECKLIST + "?district=atlantis&household_size=0"), 422,
                   "validation", ("household_size", "out_of_range"))  # fmt: skip
    assert_problem(db_client.get(CHECKLIST + "?household_size=4"), 422, "validation",
                   ("district", "required"))  # fmt: skip
    assert_problem(db_client.get(CHECKLIST + "?district=gasabo&household_size=21"), 422,
                   "validation", ("household_size", "out_of_range"))  # fmt: skip
    assert_problem(db_client.get(CHECKLIST + "?district=gasabo"), 422, "validation",
                   ("household_size", "required"))  # fmt: skip
    assert_problem(db_client.get(CHECKLIST + "?district=gasabo&householdSize=4"), 400,
                   "unknown-parameter", ("householdSize", "unknown_field"))  # fmt: skip


@pytest.mark.parametrize("raw", NOT_INTEGER_QUERY_VALUES)
def test_shopping_checklist_household_size_digits(db_client: TestClient, raw: str) -> None:
    response = db_client.get(CHECKLIST + f"?district=gasabo&household_size={raw}")
    assert_problem(response, 422, "validation", ("household_size", "not_integer"))


@pytest.mark.parametrize("path", [PLATE, CALENDAR])  # no query parameters
def test_static_content_takes_no_parameters(db_client: TestClient, path: str) -> None:
    assert_problem(db_client.get(path + "?month=10"), 400, "unknown-parameter",
                   ("month", "unknown_field"))  # fmt: skip


@pytest.mark.parametrize("path", [PLATE, CALENDAR, CHECKLIST + "?district=gasabo&household_size=4"])
def test_wrong_method_is_405(db_client: TestClient, path: str) -> None:
    assert_problem(db_client.post(path), 405, "method-not-allowed")


def test_openapi_documents_the_status(stub_app: FastAPI) -> None:
    spec = stub_app.openapi()
    for path in (PLATE, CALENDAR, CHECKLIST):
        assert "get" in spec["paths"][path]
    schemas = spec["components"]["schemas"]
    for name in ("BalancedPlateResponse", "HarvestCalendarResponse", "ShoppingChecklistResponse"):
        status = schemas[name]["properties"]["status"]
        assert set(status["enum"]) == {"available", "awaiting_validated_data"}
    checklist = schemas["ShoppingChecklistResponse"]["properties"]
    basis = checklist["valueBasis"]["anyOf"]
    assert {"pdf_example", "modelled_from_pdf_example"} <= set(basis[0].get("enum", []))
    assert "valueBasis" in schemas["ShoppingChecklistResponse"]["required"]
    for field in ("totalEstimatedBasket", "unoptimizedBasket", "estimatedSavings"):
        assert {o.get("type") for o in checklist[field]["anyOf"]} == {"integer", "null"}
    assert schemas["ChecklistItem"]["properties"]["estPrice"]["type"] == "integer"
    assert {p["name"] for p in spec["paths"][CHECKLIST]["get"]["parameters"]} == {
        "district", "household_size",
    }  # fmt: skip
