"""Tracker transactions (contract §11.10). Every query is scoped to one account.

Reads use the `(account_id, occurred_at, id)` index: a month or day is a time range, the list is
keyset-paginated on `(occurred_at, id)` (no OFFSET, so page N costs the same as page 1), and the
sums are single aggregate queries. Days and months are Kigali calendar time (`Africa/Kigali`).
"""

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import Date, cast, delete, func, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import KIGALI_TZ_NAME
from app.models.tracker_transaction import TrackerTransaction as Tx


class IdempotencyKeyInUseError(Exception):
    """The (account, Idempotency-Key) unique constraint refused an insert."""


class TrackerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_page(
        self,
        account_id: str,
        start: datetime,
        end: datetime,
        kind: str | None,
        after: tuple[datetime, str] | None,
        limit: int,
    ) -> Sequence[Tx]:
        """Up to `limit` + 1 rows (the extra one tells the caller another page exists)."""
        statement = select(Tx).where(
            Tx.account_id == account_id, Tx.occurred_at >= start, Tx.occurred_at < end
        )
        if kind is not None:
            statement = statement.where(Tx.type == kind)
        if after is not None:
            statement = statement.where(tuple_(Tx.occurred_at, Tx.id) > tuple_(*after))
        statement = statement.order_by(Tx.occurred_at, Tx.id).limit(limit + 1)
        return self._session.scalars(statement).all()

    def expense_total(self, account_id: str, start: datetime, end: datetime) -> int:
        statement = select(func.coalesce(func.sum(Tx.amount), 0)).where(
            Tx.account_id == account_id,
            Tx.type == "expense",
            Tx.occurred_at >= start,
            Tx.occurred_at < end,
        )
        return int(self._session.scalar(statement) or 0)

    def daily_expense_totals(
        self, account_id: str, start: datetime, end: datetime
    ) -> list[tuple[date, int]]:
        """(Kigali date, total) for each day in [start, end) with at least one expense."""
        day = cast(func.timezone(KIGALI_TZ_NAME, Tx.occurred_at), Date).label("day")
        statement = (
            select(day, func.sum(Tx.amount))
            .where(
                Tx.account_id == account_id,
                Tx.type == "expense",
                Tx.occurred_at >= start,
                Tx.occurred_at < end,
            )
            .group_by(day)
            .order_by(day)
        )
        return [(row[0], int(row[1])) for row in self._session.execute(statement)]

    def get_for_update(self, account_id: str, transaction_id: str) -> Tx | None:
        """The caller's transaction, locked until the transaction ends (no lost update)."""
        statement = (
            select(Tx).where(Tx.id == transaction_id, Tx.account_id == account_id).with_for_update()
        )
        return self._session.scalars(statement).one_or_none()

    def find_by_idempotency_key(self, account_id: str, key: str) -> Tx | None:
        statement = select(Tx).where(Tx.account_id == account_id, Tx.idempotency_key == key)
        return self._session.scalars(statement).one_or_none()

    def add(self, transaction: Tx) -> None:
        """Insert without committing; a concurrent retry with the same key loses here."""
        self._session.add(transaction)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            if "uq_tracker_transactions_account_id_idempotency_key" not in str(exc.orig):
                raise
            raise IdempotencyKeyInUseError from None

    def delete(self, account_id: str, transaction_id: str) -> bool:
        statement = delete(Tx).where(Tx.id == transaction_id, Tx.account_id == account_id)
        return bool(self._session.execute(statement).rowcount)  # type: ignore[attr-defined]
