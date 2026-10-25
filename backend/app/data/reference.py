"""Reference datasets: methodology version, districts, categories, reference household,
budget benchmarks and dashboard dimensions. Every value is from the design or the contract.

Sources (Figma file `I9eAVerX5fH8fsr5OgtkNs`, read 2026-10-24, and contract v0.2 rev 2):
- Districts: the 30 names in the D2 alphabetical tile grid `2:6965`. `province` is NULL
  ([PD] Q-21) and `name_rw` is NULL ([PD] Q-03).
- Categories: C3 rows `2:6530`–`2:6558`; icons per contract §3 ([PD] Q-11).
- Reference household: Gasabo, 4 people, 180,000 / 150,000 / 60,000 RWF
  (`2:6430`, `2:6440`, `2:6628`, `2:7209`).
- Benchmarks: the C3 "Demo reference" column `2:6534`, applied to every district at household
  size 4 ([PD] Q-32). The design calls this comparison "invented … not a district average".
- Periods / groups / trend: `2:6783`, `2:6788`, `2:6826`; contract §5 ([PD] Q-14, Q-33).
  The year 2026 is a contract assumption [I].
"""

from typing import Final

from app.core.constants import ESSENTIALS_TREND_SERIES, METHODOLOGY_VERSION
from app.data.registry import Dataset, TableRows
from app.models import (
    BudgetBenchmark,
    District,
    ExpenseCategory,
    HouseholdGroup,
    MethodologyVersion,
    MonthlySeriesPoint,
    ReferenceHousehold,
    ReferencePeriod,
)

DISTRICT_NAMES: Final = (
    "Bugesera", "Burera", "Gakenke", "Gasabo", "Gatsibo", "Gicumbi",
    "Gisagara", "Huye", "Kamonyi", "Karongi", "Kayonza", "Kicukiro",
    "Kirehe", "Muhanga", "Musanze", "Ngoma", "Ngororero", "Nyabihu",
    "Nyagatare", "Nyamagabe", "Nyamasheke", "Nyanza", "Nyarugenge", "Nyaruguru",
    "Rubavu", "Ruhango", "Rulindo", "Rusizi", "Rutsiro", "Rwamagana",
)  # fmt: skip
DISTRICT_CODES: Final = tuple(name.lower() for name in DISTRICT_NAMES)

CATEGORIES: Final = (
    ("food", "Food", "shopping-basket"),
    ("housing", "Housing", None),
    ("transport", "Transport", "bus"),
    ("utilities", "Utilities", "zap"),
    ("other_essentials", "Other essentials", None),
)
CATEGORY_CODES: Final = tuple(code for code, _, _ in CATEGORIES)

REFERENCE_HOUSEHOLD: Final = {
    "district_code": "gasabo",
    "household_size": 4,
    "monthly_income": 180_000,
    "monthly_essentials": 150_000,
    "savings": 60_000,
}

BENCHMARK_HOUSEHOLD_SIZE: Final = 4
BENCHMARK_AMOUNTS: Final = {
    "food": 65_000,
    "housing": 40_000,
    "transport": 20_000,
    "utilities": 10_000,
    "other_essentials": 15_000,
}

DEFAULT_PERIOD: Final = "2026-10"
DEFAULT_GROUP: Final = "all"
ESSENTIALS_TREND: Final = (
    ("2026-05", 138_000),
    ("2026-06", 140_000),
    ("2026-07", 143_000),
    ("2026-08", 145_000),
    ("2026-09", 148_000),
    ("2026-10", 150_000),
)


def _methodology() -> tuple[TableRows, ...]:
    row = {"version": METHODOLOGY_VERSION, "status": "concept", "is_current": True}
    return (TableRows(MethodologyVersion, None, (row,)),)


def _districts() -> tuple[TableRows, ...]:
    rows = tuple(
        {"code": code, "name": name, "name_rw": None, "province": None, "sort_order": index}
        for index, (code, name) in enumerate(zip(DISTRICT_CODES, DISTRICT_NAMES, strict=True), 1)
    )
    return (TableRows(District, None, rows),)


def _categories() -> tuple[TableRows, ...]:
    rows = tuple(
        {"code": code, "name_en": name, "name_rw": None, "icon": icon, "sort_order": index}
        for index, (code, name, icon) in enumerate(CATEGORIES, 1)
    )
    return (TableRows(ExpenseCategory, None, rows),)


def _reference_household() -> tuple[TableRows, ...]:
    row = {"methodology_version": METHODOLOGY_VERSION, **REFERENCE_HOUSEHOLD}
    return (TableRows(ReferenceHousehold, "methodology_version", (row,)),)


def _budget_benchmarks() -> tuple[TableRows, ...]:
    if sum(BENCHMARK_AMOUNTS.values()) != REFERENCE_HOUSEHOLD["monthly_essentials"]:
        raise ValueError("benchmark lines must total the design's 150,000 RWF")
    rows = tuple(
        {
            "methodology_version": METHODOLOGY_VERSION,
            "district_code": district,
            "household_size": BENCHMARK_HOUSEHOLD_SIZE,
            "category_code": category,
            "monthly_amount": BENCHMARK_AMOUNTS[category],
        }
        for district in DISTRICT_CODES
        for category in CATEGORY_CODES
    )
    return (TableRows(BudgetBenchmark, "methodology_version", rows),)


def _dashboard_dimensions() -> tuple[TableRows, ...]:
    version = METHODOLOGY_VERSION
    periods = (
        {
            "code": DEFAULT_PERIOD,
            "methodology_version": version,
            "label": "Demo month · October",
            "is_default": True,
            "sort_order": 1,
        },
    )
    groups = (
        {
            "code": DEFAULT_GROUP,
            "methodology_version": version,
            "label": "All sample households",
            "is_default": True,
            "sort_order": 1,
        },
    )
    series = tuple(
        {
            "methodology_version": version,
            "series_code": ESSENTIALS_TREND_SERIES,
            "month": month,
            "essentials": essentials,
        }
        for month, essentials in ESSENTIALS_TREND
    )
    return (
        TableRows(ReferencePeriod, "methodology_version", periods),
        TableRows(HouseholdGroup, "methodology_version", groups),
        TableRows(MonthlySeriesPoint, "methodology_version", series),
    )


DATASETS: Final = (
    Dataset("methodology", _methodology),
    Dataset("districts", _districts),
    Dataset("expense_categories", _categories),
    Dataset("reference_household", _reference_household),
    Dataset("budget_benchmarks", _budget_benchmarks),
    Dataset("dashboard_dimensions", _dashboard_dimensions),
)
