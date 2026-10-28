"""SQLAlchemy models. Importing this package registers every table on `Base.metadata`.

The server stores approved synthetic reference data, official statistics, operational seed state,
household accounts (contract §11.8, §11.9), their tracker transactions (§11.10) and their saved
resilience plan (§11.11): the data a person sends that is stored.
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
from app.models.resilience_plan import ResiliencePlan
from app.models.seasonal_swap import SeasonalSwap, SeasonalTip
from app.models.seed_state import SeedState
from app.models.tracker_transaction import TrackerTransaction
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
    "ResiliencePlan",
    "SeasonalSwap",
    "SeasonalTip",
    "SeedState",
    "StatisticalSource",
    "SurveyEstimate",
    "SyntheticHousehold",
    "TrackerTransaction",
    "VulnerabilityBand",
    "VulnerabilityModel",
]
