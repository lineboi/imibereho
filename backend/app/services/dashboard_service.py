"""Dashboard filters and overview (contract §5; BR-01 to BR-03, BR-11, BR-12).

Geography is `all` only ([PD] Q-14). Counts come from SQL (`ShockRepository`); shares and ratios
are computed in Python with `ratio()`. `topDistricts` reuses the vulnerability ranking.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import monthly_balance, monthly_gap, ratio, shocked_income
from app.core.constants import (
    DASHBOARD_SHOCK_PCT,
    ESSENTIALS_TREND_SERIES,
    GEOGRAPHIES,
    INCOME_SOURCES,
    METHODOLOGY_VERSION,
)
from app.core.errors import FieldError, RequestValidationProblem
from app.db.session import get_read_session
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.repositories.shock_repository import ShockRepository
from app.schemas.common import Meta
from app.schemas.dashboard import (
    DashboardFiltersResponse,
    DashboardOverviewResponse,
    EssentialsTrend,
    FilterOption,
    IncomeSource,
    Insight,
    Kpis,
    OverviewQuery,
    ReferenceHouseholdOut,
    ShockDeficit,
    TopDistrict,
    TrendPoint,
)
from app.services.policy_scenario_service import ReferenceHouseholdMissingError
from app.services.vulnerability_service import VulnerabilityService, validate_filters


class DashboardService:
    def __init__(self, reference: ReferenceDataRepository, sample: ShockRepository) -> None:
        self._reference = reference
        self._sample = sample

    def filters(self) -> DashboardFiltersResponse:
        return DashboardFiltersResponse(
            geographies=[
                FilterOption(code=code, label=label, is_default=index == 0)
                for index, (code, label) in enumerate(GEOGRAPHIES)
            ],
            periods=[
                FilterOption(code=p.code, label=p.label, is_default=p.is_default)
                for p in self._reference.list_periods()
            ],
            household_groups=[
                FilterOption(code=g.code, label=g.label, is_default=g.is_default)
                for g in self._reference.list_household_groups()
            ],
            meta=Meta(),
        )

    def overview(self, query: OverviewQuery) -> DashboardOverviewResponse:
        errors = []
        if query.geography not in {code for code, _ in GEOGRAPHIES}:
            errors.append(FieldError("geography", "unknown_value", "This value is not allowed."))
        errors += validate_filters(self._reference, query.period, query.householdGroup)
        if errors:
            raise RequestValidationProblem(errors)

        household = self._reference.get_reference_household()
        if household is None:
            raise ReferenceHouseholdMissingError("reference household v0.1 is not seeded")
        income, essentials = household.monthly_income, household.monthly_essentials

        sample_size = self._sample.sample_size()
        in_deficit = self._sample.households_in_deficit(DASHBOARD_SHOCK_PCT)
        by_source = self._sample.households_by_income_source()
        _, ranked = VulnerabilityService(self._reference).ranked_scores(
            query.period, query.householdGroup, "-score", query.topN
        )

        return DashboardOverviewResponse(
            kpis=Kpis(
                sample_size=sample_size,
                reference_household=ReferenceHouseholdOut(
                    district_code=household.district_code,
                    household_size=household.household_size,
                    monthly_income=income,
                    monthly_essentials=essentials,
                    savings=household.savings,
                ),
                essentials_to_income_ratio=ratio(essentials, income),
                shock_deficit=ShockDeficit(
                    income_reduction_pct=DASHBOARD_SHOCK_PCT,
                    households_in_deficit=in_deficit,
                    share=ratio(in_deficit, sample_size),
                ),
            ),
            essentials_trend=EssentialsTrend(
                unit="RWF",
                income_reference=income,
                points=[
                    TrendPoint(month=p.month, essentials=p.essentials)
                    for p in self._reference.list_series(ESSENTIALS_TREND_SERIES)
                ],
            ),
            income_sources=[
                IncomeSource(
                    code=code,
                    label=label,
                    households=by_source.get(code, 0),
                    share=ratio(by_source.get(code, 0), sample_size),
                )
                for code, label in INCOME_SOURCES
            ],
            insight=Insight(
                baseline_monthly_balance=monthly_balance(income, essentials),
                shock_monthly_gap=monthly_gap(
                    essentials, shocked_income(income, DASHBOARD_SHOCK_PCT)
                ),
                income_reduction_pct=DASHBOARD_SHOCK_PCT,
            ),
            top_districts=[TopDistrict.from_score(item) for item in ranked],
            meta=Meta(),
        )


def get_dashboard_service(
    session: Annotated[Session, Depends(get_read_session)],
) -> DashboardService:
    return DashboardService(
        ReferenceDataRepository(session, METHODOLOGY_VERSION),
        ShockRepository(session, METHODOLOGY_VERSION),
    )
