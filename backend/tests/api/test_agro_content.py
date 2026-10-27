"""Nutrition, harvest calendar and shopping checklist (contract v0.4 §11.5, PDF pages 10-11).

The project has no cited source for any of this content, so each endpoint answers with
`status: "awaiting_validated_data"` and empty or null content. These tests pin that nothing
(no plate proportions, season months, prices or tips) is invented.
"""

from typing import Final

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.helpers import META, NOT_INTEGER_QUERY_VALUES, assert_problem, raw_json

PLATE: Final = "/api/v1/nutrition/indyo-yuzuye"
CALENDAR: Final = "/api/v1/agro/harvest-calendar"
CHECKLIST: Final = "/api/v1/market/shopping-checklist"
AWAITING: Final = ["awaiting_a_cited_official_source", "no_content_is_invented"]


def test_balanced_plate_is_awaiting_a_source(db_client: TestClient) -> None:
    response = db_client.get(PLATE)
    assert response.status_code == 200
    assert raw_json(response) == {
        "status": "awaiting_validated_data",
        "standard": "Indyo Yuzuye",
        "plateComponents": [],
        "energyTip": None,
        "assumptions": AWAITING,
        "meta": META,
    }


def test_harvest_calendar_is_awaiting_a_source(db_client: TestClient) -> None:
    assert raw_json(db_client.get(CALENDAR)) == {
        "status": "awaiting_validated_data",
        "activeSeason": None,
        "seasonName": None,
        "monthsRange": None,
        "harvestHighlights": [],
        "assumptions": AWAITING,
        "meta": META,
    }


def test_shopping_checklist_is_awaiting_prices(db_client: TestClient) -> None:
    response = db_client.get(CHECKLIST + "?district=gasabo&household_size=4")
    assert raw_json(response) == {
        "status": "awaiting_validated_data",
        "district": "gasabo",
        "items": [],
        "totalEstimatedBasket": None,
        "unoptimizedBasket": None,
        "estimatedSavings": None,
        "assumptions": [*AWAITING, "needs_sourced_district_market_prices"],
        "meta": META,
    }
    assert '"totalEstimatedBasket":null' in response.text


def test_shopping_checklist_validates_its_query(db_client: TestClient) -> None:
    assert_problem(db_client.get(CHECKLIST + "?district=atlantis&household_size=4"), 404,
                   "district-not-found")  # fmt: skip
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


@pytest.mark.parametrize("path", [PLATE, CALENDAR])
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
