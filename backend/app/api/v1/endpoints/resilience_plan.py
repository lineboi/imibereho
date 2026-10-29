"""The household's saved resilience plan (contract §11.11, MISSING_APIS.pdf inventory item 17).

Every route needs `Authorization: Bearer <token>` and works only on that household's plan. The
PDF names only `POST`; `GET` reads the plan back and `DELETE` removes it.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.v1.responses import problem_responses
from app.schemas.common import NoQuery
from app.schemas.resilience import ResilienceSimulationRequest
from app.schemas.resilience_plan import ResiliencePlanResponse
from app.services.current_account import CurrentAccountDep
from app.services.resilience_plan_service import (
    ResiliencePlanService,
    get_plan_reader,
    get_plan_writer,
)

router = APIRouter(prefix="/user", tags=["accounts"])
Reader = Annotated[ResiliencePlanService, Depends(get_plan_reader)]
Writer = Annotated[ResiliencePlanService, Depends(get_plan_writer)]


@router.post(
    "/resilience-plan",
    status_code=status.HTTP_201_CREATED,
    summary="Save the household's resilience plan, replacing any earlier one (bearer token)",
    responses={
        200: {"description": "The plan replaced the household's earlier plan"},
        201: {"description": "The household's first saved plan"},
        **problem_responses(400, 401, 422, 503),
    },
)
def save_resilience_plan(
    account: CurrentAccountDep,
    body: ResilienceSimulationRequest,
    _: Annotated[NoQuery, Query()],
    service: Writer,
    response: Response,
) -> ResiliencePlanResponse:
    plan, created = service.save(account, body)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return plan


@router.get(
    "/resilience-plan",
    summary="The household's saved resilience plan, with its simulation (bearer token)",
    responses=problem_responses(400, 401, 404, 503),
)
def get_resilience_plan(
    account: CurrentAccountDep, _: Annotated[NoQuery, Query()], service: Reader
) -> ResiliencePlanResponse:
    return service.get(account)


@router.delete(
    "/resilience-plan",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete the household's saved resilience plan (bearer token)",
    responses=problem_responses(400, 401, 404, 503),
)
def delete_resilience_plan(
    account: CurrentAccountDep, _: Annotated[NoQuery, Query()], service: Writer
) -> Response:
    service.delete(account)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
