"""Daily tracker endpoints (contract §11.10, MISSING_APIS.pdf pages 5-6).

The clock is fixed at 2026-10-26 18:00 Kigali time (16:00 UTC), so the PDF's own examples (data
for 1-25 October, and its POST dated 26 October 14:30 UTC) reproduce exactly.
"""

from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any, Final

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from app.core.clock import get_clock
from app.core.config import Settings
from app.db.session import Database
from app.main import create_app
from app.models import HouseholdAccount, TrackerTransaction
from app.repositories.tracker_repository import TrackerRepository
from tests.helpers import NOT_INTEGER_BODY_VALUES, assert_problem, raw_json

BASE: Final = "/api/v1/tracker"
TX: Final = f"{BASE}/transactions"
SECRET: Final = "test-only-signing-key-0123456789abcdef"  # never a real key
NOW: Final = datetime(2026, 10, 26, 16, 0, tzinfo=UTC)
PDF_REGISTER: Final[dict[str, Any]] = {
    "identifier": "+250788123456",
    "password": "SecurePassword123!",
    "profile": {"district": "gasabo", "householdSize": 4, "monthlyIncome": 180000,
                "currency": "RWF", "preferredLanguage": "RW"},
}  # fmt: skip
# MISSING_APIS.pdf page 6, the POST request exactly.
PDF_POST: Final[dict[str, Any]] = {
    "type": "expense",
    "title": "Cooking gas refill (6kg)",
    "category": "utilities",
    "note": "Gasabo local depot",
    "amount": 9500,
    "date": "2026-10-26T14:30:00Z",
}
ITEM_KEYS: Final = {"id", "type", "title", "category", "amount", "date", "iconType", "note"}


def _client(
    settings: Settings, database: Database, clock: Callable[[], datetime]
) -> Iterator[TestClient]:
    configured = settings.model_copy(update={"jwt_secret_key": SecretStr(SECRET)})
    app = create_app("test", settings=configured, database=database)
    app.dependency_overrides[get_clock] = lambda: clock
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def _clear(database: Database) -> None:
    with database.session() as session:
        session.execute(delete(HouseholdAccount))  # transactions cascade
        session.commit()


@pytest.fixture
def client(db_settings: Settings, test_database: Database) -> Iterator[TestClient]:
    _clear(test_database)
    yield from _client(db_settings, test_database, lambda: NOW)
    _clear(test_database)


def register(client: TestClient, identifier: str = "+250788123456") -> dict[str, str]:
    data = raw_json(client.post("/api/v1/auth/register",
                                json={**PDF_REGISTER, "identifier": identifier}))  # fmt: skip
    return {"Authorization": f"Bearer {data['token']}"}


@pytest.fixture
def auth(client: TestClient) -> dict[str, str]:
    return register(client)


def with_plan(client: TestClient, auth: dict[str, str]) -> None:
    """The PDF household's plan and savings (the GET profile example)."""
    body = {"plannedEssentials": 150000, "savingsBuffer": 60000}
    assert client.patch("/api/v1/user/profile", json=body, headers=auth).status_code == 200


def add(client: TestClient, auth: dict[str, str], **fields: object) -> dict[str, Any]:
    response = client.post(TX, json={**PDF_POST, **fields}, headers=auth)
    assert response.status_code == 201, response.text
    data: dict[str, Any] = raw_json(response)
    return data


def count(database: Database) -> int:
    with database.read_only_session() as session:
        return int(session.scalar(select(func.count()).select_from(TrackerTransaction)) or 0)


# --- Overview (PDF page 5) ---


def test_overview_reproduces_the_pdf_example(client: TestClient, auth: dict[str, str]) -> None:
    with_plan(client, auth)
    add(client, auth, amount=100_000, date="2026-10-10T08:00:00Z")
    add(client, auth, amount=18_400, date="2026-10-20T08:00:00Z")
    add(client, auth, type="income", category="day_wage", amount=50_000)  # not spending
    response = client.get(f"{BASE}/overview?month=2026-10", headers=auth)
    assert response.status_code == 200
    assert raw_json(response) == {
        "month": "2026-10", "monthlyIncome": 180000, "plannedExpenses": 150000,
        "leftAfterPlan": 30000, "demoSavings": 60000, "totalSpentSoFar": 118400,
        "dailyBudgetHealth": "normal",
    }  # fmt: skip
    # Without `month`, the current Kigali month.
    assert raw_json(client.get(f"{BASE}/overview", headers=auth))["month"] == "2026-10"


def test_overview_health_follows_the_pace(client: TestClient, auth: dict[str, str]) -> None:
    with_plan(client, auth)
    add(client, auth, amount=126_000, date="2026-10-20T08:00:00Z")  # pace at day 26: 125,806
    assert raw_json(client.get(f"{BASE}/overview", headers=auth))["dailyBudgetHealth"] == "caution"
    add(client, auth, amount=25_000, date="2026-10-21T08:00:00Z")  # 151,000 > 150,000
    assert raw_json(client.get(f"{BASE}/overview", headers=auth))["dailyBudgetHealth"] == "exceeded"


def test_overview_without_a_plan_is_null_not_zero(client: TestClient, auth: dict[str, str]) -> None:
    add(client, auth, amount=1_000, date="2026-10-01T08:00:00Z")
    response = client.get(f"{BASE}/overview", headers=auth)
    assert raw_json(response) == {
        "month": "2026-10", "monthlyIncome": 180000, "plannedExpenses": None,
        "leftAfterPlan": None, "demoSavings": None, "totalSpentSoFar": 1000,
        "dailyBudgetHealth": None,
    }  # fmt: skip
    assert '"plannedExpenses":null' in response.text


def test_months_are_kigali_calendar_months(client: TestClient, auth: dict[str, str]) -> None:
    add(client, auth, amount=700, date="2026-09-30T22:30:00Z")  # 00:30 on 1 Oct in Kigali
    add(client, auth, amount=300, date="2026-09-30T21:30:00Z")  # 23:30 on 30 Sep in Kigali
    october = raw_json(client.get(f"{BASE}/overview?month=2026-10", headers=auth))
    september = raw_json(client.get(f"{BASE}/overview?month=2026-09", headers=auth))
    assert (october["totalSpentSoFar"], september["totalSpentSoFar"]) == (700, 300)


@pytest.mark.parametrize(
    ("query", "error"),
    [
        ("month=2026-13", ("month", "invalid_format")),
        ("month=2026-1", ("month", "invalid_format")),
        ("month=26-10", ("month", "invalid_format")),
        ("month=2026-10-01", ("month", "too_long")),
        ("month=2026-11", ("month", "out_of_range")),  # after the current month
        ("month=1999-12", ("month", "out_of_range")),
    ],
)
def test_month_validation(client: TestClient, auth: dict[str, str], query: str,
                          error: tuple[str, str]) -> None:  # fmt: skip
    for path in ("overview", "daily-trend", "burn-rate", "transactions"):
        assert_problem(client.get(f"{BASE}/{path}?{query}", headers=auth), 422, "validation", error)
    assert_problem(client.get(f"{BASE}/overview?period=2026-10", headers=auth), 400,
                   "unknown-parameter")  # fmt: skip


# --- POST /transactions (PDF page 6) ---


def test_post_reproduces_the_pdf_example(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    add(client, auth, amount=100_000, date="2026-10-10T08:00:00Z")
    add(client, auth, amount=18_400, date="2026-10-20T08:00:00Z")
    response = client.post(TX, json=PDF_POST, headers=auth)
    assert response.status_code == 201
    data = raw_json(response)
    assert set(data) == {"id", "status", "amount", "newMonthlySpentTotal"}
    assert (data["status"], data["amount"], data["newMonthlySpentTotal"]) == (
        "recorded", 9500, 127900,
    )  # fmt: skip
    assert data["id"].startswith("tx_") and len(data["id"]) == 29
    with test_database.read_only_session() as session:
        row = session.get(TrackerTransaction, data["id"])
        assert row is not None
        assert (row.type, row.title, row.category, row.note, row.amount) == (
            "expense", "Cooking gas refill (6kg)", "utilities", "Gasabo local depot", 9500,
        )  # fmt: skip
        assert row.occurred_at == datetime(2026, 10, 26, 14, 30, tzinfo=UTC)


def test_income_does_not_count_as_spending(client: TestClient, auth: dict[str, str]) -> None:
    add(client, auth, amount=4_000)
    data = add(client, auth, type="income", category="mobile_money", title="Salary", amount=90_000)
    assert data["newMonthlySpentTotal"] == 4_000


def test_post_normalises_text_and_time(client: TestClient, auth: dict[str, str]) -> None:
    created = add(client, auth, title="  Bus fare  ", note="   ",
                  date="2026-10-26T17:45:30.987+02:00")  # fmt: skip
    item = raw_json(client.get(f"{TX}?date=2026-10-26", headers=auth))["items"][0]
    assert item["id"] == created["id"]
    assert (item["title"], item["note"], item["date"]) == ("Bus fare", None, "2026-10-26T15:45:30Z")


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"type": "transfer"}, ("type", "unknown_value")),
        ({"category": "mobile_money"}, ("category", "unknown_value")),  # an income category
        ({"type": "income"}, ("category", "unknown_value")),  # utilities is an expense category
        ({"category": "rent"}, ("category", "unknown_value")),
        ({"amount": 0}, ("amount", "out_of_range")),
        ({"amount": -5}, ("amount", "out_of_range")),
        ({"amount": 100_000_001}, ("amount", "out_of_range")),
        ({"title": ""}, ("title", "too_short")),
        ({"title": "   "}, ("title", "too_short")),
        ({"title": "x" * 121}, ("title", "too_long")),
        ({"title": "Gas\x00refill"}, ("title", "invalid_format")),
        ({"title": "Gas\nrefill"}, ("title", "invalid_format")),
        ({"note": "x" * 281}, ("note", "too_long")),
        ({"note": "depot\x00"}, ("note", "invalid_format")),
        ({"date": "2026-10-26T14:30:00"}, ("date", "invalid_format")),  # no zone
        ({"date": "2026-10-26"}, ("date", "invalid_format")),
        ({"date": 1793030400}, ("date", "invalid_format")),  # not a string
        ({"date": "2026-10-26T14:30:00Z\u200b"}, ("date", "invalid_format")),
        ({"date": "2026-10-26T16:06:00Z"}, ("date", "out_of_range")),  # > 5 min in the future
        ({"date": "1999-12-31T23:59:59Z"}, ("date", "out_of_range")),
        ({"iconType": "food"}, ("iconType", "unknown_field")),
        ({"id": "tx_x"}, ("id", "unknown_field")),
    ],
)
def test_post_validation(client: TestClient, auth: dict[str, str], test_database: Database,
                         change: dict[str, object], error: tuple[str, str]) -> None:  # fmt: skip
    response = client.post(TX, json={**PDF_POST, **change}, headers=auth)
    assert_problem(response, 422, "validation", error)
    assert count(test_database) == 0


@pytest.mark.parametrize("field", ["type", "title", "category", "amount", "date"])
def test_post_requires_every_field_but_note(client: TestClient, auth: dict[str, str],
                                            field: str) -> None:  # fmt: skip
    body = {k: v for k, v in PDF_POST.items() if k != field}
    assert_problem(client.post(TX, json=body, headers=auth), 422, "validation", (field, "required"))
    body = {k: v for k, v in PDF_POST.items() if k != "note"}
    assert client.post(TX, json=body, headers=auth).status_code == 201


@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_post_amount_must_be_an_integer(client: TestClient, auth: dict[str, str],
                                        value: object) -> None:  # fmt: skip
    response = client.post(TX, json={**PDF_POST, "amount": value}, headers=auth)
    assert_problem(response, 422, "validation", ("amount", "not_integer"))


def test_a_date_within_the_clock_skew_is_accepted(client: TestClient, auth: dict[str, str]) -> None:
    assert client.post(TX, json={**PDF_POST, "date": "2026-10-26T16:04:59Z"},
                       headers=auth).status_code == 201  # fmt: skip


# --- Idempotency-Key ---


def test_a_retry_with_the_same_key_records_once(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    headers = {**auth, "Idempotency-Key": "pos-7f3a-0001"}
    first = client.post(TX, json=PDF_POST, headers=headers)
    second = client.post(TX, json=PDF_POST, headers=headers)
    assert first.status_code == second.status_code == 201
    assert raw_json(first) == raw_json(second)
    assert count(test_database) == 1
    # Another key, or no key, is another transaction.
    other_key = {**auth, "Idempotency-Key": "k2"}
    assert client.post(TX, json=PDF_POST, headers=other_key).status_code == 201
    assert client.post(TX, json=PDF_POST, headers=auth).status_code == 201
    assert count(test_database) == 3


def test_reusing_a_key_for_another_body_is_a_conflict(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    headers = {**auth, "Idempotency-Key": "k1"}
    assert client.post(TX, json=PDF_POST, headers=headers).status_code == 201
    response = client.post(TX, json={**PDF_POST, "amount": 9600}, headers=headers)
    assert_problem(response, 409, "idempotency-key-reused")
    assert count(test_database) == 1


def test_keys_belong_to_one_account(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    other = register(client, "b@example.rw")
    first = raw_json(client.post(TX, json=PDF_POST, headers={**auth, "Idempotency-Key": "same"}))
    second = raw_json(client.post(TX, json=PDF_POST, headers={**other, "Idempotency-Key": "same"}))
    assert first["id"] != second["id"] and count(test_database) == 2


def test_concurrent_retries_record_once(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    headers = {**auth, "Idempotency-Key": "burst-1"}
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda _: client.post(TX, json=PDF_POST, headers=headers),
                                  range(8)))  # fmt: skip
    assert {r.status_code for r in responses} == {201}
    assert len({raw_json(r)["id"] for r in responses}) == 1
    assert count(test_database) == 1


# Raw bytes: a client can send any header byte, though httpx refuses non-ASCII `str` values.
@pytest.mark.parametrize("key", [b"", b"x" * 65, b"has space", "café".encode("latin-1")])
def test_idempotency_key_format(client: TestClient, auth: dict[str, str], key: bytes) -> None:
    headers = {name.encode(): value.encode() for name, value in auth.items()}
    headers[b"Idempotency-Key"] = key
    response = client.post(TX, json=PDF_POST, headers=headers)
    assert response.status_code == 422
    assert raw_json(response)["errors"][0]["field"] == "Idempotency-Key"


# --- GET /transactions (PDF page 5) ---


def test_list_reproduces_the_pdf_example(client: TestClient, auth: dict[str, str]) -> None:
    beans = add(client, auth, title="Beans & fresh vegetables", category="food", amount=3500,
                note=None, date="2026-10-07T10:30:00Z")  # fmt: skip
    bus = add(client, auth, title="Bus fare (Kimironko to Nyabugogo)", category="transport",
              amount=1000, note=None, date="2026-10-07T14:15:00Z")  # fmt: skip
    add(client, auth, amount=777, date="2026-10-08T09:00:00Z")  # another day
    response = client.get(f"{TX}?month=2026-10&date=2026-10-07", headers=auth)
    assert response.status_code == 200
    data = raw_json(response)
    assert set(data) == {"items", "dayTotalExpenses", "nextCursor"}
    assert data["items"] == [
        {"id": beans["id"], "type": "expense", "title": "Beans & fresh vegetables",
         "category": "food", "amount": 3500, "date": "2026-10-07T10:30:00Z", "iconType": "food",
         "note": None},
        {"id": bus["id"], "type": "expense", "title": "Bus fare (Kimironko to Nyabugogo)",
         "category": "transport", "amount": 1000, "date": "2026-10-07T14:15:00Z",
         "iconType": "transport", "note": None},
    ]  # fmt: skip
    assert (data["dayTotalExpenses"], data["nextCursor"]) == (4500, None)


def test_list_filters_and_orders(client: TestClient, auth: dict[str, str]) -> None:
    late = add(client, auth, amount=1, date="2026-10-20T08:00:00Z")
    early = add(client, auth, amount=2, date="2026-10-02T08:00:00Z")
    income = add(client, auth, type="income", category="side_gig", amount=3,
                 date="2026-10-10T08:00:00Z")  # fmt: skip
    add(client, auth, amount=4, date="2026-09-15T08:00:00Z")  # September
    ids = [i["id"] for i in raw_json(client.get(TX, headers=auth))["items"]]
    assert ids == [early["id"], income["id"], late["id"]]
    data = raw_json(client.get(f"{TX}?type=income", headers=auth))
    assert [i["id"] for i in data["items"]] == [income["id"]]
    assert data["items"][0]["iconType"] == "side_gig"
    assert data["dayTotalExpenses"] is None  # no `date` given
    # dayTotalExpenses counts the day's expenses whatever `type` filters.
    day = raw_json(client.get(f"{TX}?date=2026-10-10&type=income", headers=auth))
    assert day["dayTotalExpenses"] == 0 and len(day["items"]) == 1


def test_list_pages_with_a_cursor(client: TestClient, auth: dict[str, str]) -> None:
    created = [add(client, auth, amount=n + 1, date=f"2026-10-{n + 1:02d}T08:00:00Z")["id"]
               for n in range(5)]  # fmt: skip
    seen: list[str] = []
    url = f"{TX}?limit=2"
    while True:
        data = raw_json(client.get(url, headers=auth))
        seen += [i["id"] for i in data["items"]]
        if data["nextCursor"] is None:
            break
        url = f"{TX}?limit=2&cursor={data['nextCursor']}"
    assert seen == created


@pytest.mark.parametrize(
    ("query", "error"),
    [
        ("date=2026-10-32", ("date", "invalid_format")),
        ("date=07-10-2026", ("date", "invalid_format")),
        ("date=2026-10-27", ("date", "out_of_range")),  # tomorrow in Kigali
        ("month=2026-09&date=2026-10-07", ("date", "out_of_range")),
        ("type=transfer", ("type", "unknown_value")),
        ("limit=0", ("limit", "out_of_range")),
        ("limit=501", ("limit", "out_of_range")),
        ("limit=abc", ("limit", "not_integer")),
        ("cursor=bogus", ("cursor", "invalid_format")),
    ],
)
def test_list_validation(client: TestClient, auth: dict[str, str], query: str,
                         error: tuple[str, str]) -> None:  # fmt: skip
    assert_problem(client.get(f"{TX}?{query}", headers=auth), 422, "validation", error)


def test_households_never_see_each_other(client: TestClient, auth: dict[str, str]) -> None:
    mine = add(client, auth)
    other = register(client, "b@example.rw")
    assert raw_json(client.get(TX, headers=other))["items"] == []
    assert raw_json(client.get(f"{BASE}/overview", headers=other))["totalSpentSoFar"] == 0
    # Another household's id is "not found", never "forbidden".
    assert_problem(client.patch(f"{TX}/{mine['id']}", json={"amount": 1}, headers=other), 404,
                   "transaction-not-found")  # fmt: skip
    assert_problem(client.delete(f"{TX}/{mine['id']}", headers=other), 404, "transaction-not-found")
    assert raw_json(client.get(TX, headers=auth))["items"][0]["amount"] == 9500


# --- PATCH /transactions/{id} (the PDF's PUT has no body: contract extension) ---


def test_patch_changes_only_the_fields_sent(client: TestClient, auth: dict[str, str]) -> None:
    tx = add(client, auth)
    response = client.patch(f"{TX}/{tx['id']}", json={"amount": 9800, "note": None}, headers=auth)
    assert response.status_code == 200
    item = raw_json(response)
    assert set(item) == ITEM_KEYS
    assert (item["amount"], item["note"], item["title"], item["date"]) == (
        9800, None, "Cooking gas refill (6kg)", "2026-10-26T14:30:00Z",
    )  # fmt: skip
    assert raw_json(client.get(TX, headers=auth))["items"] == [item]


def test_patch_type_and_category_must_agree(client: TestClient, auth: dict[str, str]) -> None:
    tx = add(client, auth)
    url = f"{TX}/{tx['id']}"
    assert_problem(client.patch(url, json={"type": "income"}, headers=auth), 422, "validation",
                   ("category", "unknown_value"))  # fmt: skip
    assert_problem(client.patch(url, json={"category": "day_wage"}, headers=auth), 422,
                   "validation", ("category", "unknown_value"))  # fmt: skip
    both = client.patch(url, json={"type": "income", "category": "day_wage"}, headers=auth)
    assert both.status_code == 200 and raw_json(both)["iconType"] == "day_wage"


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"title": None}, ("title", "required")),
        ({"amount": None}, ("amount", "required")),
        ({"date": None}, ("date", "required")),
        ({"amount": 0}, ("amount", "out_of_range")),
        ({"date": "2026-10-27T08:00:00Z"}, ("date", "out_of_range")),
        ({"id": "tx_other"}, ("id", "unknown_field")),
    ],
)
def test_patch_validation(client: TestClient, auth: dict[str, str], change: dict[str, object],
                          error: tuple[str, str]) -> None:  # fmt: skip
    tx = add(client, auth)
    assert_problem(client.patch(f"{TX}/{tx['id']}", json=change, headers=auth), 422, "validation",
                   error)  # fmt: skip
    assert raw_json(client.get(TX, headers=auth))["items"][0]["amount"] == 9500  # unchanged


def test_patch_empty_body_and_unknown_ids(client: TestClient, auth: dict[str, str]) -> None:
    tx = add(client, auth)
    before = raw_json(client.get(TX, headers=auth))["items"][0]
    assert raw_json(client.patch(f"{TX}/{tx['id']}", json={}, headers=auth)) == before
    for unknown in ("tx_" + "0" * 26, "nope", "x" * 40):
        assert_problem(client.patch(f"{TX}/{unknown}", json={}, headers=auth), 404,
                       "transaction-not-found")  # fmt: skip


def test_put_is_not_routed(client: TestClient, auth: dict[str, str]) -> None:
    tx = add(client, auth)
    response = client.put(f"{TX}/{tx['id']}", json=PDF_POST, headers=auth)
    assert_problem(response, 405, "method-not-allowed")
    assert response.headers["allow"] == "DELETE, PATCH"


# --- DELETE /transactions/{id} ---


def test_delete(client: TestClient, auth: dict[str, str], test_database: Database) -> None:
    tx = add(client, auth)
    response = client.delete(f"{TX}/{tx['id']}", headers=auth)
    assert response.status_code == 204 and response.content == b""
    assert count(test_database) == 0
    assert_problem(client.delete(f"{TX}/{tx['id']}", headers=auth), 404, "transaction-not-found")


def test_deleting_an_account_deletes_its_transactions(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    add(client, auth)
    _clear(test_database)
    assert count(test_database) == 0


# --- GET /daily-trend (PDF page 6) and /burn-rate (contract extension) ---


def test_daily_trend_reproduces_the_pdf_example(client: TestClient, auth: dict[str, str]) -> None:
    spending = {"01": [5200], "02": [4100], "07": [3500, 1000, 2000], "25": [3800]}
    for day, amounts in spending.items():
        for amount in amounts:
            add(client, auth, amount=amount, date=f"2026-10-{day}T08:00:00Z")
    add(client, auth, type="income", category="day_wage", amount=9_999,
        date="2026-10-03T08:00:00Z")  # income is not spending  # fmt: skip
    response = client.get(f"{BASE}/daily-trend", headers=auth)
    assert response.status_code == 200
    assert raw_json(response) == {
        "month": "2026-10",
        "points": [
            {"date": "2026-10-01", "total": 5200}, {"date": "2026-10-02", "total": 4100},
            {"date": "2026-10-07", "total": 6500}, {"date": "2026-10-25", "total": 3800},
        ],
    }  # fmt: skip
    assert raw_json(client.get(f"{BASE}/daily-trend?month=2026-09", headers=auth))["points"] == []


def test_burn_rate(client: TestClient, auth: dict[str, str]) -> None:
    with_plan(client, auth)
    add(client, auth, amount=100_000, date="2026-10-10T08:00:00Z")
    add(client, auth, amount=18_400, date="2026-10-20T08:00:00Z")
    assert raw_json(client.get(f"{BASE}/burn-rate", headers=auth)) == {
        "month": "2026-10", "daysElapsed": 26, "daysInMonth": 31, "totalSpentSoFar": 118400,
        "averageDailySpend": 4554, "projectedMonthSpend": 141169, "plannedExpenses": 150000,
        "projectedVsPlan": -8831,
    }  # fmt: skip
    september = raw_json(client.get(f"{BASE}/burn-rate?month=2026-09", headers=auth))
    assert (september["daysElapsed"], september["averageDailySpend"]) == (30, 0)


def test_burn_rate_without_a_plan(client: TestClient, auth: dict[str, str]) -> None:
    data = raw_json(client.get(f"{BASE}/burn-rate", headers=auth))
    assert (data["plannedExpenses"], data["projectedVsPlan"], data["projectedMonthSpend"]) == (
        None, None, 0,
    )  # fmt: skip


def test_month_boundary_from_the_clock(db_settings: Settings, test_database: Database) -> None:
    """At 23:30 UTC on 31 October it is already November in Kigali."""
    _clear(test_database)
    late = datetime(2026, 10, 31, 23, 30, tzinfo=UTC)
    for c in _client(db_settings, test_database, lambda: late):
        headers = register(c)
        assert raw_json(c.get(f"{BASE}/overview", headers=headers))["month"] == "2026-11"
        assert raw_json(c.get(f"{BASE}/burn-rate", headers=headers))["daysElapsed"] == 1
    _clear(test_database)


# --- Authentication, documentation, CORS ---


ROUTES: Final = [
    ("GET", f"{BASE}/overview"), ("GET", TX), ("POST", TX),
    ("PATCH", f"{TX}/tx_{'0' * 26}"), ("DELETE", f"{TX}/tx_{'0' * 26}"),
    ("GET", f"{BASE}/daily-trend"), ("GET", f"{BASE}/burn-rate"),
]  # fmt: skip


@pytest.mark.parametrize(("method", "path"), ROUTES)
def test_every_route_needs_a_token(client: TestClient, method: str, path: str) -> None:
    for headers in ({}, {"Authorization": "Bearer not.a.jwt"}):
        response = client.request(method, path, json=PDF_POST, headers=headers)
        assert_problem(response, 401, "not-authenticated")
        assert response.headers["www-authenticate"] == "Bearer"


def test_openapi_documents_the_tracker(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    assert set(paths[TX]) == {"get", "post"}
    assert set(paths[f"{TX}/{{id}}"]) == {"patch", "delete"}
    for path in (f"{BASE}/overview", f"{BASE}/daily-trend", f"{BASE}/burn-rate"):
        assert set(paths[path]) == {"get"}
    for path, operations in paths.items():
        if path.startswith(BASE):
            for operation in operations.values():
                assert operation["security"] == [{"bearerToken": []}]
    assert set(paths[TX]["post"]["responses"]) == {"201", "400", "401", "409", "422", "500", "503"}
    assert set(paths[f"{TX}/{{id}}"]["delete"]["responses"]) == {
        "204", "400", "401", "404", "422", "500", "503",
    }  # fmt: skip
    schemas = spec["components"]["schemas"]
    assert set(schemas["TrackerOverviewResponse"]["properties"]) == {
        "month", "monthlyIncome", "plannedExpenses", "leftAfterPlan", "demoSavings",
        "totalSpentSoFar", "dailyBudgetHealth",
    }  # fmt: skip
    assert set(schemas["TransactionCreate"]["properties"]) == set(PDF_POST)
    assert set(schemas["TransactionCreatedResponse"]["properties"]) == {
        "id", "status", "amount", "newMonthlySpentTotal",
    }  # fmt: skip
    assert set(schemas["TransactionItem"]["properties"]) == ITEM_KEYS
    assert set(schemas["DailyTrendResponse"]["properties"]) == {"month", "points"}


def test_cors_preflight_allows_delete_and_idempotency_key(client: TestClient) -> None:
    response = client.options(TX, headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "DELETE",
        "Access-Control-Request-Headers": "authorization,idempotency-key,content-type",
    })  # fmt: skip
    assert response.status_code == 200
    assert "DELETE" in response.headers["access-control-allow-methods"]
    assert "idempotency-key" in response.headers["access-control-allow-headers"].lower()


def test_a_retry_that_loses_the_insert_race_is_answered_as_a_replay(
    client: TestClient, auth: dict[str, str], test_database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # fmt: skip
    """Two retries both pass the key lookup; the unique constraint lets one insert win."""
    headers = {**auth, "Idempotency-Key": "race-1"}
    first = raw_json(client.post(TX, json=PDF_POST, headers=headers))
    real_find = TrackerRepository.find_by_idempotency_key
    calls: list[str] = []

    def stale_first_lookup(self: TrackerRepository, account_id: str, key: str) -> Any:
        calls.append(key)
        return None if len(calls) == 1 else real_find(self, account_id, key)

    monkeypatch.setattr(TrackerRepository, "find_by_idempotency_key", stale_first_lookup)
    second = client.post(TX, json=PDF_POST, headers=headers)
    assert second.status_code == 201 and raw_json(second)["id"] == first["id"]
    assert len(calls) == 2 and count(test_database) == 1
    # The loser of the race with a different body is the same 409 as a plain reuse.
    calls.clear()
    other = client.post(TX, json={**PDF_POST, "amount": 1}, headers=headers)
    assert_problem(other, 409, "idempotency-key-reused")


def test_other_insert_errors_are_not_mistaken_for_a_key_race(test_database: Database) -> None:
    row = TrackerTransaction(
        id="tx_" + "0" * 26, account_id="usr_" + "0" * 26, type="expense", category="food",
        title="x", amount=1, occurred_at=NOW,
    )  # fmt: skip
    with test_database.session() as session, pytest.raises(IntegrityError):
        TrackerRepository(session).add(row)  # no such account: a foreign-key error


def test_an_impossible_calendar_date_is_rejected(client: TestClient, auth: dict[str, str]) -> None:
    response = client.post(TX, json={**PDF_POST, "date": "2026-02-30T10:00:00Z"}, headers=auth)
    assert_problem(response, 422, "validation", ("date", "invalid_format"))


def test_a_replay_reports_the_transaction_as_it_is_now(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    """F1 (contract §11.10): same id, nothing stored twice, current state (not a stored copy)."""
    headers = {**auth, "Idempotency-Key": "replay-after-edit"}
    first = raw_json(client.post(TX, json=PDF_POST, headers=headers))
    assert (first["amount"], first["newMonthlySpentTotal"]) == (9500, 9500)
    client.patch(f"{TX}/{first['id']}", json={"amount": 9800}, headers=auth)
    retry = client.post(TX, json=PDF_POST, headers=headers)
    assert retry.status_code == 201
    assert raw_json(retry) == {"id": first["id"], "status": "recorded", "amount": 9800,
                               "newMonthlySpentTotal": 9800}  # fmt: skip
    assert count(test_database) == 1


def test_known_limitation_a_retry_after_a_delete_records_again(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    """F2, documented in contract §11.10 and pending an owner decision (key retention, Q-13).

    The key lives on its transaction, so deleting the transaction frees it. If the owner
    decides to keep used keys after a delete, this test must change with that decision.
    """
    headers = {**auth, "Idempotency-Key": "retry-after-delete"}
    first = raw_json(client.post(TX, json=PDF_POST, headers=headers))
    assert client.delete(f"{TX}/{first['id']}", headers=auth).status_code == 204
    again = client.post(TX, json=PDF_POST, headers=headers)
    assert again.status_code == 201 and raw_json(again)["id"] != first["id"]
    assert count(test_database) == 1
