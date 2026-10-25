"""`POST /calculations/household-shock` (contract §4; BR-01 to BR-06).

Stateless: the request body is processed and discarded. Nothing is stored or logged (Q-02).
"""

from app.calculations import (
    monthly_balance,
    monthly_gap,
    runway_months,
    savings_drawdown,
    shocked_income,
)
from app.core.constants import HOUSEHOLD_SHOCK_ASSUMPTIONS
from app.schemas.common import Meta
from app.schemas.shock import HouseholdShockRequest, HouseholdShockResponse


class ShockService:
    def household_shock(self, request: HouseholdShockRequest) -> HouseholdShockResponse:
        baseline, shock = request.baseline, request.shock
        shocked = shocked_income(baseline.monthly_income, shock.income_reduction_pct)
        gap = monthly_gap(baseline.monthly_essentials, shocked)
        drawdown = savings_drawdown(baseline.savings, gap, shock.duration_months)
        return HouseholdShockResponse(
            baseline_monthly_balance=monthly_balance(
                baseline.monthly_income, baseline.monthly_essentials
            ),
            shocked_monthly_income=shocked,
            monthly_gap=gap,
            savings_used=drawdown.used,
            savings_remaining=drawdown.remaining,
            savings_exhausted=drawdown.exhausted,
            runway_months=runway_months(baseline.savings, gap),
            assumptions=list(HOUSEHOLD_SHOCK_ASSUMPTIONS),
            meta=Meta(),
        )


def get_shock_service() -> ShockService:
    return ShockService()
