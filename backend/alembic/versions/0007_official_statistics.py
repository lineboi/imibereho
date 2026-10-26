"""Official published statistics: sources, national financial-inclusion indicators, districts.

Tables for values transcribed from an identified publication (first: FinScope Rwanda 2024).
Constraint names are wrapped in op.f() so the naming convention is not applied twice (see 0006).

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "statistical_sources",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("publisher", sa.Text(), nullable=False),
        sa.Column("sponsors", sa.Text(), nullable=True),
        sa.Column("distributor", sa.Text(), nullable=True),
        sa.Column("citation", sa.Text(), nullable=False),
        sa.Column("publication_date", sa.String(10), nullable=False),
        sa.Column("survey_round", sa.String(16), nullable=False),
        sa.Column("fieldwork_period", sa.Text(), nullable=True),
        sa.Column("population", sa.Text(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("lowest_published_geography", sa.String(32), nullable=False),
        sa.Column("document_file", sa.Text(), nullable=False),
        sa.Column("document_url", sa.Text(), nullable=False),
        sa.Column("catalog_url", sa.Text(), nullable=True),
        sa.Column("document_sha256", sa.CHAR(64), nullable=False),
        sa.Column("retrieved_on", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_statistical_sources")),
        sa.CheckConstraint("id ~ '^[a-z0-9-]+$'", name=op.f("ck_statistical_sources_id_slug")),
        sa.CheckConstraint(
            "sample_size IS NULL OR sample_size > 0",
            name=op.f("ck_statistical_sources_sample_size_positive"),
        ),
        sa.CheckConstraint(
            "document_sha256 ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_statistical_sources_document_sha256_hex"),
        ),
    )
    op.create_table(
        "financial_inclusion_indicators",
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("measure", sa.String(32), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("population", sa.Text(), nullable=False),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("value_pct", sa.SmallInteger(), nullable=False),
        sa.Column("count_published", sa.String(32), nullable=True),
        sa.Column("comparison_year", sa.SmallInteger(), nullable=True),
        sa.Column("comparison_value_pct", sa.SmallInteger(), nullable=True),
        sa.Column("comparison_count_published", sa.String(32), nullable=True),
        sa.Column("page", sa.SmallInteger(), nullable=False),
        sa.Column("table_or_figure", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint(
            "source_id", "code", name=op.f("pk_financial_inclusion_indicators")
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["statistical_sources.id"],
            name=op.f("fk_financial_inclusion_indicators_source_id"),
        ),
        sa.CheckConstraint(
            "value_pct BETWEEN 0 AND 100",
            name=op.f("ck_financial_inclusion_indicators_value_pct_range"),
        ),
        sa.CheckConstraint(
            "comparison_value_pct IS NULL OR comparison_value_pct BETWEEN 0 AND 100",
            name=op.f("ck_financial_inclusion_indicators_comparison_value_pct_range"),
        ),
        sa.CheckConstraint(
            "(comparison_year IS NULL) = (comparison_value_pct IS NULL)",
            name=op.f("ck_financial_inclusion_indicators_comparison_complete"),
        ),
        sa.CheckConstraint(
            "measure IN ('inclusion_overview', 'access_strand', 'financial_health_strand')",
            name=op.f("ck_financial_inclusion_indicators_measure_known"),
        ),
        sa.CheckConstraint(
            "page > 0", name=op.f("ck_financial_inclusion_indicators_page_positive")
        ),
    )
    op.create_table(
        "financial_access_strand_districts",
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("district_code", sa.String(32), nullable=False),
        sa.Column("banked_pct", sa.SmallInteger(), nullable=False),
        sa.Column("other_formal_non_bank_pct", sa.SmallInteger(), nullable=False),
        sa.Column("informal_only_pct", sa.SmallInteger(), nullable=True),
        sa.Column("excluded_pct", sa.SmallInteger(), nullable=False),
        sa.Column("page", sa.SmallInteger(), nullable=False),
        sa.Column("table_or_figure", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint(
            "source_id", "district_code", name=op.f("pk_financial_access_strand_districts")
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["statistical_sources.id"],
            name=op.f("fk_financial_access_strand_districts_source_id"),
        ),
        sa.ForeignKeyConstraint(
            ["district_code"],
            ["districts.code"],
            name=op.f("fk_financial_access_strand_districts_district_code"),
        ),
        sa.CheckConstraint(
            "banked_pct BETWEEN 0 AND 100 AND other_formal_non_bank_pct BETWEEN 0 AND 100"
            " AND (informal_only_pct IS NULL OR informal_only_pct BETWEEN 0 AND 100)"
            " AND excluded_pct BETWEEN 0 AND 100",
            name=op.f("ck_financial_access_strand_districts_shares_range"),
        ),
        sa.CheckConstraint(
            "page > 0", name=op.f("ck_financial_access_strand_districts_page_positive")
        ),
    )


def downgrade() -> None:
    op.drop_table("financial_access_strand_districts")
    op.drop_table("financial_inclusion_indicators")
    op.drop_table("statistical_sources")
