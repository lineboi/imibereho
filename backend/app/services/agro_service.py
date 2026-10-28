"""Seasonal Agro Swaps page (contract §11.2, §11.5, §11.7; BR-14, BR-20, BR-24, BR-25, BR-28).

Stateless and read-only: the seeded swap supplies the prices (invented in the design itself,
"not market observations"); nothing from the request is stored. Purchasing-power equivalents,
the balanced plate and the shopping checklist are MISSING_APIS.pdf example values, approved by
the project owner on 2026-10-27 as illustrative data (`app/core/pdf_examples.py`); they are
labelled with `meta.provenance` and are not official guidance or market prices.

The shopping checklist is the PDF's Gasabo list for 4 people. Elsewhere its prices are scaled to
the district by its food line (BR-28, owner-approved 2026-10-28) and, for other sizes, to the
household by BR-24 (2026-10-27); `valueBasis` says when a response is modelled. The total is the
sum of the items and the savings are the unoptimized basket minus that total (owner decision of
2026-10-28; the PDF prints 6,250 for items that sum to 4,750).
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import (
    monthly_projection,
    purchasing_power_count,
    square_root_scaled,
    square_root_scaled_quantity,
    swap_difference,
)
from app.core.constants import METHODOLOGY_VERSION
from app.core.errors import SwapNotFoundError
from app.core.pdf_examples import (
    CHECKLIST,
    ENERGY_TIP,
    EXAMPLE_HOUSEHOLD_SIZE,
    PLATE_COMPONENTS,
    PROVENANCE,
    PURCHASING_POWER,
    ChecklistItemExample,
)
from app.db.session import get_read_session
from app.repositories.benchmark_repository import BenchmarkRepository
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.agro import (
    AgroSavingsProjectionRequest,
    AgroSavingsProjectionResponse,
    BalancedPlateResponse,
    ChecklistItem,
    PlateComponent,
    PurchasingPowerEquivalent,
    ShoppingChecklistQuery,
    ShoppingChecklistResponse,
)
from app.schemas.common import ExampleMeta
from app.services.benchmark_service import BenchmarkService
from app.services.district_advisor_service import (
    UNIFORM_BASKET,
    DistrictAdvisorService,
    PriceModel,
)

PROJECTION_ASSUMPTIONS = (
    "illustrative_prices_not_market_observations",
    "weeks_per_month_52_over_12",
    "priced_per_household_meal_household_size_does_not_scale",
    "swap_applies_whatever_the_month",
    "purchasing_power_unit_costs_implied_by_the_pdf_example_not_market_prices",
    "purchasing_power_counts_are_whole_units_rounded_down",
)
PLATE_ASSUMPTIONS = (
    "missing_apis_pdf_example_not_an_official_minagri_or_minisante_guideline",
    "energy_tip_figure_is_from_the_pdf_and_not_verified",
)
EXAMPLE_ONLY = "the_pdf_example_covers_only_gasabo_for_household_size_4"
CHECKLIST_ASSUMPTIONS = (
    EXAMPLE_ONLY,
    "illustrative_prices_not_market_observations",
    "total_is_the_sum_of_the_listed_items_not_the_pdf_printed_6250",
    "estimated_savings_is_the_unoptimized_basket_minus_the_total",
)
MODELLED_DISTRICT = (
    "modelled_br_28_prices_scaled_from_gasabo_by_the_district_food_line_not_observed",
    "quantities_are_gasabo_s_for_the_same_household_size",
)
MODELLED_SIZE = (
    "modelled_br_24_square_root_scaling_from_household_size_4_not_observed",
    "prices_rounded_half_up_to_whole_rwf_quantities_to_0_1_unit",
    "item_prices_scaled_from_the_pdf_price_not_recomputed_from_rounded_quantities",
)


class AgroService:
    def __init__(self, reference: ReferenceDataRepository, advisor: DistrictAdvisorService) -> None:
        self._reference = reference
        self._advisor = advisor

    def project(self, request: AgroSavingsProjectionRequest) -> AgroSavingsProjectionResponse:
        swap = self._reference.get_swap(request.swap_id)
        if swap is None:
            raise SwapNotFoundError
        per_meal = swap_difference(swap.from_price, swap.to_price)
        monthly = monthly_projection(per_meal, request.meals_per_week)
        return AgroSavingsProjectionResponse(
            swap_id=swap.id,
            per_meal_savings=per_meal,
            monthly_projected_savings=monthly,
            purchasing_power_equivalents=[
                PurchasingPowerEquivalent.model_validate(
                    {"item": item.item, item.field: purchasing_power_count(monthly, item.unit_cost)}
                )
                for item in PURCHASING_POWER
            ],
            purchasing_power_status="available",
            assumptions=list(PROJECTION_ASSUMPTIONS),
            meta=ExampleMeta(provenance=PROVENANCE),
        )

    def balanced_plate(self) -> BalancedPlateResponse:
        return BalancedPlateResponse(
            status="available",
            plate_components=[
                PlateComponent(
                    code=part.code,
                    name=part.name,
                    proportion_pct=part.proportion_pct,
                    examples=list(part.examples),
                )
                for part in PLATE_COMPONENTS
            ],
            energy_tip=ENERGY_TIP,
            assumptions=list(PLATE_ASSUMPTIONS),
            meta=ExampleMeta(provenance=PROVENANCE),
        )

    def shopping_checklist(self, query: ShoppingChecklistQuery) -> ShoppingChecklistResponse:
        model = self._advisor.price_model(query.district)
        size = query.household_size
        items = [_checklist_item(item, model, size) for item in CHECKLIST.items]
        total = sum(item.est_price for item in items)
        unoptimized = square_root_scaled(
            model.price(CHECKLIST.unoptimized_basket), size, EXAMPLE_HOUSEHOLD_SIZE
        )
        assumptions = list(CHECKLIST_ASSUMPTIONS)
        if not model.is_reference:
            assumptions.extend(MODELLED_DISTRICT)
            if not model.basket.from_example:
                assumptions.append(UNIFORM_BASKET)
        if size != EXAMPLE_HOUSEHOLD_SIZE:
            assumptions.extend(MODELLED_SIZE)
        exact = model.is_reference and size == EXAMPLE_HOUSEHOLD_SIZE
        return ShoppingChecklistResponse(
            status="available",
            value_basis="pdf_example" if exact else "modelled_from_pdf_example",
            district=model.basket.code,
            items=items,
            total_estimated_basket=total,
            unoptimized_basket=unoptimized,
            estimated_savings=unoptimized - total,
            assumptions=assumptions,
            meta=ExampleMeta(provenance=PROVENANCE),
        )


def _checklist_item(
    item: ChecklistItemExample, model: PriceModel, household_size: int
) -> ChecklistItem:
    """The PDF item in the district (BR-28) for the household size (BR-24)."""
    price = square_root_scaled(model.price(item.est_price), household_size, EXAMPLE_HOUSEHOLD_SIZE)
    if household_size == EXAMPLE_HOUSEHOLD_SIZE:
        return ChecklistItem(name=item.name, quantity=item.quantity, est_price=price)
    amount = square_root_scaled_quantity(item.amount, household_size, EXAMPLE_HOUSEHOLD_SIZE)
    return ChecklistItem(
        name=item.name, quantity=f"{amount.normalize():f} {item.unit}", est_price=price
    )


def get_agro_service(session: Annotated[Session, Depends(get_read_session)]) -> AgroService:
    reference = ReferenceDataRepository(session, METHODOLOGY_VERSION)
    benchmarks = BenchmarkService(reference, BenchmarkRepository(session, METHODOLOGY_VERSION))
    return AgroService(reference, DistrictAdvisorService(reference, benchmarks))
