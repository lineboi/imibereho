"""Shock catalogue and resilience simulation (contract v0.4 §11.1, MISSING_APIS.pdf page 9)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.common import NoQuery
from app.schemas.resilience import (
    ResilienceSimulationRequest,
    ResilienceSimulationResponse,
    ShockCatalog,
)
from app.services.resilience_service import ResilienceService, get_resilience_service

router = APIRouter(tags=["citizen"])
Service = Annotated[ResilienceService, Depends(get_resilience_service)]


@router.get(
    "/shocks/catalog",
    summary="Illustrative shock options and coping levers for the resilience simulator",
    responses=problem_responses(400),
)
def shock_catalog(_: Annotated[NoQuery, Query()], service: Service) -> ShockCatalog:
    return service.catalog()


@router.post(
    "/calculations/resilience-simulation",
    summary="Simulate a shock with coping levers (BR-02 to BR-06, BR-17 to BR-19); stores nothing",
    responses=problem_responses(400, 422),
)
def resilience_simulation(
    body: ResilienceSimulationRequest,
    _: Annotated[NoQuery, Query()],
    service: Service,
) -> ResilienceSimulationResponse:
    return service.simulate(body)
