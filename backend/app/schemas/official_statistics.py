"""Official published statistics (`/api/v1/nisr/*`).

These responses carry published figures, so their envelope says `isIllustrative: false` and
names the source(s). This differs from contract v0.2 §1.1 (which only knows illustrative data)
and is recorded as a proposed v0.3 addition in backend/README.md.
"""

from datetime import date
from typing import Literal

from app.schemas.common import ApiModel

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
