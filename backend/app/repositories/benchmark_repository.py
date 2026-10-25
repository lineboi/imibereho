"""Read-only budget benchmark queries."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BudgetBenchmark, ExpenseCategory


class BenchmarkRepository:
    def __init__(self, session: Session, methodology_version: str) -> None:
        self._session = session
        self._version = methodology_version

    def list_lines(self, district_code: str, household_size: int) -> Sequence[BudgetBenchmark]:
        """Benchmark lines in category order; empty when no benchmark exists."""
        return self._session.scalars(
            select(BudgetBenchmark)
            .join(ExpenseCategory, ExpenseCategory.code == BudgetBenchmark.category_code)
            .where(
                BudgetBenchmark.methodology_version == self._version,
                BudgetBenchmark.district_code == district_code,
                BudgetBenchmark.household_size == household_size,
            )
            .order_by(ExpenseCategory.sort_order)
        ).all()
