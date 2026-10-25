"""Budget benchmarks (plan F3).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "budget_benchmarks",
        sa.Column("methodology_version", sa.String(16), nullable=False),
        sa.Column("district_code", sa.String(32), nullable=False),
        sa.Column("household_size", sa.SmallInteger(), nullable=False),
        sa.Column("category_code", sa.String(32), nullable=False),
        sa.Column("monthly_amount", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint(
            "methodology_version",
            "district_code",
            "household_size",
            "category_code",
            name="pk_budget_benchmarks",
        ),
        sa.ForeignKeyConstraint(
            ["methodology_version"],
            ["methodology_versions.version"],
            name="fk_budget_benchmarks_methodology_version",
        ),
        sa.ForeignKeyConstraint(
            ["district_code"],
            ["districts.code"],
            name="fk_budget_benchmarks_district_code",
        ),
        sa.ForeignKeyConstraint(
            ["category_code"],
            ["expense_categories.code"],
            name="fk_budget_benchmarks_category_code",
        ),
        sa.CheckConstraint(
            "household_size BETWEEN 1 AND 20", name="ck_budget_benchmarks_household_size_range"
        ),
        sa.CheckConstraint(
            "monthly_amount >= 0", name="ck_budget_benchmarks_monthly_amount_non_negative"
        ),
    )


def downgrade() -> None:
    op.drop_table("budget_benchmarks")
