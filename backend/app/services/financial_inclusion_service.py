"""Official financial-inclusion statistics (FinScope Rwanda 2024), served exactly as published.

Nothing is computed, rounded or filled in here. When the source or its rows are not loaded, the
response says `status: "awaiting_validated_data"` with empty lists; it never falls back to
illustrative or synthetic values.
"""

from typing import Annotated, Final

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.constants import FINSCOPE_2024_SOURCE_ID
from app.db.session import get_read_session
from app.models import StatisticalSource
from app.repositories.official_statistics_repository import OfficialStatisticsRepository
from app.schemas.official_statistics import (
    Citation,
    Comparison,
    DistrictAccessStrand,
    DistrictFinancialInclusion,
    NationalFinancialInclusion,
    NationalIndicator,
    OfficialListMeta,
    SourceList,
    SourceOut,
    StrandCategory,
)

# The FinScope access strand categories (report Section 2.3, p. 27; Figure 13, p. 31).
STRAND_CATEGORIES: Final = (
    StrandCategory(
        code="banked",
        label="Banked",
        definition="Have/use financial products/services provided by a bank regulated by the "
        "Central Bank.",
    ),
    StrandCategory(
        code="otherFormalNonBank",
        label="Other formal (non-bank)",
        definition="Not banked; use non-bank formal financial services (e.g. mobile money, "
        "SACCO, insurance, MFIs, pension).",
    ),
    StrandCategory(
        code="informalOnly",
        label="Informal only",
        definition="Use informal products or mechanisms without any formal products.",
    ),
    StrandCategory(
        code="excluded",
        label="Excluded",
        definition="Use neither formal nor informal financial products or services.",
    ),
)


def _source_out(source: StatisticalSource) -> SourceOut:
    return SourceOut.model_validate(source, from_attributes=True)


class FinancialInclusionService:
    def __init__(self, repository: OfficialStatisticsRepository) -> None:
        self._repository = repository

    def sources(self) -> SourceList:
        items = [_source_out(source) for source in self._repository.list_sources()]
        return SourceList(
            items=items,
            meta=OfficialListMeta(source_ids=[item.id for item in items], count=len(items)),
        )

    def national(self) -> NationalFinancialInclusion:
        source = self._repository.get_source(FINSCOPE_2024_SOURCE_ID)
        rows = self._repository.list_national_indicators(FINSCOPE_2024_SOURCE_ID) if source else []
        indicators = [
            NationalIndicator(
                code=row.code,
                measure=row.measure,
                label=row.label,
                definition=row.definition,
                population=row.population,
                unit=row.unit,
                year=row.year,
                value_pct=row.value_pct,
                count_published=row.count_published,
                comparison=(
                    Comparison(
                        year=row.comparison_year,
                        value_pct=row.comparison_value_pct,
                        count_published=row.comparison_count_published,
                    )
                    if row.comparison_year is not None and row.comparison_value_pct is not None
                    else None
                ),
                citation=Citation(page=row.page, table_or_figure=row.table_or_figure),
                notes=row.notes,
            )
            for row in rows
        ]
        available = source is not None and bool(indicators)
        return NationalFinancialInclusion(
            status="available" if available else "awaiting_validated_data",
            source=_source_out(source) if source is not None else None,
            indicators=indicators,
            meta=OfficialListMeta(
                source_ids=[source.id] if source is not None else [], count=len(indicators)
            ),
        )

    def districts(self) -> DistrictFinancialInclusion:
        source = self._repository.get_source(FINSCOPE_2024_SOURCE_ID)
        rows = self._repository.list_district_strands(FINSCOPE_2024_SOURCE_ID) if source else []
        items = [
            DistrictAccessStrand(
                district_code=row.district_code,
                name=name,
                banked_pct=row.banked_pct,
                other_formal_non_bank_pct=row.other_formal_non_bank_pct,
                informal_only_pct=row.informal_only_pct,
                excluded_pct=row.excluded_pct,
                citation=Citation(page=row.page, table_or_figure=row.table_or_figure),
                notes=row.notes,
            )
            for row, name in rows
        ]
        available = source is not None and bool(items)
        return DistrictFinancialInclusion(
            status="available" if available else "awaiting_validated_data",
            source=_source_out(source) if source is not None else None,
            categories=list(STRAND_CATEGORIES),
            items=items,
            meta=OfficialListMeta(
                source_ids=[source.id] if source is not None else [], count=len(items)
            ),
        )


def get_financial_inclusion_service(
    session: Annotated[Session, Depends(get_read_session)],
) -> FinancialInclusionService:
    return FinancialInclusionService(OfficialStatisticsRepository(session))
