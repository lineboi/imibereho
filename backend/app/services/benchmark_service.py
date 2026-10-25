"""Reference data (contract §3) and budget benchmarks (contract §4)."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.constants import METHODOLOGY_VERSION
from app.core.errors import BenchmarkNotAvailableError, DistrictNotFoundError
from app.db.session import get_read_session
from app.models import District
from app.repositories.benchmark_repository import BenchmarkRepository
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.benchmark import (
    BenchmarkLine,
    BudgetBenchmarkResponse,
    DistrictItem,
    DistrictList,
    DistrictRef,
    ExpenseCategoryItem,
    ExpenseCategoryList,
)
from app.schemas.common import ListMeta, Meta


def require_district(reference: ReferenceDataRepository, code: str) -> District:
    """404 `district-not-found` for an unknown code. Codes are case-sensitive (contract §5)."""
    district = reference.get_district(code)
    if district is None:
        raise DistrictNotFoundError
    return district


class BenchmarkService:
    def __init__(self, reference: ReferenceDataRepository, benchmarks: BenchmarkRepository) -> None:
        self._reference = reference
        self._benchmarks = benchmarks

    def list_districts(self) -> DistrictList:
        items = [
            DistrictItem(code=d.code, name=d.name, province=d.province)
            for d in self._reference.list_districts()
        ]
        return DistrictList(items=items, meta=ListMeta(count=len(items)))

    def list_categories(self) -> ExpenseCategoryList:
        items = [
            ExpenseCategoryItem(code=c.code, name=c.name_en, icon=c.icon)
            for c in self._reference.list_categories()
        ]
        return ExpenseCategoryList(items=items, meta=ListMeta(count=len(items)))

    def reference_amounts(self, district_code: str, household_size: int) -> dict[str, int]:
        """Category → monthly amount, or 404 `benchmark-not-available`. Assumes a known district."""
        lines = self._benchmarks.list_lines(district_code, household_size)
        if not lines:
            raise BenchmarkNotAvailableError
        return {line.category_code: line.monthly_amount for line in lines}

    def get_benchmark(self, district_code: str, household_size: int) -> BudgetBenchmarkResponse:
        district = require_district(self._reference, district_code)
        amounts = self.reference_amounts(district.code, household_size)
        return BudgetBenchmarkResponse(
            district=DistrictRef(code=district.code, name=district.name),
            household_size=household_size,
            lines=[
                BenchmarkLine(category_code=code, monthly_amount=amount)
                for code, amount in amounts.items()
            ],
            total=sum(amounts.values()),
            meta=Meta(),
        )


def get_benchmark_service(
    session: Annotated[Session, Depends(get_read_session)],
) -> BenchmarkService:
    return BenchmarkService(
        ReferenceDataRepository(session, METHODOLOGY_VERSION),
        BenchmarkRepository(session, METHODOLOGY_VERSION),
    )
