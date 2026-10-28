"""Daily tracker (contract §11.10, MISSING_APIS.pdf pages 5-6).

Field names follow the PDF wherever it gives a body: overview, the transaction list and its
items, the POST request and response, and the daily trend. Where it gives none (the PATCH that
replaces its PUT, DELETE, burn-rate) the shapes are contract extensions, documented in §11.10.
Additions to PDF shapes: `note` on list items and `nextCursor` on the list.

Validation (the PDF gives none, so these are the backend's rules):
- `type` is `expense` or `income`; `category` must belong to it: expense `food`, `transport`,
  `utilities`, `other` (the frontend's four, which are also its icon types); income
  `mobile_money`, `day_wage`, `market_sales`, `side_gig` (the frontend's four, as codes).
- `title`: 1-120 characters after trimming; `note`: up to 280, blank means none. Neither may
  contain control characters (a NUL would otherwise reach PostgreSQL); a note may hold line breaks.
- `amount`: whole RWF, 1 to 100,000,000.
- `date`: an ISO 8601 date-time string with a time zone (`2026-10-26T14:30:00Z`); sub-second
  precision is dropped. Not in the future and not before 2000 (checked by the service).
- Query `month` is `YYYY-MM` and `date` is `YYYY-MM-DD`, both Kigali calendar time.
"""

import re
from datetime import UTC, datetime
from datetime import date as Date
from typing import Annotated, Final, Literal

from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    StrictInt,
    StrictStr,
    ValidationInfo,
    field_validator,
)
from pydantic_core import PydanticCustomError

from app.core.constants import MONEY_MAX
from app.schemas.common import ApiModel, BodyModel, QueryInt, QueryModel

TransactionType = Literal["expense", "income"]
ExpenseCategory = Literal["food", "transport", "utilities", "other"]
IncomeCategory = Literal["mobile_money", "day_wage", "market_sales", "side_gig"]
Category = Literal[
    "food", "transport", "utilities", "other",
    "mobile_money", "day_wage", "market_sales", "side_gig",
]  # fmt: skip
CATEGORIES_BY_TYPE: Final[dict[str, frozenset[str]]] = {
    "expense": frozenset({"food", "transport", "utilities", "other"}),
    "income": frozenset({"mobile_money", "day_wage", "market_sales", "side_gig"}),
}
BudgetHealth = Literal["normal", "caution", "exceeded"]

TITLE_MAX: Final = 120
NOTE_MAX: Final = 280
LIST_LIMIT_DEFAULT: Final = 200
LIST_LIMIT_MAX: Final = 500
CURSOR_MAX: Final = 200
IDEMPOTENCY_KEY_MAX: Final = 64

_MONTH: Final = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])")
_DAY: Final = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
# ISO 8601 date and time with seconds and a zone; ASCII digits only.
_DATETIME: Final = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})"
)
_TITLE_CONTROL: Final = re.compile(r"[\x00-\x1f\x7f]")
_NOTE_CONTROL: Final = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # \t \n \r allowed


def _month(value: str) -> str:
    if not _MONTH.fullmatch(value):
        raise PydanticCustomError("invalid_month", "Must be a month as YYYY-MM.")
    return value


def _day(value: object) -> Date:
    try:
        if not isinstance(value, str) or not _DAY.fullmatch(value):
            raise ValueError
        return Date.fromisoformat(value)
    except ValueError:
        raise PydanticCustomError("invalid_date", "Must be a date as YYYY-MM-DD.") from None


def _moment(value: object) -> datetime:
    if not isinstance(value, str) or not _DATETIME.fullmatch(value):
        raise PydanticCustomError("invalid_datetime", "Must be an ISO 8601 date-time with a zone.")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise PydanticCustomError(
            "invalid_datetime", "Must be an ISO 8601 date-time with a zone."
        ) from None
    return parsed.astimezone(UTC).replace(microsecond=0)


def _title(value: str) -> str:
    text = value.strip()
    if not text:
        raise PydanticCustomError("too_short", "This value is too short.")
    if len(text) > TITLE_MAX:
        raise PydanticCustomError("too_long", "This value is too long.")
    if _TITLE_CONTROL.search(text):
        raise PydanticCustomError("control_characters", "Must not contain control characters.")
    return text


def _note(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if len(text) > NOTE_MAX:
        raise PydanticCustomError("too_long", "This value is too long.")
    if _NOTE_CONTROL.search(text):
        raise PydanticCustomError("control_characters", "Must not contain control characters.")
    return text or None


MonthStr = Annotated[str, Field(max_length=7), AfterValidator(_month)]
DayParam = Annotated[Date, BeforeValidator(_day)]
Moment = Annotated[datetime, BeforeValidator(_moment)]
# Long enough for any title before trimming; `_title` enforces the 120 after it.
Title = Annotated[StrictStr, Field(max_length=TITLE_MAX * 2), AfterValidator(_title)]
Note = Annotated[StrictStr | None, Field(max_length=NOTE_MAX * 2), AfterValidator(_note)]
Amount = Annotated[StrictInt, Field(ge=1, le=MONEY_MAX)]


def _category_matches(category: str | None, info: ValidationInfo) -> str | None:
    allowed = CATEGORIES_BY_TYPE.get(str(info.data.get("type")))
    if category is not None and allowed is not None and category not in allowed:
        raise PydanticCustomError(
            "category_mismatch", "This category does not belong to the transaction type."
        )
    return category


# --- Requests ---


class TransactionCreate(BodyModel):
    """MISSING_APIS.pdf page 6, field for field (`note` optional)."""

    type: TransactionType
    title: Title
    category: Category
    note: Note = None
    amount: Amount
    date: Moment

    _category = field_validator("category")(_category_matches)


class TransactionPatch(BodyModel):
    """Contract extension (§11.10): the PDF's PUT has no body. Any POST field, all optional."""

    type: TransactionType | None = None
    title: Title | None = None
    category: Category | None = None
    note: Note = None
    amount: Amount | None = None
    date: Moment | None = None

    _category = field_validator("category")(_category_matches)

    @field_validator("type", "title", "category", "amount", "date", mode="before")
    @classmethod
    def _refuse_null(cls, value: object) -> object:
        # Only fields the body contains are validated: an explicit null on a field that always
        # has a value is 422 `required` (contract §1.2); `note: null` clears the note.
        if value is None:
            raise PydanticCustomError("null_not_allowed", "This field cannot be null.")
        return value

    def changes(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.model_fields_set}


class MonthQuery(QueryModel):
    month: MonthStr | None = Field(default=None, description="YYYY-MM; default: this month")


class TransactionsQuery(QueryModel):
    month: MonthStr | None = Field(default=None, description="YYYY-MM; default: this month")
    date: DayParam | None = Field(default=None, description="YYYY-MM-DD: one day instead")
    type: TransactionType | None = None
    limit: Annotated[QueryInt, Field(ge=1, le=LIST_LIMIT_MAX)] = LIST_LIMIT_DEFAULT
    cursor: Annotated[str, Field(max_length=CURSOR_MAX)] | None = Field(
        default=None, description="`nextCursor` of the previous page"
    )


# --- Responses ---


class TransactionItem(ApiModel):
    id: str
    type: TransactionType
    title: str
    category: Category
    amount: int
    date: str = Field(description="ISO 8601 in UTC, e.g. 2026-10-07T10:30:00Z")
    icon_type: Category = Field(description="Equal to category")
    note: str | None = Field(description="Addition to the PDF's item")


class TransactionListResponse(ApiModel):
    items: list[TransactionItem]
    day_total_expenses: int | None = Field(
        description="Total of the day's expenses when `date` is given, else null"
    )
    next_cursor: str | None = Field(description="Addition: pass as `cursor` for the next page")


class TransactionCreatedResponse(ApiModel):
    id: str
    status: Literal["recorded"]
    amount: int
    new_monthly_spent_total: int


class TrackerOverviewResponse(ApiModel):
    month: str
    monthly_income: int
    planned_expenses: int | None
    left_after_plan: int | None
    demo_savings: int | None
    total_spent_so_far: int
    daily_budget_health: BudgetHealth | None


class TrendPoint(ApiModel):
    date: str
    total: int


class DailyTrendResponse(ApiModel):
    month: str
    points: list[TrendPoint]


class BurnRateResponse(ApiModel):
    """Contract extension (§11.10): the PDF lists burn-rate with no body."""

    month: str
    days_elapsed: int
    days_in_month: int
    total_spent_so_far: int
    average_daily_spend: int | None
    projected_month_spend: int | None
    planned_expenses: int | None
    projected_vs_plan: int | None = Field(
        description="projectedMonthSpend − plannedExpenses: positive means over the plan"
    )
