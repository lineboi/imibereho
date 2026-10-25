"""Synthetic household profiles only.

Citizen profiles, plans and expenses stay on the user's device (Q-02, Option A) and have no
table. These two tables hold invented, illustrative data under a methodology version:
- `ReferenceHousehold`: the design's demo household (Gasabo, 4 people, 180,000 / 150,000 /
  60,000 RWF; [E] `2:6430`, `2:6440`, `2:6628`, `2:7209`).
- `SyntheticHousehold`: the 3,000-household sample behind the D1 KPIs ([SYN], plan F6).
Neither has a name, contact, location finer than a district, or any identifier of a person.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReferenceHousehold(Base):
    __tablename__ = "reference_households"
    __table_args__ = (
        CheckConstraint("household_size BETWEEN 1 AND 20", name="household_size_range"),
        CheckConstraint("monthly_income >= 0", name="monthly_income_non_negative"),
        CheckConstraint("monthly_essentials >= 0", name="monthly_essentials_non_negative"),
        CheckConstraint("savings >= 0", name="savings_non_negative"),
    )

    methodology_version: Mapped[str] = mapped_column(
        ForeignKey("methodology_versions.version"), primary_key=True
    )
    district_code: Mapped[str] = mapped_column(ForeignKey("districts.code"))
    household_size: Mapped[int] = mapped_column(SmallInteger)
    monthly_income: Mapped[int] = mapped_column(Integer)
    monthly_essentials: Mapped[int] = mapped_column(Integer)
    savings: Mapped[int] = mapped_column(Integer)


class SyntheticHousehold(Base):
    __tablename__ = "synthetic_households"
    __table_args__ = (
        CheckConstraint("household_size BETWEEN 1 AND 20", name="household_size_range"),
        CheckConstraint(
            "primary_income_source IN ('wage', 'agriculture', 'informal_enterprise')",
            name="primary_income_source_known",
        ),
        CheckConstraint("monthly_income >= 0", name="monthly_income_non_negative"),
        CheckConstraint("monthly_essentials >= 0", name="monthly_essentials_non_negative"),
        CheckConstraint("savings >= 0", name="savings_non_negative"),
        Index("ix_synthetic_households_methodology_version", "methodology_version"),
        Index("ix_synthetic_households_district_code", "district_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    methodology_version: Mapped[str] = mapped_column(ForeignKey("methodology_versions.version"))
    district_code: Mapped[str] = mapped_column(ForeignKey("districts.code"))
    household_size: Mapped[int] = mapped_column(SmallInteger)
    primary_income_source: Mapped[str] = mapped_column(String(32))
    monthly_income: Mapped[int] = mapped_column(Integer)
    monthly_essentials: Mapped[int] = mapped_column(Integer)
    savings: Mapped[int] = mapped_column(Integer)
