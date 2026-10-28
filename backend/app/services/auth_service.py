"""Register and log in a household account (contract §11.8, MISSING_APIS.pdf page 4).

Validation runs first (FastAPI), then the configuration check, then the district lookup, so an
invalid request never reaches the database. Register is the only write in the API: it stores
the account (Argon2id hash, never the password) and returns a bearer token. Login answers the
same 401 for an unknown identifier and a wrong password, after the same hashing work.
"""

from typing import Annotated

from fastapi import Depends, Request
from pydantic_core import PydanticCustomError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.constants import METHODOLOGY_VERSION
from app.core.errors import AuthNotConfiguredError, IdentifierTakenError, InvalidCredentialsError
from app.core.security import (
    TOKEN_TTL_SECONDS,
    hash_password,
    issue_token,
    new_account_id,
    verify_password,
)
from app.db.session import get_write_session
from app.models.household_account import HouseholdAccount
from app.repositories.account_repository import AccountRepository, IdentifierInUseError
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.auth import (
    LoggedInUser,
    LoginRequest,
    LoginResponse,
    RegisteredUser,
    RegisterRequest,
    RegisterResponse,
    normalise_identifier,
)
from app.services.benchmark_service import require_district


class AuthService:
    def __init__(
        self,
        accounts: AccountRepository,
        reference: ReferenceDataRepository,
        secret: str | None,
    ) -> None:
        self._accounts = accounts
        self._reference = reference
        self._secret = secret

    def _require_secret(self) -> str:
        if self._secret is None:
            raise AuthNotConfiguredError
        return self._secret

    def register(self, request: RegisterRequest) -> RegisterResponse:
        secret = self._require_secret()
        profile = request.profile
        district = require_district(self._reference, profile.district)
        if self._accounts.find_by_identifier(request.identifier) is not None:
            raise IdentifierTakenError
        account = HouseholdAccount(
            id=new_account_id(),
            identifier=request.identifier,
            password_hash=hash_password(request.password),
            district_code=district.code,
            household_size=profile.household_size,
            monthly_income=profile.monthly_income,
            currency=profile.currency,
            preferred_language=profile.preferred_language,
        )
        try:
            self._accounts.add(account)
        except IdentifierInUseError:
            raise IdentifierTakenError from None
        return RegisterResponse(
            token=issue_token(account.id, secret),
            expires_in=TOKEN_TTL_SECONDS,
            user=RegisteredUser(
                id=account.id,
                identifier=account.identifier,
                district=account.district_code,
                household_size=account.household_size,
            ),
        )

    def login(self, request: LoginRequest) -> LoginResponse:
        secret = self._require_secret()
        try:
            identifier: str | None = normalise_identifier(request.identifier)
        except PydanticCustomError:
            identifier = None  # cannot match an account; still answered like a wrong password
        account = self._accounts.find_by_identifier(identifier) if identifier else None
        # Always verified, with a dummy hash when there is no account, so both failures cost
        # the same.
        password_ok = verify_password(account.password_hash if account else None, request.password)
        if account is None or not password_ok:
            raise InvalidCredentialsError
        return LoginResponse(
            token=issue_token(account.id, secret),
            user=LoggedInUser(id=account.id, district=account.district_code),
        )


def get_auth_service(
    request: Request, session: Annotated[Session, Depends(get_write_session)]
) -> AuthService:
    settings: Settings = request.app.state.settings
    secret = settings.jwt_secret_key.get_secret_value() if settings.jwt_secret_key else None
    return AuthService(
        AccountRepository(session), ReferenceDataRepository(session, METHODOLOGY_VERSION), secret
    )
