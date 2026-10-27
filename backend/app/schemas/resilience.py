"""Resilience simulator (contract v0.4 §11.1, MISSING_APIS.pdf page 9).

Field names follow the PDF. Additions to the PDF shapes: `meta` on every response, explicit
`null` for catalogue defaults that do not apply, the `copingLevers` list, and the savings
drawdown fields. `scoreChange` is an integer (contract §1: numbers are never strings).
"""

from typing import Literal

from pydantic import Field

from app.schemas.common import ApiModel, Baseline, BodyModel, JsonDecimal, ListMeta, Meta, Money
from app.schemas.shock import DurationMonths, Percent

ShockId = Literal["income_drop", "medical_emergency", "school_fees"]
CopingLeverId = Literal["trim_non_essentials", "seasonal_agro_swaps", "ibimina_tontine"]


class ShockCatalogItem(ApiModel):
    id: str
    title: str
    is_lump_sum: bool
    default_pct: int | None = Field(description="Default income reduction, percent")
    default_duration: int | None = Field(description="Default duration, months")
    default_amount: int | None = Field(description="Default one-off cost, RWF")


class CopingLeverItem(ApiModel):
    id: str
    title: str
    kind: Literal["monthly_relief", "one_off_support"]
    amount: int = Field(description="RWF per month (monthly_relief) or once (one_off_support)")


class ShockCatalog(ApiModel):
    items: list[ShockCatalogItem]
    coping_levers: list[CopingLeverItem]
    meta: ListMeta


class ResilienceShock(BodyModel):
    type: ShockId
    income_reduction_pct: Percent | None = Field(
        default=None, description="Required for income_drop; not allowed for lump-sum shocks"
    )
    duration_months: DurationMonths
    amount: Money | None = Field(
        default=None,
        description="Lump-sum shocks only; defaults to the catalogue's defaultAmount",
    )


class ResilienceSimulationRequest(BodyModel):
    baseline: Baseline
    shock: ResilienceShock
    active_coping_levers: list[CopingLeverId]


class ResilienceSimulationResponse(ApiModel):
    raw_monthly_gap: int
    coping_relief_monthly: int
    lump_sum_support: int
    net_monthly_gap: int
    total_effective_buffer: int
    runway_months: JsonDecimal | None = Field(
        description="totalEffectiveBuffer ÷ netMonthlyGap, 1 dp; null when netMonthlyGap is 0"
    )
    resilience_score: int
    score_change: int
    shock_cost_monthly: int = Field(description="A lump-sum shock spread over the duration")
    savings_used: int
    savings_remaining: int
    savings_exhausted: bool
    assumptions: list[str]
    meta: Meta
