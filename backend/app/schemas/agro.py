"""Seasonal Agro Swaps page (contract v0.4 §11.2, MISSING_APIS.pdf pages 10-11).

Field names follow the PDF. Additions: `meta`, `assumptions`, and a `purchasingPowerStatus`
that says why `purchasingPowerEquivalents` is empty (no sourced prices exist in the project).
"""

from typing import Annotated, Literal

from pydantic import Field, StrictInt

from app.core.constants import HOUSEHOLD_SIZE_MAX, HOUSEHOLD_SIZE_MIN
from app.schemas.common import ApiModel, BodyModel, Meta

MEALS_PER_WEEK_MAX = 21  # three meals a day
DataStatus = Literal["available", "awaiting_validated_data"]


class AgroSavingsProjectionRequest(BodyModel):
    swap_id: Annotated[str, Field(min_length=1, max_length=64)]
    meals_per_week: Annotated[StrictInt, Field(ge=1, le=MEALS_PER_WEEK_MAX)]
    household_size: Annotated[StrictInt, Field(ge=HOUSEHOLD_SIZE_MIN, le=HOUSEHOLD_SIZE_MAX)] = (
        Field(description="Validated; the swap is priced per household meal, so it does not scale")
    )


class PurchasingPowerEquivalent(ApiModel):
    item: str
    covers_weeks: int | None = None
    rides_count: int | None = None
    quantity: int | None = None


class AgroSavingsProjectionResponse(ApiModel):
    swap_id: str
    per_meal_savings: int
    monthly_projected_savings: int = Field(
        description="perMealSavings × mealsPerWeek × 52 ÷ 12, whole RWF rounded half up"
    )
    purchasing_power_equivalents: list[PurchasingPowerEquivalent]
    purchasing_power_status: DataStatus
    assumptions: list[str]
    meta: Meta
