"""Rename CHECK constraints to the naming convention (fixes 0001-0005).

Revisions 0001-0005 passed full names (e.g. "ck_districts_code_slug") to CHECK constraints.
Alembic applied the `ck_%(table_name)s_%(constraint_name)s` convention on top, so PostgreSQL
received doubled names such as "ck_districts_ck_districts_code_slug", truncated with a hash when
longer than 63 characters. Autogenerate does not compare CHECK constraints, so `check` did not
notice; the round-trip integration test did.

The doubled names are deterministic, so this revision renames them on every database migrated by
0001-0005. RENAME CONSTRAINT changes no data and exists in PostgreSQL 16 and 18. New revisions
must wrap explicit constraint names in `op.f()` so the convention is not applied twice.

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-25
"""

from collections.abc import Sequence
from typing import Final

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, name created by 0001-0005, conventional name)
RENAMES: Final = (
    (
        "budget_benchmarks",
        "ck_budget_benchmarks_ck_budget_benchmarks_household_size_range",
        "ck_budget_benchmarks_household_size_range",
    ),
    (
        "budget_benchmarks",
        "ck_budget_benchmarks_ck_budget_benchmarks_monthly_amoun_b4dc",
        "ck_budget_benchmarks_monthly_amount_non_negative",
    ),
    (
        "district_vulnerability",
        "ck_district_vulnerability_ck_district_vulnerability_com_37d5",
        "ck_district_vulnerability_components_range",
    ),
    (
        "district_vulnerability",
        "ck_district_vulnerability_ck_district_vulnerability_score_range",
        "ck_district_vulnerability_score_range",
    ),
    ("districts", "ck_districts_ck_districts_code_slug", "ck_districts_code_slug"),
    (
        "expense_categories",
        "ck_expense_categories_ck_expense_categories_code_slug",
        "ck_expense_categories_code_slug",
    ),
    (
        "household_groups",
        "ck_household_groups_ck_household_groups_code_slug",
        "ck_household_groups_code_slug",
    ),
    (
        "methodology_versions",
        "ck_methodology_versions_ck_methodology_versions_status_known",
        "ck_methodology_versions_status_known",
    ),
    (
        "monthly_series",
        "ck_monthly_series_ck_monthly_series_essentials_non_negative",
        "ck_monthly_series_essentials_non_negative",
    ),
    (
        "monthly_series",
        "ck_monthly_series_ck_monthly_series_month_format",
        "ck_monthly_series_month_format",
    ),
    (
        "reference_households",
        "ck_reference_households_ck_reference_households_househo_88ba",
        "ck_reference_households_household_size_range",
    ),
    (
        "reference_households",
        "ck_reference_households_ck_reference_households_monthly_ffe9",
        "ck_reference_households_monthly_essentials_non_negative",
    ),
    (
        "reference_households",
        "ck_reference_households_ck_reference_households_monthly_5907",
        "ck_reference_households_monthly_income_non_negative",
    ),
    (
        "reference_households",
        "ck_reference_households_ck_reference_households_savings_8615",
        "ck_reference_households_savings_non_negative",
    ),
    (
        "reference_periods",
        "ck_reference_periods_ck_reference_periods_code_month",
        "ck_reference_periods_code_month",
    ),
    (
        "seasonal_swaps",
        "ck_seasonal_swaps_ck_seasonal_swaps_from_price_non_negative",
        "ck_seasonal_swaps_from_price_non_negative",
    ),
    (
        "seasonal_swaps",
        "ck_seasonal_swaps_ck_seasonal_swaps_from_quantity_positive",
        "ck_seasonal_swaps_from_quantity_positive",
    ),
    (
        "seasonal_swaps",
        "ck_seasonal_swaps_ck_seasonal_swaps_month_range",
        "ck_seasonal_swaps_month_range",
    ),
    (
        "seasonal_swaps",
        "ck_seasonal_swaps_ck_seasonal_swaps_to_price_non_negative",
        "ck_seasonal_swaps_to_price_non_negative",
    ),
    (
        "seasonal_swaps",
        "ck_seasonal_swaps_ck_seasonal_swaps_to_quantity_positive",
        "ck_seasonal_swaps_to_quantity_positive",
    ),
    (
        "seasonal_tips",
        "ck_seasonal_tips_ck_seasonal_tips_month_range",
        "ck_seasonal_tips_month_range",
    ),
    (
        "synthetic_households",
        "ck_synthetic_households_ck_synthetic_households_househo_e767",
        "ck_synthetic_households_household_size_range",
    ),
    (
        "synthetic_households",
        "ck_synthetic_households_ck_synthetic_households_monthly_894f",
        "ck_synthetic_households_monthly_essentials_non_negative",
    ),
    (
        "synthetic_households",
        "ck_synthetic_households_ck_synthetic_households_monthly_4fa2",
        "ck_synthetic_households_monthly_income_non_negative",
    ),
    (
        "synthetic_households",
        "ck_synthetic_households_ck_synthetic_households_primary_6693",
        "ck_synthetic_households_primary_income_source_known",
    ),
    (
        "synthetic_households",
        "ck_synthetic_households_ck_synthetic_households_savings_dbad",
        "ck_synthetic_households_savings_non_negative",
    ),
    (
        "vulnerability_bands",
        "ck_vulnerability_bands_ck_vulnerability_bands_score_range",
        "ck_vulnerability_bands_score_range",
    ),
    (
        "vulnerability_models",
        "ck_vulnerability_models_ck_vulnerability_models_weights_range",
        "ck_vulnerability_models_weights_range",
    ),
    (
        "vulnerability_models",
        "ck_vulnerability_models_ck_vulnerability_models_weights_9620",
        "ck_vulnerability_models_weights_sum_to_one",
    ),
)


def _rename(table: str, old: str, new: str) -> None:
    op.execute(f'ALTER TABLE "{table}" RENAME CONSTRAINT "{old}" TO "{new}"')


def upgrade() -> None:
    for table, old, new in RENAMES:
        _rename(table, old, new)


def downgrade() -> None:
    for table, old, new in reversed(RENAMES):
        _rename(table, new, old)
