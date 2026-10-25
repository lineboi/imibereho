"""Policy scenario calculation (contract §5)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.common import NoQuery
from app.schemas.policy_scenario import PolicyScenarioRequest, PolicyScenarioResponse
from app.services.policy_scenario_service import (
    PolicyScenarioService,
    get_policy_scenario_service,
)

router = APIRouter(tags=["decision-maker"])


@router.post(
    "/calculations/policy-scenario",
    summary="Compare no shock, shock only and shock with cash support; nothing is stored",
    responses=problem_responses(400, 422),
)
def policy_scenario(
    body: PolicyScenarioRequest,
    _: Annotated[NoQuery, Query()],
    service: Annotated[PolicyScenarioService, Depends(get_policy_scenario_service)],
) -> PolicyScenarioResponse:
    return service.simulate(body)
