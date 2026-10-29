"""The household's saved resilience plan (contract §11.11).

A new table, so the upgrade touches no existing row. One row per account, cascading with it.
Constraint names are wrapped in op.f() (see 0006) and match the model's naming convention.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "resilience_plans"
SHOCKS = "'income_drop', 'medical_emergency', 'school_fees', 'harvest_disruption'"
LUMP_SUMS = "'medical_emergency', 'school_fees'"
LEVERS = "'trim_non_essentials', 'seasonal_agro_swaps', 'ibimina_tontine'"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("account_id", sa.String(30), nullable=False),
        sa.Column("monthly_income", sa.Integer(), nullable=False),
        sa.Column("monthly_essentials", sa.Integer(), nullable=False),
        sa.Column("savings", sa.Integer(), nullable=False),
        sa.Column("shock_type", sa.String(24), nullable=False),
        sa.Column("income_reduction_pct", sa.SmallInteger(), nullable=True),
        sa.Column("duration_months", sa.SmallInteger(), nullable=False),
        sa.Column("shock_amount", sa.Integer(), nullable=True),
        sa.Column("coping_levers", postgresql.ARRAY(sa.String(32)), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("account_id", name=op.f("pk_resilience_plans")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["household_accounts.id"],
            name=op.f("fk_resilience_plans_account_id"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "monthly_income BETWEEN 0 AND 100000000",
            name=op.f("ck_resilience_plans_monthly_income_range"),
        ),
        sa.CheckConstraint(
            "monthly_essentials BETWEEN 0 AND 100000000",
            name=op.f("ck_resilience_plans_monthly_essentials_range"),
        ),
        sa.CheckConstraint(
            "savings BETWEEN 0 AND 100000000", name=op.f("ck_resilience_plans_savings_range")
        ),
        sa.CheckConstraint(
            f"shock_type IN ({SHOCKS})", name=op.f("ck_resilience_plans_shock_type_known")
        ),
        sa.CheckConstraint(
            "duration_months BETWEEN 1 AND 24",
            name=op.f("ck_resilience_plans_duration_months_range"),
        ),
        sa.CheckConstraint(
            f"(shock_type IN ({LUMP_SUMS}) AND income_reduction_pct IS NULL"
            " AND (shock_amount IS NULL OR shock_amount BETWEEN 0 AND 100000000))"
            f" OR (shock_type NOT IN ({LUMP_SUMS}) AND shock_amount IS NULL"
            " AND income_reduction_pct IS NOT NULL AND income_reduction_pct BETWEEN 0 AND 100)",
            name=op.f("ck_resilience_plans_shock_fields_match_type"),
        ),
        sa.CheckConstraint(
            f"coping_levers <@ ARRAY[{LEVERS}]::varchar[]"
            " AND cardinality(coping_levers) <= 3"
            " AND (cardinality(coping_levers) < 2 OR coping_levers[1] <> coping_levers[2])"
            " AND (cardinality(coping_levers) < 3 OR (coping_levers[1] <> coping_levers[3]"
            " AND coping_levers[2] <> coping_levers[3]))",
            name=op.f("ck_resilience_plans_coping_levers_known_and_unique"),
        ),
    )


def downgrade() -> None:
    op.drop_table(TABLE)
