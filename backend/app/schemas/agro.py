"""Seasonal Agro Swaps page (contract v0.4 §11.2 and §11.5, MISSING_APIS.pdf pages 10-11).

Field names follow the PDF. Additions: `meta` (with `provenance` where MISSING_APIS.pdf example
values are served, contract §11.7), `assumptions`, `status` on the content endpoints, and a
`purchasingPowerStatus`. Each purchasing-power item sets only the PDF's count key for it
(`coversWeeks`, `ridesCount` or `quantity`); the other two are `null`.
"""

from typing import Annotated, Literal

from pydantic import Field, StrictInt

from app.core.constants import HOUSEHOLD_SIZE_MAX, HOUSEHOLD_SIZE_MIN
from app.schemas.benchmark import DistrictCodeParam
from app.schemas.common import ApiModel, BodyModel, ExampleMeta, QueryInt, QueryModel
from app.schemas.official_statistics import OfficialMeta, SourceOut

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
    meta: ExampleMeta


# --- Content (contract v0.4 §11.5 and §11.7) ---


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
    meta: ExampleMeta


SeasonId = Literal["A", "B", "C"]


class SeasonOut(ApiModel):
    season: SeasonId
    name: str
    months_range: str


class HarvestCalendarResponse(ApiModel):
    """Official NISR season calendar (SAS 2025), not illustrative: `meta.isIllustrative` false."""

    status: DataStatus
    active_season: SeasonId | None = Field(description="The season of the current month (Kigali)")
    season_name: str | None
    months_range: str | None
    harvest_highlights: list[str] = Field(
        description="The active season's three largest seasonal crops by 2025 production"
    )
    month: str = Field(description="The month the active season was taken from, YYYY-MM")
    seasons: list[SeasonOut]
    source: SourceOut | None
    assumptions: list[str]
    meta: OfficialMeta


class ShoppingChecklistQuery(QueryModel):
    district: DistrictCodeParam
    household_size: Annotated[QueryInt, Field(ge=HOUSEHOLD_SIZE_MIN, le=HOUSEHOLD_SIZE_MAX)]


class ChecklistItem(ApiModel):
    name: str
    quantity: str
    est_price: int


ChecklistBasis = Literal["pdf_example", "modelled_from_pdf_example"]


class ShoppingChecklistResponse(ApiModel):
    status: DataStatus
    value_basis: ChecklistBasis | None = Field(
        description="pdf_example: the MISSING_APIS.pdf figures as given (household size 4); "
        "modelled_from_pdf_example: those figures scaled by BR-24 (√(householdSize ÷ 4)), a "
        "model output, not a market observation; null when status is awaiting_validated_data"
    )
    district: str
    items: list[ChecklistItem]
    total_estimated_basket: int | None
    unoptimized_basket: int | None
    estimated_savings: int | None
    assumptions: list[str]
    meta: ExampleMeta
