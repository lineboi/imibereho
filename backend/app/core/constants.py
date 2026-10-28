"""Fixed values from the API contract (v0.2 rev 2) and methodology v0.1.

Three versions exist and are independent (contract §0):
the HTTP path version, the contract version mirrored in OpenAPI, and the methodology version.
"""

from typing import Final

API_PATH_VERSION: Final = "v1"
API_PREFIX: Final = f"/api/{API_PATH_VERSION}"
OPENAPI_VERSION: Final = "0.2.0"
METHODOLOGY_VERSION: Final = "0.1"

PROBLEM_TYPE_BASE: Final = "https://imibereho.example/errors/"
PROBLEM_MEDIA_TYPE: Final = "application/problem+json"
REQUEST_ID_HEADER: Final = "X-Request-ID"
CONTENT_LANGUAGE: Final = "en"

# Contract §1.2 and [PD] Q-20 bounds.
MONEY_MAX: Final = 100_000_000
HOUSEHOLD_SIZE_MIN: Final = 1
HOUSEHOLD_SIZE_MAX: Final = 20
PERCENT_MAX: Final = 100
DURATION_MIN: Final = 1
DURATION_MAX: Final = 24
LIST_LIMIT_MAX: Final = 30  # every list holds 30 items or fewer (contract §1)

# Official published statistics (not illustrative): the FinScope Rwanda 2024 report.
FINSCOPE_2024_SOURCE_ID: Final = "finscope-2024"
# Official published statistics: NISR's EICV7 (2023/24) Main Indicators Report annex tables.
EICV7_SOURCE_ID: Final = "eicv7-2023-2024"
EICV7_POVERTY_INDICATOR: Final = "poverty_headcount_rate"  # Table A9.23
EICV7_HEALTH_INSURANCE_INDICATOR: Final = "health_insurance_coverage"  # Table A3.7
# Official published statistics: NISR's Seasonal Agricultural Survey 2025 (crop-season calendar).
SAS_2025_SOURCE_ID: Final = "sas-2025"

# Contract §5 / [PD] Q-14: geography offers `all` only. Label from the design (`2:6774`).
GEOGRAPHY_ALL: Final = "all"
GEOGRAPHIES: Final = ((GEOGRAPHY_ALL, "All districts"),)

# The D1 essentials trend is one reference-household series ([PD] Q-33, [E] `2:6826`).
ESSENTIALS_TREND_SERIES: Final = "reference_household"

# D1 KPI "share in deficit after a 20% shock" ([E] `2:6805`).
DASHBOARD_SHOCK_PCT: Final = 20

# Income sources, labels as drawn in D1 ([E] `2:6864`).
INCOME_SOURCES: Final = (
    ("wage", "Wage income"),
    ("agriculture", "Agriculture"),
    ("informal_enterprise", "Informal enterprise"),
)

# Vulnerability components, labels as drawn in D2 ([E] `2:7079`).
VULNERABILITY_COMPONENTS: Final = (
    ("incomeInstability", "Income instability"),
    ("essentialCostPressure", "Essential-cost pressure"),
    ("lowBufferExposure", "Low-buffer exposure"),
)

HOUSEHOLD_SHOCK_ASSUMPTIONS: Final = (
    "expenses_held_constant",
    "no_new_borrowing",
    "no_additional_shocks",
)
POLICY_SCENARIO_ASSUMPTIONS: Final = (
    "surpluses_saved",
    "gaps_paid_from_savings",
    "no_interest",
    "no_debt",
    "no_admin_costs",
    "no_further_shocks",
    "no_behavioural_effects",
)
