"""Read-only queries over seeded reference data. No business rules, rounding or HTTP concepts."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
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


class ReferenceDataRepository:
    def __init__(self, session: Session, methodology_version: str) -> None:
        self._session = session
        self._version = methodology_version

    # --- districts and categories ---

    def list_districts(self) -> Sequence[District]:
        return self._session.scalars(select(District).order_by(District.name)).all()

    def get_district(self, code: str) -> District | None:
        return self._session.get(District, code)

    def list_categories(self) -> Sequence[ExpenseCategory]:
        return self._session.scalars(
            select(ExpenseCategory).order_by(ExpenseCategory.sort_order)
        ).all()

    def get_reference_household(self) -> ReferenceHousehold | None:
        return self._session.get(ReferenceHousehold, self._version)

    # --- dashboard dimensions ---

    def list_periods(self) -> Sequence[ReferencePeriod]:
        return self._session.scalars(
            select(ReferencePeriod)
            .where(ReferencePeriod.methodology_version == self._version)
            .order_by(ReferencePeriod.sort_order)
        ).all()

    def list_household_groups(self) -> Sequence[HouseholdGroup]:
        return self._session.scalars(
            select(HouseholdGroup)
            .where(HouseholdGroup.methodology_version == self._version)
            .order_by(HouseholdGroup.sort_order)
        ).all()

    def list_series(self, series_code: str) -> Sequence[MonthlySeriesPoint]:
        return self._session.scalars(
            select(MonthlySeriesPoint)
            .where(
                MonthlySeriesPoint.methodology_version == self._version,
                MonthlySeriesPoint.series_code == series_code,
            )
            .order_by(MonthlySeriesPoint.month)
        ).all()

    # --- seasonal swaps ---

    def list_swaps(self, district_code: str, month: int) -> Sequence[SeasonalSwap]:
        return self._session.scalars(
            select(SeasonalSwap)
            .where(
                SeasonalSwap.methodology_version == self._version,
                SeasonalSwap.month == month,
                (SeasonalSwap.district_code.is_(None))
                | (SeasonalSwap.district_code == district_code),
            )
            .order_by(SeasonalSwap.sort_order, SeasonalSwap.id)
        ).all()

    def list_tips(self, district_code: str, month: int) -> Sequence[SeasonalTip]:
        return self._session.scalars(
            select(SeasonalTip)
            .where(
                SeasonalTip.methodology_version == self._version,
                (SeasonalTip.month.is_(None)) | (SeasonalTip.month == month),
                (SeasonalTip.district_code.is_(None))
                | (SeasonalTip.district_code == district_code),
            )
            .order_by(SeasonalTip.sort_order, SeasonalTip.id)
        ).all()

    # --- vulnerability ---

    def get_vulnerability_model(self) -> VulnerabilityModel | None:
        return self._session.get(VulnerabilityModel, self._version)

    def list_bands(self) -> Sequence[VulnerabilityBand]:
        return self._session.scalars(
            select(VulnerabilityBand)
            .where(VulnerabilityBand.model_version == self._version)
            .order_by(VulnerabilityBand.min_score)
        ).all()

    def list_district_scores(
        self, period_code: str, group_code: str
    ) -> Sequence[tuple[DistrictVulnerability, str]]:
        """Scores with district names, in name order. Sorting by score is a service rule."""
        rows = self._session.execute(
            select(DistrictVulnerability, District.name)
            .join(District, District.code == DistrictVulnerability.district_code)
            .where(
                DistrictVulnerability.model_version == self._version,
                DistrictVulnerability.period_code == period_code,
                DistrictVulnerability.household_group_code == group_code,
            )
            .order_by(District.name)
        ).all()
        return [(score, name) for score, name in rows]

    def get_district_score(
        self, period_code: str, group_code: str, district_code: str
    ) -> DistrictVulnerability | None:
        return self._session.get(
            DistrictVulnerability, (self._version, period_code, group_code, district_code)
        )
