"""Profile fields for `GET` and `PATCH /api/v1/user/profile` (contract §11.9).

Adds the two profile values of MISSING_APIS.pdf's GET example that register does not collect,
`planned_essentials` and `savings_buffer` (whole RWF, NULL until the household sets them, never a
default 0), and `updated_at` (NULL until the first profile change). Existing rows keep NULL, so
the upgrade needs no backfill and takes no long lock. Constraint names are wrapped in op.f().

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "household_accounts"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("planned_essentials", sa.Integer(), nullable=True))
    op.add_column(TABLE, sa.Column("savings_buffer", sa.Integer(), nullable=True))
    op.add_column(TABLE, sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        op.f("ck_household_accounts_planned_essentials_range"),
        TABLE,
        "planned_essentials IS NULL OR planned_essentials BETWEEN 0 AND 100000000",
    )
    op.create_check_constraint(
        op.f("ck_household_accounts_savings_buffer_range"),
        TABLE,
        "savings_buffer IS NULL OR savings_buffer BETWEEN 0 AND 100000000",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_household_accounts_savings_buffer_range"), TABLE, type_="check")
    op.drop_constraint(op.f("ck_household_accounts_planned_essentials_range"), TABLE, type_="check")
    op.drop_column(TABLE, "updated_at")
    op.drop_column(TABLE, "savings_buffer")
    op.drop_column(TABLE, "planned_essentials")
