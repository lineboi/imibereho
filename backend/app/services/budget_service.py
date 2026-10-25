"""Optional `POST /calculations/budget-comparison` (contract §6, BR-13, [PD] Q-09).

Each of the 5 categories must appear exactly once. Contract §6 does not name the error codes for
a missing or duplicated category; this implementation reports a missing category as `required`
at `plan` and a duplicate or unknown one as `unknown_value` at `plan.<i>.categoryCode`. That
choice is recorded as an open item for the frontend sign-off.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import ComparisonLine, budget_comparison
from app.core.constants import METHODOLOGY_VERSION
from app.core.errors import FieldError, RequestValidationProblem
from app.db.session import get_read_session
from app.repositories.benchmark_repository import BenchmarkRepository
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.budget import (
    BudgetComparisonRequest,
    BudgetComparisonResponse,
    ComparisonLineOut,
    ComparisonTotals,
    LargestDifference,
)
from app.schemas.common import Meta
from app.services.benchmark_service import BenchmarkService, require_district


def _largest(line: ComparisonLine | None) -> LargestDifference | None:
    if line is None:
        return None
    return LargestDifference(category_code=line.category_code, difference=line.difference)


class BudgetService:
    def __init__(self, reference: ReferenceDataRepository, benchmarks: BenchmarkService) -> None:
        self._reference = reference
        self._benchmarks = benchmarks

    def _validate_plan(self, request: BudgetComparisonRequest, order: list[str]) -> None:
        errors: list[FieldError] = []
        seen: set[str] = set()
        for index, line in enumerate(request.plan):
            if line.category_code not in order or line.category_code in seen:
                errors.append(
                    FieldError(
                        f"plan.{index}.categoryCode",
                        "unknown_value",
                        "Each category must be a known code and appear once.",
                    )
                )
            seen.add(line.category_code)
        missing = [code for code in order if code not in seen]
        if missing:
            errors.append(
                FieldError("plan", "required", f"Missing categories: {', '.join(missing)}.")
            )
        if errors:
            raise RequestValidationProblem(errors)

    def compare(self, request: BudgetComparisonRequest) -> BudgetComparisonResponse:
        order = [category.code for category in self._reference.list_categories()]
        self._validate_plan(request, order)  # validation before lookup (contract §1.3)
        district = require_district(self._reference, request.district)
        reference = self._benchmarks.reference_amounts(district.code, request.household_size)
        plan = {line.category_code: line.planned_amount for line in request.plan}
        result = budget_comparison(order, plan, reference)

        return BudgetComparisonResponse(
            lines=[
                ComparisonLineOut(
                    category_code=line.category_code,
                    planned=line.planned,
                    reference=line.reference,
                    difference=line.difference,
                )
                for line in result.lines
            ],
            totals=ComparisonTotals(
                planned=result.planned_total,
                reference=result.reference_total,
                difference=result.planned_total - result.reference_total,
            ),
            largest_above=_largest(result.largest_above),
            largest_below=_largest(result.largest_below),
            meta=Meta(),
        )


def get_budget_service(session: Annotated[Session, Depends(get_read_session)]) -> BudgetService:
    reference = ReferenceDataRepository(session, METHODOLOGY_VERSION)
    return BudgetService(
        reference,
        BenchmarkService(reference, BenchmarkRepository(session, METHODOLOGY_VERSION)),
    )
