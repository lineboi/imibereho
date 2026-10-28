"""Tracker rules without a database: BR-26, BR-27, Kigali months, cursors (contract §11.10)."""

from datetime import UTC, date, datetime

import pytest

from app.calculations import budget_health, burn_rate
from app.core.clock import KIGALI, Month, day_window, get_clock
from app.core.errors import RequestValidationProblem
from app.models.tracker_transaction import TrackerTransaction
from app.schemas.tracker import TransactionCreate
from app.services.tracker_service import decode_cursor, encode_cursor, request_hash


@pytest.mark.parametrize(
    ("spent", "planned", "elapsed", "days", "expected"),
    [
        # The PDF's overview: 118,400 by 26 October of a 150,000 plan is under an even pace.
        (118_400, 150_000, 26, 31, "normal"),
        (118_400, 150_000, 25, 31, "normal"),  # pace 120,967.7
        (121_000, 150_000, 25, 31, "caution"),  # ahead of pace, within the plan
        (150_000, 150_000, 31, 31, "normal"),  # exactly the plan at the end of the month
        (150_001, 150_000, 31, 31, "exceeded"),
        (150_001, 150_000, 3, 31, "exceeded"),
        (0, 150_000, 0, 31, "normal"),
        (1, 0, 10, 31, "exceeded"),
        (0, 0, 10, 31, "normal"),
        (5_000, None, 10, 31, None),  # no plan, no health
    ],
)
def test_br_26_budget_health(
    spent: int, planned: int | None, elapsed: int, days: int, expected: str | None
) -> None:
    assert budget_health(spent, planned, elapsed, days) == expected


def test_br_26_rejects_impossible_inputs() -> None:
    with pytest.raises(ValueError, match="spent"):
        budget_health(-1, 100, 1, 31)
    with pytest.raises(ValueError, match="days_in_month"):
        budget_health(1, 100, 1, 0)
    with pytest.raises(ValueError, match="planned"):
        budget_health(1, -100, 1, 31)


@pytest.mark.parametrize(
    ("spent", "elapsed", "days", "average", "projected"),
    [
        (118_400, 26, 31, 4_554, 141_169),  # 4,553.85 and 141,169.23, half up
        (3_100, 31, 31, 100, 3_100),
        (0, 5, 30, 0, 0),
        (1, 2, 31, 1, 16),  # 0.5 -> 1 and 15.5 -> 16 (projected from spent, not the average)
    ],
)
def test_br_27_burn_rate(spent: int, elapsed: int, days: int, average: int, projected: int) -> None:
    rate = burn_rate(spent, elapsed, days)
    assert rate is not None
    assert (rate.average_daily, rate.projected_month) == (average, projected)


def test_br_27_before_the_month_starts_and_bad_inputs() -> None:
    assert burn_rate(0, 0, 31) is None
    with pytest.raises(ValueError, match="elapsed_days"):
        burn_rate(10, 32, 31)
    with pytest.raises(ValueError, match="spent"):
        burn_rate(-1, 1, 31)


def test_kigali_months() -> None:
    october = Month.parse("2026-10")
    assert (str(october), october.days) == ("2026-10", 31)
    assert october.start == datetime(2026, 9, 30, 22, 0, tzinfo=UTC)  # midnight in Kigali
    assert october.end == datetime(2026, 10, 31, 22, 0, tzinfo=UTC)
    assert Month.parse("2026-12").end == datetime(2027, 1, 1, tzinfo=KIGALI)
    assert Month.parse("2028-02").days == 29
    # 23:30 UTC on 31 October is 1 November in Kigali.
    assert Month.of(datetime(2026, 10, 31, 23, 30, tzinfo=UTC)) == Month(2026, 11)
    now = datetime(2026, 10, 26, 16, 0, tzinfo=UTC)  # 18:00 in Kigali
    assert october.elapsed_days(now) == 26
    assert Month.parse("2026-09").elapsed_days(now) == 30
    assert Month.parse("2026-11").elapsed_days(now) == 0
    assert october.contains(date(2026, 10, 7)) and not october.contains(date(2026, 11, 1))
    start, end = day_window(date(2026, 10, 7))
    assert (start, end) == (
        datetime(2026, 10, 6, 22, 0, tzinfo=UTC), datetime(2026, 10, 7, 22, 0, tzinfo=UTC),
    )  # fmt: skip


def test_cursor_round_trip_and_rejection() -> None:
    row = TrackerTransaction(
        id="tx_" + "0" * 10 + "A" * 16, occurred_at=datetime(2026, 10, 7, 10, 30, tzinfo=UTC)
    )
    assert decode_cursor(encode_cursor(row)) == (row.occurred_at, row.id)
    for bad in ("", "not-base64!", "Zm9v", encode_cursor(row)[:-3] + "AAA"):
        with pytest.raises(RequestValidationProblem) as excinfo:
            decode_cursor(bad)
        assert excinfo.value.errors is not None
        assert [(e.field, e.code) for e in excinfo.value.errors] == [("cursor", "invalid_format")]


def test_request_hash_is_stable_and_body_sensitive() -> None:
    body = {"type": "expense", "title": "Gas", "category": "utilities", "amount": 9500,
            "date": "2026-10-26T14:30:00Z"}  # fmt: skip
    first = request_hash(TransactionCreate.model_validate(body))
    # The same request written differently (zone, spacing in the title) hashes the same.
    same = {**body, "date": "2026-10-26T16:30:00+02:00", "title": "  Gas "}
    assert request_hash(TransactionCreate.model_validate(same)) == first
    assert request_hash(TransactionCreate.model_validate({**body, "amount": 9501})) != first


def test_the_production_clock_is_utc_now() -> None:
    clock = get_clock()
    before = datetime.now(UTC)
    moment = clock()
    assert moment.tzinfo is not None and before <= moment <= datetime.now(UTC)
