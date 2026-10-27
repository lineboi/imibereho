"""District Budget Advisor (contract v0.4 §11.3, MISSING_APIS.pdf pages 7-8).

Field and query names follow the PDF, including its snake_case query parameters for
`district-comparison`. Additions: `meta`, `assumptions`, `householdSize` where the basket size is
implicit, and `unavailableFields` on the basket drawer.

Every amount comes from the one illustrative benchmark basket (the same for every district,
household size 4; [PD] Q-32). Nothing here is observed district data.
"""

from typing import Annotated, Literal

from pydantic import Field, StrictInt

from app.core.constants import HOUSEHOLD_SIZE_MAX, HOUSEHOLD_SIZE_MIN
from app.schemas.benchmark import DistrictCodeParam
from app.schemas.common import ApiModel, BodyModel, JsonDecimal, Meta, QueryInt, QueryModel

HouseholdSizeBody = Annotated[StrictInt, Field(ge=HOUSEHOLD_SIZE_MIN, le=HOUSEHOLD_SIZE_MAX)]
HouseholdSizeQuery = Annotated[QueryInt, Field(ge=HOUSEHOLD_SIZE_MIN, le=HOUSEHOLD_SIZE_MAX)]
StressScenarioId = Literal["food_inflation_15", "rent_surge_10"]


class Breakdown(ApiModel):
    """The PDF's category keys; `other` is the `other_essentials` category."""

    food: int
    housing: int
    transport: int
    utilities: int
    other: int


# --- POST /calculations/stress-test ---


class StressTestRequest(BodyModel):
    district: DistrictCodeParam
    household_size: HouseholdSizeBody
    scenario: StressScenarioId


class StressTestResponse(ApiModel):
    baseline_total: int
    stressed_total: int
    monthly_increase: int
    buffer_impact_months: JsonDecimal | None = Field(
        description="−(12 × monthlyIncrease ÷ baselineTotal), 1 dp: a year of the increase in "
        "months of the baseline basket"
    )
    assumptions: list[str]
    meta: Meta


# --- GET /calculations/district-comparison ---


class DistrictComparisonQuery(QueryModel):
    district_a: DistrictCodeParam
    district_b: DistrictCodeParam
    household_size: HouseholdSizeQuery


class DistrictBasket(ApiModel):
    code: str
    name: str
    total: int
    breakdown: Breakdown


class Variance(ApiModel):
    net_difference: int
    percentage_difference: JsonDecimal | None = Field(description="1 dp; null if A's total is 0")
    category_differences: Breakdown


class DistrictComparisonResponse(ApiModel):
    district_a: DistrictBasket
    district_b: DistrictBasket
    variance: Variance
    cost_of_living_multiplier: JsonDecimal | None = Field(
        description="total B ÷ total A, 3 dp; null if A's total is 0"
    )
    assumptions: list[str]
    meta: Meta


# --- GET /districts/{code}/basket-details ---


class StaplePriceIndex(ApiModel):
    irish_potatoes_per_kg: int | None
    sweet_potatoes_per_kg: int | None
    red_beans_per_kg: int | None


class BasketDetailsResponse(ApiModel):
    district_code: str
    household_size: int
    reference_rent_index: int = Field(description="The illustrative housing benchmark line")
    reference_transit_pass: int = Field(description="The illustrative transport benchmark line")
    staple_price_index: StaplePriceIndex
    primary_market_hub: str | None
    unavailable_fields: list[str]
    assumptions: list[str]
    meta: Meta
