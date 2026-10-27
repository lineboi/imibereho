"""Stress-test scenarios for the district basket (contract v0.4 §11.3, methodology v0.1).

ILLUSTRATIVE "what if" price shocks, not forecasts. Provenance: MISSING_APIS.pdf page 8
("food inflation +15%, rent surge +10%"; the example scenario id `food_inflation_15`). The
frontend's stress chips use the same two percentages. Versioned code constants, like the
resilience catalogue: small, fixed per methodology version, and used to validate requests.
"""

from typing import Final

# scenario id -> {category code: percentage increase}
STRESS_SCENARIOS: Final[dict[str, dict[str, int]]] = {
    "food_inflation_15": {"food": 15},
    "rent_surge_10": {"housing": 10},
}
