"""Daily tracker transactions (contract §11.10).

A new table, so the upgrade touches no existing row. Rows cascade with their account. Constraint
and index names are wrapped in op.f() (see 0006) and match the model's naming convention.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "tracker_transactions"
EXPENSE = "'food', 'transport', 'utilities', 'other'"
INCOME = "'mobile_money', 'day_wage', 'market_sales', 'side_gig'"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.String(30), nullable=False),
        sa.Column("account_id", sa.String(30), nullable=False),
        sa.Column("type", sa.String(7), nullable=False),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("note", sa.String(280), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=True),
        sa.Column("request_hash", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tracker_transactions")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["household_accounts.id"],
            name=op.f("fk_tracker_transactions_account_id"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "account_id",
            "idempotency_key",
            name=op.f("uq_tracker_transactions_account_id_idempotency_key"),
        ),
        sa.CheckConstraint(
            "id ~ '^tx_[0-9A-HJKMNP-TV-Z]{26}$'", name=op.f("ck_tracker_transactions_id_format")
        ),
        sa.CheckConstraint(
            "type IN ('expense', 'income')", name=op.f("ck_tracker_transactions_type_known")
        ),
        sa.CheckConstraint(
            f"(type = 'expense' AND category IN ({EXPENSE}))"
            f" OR (type = 'income' AND category IN ({INCOME}))",
            name=op.f("ck_tracker_transactions_category_matches_type"),
        ),
        sa.CheckConstraint(
            "amount BETWEEN 1 AND 100000000", name=op.f("ck_tracker_transactions_amount_range")
        ),
        sa.CheckConstraint(
            "length(btrim(title)) BETWEEN 1 AND 120",
            name=op.f("ck_tracker_transactions_title_length"),
        ),
        sa.CheckConstraint(
            "note IS NULL OR length(note) <= 280", name=op.f("ck_tracker_transactions_note_length")
        ),
        sa.CheckConstraint(
            "(idempotency_key IS NULL) = (request_hash IS NULL)",
            name=op.f("ck_tracker_transactions_idempotency_complete"),
        ),
    )
    op.create_index(
        op.f("ix_tracker_transactions_account_id_occurred_at_id"),
        TABLE,
        ["account_id", "occurred_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tracker_transactions_account_id_occurred_at_id"), TABLE)
    op.drop_table(TABLE)
