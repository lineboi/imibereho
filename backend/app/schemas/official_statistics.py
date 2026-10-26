"""Official published statistics (`/api/v1/nisr/*`).

These responses carry published figures, so their envelope says `isIllustrative: false` and
names the source(s). This differs from contract v0.2 §1.1 (which only knows illustrative data)
and is specified by contract v0.3 (§10, agreed 27 October 2026).
"""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.common import ApiModel, JsonDecimal

DataStatus = Literal["available", "awaiting_validated_data"]


class OfficialMeta(ApiModel):
    is_illustrative: Literal[False] = False
    data_kind: Literal["official_published_statistics"] = "official_published_statistics"
    source_ids: list[str]


class OfficialListMeta(OfficialMeta):
    count: int


class SourceOut(ApiModel):
    id: str
    title: str
    publisher: str
    sponsors: str | None
    distributor: str | None
    citation: str
    publication_date: str
    survey_round: str
    fieldwork_period: str | None
    population: str
    sample_size: int | None
    lowest_published_geography: str
    document_file: str
    document_url: str
    catalog_url: str | None
    document_sha256: str
    retrieved_on: date
    notes: str | None


class SourceList(ApiModel):
    items: list[SourceOut]
    meta: OfficialListMeta


class Citation(ApiModel):
    page: int
    table_or_figure: str


class Comparison(ApiModel):
    year: int
    value_pct: int
    count_published: str | None


class NationalIndicator(ApiModel):
    code: str
    measure: str
    label: str
    definition: str
    population: str
    unit: str
    year: int
    value_pct: int
    count_published: str | None
    comparison: Comparison | None
    citation: Citation
    notes: str | None


class NationalFinancialInclusion(ApiModel):
    status: DataStatus
    geographic_level: Literal["national"] = "national"
    source: SourceOut | None
    indicators: list[NationalIndicator]
    meta: OfficialListMeta


class StrandCategory(ApiModel):
    code: str
    label: str
    definition: str


class DistrictAccessStrand(ApiModel):
    district_code: str
    name: str
    banked_pct: int
    other_formal_non_bank_pct: int
    informal_only_pct: int | None
    excluded_pct: int
    citation: Citation
    notes: str | None


class DistrictFinancialInclusion(ApiModel):
    status: DataStatus
    geographic_level: Literal["district"] = "district"
    source: SourceOut | None
    categories: list[StrandCategory]
    items: list[DistrictAccessStrand]
    meta: OfficialListMeta


# --- Survey estimates with sampling uncertainty (EICV7) ---

SurveyDimension = Literal["national", "area", "province", "sex", "quintile", "district"]


class SurveyIndicator(ApiModel):
    code: str = Field(examples=["poverty_headcount_rate"])
    table_id: str = Field(description="Table number in the source report.", examples=["A9.23"])
    label: str
    definition: str
    population: str = Field(description="Who the percentage is a share of (the denominator).")
    unit: Literal["percent"]
    survey_round: str = Field(examples=["2023/24"])
    printed_decimals: int = Field(
        description="Decimals the report prints for this table. Values below carry the "
        "workbook's full precision; round to this many decimals to display them as published.",
        examples=[2],
    )
    citation: Citation


class SurveyEstimateOut(ApiModel):
    """One published estimate. Uncertainty fields are null when the source publishes none."""

    indicator_code: str
    table_id: str
    dimension: SurveyDimension
    code: str = Field(
        description="Stable group code: `rwanda`, `urban`, `city_of_kigali`, `female`, `q1`, or "
        "the district code used by `GET /api/v1/districts`.",
        examples=["rwanda"],
    )
    label: str = Field(description="Row label exactly as published.", examples=["Poverty Rate"])
    district_code: str | None = Field(description="Set only when `dimension` is `district`.")
    estimate_pct: JsonDecimal = Field(
        description="Estimate on a 0-100 scale.", examples=[27.362976067289672]
    )
    standard_error_pct: JsonDecimal | None = Field(
        description="Standard error, in percentage points.", examples=[0.49624639004466625]
    )
    ci_lower_pct: JsonDecimal | None = Field(
        description="Lower bound of the published 95% confidence interval.",
        examples=[26.389621090104246],
    )
    ci_upper_pct: JsonDecimal | None = Field(
        description="Upper bound of the published 95% confidence interval.",
        examples=[28.336331044475099],
    )
    cv_pct: JsonDecimal | None = Field(
        description="Coefficient of variation, in percent of the estimate.",
        examples=[1.8135687756489709],
    )
    design_effect: JsonDecimal | None = Field(
        description="Design effect (no unit).", examples=[1.8650754691612403]
    )
    notes: str | None


class SurveyIndicatorEstimates(ApiModel):
    status: DataStatus
    source: SourceOut | None
    indicator: SurveyIndicator | None = Field(
        description="Null only when no validated data is loaded."
    )
    dimensions: list[SurveyDimension] = Field(
        description="The dimensions present in `items`, in published order."
    )
    items: list[SurveyEstimateOut]
    meta: OfficialListMeta
