"""Strict number types and the illustrative envelope (contract §1, §1.1, §1.2)."""

import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.common import ApiModel, Baseline, JsonDecimal, ListMeta, Meta


class _Ratio(ApiModel):
    value: JsonDecimal


@pytest.mark.parametrize(
    ("value", "text"), [("0.8333", "0.8333"), ("10.0", "10.0"), ("0.40", "0.4")]
)
def test_json_decimal_serialises_as_a_json_number(value: str, text: str) -> None:
    raw = _Ratio(value=Decimal(value)).model_dump_json()
    assert raw == f'{{"value":{text}}}'
    assert isinstance(json.loads(raw)["value"], float)


def test_json_decimal_is_typed_number_in_the_serialisation_schema() -> None:
    schema = _Ratio.model_json_schema(mode="serialization")
    assert schema["properties"]["value"]["type"] == "number"


def test_meta_envelope() -> None:
    assert Meta().model_dump(by_alias=True) == {"isIllustrative": True, "methodologyVersion": "0.1"}
    assert ListMeta(count=30).model_dump(by_alias=True)["count"] == 30


def test_meta_cannot_claim_non_illustrative_data() -> None:
    with pytest.raises(ValidationError):
        Meta(is_illustrative=False)  # type: ignore[arg-type]


def test_body_models_accept_only_camel_case_names() -> None:
    Baseline.model_validate({"monthlyIncome": 1, "monthlyEssentials": 2, "savings": 3})
    with pytest.raises(ValidationError) as excinfo:
        Baseline.model_validate({"monthly_income": 1, "monthlyEssentials": 2, "savings": 3})
    types = {error["type"] for error in excinfo.value.errors()}
    assert types == {"extra_forbidden", "missing"}
