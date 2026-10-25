"""Reference data (contract §3) and budget benchmarks (contract §4)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.benchmark import (
    BenchmarkQuery,
    BudgetBenchmarkResponse,
    DistrictList,
    ExpenseCategoryList,
)
from app.schemas.common import NoQuery
from app.services.benchmark_service import BenchmarkService, get_benchmark_service

router = APIRouter(tags=["reference data"])
Service = Annotated[BenchmarkService, Depends(get_benchmark_service)]


@router.get(
    "/districts",
    summary="List the 30 districts alphabetically",
    responses=problem_responses(400),
)
def list_districts(_: Annotated[NoQuery, Query()], service: Service) -> DistrictList:
    return service.list_districts()


@router.get(
    "/expense-categories",
    summary="List the five expense categories",
    responses=problem_responses(400),
)
def list_expense_categories(
    _: Annotated[NoQuery, Query()], service: Service
) -> ExpenseCategoryList:
    return service.list_categories()


@router.get(
    "/budget-benchmarks",
    summary="Illustrative budget benchmark for a district and household size",
    responses=problem_responses(400, 404, 422),
)
def get_budget_benchmark(
    query: Annotated[BenchmarkQuery, Query()], service: Service
) -> BudgetBenchmarkResponse:
    return service.get_benchmark(query.district, query.householdSize)
