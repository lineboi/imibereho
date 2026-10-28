"""MISSING_APIS.pdf example values served as illustrative data (contract v0.4 §11.7), BR-25, BR-28.

The values are the PDF's examples, copied exactly; these tests pin the arithmetic that ties them
together, so an edit to one value cannot silently break the examples the frontend relies on.
"""

from decimal import Decimal
from typing import get_args

import pytest

from app.calculations import (
    district_price_scaled,
    purchasing_power_count,
    square_root_scaled_quantity,
)
from app.core.pdf_examples import (
    CHECKLIST,
    DISTRICT_BASKETS,
    EXAMPLE_HOUSEHOLD_SIZE,
    EXAMPLE_MONTHLY_SAVINGS,
    PLATE_COMPONENTS,
    PROVENANCE,
    PURCHASING_POWER,
    REFERENCE_DISTRICT,
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
    assert set(STAPLE_PRICES) == {REFERENCE_DISTRICT} == {"gasabo"}
    assert REFERENCE_DISTRICT in DISTRICT_BASKETS  # BR-28 needs its food line


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


def test_checklist_example_and_its_printed_totals() -> None:
    # The PDF prints 6,250 and 2,400 (= 8,650 − 6,250), but its three items sum to 4,750. The
    # API serves the sum (owner decision, 2026-10-28), so its savings are 8,650 − 4,750 = 3,900.
    assert CHECKLIST.unoptimized_basket - CHECKLIST.printed_total == CHECKLIST.printed_savings
    assert (CHECKLIST.printed_total, CHECKLIST.printed_savings) == (6_250, 2_400)
    assert sum(item.est_price for item in CHECKLIST.items) == 4_750
    assert [item.quantity for item in CHECKLIST.items] == ["3 kg", "2 kg", "3 bundles"]


@pytest.mark.parametrize(
    ("price", "food", "expected"),
    [
        (750, 65_000, 750),  # Gasabo's own food line: unchanged
        (750, 50_000, 577),  # Musanze: 576.92
        (800, 50_000, 615),  # 615.38
        (850, 50_000, 654),  # 653.85
        (2_400, 50_000, 1_846),  # 1,846.15
        (13, 32_500, 7),  # 6.5 rounds half up
        (0, 50_000, 0),
        (750, 0, 0),
    ],
)
def test_br_28_district_price_scaling(price: int, food: int, expected: int) -> None:
    assert district_price_scaled(price, food, 65_000) == expected


def test_br_28_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError, match="price"):
        district_price_scaled(-1, 50_000, 65_000)
    with pytest.raises(ValueError, match="district_food"):
        district_price_scaled(750, -1, 65_000)
    with pytest.raises(ValueError, match="reference_food"):
        district_price_scaled(750, 50_000, 0)


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
