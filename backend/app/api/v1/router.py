"""The v1 router. It carries no prefix of its own: `app.api.router` mounts it once at `/api/v1`."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    benchmarks,
    budget,
    dashboard,
    policy_scenarios,
    seasonal_swaps,
    shocks,
    vulnerability,
)

router = APIRouter()
for module in (
    benchmarks,
    budget,
    shocks,
    seasonal_swaps,
    vulnerability,
    policy_scenarios,
    dashboard,
):
    router.include_router(module.router)
