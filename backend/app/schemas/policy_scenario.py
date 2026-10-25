"""`POST /calculations/policy-scenario` (contract §5, BR-01 to BR-03, BR-07, BR-08)."""

from typing import Annotated, Literal

from pydantic import ConfigDict, Field, StrictInt

from app.schemas.common import ApiModel, Baseline, BodyModel, Meta, Money
from app.schemas.shock import DurationMonths, Percent

SAMPLE_SIZE_MAX = 3_000  # eligible households are bounded by the seeded sample size [I]


class PolicyScenarioRequest(BodyModel):
    instrument: Literal["monthly_cash_support"]  # [PD] Q-10
    income_loss_pct: Percent
    duration_months: DurationMonths
    support_per_household_monthly: Money
    eligible_households: Annotated[StrictInt, Field(ge=0, le=SAMPLE_SIZE_MAX)]
    baseline: Baseline | None = None  # [PD] Q-23: omitted → the reference household


class BaselineUsed(ApiModel):
    monthly_income: int
    monthly_essentials: int
    savings: int
    source: Literal["reference", "request"]


class ComparisonRow(ApiModel):
    """Keys are the column codes, as the contract writes them (not camelCased)."""

    model_config = ConfigDict(alias_generator=None)

    no_shock: int
    shock_only: int
    shock_with_support: int


class ComparisonRows(ApiModel):
    income_per_month: ComparisonRow
    support_per_month: ComparisonRow
    expenses_per_month: ComparisonRow
    net_monthly_balance: ComparisonRow
    savings_after_horizon: ComparisonRow


class Comparison(ApiModel):
    columns: list[str]
    rows: ComparisonRows


class PolicyScenarioResponse(ApiModel):
    direct_transfer_budget: int
    modelled_monthly_gap_with_support: int
    horizon_months: int
    baseline_used: BaselineUsed
    comparison: Comparison
    assumptions: list[str]
    meta: Meta
