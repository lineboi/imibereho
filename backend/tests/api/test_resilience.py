"""`GET /api/v1/shocks/catalog` and `POST /api/v1/calculations/resilience-simulation`.

Contract v0.4 §11.1, from MISSING_APIS.pdf page 9. Both are stateless and need no database.
Shock defaults and lever amounts are the PDF's example values (owner-approved illustrative data,
contract §11.7), so both responses carry `meta.provenance`.
"""

import copy
from typing import Any, Final

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.helpers import (
    EXAMPLE_META,
    NOT_INTEGER_BODY_VALUES,
    assert_number,
    assert_problem,
    raw_json,
)

CATALOG: Final = "/api/v1/shocks/catalog"
URL: Final = "/api/v1/calculations/resilience-simulation"
PDF_REQUEST: Final[dict[str, Any]] = {
    "baseline": {"monthlyIncome": 180_000, "monthlyEssentials": 150_000, "savings": 60_000},
    "shock": {"type": "income_drop", "incomeReductionPct": 20, "durationMonths": 3},
    "activeCopingLevers": ["trim_non_essentials", "seasonal_agro_swaps", "ibimina_tontine"],
}
INTEGER_FIELDS: Final = [
    ("baseline", "monthlyIncome"),
    ("baseline", "monthlyEssentials"),
    ("baseline", "savings"),
    ("shock", "incomeReductionPct"),
    ("shock", "durationMonths"),
]


def payload(**changes: Any) -> dict[str, Any]:
    body = copy.deepcopy(PDF_REQUEST)
    for path, value in changes.items():
        section, field = path.split("__")
        body[section][field] = value
    return body


def lump_sum(**shock: Any) -> dict[str, Any]:
    body = copy.deepcopy(PDF_REQUEST)
    body["shock"] = {"type": "medical_emergency", "durationMonths": 3, **shock}
    return body


# --- GET /shocks/catalog ---


def test_catalog_items_follow_the_pdf(client: TestClient) -> None:
    response = client.get(CATALOG)
    assert response.status_code == 200
    data = raw_json(response)
    assert data["items"] == [
        {"id": "income_drop", "title": "Monthly income falls", "isLumpSum": False,
         "defaultPct": 20, "defaultDuration": 3, "defaultAmount": None},
        {"id": "medical_emergency", "title": "Unexpected medical cost", "isLumpSum": True,
         "defaultPct": None, "defaultDuration": None, "defaultAmount": 45_000},
        {"id": "school_fees", "title": "School term fees", "isLumpSum": True,
         "defaultPct": None, "defaultDuration": None, "defaultAmount": 60_000},
        # Named in the PDF's description without values: an income shock with no defaults.
        {"id": "harvest_disruption", "title": "Harvest disruption", "isLumpSum": False,
         "defaultPct": None, "defaultDuration": None, "defaultAmount": None},
    ]  # fmt: skip
    assert data["meta"] == {**EXAMPLE_META, "count": 4}


def test_catalog_lists_the_coping_levers(client: TestClient) -> None:
    levers = raw_json(client.get(CATALOG))["copingLevers"]
    assert [(lever["id"], lever["kind"], lever["amount"]) for lever in levers] == [
        ("trim_non_essentials", "monthly_relief", 12_000),
        ("seasonal_agro_swaps", "monthly_relief", 5_200),
        ("ibimina_tontine", "one_off_support", 25_000),
    ]
    assert all(isinstance(lever["title"], str) and lever["title"] for lever in levers)


def test_catalog_refuses_query_parameters_and_other_methods(client: TestClient) -> None:
    assert_problem(client.get(CATALOG + "?district=gasabo"), 400, "unknown-parameter",
                   ("district", "unknown_field"))  # fmt: skip
    assert_problem(client.post(CATALOG), 405, "method-not-allowed")


# --- POST /calculations/resilience-simulation ---


def test_pdf_example(client: TestClient) -> None:
    response = client.post(URL, json=PDF_REQUEST)
    assert response.status_code == 200
    data = raw_json(response)
    # The PDF's fields, with its values where its example is consistent with BR-06 and BR-19.
    assert {key: data[key] for key in (
        "rawMonthlyGap", "copingReliefMonthly", "lumpSumSupport", "netMonthlyGap",
        "totalEffectiveBuffer",
    )} == {"rawMonthlyGap": 6_000, "copingReliefMonthly": 17_200, "lumpSumSupport": 25_000,
           "netMonthlyGap": 0, "totalEffectiveBuffer": 85_000}  # fmt: skip
    assert_number(data["runwayMonths"], 14.2, integer=False)  # the PDF: 85,000 ÷ 6,000
    # BR-19 (the frontend's own heuristic) gives 95 and +28. The PDF's 88 and "+26" are not
    # produced by any formula it states (contract §11.1); scoreChange stays an integer.
    assert (data["resilienceScore"], data["scoreChange"]) == (95, 28)
    assert data["shockCostMonthly"] == 0
    assert (data["savingsUsed"], data["savingsRemaining"], data["savingsExhausted"]) == (
        0, 85_000, False,
    )  # fmt: skip
    assert data["assumptions"] == [
        "illustrative_parameters_not_observations", "expenses_held_constant",
        "lump_sum_spread_evenly_over_duration", "lever_amounts_from_catalogue",
        "no_new_borrowing", "no_additional_shocks",
        "resilience_score_is_br_19_the_pdf_example_figures_are_not_derivable",
    ]  # fmt: skip
    assert data["meta"] == EXAMPLE_META


def test_harvest_disruption_is_an_income_shock(client: TestClient) -> None:
    harvest = raw_json(client.post(URL, json=payload(shock__type="harvest_disruption")))
    income = raw_json(client.post(URL, json=PDF_REQUEST))
    same = ("rawMonthlyGap", "netMonthlyGap", "totalEffectiveBuffer", "runwayMonths",
            "resilienceScore", "scoreChange")  # fmt: skip
    assert {k: harvest[k] for k in same} == {k: income[k] for k in same}
    assert harvest["assumptions"][-1] == "harvest_disruption_modelled_as_a_loss_of_income"
    assert "harvest_disruption_modelled_as_a_loss_of_income" not in income["assumptions"]


def test_harvest_disruption_needs_its_parameters(client: TestClient) -> None:
    """The PDF gives no defaults, so the caller must say how much income is lost."""
    body = payload(shock__type="harvest_disruption")
    del body["shock"]["incomeReductionPct"]
    assert_problem(client.post(URL, json=body), 422, "validation",
                   ("shock.incomeReductionPct", "required"))  # fmt: skip
    body = payload(shock__type="harvest_disruption", shock__amount=5_000)
    assert_problem(client.post(URL, json=body), 422, "validation",
                   ("shock.amount", "unknown_field"))  # fmt: skip


def test_numbers_are_json_numbers(client: TestClient) -> None:
    data = raw_json(client.post(URL, json=payload(shock__incomeReductionPct=50)))
    for key in ("rawMonthlyGap", "netMonthlyGap", "resilienceScore", "scoreChange"):
        assert_number(data[key], data[key], integer=True)
    assert data["rawMonthlyGap"] == 60_000 and data["netMonthlyGap"] == 42_800
    assert_number(data["runwayMonths"], 1.4, integer=False)  # buffer ÷ raw gap: 85,000 ÷ 60,000
    assert isinstance(data["scoreChange"], int)


def test_no_levers_is_the_plain_income_shock(client: TestClient) -> None:
    body = payload()
    body["activeCopingLevers"] = []
    data = raw_json(client.post(URL, json=body))
    assert (data["copingReliefMonthly"], data["lumpSumSupport"], data["netMonthlyGap"]) == (
        0, 0, 6_000,
    )  # fmt: skip
    assert_number(data["runwayMonths"], 10.0, integer=False)  # same as household-shock
    assert (data["savingsUsed"], data["savingsRemaining"]) == (18_000, 42_000)
    assert (data["resilienceScore"], data["scoreChange"]) == (67, 0)


def test_no_gap_and_no_levers_changes_nothing(client: TestClient) -> None:
    body = lump_sum()  # 45,000 over 3 months: no gap at 180,000 income
    body["activeCopingLevers"] = []
    data = raw_json(client.post(URL, json=body))
    assert (data["rawMonthlyGap"], data["resilienceScore"], data["scoreChange"]) == (0, 70, 0)


def test_lump_sum_uses_the_catalogue_default_or_the_given_amount(client: TestClient) -> None:
    default = raw_json(client.post(URL, json=lump_sum()))
    assert default["shockCostMonthly"] == 15_000  # 45,000 ÷ 3
    assert default["rawMonthlyGap"] == 0  # 150,000 + 15,000 ≤ 180,000
    given = raw_json(client.post(URL, json=lump_sum(amount=120_000, durationMonths=2)))
    assert given["shockCostMonthly"] == 60_000
    assert given["rawMonthlyGap"] == 30_000  # 150,000 + 60,000 − 180,000


def test_income_drop_requires_a_reduction(client: TestClient) -> None:
    body = payload()
    del body["shock"]["incomeReductionPct"]
    assert_problem(client.post(URL, json=body), 422, "validation",
                   ("shock.incomeReductionPct", "required"))  # fmt: skip


def test_fields_that_do_not_apply_to_the_shock_are_refused(client: TestClient) -> None:
    assert_problem(client.post(URL, json=payload(shock__amount=5_000)), 422, "validation",
                   ("shock.amount", "unknown_field"))  # fmt: skip
    assert_problem(client.post(URL, json=lump_sum(incomeReductionPct=20)), 422, "validation",
                   ("shock.incomeReductionPct", "unknown_field"))  # fmt: skip


def test_duration_is_required_for_every_shock(client: TestClient) -> None:
    body = lump_sum()
    del body["shock"]["durationMonths"]
    assert_problem(client.post(URL, json=body), 422, "validation",
                   ("shock.durationMonths", "required"))  # fmt: skip


def test_unknown_shock_and_lever_are_unknown_value(client: TestClient) -> None:
    assert_problem(client.post(URL, json=payload(shock__type="income_fall")), 422, "validation",
                   ("shock.type", "unknown_value"))  # fmt: skip
    body = payload()
    body["activeCopingLevers"] = ["trim_non_essentials", "lottery"]
    assert_problem(client.post(URL, json=body), 422, "validation",
                   ("activeCopingLevers.1", "unknown_value"))  # fmt: skip


def test_duplicate_lever_is_unknown_value(client: TestClient) -> None:
    body = payload()
    body["activeCopingLevers"] = ["ibimina_tontine", "ibimina_tontine"]
    assert_problem(client.post(URL, json=body), 422, "validation",
                   ("activeCopingLevers.1", "unknown_value"))  # fmt: skip


def test_client_supplied_results_are_refused(client: TestClient) -> None:
    body = payload()
    body["copingReliefMonthly"] = 1_000_000
    assert_problem(client.post(URL, json=body), 422, "validation",
                   ("copingReliefMonthly", "unknown_field"))  # fmt: skip


def test_levers_are_required(client: TestClient) -> None:
    body = payload()
    del body["activeCopingLevers"]
    assert_problem(client.post(URL, json=body), 422, "validation",
                   ("activeCopingLevers", "required"))  # fmt: skip


@pytest.mark.parametrize(("section", "field"), INTEGER_FIELDS)
@pytest.mark.parametrize("value", NOT_INTEGER_BODY_VALUES)
def test_body_integer_matrix(client: TestClient, section: str, field: str, value: object) -> None:
    response = client.post(URL, json=payload(**{f"{section}__{field}": value}))
    assert_problem(response, 422, "validation", (f"{section}.{field}", "not_integer"))


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"shock__incomeReductionPct": 101}, "shock.incomeReductionPct"),
        ({"shock__durationMonths": 0}, "shock.durationMonths"),
        ({"shock__durationMonths": 25}, "shock.durationMonths"),
        ({"baseline__monthlyIncome": 100_000_001}, "baseline.monthlyIncome"),
        ({"baseline__savings": -1}, "baseline.savings"),
    ],
)
def test_out_of_range(client: TestClient, change: dict[str, int], field: str) -> None:
    assert_problem(client.post(URL, json=payload(**change)), 422, "validation",
                   (field, "out_of_range"))  # fmt: skip


def test_lump_sum_amount_bounds(client: TestClient) -> None:
    assert_problem(client.post(URL, json=lump_sum(amount=100_000_001)), 422, "validation",
                   ("shock.amount", "out_of_range"))  # fmt: skip


def test_maximum_inputs_are_accepted(client: TestClient) -> None:
    body = lump_sum(amount=100_000_000, durationMonths=1)
    body["baseline"] = {
        "monthlyIncome": 0,
        "monthlyEssentials": 100_000_000,
        "savings": 100_000_000,
    }
    data = client.post(URL, json=body).json()
    assert data["rawMonthlyGap"] == 200_000_000 and data["savingsExhausted"] is True


def test_malformed_json_query_and_method(client: TestClient) -> None:
    response = client.post(URL, content="{nope", headers={"Content-Type": "application/json"})
    assert_problem(response, 400, "malformed-request")
    assert_problem(client.post(URL + "?savings=1", json=PDF_REQUEST), 400, "unknown-parameter",
                   ("savings", "unknown_field"))  # fmt: skip
    assert_problem(client.get(URL), 405, "method-not-allowed")


def test_openapi_documents_both_routes(stub_app: FastAPI) -> None:
    spec = stub_app.openapi()
    assert "get" in spec["paths"][CATALOG] and "post" in spec["paths"][URL]
    schemas = spec["components"]["schemas"]
    item = schemas["ShockCatalogItem"]["properties"]
    assert {o.get("type") for o in item["defaultAmount"]["anyOf"]} == {"integer", "null"}
    result = schemas["ResilienceSimulationResponse"]["properties"]
    assert result["scoreChange"]["type"] == "integer"
    assert {o.get("type") for o in result["runwayMonths"]["anyOf"]} == {"number", "null"}


def test_runway_is_null_only_without_a_raw_gap(client: TestClient) -> None:
    body = lump_sum()  # 45,000 over 3 months: no raw gap at 180,000 income
    assert raw_json(client.post(URL, json=body))["runwayMonths"] is None
    closed = raw_json(client.post(URL, json=PDF_REQUEST))  # levers close a 6,000 gap
    assert closed["netMonthlyGap"] == 0 and closed["runwayMonths"] == 14.2
