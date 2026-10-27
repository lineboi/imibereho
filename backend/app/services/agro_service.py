"""Seasonal Agro Swaps calculations (contract v0.4 §11.2; BR-14, BR-20).

Stateless and read-only: the seeded swap supplies the prices (invented in the design itself,
"not market observations"); nothing from the request is stored.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import monthly_projection, swap_difference
from app.core.constants import METHODOLOGY_VERSION
from app.core.errors import SwapNotFoundError
from app.db.session import get_read_session
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.agro import AgroSavingsProjectionRequest, AgroSavingsProjectionResponse
from app.schemas.common import Meta

PROJECTION_ASSUMPTIONS = (
    "illustrative_prices_not_market_observations",
    "weeks_per_month_52_over_12",
    "priced_per_household_meal_household_size_does_not_scale",
    "swap_applies_whatever_the_month",
    "purchasing_power_equivalents_need_sourced_prices",
)


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


def get_agro_service(session: Annotated[Session, Depends(get_read_session)]) -> AgroService:
    return AgroService(ReferenceDataRepository(session, METHODOLOGY_VERSION))
