"""Reference data and budget benchmarks (contract §3, §4)."""

from typing import Annotated

from pydantic import Field

from app.core.constants import HOUSEHOLD_SIZE_MAX, HOUSEHOLD_SIZE_MIN
from app.schemas.common import ApiModel, ListMeta, Meta, QueryInt, QueryModel

DistrictCodeParam = Annotated[str, Field(max_length=64)]


class DistrictItem(ApiModel):
    code: str
    name: str
    province: str | None


class DistrictList(ApiModel):
    items: list[DistrictItem]
    meta: ListMeta


class ExpenseCategoryItem(ApiModel):
    code: str
    name: str
    icon: str | None


class ExpenseCategoryList(ApiModel):
    items: list[ExpenseCategoryItem]
    meta: ListMeta


class BenchmarkQuery(QueryModel):
    district: DistrictCodeParam
    householdSize: Annotated[QueryInt, Field(ge=HOUSEHOLD_SIZE_MIN, le=HOUSEHOLD_SIZE_MAX)]


class DistrictRef(ApiModel):
    code: str
    name: str


class BenchmarkLine(ApiModel):
    category_code: str
    monthly_amount: int


class BudgetBenchmarkResponse(ApiModel):
    district: DistrictRef
    household_size: int
    lines: list[BenchmarkLine]
    total: int
    meta: Meta
