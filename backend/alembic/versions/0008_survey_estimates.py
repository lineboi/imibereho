"""Official survey estimates with sampling uncertainty (first: EICV7 tables A9.23 and A3.7).

One row per published estimate for one population group (national, area, province, sex,
consumption quintile or district). Values are unconstrained NUMERIC so the source's digits are
kept exactly. Constraint and index names are wrapped in op.f() (see 0006).

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "survey_estimates",
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("table_id", sa.String(16), nullable=False),
        sa.Column("indicator_code", sa.String(64), nullable=False),
        sa.Column("dimension", sa.String(16), nullable=False),
        sa.Column("category_code", sa.String(32), nullable=False),
        sa.Column("district_code", sa.String(32), nullable=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("indicator_label", sa.Text(), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("population", sa.Text(), nullable=False),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.Column("survey_round", sa.String(16), nullable=False),
        sa.Column("estimate_pct", sa.Numeric(), nullable=False),
        sa.Column("standard_error_pct", sa.Numeric(), nullable=True),
        sa.Column("ci_lower_pct", sa.Numeric(), nullable=True),
        sa.Column("ci_upper_pct", sa.Numeric(), nullable=True),
        sa.Column("cv_pct", sa.Numeric(), nullable=True),
        sa.Column("design_effect", sa.Numeric(), nullable=True),
        sa.Column("printed_decimals", sa.SmallInteger(), nullable=False),
        sa.Column("page", sa.SmallInteger(), nullable=False),
        sa.Column("table_or_figure", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint(
            "source_id",
            "table_id",
            "indicator_code",
            "dimension",
            "category_code",
            name=op.f("pk_survey_estimates"),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["statistical_sources.id"],
            name=op.f("fk_survey_estimates_source_id"),
        ),
        sa.ForeignKeyConstraint(
            ["district_code"],
            ["districts.code"],
            name=op.f("fk_survey_estimates_district_code"),
        ),
        sa.CheckConstraint(
            "table_id ~ '^[A-Z]?[0-9]+[.][0-9]+$'",
            name=op.f("ck_survey_estimates_table_id_format"),
        ),
        sa.CheckConstraint(
            "indicator_code ~ '^[a-z0-9_]+$'",
            name=op.f("ck_survey_estimates_indicator_code_slug"),
        ),
        sa.CheckConstraint(
            "category_code ~ '^[a-z0-9_]+$'",
            name=op.f("ck_survey_estimates_category_code_slug"),
        ),
        sa.CheckConstraint(
            "dimension IN ('national', 'area', 'province', 'sex', 'quintile', 'district')",
            name=op.f("ck_survey_estimates_dimension_known"),
        ),
        sa.CheckConstraint(
            "(dimension = 'district') = (district_code IS NOT NULL)",
            name=op.f("ck_survey_estimates_district_dimension"),
        ),
        sa.CheckConstraint("unit = 'percent'", name=op.f("ck_survey_estimates_unit_known")),
        sa.CheckConstraint(
            "estimate_pct BETWEEN 0 AND 100",
            name=op.f("ck_survey_estimates_estimate_pct_range"),
        ),
        sa.CheckConstraint(
            "(ci_lower_pct IS NULL) = (ci_upper_pct IS NULL)",
            name=op.f("ck_survey_estimates_ci_complete"),
        ),
        sa.CheckConstraint(
            "ci_lower_pct IS NULL OR estimate_pct BETWEEN ci_lower_pct AND ci_upper_pct",
            name=op.f("ck_survey_estimates_ci_contains_estimate"),
        ),
        sa.CheckConstraint(
            "(standard_error_pct IS NULL OR standard_error_pct >= 0)"
            " AND (cv_pct IS NULL OR cv_pct >= 0)"
            " AND (design_effect IS NULL OR design_effect >= 0)",
            name=op.f("ck_survey_estimates_uncertainty_nonnegative"),
        ),
        sa.CheckConstraint(
            "printed_decimals BETWEEN 0 AND 6",
            name=op.f("ck_survey_estimates_printed_decimals_range"),
        ),
        sa.CheckConstraint("page > 0", name=op.f("ck_survey_estimates_page_positive")),
    )
    op.create_index(
        op.f("ix_survey_estimates_source_id_indicator_code_sort_order"),
        "survey_estimates",
        ["source_id", "indicator_code", "sort_order"],
    )
    op.create_index(
        op.f("ix_survey_estimates_district_code"), "survey_estimates", ["district_code"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_survey_estimates_district_code"), "survey_estimates")
    op.drop_index(
        op.f("ix_survey_estimates_source_id_indicator_code_sort_order"), "survey_estimates"
    )
    op.drop_table("survey_estimates")
