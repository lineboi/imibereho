"""Shock catalogue and resilience simulation (contract v0.4 §11.1; BR-02 to BR-06, BR-17 to BR-19).

Stateless: the request body is processed and discarded. Nothing is stored or logged (Q-02).
Every total, relief amount and score is computed here; the client sends only its baseline, the
shock parameters and the lever ids, and lever amounts always come from the catalogue.
"""

from app.calculations import (
    monthly_gap,
    net_monthly_gap,
    resilience_score,
    runway_months,
    savings_drawdown,
    shocked_income,
    spread_monthly,
)
from app.core.errors import FieldError, RequestValidationProblem
from app.core.pdf_examples import PROVENANCE
from app.core.resilience_catalog import COPING_LEVERS, LEVERS_BY_ID, SHOCKS, SHOCKS_BY_ID
from app.schemas.common import ExampleListMeta, ExampleMeta
from app.schemas.resilience import (
    CopingLeverItem,
    ResilienceSimulationRequest,
    ResilienceSimulationResponse,
    ShockCatalog,
    ShockCatalogItem,
)

ASSUMPTIONS = (
    "illustrative_parameters_not_observations",
    "expenses_held_constant",
    "lump_sum_spread_evenly_over_duration",
    "lever_amounts_from_catalogue",
    "no_new_borrowing",
    "no_additional_shocks",
    "resilience_score_is_br_19_the_pdf_example_figures_are_not_derivable",
)
HARVEST_AS_INCOME = "harvest_disruption_modelled_as_a_loss_of_income"


def _validate(request: ResilienceSimulationRequest) -> None:
    """Cross-field rules (422 `validation`), checked before any calculation."""
    errors: list[FieldError] = []
    shock = request.shock
    if SHOCKS_BY_ID[shock.type].is_lump_sum:
        if shock.income_reduction_pct is not None:
            errors.append(
                FieldError(
                    "shock.incomeReductionPct",
                    "unknown_field",
                    "Not used by a lump-sum shock.",
                )
            )
    else:
        if shock.income_reduction_pct is None:
            errors.append(
                FieldError("shock.incomeReductionPct", "required", "This field is required.")
            )
        if shock.amount is not None:
            errors.append(
                FieldError("shock.amount", "unknown_field", "Only lump-sum shocks take an amount.")
            )
    seen: set[str] = set()
    for index, lever in enumerate(request.active_coping_levers):
        if lever in seen:
            errors.append(
                FieldError(
                    f"activeCopingLevers.{index}",
                    "unknown_value",
                    "Each lever may appear once.",
                )
            )
        seen.add(lever)
    if errors:
        raise RequestValidationProblem(errors)


class ResilienceService:
    def catalog(self) -> ShockCatalog:
        items = [
            ShockCatalogItem(
                id=shock.id,
                title=shock.title,
                is_lump_sum=shock.is_lump_sum,
                default_pct=shock.default_pct,
                default_duration=shock.default_duration,
                default_amount=shock.default_amount,
            )
            for shock in SHOCKS
        ]
        levers = [
            CopingLeverItem(id=lever.id, title=lever.title, kind=lever.kind, amount=lever.amount)
            for lever in COPING_LEVERS
        ]
        return ShockCatalog(
            items=items,
            coping_levers=levers,
            meta=ExampleListMeta(count=len(items), provenance=PROVENANCE),
        )

    def simulate(self, request: ResilienceSimulationRequest) -> ResilienceSimulationResponse:
        _validate(request)
        baseline, shock = request.baseline, request.shock
        definition = SHOCKS_BY_ID[shock.type]
        if definition.is_lump_sum:
            amount = shock.amount if shock.amount is not None else definition.default_amount
            if amount is None:  # every lump-sum catalogue entry has a default
                raise RuntimeError(f"catalogue shock {definition.id} has no default amount")
            shocked, shock_cost = (
                baseline.monthly_income,
                spread_monthly(amount, shock.duration_months),
            )
        else:
            if shock.income_reduction_pct is None:  # rejected by _validate
                raise RuntimeError("income shock without a reduction")
            shocked = shocked_income(baseline.monthly_income, shock.income_reduction_pct)
            shock_cost = 0
        raw_gap = monthly_gap(baseline.monthly_essentials + shock_cost, shocked)
        levers = [LEVERS_BY_ID[lever_id] for lever_id in request.active_coping_levers]
        relief = sum(lever.amount for lever in levers if lever.kind == "monthly_relief")
        support = sum(lever.amount for lever in levers if lever.kind == "one_off_support")
        net_gap = net_monthly_gap(raw_gap, relief)
        buffer = baseline.savings + support
        drawdown = savings_drawdown(buffer, net_gap, shock.duration_months)
        score = resilience_score(raw_gap, len(levers), net_gap)
        return ResilienceSimulationResponse(
            raw_monthly_gap=raw_gap,
            coping_relief_monthly=relief,
            lump_sum_support=support,
            net_monthly_gap=net_gap,
            total_effective_buffer=buffer,
            # The PDF's runway (owner-approved 2026-10-27): how long the buffer covers the raw gap,
            # i.e. if the levers did not work. Null only when there is no raw gap.
            runway_months=runway_months(buffer, raw_gap),
            resilience_score=score.score,
            score_change=score.change,
            shock_cost_monthly=shock_cost,
            savings_used=drawdown.used,
            savings_remaining=drawdown.remaining,
            savings_exhausted=drawdown.exhausted,
            assumptions=[
                *ASSUMPTIONS,
                *([HARVEST_AS_INCOME] if shock.type == "harvest_disruption" else []),
            ],
            meta=ExampleMeta(provenance=PROVENANCE),
        )


def get_resilience_service() -> ResilienceService:
    return ResilienceService()
