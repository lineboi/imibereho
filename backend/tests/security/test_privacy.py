"""No citizen personal data is stored on the server (Q-02, Option A)."""

from typing import Final

from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select

import app.models  # noqa: F401
from app.db.base import Base
from app.db.seed import check
from app.db.session import Database
from app.models import SyntheticHousehold

# Server-side storage is limited to approved synthetic reference data and seed state.
APPROVED_TABLES: Final = frozenset(
    {
        "seed_state",
        "methodology_versions",
        "districts",
        "expense_categories",
        "reference_households",
        "budget_benchmarks",
        "seasonal_swaps",
        "seasonal_tips",
        "reference_periods",
        "household_groups",
        "monthly_series",
        "synthetic_households",
        "vulnerability_models",
        "vulnerability_bands",
        "district_vulnerability",
        # Published aggregate statistics with their source record (no individual data):
        "statistical_sources",
        "financial_inclusion_indicators",
        "financial_access_strand_districts",
        "survey_estimates",
    }
)
# Matched against whole `_`-separated tokens, so `footnote` or a district `name` do not match.
PERSONAL_TOKENS: Final = frozenset(
    {
        "email", "phone", "msisdn", "password", "firstname", "surname", "birth", "dob",
        "national", "address", "ip", "device", "user", "account", "latitude", "longitude",
        "expense", "expenses", "note", "notes", "gps", "contact",
    }
)  # fmt: skip
PERSONAL_NAMES: Final = frozenset({"first_name", "last_name", "full_name", "person_name"})
# Reviewed exemptions, one column at a time. These `notes` hold provenance annotations about a
# published statistic (e.g. "the report gives two counts"), written by us from the source
# document; they never hold user input. Any other `notes`/`note` column still fails.
REVIEWED_NON_PERSONAL_COLUMNS: Final = frozenset(
    {
        "statistical_sources.notes",
        "financial_inclusion_indicators.notes",
        "financial_access_strand_districts.notes",
        "survey_estimates.notes",
    }
)


def test_only_approved_tables_exist_in_the_models() -> None:
    assert set(Base.metadata.tables) == APPROVED_TABLES
    forbidden = {"users", "households", "budget_plans", "budget_plan_lines", "expenses"}
    assert not forbidden & set(Base.metadata.tables)


def test_no_column_looks_like_personal_data() -> None:
    offenders = [
        f"{table.name}.{column.name}"
        for table in Base.metadata.tables.values()
        for column in table.columns
        if column.name in PERSONAL_NAMES or set(column.name.split("_")) & PERSONAL_TOKENS
    ]
    unexplained = [name for name in offenders if name not in REVIEWED_NON_PERSONAL_COLUMNS]
    assert not unexplained, unexplained
    # Every exemption must still exist, so a stale entry cannot hide a future column.
    assert set(offenders) == REVIEWED_NON_PERSONAL_COLUMNS


def test_migrated_database_has_only_approved_tables(test_database: Database) -> None:
    with test_database.engine.connect() as connection:
        tables = set(inspect(connection).get_table_names()) - {"alembic_version"}
    assert tables == APPROVED_TABLES


def test_calculation_requests_write_nothing(db_client: TestClient, test_database: Database) -> None:
    with test_database.read_only_session() as session:
        before = session.scalar(select(func.count()).select_from(SyntheticHousehold))
    for _ in range(3):
        db_client.post(
            "/api/v1/calculations/household-shock",
            json={
                "baseline": {"monthlyIncome": 123_456, "monthlyEssentials": 1, "savings": 2},
                "shock": {"type": "income_fall", "incomeReductionPct": 20, "durationMonths": 3},
            },
        )
        db_client.post(
            "/api/v1/calculations/policy-scenario",
            json={
                "instrument": "monthly_cash_support",
                "incomeLossPct": 20,
                "durationMonths": 3,
                "supportPerHouseholdMonthly": 6_000,
                "eligibleHouseholds": 1_000,
            },
        )
    with test_database.read_only_session() as session:
        assert session.scalar(select(func.count()).select_from(SyntheticHousehold)) == before
    assert check(test_database) == []  # every table still equals the seed exactly
