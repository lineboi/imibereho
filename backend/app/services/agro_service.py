"""Seasonal Agro Swaps page (contract v0.4 §11.2, §11.5 and §11.7; BR-14, BR-20, BR-25).

Stateless and read-only: the seeded swap supplies the prices (invented in the design itself,
"not market observations"); nothing from the request is stored. Purchasing-power equivalents,
the balanced plate and the shopping checklist are MISSING_APIS.pdf example values, approved by
the project owner on 2026-10-27 as illustrative data (`app/core/pdf_examples.py`); they are
labelled with `meta.provenance` and are not official guidance or market prices. The Gasabo
checklist for other household sizes is that example scaled by BR-24, as the owner approved, and
says so in `valueBasis`. Where the PDF gives no example (any checklist outside Gasabo) the
response says `awaiting_validated_data` with empty or null content; nothing is filled in.
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
    CHECKLISTS,
    ENERGY_TIP,
    EXAMPLE_HOUSEHOLD_SIZE,
    PLATE_COMPONENTS,
    PROVENANCE,
    PURCHASING_POWER,
    ChecklistItemExample,
)
from app.db.session import get_read_session
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
from app.services.benchmark_service import require_district

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
CHECKLIST_ASSUMPTIONS = (EXAMPLE_ONLY, "illustrative_prices_not_market_observations")
MODELLED_CHECKLIST = (
    "modelled_br_24_square_root_scaling_from_household_size_4_not_observed",
    "prices_and_totals_rounded_half_up_to_whole_rwf_quantities_to_0_1_unit",
    "item_prices_scaled_from_the_pdf_price_not_recomputed_from_rounded_quantities",
    "estimated_savings_is_the_scaled_unoptimized_basket_minus_the_scaled_total",
    "totals_are_the_scaled_pdf_figures_not_the_sum_of_the_listed_items",
)


class AgroService:
    def __init__(self, reference: ReferenceDataRepository) -> None:
        self._reference = reference

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
        district = require_district(self._reference, query.district)
        example = CHECKLISTS.get((district.code, EXAMPLE_HOUSEHOLD_SIZE))
        if example is None:
            return ShoppingChecklistResponse(
                status="awaiting_validated_data",
                value_basis=None,
                district=district.code,
                items=[],
                total_estimated_basket=None,
                unoptimized_basket=None,
                estimated_savings=None,
                assumptions=[EXAMPLE_ONLY, "no_content_is_invented"],
                meta=ExampleMeta(provenance=None),
            )
        size = query.household_size
        if size == EXAMPLE_HOUSEHOLD_SIZE:
            return ShoppingChecklistResponse(
                status="available",
                value_basis="pdf_example",
                district=district.code,
                items=[
                    ChecklistItem(name=item.name, quantity=item.quantity, est_price=item.est_price)
                    for item in example.items
                ],
                total_estimated_basket=example.total_estimated_basket,
                unoptimized_basket=example.unoptimized_basket,
                estimated_savings=example.estimated_savings,
                assumptions=[
                    *CHECKLIST_ASSUMPTIONS,
                    "totals_are_the_pdf_figures_not_the_sum_of_the_listed_items",
                ],
                meta=ExampleMeta(provenance=PROVENANCE),
            )
        # Owner-approved BR-24 scaling of the size-4 example (contract §11.5): a model output.
        total = square_root_scaled(example.total_estimated_basket, size, EXAMPLE_HOUSEHOLD_SIZE)
        unoptimized = square_root_scaled(example.unoptimized_basket, size, EXAMPLE_HOUSEHOLD_SIZE)
        return ShoppingChecklistResponse(
            status="available",
            value_basis="modelled_from_pdf_example",
            district=district.code,
            items=[_scaled_item(item, size) for item in example.items],
            total_estimated_basket=total,
            unoptimized_basket=unoptimized,
            estimated_savings=unoptimized - total,
            assumptions=[*CHECKLIST_ASSUMPTIONS, *MODELLED_CHECKLIST],
            meta=ExampleMeta(provenance=PROVENANCE),
        )


def _scaled_item(item: ChecklistItemExample, household_size: int) -> ChecklistItem:
    amount = square_root_scaled_quantity(item.amount, household_size, EXAMPLE_HOUSEHOLD_SIZE)
    return ChecklistItem(
        name=item.name,
        quantity=f"{amount.normalize():f} {item.unit}",
        est_price=square_root_scaled(item.est_price, household_size, EXAMPLE_HOUSEHOLD_SIZE),
    )


def get_agro_service(session: Annotated[Session, Depends(get_read_session)]) -> AgroService:
    return AgroService(ReferenceDataRepository(session, METHODOLOGY_VERSION))
