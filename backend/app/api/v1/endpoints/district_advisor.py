"""District Budget Advisor (contract v0.4 §11.3, MISSING_APIS.pdf pages 7-8)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.v1.responses import problem_responses
from app.schemas.common import NoQuery
from app.schemas.district_advisor import (
    BasketDetailsResponse,
    DistrictComparisonQuery,
    DistrictComparisonResponse,
    StressTestRequest,
    StressTestResponse,
)
from app.services.district_advisor_service import (
    DistrictAdvisorService,
    get_district_advisor_service,
)

router = APIRouter(tags=["citizen"])
Service = Annotated[DistrictAdvisorService, Depends(get_district_advisor_service)]


@router.post(
    "/calculations/stress-test",
    summary="Apply an illustrative price shock to a district basket (BR-21, BR-22, BR-24)",
    responses=problem_responses(400, 404, 422),
)
def stress_test(
    body: StressTestRequest, _: Annotated[NoQuery, Query()], service: Service
) -> StressTestResponse:
    return service.stress_test(body)


@router.get(
    "/calculations/district-comparison",
    summary="Compare the illustrative baskets of two districts (BR-23, BR-24)",
    responses=problem_responses(400, 404, 422),
)
def district_comparison(
    query: Annotated[DistrictComparisonQuery, Query()], service: Service
) -> DistrictComparisonResponse:
    return service.compare(query)


@router.get(
    "/districts/{code}/basket-details",
    summary="The basket drawer for a district: rent and transit lines; staple prices and "
    "market hub where the MISSING_APIS.pdf example gives them (Gasabo), else null",
    responses=problem_responses(400, 404),
)
def basket_details(
    code: Annotated[str, Path(max_length=64)],
    _: Annotated[NoQuery, Query()],
    service: Service,
) -> BasketDetailsResponse:
    return service.basket_details(code)
