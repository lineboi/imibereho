"""The current household account, for protected routes (contract §11.8).

Used by `GET` and `PATCH /user/profile` (§11.9); the tracker endpoints stay unserved (§11.4). A
protected route declares `account: CurrentAccountDep` and receives the account of a valid bearer
token, or the request ends in 401 `not-authenticated` with `WWW-Authenticate: Bearer`.

The token comes from `Authorization: Bearer <token>` and is verified by
`app.core.security.verify_token` (HS256 only; `sub`, `iat` and `exp` required). Its subject must
still be an existing account, so a token outlives neither a deleted account nor the 24 hours.
Every failure gets the same 401, and nothing about the token, the secret or the exception is
returned or logged. Without JWT_SECRET_KEY the answer is 503 `auth-not-configured`, as for
register and login. Reads use a read-only session.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AuthNotConfiguredError, NotAuthenticatedError
from app.core.security import InvalidTokenError, verify_token
from app.db.session import get_read_session
from app.repositories.account_repository import AccountRepository

# auto_error=False: a missing header or another scheme reaches us as None, so it gets our 401
# problem body rather than FastAPI's default. It also documents the scheme in OpenAPI for any
# route that uses this dependency.
_bearer = HTTPBearer(auto_error=False, scheme_name="bearerToken")


@dataclass(frozen=True, slots=True)
class CurrentAccount:
    """What a protected route may use. Never the password hash."""

    id: str
    identifier: str
    district: str
    household_size: int
    monthly_income: int
    currency: str
    preferred_language: str
    planned_essentials: int | None
    savings_buffer: int | None


def get_current_account(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[Session, Depends(get_read_session)],
) -> CurrentAccount:
    settings: Settings = request.app.state.settings
    if settings.jwt_secret_key is None:
        raise AuthNotConfiguredError
    if credentials is None:
        raise NotAuthenticatedError
    secret = settings.jwt_secret_key.get_secret_value()
    try:
        account_id = verify_token(credentials.credentials, secret)
    except InvalidTokenError:
        raise NotAuthenticatedError from None
    account = AccountRepository(session).get(account_id)
    if account is None:
        raise NotAuthenticatedError
    return CurrentAccount(
        id=account.id,
        identifier=account.identifier,
        district=account.district_code,
        household_size=account.household_size,
        monthly_income=account.monthly_income,
        currency=account.currency,
        preferred_language=account.preferred_language,
        planned_essentials=account.planned_essentials,
        savings_buffer=account.savings_buffer,
    )


CurrentAccountDep = Annotated[CurrentAccount, Depends(get_current_account)]
