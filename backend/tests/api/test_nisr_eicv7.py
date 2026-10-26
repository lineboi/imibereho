"""`/api/v1/nisr/poverty` and `/api/v1/nisr/health-insurance`: EICV7 2023/24 estimates.

DB-backed tests read the seeded test database. The awaiting-data and null-serialisation tests
swap in a fake repository, so they need no database.
"""

from collections.abc import Iterator, Sequence
from decimal import Decimal
from typing import Any, Final, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.data.eicv7_2023_24 import SOURCE
from app.data.reference import DISTRICT_CODES
from app.models import StatisticalSource, SurveyEstimate
from app.repositories.official_statistics_repository import OfficialStatisticsRepository
from app.services.household_survey_service import (
    HouseholdSurveyService,
    get_household_survey_service,
)
from tests.api.test_nisr import assert_official_meta
from tests.helpers import assert_problem, raw_json

BASE: Final = "/api/v1/nisr"
SOURCE_ID: Final = "eicv7-2023-2024"
UNCERTAINTY: Final = ("standardErrorPct", "ciLowerPct", "ciUpperPct", "cvPct", "designEffect")
ITEM_KEYS: Final = {
    "indicatorCode", "tableId", "dimension", "code", "label", "districtCode", "estimatePct",
    *UNCERTAINTY, "notes",
}  # fmt: skip


def item(data: dict[str, Any], dimension: str, code: str) -> dict[str, Any]:
    return next(i for i in data["items"] if i["dimension"] == dimension and i["code"] == code)


def assert_exact(value: object, published: str) -> None:
    """A JSON number that parses to exactly the workbook's stored double: its 17-significant-
    digit form is the published text (the wire uses the shortest form of the same double)."""
    assert isinstance(value, float), value
    assert Decimal(format(value, ".17g")) == Decimal(published)


# --- DB-backed: the seeded EICV7 data ---


def test_poverty_response(db_client: TestClient) -> None:
    response = db_client.get(f"{BASE}/poverty")
    assert response.status_code == 200
    data = raw_json(response)
    assert data["status"] == "available"
    assert_official_meta(data["meta"], 38, [SOURCE_ID])
    assert data["dimensions"] == ["national", "area", "province", "district"]
    assert data["indicator"] == {
        "code": "poverty_headcount_rate",
        "tableId": "A9.23",
        "label": "Headcount poverty rate",
        "definition": data["indicator"]["definition"],
        "population": "All individuals in the household-based population",
        "unit": "percent",
        "surveyRound": "2023/24",
        "printedDecimals": 2,
        "citation": {
            "page": 107,
            "tableOrFigure": "Table A9.23: Headcount Poverty rate(%) by area of residence, "
            "province and district",
        },
    }
    poverty_line = "RWF 560,127 per adult equivalent per year in January 2024 prices"
    assert poverty_line in data["indicator"]["definition"]
    assert data["source"]["id"] == SOURCE_ID
    assert data["source"]["publisher"] == "National Institute of Statistics of Rwanda (NISR)"
    assert data["source"]["fieldworkPeriod"].startswith("October 2023 - October 2024")


def test_poverty_values_are_exact(db_client: TestClient) -> None:
    response = db_client.get(f"{BASE}/poverty")
    data = raw_json(response)
    national = item(data, "national", "rwanda")
    assert set(national) == ITEM_KEYS
    assert national["label"] == "Poverty Rate" and national["districtCode"] is None
    assert national["tableId"] == "A9.23"
    published = ("27.362976067289672", "0.49624639004466625", "26.389621090104246",
                 "28.336331044475099", "1.8135687756489709", "1.8650754691612403")  # fmt: skip
    for key, text in zip(("estimatePct", *UNCERTAINTY), published, strict=True):
        assert_exact(national[key], text)
    assert '"estimatePct":27.362976067289672' in response.text  # full precision on the wire
    nyamagabe = item(data, "district", "nyamagabe")
    assert nyamagabe["districtCode"] == "nyamagabe"
    assert_exact(nyamagabe["estimatePct"], "51.39408818367712")
    assert_exact(nyamagabe["ciUpperPct"], "57.698173083125276")
    kigali = item(data, "province", "city_of_kigali")
    assert kigali["label"] == "City of Kigali"
    assert_exact(kigali["estimatePct"], "9.0541946554448476")


def test_health_insurance_response(db_client: TestClient) -> None:
    data = raw_json(db_client.get(f"{BASE}/health-insurance"))
    assert data["status"] == "available"
    assert_official_meta(data["meta"], 45, [SOURCE_ID])
    assert data["dimensions"] == ["national", "sex", "area", "province", "quintile", "district"]
    assert data["indicator"]["code"] == "health_insurance_coverage"
    assert data["indicator"]["tableId"] == "A3.7"
    assert data["indicator"]["citation"]["page"] == 91
    assert_exact(item(data, "national", "rwanda")["estimatePct"], "85.310917075321285")
    assert_exact(item(data, "sex", "female")["estimatePct"], "85.677015852419231")
    assert_exact(item(data, "sex", "male")["designEffect"], "3.4873094645318745")
    assert_exact(item(data, "area", "rural")["estimatePct"], "85.404110132167702")
    assert_exact(item(data, "quintile", "q1")["estimatePct"], "76.018949867683503")
    assert_exact(item(data, "quintile", "q5")["ciLowerPct"], "92.509701024087406")
    assert_exact(item(data, "province", "northern")["estimatePct"], "91.673941182269573")
    assert_exact(item(data, "district", "gakenke")["estimatePct"], "96.349709583879303")
    assert [i["code"] for i in data["items"] if i["dimension"] == "quintile"] == [
        "q1", "q2", "q3", "q4", "q5",
    ]  # fmt: skip


@pytest.mark.parametrize("path", ["/poverty", "/health-insurance"])
def test_thirty_districts_and_consistent_records(db_client: TestClient, path: str) -> None:
    data = raw_json(db_client.get(f"{BASE}{path}"))
    districts = [i for i in data["items"] if i["dimension"] == "district"]
    assert sorted(i["code"] for i in districts) == sorted(DISTRICT_CODES)
    assert all(i["districtCode"] == i["code"] for i in districts)
    assert all(i["districtCode"] is None for i in data["items"] if i["dimension"] != "district")
    assert len({(i["dimension"], i["code"]) for i in data["items"]}) == len(data["items"])
    for record in data["items"]:
        assert set(record) == ITEM_KEYS
        assert record["indicatorCode"] == data["indicator"]["code"]
        assert 0 <= record["ciLowerPct"] <= record["estimatePct"] <= record["ciUpperPct"] <= 100
        assert all(isinstance(record[key], float) and record[key] >= 0 for key in UNCERTAINTY)


def test_source_notes_and_record_notes(db_client: TestClient) -> None:
    data = raw_json(db_client.get(f"{BASE}/poverty"))
    assert "46.6%" in item(data, "district", "gisagara")["notes"]
    assert item(data, "district", "huye")["notes"] is None
    notes = data["source"]["notes"]
    assert "modelled 2016/17 rate of 39.8%" in notes and "not directly comparable" in notes


def test_eicv7_is_listed_with_finscope_in_sources(db_client: TestClient) -> None:
    data = raw_json(db_client.get(f"{BASE}/sources"))
    eicv7 = next(s for s in data["items"] if s["id"] == SOURCE_ID)
    assert eicv7["sampleSize"] == 15_054
    assert eicv7["surveyRound"] == "2023/24"
    assert eicv7["documentSha256"] == SOURCE["document_sha256"]
    assert eicv7["documentFile"] == "EICV7_Tables_MainIndicatorReport.xlsx"
    assert eicv7["retrievedOn"] == "2026-10-26"


def test_finscope_endpoints_do_not_include_eicv7(db_client: TestClient) -> None:
    for path in ("/financial-inclusion/national", "/financial-inclusion/districts"):
        assert raw_json(db_client.get(f"{BASE}{path}"))["meta"]["sourceIds"] == ["finscope-2024"]


@pytest.mark.parametrize("path", ["/poverty", "/health-insurance"])
def test_unknown_query_parameter_is_400(db_client: TestClient, path: str) -> None:
    response = db_client.get(f"{BASE}{path}?district=gasabo")
    assert_problem(response, 400, "unknown-parameter", ("district", "unknown_field"))


@pytest.mark.parametrize("path", ["/poverty", "/health-insurance"])
@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_wrong_method_is_405(db_client: TestClient, path: str, method: str) -> None:
    assert_problem(getattr(db_client, method)(f"{BASE}{path}"), 405, "method-not-allowed")


@pytest.mark.parametrize("path", ["/poverty/districts", "/health-insurance/national", "/eicv7"])
def test_unknown_paths_are_404(db_client: TestClient, path: str) -> None:
    assert_problem(db_client.get(f"{BASE}{path}"), 404, "not-found")


# --- DB-free: fake repositories ---


def _source() -> StatisticalSource:
    return StatisticalSource(**SOURCE)


def _estimate(**overrides: object) -> SurveyEstimate:
    values: dict[str, object] = {
        "source_id": SOURCE_ID,
        "table_id": "A9.23",
        "indicator_code": "poverty_headcount_rate",
        "dimension": "district",
        "category_code": "huye",
        "district_code": "huye",
        "label": "Huye",
        "indicator_label": "Headcount poverty rate",
        "definition": "…",
        "population": "All individuals in the household-based population",
        "unit": "percent",
        "survey_round": "2023/24",
        "estimate_pct": Decimal("24.190701339070184"),
        "standard_error_pct": None,
        "ci_lower_pct": None,
        "ci_upper_pct": None,
        "cv_pct": None,
        "design_effect": None,
        "printed_decimals": 2,
        "page": 107,
        "table_or_figure": "Table A9.23",
        "notes": None,
        "sort_order": 1,
    }
    return SurveyEstimate(**(values | overrides))


class _FakeRepository(OfficialStatisticsRepository):
    def __init__(self, source: StatisticalSource | None, rows: list[SurveyEstimate]) -> None:
        super().__init__(cast(Session, None))
        self.source, self.rows = source, rows

    def get_source(self, source_id: str) -> StatisticalSource | None:
        return self.source if self.source is not None and source_id == self.source.id else None

    def list_survey_estimates(
        self, source_id: str, indicator_code: str
    ) -> Sequence[SurveyEstimate]:
        return [r for r in self.rows if r.indicator_code == indicator_code]


@pytest.fixture
def fake_client(stub_app: FastAPI) -> Iterator[Any]:
    def install(source: StatisticalSource | None, rows: list[SurveyEstimate]) -> TestClient:
        stub_app.dependency_overrides[get_household_survey_service] = lambda: (
            HouseholdSurveyService(_FakeRepository(source, rows))
        )
        return TestClient(stub_app)

    yield install
    stub_app.dependency_overrides.clear()


@pytest.mark.parametrize("with_source", [False, True], ids=["no-source", "source-without-rows"])
@pytest.mark.parametrize("path", ["/poverty", "/health-insurance"])
def test_awaiting_validated_data(fake_client: Any, with_source: bool, path: str) -> None:
    client = fake_client(_source() if with_source else None, [])
    data = raw_json(client.get(f"{BASE}{path}"))
    assert data["status"] == "awaiting_validated_data"
    assert data["items"] == [] and data["dimensions"] == [] and data["indicator"] is None
    assert data["meta"] == {
        "isIllustrative": False,
        "dataKind": "official_published_statistics",
        "sourceIds": [SOURCE_ID] if with_source else [],
        "count": 0,
    }
    assert (data["source"] is not None) is with_source


def test_rows_without_their_source_are_not_served(fake_client: Any) -> None:
    client = fake_client(None, [_estimate()])
    assert raw_json(client.get(f"{BASE}/poverty"))["status"] == "awaiting_validated_data"


def test_unpublished_uncertainty_serialises_as_null(fake_client: Any) -> None:
    client = fake_client(_source(), [_estimate()])
    response = client.get(f"{BASE}/poverty")
    huye = raw_json(response)["items"][0]
    assert all(huye[key] is None for key in UNCERTAINTY)
    assert '"standardErrorPct":null' in response.text and '"designEffect":null' in response.text
    assert huye["estimatePct"] == 24.190701339070184
    # The other indicator never borrows these rows.
    assert raw_json(client.get(f"{BASE}/health-insurance"))["items"] == []


def test_openapi_documents_both_routes(stub_app: FastAPI) -> None:
    spec = stub_app.openapi()
    for path in ("/poverty", "/health-insurance"):
        operation = spec["paths"][f"{BASE}{path}"]["get"]
        schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        assert schema == {"$ref": "#/components/schemas/SurveyIndicatorEstimates"}
        assert "400" in operation["responses"]
    schemas = spec["components"]["schemas"]
    estimate = schemas["SurveyEstimateOut"]["properties"]
    assert estimate["estimatePct"]["type"] == "number"
    for key in UNCERTAINTY:
        assert {o.get("type") for o in estimate[key]["anyOf"]} == {"number", "null"}
    assert set(estimate["dimension"]["enum"]) == {
        "national", "area", "province", "sex", "quintile", "district",
    }  # fmt: skip
    response = schemas["SurveyIndicatorEstimates"]["properties"]
    assert set(response["status"]["enum"]) == {"available", "awaiting_validated_data"}
    assert schemas["SurveyIndicator"]["properties"]["printedDecimals"]["type"] == "integer"
