"""Service business rules, isolated from the database with in-memory repositories."""

from decimal import Decimal

import pytest

from app.core.errors import (
    BenchmarkNotAvailableError,
    DistrictNotFoundError,
    RequestValidationProblem,
)
from app.schemas.budget import BudgetComparisonRequest
from app.schemas.dashboard import OverviewQuery
from app.schemas.policy_scenario import PolicyScenarioRequest
from app.schemas.shock import HouseholdShockRequest
from app.services.benchmark_service import BenchmarkService
from app.services.budget_service import BudgetService
from app.services.dashboard_service import DashboardService
from app.services.policy_scenario_service import (
    PolicyScenarioService,
    ReferenceHouseholdMissingError,
)
from app.services.seasonal_swap_service import SeasonalSwapService
from app.services.shock_service import ShockService
from app.services.vulnerability_service import (
    VulnerabilityDataMissingError,
    VulnerabilityService,
)

from .fakes import FakeBenchmarks, FakeReference, FakeSample


def shock_request(
    income: int, essentials: int, savings: int, pct: int, months: int
) -> HouseholdShockRequest:
    return HouseholdShockRequest.model_validate(
        {
            "baseline": {
                "monthlyIncome": income,
                "monthlyEssentials": essentials,
                "savings": savings,
            },
            "shock": {"type": "income_fall", "incomeReductionPct": pct, "durationMonths": months},
        }
    )


# --- household shock ---


def test_household_shock_design_values() -> None:
    result = ShockService().household_shock(shock_request(180_000, 150_000, 60_000, 20, 3))
    assert (
        result.baseline_monthly_balance,
        result.shocked_monthly_income,
        result.monthly_gap,
        result.savings_used,
        result.savings_remaining,
        result.savings_exhausted,
        result.runway_months,
    ) == (30_000, 144_000, 6_000, 18_000, 42_000, False, Decimal("10.0"))
    assert result.assumptions == [
        "expenses_held_constant",
        "no_new_borrowing",
        "no_additional_shocks",
    ]


def test_household_shock_without_a_gap_has_no_runway() -> None:
    result = ShockService().household_shock(shock_request(180_000, 150_000, 60_000, 0, 3))
    assert (result.monthly_gap, result.runway_months, result.savings_used) == (0, None, 0)


def test_household_shock_with_no_savings_is_exhausted() -> None:
    result = ShockService().household_shock(shock_request(180_000, 150_000, 0, 20, 3))
    assert result.savings_exhausted is True and result.runway_months == Decimal("0.0")


# --- benchmarks ---


def test_benchmark_design_values() -> None:
    result = BenchmarkService(FakeReference(), FakeBenchmarks()).get_benchmark("gasabo", 4)
    assert [line.monthly_amount for line in result.lines] == [
        65_000,
        40_000,
        20_000,
        10_000,
        15_000,
    ]
    assert result.total == 150_000 and result.district.name == "Gasabo"


def test_benchmark_unknown_district_is_404_before_benchmark_lookup() -> None:
    with pytest.raises(DistrictNotFoundError):
        BenchmarkService(FakeReference(), FakeBenchmarks()).get_benchmark("atlantis", 4)


def test_benchmark_for_another_household_size_is_not_available() -> None:
    with pytest.raises(BenchmarkNotAvailableError):
        BenchmarkService(FakeReference(), FakeBenchmarks()).get_benchmark("gasabo", 3)


def test_district_and_category_lists_carry_counts() -> None:
    service = BenchmarkService(FakeReference(), FakeBenchmarks())
    assert service.list_districts().meta.count == 2
    assert service.list_categories().meta.count == 5


# --- budget comparison (optional O2) ---


def budget_request(
    plan: list[tuple[str, int]], district: str = "gasabo"
) -> BudgetComparisonRequest:
    return BudgetComparisonRequest.model_validate(
        {
            "district": district,
            "householdSize": 4,
            "plan": [{"categoryCode": c, "plannedAmount": a} for c, a in plan],
        }
    )


DESIGN_PLAN = [
    ("food", 60_000),
    ("housing", 45_000),
    ("transport", 18_000),
    ("utilities", 12_000),
    ("other_essentials", 15_000),
]


def budget_service(reference: FakeReference | None = None) -> BudgetService:
    reference = reference or FakeReference()
    return BudgetService(reference, BenchmarkService(reference, FakeBenchmarks()))


def test_budget_comparison_design_values() -> None:
    result = budget_service().compare(budget_request(DESIGN_PLAN))
    assert result.largest_above is not None and result.largest_below is not None
    assert (result.largest_above.category_code, result.largest_above.difference) == (
        "housing",
        5_000,
    )
    assert (result.largest_below.category_code, result.largest_below.difference) == ("food", -5_000)
    assert (result.totals.planned, result.totals.reference, result.totals.difference) == (
        150_000,
        150_000,
        0,
    )


def test_budget_comparison_missing_and_duplicate_categories_are_422_before_lookup() -> None:
    reference = FakeReference()
    plan = [*DESIGN_PLAN[:3], ("food", 1)]
    with pytest.raises(RequestValidationProblem) as excinfo:
        budget_service(reference).compare(budget_request(plan, district="atlantis"))
    fields = [(e.field, e.code) for e in excinfo.value.errors or []]
    assert fields == [("plan.3.categoryCode", "unknown_value"), ("plan", "required")]
    assert reference.district_lookups == 0  # validation happened before the district lookup


def test_budget_comparison_unknown_district_is_404() -> None:
    with pytest.raises(DistrictNotFoundError):
        budget_service().compare(budget_request(DESIGN_PLAN, district="atlantis"))


# --- seasonal swaps ---


def test_seasonal_swap_difference_and_empty_month() -> None:
    service = SeasonalSwapService(FakeReference())
    october = service.list_swaps("gasabo", 10)
    assert october.items[0].difference == 400
    march = service.list_swaps("gasabo", 3)
    assert march.items == [] and len(march.tips) == 1


def test_seasonal_swap_unknown_district() -> None:
    with pytest.raises(DistrictNotFoundError):
        SeasonalSwapService(FakeReference()).list_swaps("atlantis", 10)


# --- vulnerability ---


def test_ranking_breaks_ties_by_name() -> None:
    reference = FakeReference({"rutsiro": 60, "ngoma": 60, "nyagatare": 74, "gasabo": 46})
    _, items = VulnerabilityService(reference).ranked_scores("2026-10", "all", "-score", 30)
    assert [(i.district_code, i.score) for i in items] == [
        ("nyagatare", 74),
        ("ngoma", 60),
        ("rutsiro", 60),
        ("gasabo", 46),
    ]


def test_list_is_alphabetical_by_default_and_limited() -> None:
    reference = FakeReference({"rutsiro": 60, "ngoma": 60, "bugesera": 71})
    result = VulnerabilityService(reference).list_scores("2026-10", "all", "name", 2)
    assert [i.district_code for i in result.items] == ["bugesera", "ngoma"]
    assert result.meta.count == 2


def test_invalid_filters_are_422_before_the_district_lookup() -> None:
    reference = FakeReference()
    with pytest.raises(RequestValidationProblem) as excinfo:
        VulnerabilityService(reference).get_detail("atlantis", "2026-09", "wage")
    assert [(e.field, e.code) for e in excinfo.value.errors or []] == [
        ("period", "unknown_value"),
        ("householdGroup", "unknown_value"),
    ]
    assert reference.district_lookups == 0


def test_gasabo_detail_matches_the_design() -> None:
    detail = VulnerabilityService(FakeReference()).get_detail("gasabo", "2026-10", "all")
    assert (detail.score, detail.band) == (46, "band2")
    assert [(c.code, c.weight, c.value) for c in detail.components] == [
        ("incomeInstability", Decimal("0.40"), 50),
        ("essentialCostPressure", Decimal("0.40"), 40),
        ("lowBufferExposure", Decimal("0.20"), 50),
    ]


def test_missing_vulnerability_model_is_an_internal_error_not_fake_data() -> None:
    with pytest.raises(VulnerabilityDataMissingError):
        VulnerabilityService(FakeReference(with_model=False)).list_scores(
            "2026-10", "all", "name", 30
        )


# --- policy scenario ---


def policy_request(**overrides: object) -> PolicyScenarioRequest:
    body: dict[str, object] = {
        "instrument": "monthly_cash_support",
        "incomeLossPct": 20,
        "durationMonths": 3,
        "supportPerHouseholdMonthly": 6_000,
        "eligibleHouseholds": 1_000,
    }
    body.update(overrides)
    return PolicyScenarioRequest.model_validate(body)


def test_policy_scenario_design_matrix() -> None:
    result = PolicyScenarioService(FakeReference()).simulate(policy_request())
    rows = result.comparison.rows
    assert result.direct_transfer_budget == 18_000_000
    assert result.modelled_monthly_gap_with_support == 0
    assert result.baseline_used.source == "reference"
    assert (rows.income_per_month.no_shock, rows.income_per_month.shock_only) == (180_000, 144_000)
    assert rows.support_per_month.shock_with_support == 6_000
    assert (rows.net_monthly_balance.no_shock, rows.net_monthly_balance.shock_only) == (
        30_000,
        -6_000,
    )
    assert rows.net_monthly_balance.shock_with_support == 0
    assert (
        rows.savings_after_horizon.no_shock,
        rows.savings_after_horizon.shock_only,
        rows.savings_after_horizon.shock_with_support,
    ) == (150_000, 42_000, 60_000)


def test_policy_scenario_uses_a_supplied_baseline_and_allows_negative_savings() -> None:
    baseline = {"monthlyIncome": 100_000, "monthlyEssentials": 150_000, "savings": 10_000}
    result = PolicyScenarioService(FakeReference(with_household=False)).simulate(
        policy_request(baseline=baseline, supportPerHouseholdMonthly=0)
    )
    assert result.baseline_used.source == "request"
    assert result.comparison.rows.savings_after_horizon.shock_only == 10_000 + 3 * (
        80_000 - 150_000
    )


def test_policy_scenario_without_reference_household_fails_loudly() -> None:
    with pytest.raises(ReferenceHouseholdMissingError):
        PolicyScenarioService(FakeReference(with_household=False)).simulate(policy_request())


# --- dashboard ---


def test_dashboard_overview_design_values() -> None:
    reference = FakeReference({"nyagatare": 74, "bugesera": 71, "gasabo": 46})
    overview = DashboardService(reference, FakeSample()).overview(OverviewQuery())
    assert overview.kpis.sample_size == 3_000
    assert overview.kpis.essentials_to_income_ratio == Decimal("0.8333")
    assert overview.kpis.shock_deficit.households_in_deficit == 1_000
    assert overview.kpis.shock_deficit.share == Decimal("0.3333")
    assert [(s.code, s.households, s.share) for s in overview.income_sources] == [
        ("wage", 1_200, Decimal("0.4000")),
        ("agriculture", 1_050, Decimal("0.3500")),
        ("informal_enterprise", 750, Decimal("0.2500")),
    ]
    assert (overview.insight.baseline_monthly_balance, overview.insight.shock_monthly_gap) == (
        30_000,
        6_000,
    )
    assert [(d.code, d.score, d.band) for d in overview.top_districts] == [
        ("nyagatare", 74, "band4"),
        ("bugesera", 71, "band4"),
    ]


@pytest.mark.parametrize(
    ("query", "field"),
    [({"geography": "gasabo"}, "geography"), ({"geography": "atlantis"}, "geography"),
     ({"period": "2026-09"}, "period"), ({"householdGroup": "wage"}, "householdGroup")],
)  # fmt: skip
def test_dashboard_unlisted_filters_are_422(query: dict[str, str], field: str) -> None:
    with pytest.raises(RequestValidationProblem) as excinfo:
        DashboardService(FakeReference(), FakeSample()).overview(
            OverviewQuery.model_validate(query)
        )
    assert [(e.field, e.code) for e in excinfo.value.errors or []] == [(field, "unknown_value")]


def test_dashboard_filters_offer_only_the_defaults() -> None:
    filters = DashboardService(FakeReference(), FakeSample()).filters()
    assert [(g.code, g.is_default) for g in filters.geographies] == [("all", True)]
    assert [p.code for p in filters.periods] == ["2026-10"]
    assert [g.code for g in filters.household_groups] == ["all"]
