"""Household accounts for `POST /auth/register` and `POST /auth/login` (contract §11.8).

The only table holding data a person sends. It was added on 2026-10-28 at the project owner's
direction: a Q-02 change for this table only (citizen accounts, Option C; Q-02 otherwise keeps
nothing a person sends). Q-04, decision-maker login, is unchanged. Retention, deletion and
consent (Q-13) are open. It keeps
the minimum the PDF's register request carries: the login identifier, an Argon2id hash of the
password (never the password), and the profile fields; since migration 0010 also the planned
essentials and savings buffer that PATCH /user/profile sets (contract §11.9). No name and nothing
finer than a district.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HouseholdAccount(Base):
    __tablename__ = "household_accounts"
    __table_args__ = (
        CheckConstraint("id ~ '^usr_[0-9A-HJKMNP-TV-Z]{26}$'", name="id_format"),
        CheckConstraint("household_size BETWEEN 1 AND 20", name="household_size_range"),
        CheckConstraint("monthly_income BETWEEN 0 AND 100000000", name="monthly_income_range"),
        CheckConstraint("currency = 'RWF'", name="currency_known"),
        CheckConstraint("preferred_language IN ('EN', 'RW')", name="preferred_language_known"),
        CheckConstraint(
            "planned_essentials IS NULL OR planned_essentials BETWEEN 0 AND 100000000",
            name="planned_essentials_range",
        ),
        CheckConstraint(
            "savings_buffer IS NULL OR savings_buffer BETWEEN 0 AND 100000000",
            name="savings_buffer_range",
        ),
        CheckConstraint("role IN ('citizen', 'decision_maker')", name="role_known"),
    )

    id: Mapped[str] = mapped_column(String(30), primary_key=True)  # "usr_" + a ULID
    # Normalised (an email is lower-cased; a phone number is +2507XXXXXXXX), so unique as is.
    identifier: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    district_code: Mapped[str] = mapped_column(ForeignKey("districts.code"))
    household_size: Mapped[int] = mapped_column(SmallInteger)
    monthly_income: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    preferred_language: Mapped[str] = mapped_column(String(2))
    role: Mapped[str] = mapped_column(String(32), default="citizen", server_default="citizen")
    # Profile values register does not collect (contract §11.9): NULL until the household sets
    # them with PATCH /user/profile, never a default 0.
    planned_essentials: Mapped[int | None] = mapped_column(Integer)
    savings_buffer: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
