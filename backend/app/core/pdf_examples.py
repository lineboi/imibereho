"""Example values from MISSING_APIS.pdf served as ILLUSTRATIVE data (contract v0.4 §11.7).

The project owner approved these on 2026-10-27 for frontend integration, with the provenance
label `PROVENANCE` and `meta.isIllustrative: true`. They are the PDF's own example responses
(26 October 2026), copied exactly. They are not observations, market prices or official
guidance, and nothing here is extended to districts or items the PDF does not show. The one
extension, approved by the owner, is BR-24 scaling of the Gasabo checklist to other household
sizes; the agro service does it and labels the result as modelled, not as a PDF value.

Versioned code constants, like the resilience catalogue: small, fixed per methodology version,
never joined with other data, so no seeded table or migration.
"""

from dataclasses import dataclass
from typing import Final, Literal

Provenance = Literal["MISSING_APIS.pdf example, owner-approved"]
PROVENANCE: Final[Provenance] = "MISSING_APIS.pdf example, owner-approved"
EXAMPLE_HOUSEHOLD_SIZE: Final = 4  # every PDF example basket and checklist is for 4 people

# --- Page 7: `district-comparison` example baskets (household size 4), by category code ---
# Gasabo's basket equals the seeded benchmark basket (a test pins this); Musanze's is the only
# other district basket the PDF gives.
DISTRICT_BASKETS: Final[dict[str, dict[str, int]]] = {
    "gasabo": {
        "food": 65_000, "housing": 40_000, "transport": 20_000, "utilities": 10_000,
        "other_essentials": 15_000,
    },
    "musanze": {
        "food": 50_000, "housing": 28_000, "transport": 14_000, "utilities": 9_000,
        "other_essentials": 14_000,
    },
}  # fmt: skip


# --- Page 7: `basket-details` example (Gasabo only) ---
@dataclass(frozen=True, slots=True)
class StaplePrices:
    irish_potatoes_per_kg: int
    sweet_potatoes_per_kg: int
    red_beans_per_kg: int


STAPLE_PRICES: Final = {"gasabo": StaplePrices(750, 800, 850)}
MARKET_HUBS: Final = {"gasabo": "Kimironko Market"}


# --- Page 10: `agro-savings-projection` purchasing-power equivalents ---
@dataclass(frozen=True, slots=True)
class PurchasingPowerItem:
    item: str
    unit_cost: int  # RWF per unit, implied by the example: 5,200 ÷ the example count
    field: str  # the PDF's key for the count: coversWeeks, ridesCount or quantity


# The example spends 5,200 RWF a month on 2 weeks of water, 8 bus rides or 26 eggs. The unit
# costs below are those divisions (2,600, 650 and 200 RWF), which reproduce the example exactly.
# They are implied by the example, not market prices.
EXAMPLE_MONTHLY_SAVINGS: Final = 5_200
PURCHASING_POWER: Final = (
    PurchasingPowerItem("WASAC Clean Water", 2_600, "coversWeeks"),
    PurchasingPowerItem("Kigali City Bus Rides", 650, "ridesCount"),
    PurchasingPowerItem("Fresh Farm Eggs", 200, "quantity"),
)


# --- Page 10: `nutrition/indyo-yuzuye` example ---
@dataclass(frozen=True, slots=True)
class PlateComponentExample:
    code: str
    name: str
    proportion_pct: int
    examples: tuple[str, ...]


PLATE_COMPONENTS: Final = (
    PlateComponentExample("energy", "Energy Staples", 50, ("Sweet potatoes", "Cassava")),
    PlateComponentExample("protective", "Protective Greens", 25, ("Dodo amaranth", "Isombe")),
    PlateComponentExample("protein", "Plant Protein", 25, ("Red beans", "Groundnuts")),
)
ENERGY_TIP: Final = "Boiling sweet potatoes alongside beans saves 35% charcoal fuel."


# --- Page 11: `market/shopping-checklist` example (Gasabo, household size 4) ---
@dataclass(frozen=True, slots=True)
class ChecklistItemExample:
    name: str
    amount: int  # the PDF's quantity, split so BR-24 can scale it: "3 kg" is 3 and "kg"
    unit: str
    est_price: int

    @property
    def quantity(self) -> str:
        return f"{self.amount} {self.unit}"


@dataclass(frozen=True, slots=True)
class ChecklistExample:
    items: tuple[ChecklistItemExample, ...]
    total_estimated_basket: int
    unoptimized_basket: int
    estimated_savings: int


# The PDF's totals are served as given. Its three items sum to 4,750, not 6,250, and the PDF
# does not say what else the basket holds, so the totals are not derived from the items.
CHECKLISTS: Final = {
    ("gasabo", EXAMPLE_HOUSEHOLD_SIZE): ChecklistExample(
        items=(
            ChecklistItemExample("Fresh Sweet Potatoes", 3, "kg", 2_400),
            ChecklistItemExample("Local Red Kidney Beans", 2, "kg", 1_700),
            ChecklistItemExample("Fresh Amaranth Greens (Dodo)", 3, "bundles", 650),
        ),
        total_estimated_basket=6_250,
        unoptimized_basket=8_650,
        estimated_savings=2_400,
    ),
}
