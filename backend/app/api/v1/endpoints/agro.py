"""Seasonal Agro Swaps page (contract v0.4 §11.2 and §11.5, MISSING_APIS.pdf pages 10-11)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.agro import (
    AgroSavingsProjectionRequest,
    AgroSavingsProjectionResponse,
    BalancedPlateResponse,
    HarvestCalendarResponse,
    ShoppingChecklistQuery,
    ShoppingChecklistResponse,
)
from app.schemas.common import NoQuery
from app.services.agro_service import AgroService, get_agro_service
from app.services.harvest_calendar_service import (
    HarvestCalendarService,
    get_harvest_calendar_service,
)

router = APIRouter(tags=["citizen"])
Service = Annotated[AgroService, Depends(get_agro_service)]


@router.post(
    "/calculations/agro-savings-projection",
    summary="Project monthly savings from an illustrative meal swap and what they could buy "
    "(BR-14, BR-20, BR-25; PDF example unit costs); stores nothing",
    responses=problem_responses(400, 404, 422),
)
def agro_savings_projection(
    body: AgroSavingsProjectionRequest,
    _: Annotated[NoQuery, Query()],
    service: Service,
) -> AgroSavingsProjectionResponse:
    return service.project(body)


@router.get(
    "/nutrition/indyo-yuzuye",
    summary="Indyo Yuzuye balanced plate: the MISSING_APIS.pdf example (illustrative, not "
    "official guidance)",
    responses=problem_responses(400),
)
def balanced_plate(_: Annotated[NoQuery, Query()], service: Service) -> BalancedPlateResponse:
    return service.balanced_plate()


@router.get(
    "/agro/harvest-calendar",
    summary="Rwanda's crop-season calendar and the active season's main crops (NISR SAS 2025)",
    responses=problem_responses(400),
)
def harvest_calendar(
    _: Annotated[NoQuery, Query()],
    service: Annotated[HarvestCalendarService, Depends(get_harvest_calendar_service)],
) -> HarvestCalendarResponse:
    return service.calendar()


@router.get(
    "/market/shopping-checklist",
    summary="Shopping checklist: the MISSING_APIS.pdf example for Gasabo (illustrative; "
    "sizes other than 4 modelled by BR-24); other districts are awaiting_validated_data",
    responses=problem_responses(400, 404, 422),
)
def shopping_checklist(
    query: Annotated[ShoppingChecklistQuery, Query()], service: Service
) -> ShoppingChecklistResponse:
    return service.shopping_checklist(query)
