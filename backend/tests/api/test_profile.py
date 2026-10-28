"""Household profile: GET and PATCH /api/v1/user/profile (contract §11.9, MISSING_APIS.pdf page 4).

The PDF's GET example fixes the response; its PUT has no body, so PATCH takes the editable part of
the GET shape, every field optional (owner direction: PATCH instead of PUT).
"""

import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Final

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, select

from app.core.config import Settings
from app.core.errors import NotAuthenticatedError
from app.db.session import Database
from app.main import create_app
from app.models import HouseholdAccount
from app.schemas.profile import ProfilePatch
from app.services.current_account import CurrentAccount
from app.services.profile_service import ProfileService
from tests.helpers import NOT_INTEGER_BODY_VALUES, assert_problem, raw_json

PROFILE: Final = "/api/v1/user/profile"
REGISTER: Final = "/api/v1/auth/register"
LOGIN: Final = "/api/v1/auth/login"
SECRET: Final = "test-only-signing-key-0123456789abcdef"  # never a real key
PASSWORD: Final = "SecurePassword123!"
# The PDF's register request (page 3), so the profile starts from the PDF's own household.
PDF_REGISTER: Final[dict[str, Any]] = {
    "identifier": "+250788123456",
    "password": PASSWORD,
    "profile": {
        "district": "gasabo",
        "householdSize": 4,
        "monthlyIncome": 180000,
        "currency": "RWF",
        "preferredLanguage": "RW",
    },
}
# The PDF's GET example (page 4) has exactly these keys.
PDF_PROFILE_KEYS: Final = {
    "id", "district", "householdSize", "monthlyIncome", "plannedEssentials", "savingsBuffer",
    "preferredLanguage",
}  # fmt: skip


def _client(settings: Settings, database: Database, secret: str | None) -> Iterator[TestClient]:
    configured = settings.model_copy(
        update={"jwt_secret_key": SecretStr(secret) if secret else None}
    )
    app = create_app("test", settings=configured, database=database)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def _clear(database: Database) -> None:
    with database.session() as session:
        session.execute(delete(HouseholdAccount))
        session.commit()


@pytest.fixture
def accounts(test_database: Database) -> Iterator[None]:
    """Each test starts and ends with no accounts (test database only)."""
    _clear(test_database)
    yield
    _clear(test_database)


@pytest.fixture
def client(db_settings: Settings, test_database: Database, accounts: None) -> Iterator[TestClient]:
    yield from _client(db_settings, test_database, SECRET)


@pytest.fixture
def registered(client: TestClient) -> dict[str, Any]:
    """The PDF's household, registered: its token and id."""
    data: dict[str, Any] = raw_json(client.post(REGISTER, json=PDF_REGISTER))
    return data


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def row(database: Database, account_id: str) -> HouseholdAccount:
    with database.read_only_session() as session:
        account = session.scalars(
            select(HouseholdAccount).where(HouseholdAccount.id == account_id)
        ).one()
        session.expunge_all()
    return account


def assert_not_authenticated(response: Any) -> None:
    assert_problem(response, 401, "not-authenticated")
    assert response.headers["www-authenticate"] == "Bearer"


# --- GET ---


def test_get_profile_has_the_pdf_shape(client: TestClient, registered: dict[str, Any]) -> None:
    response = client.get(PROFILE, headers=auth(registered["token"]))
    assert response.status_code == 200
    data = raw_json(response)
    assert set(data) == PDF_PROFILE_KEYS
    # Register does not collect plannedEssentials or savingsBuffer: null, never an invented 0.
    assert data == {
        "id": registered["user"]["id"], "district": "gasabo", "householdSize": 4,
        "monthlyIncome": 180000, "plannedEssentials": None, "savingsBuffer": None,
        "preferredLanguage": "RW",
    }  # fmt: skip
    assert '"plannedEssentials":null' in response.text


def test_get_profile_works_with_a_login_token(
    client: TestClient, registered: dict[str, Any]
) -> None:
    credentials = {"identifier": "+250788123456", "password": PASSWORD}
    login = raw_json(client.post(LOGIN, json=credentials))
    response = client.get(PROFILE, headers=auth(login["token"]))
    assert response.status_code == 200 and raw_json(response)["id"] == registered["user"]["id"]


def test_get_profile_after_the_pdf_values_are_set(
    client: TestClient, registered: dict[str, Any]
) -> None:
    """With the two values set, GET returns the PDF's example exactly (except the id)."""
    token = registered["token"]
    patch = {"plannedEssentials": 150000, "savingsBuffer": 60000}
    assert client.patch(PROFILE, json=patch, headers=auth(token)).status_code == 200
    data = raw_json(client.get(PROFILE, headers=auth(token)))
    assert {k: v for k, v in data.items() if k != "id"} == {
        "district": "gasabo", "householdSize": 4, "monthlyIncome": 180000,
        "plannedEssentials": 150000, "savingsBuffer": 60000, "preferredLanguage": "RW",
    }  # fmt: skip


def test_get_profile_refuses_query_parameters(
    client: TestClient, registered: dict[str, Any]
) -> None:
    response = client.get(PROFILE + "?fields=all", headers=auth(registered["token"]))
    assert_problem(response, 400, "unknown-parameter")


# --- PATCH ---


@pytest.mark.parametrize(
    ("patch", "expected"),
    [
        ({"district": "musanze"}, {"district": "musanze"}),
        ({"householdSize": 6}, {"householdSize": 6}),
        ({"monthlyIncome": 0}, {"monthlyIncome": 0}),
        ({"plannedEssentials": 150000}, {"plannedEssentials": 150000}),
        ({"savingsBuffer": 60000}, {"savingsBuffer": 60000}),
        ({"preferredLanguage": "EN"}, {"preferredLanguage": "EN"}),
        (
            {"householdSize": 20, "monthlyIncome": 100_000_000, "plannedEssentials": 0},
            {"householdSize": 20, "monthlyIncome": 100_000_000, "plannedEssentials": 0},
        ),
    ],
)
def test_patch_changes_only_the_fields_sent(
    client: TestClient, registered: dict[str, Any], test_database: Database,
    patch: dict[str, object], expected: dict[str, object],
) -> None:  # fmt: skip
    token, account_id = registered["token"], registered["user"]["id"]
    before = raw_json(client.get(PROFILE, headers=auth(token)))
    response = client.patch(PROFILE, json=patch, headers=auth(token))
    assert response.status_code == 200
    data = raw_json(response)
    assert set(data) == PDF_PROFILE_KEYS
    assert data == {**before, **expected}
    # The response is what was stored, and a later GET agrees.
    assert raw_json(client.get(PROFILE, headers=auth(token))) == data
    stored = row(test_database, account_id)
    assert stored.updated_at is not None
    # Never part of the profile: unchanged.
    assert (stored.identifier, stored.currency) == ("+250788123456", "RWF")


def test_patch_null_clears_the_two_optional_values(
    client: TestClient, registered: dict[str, Any]
) -> None:
    token = registered["token"]
    client.patch(PROFILE, json={"plannedEssentials": 150000, "savingsBuffer": 60000},
                 headers=auth(token))  # fmt: skip
    data = raw_json(client.patch(PROFILE, json={"savingsBuffer": None}, headers=auth(token)))
    assert (data["plannedEssentials"], data["savingsBuffer"]) == (150000, None)


def test_an_empty_patch_changes_nothing(
    client: TestClient, registered: dict[str, Any], test_database: Database
) -> None:
    token = registered["token"]
    before = raw_json(client.get(PROFILE, headers=auth(token)))
    response = client.patch(PROFILE, json={}, headers=auth(token))
    assert response.status_code == 200 and raw_json(response) == before
    assert row(test_database, registered["user"]["id"]).updated_at is None  # no write at all


NON_NULLABLE: Final = ["district", "householdSize", "monthlyIncome", "preferredLanguage"]


@pytest.mark.parametrize("field", NON_NULLABLE)
def test_patch_refuses_null_for_fields_that_always_have_a_value(
    client: TestClient, registered: dict[str, Any], field: str
) -> None:
    response = client.patch(PROFILE, json={field: None}, headers=auth(registered["token"]))
    assert_problem(response, 422, "validation", (field, "required"))


@pytest.mark.parametrize(
    ("patch", "error"),
    [
        ({"householdSize": 0}, ("householdSize", "out_of_range")),
        ({"householdSize": 21}, ("householdSize", "out_of_range")),
        ({"monthlyIncome": -1}, ("monthlyIncome", "out_of_range")),
        ({"monthlyIncome": 100_000_001}, ("monthlyIncome", "out_of_range")),
        ({"plannedEssentials": -1}, ("plannedEssentials", "out_of_range")),
        ({"savingsBuffer": 100_000_001}, ("savingsBuffer", "out_of_range")),
        ({"preferredLanguage": "FR"}, ("preferredLanguage", "unknown_value")),
        ({"preferredLanguage": "rw"}, ("preferredLanguage", "unknown_value")),
        ({"district": "x" * 33}, ("district", "too_long")),
        ({"savingsBuffer": "60000"}, ("savingsBuffer", "not_integer")),
        # Not profile fields: refused, never silently ignored or changed.
        ({"id": "usr_" + "0" * 26}, ("id", "unknown_field")),
        ({"identifier": "+250788000000"}, ("identifier", "unknown_field")),
        ({"password": "AnotherPassword123"}, ("password", "unknown_field")),
        ({"currency": "USD"}, ("currency", "unknown_field")),
        ({"household_size": 5}, ("household_size", "unknown_field")),  # wire names are camelCase
    ],
)
def test_patch_validation(
    client: TestClient, registered: dict[str, Any], test_database: Database,
    patch: dict[str, object], error: tuple[str, str],
) -> None:  # fmt: skip
    response = client.patch(PROFILE, json=patch, headers=auth(registered["token"]))
    assert_problem(response, 422, "validation", error)
    assert row(test_database, registered["user"]["id"]).updated_at is None  # nothing written


@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_patch_money_must_be_an_integer(
    client: TestClient, registered: dict[str, Any], value: object
) -> None:
    response = client.patch(PROFILE, json={"plannedEssentials": value},
                            headers=auth(registered["token"]))  # fmt: skip
    assert_problem(response, 422, "validation", ("plannedEssentials", "not_integer"))


def test_patch_shape_errors(client: TestClient, registered: dict[str, Any]) -> None:
    headers = {**auth(registered["token"]), "Content-Type": "application/json"}
    assert_problem(client.patch(PROFILE, content=b"{", headers=headers), 400, "malformed-request")
    assert_problem(client.patch(PROFILE + "?x=1", json={}, headers=auth(registered["token"])),
                   400, "unknown-parameter")  # fmt: skip
    assert_problem(client.patch(PROFILE, json=[1], headers=auth(registered["token"])), 422,
                   "validation")  # fmt: skip


def test_patch_unknown_district_is_404_after_validation(
    client: TestClient, registered: dict[str, Any], test_database: Database
) -> None:
    token = registered["token"]
    assert_problem(client.patch(PROFILE, json={"district": "atlantis"}, headers=auth(token)), 404,
                   "district-not-found")  # fmt: skip
    # District codes are case-sensitive (contract §5).
    assert_problem(client.patch(PROFILE, json={"district": "GASABO"}, headers=auth(token)), 404,
                   "district-not-found")  # fmt: skip
    # Validation first: an invalid field beats an unknown district.
    both = {"district": "atlantis", "householdSize": 0}
    assert_problem(client.patch(PROFILE, json=both, headers=auth(token)), 422, "validation",
                   ("householdSize", "out_of_range"))  # fmt: skip
    # The failed district change wrote nothing, not even the other field.
    mixed = {"district": "atlantis", "householdSize": 7}
    client.patch(PROFILE, json=mixed, headers=auth(token))
    assert row(test_database, registered["user"]["id"]).household_size == 4


def test_put_is_not_routed(client: TestClient, registered: dict[str, Any]) -> None:
    """The PDF's PUT is replaced by PATCH (owner direction)."""
    response = client.put(PROFILE, json={"householdSize": 5}, headers=auth(registered["token"]))
    assert_problem(response, 405, "method-not-allowed")
    assert set(response.headers["allow"].replace(" ", "").split(",")) == {"GET", "PATCH"}


def test_concurrent_patches_of_different_fields_both_survive(
    client: TestClient, registered: dict[str, Any]
) -> None:
    """One UPDATE per request sets only its own fields: no lost update between them."""
    token = registered["token"]
    patches = [{"plannedEssentials": 150000}, {"savingsBuffer": 60000}, {"householdSize": 5},
               {"preferredLanguage": "EN"}] * 3  # fmt: skip
    with ThreadPoolExecutor(max_workers=6) as pool:
        statuses = list(pool.map(
            lambda body: client.patch(PROFILE, json=body, headers=auth(token)).status_code,
            patches,
        ))  # fmt: skip
    assert statuses == [200] * len(patches)
    data = raw_json(client.get(PROFILE, headers=auth(token)))
    assert (data["plannedEssentials"], data["savingsBuffer"], data["householdSize"],
            data["preferredLanguage"]) == (150000, 60000, 5, "EN")  # fmt: skip


def test_patches_are_isolated_between_accounts(
    client: TestClient, registered: dict[str, Any]
) -> None:
    other = raw_json(client.post(REGISTER, json={**PDF_REGISTER, "identifier": "b@example.rw"}))
    client.patch(PROFILE, json={"householdSize": 9}, headers=auth(other["token"]))
    assert raw_json(client.get(PROFILE, headers=auth(registered["token"])))["householdSize"] == 4
    assert raw_json(client.get(PROFILE, headers=auth(other["token"])))["householdSize"] == 9


# --- Authentication (both methods) ---


@pytest.mark.parametrize("method", ["GET", "PATCH"])
def test_both_methods_need_a_valid_token(
    client: TestClient, registered: dict[str, Any], test_database: Database, method: str
) -> None:
    account_id = registered["user"]["id"]
    now = int(time.time())
    valid = {"sub": account_id, "iat": now, "exp": now + 3600}
    bad = {
        "missing": {},
        "malformed": {"Authorization": "Bearer not.a.jwt"},
        "other scheme": {"Authorization": "Basic dXNlcjpwYXNz"},
        "wrong key": auth(jwt.encode(valid, "another-key-another-key-another-key", "HS256")),
        "expired": auth(jwt.encode({**valid, "iat": now - 7200, "exp": now - 3600}, SECRET)),
        "unknown account": auth(jwt.encode({**valid, "sub": "usr_" + "0" * 26}, SECRET)),
    }
    for name, headers in bad.items():
        # Even an invalid body gets the 401: an unauthenticated caller learns nothing more.
        response = client.request(method, PROFILE, json={"householdSize": 0}, headers=headers)
        assert_not_authenticated(response)
        assert name and SECRET not in response.text
    assert row(test_database, account_id).updated_at is None


def test_a_deleted_account_token_stops_working(
    client: TestClient, registered: dict[str, Any], test_database: Database
) -> None:
    token = registered["token"]
    assert client.get(PROFILE, headers=auth(token)).status_code == 200
    with test_database.session() as session:
        session.execute(delete(HouseholdAccount))
        session.commit()
    assert_not_authenticated(client.get(PROFILE, headers=auth(token)))
    assert_not_authenticated(client.patch(PROFILE, json={"householdSize": 5}, headers=auth(token)))


def test_without_a_signing_key_the_profile_is_unavailable(
    db_settings: Settings, test_database: Database, accounts: None
) -> None:
    for unconfigured in _client(db_settings, test_database, None):
        for method in ("GET", "PATCH"):
            response = unconfigured.request(method, PROFILE, json={}, headers=auth("x.y.z"))
            assert_problem(response, 503, "auth-not-configured")


# --- Documentation ---


def test_openapi_documents_the_pdf_profile_and_the_bearer_scheme(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    path = spec["paths"][PROFILE]
    assert set(path) == {"get", "patch"}
    assert set(path["get"]["responses"]) == {"200", "400", "401", "500", "503"}
    assert set(path["patch"]["responses"]) == {"200", "400", "401", "404", "422", "500", "503"}
    for method in ("get", "patch"):
        assert path[method]["security"] == [{"bearerToken": []}]
    assert spec["components"]["securitySchemes"]["bearerToken"] == {
        "type": "http", "scheme": "bearer",
    }  # fmt: skip
    schemas = spec["components"]["schemas"]
    assert set(schemas["ProfileResponse"]["properties"]) == PDF_PROFILE_KEYS
    assert set(schemas["ProfilePatch"]["properties"]) == PDF_PROFILE_KEYS - {"id"}
    assert not schemas["ProfilePatch"].get("required")  # every PATCH field is optional


def test_cors_preflight_allows_patch_with_a_token(client: TestClient) -> None:
    response = client.options(PROFILE, headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "PATCH",
        "Access-Control-Request-Headers": "authorization,content-type",
    })  # fmt: skip
    assert response.status_code == 200
    assert "PATCH" in response.headers["access-control-allow-methods"]
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_an_account_deleted_after_the_token_check_writes_nothing(
    test_database: Database, accounts: None
) -> None:
    """The race between the token check and the UPDATE: 401, as for any vanished account."""
    vanished = CurrentAccount(
        id="usr_" + "0" * 26, identifier="+250788000009", district="gasabo", household_size=4,
        monthly_income=0, currency="RWF", preferred_language="EN", planned_essentials=None,
        savings_buffer=None,
    )  # fmt: skip
    patch = ProfilePatch.model_validate({"householdSize": 5})
    with test_database.session() as session, pytest.raises(NotAuthenticatedError):
        ProfileService(session).update(vanished, patch)
    with test_database.read_only_session() as session:
        assert session.scalars(select(HouseholdAccount)).first() is None
