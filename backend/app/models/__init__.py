"""SQLAlchemy models. Importing this package registers every table on `Base.metadata`.

The server stores approved synthetic reference data, official statistics, operational seed state
and, since contract §11.8, household accounts (the only data a person sends that is stored).
"""

from app.models.benchmark import BudgetBenchmark
from app.models.household_account import HouseholdAccount
from app.models.household_profile import ReferenceHousehold, SyntheticHousehold
from app.models.official_statistics import (
    FinancialAccessStrandDistrict,
    FinancialInclusionIndicator,
    StatisticalSource,
    SurveyEstimate,
)
from app.models.reference_data import (
    District,
    ExpenseCategory,
    HouseholdGroup,
    MethodologyVersion,
    MonthlySeriesPoint,
    ReferencePeriod,
)
from app.models.seasonal_swap import SeasonalSwap, SeasonalTip
from app.models.seed_state import SeedState
from app.models.vulnerability import DistrictVulnerability, VulnerabilityBand, VulnerabilityModel

__all__ = [
    "BudgetBenchmark",
    "District",
    "DistrictVulnerability",
    "ExpenseCategory",
    "FinancialAccessStrandDistrict",
    "FinancialInclusionIndicator",
    "HouseholdAccount",
    "HouseholdGroup",
    "MethodologyVersion",
    "MonthlySeriesPoint",
    "ReferenceHousehold",
    "ReferencePeriod",
    "SeasonalSwap",
    "SeasonalTip",
    "SeedState",
    "StatisticalSource",
    "SurveyEstimate",
    "SyntheticHousehold",
    "VulnerabilityBand",
    "VulnerabilityModel",
]
