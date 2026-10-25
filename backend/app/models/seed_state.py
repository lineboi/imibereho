"""Operational seed state: which seed datasets are loaded, at which content hash (plan A3)."""

from datetime import datetime

from sqlalchemy import CHAR, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SeedState(Base):
    __tablename__ = "seed_state"

    dataset: Mapped[str] = mapped_column(String(64), primary_key=True)
    methodology_version: Mapped[str] = mapped_column(String(16))
    content_hash: Mapped[str] = mapped_column(CHAR(64))
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
