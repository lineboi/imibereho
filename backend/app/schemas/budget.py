"""Optional `POST /calculations/budget-comparison` (contract §6, BR-13, [PD] Q-09)."""

from typing import Annotated

from pydantic import Field, StrictInt

from app.core.constants import HOUSEHOLD_SIZE_MAX, HOUSEHOLD_SIZE_MIN
from app.schemas.benchmark import DistrictCodeParam
from app.schemas.common import ApiModel, BodyModel, Meta, Money


class PlanLine(BodyModel):
    category_code: Annotated[str, Field(max_length=64)]
    planned_amount: Money


class BudgetComparisonRequest(BodyModel):
    district: DistrictCodeParam
    household_size: Annotated[StrictInt, Field(ge=HOUSEHOLD_SIZE_MIN, le=HOUSEHOLD_SIZE_MAX)]
    plan: Annotated[list[PlanLine], Field(max_length=5)]


class ComparisonLineOut(ApiModel):
    category_code: str
    planned: int
    reference: int
    difference: int


class ComparisonTotals(ApiModel):
    planned: int
    reference: int
    difference: int


class LargestDifference(ApiModel):
    category_code: str
    difference: int


class BudgetComparisonResponse(ApiModel):
    lines: list[ComparisonLineOut]
    totals: ComparisonTotals
    largest_above: LargestDifference | None
    largest_below: LargestDifference | None
    meta: Meta
