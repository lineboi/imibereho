"""BR-17 to BR-19 and the resilience catalogue (contract v0.4 §11.1, MISSING_APIS.pdf page 9)."""

from decimal import Decimal
from typing import get_args

import pytest

from app.calculations import (
    monthly_projection,
    net_monthly_gap,
    resilience_score,
    spread_monthly,
    swap_difference,
)
from app.core.resilience_catalog import (
    AGRO_LEVER_MEALS_PER_WEEK,
    AGRO_LEVER_SWAP_ID,
    COPING_LEVERS,
    LEVERS_BY_ID,
    SHOCKS,
)
from app.data.seasonal import SWAP
from app.schemas.resilience import CopingLeverId, ResilienceSimulationRequest, ShockId
from app.services.resilience_service import ResilienceService

PDF_EXAMPLE = {
    "baseline": {"monthlyIncome": 180_000, "monthlyEssentials": 150_000, "savings": 60_000},
    "shock": {"type": "income_drop", "incomeReductionPct": 20, "durationMonths": 3},
    "activeCopingLevers": ["trim_non_essentials", "seasonal_agro_swaps", "ibimina_tontine"],
}


@pytest.mark.parametrize(
    ("amount", "months", "expected"),
    [
        (45_000, 1, 45_000),
        (45_000, 3, 15_000),
        (60_000, 7, 8_571),
        (10, 4, 3),
        (5, 2, 3),
        (0, 5, 0),
    ],
)
def test_spread_monthly_rounds_half_up(amount: int, months: int, expected: int) -> None:
    assert spread_monthly(amount, months) == expected


def test_spread_monthly_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        spread_monthly(100, 0)
    with pytest.raises(ValueError):
        spread_monthly(-1, 1)


@pytest.mark.parametrize(
    ("raw", "relief", "expected"), [(6_000, 17_200, 0), (20_000, 12_000, 8_000), (0, 0, 0)]
)
def test_net_monthly_gap_is_never_negative(raw: int, relief: int, expected: int) -> None:
    assert net_monthly_gap(raw, relief) == expected


@pytest.mark.parametrize(
    ("raw", "levers", "net", "baseline", "score"),
    [
        (6_000, 3, 0, 67, 95),  # PDF inputs: 70 − 3; 67 + 21 + 8 = 96, capped at 95
        (6_000, 0, 6_000, 67, 67),
        (0, 0, 0, 70, 70),  # no gap and no levers: nothing changes (no bonus)
        (1_000, 0, 1_000, 69, 69),  # 1,000 ÷ 2,000 = 0.5 rounds half up to 1
        (999, 0, 999, 70, 70),
        (100_000, 1, 100_000, 45, 52),  # baseline floor
        (0, 3, 0, 70, 91),  # levers without a gap to close: no +8
    ],
)
def test_resilience_score_br19(raw: int, levers: int, net: int, baseline: int, score: int) -> None:
    result = resilience_score(raw, levers, net)
    assert (result.baseline, result.score, result.change) == (baseline, score, score - baseline)
    assert 0 <= result.score <= 100


def test_catalogue_ids_match_the_request_literals() -> None:
    assert [shock.id for shock in SHOCKS] == list(get_args(ShockId))
    assert [lever.id for lever in COPING_LEVERS] == list(get_args(CopingLeverId))


def test_catalogue_matches_the_pdf_example() -> None:
    assert [(s.id, s.title, s.is_lump_sum, s.default_pct, s.default_duration, s.default_amount)
            for s in SHOCKS] == [
        ("income_drop", "Monthly income falls", False, 20, 3, None),
        ("medical_emergency", "Unexpected medical cost", True, None, None, 45_000),
        ("school_fees", "School term fees", True, None, None, 60_000),
    ]  # fmt: skip


def test_agro_lever_equals_the_projection_of_the_seeded_swap() -> None:
    """`seasonal_agro_swaps` = BR-20 for the seeded swap at 3 meals/week (52/12 weeks a month)."""
    assert SWAP["id"] == AGRO_LEVER_SWAP_ID
    per_meal = swap_difference(int(str(SWAP["from_price"])), int(str(SWAP["to_price"])))
    assert per_meal == 400
    projected = monthly_projection(per_meal, AGRO_LEVER_MEALS_PER_WEEK)
    assert projected == LEVERS_BY_ID["seasonal_agro_swaps"].amount


def test_pdf_example_reproduces_every_reproducible_field() -> None:
    result = ResilienceService().simulate(ResilienceSimulationRequest.model_validate(PDF_EXAMPLE))
    # Exactly as in the PDF.
    assert result.raw_monthly_gap == 6_000
    assert result.coping_relief_monthly == 17_200
    assert result.lump_sum_support == 25_000
    assert result.net_monthly_gap == 0
    assert result.total_effective_buffer == 85_000
    # Documented corrections: BR-06 gives no runway without a gap (PDF: 14.2), and BR-19 gives
    # 95 / +28 (PDF: 88 / "+26", which no formula in the repository reproduces).
    assert result.runway_months is None
    assert (result.resilience_score, result.score_change) == (95, 28)


def test_lump_sum_shock_is_spread_and_drawn_from_the_buffer() -> None:
    body = {
        "baseline": {"monthlyIncome": 140_000, "monthlyEssentials": 150_000, "savings": 60_000},
        "shock": {"type": "medical_emergency", "durationMonths": 3},
        "activeCopingLevers": ["trim_non_essentials"],
    }
    result = ResilienceService().simulate(ResilienceSimulationRequest.model_validate(body))
    assert result.shock_cost_monthly == 15_000  # 45,000 default over 3 months
    assert result.raw_monthly_gap == 25_000  # 150,000 + 15,000 − 140,000
    assert result.net_monthly_gap == 13_000
    assert result.runway_months == Decimal("4.6")  # 60,000 ÷ 13,000 = 4.615…
    assert (result.savings_used, result.savings_remaining) == (39_000, 21_000)
    assert result.savings_exhausted is False


@pytest.mark.parametrize(
    ("per_meal", "meals", "expected"),
    [
        (400, 3, 5_200),  # the PDF example: 400 × 3 × 52 ÷ 12 = 5,200 exactly
        (400, 1, 1_733),  # 1,733.33… rounds down
        (450, 3, 5_850),
        (1, 1, 4),  # 4.333… rounds down
        (3, 1, 13),  # 13.0
        (-400, 3, -5_200),  # a swap that costs more
        (0, 21, 0),
        (2_000, 21, 182_000),
    ],
)
def test_monthly_projection_br20(per_meal: int, meals: int, expected: int) -> None:
    assert monthly_projection(per_meal, meals) == expected


def test_monthly_projection_resolves_the_pdf_mismatch() -> None:
    """The frontend's 4.33 weeks/month gives 5,196; the exact 52/12 gives the PDF's 5,200."""
    assert round(400 * 3 * 4.33) == 5_196
    assert monthly_projection(400, 3) == 5_200


def test_monthly_projection_rounds_thirds_to_the_nearest_rwf() -> None:
    """× 52/12 = × 13/3, so the exact value is always a whole number of thirds: no .5 ties."""
    assert monthly_projection(1, 1) == 4  # 4 1/3 → 4
    assert monthly_projection(1, 2) == 9  # 8 2/3 → 9
    assert monthly_projection(-1, 2) == -9  # −8 2/3 → −9
