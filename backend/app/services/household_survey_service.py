"""Official EICV7 (2023/24) survey estimates, served exactly as published by NISR.

Headcount poverty (Table A9.23) and health-insurance coverage (Table A3.7), each with its
published standard error, 95% confidence interval, coefficient of variation and design effect.
Nothing is computed, rounded or filled in: a NULL uncertainty value stays null. When the source
or its rows are not loaded, the response says `status: "awaiting_validated_data"` with an empty
list; it never falls back to illustrative, synthetic or FinScope values.
"""

from typing import Annotated, cast

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.constants import (
    EICV7_HEALTH_INSURANCE_INDICATOR,
    EICV7_POVERTY_INDICATOR,
    EICV7_SOURCE_ID,
)
from app.db.session import get_read_session
from app.models import SurveyEstimate
from app.repositories.official_statistics_repository import OfficialStatisticsRepository
from app.schemas.official_statistics import (
    Citation,
    OfficialListMeta,
    SourceOut,
    SurveyDimension,
    SurveyEstimateOut,
    SurveyIndicator,
    SurveyIndicatorEstimates,
)


def _indicator(row: SurveyEstimate) -> SurveyIndicator:
    return SurveyIndicator(
        code=row.indicator_code,
        table_id=row.table_id,
        label=row.indicator_label,
        definition=row.definition,
        population=row.population,
        unit="percent",
        survey_round=row.survey_round,
        printed_decimals=row.printed_decimals,
        citation=Citation(page=row.page, table_or_figure=row.table_or_figure),
    )


def _estimate(row: SurveyEstimate) -> SurveyEstimateOut:
    return SurveyEstimateOut(
        indicator_code=row.indicator_code,
        table_id=row.table_id,
        # A database CHECK limits the values; pydantic still validates the Literal here.
        dimension=cast(SurveyDimension, row.dimension),
        code=row.category_code,
        label=row.label,
        district_code=row.district_code,
        estimate_pct=row.estimate_pct,
        standard_error_pct=row.standard_error_pct,
        ci_lower_pct=row.ci_lower_pct,
        ci_upper_pct=row.ci_upper_pct,
        cv_pct=row.cv_pct,
        design_effect=row.design_effect,
        notes=row.notes,
    )


class HouseholdSurveyService:
    def __init__(self, repository: OfficialStatisticsRepository) -> None:
        self._repository = repository

    def poverty(self) -> SurveyIndicatorEstimates:
        return self._estimates(EICV7_POVERTY_INDICATOR)

    def health_insurance(self) -> SurveyIndicatorEstimates:
        return self._estimates(EICV7_HEALTH_INSURANCE_INDICATOR)

    def _estimates(self, indicator_code: str) -> SurveyIndicatorEstimates:
        source = self._repository.get_source(EICV7_SOURCE_ID)
        rows = (
            self._repository.list_survey_estimates(EICV7_SOURCE_ID, indicator_code)
            if source is not None
            else []
        )
        items = [_estimate(row) for row in rows]
        dimensions: list[SurveyDimension] = []
        for item in items:
            if item.dimension not in dimensions:
                dimensions.append(item.dimension)
        return SurveyIndicatorEstimates(
            status="available" if items else "awaiting_validated_data",
            source=SourceOut.model_validate(source, from_attributes=True) if source else None,
            indicator=_indicator(rows[0]) if rows else None,
            dimensions=dimensions,
            items=items,
            meta=OfficialListMeta(
                source_ids=[source.id] if source is not None else [], count=len(items)
            ),
        )


def get_household_survey_service(
    session: Annotated[Session, Depends(get_read_session)],
) -> HouseholdSurveyService:
    return HouseholdSurveyService(OfficialStatisticsRepository(session))
