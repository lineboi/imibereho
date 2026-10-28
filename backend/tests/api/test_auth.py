"""Household accounts: register and login (contract §11.8, MISSING_APIS.pdf page 4)."""

import copy
import re
import time
from collections.abc import Iterator
from typing import Any, Final

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.db.session import Database
from app.main import create_app
from app.models import HouseholdAccount
from app.repositories.account_repository import AccountRepository
from app.services.current_account import CurrentAccountDep
from tests.helpers import NOT_INTEGER_BODY_VALUES, assert_problem, raw_json

REGISTER: Final = "/api/v1/auth/register"
LOGIN: Final = "/api/v1/auth/login"
SECRET: Final = "test-only-signing-key-0123456789abcdef"  # never a real key
# The PDF's register request, exactly.
PDF_REGISTER: Final[dict[str, Any]] = {
    "identifier": "+250788123456",
    "password": "SecurePassword123!",
    "profile": {
        "district": "gasabo",
        "householdSize": 4,
        "monthlyIncome": 180000,
        "currency": "RWF",
        "preferredLanguage": "RW",
    },
}
PDF_LOGIN: Final = {"identifier": "+250788123456", "password": "SecurePassword123!"}
ACCOUNT_ID: Final = r"usr_[0-9A-HJKMNP-TV-Z]{26}"


def _client(settings: Settings, database: Database, secret: str | None) -> Iterator[TestClient]:
    configured = settings.model_copy(
        update={"jwt_secret_key": SecretStr(secret) if secret else None}
    )
    app = create_app("test", settings=configured, database=database)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def accounts(test_database: Database) -> Iterator[None]:
    """Each test starts and ends with no accounts (test database only)."""
    with test_database.session() as session:
        session.execute(delete(HouseholdAccount))
        session.commit()
    yield
    with test_database.session() as session:
        session.execute(delete(HouseholdAccount))
        session.commit()


@pytest.fixture
def auth_client(
    db_settings: Settings, test_database: Database, accounts: None
) -> Iterator[TestClient]:
    yield from _client(db_settings, test_database, SECRET)


@pytest.fixture
def unconfigured_client(
    db_settings: Settings, test_database: Database, accounts: None
) -> Iterator[TestClient]:
    yield from _client(db_settings, test_database, None)


def stored(database: Database) -> list[HouseholdAccount]:
    with database.read_only_session() as session:
        accounts = list(session.scalars(select(HouseholdAccount)))
        session.expunge_all()  # detached before the closing rollback, so they stay readable
    return accounts


def with_profile(**changes: object) -> dict[str, Any]:
    body = copy.deepcopy(PDF_REGISTER)
    body["profile"].update(changes)
    return body


def claims(token: str) -> dict[str, Any]:
    decoded: dict[str, Any] = jwt.decode(token, SECRET, algorithms=["HS256"])
    return decoded


# --- Register ---


def test_register_pdf_example(auth_client: TestClient, test_database: Database) -> None:
    before = int(time.time())
    response = auth_client.post(REGISTER, json=PDF_REGISTER)
    assert response.status_code == 201
    data = raw_json(response)
    assert set(data) == {"token", "tokenType", "expiresIn", "user"}
    assert data["tokenType"] == "bearer" and data["expiresIn"] == 86_400
    user = data["user"]
    assert set(user) == {"id", "identifier", "district", "householdSize"}
    assert (user["identifier"], user["district"], user["householdSize"]) == (
        "+250788123456", "gasabo", 4,
    )  # fmt: skip
    assert re.fullmatch(ACCOUNT_ID, user["id"])
    # The token is HS256, as in the PDF's example header, and names the account.
    assert jwt.get_unverified_header(data["token"]) == {"alg": "HS256", "typ": "JWT"}
    token = claims(data["token"])
    assert token["sub"] == user["id"]
    assert before <= token["iat"] <= int(time.time())
    assert token["exp"] - token["iat"] == 86_400
    # What is stored: the profile and an Argon2id hash, never the password.
    (account,) = stored(test_database)
    assert account.id == user["id"] and account.identifier == "+250788123456"
    assert (account.district_code, account.household_size, account.monthly_income) == (
        "gasabo", 4, 180_000,
    )  # fmt: skip
    assert (account.currency, account.preferred_language) == ("RWF", "RW")
    assert account.password_hash.startswith("$argon2id$")
    assert "SecurePassword123!" not in account.password_hash
    assert "SecurePassword123!" not in response.text


def test_register_an_email_is_stored_lower_cased(
    auth_client: TestClient, test_database: Database
) -> None:
    body = {**PDF_REGISTER, "identifier": "  Umuryango@Example.RW "}
    response = auth_client.post(REGISTER, json=body)
    assert response.status_code == 201
    assert raw_json(response)["user"]["identifier"] == "umuryango@example.rw"
    assert [a.identifier for a in stored(test_database)] == ["umuryango@example.rw"]


def test_register_twice_is_a_conflict(auth_client: TestClient, test_database: Database) -> None:
    assert auth_client.post(REGISTER, json=PDF_REGISTER).status_code == 201
    again = {**PDF_REGISTER, "password": "AnotherPassword456"}
    assert_problem(auth_client.post(REGISTER, json=again), 409, "identifier-taken")
    # The same email in another case is the same identifier.
    email = {**PDF_REGISTER, "identifier": "a@example.rw"}
    assert auth_client.post(REGISTER, json=email).status_code == 201
    upper = {**PDF_REGISTER, "identifier": "A@EXAMPLE.RW"}
    assert_problem(auth_client.post(REGISTER, json=upper), 409, "identifier-taken")
    assert len(stored(test_database)) == 2


def test_register_unknown_district(auth_client: TestClient, test_database: Database) -> None:
    assert_problem(
        auth_client.post(REGISTER, json=with_profile(district="atlantis")), 404,
        "district-not-found",
    )  # fmt: skip
    # District codes are case-sensitive (contract §5).
    assert_problem(
        auth_client.post(REGISTER, json=with_profile(district="GASABO")), 404,
        "district-not-found",
    )  # fmt: skip
    assert stored(test_database) == []


@pytest.mark.parametrize(
    ("identifier", "code"),
    [
        ("0788123456", "invalid_format"),  # national form: E.164 is required
        ("+25078812345", "invalid_format"),  # one digit short
        ("+250688123456", "invalid_format"),  # not a mobile number
        ("not-an-email", "invalid_format"),
        ("a@b", "invalid_format"),
        ("", "invalid_format"),
        ("x" * 250 + "@a.rw", "too_long"),
        # Unicode lookalikes are rejected, never transformed (regression: Python's `\d` and `\s`
        # match them, so these were accepted as identifiers distinct from their ASCII forms).
        ("+2507\u0668\u0668123456", "invalid_format"),  # Arabic-Indic digits
        ("+250\uff17\uff18\uff18123456", "invalid_format"),  # fullwidth digits
        ("a@example.rw\u200b", "invalid_format"),  # trailing zero-width space
        ("a\u200b@example.rw", "invalid_format"),  # zero-width space inside
        ("\uff41@example.rw", "invalid_format"),  # fullwidth letter
        ("a@ex\u0430mple.rw", "invalid_format"),  # Cyrillic small a in the domain
        ("\u00a0a@example.rw", "invalid_format"),  # no-break space: only ASCII space is trimmed
        ("x@exa_mple.rw", "invalid_format"),  # domains hold letters, digits and hyphens only
    ],
)
def test_register_identifier_rules(
    auth_client: TestClient, test_database: Database, identifier: str, code: str
) -> None:
    response = auth_client.post(REGISTER, json={**PDF_REGISTER, "identifier": identifier})
    assert_problem(response, 422, "validation", ("identifier", code))
    assert stored(test_database) == []


@pytest.mark.parametrize(
    ("identifier", "normalised"),
    [
        ("+250788123456", "+250788123456"),
        (" +250788123456\t", "+250788123456"),  # ASCII whitespace is trimmed
        ("first.last+tag@sub.example.rw", "first.last+tag@sub.example.rw"),
        ("Umuryango-1@EXAMPLE-site.RW", "umuryango-1@example-site.rw"),
    ],
)
def test_register_valid_ascii_identifiers(
    auth_client: TestClient, identifier: str, normalised: str
) -> None:
    response = auth_client.post(REGISTER, json={**PDF_REGISTER, "identifier": identifier})
    assert response.status_code == 201
    assert raw_json(response)["user"]["identifier"] == normalised


def test_lookalikes_never_reach_an_existing_account(
    auth_client: TestClient, test_database: Database
) -> None:
    """Neither registration nor login treats a lookalike as another form of a real identifier."""
    assert auth_client.post(REGISTER, json=PDF_REGISTER).status_code == 201
    auth_client.post(REGISTER, json={**PDF_REGISTER, "identifier": "a@example.rw"})
    for lookalike in ("+2507\u0668\u0668123456", "+250788123456\u200b", "\uff41@example.rw"):
        register = auth_client.post(REGISTER, json={**PDF_REGISTER, "identifier": lookalike})
        assert_problem(register, 422, "validation", ("identifier", "invalid_format"))
        login = auth_client.post(LOGIN, json={**PDF_LOGIN, "identifier": lookalike})
        assert_problem(login, 401, "invalid-credentials")
    assert sorted(a.identifier for a in stored(test_database)) == ["+250788123456", "a@example.rw"]


@pytest.mark.parametrize(
    ("password", "code"), [("", "too_short"), ("1234567", "too_short"), ("x" * 129, "too_long")]
)
def test_register_password_rules(auth_client: TestClient, password: str, code: str) -> None:
    response = auth_client.post(REGISTER, json={**PDF_REGISTER, "password": password})
    assert_problem(response, 422, "validation", ("password", code))
    if password:
        assert password not in response.text  # an error never echoes the password


def test_register_password_bounds_are_accepted(auth_client: TestClient) -> None:
    for number, password in enumerate(("12345678", "y" * 128)):
        body = {**PDF_REGISTER, "identifier": f"+25078800000{number}", "password": password}
        assert auth_client.post(REGISTER, json=body).status_code == 201


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"householdSize": 0}, ("profile.householdSize", "out_of_range")),
        ({"householdSize": 21}, ("profile.householdSize", "out_of_range")),
        ({"monthlyIncome": -1}, ("profile.monthlyIncome", "out_of_range")),
        ({"monthlyIncome": 100_000_001}, ("profile.monthlyIncome", "out_of_range")),
        ({"currency": "USD"}, ("profile.currency", "unknown_value")),
        ({"preferredLanguage": "FR"}, ("profile.preferredLanguage", "unknown_value")),
        ({"preferredLanguage": "rw"}, ("profile.preferredLanguage", "unknown_value")),
        ({"district": None}, ("profile.district", "required")),
        ({"nickname": "x"}, ("profile.nickname", "unknown_field")),
    ],
)
def test_register_profile_rules(
    auth_client: TestClient, test_database: Database, changes: dict[str, object],
    error: tuple[str, str],
) -> None:  # fmt: skip
    response = auth_client.post(REGISTER, json=with_profile(**changes))
    assert_problem(response, 422, "validation", error)
    assert stored(test_database) == []


@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_register_household_size_must_be_an_integer(auth_client: TestClient, value: object) -> None:
    response = auth_client.post(REGISTER, json=with_profile(householdSize=value))
    assert_problem(response, 422, "validation", ("profile.householdSize", "not_integer"))


def test_register_shape_errors(auth_client: TestClient) -> None:
    missing = {k: v for k, v in PDF_REGISTER.items() if k != "profile"}
    assert_problem(auth_client.post(REGISTER, json=missing), 422, "validation",
                   ("profile", "required"))  # fmt: skip
    extra = {**PDF_REGISTER, "role": "admin"}
    assert_problem(auth_client.post(REGISTER, json=extra), 422, "validation",
                   ("role", "unknown_field"))  # fmt: skip
    malformed = auth_client.post(
        REGISTER, content=b"{", headers={"Content-Type": "application/json"}
    )
    assert_problem(malformed, 400, "malformed-request")
    assert_problem(auth_client.post(REGISTER + "?next=1", json=PDF_REGISTER), 400,
                   "unknown-parameter")  # fmt: skip


def test_register_validates_before_the_district_lookup(auth_client: TestClient) -> None:
    body = with_profile(district="atlantis", householdSize=0)
    assert_problem(auth_client.post(REGISTER, json=body), 422, "validation",
                   ("profile.householdSize", "out_of_range"))  # fmt: skip


# --- Login ---


def test_login_pdf_example(auth_client: TestClient) -> None:
    registered = raw_json(auth_client.post(REGISTER, json=PDF_REGISTER))
    response = auth_client.post(LOGIN, json=PDF_LOGIN)
    assert response.status_code == 200
    data = raw_json(response)
    # The PDF's login response: no `expiresIn`, and a user with only `id` and `district`.
    assert set(data) == {"token", "tokenType", "user"}
    assert data["tokenType"] == "bearer"
    assert data["user"] == {"id": registered["user"]["id"], "district": "gasabo"}
    token = claims(data["token"])
    assert token["sub"] == registered["user"]["id"]
    assert token["exp"] - token["iat"] == 86_400


def test_login_with_an_email_ignores_its_case(auth_client: TestClient) -> None:
    auth_client.post(REGISTER, json={**PDF_REGISTER, "identifier": "a@example.rw"})
    response = auth_client.post(LOGIN, json={**PDF_LOGIN, "identifier": " A@Example.RW"})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "body",
    [
        {**PDF_LOGIN, "password": "WrongPassword123!"},
        {**PDF_LOGIN, "password": "securepassword123!"},  # passwords are case-sensitive
        {**PDF_LOGIN, "identifier": "+250788000000"},  # no such account
        {**PDF_LOGIN, "identifier": "not an identifier"},
        {**PDF_LOGIN, "password": ""},
    ],
)
def test_login_failures_all_look_the_same(auth_client: TestClient, body: dict[str, str]) -> None:
    auth_client.post(REGISTER, json=PDF_REGISTER)
    response = auth_client.post(LOGIN, json=body)
    problem = assert_problem(response, 401, "invalid-credentials")
    assert problem["detail"] == "The identifier or password is incorrect."
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_shape_errors(auth_client: TestClient) -> None:
    assert_problem(auth_client.post(LOGIN, json={"identifier": "+250788123456"}), 422,
                   "validation", ("password", "required"))  # fmt: skip
    assert_problem(auth_client.post(LOGIN, json={**PDF_LOGIN, "remember": True}), 422,
                   "validation", ("remember", "unknown_field"))  # fmt: skip
    assert_problem(auth_client.post(LOGIN, json={**PDF_LOGIN, "password": "x" * 129}), 422,
                   "validation", ("password", "too_long"))  # fmt: skip


# --- Configuration, storage and documentation ---


def test_without_a_signing_key_accounts_are_unavailable(
    unconfigured_client: TestClient, test_database: Database
) -> None:
    for path, body in ((REGISTER, PDF_REGISTER), (LOGIN, PDF_LOGIN)):
        assert_problem(unconfigured_client.post(path, json=body), 503, "auth-not-configured")
    assert stored(test_database) == []
    # Validation still comes first.
    assert_problem(unconfigured_client.post(REGISTER, json=with_profile(householdSize=0)), 422,
                   "validation", ("profile.householdSize", "out_of_range"))  # fmt: skip


def test_a_token_from_another_key_does_not_verify(auth_client: TestClient) -> None:
    token = raw_json(auth_client.post(REGISTER, json=PDF_REGISTER))["token"]
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, "another-key-another-key-another-key", algorithms=["HS256"])


def test_openapi_documents_the_pdf_shapes(auth_client: TestClient) -> None:
    spec = auth_client.get("/openapi.json").json()
    register = spec["paths"][REGISTER]["post"]
    login = spec["paths"][LOGIN]["post"]
    assert set(register["responses"]) == {"201", "400", "404", "409", "422", "500", "503"}
    assert set(login["responses"]) == {"200", "400", "401", "422", "500", "503"}
    schemas = spec["components"]["schemas"]
    assert set(schemas["RegisterRequest"]["properties"]) == {"identifier", "password", "profile"}
    assert set(schemas["RegisterProfile"]["properties"]) == {
        "district", "householdSize", "monthlyIncome", "currency", "preferredLanguage",
    }  # fmt: skip
    assert set(schemas["RegisterResponse"]["properties"]) == {
        "token", "tokenType", "expiresIn", "user",
    }  # fmt: skip
    assert set(schemas["LoginResponse"]["properties"]) == {"token", "tokenType", "user"}
    assert set(schemas["LoggedInUser"]["properties"]) == {"id", "district"}


def test_a_concurrent_duplicate_is_still_a_conflict(
    auth_client: TestClient, test_database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two registrations racing past the lookup: the unique constraint makes the second a 409."""
    assert auth_client.post(REGISTER, json=PDF_REGISTER).status_code == 201
    monkeypatch.setattr(AccountRepository, "find_by_identifier", lambda self, identifier: None)
    assert_problem(auth_client.post(REGISTER, json=PDF_REGISTER), 409, "identifier-taken")
    assert len(stored(test_database)) == 1


def test_other_integrity_errors_are_not_reported_as_a_conflict(
    test_database: Database, accounts: None
) -> None:
    with test_database.session() as session:
        account = HouseholdAccount(
            id="usr_" + "0" * 26, identifier="+250788000001", password_hash="x",
            district_code="atlantis", household_size=4, monthly_income=0, currency="RWF",
            preferred_language="EN",
        )  # fmt: skip
        with pytest.raises(IntegrityError):
            AccountRepository(session).add(account)  # unknown district: a foreign-key error
    assert stored(test_database) == []


# --- The current-account dependency for future protected routes ---

PROBE: Final = "/api/v1/__test-only/whoami"


def _probe(account: CurrentAccountDep) -> dict[str, object]:
    return {"id": account.id, "district": account.district, "householdSize": account.household_size}


def _protected_client(
    settings: Settings, database: Database, secret: str | None
) -> Iterator[TestClient]:
    """A test-only app with one probe route that uses the dependency; no product route."""
    configured = settings.model_copy(
        update={"jwt_secret_key": SecretStr(secret) if secret else None}
    )
    app = create_app("test", settings=configured, database=database)
    app.add_api_route(PROBE, _probe, methods=["GET"])
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def protected_client(
    db_settings: Settings, test_database: Database, accounts: None
) -> Iterator[TestClient]:
    yield from _protected_client(db_settings, test_database, SECRET)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assert_not_authenticated(response: Any) -> None:
    problem = assert_problem(response, 401, "not-authenticated")
    assert problem["detail"] == "A valid bearer token is required."
    assert response.headers["www-authenticate"] == "Bearer"


def test_a_registered_account_token_reaches_a_protected_route(
    protected_client: TestClient,
) -> None:
    registered = raw_json(protected_client.post(REGISTER, json=PDF_REGISTER))
    response = protected_client.get(PROBE, headers=bearer(registered["token"]))
    assert response.status_code == 200
    assert response.json() == {"id": registered["user"]["id"], "district": "gasabo",
                               "householdSize": 4}  # fmt: skip
    login = raw_json(protected_client.post(LOGIN, json=PDF_LOGIN))
    assert protected_client.get(PROBE, headers=bearer(login["token"])).status_code == 200
    # The scheme name is case-insensitive (RFC 9110 §11.1).
    lower = {"Authorization": "bearer " + login["token"]}
    assert protected_client.get(PROBE, headers=lower).status_code == 200


def _signed(claims: dict[str, object], key: str = SECRET) -> str:
    return jwt.encode(claims, key, algorithm="HS256")


@pytest.mark.parametrize(
    "headers",
    [
        {},  # missing
        {"Authorization": ""},
        {"Authorization": "Bearer"},  # no token
        {"Authorization": "Basic dXNlcjpwYXNz"},  # another scheme
        {"Authorization": "Bearer not.a.jwt"},  # malformed
        {"Authorization": "Bearer " + "x" * 40},
    ],
)
def test_missing_or_malformed_credentials_are_401(
    protected_client: TestClient, headers: dict[str, str]
) -> None:
    assert_not_authenticated(protected_client.get(PROBE, headers=headers))


def test_wrongly_signed_expired_and_unknown_subject_tokens_are_401(
    protected_client: TestClient, test_database: Database
) -> None:
    account_id = raw_json(protected_client.post(REGISTER, json=PDF_REGISTER))["user"]["id"]
    now = int(time.time())
    valid = {"sub": account_id, "iat": now, "exp": now + 3_600}
    rejected = {
        "wrong key": _signed(valid, key="another-key-another-key-another-key"),
        "expired": _signed({**valid, "iat": now - 7_200, "exp": now - 3_600}),
        "no exp": _signed({"sub": account_id, "iat": now}),
        "no sub": _signed({"iat": now, "exp": now + 3_600}),
        "unsigned": jwt.encode(valid, None, algorithm="none"),
        "unknown account": _signed({**valid, "sub": "usr_" + "0" * 26}),
    }
    for name, token in rejected.items():
        response = protected_client.get(PROBE, headers=bearer(token))
        assert_not_authenticated(response)
        assert token not in response.text and SECRET not in response.text, name
    # A token whose account is deleted stops working at once.
    token = raw_json(protected_client.post(LOGIN, json=PDF_LOGIN))["token"]
    assert protected_client.get(PROBE, headers=bearer(token)).status_code == 200
    with test_database.session() as session:
        session.execute(delete(HouseholdAccount).where(HouseholdAccount.id == account_id))
        session.commit()
    assert_not_authenticated(protected_client.get(PROBE, headers=bearer(token)))


def test_the_dependency_without_a_signing_key_is_503(
    db_settings: Settings, test_database: Database, accounts: None
) -> None:
    for client in _protected_client(db_settings, test_database, None):
        assert_problem(client.get(PROBE, headers=bearer("x.y.z")), 503, "auth-not-configured")


def test_cors_preflight_allows_the_authorization_header(protected_client: TestClient) -> None:
    response = protected_client.options(
        PROBE,
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
