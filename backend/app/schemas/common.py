"""Shared request/response types implementing contract §1, §1.1 and §1.2.

- `BodyModel`: JSON bodies. camelCase field names only, unknown fields rejected, integers strict
  (strings, fractions, `4.0` and booleans are `not_integer`).
- `QueryModel`: query strings. Unknown parameters rejected (400 `unknown-parameter`).
- `QueryInt`: digits only (`^[0-9]+$` after URL decoding), then bounds.
- `JsonDecimal`: a `Decimal` always emitted as a JSON number, never a string.
- `Meta` / `ListMeta`: the illustrative envelope; `ExampleMeta` / `ExampleListMeta` add the
  provenance of owner-approved PDF example values.
"""

import re
from decimal import Decimal
from typing import Annotated, Final, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer, StrictInt
from pydantic.alias_generators import to_camel
from pydantic_core import PydanticCustomError

from app.core.constants import METHODOLOGY_VERSION, MONEY_MAX
from app.core.pdf_examples import Provenance

_DIGITS: Final = re.compile(r"[0-9]+")
_MAX_DIGITS: Final = 12  # anything longer is far out of every bound; avoids huge int parsing


def _parse_query_int(value: object) -> object:
    if isinstance(value, int) and not isinstance(value, bool):
        return value  # defaults declared in code
    if not isinstance(value, str) or not _DIGITS.fullmatch(value):
        raise PydanticCustomError("not_integer", "Must be a whole number.")
    if len(value) > _MAX_DIGITS:
        raise PydanticCustomError("out_of_range", "Value is out of range.")
    return int(value)


QueryInt = Annotated[int, BeforeValidator(_parse_query_int)]
JsonDecimal = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
Money = Annotated[StrictInt, Field(ge=0, le=MONEY_MAX)]


class ApiModel(BaseModel):
    """Response models: Python names in code, camelCase on the wire."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BodyModel(BaseModel):
    """Request bodies: only camelCase names are accepted; extra fields are refused."""

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", validate_by_name=False)


class QueryModel(BaseModel):
    """Query parameters, declared with their wire (camelCase) names."""

    model_config = ConfigDict(extra="forbid")


class NoQuery(QueryModel):
    """For endpoints that define no query parameters: any parameter is a 400."""


class Meta(ApiModel):
    is_illustrative: Literal[True] = True
    methodology_version: Literal["0.1"] = METHODOLOGY_VERSION


class ListMeta(Meta):
    count: int


class ExampleMeta(Meta):
    """The illustrative envelope of a response that may serve owner-approved PDF example values."""

    provenance: Provenance | None = Field(
        description="Set when the response serves MISSING_APIS.pdf example values (contract "
        "§11.7); null when it serves none"
    )


class ExampleListMeta(ExampleMeta):
    count: int


class Baseline(BodyModel):
    """A household baseline in whole RWF (contract §4, [PD] Q-20)."""

    monthly_income: Money
    monthly_essentials: Money
    savings: Money
