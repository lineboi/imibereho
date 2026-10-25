"""BR-01 to BR-14 and BR-16, pinned to the design values (plan §2.4) plus derived edge cases."""

from decimal import Decimal

import pytest

from app import calculations as calc
from app.calculations import Band

WEIGHTS = (Decimal("0.40"), Decimal("0.40"), Decimal("0.20"))
BANDS = (Band("band1", 0, 39), Band("band2", 40, 59), Band("band3", 60, 69), Band("band4", 70, 100))


def test_design_values() -> None:
    """Every design reference value (plan §2.4) from the demo household."""
    assert calc.monthly_balance(180_000, 150_000) == 30_000  # BR-01, 2:6430
    shocked = calc.shocked_income(180_000, 20)
    assert shocked == 144_000  # BR-02, 2:6636
    gap = calc.monthly_gap(150_000, shocked)
    assert gap == 6_000  # BR-03, 2:6635
    assert calc.monthly_gap(150_000, shocked, support=6_000) == 0  # BR-03, 2:7231
    drawdown = calc.savings_drawdown(60_000, gap, 3)
    assert (drawdown.used, drawdown.remaining, drawdown.exhausted) == (18_000, 42_000, False)
    assert calc.runway_months(60_000, gap) == Decimal("10.0")  # BR-06, 2:6644
    assert calc.direct_transfer_budget(6_000, 1_000, 3) == 18_000_000  # BR-08, 2:7228
    assert calc.vulnerability_score((50, 40, 50), WEIGHTS) == 46  # BR-09, 2:7097
    assert calc.vulnerability_band(46, BANDS) == "band2"  # BR-10, 2:7061
    assert calc.ratio(150_000, 180_000) == Decimal("0.8333")  # BR-11, 2:6801
    assert calc.ratio(1_000, 3_000) == Decimal("0.3333")  # BR-12, 2:6805
    assert calc.swap_difference(2_000, 1_600) == 400  # BR-14, 2:6712


def test_design_policy_matrix_br07() -> None:
    """BR-07 for the three D3 columns (2:7276–2:7278): 150,000 / 42,000 / 60,000."""
    assert calc.savings_after_horizon(60_000, 30_000, 3) == 150_000
    assert calc.savings_after_horizon(60_000, -6_000, 3) == 42_000
    assert calc.savings_after_horizon(60_000, 0, 3) == 60_000


def test_design_budget_comparison_br13() -> None:
    order = ["food", "housing", "transport", "utilities", "other_essentials"]
    plan = dict(zip(order, (60_000, 45_000, 18_000, 12_000, 15_000), strict=True))
    reference = dict(zip(order, (65_000, 40_000, 20_000, 10_000, 15_000), strict=True))
    result = calc.budget_comparison(order, plan, reference)
    assert result.planned_total == result.reference_total == 150_000
    assert result.largest_above is not None and result.largest_below is not None
    assert (result.largest_above.category_code, result.largest_above.difference) == (
        "housing",
        5_000,
    )
    assert (result.largest_below.category_code, result.largest_below.difference) == ("food", -5_000)


@pytest.mark.parametrize(("pct", "expected"), [(0, 180_000), (100, 0)])
def test_reduction_bounds(pct: int, expected: int) -> None:
    assert calc.shocked_income(180_000, pct) == expected


def test_derived_input_rounds_half_up_in_integer_arithmetic() -> None:
    assert calc.shocked_income(180_001, 20) == 144_001  # 144,000.8 → 144,001
    assert calc.shocked_income(5, 50) == 3  # 2.5 → 3 (half up, not banker's rounding)


@pytest.mark.parametrize("pct", [-1, 101])
def test_shocked_income_rejects_out_of_range_percent(pct: int) -> None:
    with pytest.raises(ValueError, match="reduction_pct"):
        calc.shocked_income(100, pct)


def test_no_gap_means_no_runway() -> None:
    assert calc.runway_months(60_000, 0) is None


def test_zero_savings_with_a_gap_is_exhausted_with_zero_runway() -> None:
    drawdown = calc.savings_drawdown(0, 6_000, 3)
    assert (drawdown.used, drawdown.remaining, drawdown.exhausted) == (0, 0, True)
    assert calc.runway_months(0, 6_000) == Decimal("0.0")


def test_savings_used_is_capped_and_remaining_never_negative() -> None:
    drawdown = calc.savings_drawdown(10_000, 6_000, 3)
    assert (drawdown.used, drawdown.remaining, drawdown.exhausted) == (10_000, 0, True)


def test_exact_cover_is_not_exhausted() -> None:
    assert calc.savings_drawdown(18_000, 6_000, 3).exhausted is False


@pytest.mark.parametrize(
    ("savings", "gap", "expected"),
    [(45_000, 6_000, "7.5"), (10_000, 3_000, "3.3"), (1, 20, "0.1"), (1, 21, "0.0")],
)
def test_runway_rounds_to_one_decimal_half_up(savings: int, gap: int, expected: str) -> None:
    assert calc.runway_months(savings, gap) == Decimal(expected)


def test_negative_br07_is_returned_unchanged() -> None:
    assert calc.savings_after_horizon(10_000, -6_000, 3) == -8_000


def test_weights_must_sum_to_exactly_one() -> None:
    with pytest.raises(ValueError, match=r"sum to 1\.00"):
        calc.vulnerability_score((50, 40, 50), (Decimal("0.40"), Decimal("0.40"), Decimal("0.19")))


def test_component_bounds_and_lengths_are_enforced() -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        calc.vulnerability_score((101, 40, 50), WEIGHTS)
    with pytest.raises(ValueError, match="same length"):
        calc.vulnerability_score((50, 40), WEIGHTS)


@pytest.mark.parametrize(
    ("score", "band"),
    [(0, "band1"), (39, "band1"), (40, "band2"), (59, "band2"), (60, "band3"), (69, "band3"),
     (70, "band4"), (100, "band4")],
)  # fmt: skip
def test_band_boundaries(score: int, band: str) -> None:
    assert calc.vulnerability_band(score, BANDS) == band


def test_score_outside_every_band_is_an_error() -> None:
    with pytest.raises(ValueError, match="no band"):
        calc.vulnerability_band(101, BANDS)


def test_band_coverage_check() -> None:
    calc.check_bands_cover(BANDS)
    with pytest.raises(ValueError, match="gaps"):
        calc.check_bands_cover((Band("a", 0, 39), Band("b", 41, 100)))
    with pytest.raises(ValueError, match="gaps"):
        calc.check_bands_cover((Band("a", 0, 39), Band("b", 40, 99)))


def test_integer_score_rounds_half_up() -> None:
    assert calc.integer_score(Decimal("45.50")) == 46
    assert calc.integer_score(Decimal("45.49")) == 45


def test_zero_denominator_ratio_is_none() -> None:
    assert calc.ratio(5, 0) is None


def test_budget_comparison_ties_go_to_the_earlier_category() -> None:
    order = ["a", "b", "c"]
    result = calc.budget_comparison(order, {"a": 10, "b": 10, "c": 5}, {"a": 5, "b": 5, "c": 5})
    assert result.largest_above is not None and result.largest_above.category_code == "a"
    assert result.largest_below is None  # no category is below; equal is neither


def test_br08_at_the_largest_allowed_inputs() -> None:
    assert calc.direct_transfer_budget(100_000_000, 3_000, 24) == 7_200_000_000_000


def test_negative_inputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="households"):
        calc.direct_transfer_budget(1, -1, 1)


@pytest.mark.parametrize(
    ("income", "essentials", "expected"),
    [(180_000, 144_000, False), (180_000, 144_001, True), (180_001, 144_001, False),
     (180_001, 144_002, True), (0, 0, False), (0, 1, True)],
)  # fmt: skip
def test_deficit_predicate_boundaries(income: int, essentials: int, expected: bool) -> None:
    assert calc.is_in_deficit(income, essentials, 20) is expected
