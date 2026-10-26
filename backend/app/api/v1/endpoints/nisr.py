"""Official published statistics (`/api/v1/nisr/*`): sources, FinScope 2024 financial inclusion
and EICV7 2023/24 poverty and health insurance.

These endpoints are contract v0.3 (contract §10, agreed 27 October 2026). Unlike the
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
    SurveyIndicatorEstimates,
)
from app.services.financial_inclusion_service import (
    FinancialInclusionService,
    get_financial_inclusion_service,
)
from app.services.household_survey_service import (
    HouseholdSurveyService,
    get_household_survey_service,
)

router = APIRouter(prefix="/nisr", tags=["official statistics"])
Service = Annotated[FinancialInclusionService, Depends(get_financial_inclusion_service)]
SurveyService = Annotated[HouseholdSurveyService, Depends(get_household_survey_service)]


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


@router.get(
    "/poverty",
    summary="EICV7 2023/24 headcount poverty rate with uncertainty: national, urban/rural, "
    "province and district (Table A9.23)",
    responses=problem_responses(400),
)
def poverty(_: Annotated[NoQuery, Query()], service: SurveyService) -> SurveyIndicatorEstimates:
    return service.poverty()


@router.get(
    "/health-insurance",
    summary="EICV7 2023/24 health-insurance coverage with uncertainty: national, sex, "
    "urban/rural, province, consumption quintile and district (Table A3.7)",
    responses=problem_responses(400),
)
def health_insurance(
    _: Annotated[NoQuery, Query()], service: SurveyService
) -> SurveyIndicatorEstimates:
    return service.health_insurance()
