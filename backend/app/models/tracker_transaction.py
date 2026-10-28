"""Daily tracker transactions (contract §11.10, MISSING_APIS.pdf pages 5-6).

One row per expense or income a household logs. Rows belong to one account and go with it
(ON DELETE CASCADE). The database enforces what the API validates, so no other writer can store
an inconsistent row: the type/category pairs, positive amounts within the money bound, non-blank
titles and the idempotency pair. Stored since 2026-10-28 at the project owner's direction: a
further Q-02 change (citizen data on the server), not a privacy-policy approval (Q-13 open).
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EXPENSE_CATEGORIES = ("food", "transport", "utilities", "other")
INCOME_CATEGORIES = ("mobile_money", "day_wage", "market_sales", "side_gig")


def _quoted(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


class TrackerTransaction(Base):
    __tablename__ = "tracker_transactions"
    __table_args__ = (
        CheckConstraint("id ~ '^tx_[0-9A-HJKMNP-TV-Z]{26}$'", name="id_format"),
        CheckConstraint("type IN ('expense', 'income')", name="type_known"),
        CheckConstraint(
            f"(type = 'expense' AND category IN ({_quoted(EXPENSE_CATEGORIES)}))"
            f" OR (type = 'income' AND category IN ({_quoted(INCOME_CATEGORIES)}))",
            name="category_matches_type",
        ),
        CheckConstraint("amount BETWEEN 1 AND 100000000", name="amount_range"),
        CheckConstraint("length(btrim(title)) BETWEEN 1 AND 120", name="title_length"),
        CheckConstraint("note IS NULL OR length(note) <= 280", name="note_length"),
        CheckConstraint(
            "(idempotency_key IS NULL) = (request_hash IS NULL)", name="idempotency_complete"
        ),
        UniqueConstraint("account_id", "idempotency_key"),
        # Every read is one account's rows in a time range, in (time, id) order.
        Index(None, "account_id", "occurred_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(30), primary_key=True)  # "tx_" + a ULID
    account_id: Mapped[str] = mapped_column(ForeignKey("household_accounts.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(7))
    category: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(String(280))
    amount: Mapped[int] = mapped_column(Integer)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # the API's `date`
    # Idempotency-Key of the POST that created the row, and a hash of its body (§11.10).
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    request_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
