"""Reference data: methodology versions, districts, categories, reference household (plan F2).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "methodology_versions",
        sa.Column("version", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("version", name="pk_methodology_versions"),
        sa.CheckConstraint("status = 'concept'", name="ck_methodology_versions_status_known"),
    )
    op.create_index(
        "uq_methodology_versions_is_current",
        "methodology_versions",
        ["is_current"],
        unique=True,
        postgresql_where=sa.text("is_current"),
    )
    op.create_table(
        "districts",
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("name_rw", sa.String(64), nullable=True),
        sa.Column("province", sa.String(64), nullable=True),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_districts"),
        sa.UniqueConstraint("name", name="uq_districts_name"),
        sa.UniqueConstraint("sort_order", name="uq_districts_sort_order"),
        sa.CheckConstraint("code ~ '^[a-z]+$'", name="ck_districts_code_slug"),
    )
    op.create_table(
        "expense_categories",
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name_en", sa.String(64), nullable=False),
        sa.Column("name_rw", sa.String(64), nullable=True),
        sa.Column("icon", sa.String(64), nullable=True),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_expense_categories"),
        sa.UniqueConstraint("sort_order", name="uq_expense_categories_sort_order"),
        sa.CheckConstraint("code ~ '^[a-z_]+$'", name="ck_expense_categories_code_slug"),
    )
    op.create_table(
        "reference_households",
        sa.Column("methodology_version", sa.String(16), nullable=False),
        sa.Column("district_code", sa.String(32), nullable=False),
        sa.Column("household_size", sa.SmallInteger(), nullable=False),
        sa.Column("monthly_income", sa.Integer(), nullable=False),
        sa.Column("monthly_essentials", sa.Integer(), nullable=False),
        sa.Column("savings", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("methodology_version", name="pk_reference_households"),
        sa.ForeignKeyConstraint(
            ["methodology_version"],
            ["methodology_versions.version"],
            name="fk_reference_households_methodology_version",
        ),
        sa.ForeignKeyConstraint(
            ["district_code"],
            ["districts.code"],
            name="fk_reference_households_district_code",
        ),
        sa.CheckConstraint(
            "household_size BETWEEN 1 AND 20",
            name="ck_reference_households_household_size_range",
        ),
        sa.CheckConstraint(
            "monthly_income >= 0", name="ck_reference_households_monthly_income_non_negative"
        ),
        sa.CheckConstraint(
            "monthly_essentials >= 0",
            name="ck_reference_households_monthly_essentials_non_negative",
        ),
        sa.CheckConstraint("savings >= 0", name="ck_reference_households_savings_non_negative"),
    )


def downgrade() -> None:
    op.drop_table("reference_households")
    op.drop_table("expense_categories")
    op.drop_table("districts")
    op.drop_index("uq_methodology_versions_is_current", table_name="methodology_versions")
    op.drop_table("methodology_versions")
