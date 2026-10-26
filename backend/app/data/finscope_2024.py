"""FinScope Rwanda 2024: published national and district financial-inclusion statistics.

OFFICIAL PUBLISHED STATISTICS, transcribed from the report and checked value by value. These are
not synthetic, and nothing here is derived, recomputed or rounded differently from the report.

Source document (verified 2026-10-26):
- "Rwanda FinScope Survey 2024", Access to Finance Rwanda (AFR), recommended citation
  "Access to Finance Rwanda, FinScope 2024 report, June 2024" (report p. 2). Sponsors named in the
  foreword (p. 3): MINECOFIN, AFR, the National Bank of Rwanda and NISR.
- File "Finscope-Final-Report__10_07_2024-1.pdf", 77 pages, SHA-256
  981727b88cd05fe271b64c3a4541a1c0931e5934cdc7c9eb4fd3e6da67d81026, downloaded from the NISR
  Microdata Catalog, study 120 (download 1085).

How values were verified: each percentage was read from the PDF text layer (exact printed
labels, not pixel estimates) and confirmed against a rendered image of the page. District rows
were also checked against two statements in the report's own prose (p. 30): exactly twelve
districts are above the national exclusion rate of 4%, and Gicumbi has the highest
informal-only share. `tests/unit/test_services/test_finscope_data.py` re-asserts both.

Report-level caveats preserved here:
- Fieldwork dates are not stated anywhere in the report, so `fieldwork_period` is NULL. The NISR
  web summary gives 6 Sept - 8 Oct 2024, which post-dates the June 2024 publication; that
  discrepancy is unresolved and those dates are not used.
- "Due to rounding off, percentages presented throughout this report may not always add up
  100%" (p. 21). District rows therefore sum to 99-101 and are published as printed.
- Where the report gives two different adult counts for the same figure, no count is published;
  the note quotes both.
"""

from datetime import date
from typing import Final

from app.core.constants import FINSCOPE_2024_SOURCE_ID
from app.data.registry import Dataset, TableRows
from app.models import FinancialAccessStrandDistrict, FinancialInclusionIndicator, StatisticalSource

SOURCE_ID: Final = FINSCOPE_2024_SOURCE_ID
FIGURE_13: Final = "Figure 13: Financia [sic] Access Strand by districts (%)"

SOURCE: Final = {
    "id": SOURCE_ID,
    "title": "Rwanda FinScope Survey 2024",
    "publisher": "Access to Finance Rwanda (AFR)",
    "sponsors": (
        "MINECOFIN; Access to Finance Rwanda; National Bank of Rwanda; NISR (foreword, p. 3)"
    ),
    "distributor": "National Institute of Statistics of Rwanda (NISR) Microdata Catalog, study 120",
    "citation": "Access to Finance Rwanda, FinScope 2024 report, June 2024",
    "publication_date": "2024-06",
    "survey_round": "2024",
    "fieldwork_period": None,
    "population": (
        "Adults aged 16 years and older in private households; one eligible member interviewed "
        "per selected household (p. 20)"
    ),
    "sample_size": 13_994,
    "lowest_published_geography": "district",
    "document_file": "Finscope-Final-Report__10_07_2024-1.pdf",
    "document_url": "https://microdata.statistics.gov.rw/index.php/catalog/120/download/1085",
    "catalog_url": "https://microdata.statistics.gov.rw/index.php/catalog/120",
    "document_sha256": "981727b88cd05fe271b64c3a4541a1c0931e5934cdc7c9eb4fd3e6da67d81026",
    "retrieved_on": date(2026, 10, 26),
    "notes": (
        "Fieldwork dates are not stated in the report. Percentages are rounded and may not add "
        "up to 100% (p. 21). Refugee results are reported separately (p. 20) and are not "
        "included here. District samples were designed for 'reasonable precision at the "
        "district level' with at least 400 adults per district (p. 20); the report publishes no "
        "confidence intervals."
    ),
}

ADULTS: Final = "Adults aged 16 years and older"

# (code, measure, label, definition, value, count, comparison value (2020), comparison count,
#  page, figure, notes). Values are percentages as printed; counts are quoted as printed.
NATIONAL: Final = (
    (
        "financially_included", "inclusion_overview", "Financially included",
        "Have/use financial products and/or services - formal and/or informal (Figure 2, p. 25)",
        96, "7.8 million", 93, None, 25,
        "Section 2.1; Figure 3: Overview of financial products/services (%)", None,
    ),
    (
        "formally_served", "inclusion_overview", "Formally served (formal financial inclusion)",
        "Have/use financial products and/or services provided by a formal financial institution "
        "(bank and/or non-bank) (Figure 2, p. 25)",
        92, "7.5 million", 77, "5.4 million", 25,
        "Section 2.1; Figure 3 (also Figure 5, p. 27)", None,
    ),
    (
        "financially_excluded", "inclusion_overview", "Financially excluded",
        "Do not have/use any financial products and/or services - neither formal nor informal "
        "(Figure 2, p. 25)",
        4, None, 7, None, 25,
        "Section 2.1; Figure 3 (also Section 2.3 and Figure 5, p. 27)",
        "The report gives two adult counts: 316,000 (p. 25) and 317,000 (p. 27). Neither is "
        "published here.",
    ),
    (
        "banked", "access_strand", "Banked",
        "Have/use financial products/services provided by a bank, regulated by the Central Bank "
        "(Figure 2, p. 25)",
        22, "1.8 million", 22, "1.6 million", 27,
        "Section 2.3; Figure 5: Rwanda Financial Access Strand (%)", None,
    ),
    (
        "other_formal_non_bank_only", "access_strand", "Other formal (non-bank), not banked",
        "Not banked but use non-bank formal financial services, e.g. mobile money, SACCO, "
        "insurance, MFIs, pension (Section 2.3, p. 27)",
        70, "5.7 million", 55, "3.8 million", 27,
        "Section 2.3; Figure 5: Rwanda Financial Access Strand (%)", None,
    ),
    (
        "informal_only", "access_strand", "Informal only",
        "Use informal products or mechanisms without any formal products (Section 2.3, p. 27)",
        4, None, 16, "1.1 million", 27,
        "Section 2.3; Figure 5: Rwanda Financial Access Strand (%)",
        "The report gives two 2024 adult counts: 358,000 (executive summary, p. 11) and 317,000 "
        "(Section 2.2, p. 26). Neither is published here.",
    ),
    (
        "financially_excluded_strand", "access_strand", "Excluded",
        "Neither formal nor informal products; access strand category (Section 2.3, p. 27)",
        4, None, 7, None, 27,
        "Section 2.3; Figure 5: Rwanda Financial Access Strand (%)",
        "Same population share as 'financially_excluded'; listed so the access strand is complete.",
    ),
    (
        "financially_healthy", "financial_health_strand", "Financially healthy",
        "Financial health index 75-100 (Section 5.2.1, p. 67)",
        10, None, 4, None, 69,
        "Section 5.2.6; Figure 65: Financial health strand (%)",
        "The report gives two adult counts: 778k (Figure 65) and 780,000 (text, p. 69). Neither "
        "is published here.",
    ),
    (
        "financially_coping", "financial_health_strand", "Financially coping",
        "Financial health index 50-74 (Section 5.2.1, p. 67)",
        57, "4.6 million", 53, None, 69,
        "Section 5.2.6; Figure 65: Financial health strand (%)",
        "The 2020 value is printed in Figure 65 only, not in the text.",
    ),
    (
        "financially_vulnerable", "financial_health_strand", "Financially vulnerable",
        "Financial health index 25-49 (Section 5.2.1, p. 67)",
        31, "2.6 million", 37, None, 69,
        "Section 5.2.6; Figure 65: Financial health strand (%)",
        "The 2020 value is printed in Figure 65 only, not in the text.",
    ),
    (
        "financially_extremely_vulnerable", "financial_health_strand",
        "Extremely financially vulnerable",
        "Financial health index below 25 (Section 5.2.1, p. 67)",
        3, "206K", 7, None, 69,
        "Section 5.2.6; Figure 65: Financial health strand (%)",
        "The 2020 value is printed in Figure 65 only, not in the text.",
    ),
)  # fmt: skip

# Figure 13, p. 31: (banked, other formal non-bank, informal only, excluded), as printed.
# None = no segment label is printed for that district (checked on a 6x zoomed render).
DISTRICTS: Final[dict[str, tuple[int, int, int | None, int]]] = {
    "burera": (11, 87, 2, 1),
    "nyarugenge": (59, 40, None, 1),
    "nyamagabe": (11, 84, 4, 1),
    "gatsibo": (23, 73, 3, 1),
    "musanze": (24, 71, 5, 1),
    "gasabo": (51, 46, 2, 1),
    "bugesera": (23, 71, 5, 2),
    "kicukiro": (62, 35, 2, 2),
    "muhanga": (17, 76, 5, 2),
    "rwamagana": (27, 68, 3, 2),
    "nyagatare": (17, 77, 4, 3),
    "ruhango": (22, 70, 5, 3),
    "kamonyi": (16, 76, 4, 3),
    "kirehe": (7, 86, 5, 3),
    "karongi": (8, 83, 6, 3),
    "rubavu": (22, 71, 4, 3),
    "gisagara": (10, 77, 9, 4),
    "nyanza": (17, 74, 4, 4),
    "kayonza": (11, 76, 8, 5),
    "huye": (15, 73, 6, 6),
    "nyamasheke": (13, 78, 3, 6),
    "rusizi": (22, 68, 5, 6),
    "rutsiro": (9, 78, 6, 6),
    "gicumbi": (8, 75, 11, 7),
    "ngororero": (10, 78, 5, 7),
    "gakenke": (18, 69, 5, 8),
    "nyabihu": (13, 74, 5, 8),
    "rulindo": (13, 74, 4, 8),
    "ngoma": (9, 77, 6, 8),
    "nyaruguru": (6, 78, 5, 10),
}

DISTRICT_NOTES: Final = {
    "nyarugenge": (
        "Figure 13 prints no 'Informal ONLY' label or segment for Nyarugenge (the bar runs "
        "from 'Other Formal' 40 directly to 'Excluded' 1). The value is not published here; it "
        "is not assumed to be 0."
    ),
}


def _finscope_2024() -> tuple[TableRows, ...]:
    national = tuple(
        {
            "source_id": SOURCE_ID,
            "code": code,
            "measure": measure,
            "label": label,
            "definition": definition,
            "population": ADULTS,
            "unit": "percent",
            "year": 2024,
            "value_pct": value,
            "count_published": count,
            "comparison_year": 2020 if comparison is not None else None,
            "comparison_value_pct": comparison,
            "comparison_count_published": comparison_count,
            "page": page,
            "table_or_figure": figure,
            "notes": notes,
            "sort_order": index,
        }
        for index, (
            code, measure, label, definition, value, count, comparison, comparison_count,
            page, figure, notes,
        ) in enumerate(NATIONAL, 1)
    )  # fmt: skip
    districts = tuple(
        {
            "source_id": SOURCE_ID,
            "district_code": code,
            "banked_pct": banked,
            "other_formal_non_bank_pct": other,
            "informal_only_pct": informal,
            "excluded_pct": excluded,
            "page": 31,
            "table_or_figure": FIGURE_13,
            "notes": DISTRICT_NOTES.get(code),
        }
        for code, (banked, other, informal, excluded) in DISTRICTS.items()
    )
    return (
        TableRows(StatisticalSource, None, (SOURCE,)),
        TableRows(FinancialInclusionIndicator, None, national),
        TableRows(FinancialAccessStrandDistrict, None, districts),
    )


DATASETS: Final = (Dataset("finscope_2024", _finscope_2024),)
