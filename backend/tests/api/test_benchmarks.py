"""Reference data (contract §3) and `GET /api/v1/budget-benchmarks` (contract §4). DB-backed."""

import pytest
from fastapi.testclient import TestClient

from tests.helpers import META, NOT_INTEGER_QUERY_VALUES, assert_number, assert_problem, raw_json

BENCHMARKS = "/api/v1/budget-benchmarks"


def test_districts_are_thirty_alphabetical(db_client: TestClient) -> None:
    data = raw_json(db_client.get("/api/v1/districts"))
    assert data["meta"] == {**META, "count": 30}
    assert_number(data["meta"]["count"], 30, integer=True)
    assert data["items"][0] == {"code": "bugesera", "name": "Bugesera", "province": None}
    names = [item["name"] for item in data["items"]]
    assert names == sorted(names) and "Gasabo" in names


def test_expense_categories_match_the_contract(db_client: TestClient) -> None:
    data = db_client.get("/api/v1/expense-categories").json()
    assert data["items"] == [
        {"code": "food", "name": "Food", "icon": "shopping-basket"},
        {"code": "housing", "name": "Housing", "icon": None},
        {"code": "transport", "name": "Transport", "icon": "bus"},
        {"code": "utilities", "name": "Utilities", "icon": "zap"},
        {"code": "other_essentials", "name": "Other essentials", "icon": None},
    ]
    assert data["meta"] == {**META, "count": 5}


@pytest.mark.parametrize("path", ["/api/v1/districts", "/api/v1/expense-categories"])
def test_reference_lists_refuse_any_parameter(db_client: TestClient, path: str) -> None:
    assert_problem(
        db_client.get(path + "?lang=rw"), 400, "unknown-parameter", ("lang", "unknown_field")
    )


def test_benchmark_design_values(db_client: TestClient) -> None:
    response = db_client.get(f"{BENCHMARKS}?district=gasabo&householdSize=4")
    data = raw_json(response)
    assert data == {
        "district": {"code": "gasabo", "name": "Gasabo"},
        "householdSize": 4,
        "lines": [
            {"categoryCode": "food", "monthlyAmount": 65_000},
            {"categoryCode": "housing", "monthlyAmount": 40_000},
            {"categoryCode": "transport", "monthlyAmount": 20_000},
            {"categoryCode": "utilities", "monthlyAmount": 10_000},
            {"categoryCode": "other_essentials", "monthlyAmount": 15_000},
        ],
        "total": 150_000,
        "meta": META,
    }
    assert_number(data["total"], 150_000, integer=True)


def test_every_district_has_the_illustrative_set(db_client: TestClient) -> None:
    assert (
        db_client.get(f"{BENCHMARKS}?district=nyagatare&householdSize=4").json()["total"] == 150_000
    )


@pytest.mark.parametrize("raw", ["4", "%34", "04"])
def test_household_size_accepted_forms(db_client: TestClient, raw: str) -> None:
    assert db_client.get(f"{BENCHMARKS}?district=gasabo&householdSize={raw}").status_code == 200


@pytest.mark.parametrize("raw", NOT_INTEGER_QUERY_VALUES)
def test_household_size_not_integer(db_client: TestClient, raw: str) -> None:
    response = db_client.get(f"{BENCHMARKS}?district=gasabo&householdSize={raw}")
    assert_problem(response, 422, "validation", ("householdSize", "not_integer"))


@pytest.mark.parametrize("raw", ["0", "21"])
def test_household_size_out_of_range(db_client: TestClient, raw: str) -> None:
    response = db_client.get(f"{BENCHMARKS}?district=gasabo&householdSize={raw}")
    assert_problem(response, 422, "validation", ("householdSize", "out_of_range"))


def test_missing_parameters_are_required(db_client: TestClient) -> None:
    assert_problem(
        db_client.get(f"{BENCHMARKS}?householdSize=4"), 422, "validation", ("district", "required")
    )
    assert_problem(
        db_client.get(f"{BENCHMARKS}?district=gasabo"),
        422,
        "validation",
        ("householdSize", "required"),
    )


def test_unknown_district_is_404(db_client: TestClient) -> None:
    assert_problem(
        db_client.get(f"{BENCHMARKS}?district=atlantis&householdSize=4"), 404, "district-not-found"
    )


def test_district_codes_are_case_sensitive(db_client: TestClient) -> None:
    assert_problem(
        db_client.get(f"{BENCHMARKS}?district=Gasabo&householdSize=4"), 404, "district-not-found"
    )


def test_other_household_size_is_benchmark_not_available(db_client: TestClient) -> None:
    assert_problem(
        db_client.get(f"{BENCHMARKS}?district=gasabo&householdSize=3"),
        404,
        "benchmark-not-available",
    )


def test_validation_runs_before_the_district_lookup(db_client: TestClient) -> None:
    response = db_client.get(f"{BENCHMARKS}?district=atlantis&householdSize=0")
    assert_problem(response, 422, "validation", ("householdSize", "out_of_range"))


def test_unknown_parameter_is_400(db_client: TestClient) -> None:
    response = db_client.get(f"{BENCHMARKS}?district=gasabo&householdSize=4&income=180000")
    assert_problem(response, 400, "unknown-parameter", ("income", "unknown_field"))
