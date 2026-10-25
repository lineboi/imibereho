"""`GET /seasonal-swaps` (contract §4)."""

from typing import Annotated

from pydantic import ConfigDict, Field

from app.schemas.benchmark import DistrictCodeParam
from app.schemas.common import ApiModel, JsonDecimal, Meta, QueryInt, QueryModel


class SeasonalSwapQuery(QueryModel):
    district: DistrictCodeParam
    month: Annotated[QueryInt, Field(ge=1, le=12)]


class SwapItem(ApiModel):
    name: str
    quantity: JsonDecimal
    unit: str
    price: int


class SwapOut(ApiModel):
    model_config = ConfigDict(alias_generator=None, populate_by_name=True)

    id: str
    title: str
    description: str
    from_: SwapItem = Field(serialization_alias="from")
    to: SwapItem
    difference: int
    footnote: str


class TipOut(ApiModel):
    title: str
    body: str


class SeasonalSwapResponse(ApiModel):
    items: list[SwapOut]
    tips: list[TipOut]
    meta: Meta
