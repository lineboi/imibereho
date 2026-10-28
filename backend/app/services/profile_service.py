"""Read and update the logged-in household's profile (contract §11.9).

`GET` needs no query of its own: `CurrentAccountDep` has already loaded and verified the account.
`PATCH` writes with one `UPDATE ... RETURNING` that sets only the fields the body contains, so two
concurrent PATCHes of different fields both survive (no read-modify-write window), and the
response is the row as committed. Order: token (401), body validation (422), district (404).
"""

from typing import Annotated, Final, cast

from fastapi import Depends
from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.core.constants import METHODOLOGY_VERSION
from app.core.errors import NotAuthenticatedError
from app.db.session import get_write_session
from app.models.household_account import HouseholdAccount
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.auth import PreferredLanguage
from app.schemas.profile import ProfilePatch, ProfileResponse
from app.services.benchmark_service import require_district
from app.services.current_account import CurrentAccount

# Wire field (Python name) -> column. Only these can change; the schema refuses anything else.
_COLUMNS: Final = {
    "district": HouseholdAccount.district_code,
    "household_size": HouseholdAccount.household_size,
    "monthly_income": HouseholdAccount.monthly_income,
    "planned_essentials": HouseholdAccount.planned_essentials,
    "savings_buffer": HouseholdAccount.savings_buffer,
    "preferred_language": HouseholdAccount.preferred_language,
}


def _language(value: str) -> PreferredLanguage:
    # The column's CHECK constraint allows only 'EN' and 'RW' (migration 0009).
    return cast(PreferredLanguage, value)


def profile_of(account: CurrentAccount) -> ProfileResponse:
    return ProfileResponse(
        id=account.id,
        district=account.district,
        household_size=account.household_size,
        monthly_income=account.monthly_income,
        planned_essentials=account.planned_essentials,
        savings_buffer=account.savings_buffer,
        preferred_language=_language(account.preferred_language),
    )


def _profile_of_row(row: HouseholdAccount) -> ProfileResponse:
    return ProfileResponse(
        id=row.id,
        district=row.district_code,
        household_size=row.household_size,
        monthly_income=row.monthly_income,
        planned_essentials=row.planned_essentials,
        savings_buffer=row.savings_buffer,
        preferred_language=_language(row.preferred_language),
    )


class ProfileService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def update(self, account: CurrentAccount, patch: ProfilePatch) -> ProfileResponse:
        changes = patch.changes()
        if not changes:
            return profile_of(account)  # `{}` changes nothing: no write, no updated_at
        if "district" in changes:
            reference = ReferenceDataRepository(self._session, METHODOLOGY_VERSION)
            require_district(reference, str(changes["district"]))
        values = {_COLUMNS[name].key: value for name, value in changes.items()}
        statement = (
            update(HouseholdAccount)
            .where(HouseholdAccount.id == account.id)
            .values(**values, updated_at=func.now())
            .returning(HouseholdAccount)
        )
        row = self._session.scalars(statement).one_or_none()
        if row is None:
            # The account was deleted after its token was checked: the same 401 as any other
            # token whose account no longer exists.
            self._session.rollback()
            raise NotAuthenticatedError
        self._session.commit()
        return _profile_of_row(row)


def get_profile_service(session: Annotated[Session, Depends(get_write_session)]) -> ProfileService:
    return ProfileService(session)
