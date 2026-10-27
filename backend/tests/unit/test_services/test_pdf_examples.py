"""MISSING_APIS.pdf example values served as illustrative data (contract v0.4 §11.7) and BR-25.

The values are the PDF's examples, copied exactly; these tests pin the arithmetic that ties them
together, so an edit to one value cannot silently break the examples the frontend relies on.
"""

from decimal import Decimal
from typing import get_args

import pytest

from app.calculations import purchasing_power_count, square_root_scaled_quantity
from app.core.pdf_examples import (
    CHECKLISTS,
    DISTRICT_BASKETS,
    EXAMPLE_HOUSEHOLD_SIZE,
    EXAMPLE_MONTHLY_SAVINGS,
    PLATE_COMPONENTS,
    PROVENANCE,
    PURCHASING_POWER,
    STAPLE_PRICES,
    Provenance,
)
from app.data.reference import BENCHMARK_HOUSEHOLD_SIZE
from app.schemas.agro import PurchasingPowerEquivalent
from tests.helpers import PROVENANCE as WIRE_PROVENANCE


def test_provenance_label_is_the_approved_wording() -> None:
    assert PROVENANCE == WIRE_PROVENANCE == "MISSING_APIS.pdf example, owner-approved"
    assert get_args(Provenance) == (PROVENANCE,)


def test_example_baskets_match_the_pdf_totals() -> None:
    """Page 7: Gasabo 150,000 and Musanze 115,000, for the benchmark's household size."""
    assert EXAMPLE_HOUSEHOLD_SIZE == BENCHMARK_HOUSEHOLD_SIZE
    assert {code: sum(basket.values()) for code, basket in DISTRICT_BASKETS.items()} == {
        "gasabo": 150_000,
        "musanze": 115_000,
    }
    categories = {"food", "housing", "transport", "utilities", "other_essentials"}
    assert all(set(basket) == categories for basket in DISTRICT_BASKETS.values())


def test_staple_prices_only_where_the_pdf_gives_them() -> None:
    assert set(STAPLE_PRICES) == {"gasabo"} <= set(DISTRICT_BASKETS)


def test_unit_costs_reproduce_the_pdf_example() -> None:
    """Page 10: 5,200 RWF a month buys 2 weeks of water, 8 bus rides or 26 eggs."""
    counts = {
        item.item: purchasing_power_count(EXAMPLE_MONTHLY_SAVINGS, item.unit_cost)
        for item in PURCHASING_POWER
    }
    assert counts == {"WASAC Clean Water": 2, "Kigali City Bus Rides": 8, "Fresh Farm Eggs": 26}
    keys = {field.alias for field in PurchasingPowerEquivalent.model_fields.values()}
    assert {item.field for item in PURCHASING_POWER} <= keys


def test_plate_proportions_sum_to_100() -> None:
    assert [part.proportion_pct for part in PLATE_COMPONENTS] == [50, 25, 25]


def test_checklist_example_is_internally_consistent_except_its_item_sum() -> None:
    (key, example), *others = CHECKLISTS.items()
    assert key == ("gasabo", EXAMPLE_HOUSEHOLD_SIZE) and not others
    assert example.unoptimized_basket - example.total_estimated_basket == example.estimated_savings
    # The PDF's three items sum to 4,750, not the 6,250 total: served as given (§11.7).
    assert sum(item.est_price for item in example.items) == 4_750
    assert [item.quantity for item in example.items] == ["3 kg", "2 kg", "3 bundles"]


@pytest.mark.parametrize(
    ("quantity", "size", "expected"),
    [(3, 4, "3.0"), (3, 1, "1.5"), (3, 5, "3.4"), (2, 5, "2.2"), (3, 20, "6.7"), (0, 9, "0.0")],
)
def test_br_24_quantity_scaling_to_one_decimal_half_up(
    quantity: int, size: int, expected: str
) -> None:
    assert square_root_scaled_quantity(quantity, size, EXAMPLE_HOUSEHOLD_SIZE) == Decimal(expected)


def test_br_24_quantity_scaling_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError, match="household sizes"):
        square_root_scaled_quantity(3, 0, EXAMPLE_HOUSEHOLD_SIZE)
    with pytest.raises(ValueError, match="quantity"):
        square_root_scaled_quantity(-1, 4, EXAMPLE_HOUSEHOLD_SIZE)


@pytest.mark.parametrize(
    ("savings", "unit", "expected"),
    [(5_200, 200, 26), (5_199, 200, 25), (0, 650, 0), (-1_733, 650, 0), (649, 650, 0)],
)
def test_br_25_whole_units_rounded_down(savings: int, unit: int, expected: int) -> None:
    assert purchasing_power_count(savings, unit) == expected


@pytest.mark.parametrize("unit", [0, -1])
def test_br_25_needs_a_positive_unit_cost(unit: int) -> None:
    with pytest.raises(ValueError, match="unit_cost"):
        purchasing_power_count(5_200, unit)
