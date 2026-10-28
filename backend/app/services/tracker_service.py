"""Daily tracker (contract §11.10; BR-26, BR-27): one household's transactions and summaries.

Every operation is scoped to the account of the bearer token; another household's transaction
answers 404 as if it did not exist. Months and days are Kigali calendar time, and "now" comes
from the injectable clock. Reads run on a read-only session; writes on a writable one.

Rules the PDF leaves open (documented in §11.10):
- `month` defaults to the current Kigali month; a future month or day is 422 `out_of_range`.
- A transaction's `date` may not be more than 5 minutes ahead of the server (phone clocks
  drift) and not before 2000-01-01.
- POST with `Idempotency-Key`: a retry with the same key and body answers with the same `id`
  and stores nothing twice; it reports the transaction as it is now (not a stored copy of the
  first response). The same key with a different body is 409. Known limitation: the key lives
  on the transaction, so after a delete a late retry records it again (contract §11.10).
- PATCH locks the row (`SELECT ... FOR UPDATE`), applies the fields sent, and checks that the
  resulting category belongs to the resulting type.
"""

import base64
import binascii
import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from typing import Annotated, Final

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import budget_health, burn_rate
from app.core.clock import KIGALI, Clock, Month, day_window, get_clock
from app.core.errors import (
    FieldError,
    IdempotencyKeyReusedError,
    RequestValidationProblem,
    TransactionNotFoundError,
)
from app.core.security import new_transaction_id
from app.db.session import get_read_session, get_write_session
from app.models.tracker_transaction import TrackerTransaction
from app.repositories.tracker_repository import IdempotencyKeyInUseError, TrackerRepository
from app.schemas.tracker import (
    CATEGORIES_BY_TYPE,
    BurnRateResponse,
    DailyTrendResponse,
    MonthQuery,
    TrackerOverviewResponse,
    TransactionCreate,
    TransactionCreatedResponse,
    TransactionItem,
    TransactionListResponse,
    TransactionPatch,
    TransactionsQuery,
    TrendPoint,
)
from app.services.current_account import CurrentAccount

CLOCK_SKEW: Final = timedelta(minutes=5)
EARLIEST: Final = datetime(2000, 1, 1, tzinfo=UTC)
EARLIEST_MONTH: Final = Month(2000, 1)
_TX_ID: Final = re.compile(r"tx_[0-9A-HJKMNP-TV-Z]{26}")


def _invalid(field: str, code: str, message: str) -> RequestValidationProblem:
    return RequestValidationProblem([FieldError(field=field, code=code, message=message)])


def _wire_time(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def item_of(row: TrackerTransaction) -> TransactionItem:
    return TransactionItem.model_validate(
        {
            "id": row.id,
            "type": row.type,
            "title": row.title,
            "category": row.category,
            "amount": row.amount,
            "date": _wire_time(row.occurred_at),
            "icon_type": row.category,
            "note": row.note,
        }
    )


def encode_cursor(row: TrackerTransaction) -> str:
    raw = f"{row.occurred_at.astimezone(UTC).isoformat()}|{row.id}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
        moment, transaction_id = raw.split("|")
        parsed = datetime.fromisoformat(moment)
        if parsed.tzinfo is None or not _TX_ID.fullmatch(transaction_id):
            raise ValueError
    except (ValueError, binascii.Error, UnicodeDecodeError):
        raise _invalid(
            "cursor", "invalid_format", "Must be the nextCursor of a previous page."
        ) from None
    return parsed, transaction_id


def request_hash(body: TransactionCreate) -> str:
    canonical = json.dumps(body.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


class TrackerService:
    def __init__(self, session: Session, clock: Clock) -> None:
        self._session = session
        self._repository = TrackerRepository(session)
        self._clock = clock

    # --- periods ---

    def _month(self, value: str | None, now: datetime) -> Month:
        if value is None:
            return Month.of(now)
        month = Month.parse(value)
        current = Month.of(now)
        if (month.year, month.month) > (current.year, current.month):
            raise _invalid("month", "out_of_range", "Must not be after the current month.")
        if (month.year, month.month) < (EARLIEST_MONTH.year, EARLIEST_MONTH.month):
            raise _invalid("month", "out_of_range", "Must not be before 2000-01.")
        return month

    def _check_moment(self, moment: datetime, now: datetime) -> None:
        if moment > now + CLOCK_SKEW:
            raise _invalid("date", "out_of_range", "Must not be in the future.")
        if moment < EARLIEST:
            raise _invalid("date", "out_of_range", "Must not be before 2000-01-01.")

    # --- reads ---

    def overview(self, account: CurrentAccount, query: MonthQuery) -> TrackerOverviewResponse:
        now = self._clock()
        month = self._month(query.month, now)
        spent = self._repository.expense_total(account.id, month.start, month.end)
        planned = account.planned_essentials
        return TrackerOverviewResponse(
            month=str(month),
            monthly_income=account.monthly_income,
            planned_expenses=planned,
            left_after_plan=None if planned is None else account.monthly_income - planned,
            demo_savings=account.savings_buffer,
            total_spent_so_far=spent,
            daily_budget_health=budget_health(spent, planned, month.elapsed_days(now), month.days),
        )

    def transactions(
        self, account: CurrentAccount, query: TransactionsQuery
    ) -> TransactionListResponse:
        now = self._clock()
        day = query.date
        if day is not None:
            if query.month is not None and not Month.parse(query.month).contains(day):
                raise _invalid("date", "out_of_range", "Must be inside the given month.")
            if day > now.astimezone(KIGALI).date():
                raise _invalid("date", "out_of_range", "Must not be in the future.")
            start, end = day_window(day)
        else:
            month = self._month(query.month, now)
            start, end = month.start, month.end
        after = decode_cursor(query.cursor) if query.cursor is not None else None
        rows = self._repository.list_page(account.id, start, end, query.type, after, query.limit)
        page, more = rows[: query.limit], len(rows) > query.limit
        return TransactionListResponse(
            items=[item_of(row) for row in page],
            day_total_expenses=(
                self._repository.expense_total(account.id, start, end) if day is not None else None
            ),
            next_cursor=encode_cursor(page[-1]) if more else None,
        )

    def daily_trend(self, account: CurrentAccount, query: MonthQuery) -> DailyTrendResponse:
        month = self._month(query.month, self._clock())
        totals = self._repository.daily_expense_totals(account.id, month.start, month.end)
        return DailyTrendResponse(
            month=str(month),
            points=[TrendPoint(date=day.isoformat(), total=total) for day, total in totals],
        )

    def burn_rate(self, account: CurrentAccount, query: MonthQuery) -> BurnRateResponse:
        now = self._clock()
        month = self._month(query.month, now)
        spent = self._repository.expense_total(account.id, month.start, month.end)
        elapsed = month.elapsed_days(now)
        rate = burn_rate(spent, elapsed, month.days)
        planned = account.planned_essentials
        projected = rate.projected_month if rate else None
        return BurnRateResponse(
            month=str(month),
            days_elapsed=elapsed,
            days_in_month=month.days,
            total_spent_so_far=spent,
            average_daily_spend=rate.average_daily if rate else None,
            projected_month_spend=projected,
            planned_expenses=planned,
            projected_vs_plan=(
                None if projected is None or planned is None else projected - planned
            ),
        )

    # --- writes ---

    def create(
        self, account: CurrentAccount, body: TransactionCreate, idempotency_key: str | None
    ) -> TransactionCreatedResponse:
        self._check_moment(body.date, self._clock())
        fingerprint = request_hash(body) if idempotency_key is not None else None
        if idempotency_key is not None:
            existing = self._repository.find_by_idempotency_key(account.id, idempotency_key)
            if existing is not None:
                return self._replay(account, existing, fingerprint)
        row = TrackerTransaction(
            id=new_transaction_id(),
            account_id=account.id,
            type=body.type,
            category=body.category,
            title=body.title,
            note=body.note,
            amount=body.amount,
            occurred_at=body.date,
            idempotency_key=idempotency_key,
            request_hash=fingerprint,
        )
        try:
            self._repository.add(row)
        except IdempotencyKeyInUseError:
            # A concurrent retry with the same key committed first: answer as a replay. Only
            # keyed inserts can collide, so the key is set here.
            winner = self._repository.find_by_idempotency_key(account.id, idempotency_key or "")
            if winner is None:  # pragma: no cover - the row that won cannot vanish here
                raise
            return self._replay(account, winner, fingerprint)
        total = self._month_total(account.id, row.occurred_at)
        self._session.commit()
        return TransactionCreatedResponse(
            id=row.id, status="recorded", amount=row.amount, new_monthly_spent_total=total
        )

    def _replay(
        self, account: CurrentAccount, row: TrackerTransaction, fingerprint: str | None
    ) -> TransactionCreatedResponse:
        if row.request_hash != fingerprint:
            raise IdempotencyKeyReusedError
        return TransactionCreatedResponse(
            id=row.id,
            status="recorded",
            amount=row.amount,
            new_monthly_spent_total=self._month_total(account.id, row.occurred_at),
        )

    def _month_total(self, account_id: str, moment: datetime) -> int:
        month = Month.of(moment)
        return self._repository.expense_total(account_id, month.start, month.end)

    def update(
        self, account: CurrentAccount, transaction_id: str, patch: TransactionPatch
    ) -> TransactionItem:
        row = self._repository.get_for_update(account.id, transaction_id)
        if row is None:
            raise TransactionNotFoundError
        changes = patch.changes()
        if not changes:
            self._session.rollback()  # release the lock; `{}` changes nothing
            return item_of(row)
        kind = str(changes.get("type", row.type))
        category = str(changes.get("category", row.category))
        if category not in CATEGORIES_BY_TYPE[kind]:
            raise _invalid(
                "category",
                "unknown_value",
                "This category does not belong to the transaction type.",
            )
        now = self._clock()
        if patch.date is not None:
            self._check_moment(patch.date, now)
        for name, value in changes.items():
            setattr(row, "occurred_at" if name == "date" else name, value)
        row.updated_at = now
        self._session.commit()
        return item_of(row)

    def delete(self, account: CurrentAccount, transaction_id: str) -> None:
        if not self._repository.delete(account.id, transaction_id):
            raise TransactionNotFoundError
        self._session.commit()


def get_tracker_reader(
    session: Annotated[Session, Depends(get_read_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> TrackerService:
    return TrackerService(session, clock)


def get_tracker_writer(
    session: Annotated[Session, Depends(get_write_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> TrackerService:
    return TrackerService(session, clock)
