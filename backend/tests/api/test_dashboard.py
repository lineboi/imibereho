"""Dashboard filters and overview (contract §5). DB-backed."""

import pytest
from fastapi.testclient import TestClient

from tests.helpers import META, NOT_INTEGER_QUERY_VALUES, assert_number, assert_problem, raw_json

OVERVIEW = "/api/v1/dashboard/overview"


def test_filters_offer_only_the_design_defaults(db_client: TestClient) -> None:
    assert db_client.get("/api/v1/dashboard/filters").json() == {
        "geographies": [{"code": "all", "label": "All districts", "isDefault": True}],
        "periods": [{"code": "2026-10", "label": "Demo month · October", "isDefault": True}],
        "householdGroups": [{"code": "all", "label": "All sample households", "isDefault": True}],
        "meta": META,
    }


def test_filters_refuse_parameters(db_client: TestClient) -> None:
    assert_problem(db_client.get("/api/v1/dashboard/filters?x=1"), 400, "unknown-parameter")


def test_overview_design_values(db_client: TestClient) -> None:
    data = raw_json(db_client.get(OVERVIEW))
    kpis = data["kpis"]
    assert_number(kpis["sampleSize"], 3_000, integer=True)
    assert kpis["referenceHousehold"] == {
        "districtCode": "gasabo",
        "householdSize": 4,
        "monthlyIncome": 180_000,
        "monthlyEssentials": 150_000,
        "savings": 60_000,
    }
    assert_number(kpis["essentialsToIncomeRatio"], 0.8333, integer=False)
    assert kpis["shockDeficit"]["incomeReductionPct"] == 20
    assert_number(kpis["shockDeficit"]["householdsInDeficit"], 1_000, integer=True)
    assert_number(kpis["shockDeficit"]["share"], 0.3333, integer=False)
    assert data["essentialsTrend"] == {
        "unit": "RWF",
        "incomeReference": 180_000,
        "points": [
            {"month": "2026-05", "essentials": 138_000},
            {"month": "2026-06", "essentials": 140_000},
            {"month": "2026-07", "essentials": 143_000},
            {"month": "2026-08", "essentials": 145_000},
            {"month": "2026-09", "essentials": 148_000},
            {"month": "2026-10", "essentials": 150_000},
        ],
    }
    assert data["incomeSources"] == [
        {"code": "wage", "label": "Wage income", "households": 1_200, "share": 0.4},
        {"code": "agriculture", "label": "Agriculture", "households": 1_050, "share": 0.35},
        {
            "code": "informal_enterprise",
            "label": "Informal enterprise",
            "households": 750,
            "share": 0.25,
        },
    ]
    for source in data["incomeSources"]:
        assert isinstance(source["share"], float)
    assert data["insight"] == {
        "baselineMonthlyBalance": 30_000,
        "shockMonthlyGap": 6_000,
        "incomeReductionPct": 20,
    }
    assert data["topDistricts"] == [
        {"code": "nyagatare", "name": "Nyagatare", "score": 74, "band": "band4"},
        {"code": "bugesera", "name": "Bugesera", "score": 71, "band": "band4"},
    ]
    assert data["meta"] == META


def test_top_n(db_client: TestClient) -> None:
    assert len(db_client.get(f"{OVERVIEW}?topN=6").json()["topDistricts"]) == 6


@pytest.mark.parametrize(
    ("query", "field"),
    [("geography=gasabo", "geography"), ("geography=atlantis", "geography"),
     ("period=2026-09", "period"), ("householdGroup=wage", "householdGroup")],
)  # fmt: skip
def test_unlisted_filter_values_are_422_never_404(
    db_client: TestClient, query: str, field: str
) -> None:
    assert_problem(
        db_client.get(f"{OVERVIEW}?{query}"), 422, "validation", (field, "unknown_value")
    )


@pytest.mark.parametrize("raw", NOT_INTEGER_QUERY_VALUES)
def test_top_n_not_integer(db_client: TestClient, raw: str) -> None:
    assert_problem(
        db_client.get(f"{OVERVIEW}?topN={raw}"), 422, "validation", ("topN", "not_integer")
    )


@pytest.mark.parametrize("raw", ["0", "31"])
def test_top_n_out_of_range(db_client: TestClient, raw: str) -> None:
    assert_problem(
        db_client.get(f"{OVERVIEW}?topN={raw}"), 422, "validation", ("topN", "out_of_range")
    )
