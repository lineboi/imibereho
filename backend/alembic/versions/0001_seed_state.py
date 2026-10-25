"""seed_state: operational seed tracking (plan A3).

Revision ID: 0001
Revises:
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "seed_state",
        sa.Column("dataset", sa.String(64), nullable=False),
        sa.Column("methodology_version", sa.String(16), nullable=False),
        sa.Column("content_hash", sa.CHAR(64), nullable=False),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("dataset", name="pk_seed_state"),
    )


def downgrade() -> None:
    op.drop_table("seed_state")
