"""Decision-maker dataset: periods, groups, series, synthetic households, vulnerability (plan F6).

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MV = "methodology_versions.version"


def _version_fk(table: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["methodology_version"], [_MV], name=f"fk_{table}_methodology_version"
    )


def upgrade() -> None:
    for table, check_name, pattern in (
        ("reference_periods", "code_month", "^[0-9]{4}-[0-9]{2}$"),
        ("household_groups", "code_slug", "^[a-z_]+$"),
    ):
        op.create_table(
            table,
            sa.Column("code", sa.String(7 if table == "reference_periods" else 32), nullable=False),
            sa.Column("methodology_version", sa.String(16), nullable=False),
            sa.Column("label", sa.String(64), nullable=False),
            sa.Column("is_default", sa.Boolean(), nullable=False),
            sa.Column("sort_order", sa.SmallInteger(), nullable=False),
            sa.PrimaryKeyConstraint("code", name=f"pk_{table}"),
            _version_fk(table),
            sa.CheckConstraint(f"code ~ '{pattern}'", name=f"ck_{table}_{check_name}"),
        )

    op.create_table(
        "monthly_series",
        sa.Column("methodology_version", sa.String(16), nullable=False),
        sa.Column("series_code", sa.String(32), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("essentials", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint(
            "methodology_version", "series_code", "month", name="pk_monthly_series"
        ),
        _version_fk("monthly_series"),
        sa.CheckConstraint("month ~ '^[0-9]{4}-[0-9]{2}$'", name="ck_monthly_series_month_format"),
        sa.CheckConstraint("essentials >= 0", name="ck_monthly_series_essentials_non_negative"),
    )

    op.create_table(
        "synthetic_households",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("methodology_version", sa.String(16), nullable=False),
        sa.Column("district_code", sa.String(32), nullable=False),
        sa.Column("household_size", sa.SmallInteger(), nullable=False),
        sa.Column("primary_income_source", sa.String(32), nullable=False),
        sa.Column("monthly_income", sa.Integer(), nullable=False),
        sa.Column("monthly_essentials", sa.Integer(), nullable=False),
        sa.Column("savings", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_synthetic_households"),
        _version_fk("synthetic_households"),
        sa.ForeignKeyConstraint(
            ["district_code"],
            ["districts.code"],
            name="fk_synthetic_households_district_code",
        ),
        sa.CheckConstraint(
            "household_size BETWEEN 1 AND 20", name="ck_synthetic_households_household_size_range"
        ),
        sa.CheckConstraint(
            "primary_income_source IN ('wage', 'agriculture', 'informal_enterprise')",
            name="ck_synthetic_households_primary_income_source_known",
        ),
        sa.CheckConstraint(
            "monthly_income >= 0", name="ck_synthetic_households_monthly_income_non_negative"
        ),
        sa.CheckConstraint(
            "monthly_essentials >= 0",
            name="ck_synthetic_households_monthly_essentials_non_negative",
        ),
        sa.CheckConstraint("savings >= 0", name="ck_synthetic_households_savings_non_negative"),
    )
    op.create_index(
        "ix_synthetic_households_methodology_version",
        "synthetic_households",
        ["methodology_version"],
    )
    op.create_index(
        "ix_synthetic_households_district_code", "synthetic_households", ["district_code"]
    )

    op.create_table(
        "vulnerability_models",
        sa.Column("version", sa.String(16), nullable=False),
        sa.Column("weight_income_instability", sa.Numeric(3, 2), nullable=False),
        sa.Column("weight_essential_cost_pressure", sa.Numeric(3, 2), nullable=False),
        sa.Column("weight_low_buffer_exposure", sa.Numeric(3, 2), nullable=False),
        sa.PrimaryKeyConstraint("version", name="pk_vulnerability_models"),
        sa.ForeignKeyConstraint(["version"], [_MV], name="fk_vulnerability_models_version"),
        sa.CheckConstraint(
            "weight_income_instability + weight_essential_cost_pressure"
            " + weight_low_buffer_exposure = 1.00",
            name="ck_vulnerability_models_weights_sum_to_one",
        ),
        sa.CheckConstraint(
            "weight_income_instability BETWEEN 0 AND 1"
            " AND weight_essential_cost_pressure BETWEEN 0 AND 1"
            " AND weight_low_buffer_exposure BETWEEN 0 AND 1",
            name="ck_vulnerability_models_weights_range",
        ),
    )

    op.create_table(
        "vulnerability_bands",
        sa.Column("model_version", sa.String(16), nullable=False),
        sa.Column("key", sa.String(8), nullable=False),
        sa.Column("min_score", sa.SmallInteger(), nullable=False),
        sa.Column("max_score", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("model_version", "key", name="pk_vulnerability_bands"),
        sa.ForeignKeyConstraint(
            ["model_version"],
            ["vulnerability_models.version"],
            name="fk_vulnerability_bands_model_version",
        ),
        sa.CheckConstraint(
            "min_score BETWEEN 0 AND 100 AND max_score BETWEEN 0 AND 100"
            " AND min_score <= max_score",
            name="ck_vulnerability_bands_score_range",
        ),
    )

    op.create_table(
        "district_vulnerability",
        sa.Column("model_version", sa.String(16), nullable=False),
        sa.Column("period_code", sa.String(7), nullable=False),
        sa.Column("household_group_code", sa.String(32), nullable=False),
        sa.Column("district_code", sa.String(32), nullable=False),
        sa.Column("income_instability", sa.SmallInteger(), nullable=False),
        sa.Column("essential_cost_pressure", sa.SmallInteger(), nullable=False),
        sa.Column("low_buffer_exposure", sa.SmallInteger(), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.PrimaryKeyConstraint(
            "model_version",
            "period_code",
            "household_group_code",
            "district_code",
            name="pk_district_vulnerability",
        ),
        sa.ForeignKeyConstraint(
            ["model_version"],
            ["vulnerability_models.version"],
            name="fk_district_vulnerability_model_version",
        ),
        sa.ForeignKeyConstraint(
            ["period_code"],
            ["reference_periods.code"],
            name="fk_district_vulnerability_period_code",
        ),
        sa.ForeignKeyConstraint(
            ["household_group_code"],
            ["household_groups.code"],
            name="fk_district_vulnerability_household_group_code",
        ),
        sa.ForeignKeyConstraint(
            ["district_code"],
            ["districts.code"],
            name="fk_district_vulnerability_district_code",
        ),
        sa.CheckConstraint(
            "income_instability BETWEEN 0 AND 100"
            " AND essential_cost_pressure BETWEEN 0 AND 100"
            " AND low_buffer_exposure BETWEEN 0 AND 100",
            name="ck_district_vulnerability_components_range",
        ),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="ck_district_vulnerability_score_range"),
    )
    op.create_index(
        "ix_district_vulnerability_period_code_score",
        "district_vulnerability",
        ["period_code", "score"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_district_vulnerability_period_code_score", table_name="district_vulnerability"
    )
    op.drop_table("district_vulnerability")
    op.drop_table("vulnerability_bands")
    op.drop_table("vulnerability_models")
    op.drop_index("ix_synthetic_households_district_code", table_name="synthetic_households")
    op.drop_index("ix_synthetic_households_methodology_version", table_name="synthetic_households")
    op.drop_table("synthetic_households")
    op.drop_table("monthly_series")
    op.drop_table("household_groups")
    op.drop_table("reference_periods")
