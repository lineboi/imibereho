"""Household accounts for the register and login endpoints (contract §11.8).

The first table that stores data a person sends: citizen accounts, a Q-02 change for this table
only, made at the project owner's direction on 2026-10-28 (Q-04 unchanged). Seed datasets never
own it, so seeding never touches it. Constraint and index names are wrapped in op.f() (see 0006).

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "household_accounts",
        sa.Column("id", sa.String(30), nullable=False),
        sa.Column("identifier", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("district_code", sa.String(32), nullable=False),
        sa.Column("household_size", sa.SmallInteger(), nullable=False),
        sa.Column("monthly_income", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("preferred_language", sa.String(2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_household_accounts")),
        sa.UniqueConstraint("identifier", name=op.f("uq_household_accounts_identifier")),
        sa.ForeignKeyConstraint(
            ["district_code"],
            ["districts.code"],
            name=op.f("fk_household_accounts_district_code"),
        ),
        sa.CheckConstraint(
            "id ~ '^usr_[0-9A-HJKMNP-TV-Z]{26}$'", name=op.f("ck_household_accounts_id_format")
        ),
        sa.CheckConstraint(
            "household_size BETWEEN 1 AND 20",
            name=op.f("ck_household_accounts_household_size_range"),
        ),
        sa.CheckConstraint(
            "monthly_income BETWEEN 0 AND 100000000",
            name=op.f("ck_household_accounts_monthly_income_range"),
        ),
        sa.CheckConstraint("currency = 'RWF'", name=op.f("ck_household_accounts_currency_known")),
        sa.CheckConstraint(
            "preferred_language IN ('EN', 'RW')",
            name=op.f("ck_household_accounts_preferred_language_known"),
        ),
    )


def downgrade() -> None:
    op.drop_table("household_accounts")
