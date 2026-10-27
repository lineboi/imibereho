"""Seasonal Agro Swaps page (contract v0.4 §11.2 and §11.5, MISSING_APIS.pdf pages 10-11).

Field names follow the PDF. Additions: `meta`, `assumptions`, and a `purchasingPowerStatus`
that says why `purchasingPowerEquivalents` is empty (no sourced prices exist in the project).
"""

from typing import Annotated, Literal

from pydantic import Field, StrictInt

from app.core.constants import HOUSEHOLD_SIZE_MAX, HOUSEHOLD_SIZE_MIN
from app.schemas.benchmark import DistrictCodeParam
from app.schemas.common import ApiModel, BodyModel, Meta, QueryInt, QueryModel

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


# --- Content that needs a cited source (contract v0.4 §11.5): served as unavailable ---


class PlateComponent(ApiModel):
    code: str
    name: str
    proportion_pct: int
    examples: list[str]


class BalancedPlateResponse(ApiModel):
    status: DataStatus
    standard: Literal["Indyo Yuzuye"] = "Indyo Yuzuye"
    plate_components: list[PlateComponent]
    energy_tip: str | None
    assumptions: list[str]
    meta: Meta


class HarvestCalendarResponse(ApiModel):
    status: DataStatus
    active_season: Literal["A", "B", "C"] | None
    season_name: str | None
    months_range: str | None
    harvest_highlights: list[str]
    assumptions: list[str]
    meta: Meta


class ShoppingChecklistQuery(QueryModel):
    district: DistrictCodeParam
    household_size: Annotated[QueryInt, Field(ge=HOUSEHOLD_SIZE_MIN, le=HOUSEHOLD_SIZE_MAX)]


class ChecklistItem(ApiModel):
    name: str
    quantity: str
    est_price: int


class ShoppingChecklistResponse(ApiModel):
    status: DataStatus
    district: str
    items: list[ChecklistItem]
    total_estimated_basket: int | None
    unoptimized_basket: int | None
    estimated_savings: int | None
    assumptions: list[str]
    meta: Meta
