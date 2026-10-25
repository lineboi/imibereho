"""Aggregate queries over the synthetic sample under an income shock (BR-12).

The deficit count is the only aggregate computed in SQL. Its predicate is
`app.calculations.DEFICIT_PREDICATE_SQL`, the integer half-up BR-02 expression shared with
Python's `is_in_deficit`. Ratios are never computed in SQL.
"""

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.calculations import DEFICIT_PREDICATE_SQL
from app.models import SyntheticHousehold


class ShockRepository:
    def __init__(self, session: Session, methodology_version: str) -> None:
        self._session = session
        self._version = methodology_version

    def sample_size(self) -> int:
        return (
            self._session.scalar(
                select(func.count())
                .select_from(SyntheticHousehold)
                .where(SyntheticHousehold.methodology_version == self._version)
            )
            or 0
        )

    def households_in_deficit(self, reduction_pct: int) -> int:
        return (
            self._session.scalar(
                select(func.count())
                .select_from(SyntheticHousehold)
                .where(
                    SyntheticHousehold.methodology_version == self._version,
                    text(DEFICIT_PREDICATE_SQL).bindparams(pct=reduction_pct),
                )
            )
            or 0
        )

    def households_by_income_source(self) -> dict[str, int]:
        rows = self._session.execute(
            select(SyntheticHousehold.primary_income_source, func.count())
            .where(SyntheticHousehold.methodology_version == self._version)
            .group_by(SyntheticHousehold.primary_income_source)
        ).all()
        return {source: count for source, count in rows}
