"""BR-21 to BR-23 and the stress scenarios (contract v0.4 §11.3, MISSING_APIS.pdf pages 7-8)."""

from decimal import Decimal
from typing import Final, get_args

import pytest

from app.calculations import buffer_impact_months, district_variance, percent_increase
from app.core.stress_scenarios import STRESS_SCENARIOS
from app.schemas.district_advisor import StressScenarioId

ORDER: Final = ("food", "housing", "transport", "utilities", "other_essentials")
GASABO_PDF: Final = {
    "food": 65_000, "housing": 40_000, "transport": 20_000, "utilities": 10_000,
    "other_essentials": 15_000,
}  # fmt: skip
MUSANZE_PDF: Final = {
    "food": 50_000, "housing": 28_000, "transport": 14_000, "utilities": 9_000,
    "other_essentials": 14_000,
}  # fmt: skip


def test_variance_reproduces_the_pdf_example_from_its_own_baskets() -> None:
    """The PDF's Musanze basket has no source; its arithmetic is still checked here."""
    variance = district_variance(ORDER, GASABO_PDF, MUSANZE_PDF)
    assert variance.net_difference == -35_000
    assert variance.percentage_difference == Decimal("-23.3")
    assert variance.cost_of_living_multiplier == Decimal("0.767")
    # The PDF lists three categories; utilities and other also differ (−1,000 each).
    assert variance.category_differences == {
        "food": -15_000, "housing": -12_000, "transport": -6_000, "utilities": -1_000,
        "other_essentials": -1_000,
    }  # fmt: skip


def test_identical_baskets_have_no_difference() -> None:
    variance = district_variance(ORDER, GASABO_PDF, dict(GASABO_PDF))
    assert variance.net_difference == 0
    assert variance.percentage_difference == Decimal("0.0")
    assert variance.cost_of_living_multiplier == Decimal("1.000")
    assert set(variance.category_differences.values()) == {0}


def test_empty_basket_a_gives_null_ratios() -> None:
    empty = dict.fromkeys(ORDER, 0)
    variance = district_variance(ORDER, empty, GASABO_PDF)
    assert variance.net_difference == 150_000
    assert variance.percentage_difference is None and variance.cost_of_living_multiplier is None


@pytest.mark.parametrize(
    ("amount", "pct", "expected"),
    [(65_000, 15, 9_750), (40_000, 10, 4_000), (1_005, 10, 101), (1_004, 10, 100), (0, 15, 0)],
)
def test_percent_increase_br21(amount: int, pct: int, expected: int) -> None:
    assert percent_increase(amount, pct) == expected


@pytest.mark.parametrize(
    ("increase", "baseline", "expected"),
    [
        (9_750, 150_000, Decimal("-0.8")),
        (4_000, 150_000, Decimal("-0.3")),
        (0, 150_000, Decimal("0.0")),
    ],
)
def test_buffer_impact_months_br22(increase: int, baseline: int, expected: Decimal) -> None:
    result = buffer_impact_months(increase, baseline)
    assert result == expected


def test_no_increase_is_zero_not_negative_zero() -> None:
    result = buffer_impact_months(0, 150_000)
    assert result == 0 and result is not None and not result.is_signed()


def test_buffer_impact_of_an_empty_basket_is_null() -> None:
    assert buffer_impact_months(100, 0) is None


def test_scenarios_match_the_request_literal_and_the_pdf() -> None:
    assert sorted(STRESS_SCENARIOS) == sorted(get_args(StressScenarioId))
    assert STRESS_SCENARIOS == {"food_inflation_15": {"food": 15}, "rent_surge_10": {"housing": 10}}
