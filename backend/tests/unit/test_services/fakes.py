"""In-memory stand-ins for the repositories, holding transient (session-less) model instances."""

from collections.abc import Sequence
from decimal import Decimal
from typing import cast

from sqlalchemy.orm import Session

from app.models import (
    BudgetBenchmark,
    District,
    DistrictVulnerability,
    ExpenseCategory,
    HouseholdGroup,
    MonthlySeriesPoint,
    ReferenceHousehold,
    ReferencePeriod,
    SeasonalSwap,
    SeasonalTip,
    VulnerabilityBand,
    VulnerabilityModel,
)
from app.repositories.benchmark_repository import BenchmarkRepository
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.repositories.shock_repository import ShockRepository

NO_SESSION = cast(Session, None)
CATEGORY_CODES = ("food", "housing", "transport", "utilities", "other_essentials")


class FakeReference(ReferenceDataRepository):
    def __init__(
        self,
        scores: dict[str, int] | None = None,
        *,
        with_model: bool = True,
        with_household: bool = True,
    ) -> None:
        super().__init__(NO_SESSION, "0.1")
        self.scores = scores if scores is not None else {"gasabo": 46, "nyagatare": 74}
        self.with_model = with_model
        self.with_household = with_household
        self.district_lookups = 0

    def list_districts(self) -> Sequence[District]:
        return [District(code=c, name=c.title(), province=None) for c in sorted(self.scores)]

    def get_district(self, code: str) -> District | None:
        self.district_lookups += 1
        return (
            District(code=code, name=code.title(), province=None) if code in self.scores else None
        )

    def list_categories(self) -> Sequence[ExpenseCategory]:
        return [
            ExpenseCategory(code=code, name_en=code.title(), icon=None, sort_order=i)
            for i, code in enumerate(CATEGORY_CODES, 1)
        ]

    def get_reference_household(self) -> ReferenceHousehold | None:
        if not self.with_household:
            return None
        return ReferenceHousehold(
            district_code="gasabo",
            household_size=4,
            monthly_income=180_000,
            monthly_essentials=150_000,
            savings=60_000,
        )

    def list_periods(self) -> Sequence[ReferencePeriod]:
        return [ReferencePeriod(code="2026-10", label="Demo month · October", is_default=True)]

    def list_household_groups(self) -> Sequence[HouseholdGroup]:
        return [HouseholdGroup(code="all", label="All sample households", is_default=True)]

    def list_series(self, series_code: str) -> Sequence[MonthlySeriesPoint]:
        return [MonthlySeriesPoint(month="2026-10", essentials=150_000)]

    def list_swaps(self, district_code: str, month: int) -> Sequence[SeasonalSwap]:
        if month != 10:
            return []
        return [
            SeasonalSwap(
                id="rice-to-sweet-potato",
                title="t",
                description="d",
                footnote="f",
                from_name="Rice",
                from_quantity=Decimal("1.00"),
                from_unit="kg",
                from_price=2_000,
                to_name="Sweet potatoes",
                to_quantity=Decimal("2.00"),
                to_unit="kg",
                to_price=1_600,
            )
        ]

    def list_tips(self, district_code: str, month: int) -> Sequence[SeasonalTip]:
        return [SeasonalTip(title="Keep variety on the plate.", body="b")]

    def get_vulnerability_model(self) -> VulnerabilityModel | None:
        if not self.with_model:
            return None
        return VulnerabilityModel(
            version="0.1",
            weight_income_instability=Decimal("0.40"),
            weight_essential_cost_pressure=Decimal("0.40"),
            weight_low_buffer_exposure=Decimal("0.20"),
        )

    def list_bands(self) -> Sequence[VulnerabilityBand]:
        if not self.with_model:
            return []
        return [
            VulnerabilityBand(key=k, min_score=lo, max_score=hi)
            for k, lo, hi in (
                ("band1", 0, 39),
                ("band2", 40, 59),
                ("band3", 60, 69),
                ("band4", 70, 100),
            )
        ]

    def _row(self, code: str) -> DistrictVulnerability:
        score = self.scores[code]
        triple = (50, 40, 50) if code == "gasabo" else (score, score, score)
        return DistrictVulnerability(
            district_code=code,
            income_instability=triple[0],
            essential_cost_pressure=triple[1],
            low_buffer_exposure=triple[2],
            score=Decimal(score),
        )

    def list_district_scores(
        self, period_code: str, group_code: str
    ) -> Sequence[tuple[DistrictVulnerability, str]]:
        return [(self._row(code), code.title()) for code in sorted(self.scores)]

    def get_district_score(
        self, period_code: str, group_code: str, district_code: str
    ) -> DistrictVulnerability | None:
        return self._row(district_code) if district_code in self.scores else None


class FakeBenchmarks(BenchmarkRepository):
    def __init__(self, sizes: tuple[int, ...] = (4,)) -> None:
        super().__init__(NO_SESSION, "0.1")
        self.sizes = sizes

    def list_lines(self, district_code: str, household_size: int) -> Sequence[BudgetBenchmark]:
        if household_size not in self.sizes:
            return []
        amounts = (65_000, 40_000, 20_000, 10_000, 15_000)
        return [
            BudgetBenchmark(category_code=code, monthly_amount=amount)
            for code, amount in zip(CATEGORY_CODES, amounts, strict=True)
        ]


class FakeSample(ShockRepository):
    def __init__(self) -> None:
        super().__init__(NO_SESSION, "0.1")

    def sample_size(self) -> int:
        return 3_000

    def households_in_deficit(self, reduction_pct: int) -> int:
        return 1_000 if reduction_pct == 20 else 0

    def households_by_income_source(self) -> dict[str, int]:
        return {"wage": 1_200, "agriculture": 1_050, "informal_enterprise": 750}
