"""`GET /api/v1/seasonal-swaps` (contract §4). DB-backed."""

import pytest
from fastapi.testclient import TestClient

from tests.helpers import META, NOT_INTEGER_QUERY_VALUES, assert_number, assert_problem, raw_json

URL = "/api/v1/seasonal-swaps"


def test_gasabo_in_october_matches_the_contract(db_client: TestClient) -> None:
    response = db_client.get(f"{URL}?district=gasabo&month=10")
    data = raw_json(response)
    assert data["items"] == [
        {
            "id": "rice-to-sweet-potato",
            "title": "Try a different staple",
            "description": (
                "For one household meal, consider sweet potatoes instead of rice. "
                "Pair with beans and leafy vegetables."
            ),
            "from": {"name": "Rice", "quantity": 1, "unit": "kg", "price": 2_000},
            "to": {"name": "Sweet potatoes", "quantity": 2, "unit": "kg", "price": 1_600},
            "difference": 400,
            "footnote": (
                "Different quantities; not a nutritional equivalent. "
                "Prices are invented, not market observations."
            ),
        }
    ]
    assert data["tips"][0]["title"] == "Keep variety on the plate."
    assert data["meta"] == META
    assert_number(data["items"][0]["from"]["quantity"], 1, integer=False)


def test_the_swap_applies_to_every_district(db_client: TestClient) -> None:
    assert (
        db_client.get(f"{URL}?district=nyagatare&month=10").json()["items"][0]["difference"] == 400
    )


def test_other_months_have_no_swaps_but_keep_the_tip(db_client: TestClient) -> None:
    data = db_client.get(f"{URL}?district=gasabo&month=3").json()
    assert data["items"] == [] and len(data["tips"]) == 1


def test_unknown_district_is_404(db_client: TestClient) -> None:
    assert_problem(db_client.get(f"{URL}?district=atlantis&month=10"), 404, "district-not-found")


@pytest.mark.parametrize("raw", NOT_INTEGER_QUERY_VALUES)
def test_month_not_integer(db_client: TestClient, raw: str) -> None:
    assert_problem(
        db_client.get(f"{URL}?district=gasabo&month={raw}"),
        422,
        "validation",
        ("month", "not_integer"),
    )


@pytest.mark.parametrize("raw", ["0", "13"])
def test_month_out_of_range(db_client: TestClient, raw: str) -> None:
    assert_problem(
        db_client.get(f"{URL}?district=gasabo&month={raw}"),
        422,
        "validation",
        ("month", "out_of_range"),
    )


def test_both_parameters_are_required(db_client: TestClient) -> None:
    assert_problem(
        db_client.get(URL), 422, "validation", ("district", "required"), ("month", "required")
    )
