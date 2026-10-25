"""Seasonal swap and tip (C5). Text as given in contract §4, which cites `2:6698` and `2:6714`.

[PD] Q-32: the swap applies to every district (district NULL) in month 10 only; the tip applies to
every district and month. Prices are invented in the design itself ("not market observations").
"""

from decimal import Decimal
from typing import Final

from app.core.constants import METHODOLOGY_VERSION
from app.data.registry import Dataset, TableRows
from app.models import SeasonalSwap, SeasonalTip

SWAP: Final = {
    "id": "rice-to-sweet-potato",
    "district_code": None,
    "month": 10,
    "title": "Try a different staple",
    "description": (
        "For one household meal, consider sweet potatoes instead of rice. "
        "Pair with beans and leafy vegetables."
    ),
    "footnote": (
        "Different quantities; not a nutritional equivalent. "
        "Prices are invented, not market observations."
    ),
    "from_name": "Rice",
    "from_quantity": Decimal("1"),
    "from_unit": "kg",
    "from_price": 2_000,
    "to_name": "Sweet potatoes",
    "to_quantity": Decimal("2"),
    "to_unit": "kg",
    "to_price": 1_600,
    "sort_order": 1,
}

TIP: Final = {
    "id": "keep-variety",
    "district_code": None,
    "month": None,
    "title": "Keep variety on the plate.",
    "body": (
        "Beans, amaranth leaves (dodo) and a locally available staple can offer variety. "
        "Consider cooking fuel, storage, dietary needs and portions for your household."
    ),
    "sort_order": 1,
}


def _seasonal() -> tuple[TableRows, ...]:
    version = {"methodology_version": METHODOLOGY_VERSION}
    return (
        TableRows(SeasonalSwap, "methodology_version", ({**version, **SWAP},)),
        TableRows(SeasonalTip, "methodology_version", ({**version, **TIP},)),
    )


DATASETS: Final = (Dataset("seasonal", _seasonal),)
