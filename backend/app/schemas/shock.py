"""`POST /calculations/household-shock` (contract §4, BR-01 to BR-06)."""

from typing import Annotated, Literal

from pydantic import Field, StrictInt

from app.core.constants import DURATION_MAX, DURATION_MIN, PERCENT_MAX
from app.schemas.common import ApiModel, Baseline, BodyModel, JsonDecimal, Meta

Percent = Annotated[StrictInt, Field(ge=0, le=PERCENT_MAX)]
DurationMonths = Annotated[StrictInt, Field(ge=DURATION_MIN, le=DURATION_MAX)]


class Shock(BodyModel):
    type: Literal["income_fall"]  # [PD] Q-10
    income_reduction_pct: Percent
    duration_months: DurationMonths


class HouseholdShockRequest(BodyModel):
    baseline: Baseline
    shock: Shock


class HouseholdShockResponse(ApiModel):
    baseline_monthly_balance: int
    shocked_monthly_income: int
    monthly_gap: int
    savings_used: int
    savings_remaining: int
    savings_exhausted: bool
    runway_months: JsonDecimal | None
    assumptions: list[str]
    meta: Meta
