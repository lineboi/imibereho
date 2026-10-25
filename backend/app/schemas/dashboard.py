"""Dashboard filters and overview (contract §5)."""

from typing import Annotated

from pydantic import Field

from app.core.constants import LIST_LIMIT_MAX
from app.schemas.common import ApiModel, JsonDecimal, Meta, QueryInt
from app.schemas.vulnerability import DistrictScore, FilterCode, VulnerabilityFilters


class FilterOption(ApiModel):
    code: str
    label: str
    is_default: bool


class DashboardFiltersResponse(ApiModel):
    geographies: list[FilterOption]
    periods: list[FilterOption]
    household_groups: list[FilterOption]
    meta: Meta


class OverviewQuery(VulnerabilityFilters):
    geography: FilterCode = "all"
    topN: Annotated[QueryInt, Field(ge=1, le=LIST_LIMIT_MAX)] = 2


class ReferenceHouseholdOut(ApiModel):
    district_code: str
    household_size: int
    monthly_income: int
    monthly_essentials: int
    savings: int


class ShockDeficit(ApiModel):
    income_reduction_pct: int
    households_in_deficit: int
    share: JsonDecimal | None


class Kpis(ApiModel):
    sample_size: int
    reference_household: ReferenceHouseholdOut
    essentials_to_income_ratio: JsonDecimal | None
    shock_deficit: ShockDeficit


class TrendPoint(ApiModel):
    month: str
    essentials: int


class EssentialsTrend(ApiModel):
    unit: str
    income_reference: int
    points: list[TrendPoint]


class IncomeSource(ApiModel):
    code: str
    label: str
    households: int
    share: JsonDecimal | None


class Insight(ApiModel):
    baseline_monthly_balance: int
    shock_monthly_gap: int
    income_reduction_pct: int


class TopDistrict(ApiModel):
    code: str
    name: str
    score: int
    band: str

    @classmethod
    def from_score(cls, item: DistrictScore) -> "TopDistrict":
        return cls(code=item.district_code, name=item.name, score=item.score, band=item.band)


class DashboardOverviewResponse(ApiModel):
    kpis: Kpis
    essentials_trend: EssentialsTrend
    income_sources: list[IncomeSource]
    insight: Insight
    top_districts: list[TopDistrict]
    meta: Meta
