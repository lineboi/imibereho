"""NISR Seasonal Agricultural Survey (SAS) 2025: Rwanda's crop-season calendar and production.

OFFICIAL PUBLISHED STATISTICS, served by `GET /api/v1/agro/harvest-calendar` (contract v0.4
§11.5). Nothing here is synthetic or illustrative.

Source documents (retrieved 2026-10-27 from the NISR SAS 2025 page, "LAST UPDATED: 31 Dec 2025"):
- Data: "SAS 2025_Annual Tables.xlsx", SHA-256
  3a6ed44f1e973578e46221b392e54833bb39e73b681be6e54fa2b44efe5fe1f7, sheet "Table 0: Summary of
  Seasonal Agricultural Survey main indicators", rows "Production for major crops (MT)", columns
  I-K (SAS 2025, Seasons A, B, C).
- Season calendar: "SAS 2025 summary in English.pdf", SHA-256
  49e1d569170a862d048320388c722bf87e559f35d20f11bad7f6fcabf7212bbc, page 2: "Season A
  (September 2024–February 2025), Season B (March–June 2025), and Season C (July–September
  2025)". The SAS 2022 Annual Report (introduction) gives the same definition and adds that
  Season C is "a shorter season mainly for vegetables, sweet potato grown in swamps and Irish
  potato grown in the volcanic agro-ecological zone".

Kinyarwanda season names are not given by NISR and other sources disagree (Season A is called
Umuhindo in one source and Urugaryi in another), so only NISR's English names are used.
"""

from datetime import date
from decimal import Decimal
from typing import Final

from app.core.constants import SAS_2025_SOURCE_ID
from app.data.registry import Dataset, TableRows
from app.models import StatisticalSource

SOURCE_ID: Final = SAS_2025_SOURCE_ID

SOURCE: Final = {
    "id": SOURCE_ID,
    "title": "Seasonal Agricultural Survey (SAS) 2025: Annual Report and Tables",
    "publisher": "National Institute of Statistics of Rwanda (NISR)",
    "sponsors": None,
    "distributor": "National Institute of Statistics of Rwanda (NISR), statistics.gov.rw",
    "citation": "National Institute of Statistics of Rwanda (NISR), Seasonal Agricultural Survey "
    "2025, Annual Tables, Table 0",
    "publication_date": "2025-12",
    "survey_round": "2024/25",
    "fieldwork_period": "Conducted once in each season: Season A (September 2024 - February "
    "2025), Season B (March - June 2025), Season C (July - September 2025) (summary, p. 2)",
    "population": "Agricultural land nationwide, all districts; production in metric tonnes "
    "(MT) by crop and season",
    "sample_size": None,
    "lowest_published_geography": "district",
    "document_file": "SAS 2025_Annual Tables.xlsx",
    "document_url": "https://statistics.gov.rw/sites/default/files/documents/2025-12/"
    "SAS%202025_Annual%20Tables.xlsx",
    "catalog_url": "https://statistics.gov.rw/data-sources/surveys/Seasonal-Agricultural-Survey/"
    "Seasonal-Agricultural-Survey/seasonal-agricultural-survey-2025-",
    "document_sha256": "3a6ed44f1e973578e46221b392e54833bb39e73b681be6e54fa2b44efe5fe1f7",
    "retrieved_on": date(2026, 10, 27),
    "notes": (
        "Season calendar from 'SAS 2025 summary in English.pdf' (SHA-256 49e1d569170a862d048320"
        "388c722bf87e559f35d20f11bad7f6fcabf7212bbc), p. 2. Production figures are Table 0 of "
        "the annual tables, rounded half up to whole tonnes for display. Season C has no "
        "production for most crops (shown as '-' in the table). September falls in both "
        "Season A (which starts in September) and Season C (which ends in September)."
    ),
}

# Season -> (name, months of the year, month range as published).
SEASONS: Final[dict[str, tuple[str, tuple[int, ...], str]]] = {
    "A": ("Season A", (9, 10, 11, 12, 1, 2), "September – February"),
    "B": ("Season B", (3, 4, 5, 6), "March – June"),
    "C": ("Season C", (7, 8, 9), "July – September"),
}

# SAS 2025, Table 0, "Production for major crops (MT)", columns I (A), J (B), K (C), as stored
# in the workbook. None = "-" or blank (no production reported in that season). Bananas are
# permanent crops harvested all year and are left out of the seasonal highlights.
PRODUCTION_2025_MT: Final[dict[str, tuple[Decimal | None, Decimal | None, Decimal | None]]] = {
    "Maize": (Decimal("481245.7740529139"), Decimal("117710.62025771625"), None),
    "Sorghum": (Decimal("54993.73030853026"), Decimal("125655.5902792073"), None),
    "Paddy rice": (Decimal("69680.07998574444"), Decimal("72976.07382234184"), None),
    "Wheat": (Decimal("3143.615430223661"), Decimal("11667.10314831459"), None),
    "Cassava": (Decimal("542874.0991801189"), Decimal("852541.2360327417"), None),
    "Sweet potato": (
        Decimal("656320.4082028759"), Decimal("652515.1298667592"), Decimal("41288.65201682702"),
    ),
    "Irish potato": (
        Decimal("475784.9758518617"), Decimal("314092.53794686176"), Decimal("94892.23644781235"),
    ),
    "Taro & yams": (Decimal("82306.84780545044"), Decimal("117940.68364047109"), None),
    "Bean": (
        Decimal("230456.08919149387"), Decimal("240720.6245832633"), Decimal("3178.0037303633426"),
    ),
    "Pea": (
        Decimal("5983.682846381793"), Decimal("4585.801190894167"), Decimal("569.1499969040501"),
    ),
    "Groundnut": (
        Decimal("4677.624359870967"), Decimal("7746.527246042963"), Decimal("8.804753882708708"),
    ),
    "Soybean": (
        Decimal("15656.676359706991"), Decimal("16388.39418811726"), Decimal("507.42344646806094"),
    ),
    "Vegetables": (
        Decimal("149806.2121393904"), Decimal("181271.58421383865"), Decimal("67626.29847435938"),
    ),
    "Fruits": (Decimal("28440.31097966584"), Decimal("29797.7227337507"), None),
}  # fmt: skip
PRODUCTION_SEASON_COLUMN: Final = {"A": 0, "B": 1, "C": 2}
PRODUCTION_YEAR: Final = 2025
HIGHLIGHT_COUNT: Final = 3


def _sas_2025() -> tuple[TableRows, ...]:
    return (TableRows(StatisticalSource, None, (SOURCE,), partition=("id", SOURCE_ID)),)


DATASETS: Final = (Dataset("sas_2025", _sas_2025),)
