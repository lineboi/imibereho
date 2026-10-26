"""Official published statistics (`/api/v1/nisr/*`): sources and FinScope 2024 financial inclusion.

These endpoints extend contract v0.2 (proposed for v0.3; see backend/README.md). Unlike the
illustrative endpoints, their `meta.isIllustrative` is false and every figure cites its source.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.responses import problem_responses
from app.schemas.common import NoQuery
from app.schemas.official_statistics import (
    DistrictFinancialInclusion,
    NationalFinancialInclusion,
    SourceList,
)
from app.services.financial_inclusion_service import (
    FinancialInclusionService,
    get_financial_inclusion_service,
)

router = APIRouter(prefix="/nisr", tags=["official statistics"])
Service = Annotated[FinancialInclusionService, Depends(get_financial_inclusion_service)]


@router.get(
    "/sources",
    summary="Source documents behind the official statistics, with full provenance",
    responses=problem_responses(400),
)
def list_sources(_: Annotated[NoQuery, Query()], service: Service) -> SourceList:
    return service.sources()


@router.get(
    "/financial-inclusion/national",
    summary="FinScope Rwanda 2024 national financial-inclusion and financial-health indicators",
    responses=problem_responses(400),
)
def national_financial_inclusion(
    _: Annotated[NoQuery, Query()], service: Service
) -> NationalFinancialInclusion:
    return service.national()


@router.get(
    "/financial-inclusion/districts",
    summary="FinScope Rwanda 2024 financial access strand for each district (Figure 13)",
    responses=problem_responses(400),
)
def district_financial_inclusion(
    _: Annotated[NoQuery, Query()], service: Service
) -> DistrictFinancialInclusion:
    return service.districts()
