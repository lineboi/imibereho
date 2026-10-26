"""Official published statistics: their source documents and the values transcribed from them.

Unlike the illustrative v0.1 datasets, these rows are published figures from an identified
document. Every row cites its page and table/figure. They are population aggregates, never
individual or household records (Q-02 still holds).
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StatisticalSource(Base):
    __tablename__ = "statistical_sources"
    __table_args__ = (
        CheckConstraint("id ~ '^[a-z0-9-]+$'", name="id_slug"),
        CheckConstraint("sample_size IS NULL OR sample_size > 0", name="sample_size_positive"),
        CheckConstraint("document_sha256 ~ '^[0-9a-f]{64}$'", name="document_sha256_hex"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    publisher: Mapped[str] = mapped_column(Text)
    sponsors: Mapped[str | None] = mapped_column(Text)
    distributor: Mapped[str | None] = mapped_column(Text)
    citation: Mapped[str] = mapped_column(Text)
    publication_date: Mapped[str] = mapped_column(String(10))
    survey_round: Mapped[str] = mapped_column(String(16))
    fieldwork_period: Mapped[str | None] = mapped_column(Text)
    population: Mapped[str] = mapped_column(Text)
    sample_size: Mapped[int | None] = mapped_column(Integer)
    lowest_published_geography: Mapped[str] = mapped_column(String(32))
    document_file: Mapped[str] = mapped_column(Text)
    document_url: Mapped[str] = mapped_column(Text)
    catalog_url: Mapped[str | None] = mapped_column(Text)
    document_sha256: Mapped[str] = mapped_column(CHAR(64))
    retrieved_on: Mapped[date] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)


class FinancialInclusionIndicator(Base):
    """A national indicator as published, with its optional comparison-year value."""

    __tablename__ = "financial_inclusion_indicators"
    __table_args__ = (
        CheckConstraint("value_pct BETWEEN 0 AND 100", name="value_pct_range"),
        CheckConstraint(
            "comparison_value_pct IS NULL OR comparison_value_pct BETWEEN 0 AND 100",
            name="comparison_value_pct_range",
        ),
        CheckConstraint(
            "(comparison_year IS NULL) = (comparison_value_pct IS NULL)",
            name="comparison_complete",
        ),
        CheckConstraint(
            "measure IN ('inclusion_overview', 'access_strand', 'financial_health_strand')",
            name="measure_known",
        ),
        CheckConstraint("page > 0", name="page_positive"),
    )

    source_id: Mapped[str] = mapped_column(ForeignKey("statistical_sources.id"), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    measure: Mapped[str] = mapped_column(String(32))
    label: Mapped[str] = mapped_column(Text)
    definition: Mapped[str] = mapped_column(Text)
    population: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(16))
    year: Mapped[int] = mapped_column(SmallInteger)
    value_pct: Mapped[int] = mapped_column(SmallInteger)
    count_published: Mapped[str | None] = mapped_column(String(32))
    comparison_year: Mapped[int | None] = mapped_column(SmallInteger)
    comparison_value_pct: Mapped[int | None] = mapped_column(SmallInteger)
    comparison_count_published: Mapped[str | None] = mapped_column(String(32))
    page: Mapped[int] = mapped_column(SmallInteger)
    table_or_figure: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger)


class FinancialAccessStrandDistrict(Base):
    """One district's published access strand. A NULL share means no value is printed."""

    __tablename__ = "financial_access_strand_districts"
    __table_args__ = (
        CheckConstraint(
            "banked_pct BETWEEN 0 AND 100 AND other_formal_non_bank_pct BETWEEN 0 AND 100"
            " AND (informal_only_pct IS NULL OR informal_only_pct BETWEEN 0 AND 100)"
            " AND excluded_pct BETWEEN 0 AND 100",
            name="shares_range",
        ),
        CheckConstraint("page > 0", name="page_positive"),
    )

    source_id: Mapped[str] = mapped_column(ForeignKey("statistical_sources.id"), primary_key=True)
    district_code: Mapped[str] = mapped_column(ForeignKey("districts.code"), primary_key=True)
    banked_pct: Mapped[int] = mapped_column(SmallInteger)
    other_formal_non_bank_pct: Mapped[int] = mapped_column(SmallInteger)
    informal_only_pct: Mapped[int | None] = mapped_column(SmallInteger)
    excluded_pct: Mapped[int] = mapped_column(SmallInteger)
    page: Mapped[int] = mapped_column(SmallInteger)
    table_or_figure: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class SurveyEstimate(Base):
    """One published survey estimate for one population group, with its sampling uncertainty.

    Values are stored as unconstrained NUMERIC, so the source's digits are kept exactly (no
    float, no fixed scale). Percentages and the standard error and CI bounds are on a 0-100
    scale; `cv_pct` is the coefficient of variation in percent; `design_effect` has no unit.
    A NULL uncertainty field means the source publishes none for that record.
    """

    __tablename__ = "survey_estimates"
    __table_args__ = (
        CheckConstraint("table_id ~ '^[A-Z]?[0-9]+[.][0-9]+$'", name="table_id_format"),
        CheckConstraint("indicator_code ~ '^[a-z0-9_]+$'", name="indicator_code_slug"),
        CheckConstraint("category_code ~ '^[a-z0-9_]+$'", name="category_code_slug"),
        CheckConstraint(
            "dimension IN ('national', 'area', 'province', 'sex', 'quintile', 'district')",
            name="dimension_known",
        ),
        CheckConstraint(
            "(dimension = 'district') = (district_code IS NOT NULL)", name="district_dimension"
        ),
        CheckConstraint("unit = 'percent'", name="unit_known"),
        CheckConstraint("estimate_pct BETWEEN 0 AND 100", name="estimate_pct_range"),
        CheckConstraint("(ci_lower_pct IS NULL) = (ci_upper_pct IS NULL)", name="ci_complete"),
        CheckConstraint(
            "ci_lower_pct IS NULL OR estimate_pct BETWEEN ci_lower_pct AND ci_upper_pct",
            name="ci_contains_estimate",
        ),
        CheckConstraint(
            "(standard_error_pct IS NULL OR standard_error_pct >= 0)"
            " AND (cv_pct IS NULL OR cv_pct >= 0)"
            " AND (design_effect IS NULL OR design_effect >= 0)",
            name="uncertainty_nonnegative",
        ),
        CheckConstraint("printed_decimals BETWEEN 0 AND 6", name="printed_decimals_range"),
        CheckConstraint("page > 0", name="page_positive"),
        Index("ix_survey_estimates_source_id_indicator_code_sort_order",
              "source_id", "indicator_code", "sort_order"),
        Index("ix_survey_estimates_district_code", "district_code"),
    )  # fmt: skip

    source_id: Mapped[str] = mapped_column(ForeignKey("statistical_sources.id"), primary_key=True)
    table_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    indicator_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    dimension: Mapped[str] = mapped_column(String(16), primary_key=True)
    category_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    district_code: Mapped[str | None] = mapped_column(ForeignKey("districts.code"))
    label: Mapped[str] = mapped_column(Text)
    indicator_label: Mapped[str] = mapped_column(Text)
    definition: Mapped[str] = mapped_column(Text)
    population: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(16))
    survey_round: Mapped[str] = mapped_column(String(16))
    estimate_pct: Mapped[Decimal] = mapped_column(Numeric)
    standard_error_pct: Mapped[Decimal | None] = mapped_column(Numeric)
    ci_lower_pct: Mapped[Decimal | None] = mapped_column(Numeric)
    ci_upper_pct: Mapped[Decimal | None] = mapped_column(Numeric)
    cv_pct: Mapped[Decimal | None] = mapped_column(Numeric)
    design_effect: Mapped[Decimal | None] = mapped_column(Numeric)
    printed_decimals: Mapped[int] = mapped_column(SmallInteger)
    page: Mapped[int] = mapped_column(SmallInteger)
    table_or_figure: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger)
