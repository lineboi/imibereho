"""`POST /api/v1/calculations/policy-scenario` (contract §5)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.helpers import META, NOT_INTEGER_BODY_VALUES, assert_problem, raw_json

URL = "/api/v1/calculations/policy-scenario"
SUPPLIED_BASELINE = {"monthlyIncome": 180_000, "monthlyEssentials": 150_000, "savings": 60_000}
TOP_INTEGER_FIELDS = [
    "incomeLossPct",
    "durationMonths",
    "supportPerHouseholdMonthly",
    "eligibleHouseholds",
]


def payload(**changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "instrument": "monthly_cash_support",
        "incomeLossPct": 20,
        "durationMonths": 3,
        "supportPerHouseholdMonthly": 6_000,
        "eligibleHouseholds": 1_000,
    }
    body.update(changes)
    return body


def test_design_matrix_with_the_reference_household(db_client: TestClient) -> None:
    data = raw_json(db_client.post(URL, json=payload()))
    assert data == {
        "directTransferBudget": 18_000_000,
        "modelledMonthlyGapWithSupport": 0,
        "horizonMonths": 3,
        "baselineUsed": {**SUPPLIED_BASELINE, "source": "reference"},
        "comparison": {
            "columns": ["no_shock", "shock_only", "shock_with_support"],
            "rows": {
                "incomePerMonth": {
                    "no_shock": 180_000,
                    "shock_only": 144_000,
                    "shock_with_support": 144_000,
                },
                "supportPerMonth": {"no_shock": 0, "shock_only": 0, "shock_with_support": 6_000},
                "expensesPerMonth": {
                    "no_shock": 150_000,
                    "shock_only": 150_000,
                    "shock_with_support": 150_000,
                },
                "netMonthlyBalance": {
                    "no_shock": 30_000,
                    "shock_only": -6_000,
                    "shock_with_support": 0,
                },
                "savingsAfterHorizon": {
                    "no_shock": 150_000,
                    "shock_only": 42_000,
                    "shock_with_support": 60_000,
                },
            },
        },
        "assumptions": [
            "surpluses_saved",
            "gaps_paid_from_savings",
            "no_interest",
            "no_debt",
            "no_admin_costs",
            "no_further_shocks",
            "no_behavioural_effects",
        ],
        "meta": META,
    }


# The tests below supply a baseline, so they need no database (the session is never used).


def test_supplied_baseline_is_reported_as_request(client: TestClient) -> None:
    data = client.post(URL, json=payload(baseline=SUPPLIED_BASELINE)).json()
    assert data["baselineUsed"]["source"] == "request"
    assert data["directTransferBudget"] == 18_000_000


def test_derived_negative_savings_follow_br07_as_written(client: TestClient) -> None:
    baseline = {"monthlyIncome": 100_000, "monthlyEssentials": 150_000, "savings": 10_000}
    data = client.post(URL, json=payload(baseline=baseline, supportPerHouseholdMonthly=0)).json()
    assert data["comparison"]["rows"]["savingsAfterHorizon"]["shock_only"] == 10_000 + 3 * (
        80_000 - 150_000
    )


def test_eligible_households_above_the_sample_size_is_out_of_range(client: TestClient) -> None:
    response = client.post(URL, json=payload(eligibleHouseholds=3_001, baseline=SUPPLIED_BASELINE))
    assert_problem(response, 422, "validation", ("eligibleHouseholds", "out_of_range"))


@pytest.mark.parametrize("field", TOP_INTEGER_FIELDS)
@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_body_integer_matrix(client: TestClient, field: str, value: object) -> None:
    response = client.post(URL, json=payload(**{field: value}, baseline=SUPPLIED_BASELINE))
    assert_problem(response, 422, "validation", (field, "not_integer"))


@pytest.mark.parametrize("field", ["monthlyIncome", "monthlyEssentials", "savings"])
@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_nested_baseline_integer_matrix(client: TestClient, field: str, value: object) -> None:
    response = client.post(URL, json=payload(baseline={**SUPPLIED_BASELINE, field: value}))
    assert_problem(response, 422, "validation", (f"baseline.{field}", "not_integer"))


@pytest.mark.parametrize("instrument", [True, "voucher", None])
def test_bad_instrument(client: TestClient, instrument: object) -> None:
    code = "required" if instrument is None else "unknown_value"
    response = client.post(URL, json=payload(instrument=instrument, baseline=SUPPLIED_BASELINE))
    assert_problem(response, 422, "validation", ("instrument", code))


def test_extra_field_is_unknown_field(client: TestClient) -> None:
    response = client.post(URL, json=payload(scenarioName="A", baseline=SUPPLIED_BASELINE))
    assert_problem(response, 422, "validation", ("scenarioName", "unknown_field"))


def test_malformed_json(client: TestClient) -> None:
    response = client.post(URL, content="{", headers={"Content-Type": "application/json"})
    assert_problem(response, 400, "malformed-request")
