"""Read-only queries over official published statistics."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    District,
    FinancialAccessStrandDistrict,
    FinancialInclusionIndicator,
    StatisticalSource,
    SurveyEstimate,
)


class OfficialStatisticsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_sources(self) -> Sequence[StatisticalSource]:
        return self._session.scalars(select(StatisticalSource).order_by(StatisticalSource.id)).all()

    def get_source(self, source_id: str) -> StatisticalSource | None:
        return self._session.get(StatisticalSource, source_id)

    def list_national_indicators(self, source_id: str) -> Sequence[FinancialInclusionIndicator]:
        return self._session.scalars(
            select(FinancialInclusionIndicator)
            .where(FinancialInclusionIndicator.source_id == source_id)
            .order_by(FinancialInclusionIndicator.sort_order)
        ).all()

    def list_district_strands(
        self, source_id: str
    ) -> Sequence[tuple[FinancialAccessStrandDistrict, str]]:
        """District rows with district names, in name order."""
        rows = self._session.execute(
            select(FinancialAccessStrandDistrict, District.name)
            .join(District, District.code == FinancialAccessStrandDistrict.district_code)
            .where(FinancialAccessStrandDistrict.source_id == source_id)
            .order_by(District.name)
        ).all()
        return [(row, name) for row, name in rows]

    def list_survey_estimates(
        self, source_id: str, indicator_code: str
    ) -> Sequence[SurveyEstimate]:
        """One indicator's estimates, in the source table's row order."""
        return self._session.scalars(
            select(SurveyEstimate)
            .where(
                SurveyEstimate.source_id == source_id,
                SurveyEstimate.indicator_code == indicator_code,
            )
            .order_by(SurveyEstimate.sort_order)
        ).all()
