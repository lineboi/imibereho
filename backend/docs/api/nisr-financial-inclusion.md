# Official financial-inclusion statistics: `/api/v1/nisr/*`

For the frontend. Three read-only endpoints serve **published** FinScope Rwanda 2024
statistics, each figure with its page and figure in the source report.

> **Status: extension beyond contract v0.2.** These endpoints are not in
> `docs/architecture/api-contract-proposal.md` (v0.2 rev 2). They are proposed for contract v0.3
> and need frontend sign-off. The `/api/v1` prefix, problem+json errors and `X-Request-ID`
> behave exactly as in the contract.

## How these differ from the illustrative endpoints

| | Illustrative endpoints (contract v0.2) | `/api/v1/nisr/*` |
|---|---|---|
| Data | Design demo values and synthetic data | Published statistics from an identified report |
| `meta.isIllustrative` | always `true` | always `false` |
| `meta.methodologyVersion` | `"0.1"` | not present (not an Imibereho method) |
| Source shown | none | `meta.sourceIds` plus a full `source` object |

**Display guidance:**
- Label these figures with the source citation and year: *"Access to Finance Rwanda, FinScope 2024 report, June 2024"*.
- The publisher is **Access to Finance Rwanda (AFR)**. NISR is a sponsor and hosts the file, so don't present the figures as produced by NISR.
- Don't mix these values with the illustrative ones in one chart without labelling which is which.

## Common rules

- No query parameters. Any parameter returns **400** `unknown-parameter` (problem+json).
- Only `GET` is allowed. Other methods return **405** `method-not-allowed`.
- Percentages are **integers exactly as printed** in the report: no recomputation, no re-rounding. The report notes that rounded percentages may not add up to 100 (p. 21), so rows can sum to 99–101.
- `status` is `"available"`, or `"awaiting_validated_data"` when no validated data is loaded. In the second case the lists are empty and `meta.count` is `0`. The API **never** substitutes synthetic values.
- `null` means *not published*, never zero.

## `GET /api/v1/nisr/sources`

The source documents with full provenance.

```json
{
  "items": [
    {
      "id": "finscope-2024",
      "title": "Rwanda FinScope Survey 2024",
      "publisher": "Access to Finance Rwanda (AFR)",
      "sponsors": "MINECOFIN; Access to Finance Rwanda; National Bank of Rwanda; NISR (foreword, p. 3)",
      "distributor": "National Institute of Statistics of Rwanda (NISR) Microdata Catalog, study 120",
      "citation": "Access to Finance Rwanda, FinScope 2024 report, June 2024",
      "publicationDate": "2024-06",
      "surveyRound": "2024",
      "fieldworkPeriod": null,
      "population": "Adults aged 16 years and older in private households; one eligible member interviewed per selected household (p. 20)",
      "sampleSize": 13994,
      "lowestPublishedGeography": "district",
      "documentFile": "Finscope-Final-Report__10_07_2024-1.pdf",
      "documentUrl": "https://microdata.statistics.gov.rw/index.php/catalog/120/download/1085",
      "catalogUrl": "https://microdata.statistics.gov.rw/index.php/catalog/120",
      "documentSha256": "981727b88cd05fe271b64c3a4541a1c0931e5934cdc7c9eb4fd3e6da67d81026",
      "retrievedOn": "2026-10-26",
      "notes": "Fieldwork dates are not stated in the report. …"
    }
  ],
  "meta": { "isIllustrative": false, "dataKind": "official_published_statistics", "sourceIds": ["finscope-2024"], "count": 1 }
}
```

`fieldworkPeriod` is `null` because the report doesn't state its fieldwork dates (see "Known source issues" below).

## `GET /api/v1/nisr/financial-inclusion/national`

```json
{
  "status": "available",
  "geographicLevel": "national",
  "source": { "…": "same object as in /sources" },
  "indicators": [
    {
      "code": "financially_included",
      "measure": "inclusion_overview",
      "label": "Financially included",
      "definition": "Have/use financial products and/or services - formal and/or informal (Figure 2, p. 25)",
      "population": "Adults aged 16 years and older",
      "unit": "percent",
      "year": 2024,
      "valuePct": 96,
      "countPublished": "7.8 million",
      "comparison": { "year": 2020, "valuePct": 93, "countPublished": null },
      "citation": { "page": 25, "tableOrFigure": "Section 2.1; Figure 3: Overview of financial products/services (%)" },
      "notes": null
    }
  ],
  "meta": { "isIllustrative": false, "dataKind": "official_published_statistics", "sourceIds": ["finscope-2024"], "count": 11 }
}
```

`measure` groups the indicators:
- **`inclusion_overview`:** categories can overlap; they don't sum to 100.
- **`access_strand`:** mutually exclusive categories; they sum to 100.
- **`financial_health_strand`:** mutually exclusive segments by financial health index score. Both years print 101, because of rounding.

All 11 indicators, verified against the report. Every 2020 value is printed in the same report.

| `code` | `measure` | 2024 | 2020 | Report page / figure |
|---|---|---|---|---|
| `financially_included` | inclusion_overview | 96 | 93 | p. 25, Figure 3 |
| `formally_served` | inclusion_overview | 92 | 77 | p. 25, Figure 3 (and Figure 5) |
| `financially_excluded` | inclusion_overview | 4 | 7 | p. 25, Figure 3 (and Figure 5) |
| `banked` | access_strand | 22 | 22 | p. 27, Figure 5 |
| `other_formal_non_bank_only` | access_strand | 70 | 55 | p. 27, Figure 5 |
| `informal_only` | access_strand | 4 | 16 | p. 27, Figure 5 |
| `financially_excluded_strand` | access_strand | 4 | 7 | p. 27, Figure 5 |
| `financially_healthy` | financial_health_strand | 10 | 4 | p. 69, Figure 65 |
| `financially_coping` | financial_health_strand | 57 | 53 | p. 69, Figure 65 (2020 value in figure only) |
| `financially_vulnerable` | financial_health_strand | 31 | 37 | p. 69, Figure 65 (2020 value in figure only) |
| `financially_extremely_vulnerable` | financial_health_strand | 3 | 7 | p. 69, Figure 65 (2020 value in figure only) |

**Counts are omitted (`countPublished: null`) wherever the report gives two different numbers:**

| Indicator | Counts the report gives |
|---|---|
| `financially_excluded` | 316,000 (p. 25) and 317,000 (p. 27) |
| `informal_only` | 358,000 (p. 11) and 317,000 (p. 26) |
| `financially_healthy` | 778k (Figure 65) and 780,000 (text) |

The indicator's `notes` field quotes both counts.

## `GET /api/v1/nisr/financial-inclusion/districts`

The financial access strand for all 30 districts, from report **Figure 13, p. 31**. The figure's title is printed as "Financia Access Strand", so the API reproduces it with `[sic]`. Items are in district-name order.

```json
{
  "status": "available",
  "geographicLevel": "district",
  "source": { "…": "same object as in /sources" },
  "categories": [
    { "code": "banked", "label": "Banked", "definition": "…" },
    { "code": "otherFormalNonBank", "label": "Other formal (non-bank)", "definition": "…" },
    { "code": "informalOnly", "label": "Informal only", "definition": "…" },
    { "code": "excluded", "label": "Excluded", "definition": "…" }
  ],
  "items": [
    {
      "districtCode": "bugesera",
      "name": "Bugesera",
      "bankedPct": 23,
      "otherFormalNonBankPct": 71,
      "informalOnlyPct": 5,
      "excludedPct": 2,
      "citation": { "page": 31, "tableOrFigure": "Figure 13: Financia [sic] Access Strand by districts (%)" },
      "notes": null
    },
    {
      "districtCode": "nyarugenge",
      "name": "Nyarugenge",
      "bankedPct": 59,
      "otherFormalNonBankPct": 40,
      "informalOnlyPct": null,
      "excludedPct": 1,
      "citation": { "page": 31, "tableOrFigure": "Figure 13: Financia [sic] Access Strand by districts (%)" },
      "notes": "Figure 13 prints no 'Informal ONLY' label or segment for Nyarugenge … it is not assumed to be 0."
    }
  ],
  "meta": { "isIllustrative": false, "dataKind": "official_published_statistics", "sourceIds": ["finscope-2024"], "count": 30 }
}
```

- `districtCode` uses the same slugs as `GET /api/v1/districts`.
- `informalOnlyPct` is `integer | null`. Render `null` as "not published", never as 0.
- There are no confidence intervals: the report doesn't publish them. Its district samples have at least 400 adults each (p. 20), so small differences between districts may not be meaningful.

## Known source issues (recorded, not resolved)

1. **Fieldwork dates are not in the report.** The NISR web summary gives "6 September – 8 October 2024", which is *after* the report's June 2024 publication (and the PDF's 10 July 2024 creation date). Those dates are not used.
2. **Inconsistent counts:** see the national section above.
3. **Nyarugenge's informal-only share** isn't printed in Figure 13, so it's `null`.

## How the values were verified

1. I downloaded the report from the NISR Microdata Catalog (study 120, download 1085) and recorded its SHA-256 (`981727b8…1026`).
2. I read each percentage from the PDF's text layer, which gives the exact printed labels rather than estimates from bar lengths. I confirmed each one on a rendered image of the page, with a 6× zoom on the narrow right-hand segments of Figure 13.
3. I cross-checked the district rows against the report's own prose (p. 30). These checks are encoded in `tests/unit/test_services/test_finscope_data.py`:
   - "Twelve districts have higher levels of financial exclusion than the national average of 4%": 12 districts.
   - "… especially Nyaruguru, Ngoma, Rulindo, Nyabihu and Gakenke": the top five.
   - "Reliance on exclusively informal products is highest in Gicumbi": the maximum.
   - Bank-led only in Kicukiro, Nyarugenge and Gasabo: the only three where banked exceeds other formal.

The values are seeded as dataset `finscope_2024` (`backend/app/data/finscope_2024.py`) into migration `0007`'s tables. `/ready` and `python -m app.db.seed --check` cover them like every other dataset.

## Commands

```powershell
cd backend
uv run python -m app.db.migrate --target dev upgrade head   # to 0007
uv run python -m app.db.seed --target dev                   # applies finscope_2024 once; reruns skip
uv run python -m app.db.seed --target dev --check           # 10/10 datasets match
uv run uvicorn app.main:app --no-access-log                 # then open /docs

# Tests for this slice
uv run pytest tests/unit/test_services/test_finscope_data.py tests/api/test_nisr.py
```
