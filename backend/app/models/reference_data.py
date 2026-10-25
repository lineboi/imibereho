"""Reference data shared by every screen: methodology version, districts, categories, filters.

All rows are seeded (plan F2, F6). Nothing here is citizen data.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MethodologyVersion(Base):
    __tablename__ = "methodology_versions"
    __table_args__ = (
        CheckConstraint("status = 'concept'", name="status_known"),
        Index(
            "uq_methodology_versions_is_current",
            "is_current",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )

    version: Mapped[str] = mapped_column(String(16), primary_key=True)
    status: Mapped[str] = mapped_column(String(16))
    is_current: Mapped[bool] = mapped_column(Boolean)


class District(Base):
    __tablename__ = "districts"
    __table_args__ = (CheckConstraint("code ~ '^[a-z]+$'", name="code_slug"),)

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    name_rw: Mapped[str | None] = mapped_column(String(64))
    province: Mapped[str | None] = mapped_column(String(64))
    sort_order: Mapped[int] = mapped_column(SmallInteger, unique=True)


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"
    __table_args__ = (CheckConstraint("code ~ '^[a-z_]+$'", name="code_slug"),)

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(64))
    name_rw: Mapped[str | None] = mapped_column(String(64))
    icon: Mapped[str | None] = mapped_column(String(64))
    sort_order: Mapped[int] = mapped_column(SmallInteger, unique=True)


class ReferencePeriod(Base):
    __tablename__ = "reference_periods"
    __table_args__ = (CheckConstraint("code ~ '^[0-9]{4}-[0-9]{2}$'", name="code_month"),)

    code: Mapped[str] = mapped_column(String(7), primary_key=True)
    methodology_version: Mapped[str] = mapped_column(ForeignKey("methodology_versions.version"))
    label: Mapped[str] = mapped_column(String(64))
    is_default: Mapped[bool] = mapped_column(Boolean)
    sort_order: Mapped[int] = mapped_column(SmallInteger)


class HouseholdGroup(Base):
    __tablename__ = "household_groups"
    __table_args__ = (CheckConstraint("code ~ '^[a-z_]+$'", name="code_slug"),)

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    methodology_version: Mapped[str] = mapped_column(ForeignKey("methodology_versions.version"))
    label: Mapped[str] = mapped_column(String(64))
    is_default: Mapped[bool] = mapped_column(Boolean)
    sort_order: Mapped[int] = mapped_column(SmallInteger)


class MonthlySeriesPoint(Base):
    """The D1 essentials trend for the reference household ([PD] Q-33)."""

    __tablename__ = "monthly_series"
    __table_args__ = (
        CheckConstraint("month ~ '^[0-9]{4}-[0-9]{2}$'", name="month_format"),
        CheckConstraint("essentials >= 0", name="essentials_non_negative"),
    )

    methodology_version: Mapped[str] = mapped_column(
        ForeignKey("methodology_versions.version"), primary_key=True
    )
    series_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    month: Mapped[str] = mapped_column(String(7), primary_key=True)
    essentials: Mapped[int] = mapped_column(Integer)
