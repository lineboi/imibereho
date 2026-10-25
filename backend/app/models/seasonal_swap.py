"""Illustrative seasonal food swaps and tips for C5 (contract §4)."""

from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
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


class SeasonalSwap(Base):
    """`district_code` NULL means the swap applies to every district ([PD] Q-32)."""

    __tablename__ = "seasonal_swaps"
    __table_args__ = (
        CheckConstraint("month BETWEEN 1 AND 12", name="month_range"),
        CheckConstraint("from_quantity > 0", name="from_quantity_positive"),
        CheckConstraint("to_quantity > 0", name="to_quantity_positive"),
        CheckConstraint("from_price >= 0", name="from_price_non_negative"),
        CheckConstraint("to_price >= 0", name="to_price_non_negative"),
        Index("ix_seasonal_swaps_month_district_code", "month", "district_code"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    methodology_version: Mapped[str] = mapped_column(ForeignKey("methodology_versions.version"))
    district_code: Mapped[str | None] = mapped_column(ForeignKey("districts.code"))
    month: Mapped[int] = mapped_column(SmallInteger)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    footnote: Mapped[str] = mapped_column(Text)
    from_name: Mapped[str] = mapped_column(String(64))
    from_quantity: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    from_unit: Mapped[str] = mapped_column(String(16))
    from_price: Mapped[int] = mapped_column(Integer)
    to_name: Mapped[str] = mapped_column(String(64))
    to_quantity: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    to_unit: Mapped[str] = mapped_column(String(16))
    to_price: Mapped[int] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(SmallInteger)


class SeasonalTip(Base):
    """`district_code` / `month` NULL means the tip applies to every district / month."""

    __tablename__ = "seasonal_tips"
    __table_args__ = (CheckConstraint("month BETWEEN 1 AND 12", name="month_range"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    methodology_version: Mapped[str] = mapped_column(ForeignKey("methodology_versions.version"))
    district_code: Mapped[str | None] = mapped_column(ForeignKey("districts.code"))
    month: Mapped[int | None] = mapped_column(SmallInteger)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger)
