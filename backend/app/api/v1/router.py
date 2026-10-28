"""The v1 router. It carries no prefix of its own: `app.api.router` mounts it once at `/api/v1`."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    agro,
    auth,
    benchmarks,
    budget,
    dashboard,
    district_advisor,
    nisr,
    policy_scenarios,
    profile,
    resilience,
    seasonal_swaps,
    shocks,
    tracker,
    vulnerability,
)

router = APIRouter()
for module in (
    benchmarks,
    budget,
    shocks,
    resilience,
    seasonal_swaps,
    agro,
    district_advisor,
    vulnerability,
    policy_scenarios,
    dashboard,
    nisr,
    auth,
    profile,
    tracker,
):
    router.include_router(module.router)
