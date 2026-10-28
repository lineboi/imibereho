"""Methodology v0.1 calculations: pure functions, no database or framework imports.

Formulas BR-01 to BR-14 and BR-16 (backend-requirements §2). Rounding follows the accepted
[PD] Q-17 defaults (implementation plan §6): money is whole RWF rounded half up in integer
arithmetic; runway is quantised to 0.1 and ratios to 0.0001, both half up. BR-15 (daily total)
is computed by the frontend because expenses never leave the device (Q-02).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Final, Literal

ONE_DECIMAL: Final = Decimal("0.1")
FOUR_DECIMALS: Final = Decimal("0.0001")
WEIGHT_TOTAL: Final = Decimal("1.00")


def _require_non_negative(**values: int) -> None:
    for name, value in values.items():
        if value < 0:
            raise ValueError(f"{name} must be >= 0")


def monthly_balance(income: int, essentials: int, support: int = 0) -> int:
    """BR-01: income + support − essentials (may be negative)."""
    return income + support - essentials


def shocked_income(income: int, reduction_pct: int) -> int:
    """BR-02: income × (1 − pct/100), whole RWF rounded half up, in integer arithmetic.

    SQL uses the identical expression with BIGINT operands (see `deficit_predicate_sql`).
    """
    _require_non_negative(income=income)
    if not 0 <= reduction_pct <= 100:
        raise ValueError("reduction_pct must be between 0 and 100")
    return (income * (100 - reduction_pct) + 50) // 100


def monthly_gap(essentials: int, shocked: int, support: int = 0) -> int:
    """BR-03: max(0, essentials − (shocked income + support))."""
    return max(0, essentials - (shocked + support))


@dataclass(frozen=True, slots=True)
class Drawdown:
    used: int
    remaining: int
    exhausted: bool


def savings_drawdown(savings: int, gap: int, months: int) -> Drawdown:
    """BR-04 / BR-05: savings used is capped at savings, so the remainder is never negative."""
    _require_non_negative(savings=savings, gap=gap, months=months)
    needed = gap * months
    used = min(savings, needed)
    return Drawdown(used=used, remaining=savings - used, exhausted=needed > savings)


def _quantise(value: Decimal, step: Decimal) -> Decimal:
    return value.quantize(step, rounding=ROUND_HALF_UP)


def runway_months(savings: int, gap: int) -> Decimal | None:
    """BR-06: savings ÷ gap to 1 dp half up; `None` when there is no gap ([PD] Q-17)."""
    _require_non_negative(savings=savings, gap=gap)
    if gap == 0:
        return None
    return _quantise(Decimal(savings) / Decimal(gap), ONE_DECIMAL)


def savings_after_horizon(savings: int, net_balance: int, months: int) -> int:
    """BR-07 as written: savings + months × net balance. May be negative (contract §5)."""
    return savings + months * net_balance


def direct_transfer_budget(support: int, households: int, months: int) -> int:
    """BR-08: support per month × eligible households × months."""
    _require_non_negative(support=support, households=households, months=months)
    return support * households * months


def check_weights(weights: Sequence[Decimal]) -> None:
    """BR-16: the vulnerability weights must sum to exactly 1.00."""
    if sum(weights, Decimal(0)) != WEIGHT_TOTAL:
        raise ValueError("vulnerability weights must sum to 1.00")


def vulnerability_score(components: Sequence[int], weights: Sequence[Decimal]) -> Decimal:
    """BR-09: Σ weight × component, with inputs 0–100 and weights checked by BR-16."""
    if len(components) != len(weights):
        raise ValueError("components and weights must have the same length")
    if any(not 0 <= value <= 100 for value in components):
        raise ValueError("components must be between 0 and 100")
    check_weights(weights)
    return sum(
        (weight * value for weight, value in zip(weights, components, strict=True)), Decimal(0)
    )


def integer_score(score: Decimal) -> int:
    """Scores are returned as integers, rounded half up ([PD] Q-17)."""
    return int(score.quantize(Decimal(1), rounding=ROUND_HALF_UP))


@dataclass(frozen=True, slots=True)
class Band:
    key: str
    min_score: int
    max_score: int


def vulnerability_band(score: int, bands: Sequence[Band]) -> str:
    """BR-10: the band whose min ≤ score ≤ max."""
    for band in bands:
        if band.min_score <= score <= band.max_score:
            return band.key
    raise ValueError(f"no band covers score {score}")


def check_bands_cover(bands: Sequence[Band], low: int = 0, high: int = 100) -> None:
    """The bands must cover low–high exactly, in order, with no gaps or overlaps."""
    expected = low
    for band in sorted(bands, key=lambda b: b.min_score):
        if band.min_score != expected or band.max_score < band.min_score:
            raise ValueError("bands must cover the score range without gaps or overlaps")
        expected = band.max_score + 1
    if expected != high + 1:
        raise ValueError("bands must cover the score range without gaps or overlaps")


def ratio(numerator: int, denominator: int) -> Decimal | None:
    """BR-11 / BR-12: a fraction rounded half up to 4 places; `None` for a zero denominator."""
    if denominator == 0:
        return None
    return _quantise(Decimal(numerator) / Decimal(denominator), FOUR_DECIMALS)


def swap_difference(price_from: int, price_to: int) -> int:
    """BR-14: price A − price B."""
    return price_from - price_to


def is_in_deficit(income: int, essentials: int, reduction_pct: int) -> bool:
    """BR-03 / BR-12 helper: a household has a gap after the shock."""
    return monthly_gap(essentials, shocked_income(income, reduction_pct)) > 0


# The same predicate in SQL, for the BR-12 count. PostgreSQL integer division truncates, which
# equals floor for non-negative operands, matching Python's `//`.
DEFICIT_PREDICATE_SQL: Final = (
    "monthly_essentials > (monthly_income::bigint * (100 - :pct) + 50) / 100"
)


@dataclass(frozen=True, slots=True)
class ComparisonLine:
    category_code: str
    planned: int
    reference: int
    difference: int


@dataclass(frozen=True, slots=True)
class BudgetComparison:
    lines: tuple[ComparisonLine, ...]
    planned_total: int
    reference_total: int
    largest_above: ComparisonLine | None
    largest_below: ComparisonLine | None


def budget_comparison(
    category_order: Sequence[str], plan: Mapping[str, int], reference: Mapping[str, int]
) -> BudgetComparison:
    """BR-13: plan − reference per category, in category order.

    Largest above / below are chosen by absolute difference; ties go to the earlier category
    ([PD] Q-09). A category with no difference is neither above nor below.
    """
    lines = tuple(
        ComparisonLine(code, plan[code], reference[code], plan[code] - reference[code])
        for code in category_order
    )
    above: ComparisonLine | None = None
    below: ComparisonLine | None = None
    for line in lines:
        if line.difference > 0 and (above is None or line.difference > above.difference):
            above = line
        if line.difference < 0 and (below is None or line.difference < below.difference):
            below = line
    return BudgetComparison(
        lines=lines,
        planned_total=sum(line.planned for line in lines),
        reference_total=sum(line.reference for line in lines),
        largest_above=above,
        largest_below=below,
    )


# --- Contract v0.4 (MISSING_APIS.pdf): resilience simulator, agro projection, stress test ---

WEEKS_PER_YEAR: Final = 52
MONTHS_PER_YEAR: Final = 12
SCORE_BASE: Final = 70
SCORE_BASE_MIN: Final = 45
SCORE_BASE_MAX: Final = 75
SCORE_GAP_STEP: Final = 2_000  # RWF of raw monthly gap per score point
SCORE_PER_LEVER: Final = 7
SCORE_GAP_CLOSED_BONUS: Final = 8
SCORE_MAX: Final = 95


def monthly_projection(per_meal: int, meals_per_week: int) -> int:
    """BR-20: per-meal saving × meals per week × 52 ÷ 12, whole RWF rounded half up.

    52/12 is the exact average number of weeks in a month (4.333…). Negative per-meal savings
    (a swap that costs more) give a negative projection, rounded half away from zero.
    """
    _require_non_negative(meals_per_week=meals_per_week)
    exact = Decimal(per_meal * meals_per_week * WEEKS_PER_YEAR) / MONTHS_PER_YEAR
    return int(_quantise(exact, Decimal(1)))


THREE_DECIMALS: Final = Decimal("0.001")


def percent_increase(amount: int, pct: int) -> int:
    """BR-21: amount × pct ÷ 100, whole RWF rounded half up, in integer arithmetic."""
    _require_non_negative(amount=amount, pct=pct)
    return (amount * pct + 50) // 100


def buffer_impact_months(monthly_increase: int, baseline_total: int) -> Decimal | None:
    """BR-22: −(12 × monthly increase ÷ baseline total), to 1 dp half up.

    A year of the increase, in months of the baseline basket; `None` for an empty basket.
    """
    _require_non_negative(monthly_increase=monthly_increase, baseline_total=baseline_total)
    if baseline_total == 0:
        return None
    months = _quantise(Decimal(MONTHS_PER_YEAR * monthly_increase) / baseline_total, ONE_DECIMAL)
    return -months if months else months  # keep 0.0, never −0.0


@dataclass(frozen=True, slots=True)
class DistrictVariance:
    net_difference: int
    percentage_difference: Decimal | None
    category_differences: dict[str, int]
    cost_of_living_multiplier: Decimal | None


def district_variance(
    category_order: Sequence[str], basket_a: Mapping[str, int], basket_b: Mapping[str, int]
) -> DistrictVariance:
    """BR-23: district B against district A, per category and in total.

    netDifference = total B − total A; percentageDifference = net ÷ total A × 100 (1 dp half
    up); multiplier = total B ÷ total A (3 dp half up). Both are `None` when total A is 0.
    """
    total_a = sum(basket_a[code] for code in category_order)
    total_b = sum(basket_b[code] for code in category_order)
    net = total_b - total_a
    percentage = _quantise(Decimal(net * 100) / total_a, ONE_DECIMAL) if total_a else None
    multiplier = _quantise(Decimal(total_b) / total_a, THREE_DECIMALS) if total_a else None
    return DistrictVariance(
        net_difference=net,
        percentage_difference=percentage,
        category_differences={code: basket_b[code] - basket_a[code] for code in category_order},
        cost_of_living_multiplier=multiplier,
    )


def square_root_scaled(amount: int, household_size: int, base_size: int) -> int:
    """BR-24: amount × √(household size ÷ base size), whole RWF rounded half up.

    The square-root equivalence scale (OECD): costs grow with household size, but less than
    proportionally. Scaling a base-size amount to its own size returns it unchanged.
    """
    _require_non_negative(amount=amount)
    if household_size < 1 or base_size < 1:
        raise ValueError("household sizes must be at least 1")
    factor = (Decimal(household_size) / Decimal(base_size)).sqrt()
    return int(_quantise(Decimal(amount) * factor, Decimal(1)))


def square_root_scaled_quantity(quantity: int, household_size: int, base_size: int) -> Decimal:
    """BR-24 for an item quantity: quantity × √(household size ÷ base size), to 0.1 half up.

    The unit is kept (kg stays kg, bundles stay bundles); a modelled quantity, not a pack size.
    """
    _require_non_negative(quantity=quantity)
    if household_size < 1 or base_size < 1:
        raise ValueError("household sizes must be at least 1")
    factor = (Decimal(household_size) / Decimal(base_size)).sqrt()
    return _quantise(Decimal(quantity) * factor, ONE_DECIMAL)


def purchasing_power_count(savings: int, unit_cost: int) -> int:
    """BR-25: how many whole units the monthly savings buy, ⌊savings ÷ unit cost⌋.

    A projection with no savings (zero or negative) buys nothing, so it gives 0.
    """
    if unit_cost < 1:
        raise ValueError("unit_cost must be at least 1")
    return max(0, savings) // unit_cost


def spread_monthly(amount: int, months: int) -> int:
    """BR-17: a one-off cost spread evenly over `months`, whole RWF rounded half up."""
    _require_non_negative(amount=amount)
    if months < 1:
        raise ValueError("months must be at least 1")
    return (2 * amount + months) // (2 * months)


def net_monthly_gap(raw_gap: int, relief: int) -> int:
    """BR-18: max(0, raw gap − monthly coping relief)."""
    _require_non_negative(raw_gap=raw_gap, relief=relief)
    return max(0, raw_gap - relief)


@dataclass(frozen=True, slots=True)
class ResilienceScore:
    baseline: int
    score: int

    @property
    def change(self) -> int:
        return self.score - self.baseline


def resilience_score(raw_gap: int, active_levers: int, net_gap: int) -> ResilienceScore:
    """BR-19 (illustrative concept score, not validated; based on the frontend's heuristic).

    baseline = clamp(70 − round(raw gap ÷ 2,000), 45, 75), rounded half up;
    score = min(95, baseline + 7 × active levers + 8 if levers close a positive raw gap).
    Unlike the frontend, the +8 needs a gap that was closed, so doing nothing never scores.
    """
    _require_non_negative(raw_gap=raw_gap, active_levers=active_levers, net_gap=net_gap)
    penalty = (raw_gap + SCORE_GAP_STEP // 2) // SCORE_GAP_STEP
    baseline = max(SCORE_BASE_MIN, min(SCORE_BASE_MAX, SCORE_BASE - penalty))
    bonus = SCORE_GAP_CLOSED_BONUS if raw_gap > 0 and net_gap == 0 else 0
    return ResilienceScore(
        baseline, min(SCORE_MAX, baseline + SCORE_PER_LEVER * active_levers + bonus)
    )


BudgetHealth = Literal["normal", "caution", "exceeded"]


def budget_health(
    spent: int, planned: int | None, elapsed_days: int, days_in_month: int
) -> BudgetHealth | None:
    """BR-26: the month's spending against the plan, by pace. `None` without a plan.

    exceeded: spent > planned (the whole month's plan is used up);
    caution:  spent > planned × elapsed ÷ days (ahead of an even pace), compared in integers;
    normal:   otherwise. No thresholds beyond the plan itself.
    """
    _require_non_negative(spent=spent, elapsed_days=elapsed_days)
    if days_in_month < 1:
        raise ValueError("days_in_month must be at least 1")
    if planned is None:
        return None
    _require_non_negative(planned=planned)
    if spent > planned:
        return "exceeded"
    if spent * days_in_month > planned * elapsed_days:
        return "caution"
    return "normal"


@dataclass(frozen=True, slots=True)
class BurnRate:
    average_daily: int
    projected_month: int


def burn_rate(spent: int, elapsed_days: int, days_in_month: int) -> BurnRate | None:
    """BR-27: average daily spending so far and the month it projects to, whole RWF half up.

    average = spent ÷ elapsed days; projected = spent × days in month ÷ elapsed days (computed
    from `spent`, not from the rounded average). `None` before the month has started.
    """
    _require_non_negative(spent=spent, elapsed_days=elapsed_days)
    if elapsed_days == 0:
        return None
    if days_in_month < elapsed_days:
        raise ValueError("elapsed_days cannot exceed days_in_month")
    average = int(_quantise(Decimal(spent) / elapsed_days, Decimal(1)))
    projected = int(_quantise(Decimal(spent * days_in_month) / elapsed_days, Decimal(1)))
    return BurnRate(average, projected)
