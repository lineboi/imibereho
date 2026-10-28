"""The household's saved resilience plan (contract §11.11, `POST /user/resilience-plan`).

One plan per account: the inputs of a resilience simulation (baseline, shock, coping levers),
saved again over the old one. The result is not stored; it is recomputed from these inputs on
every read (`ResilienceService.simulate`), so it can never disagree with them. The database
enforces what the API validates. Rows go with their account (ON DELETE CASCADE). Stored since
2026-10-28 at the project owner's direction: a further Q-02 change (citizen data on the server),
not a privacy-policy approval (Q-13 open).
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

SHOCK_TYPES = ("income_drop", "medical_emergency", "school_fees", "harvest_disruption")
LUMP_SUM_SHOCKS = ("medical_emergency", "school_fees")
COPING_LEVERS = ("trim_non_essentials", "seasonal_agro_swaps", "ibimina_tontine")


def _quoted(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


class ResiliencePlan(Base):
    __tablename__ = "resilience_plans"
    __table_args__ = (
        CheckConstraint("monthly_income BETWEEN 0 AND 100000000", name="monthly_income_range"),
        CheckConstraint(
            "monthly_essentials BETWEEN 0 AND 100000000", name="monthly_essentials_range"
        ),
        CheckConstraint("savings BETWEEN 0 AND 100000000", name="savings_range"),
        CheckConstraint(f"shock_type IN ({_quoted(SHOCK_TYPES)})", name="shock_type_known"),
        CheckConstraint("duration_months BETWEEN 1 AND 24", name="duration_months_range"),
        # A lump-sum shock has an optional amount and no reduction; an income shock the reverse.
        CheckConstraint(
            f"(shock_type IN ({_quoted(LUMP_SUM_SHOCKS)}) AND income_reduction_pct IS NULL"
            " AND (shock_amount IS NULL OR shock_amount BETWEEN 0 AND 100000000))"
            f" OR (shock_type NOT IN ({_quoted(LUMP_SUM_SHOCKS)}) AND shock_amount IS NULL"
            " AND income_reduction_pct IS NOT NULL AND income_reduction_pct BETWEEN 0 AND 100)",
            name="shock_fields_match_type",
        ),
        # Known levers (no NULL: NULL is never contained), each at most once, in the household's
        # order. A CHECK cannot hold a subquery, so uniqueness is pairwise over the 3 levers.
        CheckConstraint(
            f"coping_levers <@ ARRAY[{_quoted(COPING_LEVERS)}]::varchar[]"
            " AND cardinality(coping_levers) <= 3"
            " AND (cardinality(coping_levers) < 2 OR coping_levers[1] <> coping_levers[2])"
            " AND (cardinality(coping_levers) < 3 OR (coping_levers[1] <> coping_levers[3]"
            " AND coping_levers[2] <> coping_levers[3]))",
            name="coping_levers_known_and_unique",
        ),
    )

    account_id: Mapped[str] = mapped_column(
        ForeignKey("household_accounts.id", ondelete="CASCADE"), primary_key=True
    )
    monthly_income: Mapped[int] = mapped_column(Integer)
    monthly_essentials: Mapped[int] = mapped_column(Integer)
    savings: Mapped[int] = mapped_column(Integer)
    shock_type: Mapped[str] = mapped_column(String(24))
    income_reduction_pct: Mapped[int | None] = mapped_column(SmallInteger)
    duration_months: Mapped[int] = mapped_column(SmallInteger)
    shock_amount: Mapped[int | None] = mapped_column(Integer)
    coping_levers: Mapped[list[str]] = mapped_column(ARRAY(String(32)))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
