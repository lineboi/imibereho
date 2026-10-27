"""District Budget Advisor (contract v0.4 §11.3; BR-21 to BR-23 on the benchmark basket).

Read-only. Every amount is the one illustrative benchmark basket, which is the same for every
district at household size 4 ([PD] Q-32), so comparisons of two districts show no difference.
That is reported as it is; no district-specific numbers are invented.
"""

from typing import Annotated, Final

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import buffer_impact_months, district_variance, percent_increase
from app.core.constants import METHODOLOGY_VERSION
from app.core.stress_scenarios import STRESS_SCENARIOS
from app.db.session import get_read_session
from app.repositories.benchmark_repository import BenchmarkRepository
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.common import Meta
from app.schemas.district_advisor import (
    BasketDetailsResponse,
    Breakdown,
    DistrictBasket,
    DistrictComparisonQuery,
    DistrictComparisonResponse,
    StaplePriceIndex,
    StressTestRequest,
    StressTestResponse,
    Variance,
)
from app.services.benchmark_service import BenchmarkService, require_district

CATEGORY_ORDER: Final = ("food", "housing", "transport", "utilities", "other_essentials")
BASKET_DETAILS_HOUSEHOLD_SIZE: Final = 4  # the only seeded benchmark size ([PD] Q-32)
UNIFORM_BASKET: Final = "benchmark_is_one_illustrative_basket_for_every_district"
NOT_OBSERVED: Final = "not_observed_district_data"


def _breakdown(amounts: dict[str, int]) -> Breakdown:
    return Breakdown(
        food=amounts["food"],
        housing=amounts["housing"],
        transport=amounts["transport"],
        utilities=amounts["utilities"],
        other=amounts["other_essentials"],
    )


class DistrictAdvisorService:
    def __init__(self, reference: ReferenceDataRepository, benchmarks: BenchmarkService) -> None:
        self._reference = reference
        self._benchmarks = benchmarks

    def _basket(self, district_code: str, household_size: int) -> tuple[str, str, dict[str, int]]:
        district = require_district(self._reference, district_code)
        amounts = self._benchmarks.reference_amounts(district.code, household_size)
        return district.code, district.name, amounts

    def stress_test(self, request: StressTestRequest) -> StressTestResponse:
        _, _, amounts = self._basket(request.district, request.household_size)
        shocks = STRESS_SCENARIOS[request.scenario]
        increase = sum(percent_increase(amounts[code], pct) for code, pct in shocks.items())
        baseline = sum(amounts.values())
        return StressTestResponse(
            baseline_total=baseline,
            stressed_total=baseline + increase,
            monthly_increase=increase,
            buffer_impact_months=buffer_impact_months(increase, baseline),
            assumptions=[
                UNIFORM_BASKET,
                NOT_OBSERVED,
                "scenario_is_illustrative_not_a_forecast",
                "buffer_impact_is_a_year_of_the_increase_in_months_of_the_baseline_basket",
            ],
            meta=Meta(),
        )

    def compare(self, query: DistrictComparisonQuery) -> DistrictComparisonResponse:
        code_a, name_a, basket_a = self._basket(query.district_a, query.household_size)
        code_b, name_b, basket_b = self._basket(query.district_b, query.household_size)
        variance = district_variance(CATEGORY_ORDER, basket_a, basket_b)
        return DistrictComparisonResponse(
            district_a=DistrictBasket(
                code=code_a,
                name=name_a,
                total=sum(basket_a.values()),
                breakdown=_breakdown(basket_a),
            ),
            district_b=DistrictBasket(
                code=code_b,
                name=name_b,
                total=sum(basket_b.values()),
                breakdown=_breakdown(basket_b),
            ),
            variance=Variance(
                net_difference=variance.net_difference,
                percentage_difference=variance.percentage_difference,
                category_differences=_breakdown(variance.category_differences),
            ),
            cost_of_living_multiplier=variance.cost_of_living_multiplier,
            assumptions=[UNIFORM_BASKET, NOT_OBSERVED],
            meta=Meta(),
        )

    def basket_details(self, district_code: str) -> BasketDetailsResponse:
        code, _, amounts = self._basket(district_code, BASKET_DETAILS_HOUSEHOLD_SIZE)
        return BasketDetailsResponse(
            district_code=code,
            household_size=BASKET_DETAILS_HOUSEHOLD_SIZE,
            reference_rent_index=amounts["housing"],
            reference_transit_pass=amounts["transport"],
            staple_price_index=StaplePriceIndex(
                irish_potatoes_per_kg=None, sweet_potatoes_per_kg=None, red_beans_per_kg=None
            ),
            primary_market_hub=None,
            unavailable_fields=["staplePriceIndex", "primaryMarketHub"],
            assumptions=[
                UNIFORM_BASKET,
                NOT_OBSERVED,
                "rent_and_transit_are_the_benchmark_housing_and_transport_lines",
                "no_sourced_staple_prices_or_market_hubs",
            ],
            meta=Meta(),
        )


def get_district_advisor_service(
    session: Annotated[Session, Depends(get_read_session)],
) -> DistrictAdvisorService:
    reference = ReferenceDataRepository(session, METHODOLOGY_VERSION)
    benchmarks = BenchmarkService(reference, BenchmarkRepository(session, METHODOLOGY_VERSION))
    return DistrictAdvisorService(reference, benchmarks)
