"""Resilience simulator catalogue (contract v0.4 §11, methodology v0.1): shocks and coping levers.

ILLUSTRATIVE scenario parameters, not observations. They are versioned code constants (like
`INCOME_SOURCES` in `constants.py`), not seeded tables: the list is small, fixed per methodology
version, drives request validation and is never joined with other data.

Provenance (MISSING_APIS.pdf, 26 October 2026, page 9):
- Shocks: ids, titles and defaults exactly as in the `GET /shocks/catalog` example. The page
  also names "harvest disruption" but gives no values, so it is not listed.
- Levers: ids from the `resilience-simulation` request example. Their amounts reproduce that
  page's response example (copingReliefMonthly 17,200; lumpSumSupport 25,000):
  - `seasonal_agro_swaps` 5,200 per month: the agro-savings projection (BR-20) of the seeded
    `rice-to-sweet-potato` swap at 3 meals a week, pinned by a test against the seed;
  - `trim_non_essentials` 12,000 per month: 17,200 − 5,200, inferred from the example;
  - `ibimina_tontine` 25,000 once: the example's lumpSumSupport.
"""

from dataclasses import dataclass
from typing import Final, Literal

from app.core.constants import METHODOLOGY_VERSION

CATALOGUE_METHODOLOGY_VERSION: Final = METHODOLOGY_VERSION

LeverKind = Literal["monthly_relief", "one_off_support"]


@dataclass(frozen=True, slots=True)
class ShockDefinition:
    id: str
    title: str
    is_lump_sum: bool
    default_pct: int | None
    default_duration: int | None
    default_amount: int | None


@dataclass(frozen=True, slots=True)
class CopingLeverDefinition:
    id: str
    title: str
    kind: LeverKind
    amount: int  # RWF per month (monthly_relief) or once (one_off_support)


SHOCKS: Final = (
    ShockDefinition("income_drop", "Monthly income falls", False, 20, 3, None),
    ShockDefinition("medical_emergency", "Unexpected medical cost", True, None, None, 45_000),
    ShockDefinition("school_fees", "School term fees", True, None, None, 60_000),
)

# The seeded swap and meals per week behind `seasonal_agro_swaps` (checked by a test).
AGRO_LEVER_SWAP_ID: Final = "rice-to-sweet-potato"
AGRO_LEVER_MEALS_PER_WEEK: Final = 3

COPING_LEVERS: Final = (
    CopingLeverDefinition(
        "trim_non_essentials", "Trim non-essential spending", "monthly_relief", 12_000
    ),
    CopingLeverDefinition("seasonal_agro_swaps", "Seasonal agro swaps", "monthly_relief", 5_200),
    CopingLeverDefinition("ibimina_tontine", "Ibimina (tontine) payout", "one_off_support", 25_000),
)

SHOCKS_BY_ID: Final = {shock.id: shock for shock in SHOCKS}
LEVERS_BY_ID: Final = {lever.id: lever for lever in COPING_LEVERS}
