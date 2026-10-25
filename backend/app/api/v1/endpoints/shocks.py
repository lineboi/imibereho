"""Household shock calculation (contract §4)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.common import NoQuery
from app.schemas.shock import HouseholdShockRequest, HouseholdShockResponse
from app.services.shock_service import ShockService, get_shock_service

router = APIRouter(tags=["citizen"])


@router.post(
    "/calculations/household-shock",
    summary="Simulate an income shock for one household (BR-01 to BR-06); nothing is stored",
    responses=problem_responses(400, 422),
)
def household_shock(
    body: HouseholdShockRequest,
    _: Annotated[NoQuery, Query()],
    service: Annotated[ShockService, Depends(get_shock_service)],
) -> HouseholdShockResponse:
    return service.household_shock(body)
