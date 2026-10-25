"""Seasonal food swaps (contract §4)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.seasonal_swap import SeasonalSwapQuery, SeasonalSwapResponse
from app.services.seasonal_swap_service import SeasonalSwapService, get_seasonal_swap_service

router = APIRouter(tags=["citizen"])


@router.get(
    "/seasonal-swaps",
    summary="Illustrative food swaps and tips for a district and month",
    responses=problem_responses(400, 404, 422),
)
def list_seasonal_swaps(
    query: Annotated[SeasonalSwapQuery, Query()],
    service: Annotated[SeasonalSwapService, Depends(get_seasonal_swap_service)],
) -> SeasonalSwapResponse:
    return service.list_swaps(query.district, query.month)
