"""[SYN] The 3,000-household illustrative sample behind the D1 KPIs (plan F6, [PD] Q-18).

Only the totals come from the design: 3,000 households (`2:6793`, "Demo households · not
representative"); 1,200 wage / 1,050 agriculture / 750 informal enterprise (`2:6864`); and
1,000 in deficit after a 20% shock (`2:6805`). Everything else is invented, generated from a fixed
seed, and labelled illustrative wherever it surfaces.

Construction (exact by design, so the seed aborts on any drift):
1. District: 100 per district (an arbitrary even split).
2. Income source: a seeded shuffle, then slices of 1,200 / 1,050 / 750, independent of district.
3. Deficit flag: a separate seeded shuffle picks exactly 1,000 households, independent of
   district, income source and vulnerability. This module never reads vulnerability data.
4. Amounts: household size 1–8; income 40,000–600,000 in steps of 1,000; savings 0–300,000 in
   steps of 1,000; essentials drawn so that `is_in_deficit(income, essentials, 20)` equals the flag.
"""

import random
from collections import Counter
from typing import Final, cast

from app.calculations import is_in_deficit, shocked_income
from app.core.constants import DASHBOARD_SHOCK_PCT, INCOME_SOURCES, METHODOLOGY_VERSION
from app.data.reference import DISTRICT_CODES
from app.data.registry import Dataset, TableRows
from app.models import SyntheticHousehold

SAMPLE_SEED: Final = 20261024
SAMPLE_SIZE: Final = 3_000
PER_DISTRICT: Final = 100
SOURCE_COUNTS: Final = {"wage": 1_200, "agriculture": 1_050, "informal_enterprise": 750}
DEFICIT_COUNT: Final = 1_000


def generate() -> list[dict[str, object]]:
    rng = random.Random(SAMPLE_SEED)
    ids = list(range(1, SAMPLE_SIZE + 1))
    districts = [code for code in DISTRICT_CODES for _ in range(PER_DISTRICT)]

    source_order = ids.copy()
    rng.shuffle(source_order)
    source_of: dict[int, str] = {}
    start = 0
    for code, _label in INCOME_SOURCES:
        for household_id in source_order[start : start + SOURCE_COUNTS[code]]:
            source_of[household_id] = code
        start += SOURCE_COUNTS[code]

    deficit_order = ids.copy()
    rng.shuffle(deficit_order)
    in_deficit = set(deficit_order[:DEFICIT_COUNT])

    rows: list[dict[str, object]] = []
    for household_id, district in zip(ids, districts, strict=True):
        income = rng.randint(40, 600) * 1_000
        shocked = shocked_income(income, DASHBOARD_SHOCK_PCT)
        if household_id in in_deficit:
            essentials = rng.randint(shocked + 1, income)
        else:
            essentials = rng.randint(shocked // 2, shocked)
        rows.append(
            {
                "id": household_id,
                "methodology_version": METHODOLOGY_VERSION,
                "district_code": district,
                "household_size": rng.randint(1, 8),
                "primary_income_source": source_of[household_id],
                "monthly_income": income,
                "monthly_essentials": essentials,
                "savings": rng.randint(0, 300) * 1_000,
            }
        )
    validate(rows)
    return rows


def validate(rows: list[dict[str, object]]) -> None:
    """Abort unless the design totals hold exactly."""
    if len(rows) != SAMPLE_SIZE:
        raise ValueError("sample size must be 3,000")
    if Counter(row["primary_income_source"] for row in rows) != Counter(SOURCE_COUNTS):
        raise ValueError("income-source counts must be 1,200 / 1,050 / 750")
    deficits = 0
    for row in rows:
        income = cast(int, row["monthly_income"])
        essentials = cast(int, row["monthly_essentials"])
        deficits += is_in_deficit(income, essentials, DASHBOARD_SHOCK_PCT)
    if deficits != DEFICIT_COUNT:
        raise ValueError("exactly 1,000 households must be in deficit after a 20% shock")


def _synthetic_households() -> tuple[TableRows, ...]:
    return (TableRows(SyntheticHousehold, "methodology_version", tuple(generate())),)


DATASETS: Final = (Dataset("synthetic_households", _synthetic_households),)
