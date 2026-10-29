"""The household's workspace role, `citizen` or `decision_maker` (`household_accounts.role`).

`HouseholdAccount.role` was added to the model without a migration, so on a database built from
the migrations every query on `household_accounts` failed (register and login answered 500).
Existing rows get 'citizen' from the server default. The column is added only if it is missing,
because a live database may already have been given it by hand; the check constraint is then
(re)created under the convention's name.

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-29
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "household_accounts"
CONSTRAINT = "ck_household_accounts_role_known"


def upgrade() -> None:
    op.execute(
        f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS role VARCHAR(32) DEFAULT 'citizen' NOT NULL"
    )
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {CONSTRAINT}")
    op.create_check_constraint(op.f(CONSTRAINT), TABLE, "role IN ('citizen', 'decision_maker')")


def downgrade() -> None:
    op.drop_constraint(op.f(CONSTRAINT), TABLE, type_="check")
    op.drop_column(TABLE, "role")
