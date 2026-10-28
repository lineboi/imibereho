"""Household accounts (contract §11.8): the only repository that writes."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.household_account import HouseholdAccount


class IdentifierInUseError(Exception):
    """The unique identifier constraint refused an insert."""


class AccountRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, account_id: str) -> HouseholdAccount | None:
        return self._session.get(HouseholdAccount, account_id)

    def find_by_identifier(self, identifier: str) -> HouseholdAccount | None:
        statement = select(HouseholdAccount).where(HouseholdAccount.identifier == identifier)
        return self._session.scalars(statement).one_or_none()

    def add(self, account: HouseholdAccount) -> None:
        """Insert and commit. A concurrent registration of the same identifier loses here."""
        self._session.add(account)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if "uq_household_accounts_identifier" not in str(exc.orig):
                raise
            raise IdentifierInUseError from None
