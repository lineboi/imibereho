"""Daily tracker (contract §11.10, MISSING_APIS.pdf pages 5-6).

Every route needs `Authorization: Bearer <token>` and works only on that household's data. The
PDF's `PUT /tracker/transactions/{id}` is `PATCH` (owner direction); `PUT` is not routed.
"""

import re
from typing import Annotated, Final

from fastapi import APIRouter, Depends, Header, Path, Query, Response
from pydantic import AfterValidator
from pydantic_core import PydanticCustomError

from app.api.v1.responses import problem_responses
from app.schemas.common import NoQuery
from app.schemas.tracker import (
    IDEMPOTENCY_KEY_MAX,
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
)
from app.services.current_account import CurrentAccountDep
from app.services.tracker_service import TrackerService, get_tracker_reader, get_tracker_writer

router = APIRouter(prefix="/tracker", tags=["tracker"])
Reader = Annotated[TrackerService, Depends(get_tracker_reader)]
Writer = Annotated[TrackerService, Depends(get_tracker_writer)]

_KEY: Final = re.compile(r"[\x21-\x7e]{1,64}")


def _idempotency_key(value: str | None) -> str | None:
    if value is not None and not _KEY.fullmatch(value):
        raise PydanticCustomError("invalid_key", "Must be 1 to 64 printable ASCII characters.")
    return value


IdempotencyKey = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        max_length=IDEMPOTENCY_KEY_MAX,
        description="Optional. Retrying a POST with the same key and body records it once.",
    ),
    AfterValidator(_idempotency_key),
]
# Unknown or malformed ids are simply not found; the bound keeps the lookup cheap.
TransactionId = Annotated[str, Path(alias="id", max_length=40)]


@router.get(
    "/overview",
    summary="The month's plan and spending so far (BR-26 budget health)",
    responses=problem_responses(400, 401, 422, 503),
)
def overview(
    account: CurrentAccountDep, query: Annotated[MonthQuery, Query()], service: Reader
) -> TrackerOverviewResponse:
    return service.overview(account, query)


@router.get(
    "/transactions",
    summary="The month's (or one day's) transactions in time order, paginated",
    responses=problem_responses(400, 401, 422, 503),
)
def list_transactions(
    account: CurrentAccountDep, query: Annotated[TransactionsQuery, Query()], service: Reader
) -> TransactionListResponse:
    return service.transactions(account, query)


@router.post(
    "/transactions",
    status_code=201,
    summary="Log an expense or incoming money (safe to retry with Idempotency-Key)",
    responses=problem_responses(400, 401, 409, 422, 503),
)
def create_transaction(
    account: CurrentAccountDep,
    body: TransactionCreate,
    _: Annotated[NoQuery, Query()],
    service: Writer,
    idempotency_key: IdempotencyKey = None,
) -> TransactionCreatedResponse:
    return service.create(account, body, idempotency_key)


@router.patch(
    "/transactions/{id}",
    summary="Change some fields of one of your transactions",
    responses=problem_responses(400, 401, 404, 422, 503),
)
def patch_transaction(
    account: CurrentAccountDep,
    transaction_id: TransactionId,
    body: TransactionPatch,
    _: Annotated[NoQuery, Query()],
    service: Writer,
) -> TransactionItem:
    return service.update(account, transaction_id, body)


@router.delete(
    "/transactions/{id}",
    status_code=204,
    response_class=Response,
    summary="Delete one of your transactions",
    responses=problem_responses(400, 401, 404, 422, 503),
)
def delete_transaction(
    account: CurrentAccountDep,
    transaction_id: TransactionId,
    _: Annotated[NoQuery, Query()],
    service: Writer,
) -> Response:
    service.delete(account, transaction_id)
    return Response(status_code=204)


@router.get(
    "/daily-trend",
    summary="Each day's expense total in the month (days with spending only)",
    responses=problem_responses(400, 401, 422, 503),
)
def daily_trend(
    account: CurrentAccountDep, query: Annotated[MonthQuery, Query()], service: Reader
) -> DailyTrendResponse:
    return service.daily_trend(account, query)


@router.get(
    "/burn-rate",
    summary="Average daily spending and the month it projects to (BR-27)",
    responses=problem_responses(400, 401, 422, 503),
)
def burn_rate(
    account: CurrentAccountDep, query: Annotated[MonthQuery, Query()], service: Reader
) -> BurnRateResponse:
    return service.burn_rate(account, query)
