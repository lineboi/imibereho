"""Crop-season calendar from NISR's Seasonal Agricultural Survey 2025 (contract v0.4 §11.5).

Official published statistics: the season definitions and production figures are NISR's, with
provenance in `app/data/sas_2025.py`. The active season is taken from today's month in Kigali
(UTC+2, no daylight saving). If the SAS 2025 source row is not loaded, the response says
`awaiting_validated_data` with null and empty content; nothing is filled in.
"""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Final

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.constants import SAS_2025_SOURCE_ID
from app.data.sas_2025 import (
    HIGHLIGHT_COUNT,
    PRODUCTION_2025_MT,
    PRODUCTION_SEASON_COLUMN,
    PRODUCTION_YEAR,
    SEASONS,
)
from app.db.session import get_read_session
from app.repositories.official_statistics_repository import OfficialStatisticsRepository
from app.schemas.agro import HarvestCalendarResponse, SeasonId, SeasonOut
from app.schemas.official_statistics import OfficialMeta, SourceOut

KIGALI: Final = timezone(timedelta(hours=2), "CAT")
SEASON_ORDER: Final[tuple[SeasonId, ...]] = ("A", "B", "C")
ASSUMPTIONS: Final = (
    "official_nisr_season_definitions",
    "active_season_from_the_current_month_in_kigali",
    "september_starts_season_a_and_ends_season_c_reported_as_a",
    "highlights_are_the_top_3_seasonal_crops_by_2025_production_bananas_excluded",
    "kinyarwanda_season_names_omitted_sources_disagree",
)


def kigali_today() -> date:
    return datetime.now(UTC).astimezone(KIGALI).date()


def active_season(month: int) -> SeasonId:
    """The NISR season for a month. September belongs to A and C; A (which starts) is returned."""
    if not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")
    if month in SEASONS["A"][1]:
        return "A"
    return "B" if month in SEASONS["B"][1] else "C"


def harvest_highlights(season: SeasonId) -> list[str]:
    """The season's largest seasonal crops by 2025 production, in tonnes (rounded half up)."""
    column = PRODUCTION_SEASON_COLUMN[season]
    produced = [
        (crop, values[column])
        for crop, values in PRODUCTION_2025_MT.items()
        if values[column] is not None
    ]
    top = sorted(produced, key=lambda item: (-(item[1] or Decimal(0)), item[0]))[:HIGHLIGHT_COUNT]
    return [
        f"{crop}: {int((tonnes or Decimal(0)).quantize(Decimal(1), ROUND_HALF_UP)):,} tonnes "
        f"produced in Season {season} {PRODUCTION_YEAR} (NISR SAS {PRODUCTION_YEAR})"
        for crop, tonnes in top
    ]


class HarvestCalendarService:
    def __init__(
        self, repository: OfficialStatisticsRepository, today: Callable[[], date] = kigali_today
    ) -> None:
        self._repository = repository
        self._today = today

    def calendar(self) -> HarvestCalendarResponse:
        today = self._today()
        seasons = [
            SeasonOut(season=season, name=SEASONS[season][0], months_range=SEASONS[season][2])
            for season in SEASON_ORDER
        ]
        source = self._repository.get_source(SAS_2025_SOURCE_ID)
        if source is None:
            return HarvestCalendarResponse(
                status="awaiting_validated_data",
                active_season=None,
                season_name=None,
                months_range=None,
                harvest_highlights=[],
                month=f"{today:%Y-%m}",
                seasons=[],
                source=None,
                assumptions=list(ASSUMPTIONS),
                meta=OfficialMeta(source_ids=[]),
            )
        season = active_season(today.month)
        name, _, months_range = SEASONS[season]
        return HarvestCalendarResponse(
            status="available",
            active_season=season,
            season_name=name,
            months_range=months_range,
            harvest_highlights=harvest_highlights(season),
            month=f"{today:%Y-%m}",
            seasons=seasons,
            source=SourceOut.model_validate(source, from_attributes=True),
            assumptions=list(ASSUMPTIONS),
            meta=OfficialMeta(source_ids=[source.id]),
        )


def get_harvest_calendar_service(
    session: Annotated[Session, Depends(get_read_session)],
) -> HarvestCalendarService:
    return HarvestCalendarService(OfficialStatisticsRepository(session))
