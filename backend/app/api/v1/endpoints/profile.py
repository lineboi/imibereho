"""Household profile (contract §11.9, MISSING_APIS.pdf page 4).

Both routes need `Authorization: Bearer <token>` from register or login. The PDF names the update
`PUT`; at the project owner's direction it is `PATCH` (a partial update), and `PUT` is not routed.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.common import NoQuery
from app.schemas.profile import ProfilePatch, ProfileResponse
from app.services.current_account import CurrentAccountDep
from app.services.profile_service import ProfileService, get_profile_service, profile_of

router = APIRouter(prefix="/user", tags=["accounts"])
Service = Annotated[ProfileService, Depends(get_profile_service)]


@router.get(
    "/profile",
    summary="The logged-in household's profile (needs a bearer token)",
    responses=problem_responses(400, 401, 503),
)
def get_profile(account: CurrentAccountDep, _: Annotated[NoQuery, Query()]) -> ProfileResponse:
    return profile_of(account)


@router.patch(
    "/profile",
    summary="Change some of the logged-in household's profile fields (needs a bearer token)",
    responses=problem_responses(400, 401, 404, 422, 503),
)
def patch_profile(
    account: CurrentAccountDep,
    body: ProfilePatch,
    _: Annotated[NoQuery, Query()],
    service: Service,
) -> ProfileResponse:
    return service.update(account, body)
