"""Seasonal Agro Swaps page (contract v0.4 §11.2, MISSING_APIS.pdf pages 10-11)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.agro import AgroSavingsProjectionRequest, AgroSavingsProjectionResponse
from app.schemas.common import NoQuery
from app.services.agro_service import AgroService, get_agro_service

router = APIRouter(tags=["citizen"])
Service = Annotated[AgroService, Depends(get_agro_service)]


@router.post(
    "/calculations/agro-savings-projection",
    summary="Project monthly savings from an illustrative meal swap (BR-14, BR-20); stores nothing",
    responses=problem_responses(400, 404, 422),
)
def agro_savings_projection(
    body: AgroSavingsProjectionRequest,
    _: Annotated[NoQuery, Query()],
    service: Service,
) -> AgroSavingsProjectionResponse:
    return service.project(body)
