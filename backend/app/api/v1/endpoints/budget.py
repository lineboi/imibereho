"""Optional budget comparison (contract §6)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.budget import BudgetComparisonRequest, BudgetComparisonResponse
from app.schemas.common import NoQuery
from app.services.budget_service import BudgetService, get_budget_service

router = APIRouter(tags=["citizen"])


@router.post(
    "/calculations/budget-comparison",
    summary="Compare a household plan with the illustrative benchmark (BR-13)",
    responses=problem_responses(400, 404, 422),
)
def budget_comparison(
    body: BudgetComparisonRequest,
    _: Annotated[NoQuery, Query()],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> BudgetComparisonResponse:
    return service.compare(body)
