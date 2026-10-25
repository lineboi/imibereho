"""Liveness and readiness (contract §2). Mounted at the root, outside `/api/v1`. No `meta`."""

from collections.abc import Callable
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from starlette.responses import Response

from app.api.v1.responses import problem_responses
from app.core.errors import problem_response
from app.db.readiness import Readiness
from app.schemas.common import NoQuery

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadyChecks(BaseModel):
    database: Literal["ok", "failed"]
    migrations: Literal["ok", "failed"]
    seed: Literal["ok", "failed"]


class ReadyResponse(BaseModel):
    status: Literal["ready"]
    checks: ReadyChecks


@router.get("/health", summary="Liveness: the process is serving HTTP. Never touches the database")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    summary="Readiness: database, migrations and seed data are correct for this build",
    response_model=ReadyResponse,
    responses={
        503: {"description": "Not ready (`not-ready`), with a `checks` member"},
        **problem_responses(400),
    },
)
def ready(request: Request, _: Annotated[NoQuery, Query()]) -> Response | ReadyResponse:
    check: Callable[[], Readiness] = request.app.state.readiness
    result = check()
    if not result.ready:
        return problem_response(
            "not-ready",
            "Not ready",
            503,
            "The service cannot serve correct data yet.",
            checks=result.as_checks(),
        )
    return ReadyResponse(status="ready", checks=ReadyChecks(**result.as_checks()))  # type: ignore[arg-type]
