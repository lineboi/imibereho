"""`GET /api/v1/agro/harvest-calendar` (contract v0.4 §11.5, MISSING_APIS.pdf page 11).

Official NISR data (Seasonal Agricultural Survey 2025): the season calendar and each season's
largest crops by production. The active season comes from the current month in Kigali, so the
tests pin the date through a dependency override.
"""

from collections.abc import Iterator, Sequence
from datetime import date
from typing import Annotated, Any, Final, cast

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_read_session
from app.models import StatisticalSource
from app.repositories.official_statistics_repository import OfficialStatisticsRepository
from app.services.harvest_calendar_service import (
    HarvestCalendarService,
    active_season,
    get_harvest_calendar_service,
    harvest_highlights,
    kigali_today,
)
from tests.helpers import assert_problem, raw_json

URL: Final = "/api/v1/agro/harvest-calendar"
SEASONS: Final = [
    {"season": "A", "name": "Season A", "monthsRange": "September – February"},
    {"season": "B", "name": "Season B", "monthsRange": "March – June"},
    {"season": "C", "name": "Season C", "monthsRange": "July – September"},
]
SEASON_A_HIGHLIGHTS: Final = [
    "Sweet potato: 656,320 tonnes produced in Season A 2025 (NISR SAS 2025)",
    "Cassava: 542,874 tonnes produced in Season A 2025 (NISR SAS 2025)",
    "Maize: 481,246 tonnes produced in Season A 2025 (NISR SAS 2025)",
]


@pytest.fixture
def on_date(db_app: FastAPI) -> Iterator[Any]:
    """A client whose service sees `day` as today."""

    def install(day: date) -> TestClient:
        def service(
            session: Annotated[Session, Depends(get_read_session)],
        ) -> HarvestCalendarService:
            return HarvestCalendarService(OfficialStatisticsRepository(session), lambda: day)

        db_app.dependency_overrides[get_harvest_calendar_service] = service
        return TestClient(db_app)

    yield install
    db_app.dependency_overrides.pop(get_harvest_calendar_service, None)


def test_pdf_example_month_october_is_season_a(on_date: Any) -> None:
    response = on_date(date(2026, 10, 27)).get(URL)
    assert response.status_code == 200
    data = raw_json(response)
    assert data["status"] == "available"
    assert data["activeSeason"] == "A"
    assert data["seasonName"] == "Season A"  # PDF: "Season A (Umuhindo)"; see the assumptions
    assert data["monthsRange"] == "September – February"  # as in the PDF
    assert data["harvestHighlights"] == SEASON_A_HIGHLIGHTS
    assert data["month"] == "2026-10"
    assert data["seasons"] == SEASONS
    assert "kinyarwanda_season_names_omitted_sources_disagree" in data["assumptions"]


def test_official_source_and_meta(on_date: Any) -> None:
    data = raw_json(on_date(date(2026, 10, 1)).get(URL))
    assert data["meta"] == {
        "isIllustrative": False,
        "dataKind": "official_published_statistics",
        "sourceIds": ["sas-2025"],
    }
    source = data["source"]
    assert source["id"] == "sas-2025"
    assert source["publisher"] == "National Institute of Statistics of Rwanda (NISR)"
    assert source["documentSha256"] == (
        "3a6ed44f1e973578e46221b392e54833bb39e73b681be6e54fa2b44efe5fe1f7"
    )
    assert source["documentUrl"].startswith("https://statistics.gov.rw/")
    assert source["surveyRound"] == "2024/25" and source["retrievedOn"] == "2026-10-27"


@pytest.mark.parametrize(
    ("day", "season", "months", "first_crop"),
    [
        (date(2027, 1, 15), "A", "September – February", "Sweet potato: 656,320"),
        (date(2027, 2, 28), "A", "September – February", "Sweet potato: 656,320"),
        (date(2027, 3, 1), "B", "March – June", "Cassava: 852,541"),
        (date(2027, 6, 30), "B", "March – June", "Cassava: 852,541"),
        (date(2027, 7, 1), "C", "July – September", "Irish potato: 94,892"),
        (date(2027, 8, 31), "C", "July – September", "Irish potato: 94,892"),
        (date(2027, 9, 15), "A", "September – February", "Sweet potato: 656,320"),
        (date(2027, 12, 31), "A", "September – February", "Sweet potato: 656,320"),
    ],
)
def test_every_season_boundary(
    on_date: Any, day: date, season: str, months: str, first_crop: str
) -> None:
    data = raw_json(on_date(day).get(URL))
    assert (data["activeSeason"], data["monthsRange"]) == (season, months)
    assert data["harvestHighlights"][0].startswith(first_crop)
    assert len(data["harvestHighlights"]) == 3


def test_season_c_highlights_match_nisr_text() -> None:
    """NISR: Season C is "mainly for vegetables, sweet potato ... and Irish potato"."""
    assert harvest_highlights("C") == [
        "Irish potato: 94,892 tonnes produced in Season C 2025 (NISR SAS 2025)",
        "Vegetables: 67,626 tonnes produced in Season C 2025 (NISR SAS 2025)",
        "Sweet potato: 41,289 tonnes produced in Season C 2025 (NISR SAS 2025)",
    ]


def test_season_b_highlights() -> None:
    assert [h.split(":")[0] for h in harvest_highlights("B")] == [
        "Cassava", "Sweet potato", "Irish potato",
    ]  # fmt: skip


def test_month_to_season_mapping() -> None:
    assert [active_season(m) for m in range(1, 13)] == list("AABBBBCCAAAA")
    for bad in (0, 13):
        with pytest.raises(ValueError):
            active_season(bad)


def test_kigali_today_is_a_date() -> None:
    assert isinstance(kigali_today(), date)


def test_no_query_parameters_and_get_only(on_date: Any) -> None:
    client = on_date(date(2026, 10, 27))
    assert_problem(client.get(URL + "?month=3"), 400, "unknown-parameter",
                   ("month", "unknown_field"))  # fmt: skip
    assert_problem(client.post(URL), 405, "method-not-allowed")


# --- No source loaded: the endpoint says so instead of serving anything ---


class _NoSource(OfficialStatisticsRepository):
    def __init__(self) -> None:
        super().__init__(cast(Session, None))

    def list_sources(self) -> Sequence[StatisticalSource]:
        return []

    def get_source(self, source_id: str) -> StatisticalSource | None:
        return None


def test_awaiting_validated_data_without_the_source(stub_app: FastAPI) -> None:
    stub_app.dependency_overrides[get_harvest_calendar_service] = lambda: HarvestCalendarService(
        _NoSource(), lambda: date(2026, 10, 27)
    )
    try:
        data = raw_json(TestClient(stub_app).get(URL))
    finally:
        stub_app.dependency_overrides.clear()
    assert data["status"] == "awaiting_validated_data"
    assert (data["activeSeason"], data["seasonName"], data["monthsRange"]) == (None, None, None)
    assert data["harvestHighlights"] == [] and data["seasons"] == [] and data["source"] is None
    assert data["meta"]["sourceIds"] == [] and data["meta"]["isIllustrative"] is False


def test_openapi(stub_app: FastAPI) -> None:
    schemas = stub_app.openapi()["components"]["schemas"]
    props = schemas["HarvestCalendarResponse"]["properties"]
    assert {o.get("type") for o in props["activeSeason"]["anyOf"]} == {"string", "null"}
    assert props["harvestHighlights"]["type"] == "array"
    assert set(props) >= {"activeSeason", "seasonName", "monthsRange", "harvestHighlights"}
