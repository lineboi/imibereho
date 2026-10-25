"""`POST /calculations/policy-scenario` (contract §5; BR-01 to BR-03, BR-07, BR-08).

Deterministic and never stored ([PD] Q-19). An omitted baseline uses the seeded reference
household ([PD] Q-23).
"""

from typing import Annotated, Literal

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import (
    direct_transfer_budget,
    monthly_balance,
    monthly_gap,
    savings_after_horizon,
    shocked_income,
)
from app.core.constants import METHODOLOGY_VERSION, POLICY_SCENARIO_ASSUMPTIONS
from app.db.session import get_read_session
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.common import Meta
from app.schemas.policy_scenario import (
    BaselineUsed,
    Comparison,
    ComparisonRow,
    ComparisonRows,
    PolicyScenarioRequest,
    PolicyScenarioResponse,
)

COLUMNS = ["no_shock", "shock_only", "shock_with_support"]


class ReferenceHouseholdMissingError(RuntimeError):
    """The reference household is not seeded. `/ready` reports this as a failed seed check."""


class PolicyScenarioService:
    def __init__(self, reference: ReferenceDataRepository) -> None:
        self._reference = reference

    def _baseline(self, request: PolicyScenarioRequest) -> BaselineUsed:
        source: Literal["reference", "request"]
        if request.baseline is not None:
            income = request.baseline.monthly_income
            essentials = request.baseline.monthly_essentials
            savings = request.baseline.savings
            source = "request"
        else:
            household = self._reference.get_reference_household()
            if household is None:
                raise ReferenceHouseholdMissingError("reference household v0.1 is not seeded")
            income, essentials, savings = (
                household.monthly_income,
                household.monthly_essentials,
                household.savings,
            )
            source = "reference"
        return BaselineUsed(
            monthly_income=income, monthly_essentials=essentials, savings=savings, source=source
        )

    def simulate(self, request: PolicyScenarioRequest) -> PolicyScenarioResponse:
        base = self._baseline(request)
        months = request.duration_months
        support = request.support_per_household_monthly
        shocked = shocked_income(base.monthly_income, request.income_loss_pct)

        incomes = (base.monthly_income, shocked, shocked)
        supports = (0, 0, support)
        nets = (
            monthly_balance(incomes[0], base.monthly_essentials, supports[0]),
            monthly_balance(incomes[1], base.monthly_essentials, supports[1]),
            monthly_balance(incomes[2], base.monthly_essentials, supports[2]),
        )

        def row(values: tuple[int, int, int]) -> ComparisonRow:
            return ComparisonRow(
                no_shock=values[0], shock_only=values[1], shock_with_support=values[2]
            )

        return PolicyScenarioResponse(
            direct_transfer_budget=direct_transfer_budget(
                support, request.eligible_households, months
            ),
            modelled_monthly_gap_with_support=monthly_gap(
                base.monthly_essentials, shocked, support
            ),
            horizon_months=months,
            baseline_used=base,
            comparison=Comparison(
                columns=list(COLUMNS),
                rows=ComparisonRows(
                    income_per_month=row(incomes),
                    support_per_month=row(supports),
                    expenses_per_month=row(
                        (base.monthly_essentials, base.monthly_essentials, base.monthly_essentials)
                    ),
                    net_monthly_balance=row(nets),
                    savings_after_horizon=row(
                        (
                            savings_after_horizon(base.savings, nets[0], months),
                            savings_after_horizon(base.savings, nets[1], months),
                            savings_after_horizon(base.savings, nets[2], months),
                        )
                    ),
                ),
            ),
            assumptions=list(POLICY_SCENARIO_ASSUMPTIONS),
            meta=Meta(),
        )


def get_policy_scenario_service(
    session: Annotated[Session, Depends(get_read_session)],
) -> PolicyScenarioService:
    return PolicyScenarioService(ReferenceDataRepository(session, METHODOLOGY_VERSION))
