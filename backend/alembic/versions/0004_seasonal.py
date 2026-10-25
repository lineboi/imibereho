"""Seasonal swaps and tips (plan F5).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "seasonal_swaps",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("methodology_version", sa.String(16), nullable=False),
        sa.Column("district_code", sa.String(32), nullable=True),
        sa.Column("month", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("footnote", sa.Text(), nullable=False),
        sa.Column("from_name", sa.String(64), nullable=False),
        sa.Column("from_quantity", sa.Numeric(6, 2), nullable=False),
        sa.Column("from_unit", sa.String(16), nullable=False),
        sa.Column("from_price", sa.Integer(), nullable=False),
        sa.Column("to_name", sa.String(64), nullable=False),
        sa.Column("to_quantity", sa.Numeric(6, 2), nullable=False),
        sa.Column("to_unit", sa.String(16), nullable=False),
        sa.Column("to_price", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_seasonal_swaps"),
        sa.ForeignKeyConstraint(
            ["methodology_version"],
            ["methodology_versions.version"],
            name="fk_seasonal_swaps_methodology_version",
        ),
        sa.ForeignKeyConstraint(
            ["district_code"], ["districts.code"], name="fk_seasonal_swaps_district_code"
        ),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="ck_seasonal_swaps_month_range"),
        sa.CheckConstraint("from_quantity > 0", name="ck_seasonal_swaps_from_quantity_positive"),
        sa.CheckConstraint("to_quantity > 0", name="ck_seasonal_swaps_to_quantity_positive"),
        sa.CheckConstraint("from_price >= 0", name="ck_seasonal_swaps_from_price_non_negative"),
        sa.CheckConstraint("to_price >= 0", name="ck_seasonal_swaps_to_price_non_negative"),
    )
    op.create_index(
        "ix_seasonal_swaps_month_district_code", "seasonal_swaps", ["month", "district_code"]
    )
    op.create_table(
        "seasonal_tips",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("methodology_version", sa.String(16), nullable=False),
        sa.Column("district_code", sa.String(32), nullable=True),
        sa.Column("month", sa.SmallInteger(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_seasonal_tips"),
        sa.ForeignKeyConstraint(
            ["methodology_version"],
            ["methodology_versions.version"],
            name="fk_seasonal_tips_methodology_version",
        ),
        sa.ForeignKeyConstraint(
            ["district_code"], ["districts.code"], name="fk_seasonal_tips_district_code"
        ),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="ck_seasonal_tips_month_range"),
    )


def downgrade() -> None:
    op.drop_table("seasonal_tips")
    op.drop_index("ix_seasonal_swaps_month_district_code", table_name="seasonal_swaps")
    op.drop_table("seasonal_swaps")
