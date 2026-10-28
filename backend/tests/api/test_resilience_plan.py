"""The household's saved resilience plan (contract §11.11, MISSING_APIS.pdf inventory item 17).

`POST /user/resilience-plan` takes the resilience-simulation request (page 9) and stores its
inputs, one plan per account; `GET` reads it back with the simulation recomputed and `DELETE`
removes it. Every route needs a bearer token and works only on that household's plan.
"""

import copy
import re
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Final

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.db.session import Database
from app.main import create_app
from app.models import HouseholdAccount, ResiliencePlan
from app.repositories.resilience_plan_repository import (
    AccountGoneError,
    PlanInputs,
    ResiliencePlanRepository,
)
from tests.helpers import EXAMPLE_META, assert_problem, raw_json

URL: Final = "/api/v1/user/resilience-plan"
SIMULATION: Final = "/api/v1/calculations/resilience-simulation"
SECRET: Final = "test-only-signing-key-0123456789abcdef"  # never a real key
REGISTER: Final[dict[str, Any]] = {
    "password": "SecurePassword123!",
    "profile": {"district": "gasabo", "householdSize": 4, "monthlyIncome": 180000,
                "currency": "RWF", "preferredLanguage": "RW"},
}  # fmt: skip
# MISSING_APIS.pdf page 9, the resilience-simulation request exactly.
PDF_PLAN: Final[dict[str, Any]] = {
    "baseline": {"monthlyIncome": 180_000, "monthlyEssentials": 150_000, "savings": 60_000},
    "shock": {"type": "income_drop", "incomeReductionPct": 20, "durationMonths": 3},
    "activeCopingLevers": ["trim_non_essentials", "seasonal_agro_swaps", "ibimina_tontine"],
}
LUMP_SUM_PLAN: Final[dict[str, Any]] = {
    "baseline": {"monthlyIncome": 100_000, "monthlyEssentials": 90_000, "savings": 20_000},
    "shock": {"type": "school_fees", "durationMonths": 2},
    "activeCopingLevers": ["ibimina_tontine"],
}
WIRE_TIME: Final = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _clear(database: Database) -> None:
    with database.session() as session:
        session.execute(delete(HouseholdAccount))  # plans cascade
        session.commit()


@pytest.fixture
def client(db_settings: Settings, test_database: Database) -> Iterator[TestClient]:
    _clear(test_database)
    configured = db_settings.model_copy(update={"jwt_secret_key": SecretStr(SECRET)})
    app = create_app("test", settings=configured, database=test_database)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    _clear(test_database)


def register(client: TestClient, identifier: str = "+250788123456") -> dict[str, str]:
    response = client.post("/api/v1/auth/register", json={**REGISTER, "identifier": identifier})
    return {"Authorization": f"Bearer {raw_json(response)['token']}"}


@pytest.fixture
def auth(client: TestClient) -> dict[str, str]:
    return register(client)


def simulation_of(client: TestClient, plan: dict[str, Any]) -> dict[str, Any]:
    """What the stateless simulator answers for these inputs, without its `meta`."""
    data = raw_json(client.post(SIMULATION, json=plan))
    data.pop("meta")
    return dict(data)


def plan_count(database: Database) -> int:
    with database.read_only_session() as session:
        return int(session.scalar(select(func.count()).select_from(ResiliencePlan)) or 0)


# --- authentication ---


def test_every_route_needs_a_bearer_token(client: TestClient) -> None:
    for response in (
        client.post(URL, json=PDF_PLAN),
        client.get(URL),
        client.delete(URL),
        client.get(URL, headers={"Authorization": "Bearer not-a-token"}),
    ):
        assert_problem(response, 401, "not-authenticated")
        assert response.headers["WWW-Authenticate"] == "Bearer"


def test_without_a_signing_key_the_routes_are_unavailable(
    db_settings: Settings, test_database: Database
) -> None:
    unconfigured = db_settings.model_copy(update={"jwt_secret_key": None})
    app = create_app("test", settings=unconfigured, database=test_database)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        headers = {"Authorization": "Bearer x.y.z"}
        for response in (
            test_client.post(URL, json=PDF_PLAN, headers=headers),
            test_client.get(URL, headers=headers),
            test_client.delete(URL, headers=headers),
        ):
            assert_problem(response, 503, "auth-not-configured")


# --- save, read, replace, delete ---


def test_nothing_saved_yet(client: TestClient, auth: dict[str, str]) -> None:
    assert_problem(client.get(URL, headers=auth), 404, "resilience-plan-not-found")
    assert_problem(client.delete(URL, headers=auth), 404, "resilience-plan-not-found")


def test_save_the_pdf_plan(client: TestClient, auth: dict[str, str]) -> None:
    response = client.post(URL, json=PDF_PLAN, headers=auth)
    assert response.status_code == 201, response.text
    data = raw_json(response)
    assert set(data) == {
        "baseline", "shock", "activeCopingLevers", "simulation", "savedAt", "meta",
    }  # fmt: skip
    assert data["baseline"] == PDF_PLAN["baseline"]
    assert data["shock"] == {**PDF_PLAN["shock"], "amount": None}
    assert data["activeCopingLevers"] == PDF_PLAN["activeCopingLevers"]
    # The same figures as the stateless simulator: the PDF's gaps, buffer and 14.2 runway.
    assert data["simulation"] == simulation_of(client, PDF_PLAN)
    assert data["simulation"]["rawMonthlyGap"] == 6_000
    assert data["simulation"]["netMonthlyGap"] == 0
    assert data["simulation"]["totalEffectiveBuffer"] == 85_000
    assert data["simulation"]["runwayMonths"] == 14.2
    assert WIRE_TIME.fullmatch(data["savedAt"])
    assert data["meta"] == EXAMPLE_META
    assert client.get(URL, headers=auth).json() == data


def test_saving_again_replaces_the_plan(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    assert client.post(URL, json=PDF_PLAN, headers=auth).status_code == 201
    response = client.post(URL, json=LUMP_SUM_PLAN, headers=auth)
    assert response.status_code == 200, response.text
    data = raw_json(response)
    assert data["shock"] == {"type": "school_fees", "incomeReductionPct": None,
                             "durationMonths": 2, "amount": None}  # fmt: skip
    # No amount: the catalogue's 60,000 school fees, spread over 2 months.
    assert data["simulation"]["shockCostMonthly"] == 30_000
    assert data["simulation"] == simulation_of(client, LUMP_SUM_PLAN)
    assert raw_json(client.get(URL, headers=auth)) == data
    assert plan_count(test_database) == 1


def test_delete_the_plan(client: TestClient, auth: dict[str, str]) -> None:
    assert client.post(URL, json=PDF_PLAN, headers=auth).status_code == 201
    response = client.delete(URL, headers=auth)
    assert response.status_code == 204 and response.content == b""
    assert_problem(client.get(URL, headers=auth), 404, "resilience-plan-not-found")
    # Saving after a delete creates a plan again.
    assert client.post(URL, json=PDF_PLAN, headers=auth).status_code == 201


def test_a_lump_sum_amount_is_kept(client: TestClient, auth: dict[str, str]) -> None:
    body = copy.deepcopy(LUMP_SUM_PLAN)
    body["shock"]["amount"] = 45_001
    data = raw_json(client.post(URL, json=body, headers=auth))
    assert data["shock"]["amount"] == 45_001
    assert data["simulation"]["shockCostMonthly"] == 22_501  # 22,500.5 rounds half up


def test_households_see_only_their_own_plan(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    other = register(client, "+250788000001")
    assert client.post(URL, json=PDF_PLAN, headers=auth).status_code == 201
    assert_problem(client.get(URL, headers=other), 404, "resilience-plan-not-found")
    assert_problem(client.delete(URL, headers=other), 404, "resilience-plan-not-found")
    assert client.post(URL, json=LUMP_SUM_PLAN, headers=other).status_code == 201
    assert raw_json(client.get(URL, headers=auth))["shock"]["type"] == "income_drop"
    assert plan_count(test_database) == 2


def test_deleting_the_account_deletes_its_plan(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    assert client.post(URL, json=PDF_PLAN, headers=auth).status_code == 201
    _clear(test_database)
    assert plan_count(test_database) == 0
    # The token's account is gone, so the token no longer works.
    assert_problem(client.get(URL, headers=auth), 401, "not-authenticated")


# --- validation: exactly the simulator's, and nothing is stored on failure ---


@pytest.mark.parametrize(
    ("change", "field", "code"),
    [
        ({"shock": {"type": "school_fees", "durationMonths": 2, "incomeReductionPct": 5}},
         "shock.incomeReductionPct", "unknown_field"),
        ({"shock": {"type": "income_drop", "durationMonths": 2}},
         "shock.incomeReductionPct", "required"),
        ({"activeCopingLevers": ["ibimina_tontine", "ibimina_tontine"]},
         "activeCopingLevers.1", "unknown_value"),
        ({"shock": {"type": "income_drop", "incomeReductionPct": 20, "durationMonths": 25}},
         "shock.durationMonths", "out_of_range"),
    ],
)  # fmt: skip
def test_invalid_plans_are_refused_and_not_stored(
    client: TestClient,
    auth: dict[str, str],
    test_database: Database,
    change: dict[str, Any],
    field: str,
    code: str,
) -> None:
    body = {**copy.deepcopy(PDF_PLAN), **change}
    simulated = client.post(SIMULATION, json=body)
    saved = client.post(URL, json=body, headers=auth)
    assert saved.status_code == simulated.status_code == 422
    assert raw_json(saved)["errors"] == raw_json(simulated)["errors"]
    assert (field, code) in {(e["field"], e["code"]) for e in raw_json(saved)["errors"]}
    assert plan_count(test_database) == 0


def test_unknown_fields_and_parameters(client: TestClient, auth: dict[str, str]) -> None:
    response = client.post(URL, json={**PDF_PLAN, "accountId": "usr_x"}, headers=auth)
    assert_problem(response, 422, "validation", ("accountId", "unknown_field"))
    assert_problem(client.get(URL + "?x=1", headers=auth), 400, "unknown-parameter",
                   ("x", "unknown_field"))  # fmt: skip
    assert_problem(client.put(URL, json=PDF_PLAN, headers=auth), 405, "method-not-allowed")


# --- storage ---


def test_concurrent_saves_leave_one_plan(
    client: TestClient, auth: dict[str, str], test_database: Database
) -> None:
    bodies = [PDF_PLAN, LUMP_SUM_PLAN] * 4
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses = list(pool.map(lambda b: client.post(URL, json=b, headers=auth).status_code,
                                 bodies))  # fmt: skip
    assert statuses.count(201) == 1 and statuses.count(200) == 7
    assert plan_count(test_database) == 1


def test_saving_for_a_deleted_account_is_refused(test_database: Database) -> None:
    """The account vanished after its token was checked: the service turns this into 401."""
    _clear(test_database)
    inputs = PlanInputs(1, 1, 1, "income_drop", 10, 1, None, [])
    with test_database.session() as session, pytest.raises(AccountGoneError):
        ResiliencePlanRepository(session).save("usr_" + "0" * 26, inputs)


@pytest.mark.parametrize(
    "changes",
    [
        {"coping_levers": ["ibimina_tontine", "ibimina_tontine"]},
        {"coping_levers": ["ibimina_tontine", "trim_non_essentials", "ibimina_tontine"]},
        {"coping_levers": ["unknown_lever"]},
        {"shock_type": "school_fees"},  # a lump sum with a reduction
        {"shock_amount": 5_000},  # an income shock with an amount
        {"income_reduction_pct": None},
        {"duration_months": 0},
        {"savings": -1},
    ],
)
def test_the_database_refuses_inconsistent_plans(
    client: TestClient, auth: dict[str, str], test_database: Database, changes: dict[str, Any]
) -> None:
    with test_database.read_only_session() as session:
        account_id = session.scalars(select(HouseholdAccount.id)).one()
    row = {
        "account_id": account_id, "monthly_income": 1, "monthly_essentials": 1, "savings": 1,
        "shock_type": "income_drop", "income_reduction_pct": 10, "duration_months": 1,
        "shock_amount": None, "coping_levers": ["ibimina_tontine", "trim_non_essentials"],
    }  # fmt: skip
    with test_database.session() as session:
        session.add(ResiliencePlan(**row))
        session.commit()  # the valid row is accepted
        session.execute(delete(ResiliencePlan))
        session.commit()
        session.add(ResiliencePlan(**{**row, **changes}))
        with pytest.raises(IntegrityError):
            session.commit()
