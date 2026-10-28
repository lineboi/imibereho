"""The household's saved resilience plan (contract §11.11, MISSING_APIS.pdf inventory item 17).

The PDF names `POST /user/resilience-plan` but gives it no body. On 2026-10-28 the project owner
chose to store it behind login, so the backend defined it: the request is exactly the
`POST /calculations/resilience-simulation` request, and the response echoes the saved inputs
with that simulation's figures recomputed from them (`simulation`), when it was saved, and `meta`.
"""

from pydantic import Field

from app.schemas.common import ApiModel, ExampleMeta
from app.schemas.resilience import CopingLeverId, ResilienceSimulationResult, ShockId


class SavedBaseline(ApiModel):
    monthly_income: int
    monthly_essentials: int
    savings: int


class SavedShock(ApiModel):
    type: ShockId
    income_reduction_pct: int | None = Field(description="Null for lump-sum shocks")
    duration_months: int
    amount: int | None = Field(
        description="As sent: null for income shocks, and for a lump-sum shock that used the "
        "catalogue's defaultAmount"
    )


class ResiliencePlanResponse(ApiModel):
    baseline: SavedBaseline
    shock: SavedShock
    active_coping_levers: list[CopingLeverId]
    simulation: ResilienceSimulationResult = Field(
        description="The resilience simulation of these inputs, recomputed on every read"
    )
    saved_at: str = Field(description="When the plan was last saved, ISO 8601 in UTC")
    meta: ExampleMeta
