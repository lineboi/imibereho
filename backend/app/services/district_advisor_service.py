"""District Budget Advisor (contract v0.4 §11.3 and §11.7; BR-21 to BR-24, BR-28).

Read-only and illustrative. Gasabo and Musanze use the MISSING_APIS.pdf example baskets
(owner-approved 2026-10-27; `app/core/pdf_examples.py`). Every other district uses the one
seeded benchmark basket, the same for every district at household size 4 ([PD] Q-32), so two
such districts show no difference. That is reported as it is; no other district-specific
numbers are invented. Other household sizes scale the size-4 basket line by line with the
square-root equivalence scale (BR-24), approved by the project owner on 2026-10-27.

The basket drawer's staple prices are the PDF's for Gasabo. For every other district they are
modelled from Gasabo's by the district's food line (BR-28, approved on 2026-10-28) and say so in
`valueBasis`; the market hub is the PDF's for Gasabo and null elsewhere (never invented).
"""

from typing import Annotated, Final, NamedTuple

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import (
    buffer_impact_months,
    district_price_scaled,
    district_variance,
    percent_increase,
    square_root_scaled,
)
from app.core.constants import METHODOLOGY_VERSION
from app.core.pdf_examples import (
    DISTRICT_BASKETS,
    EXAMPLE_HOUSEHOLD_SIZE,
    MARKET_HUBS,
    PROVENANCE,
    REFERENCE_DISTRICT,
    STAPLE_PRICES,
    Provenance,
    StaplePrices,
)
from app.core.stress_scenarios import STRESS_SCENARIOS
from app.data.reference import BENCHMARK_HOUSEHOLD_SIZE
from app.db.session import get_read_session
from app.repositories.benchmark_repository import BenchmarkRepository
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.common import ExampleMeta
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
BASKET_DETAILS_HOUSEHOLD_SIZE: Final = EXAMPLE_HOUSEHOLD_SIZE  # the PDF gives the drawer no size
SCALED: Final = "household_size_scaled_from_size_4_by_square_root_equivalence"
UNIFORM_BASKET: Final = "benchmark_is_one_illustrative_basket_for_every_district"
EXAMPLE_BASKET: Final = "gasabo_and_musanze_baskets_are_missing_apis_pdf_examples"
NOT_OBSERVED: Final = "not_observed_district_data"
# The PDF's −1.2 for its own example is not produced by any formula it states (contract §11.3).
NOT_THE_PDF_FIGURE: Final = "buffer_impact_is_br_22_the_pdf_example_figure_is_not_derivable"
MODELLED_STAPLES: Final = "staple_prices_modelled_br_28_from_gasabo_by_the_food_line_not_observed"
NO_MARKET_HUB: Final = "no_market_hub_is_known_for_this_district"


class BasketAmounts(NamedTuple):
    code: str
    name: str
    amounts: dict[str, int]
    from_example: bool  # a MISSING_APIS.pdf example basket rather than the shared benchmark


class PriceModel(NamedTuple):
    """BR-28 for one district: the reference district's (Gasabo's) prices, scaled by food line."""

    basket: BasketAmounts  # the district's basket at household size 4
    reference_food: int  # Gasabo's food line at household size 4

    @property
    def is_reference(self) -> bool:
        """True for Gasabo itself, whose prices are the PDF's rather than modelled."""
        return self.basket.code == REFERENCE_DISTRICT

    def price(self, reference_price: int) -> int:
        if self.is_reference:
            return reference_price
        food = self.basket.amounts["food"]
        return district_price_scaled(reference_price, food, self.reference_food)


def _basket_notes(*baskets: BasketAmounts) -> tuple[list[str], Provenance | None]:
    """The basket assumptions, and the provenance if any basket is a PDF example."""
    from_example = [basket.from_example for basket in baskets]
    notes = [EXAMPLE_BASKET] if any(from_example) else []
    if not all(from_example):
        notes.append(UNIFORM_BASKET)
    return [*notes, NOT_OBSERVED], PROVENANCE if any(from_example) else None


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

    def basket(self, district_code: str, household_size: int) -> BasketAmounts:
        """The district's size-4 basket scaled to `household_size` (BR-24).

        The MISSING_APIS.pdf example basket where the PDF gives one, else the seeded benchmark.
        """
        district = require_district(self._reference, district_code)
        example = DISTRICT_BASKETS.get(district.code)
        base = (
            example
            if example is not None
            else self._benchmarks.reference_amounts(district.code, BENCHMARK_HOUSEHOLD_SIZE)
        )
        amounts = {
            code: square_root_scaled(amount, household_size, BENCHMARK_HOUSEHOLD_SIZE)
            for code, amount in base.items()
        }
        return BasketAmounts(district.code, district.name, amounts, example is not None)

    def price_model(self, district_code: str) -> PriceModel:
        """BR-28 for the district (404 `district-not-found` for an unknown code)."""
        return PriceModel(
            self.basket(district_code, BENCHMARK_HOUSEHOLD_SIZE),
            DISTRICT_BASKETS[REFERENCE_DISTRICT]["food"],
        )

    def stress_test(self, request: StressTestRequest) -> StressTestResponse:
        basket = self.basket(request.district, request.household_size)
        shocks = STRESS_SCENARIOS[request.scenario]
        increase = sum(percent_increase(basket.amounts[code], pct) for code, pct in shocks.items())
        baseline = sum(basket.amounts.values())
        notes, provenance = _basket_notes(basket)
        return StressTestResponse(
            baseline_total=baseline,
            stressed_total=baseline + increase,
            monthly_increase=increase,
            buffer_impact_months=buffer_impact_months(increase, baseline),
            assumptions=[
                *notes,
                SCALED,
                "scenario_is_illustrative_not_a_forecast",
                "buffer_impact_is_a_year_of_the_increase_in_months_of_the_baseline_basket",
                NOT_THE_PDF_FIGURE,
            ],
            meta=ExampleMeta(provenance=provenance),
        )

    def compare(self, query: DistrictComparisonQuery) -> DistrictComparisonResponse:
        a = self.basket(query.district_a, query.household_size)
        b = self.basket(query.district_b, query.household_size)
        variance = district_variance(CATEGORY_ORDER, a.amounts, b.amounts)
        notes, provenance = _basket_notes(a, b)
        return DistrictComparisonResponse(
            district_a=DistrictBasket(
                code=a.code,
                name=a.name,
                total=sum(a.amounts.values()),
                breakdown=_breakdown(a.amounts),
            ),
            district_b=DistrictBasket(
                code=b.code,
                name=b.name,
                total=sum(b.amounts.values()),
                breakdown=_breakdown(b.amounts),
            ),
            variance=Variance(
                net_difference=variance.net_difference,
                percentage_difference=variance.percentage_difference,
                category_differences=_breakdown(variance.category_differences),
            ),
            cost_of_living_multiplier=variance.cost_of_living_multiplier,
            assumptions=[*notes, SCALED],
            meta=ExampleMeta(provenance=provenance),
        )

    def basket_details(self, district_code: str) -> BasketDetailsResponse:
        model = self.price_model(district_code)  # BASKET_DETAILS_HOUSEHOLD_SIZE is size 4
        basket = model.basket
        reference: StaplePrices = STAPLE_PRICES[REFERENCE_DISTRICT]
        hub = MARKET_HUBS.get(basket.code)
        notes, provenance = _basket_notes(basket)
        if not model.is_reference:
            notes.append(MODELLED_STAPLES)
        if hub is None:
            notes.append(NO_MARKET_HUB)
        return BasketDetailsResponse(
            status="available",
            value_basis="pdf_example" if model.is_reference else "modelled_from_pdf_example",
            district_code=basket.code,
            household_size=BASKET_DETAILS_HOUSEHOLD_SIZE,
            reference_rent_index=basket.amounts["housing"],
            reference_transit_pass=basket.amounts["transport"],
            staple_price_index=StaplePriceIndex(
                irish_potatoes_per_kg=model.price(reference.irish_potatoes_per_kg),
                sweet_potatoes_per_kg=model.price(reference.sweet_potatoes_per_kg),
                red_beans_per_kg=model.price(reference.red_beans_per_kg),
            ),
            primary_market_hub=hub,
            unavailable_fields=[] if hub is not None else ["primaryMarketHub"],
            assumptions=[*notes, "rent_and_transit_are_the_basket_housing_and_transport_lines"],
            # Every staple price derives from the PDF example, so the provenance is always set.
            meta=ExampleMeta(provenance=provenance or PROVENANCE),
        )


def get_district_advisor_service(
    session: Annotated[Session, Depends(get_read_session)],
) -> DistrictAdvisorService:
    reference = ReferenceDataRepository(session, METHODOLOGY_VERSION)
    benchmarks = BenchmarkService(reference, BenchmarkRepository(session, METHODOLOGY_VERSION))
    return DistrictAdvisorService(reference, benchmarks)
