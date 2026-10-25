"""`GET /seasonal-swaps` (contract §4; BR-14)."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.calculations import swap_difference
from app.core.constants import METHODOLOGY_VERSION
from app.db.session import get_read_session
from app.repositories.reference_data_repository import ReferenceDataRepository
from app.schemas.common import Meta
from app.schemas.seasonal_swap import SeasonalSwapResponse, SwapItem, SwapOut, TipOut
from app.services.benchmark_service import require_district


class SeasonalSwapService:
    def __init__(self, reference: ReferenceDataRepository) -> None:
        self._reference = reference

    def list_swaps(self, district_code: str, month: int) -> SeasonalSwapResponse:
        district = require_district(self._reference, district_code)
        swaps = self._reference.list_swaps(district.code, month)
        tips = self._reference.list_tips(district.code, month)
        return SeasonalSwapResponse(
            items=[
                SwapOut(
                    id=swap.id,
                    title=swap.title,
                    description=swap.description,
                    from_=SwapItem(
                        name=swap.from_name,
                        quantity=swap.from_quantity,
                        unit=swap.from_unit,
                        price=swap.from_price,
                    ),
                    to=SwapItem(
                        name=swap.to_name,
                        quantity=swap.to_quantity,
                        unit=swap.to_unit,
                        price=swap.to_price,
                    ),
                    difference=swap_difference(swap.from_price, swap.to_price),
                    footnote=swap.footnote,
                )
                for swap in swaps
            ],
            tips=[TipOut(title=tip.title, body=tip.body) for tip in tips],
            meta=Meta(),
        )


def get_seasonal_swap_service(
    session: Annotated[Session, Depends(get_read_session)],
) -> SeasonalSwapService:
    return SeasonalSwapService(ReferenceDataRepository(session, METHODOLOGY_VERSION))
