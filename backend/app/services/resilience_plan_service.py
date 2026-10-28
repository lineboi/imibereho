"""Save, read and delete the household's resilience plan (contract §11.11).

A plan is the inputs of one resilience simulation. Saving validates and simulates them exactly as
`POST /calculations/resilience-simulation` does (so a plan that saves is one that simulates), then
stores the inputs with one upsert: one plan per account, a new save replaces the old one. Reads
recompute the simulation from the stored inputs, so the figures always match them. Order: token
(401), body validation (422). Nothing about the plan is logged.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.errors import NotAuthenticatedError, ResiliencePlanNotFoundError
from app.core.pdf_examples import PROVENANCE
from app.db.session import get_read_session, get_write_session
from app.models.resilience_plan import ResiliencePlan
from app.repositories.resilience_plan_repository import (
    AccountGoneError,
    PlanInputs,
    ResiliencePlanRepository,
)
from app.schemas.common import ExampleMeta
from app.schemas.resilience import ResilienceSimulationRequest, ResilienceSimulationResult
from app.schemas.resilience_plan import ResiliencePlanResponse, SavedBaseline, SavedShock
from app.services.current_account import CurrentAccount
from app.services.resilience_service import ResilienceService


def _wire_time(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _request_of(plan: ResiliencePlan) -> ResilienceSimulationRequest:
    """The stored inputs as the simulation request they were saved from."""
    return ResilienceSimulationRequest.model_validate(
        {
            "baseline": {
                "monthlyIncome": plan.monthly_income,
                "monthlyEssentials": plan.monthly_essentials,
                "savings": plan.savings,
            },
            "shock": {
                "type": plan.shock_type,
                "incomeReductionPct": plan.income_reduction_pct,
                "durationMonths": plan.duration_months,
                "amount": plan.shock_amount,
            },
            "activeCopingLevers": list(plan.coping_levers),
        }
    )


class ResiliencePlanService:
    def __init__(self, session: Session, simulator: ResilienceService) -> None:
        self._repository = ResiliencePlanRepository(session)
        self._simulator = simulator

    def _response(self, plan: ResiliencePlan) -> ResiliencePlanResponse:
        request = _request_of(plan)
        simulation = self._simulator.simulate(request)
        return ResiliencePlanResponse(
            baseline=SavedBaseline(
                monthly_income=plan.monthly_income,
                monthly_essentials=plan.monthly_essentials,
                savings=plan.savings,
            ),
            shock=SavedShock(
                type=request.shock.type,
                income_reduction_pct=plan.income_reduction_pct,
                duration_months=plan.duration_months,
                amount=plan.shock_amount,
            ),
            active_coping_levers=request.active_coping_levers,
            simulation=ResilienceSimulationResult.model_validate(
                simulation.model_dump(exclude={"meta"})
            ),
            saved_at=_wire_time(plan.updated_at or plan.created_at),
            meta=ExampleMeta(provenance=PROVENANCE),
        )

    def save(
        self, account: CurrentAccount, body: ResilienceSimulationRequest
    ) -> tuple[ResiliencePlanResponse, bool]:
        """The saved plan, and whether this save created it (201) rather than replaced it (200)."""
        self._simulator.simulate(body)  # the simulator's 422s, before anything is written
        inputs = PlanInputs(
            monthly_income=body.baseline.monthly_income,
            monthly_essentials=body.baseline.monthly_essentials,
            savings=body.baseline.savings,
            shock_type=body.shock.type,
            income_reduction_pct=body.shock.income_reduction_pct,
            duration_months=body.shock.duration_months,
            shock_amount=body.shock.amount,
            coping_levers=list(body.active_coping_levers),
        )
        try:
            plan, created = self._repository.save(account.id, inputs)
        except AccountGoneError:
            # The account was deleted after its token was checked: the same 401 as any token
            # whose account no longer exists.
            raise NotAuthenticatedError from None
        return self._response(plan), created

    def get(self, account: CurrentAccount) -> ResiliencePlanResponse:
        plan = self._repository.get(account.id)
        if plan is None:
            raise ResiliencePlanNotFoundError
        return self._response(plan)

    def delete(self, account: CurrentAccount) -> None:
        if not self._repository.delete(account.id):
            raise ResiliencePlanNotFoundError


def get_plan_reader(
    session: Annotated[Session, Depends(get_read_session)],
) -> ResiliencePlanService:
    return ResiliencePlanService(session, ResilienceService())


def get_plan_writer(
    session: Annotated[Session, Depends(get_write_session)],
) -> ResiliencePlanService:
    return ResiliencePlanService(session, ResilienceService())
