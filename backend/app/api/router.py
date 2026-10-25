"""Central routing: health checks at the root, every data route under `/api/v1` exactly once."""

from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.router import router as v1_router
from app.core.constants import API_PREFIX

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(v1_router, prefix=API_PREFIX)
