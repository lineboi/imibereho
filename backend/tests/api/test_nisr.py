"""`/api/v1/nisr/*`: official FinScope 2024 statistics with provenance.

DB-backed tests read the seeded test database; the awaiting-data tests swap in an empty
repository, so they need no database.
"""

from collections.abc import Iterator, Sequence
from datetime import date
from typing import Any, Final, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import FinancialAccessStrandDistrict, FinancialInclusionIndicator, StatisticalSource
from app.repositories.official_statistics_repository import OfficialStatisticsRepository
from app.services.financial_inclusion_service import (
    FinancialInclusionService,
    get_financial_inclusion_service,
)
from tests.helpers import assert_number, assert_problem, raw_json

BASE: Final = "/api/v1/nisr"
SHA256: Final = "981727b88cd05fe271b64c3a4541a1c0931e5934cdc7c9eb4fd3e6da67d81026"
OFFICIAL_META_KEYS: Final = {"isIllustrative", "dataKind", "sourceIds", "count"}


def assert_official_meta(meta: dict[str, Any], count: int, source_ids: list[str]) -> None:
    assert set(meta) == OFFICIAL_META_KEYS
    assert meta["isIllustrative"] is False
    assert meta["dataKind"] == "official_published_statistics"
    assert meta["sourceIds"] == source_ids
    assert_number(meta["count"], count, integer=True)


# --- DB-backed: the seeded FinScope 2024 data ---


def test_sources_list_full_provenance(db_client: TestClient) -> None:
    data = raw_json(db_client.get(f"{BASE}/sources"))
    # Sorted by id; EICV7 and SAS 2025 have their own provenance tests
    # (tests/api/test_nisr_eicv7.py, tests/api/test_harvest_calendar.py).
    assert_official_meta(data["meta"], 3, ["eicv7-2023-2024", "finscope-2024", "sas-2025"])
    source = next(item for item in data["items"] if item["id"] == "finscope-2024")
    assert source["publisher"] == "Access to Finance Rwanda (AFR)"
    assert source["citation"] == "Access to Finance Rwanda, FinScope 2024 report, June 2024"
    assert source["publicationDate"] == "2024-06"
    assert source["surveyRound"] == "2024"
    assert source["fieldworkPeriod"] is None
    assert source["sampleSize"] == 13_994
    assert source["lowestPublishedGeography"] == "district"
    assert source["documentSha256"] == SHA256
    assert source["documentUrl"] == (
        "https://microdata.statistics.gov.rw/index.php/catalog/120/download/1085"
    )
    assert source["retrievedOn"] == "2026-10-26"


@pytest.mark.parametrize(
    ("code", "value", "comparison"),
    [
        ("financially_included", 96, 93),
        ("formally_served", 92, 77),
        ("financially_excluded", 4, 7),
        ("financially_healthy", 10, 4),
        ("financially_vulnerable", 31, 37),
    ],
)
def test_national_indicator_values(
    db_client: TestClient, code: str, value: int, comparison: int
) -> None:
    data = raw_json(db_client.get(f"{BASE}/financial-inclusion/national"))
    indicator = next(i for i in data["indicators"] if i["code"] == code)
    assert_number(indicator["valuePct"], value, integer=True)
    assert indicator["year"] == 2024 and indicator["unit"] == "percent"
    assert indicator["comparison"]["year"] == 2020
    assert_number(indicator["comparison"]["valuePct"], comparison, integer=True)
    assert indicator["population"] == "Adults aged 16 years and older"
    assert indicator["citation"]["page"] > 0 and "Figure" in indicator["citation"]["tableOrFigure"]


def test_national_response_shape_and_source(db_client: TestClient) -> None:
    data = raw_json(db_client.get(f"{BASE}/financial-inclusion/national"))
    assert data["status"] == "available"
    assert data["geographicLevel"] == "national"
    assert data["source"]["id"] == "finscope-2024"
    assert [i["code"] for i in data["indicators"]][:3] == [
        "financially_included",
        "formally_served",
        "financially_excluded",
    ]
    assert_official_meta(data["meta"], 11, ["finscope-2024"])
    included = data["indicators"][0]
    assert included["countPublished"] == "7.8 million"
    excluded = next(i for i in data["indicators"] if i["code"] == "financially_excluded")
    assert excluded["countPublished"] is None  # the report gives 316,000 and 317,000
    assert "316,000" in excluded["notes"] and "317,000" in excluded["notes"]


def test_district_strands(db_client: TestClient) -> None:
    data = raw_json(db_client.get(f"{BASE}/financial-inclusion/districts"))
    assert data["status"] == "available"
    assert data["geographicLevel"] == "district"
    assert [c["code"] for c in data["categories"]] == [
        "banked",
        "otherFormalNonBank",
        "informalOnly",
        "excluded",
    ]
    assert_official_meta(data["meta"], 30, ["finscope-2024"])
    items = {item["districtCode"]: item for item in data["items"]}
    assert len(items) == 30
    names = [item["name"] for item in data["items"]]
    assert names == sorted(names)
    gasabo = items["gasabo"]
    assert (gasabo["bankedPct"], gasabo["otherFormalNonBankPct"]) == (51, 46)
    assert (gasabo["informalOnlyPct"], gasabo["excludedPct"]) == (2, 1)
    assert gasabo["citation"] == {
        "page": 31,
        "tableOrFigure": "Figure 13: Financia [sic] Access Strand by districts (%)",
    }
    nyaruguru = items["nyaruguru"]
    assert (nyaruguru["bankedPct"], nyaruguru["excludedPct"]) == (6, 10)


def test_unlabelled_district_value_is_null_with_a_note(db_client: TestClient) -> None:
    response = db_client.get(f"{BASE}/financial-inclusion/districts")
    nyarugenge = next(i for i in response.json()["items"] if i["districtCode"] == "nyarugenge")
    assert nyarugenge["informalOnlyPct"] is None
    assert '"informalOnlyPct":null' in response.text
    assert "not assumed to be 0" in nyarugenge["notes"]
    others = [i for i in response.json()["items"] if i["districtCode"] != "nyarugenge"]
    assert all(isinstance(i["informalOnlyPct"], int) and i["notes"] is None for i in others)


@pytest.mark.parametrize(
    "path", ["/sources", "/financial-inclusion/national", "/financial-inclusion/districts"]
)
def test_unknown_query_parameter_is_400(db_client: TestClient, path: str) -> None:
    response = db_client.get(f"{BASE}{path}?district=gasabo")
    assert_problem(response, 400, "unknown-parameter", ("district", "unknown_field"))


@pytest.mark.parametrize(
    "path", ["/sources", "/financial-inclusion/national", "/financial-inclusion/districts"]
)
def test_wrong_method_is_405(db_client: TestClient, path: str) -> None:
    assert_problem(db_client.post(f"{BASE}{path}"), 405, "method-not-allowed")


def test_unknown_nisr_route_is_404(db_client: TestClient) -> None:
    assert_problem(db_client.get(f"{BASE}/financial-inclusion/provinces"), 404, "not-found")


# --- DB-free: no validated data loaded ---


class _EmptyRepository(OfficialStatisticsRepository):
    def __init__(self, *, with_source: bool) -> None:
        super().__init__(cast(Session, None))
        self.with_source = with_source

    def list_sources(self) -> Sequence[StatisticalSource]:
        return []

    def get_source(self, source_id: str) -> StatisticalSource | None:
        if not self.with_source:
            return None
        return StatisticalSource(
            id=source_id,
            title="Rwanda FinScope Survey 2024",
            publisher="Access to Finance Rwanda (AFR)",
            sponsors=None,
            distributor=None,
            citation="Access to Finance Rwanda, FinScope 2024 report, June 2024",
            publication_date="2024-06",
            survey_round="2024",
            fieldwork_period=None,
            population="Adults aged 16 years and older",
            sample_size=13_994,
            lowest_published_geography="district",
            document_file="report.pdf",
            document_url="https://microdata.statistics.gov.rw/index.php/catalog/120/download/1085",
            catalog_url=None,
            document_sha256=SHA256,
            retrieved_on=date(2026, 10, 26),
            notes=None,
        )

    def list_national_indicators(self, source_id: str) -> Sequence[FinancialInclusionIndicator]:
        return []

    def list_district_strands(
        self, source_id: str
    ) -> Sequence[tuple[FinancialAccessStrandDistrict, str]]:
        return []


@pytest.fixture(params=[False, True], ids=["no-source", "source-without-rows"])
def empty_client(request: pytest.FixtureRequest, stub_app: FastAPI) -> Iterator[TestClient]:
    repository = _EmptyRepository(with_source=request.param)
    stub_app.dependency_overrides[get_financial_inclusion_service] = lambda: (
        FinancialInclusionService(repository)
    )
    with TestClient(stub_app) as client:
        yield client
    stub_app.dependency_overrides.clear()


def test_districts_awaiting_validated_data(empty_client: TestClient) -> None:
    data = raw_json(empty_client.get(f"{BASE}/financial-inclusion/districts"))
    assert data["status"] == "awaiting_validated_data"
    assert data["items"] == []
    assert data["meta"]["count"] == 0 and data["meta"]["isIllustrative"] is False
    assert len(data["categories"]) == 4  # definitions stay available for the UI


def test_national_awaiting_validated_data(empty_client: TestClient) -> None:
    data = raw_json(empty_client.get(f"{BASE}/financial-inclusion/national"))
    assert data["status"] == "awaiting_validated_data"
    assert data["indicators"] == []
    assert data["meta"]["count"] == 0


def test_no_sources_is_an_empty_list(empty_client: TestClient) -> None:
    data = raw_json(empty_client.get(f"{BASE}/sources"))
    assert data["items"] == [] and data["meta"]["sourceIds"] == []


def test_openapi_types_for_the_frontend(stub_app: FastAPI) -> None:
    schemas = stub_app.openapi()["components"]["schemas"]
    district = schemas["DistrictAccessStrand"]["properties"]
    assert district["bankedPct"]["type"] == "integer"
    assert {o.get("type") for o in district["informalOnlyPct"]["anyOf"]} == {"integer", "null"}
    meta = schemas["OfficialListMeta"]["properties"]
    assert meta["isIllustrative"]["const"] is False
    paths = stub_app.openapi()["paths"]
    for path in ("/sources", "/financial-inclusion/national", "/financial-inclusion/districts"):
        assert f"{BASE}{path}" in paths
