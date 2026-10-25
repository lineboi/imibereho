"""Illustrative budget benchmarks for C3 (contract §4, [PD] Q-32)."""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BudgetBenchmark(Base):
    __tablename__ = "budget_benchmarks"
    __table_args__ = (
        CheckConstraint("household_size BETWEEN 1 AND 20", name="household_size_range"),
        CheckConstraint("monthly_amount >= 0", name="monthly_amount_non_negative"),
    )

    methodology_version: Mapped[str] = mapped_column(
        ForeignKey("methodology_versions.version"), primary_key=True
    )
    district_code: Mapped[str] = mapped_column(ForeignKey("districts.code"), primary_key=True)
    household_size: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    category_code: Mapped[str] = mapped_column(
        ForeignKey("expense_categories.code"), primary_key=True
    )
    monthly_amount: Mapped[int] = mapped_column(Integer)
