"""Household accounts (contract §11.8, MISSING_APIS.pdf page 4)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.schemas.common import NoQuery
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["accounts"])
Service = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    status_code=201,
    summary="Register a household account and get a bearer token (stores the account)",
    responses=problem_responses(400, 404, 409, 422, 503),
)
def register(
    body: RegisterRequest, _: Annotated[NoQuery, Query()], service: Service
) -> RegisterResponse:
    return service.register(body)


@router.post(
    "/login",
    summary="Log in with a phone number or email and password; get a bearer token",
    responses=problem_responses(400, 401, 422, 503),
)
def login(body: LoginRequest, _: Annotated[NoQuery, Query()], service: Service) -> LoginResponse:
    return service.login(body)
