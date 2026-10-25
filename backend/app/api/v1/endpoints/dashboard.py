"""Decision-maker dashboard filters and overview (contract §5)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.common import NoQuery
from app.schemas.dashboard import DashboardFiltersResponse, DashboardOverviewResponse, OverviewQuery
from app.services.dashboard_service import DashboardService, get_dashboard_service

router = APIRouter(prefix="/dashboard", tags=["decision-maker"])
Service = Annotated[DashboardService, Depends(get_dashboard_service)]


@router.get(
    "/filters",
    summary="Filter options for the workspace views",
    responses=problem_responses(400),
)
def dashboard_filters(_: Annotated[NoQuery, Query()], service: Service) -> DashboardFiltersResponse:
    return service.filters()


@router.get(
    "/overview",
    summary="D1 KPIs, essentials trend, income sources and top districts",
    responses=problem_responses(400, 422),
)
def dashboard_overview(
    query: Annotated[OverviewQuery, Query()], service: Service
) -> DashboardOverviewResponse:
    return service.overview(query)
