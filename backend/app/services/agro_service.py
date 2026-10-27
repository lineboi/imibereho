"""Seasonal Agro Swaps page (contract v0.4 §11.2 and §11.5; BR-14, BR-20).

Stateless and read-only: the seeded swap supplies the prices (invented in the design itself,
"not market observations"); nothing from the request is stored. Nutrition guidance, the harvest
calendar and market prices have no cited source in the project, so those endpoints report
`awaiting_validated_data` with empty or null content; nothing is filled in.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import monthly_projection, swap_difference
from app.core.constants import METHODOLOGY_VERSION
from app.core.errors import SwapNotFoundError
from app.db.session import get_read_session
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.agro import (
    AgroSavingsProjectionRequest,
    AgroSavingsProjectionResponse,
    BalancedPlateResponse,
    HarvestCalendarResponse,
    ShoppingChecklistQuery,
    ShoppingChecklistResponse,
)
from app.schemas.common import Meta
from app.services.benchmark_service import require_district

PROJECTION_ASSUMPTIONS = (
    "illustrative_prices_not_market_observations",
    "weeks_per_month_52_over_12",
    "priced_per_household_meal_household_size_does_not_scale",
    "swap_applies_whatever_the_month",
    "purchasing_power_equivalents_need_sourced_prices",
)
AWAITING_SOURCE = ("awaiting_a_cited_official_source", "no_content_is_invented")


class AgroService:
    def __init__(self, reference: ReferenceDataRepository) -> None:
        self._reference = reference

    def project(self, request: AgroSavingsProjectionRequest) -> AgroSavingsProjectionResponse:
        swap = self._reference.get_swap(request.swap_id)
        if swap is None:
            raise SwapNotFoundError
        per_meal = swap_difference(swap.from_price, swap.to_price)
        return AgroSavingsProjectionResponse(
            swap_id=swap.id,
            per_meal_savings=per_meal,
            monthly_projected_savings=monthly_projection(per_meal, request.meals_per_week),
            purchasing_power_equivalents=[],
            purchasing_power_status="awaiting_validated_data",
            assumptions=list(PROJECTION_ASSUMPTIONS),
            meta=Meta(),
        )

    def balanced_plate(self) -> BalancedPlateResponse:
        return BalancedPlateResponse(
            status="awaiting_validated_data",
            plate_components=[],
            energy_tip=None,
            assumptions=list(AWAITING_SOURCE),
            meta=Meta(),
        )

    def harvest_calendar(self) -> HarvestCalendarResponse:
        return HarvestCalendarResponse(
            status="awaiting_validated_data",
            active_season=None,
            season_name=None,
            months_range=None,
            harvest_highlights=[],
            assumptions=list(AWAITING_SOURCE),
            meta=Meta(),
        )

    def shopping_checklist(self, query: ShoppingChecklistQuery) -> ShoppingChecklistResponse:
        district = require_district(self._reference, query.district)
        return ShoppingChecklistResponse(
            status="awaiting_validated_data",
            district=district.code,
            items=[],
            total_estimated_basket=None,
            unoptimized_basket=None,
            estimated_savings=None,
            assumptions=[*AWAITING_SOURCE, "needs_sourced_district_market_prices"],
            meta=Meta(),
        )


def get_agro_service(session: Annotated[Session, Depends(get_read_session)]) -> AgroService:
    return AgroService(ReferenceDataRepository(session, METHODOLOGY_VERSION))
