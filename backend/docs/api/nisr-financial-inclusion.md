# Official published statistics: `/api/v1/nisr/*`

For the frontend. Five read-only endpoints serve **published** statistics from two different
surveys. Each figure cites its page and table or figure in the source report:

| Endpoint | Survey | Publisher |
|---|---|---|
| `GET /api/v1/nisr/sources` | both | |
| `GET /api/v1/nisr/financial-inclusion/national`, `…/districts` | FinScope Rwanda 2024 | Access to Finance Rwanda (AFR) |
| `GET /api/v1/nisr/poverty`, `GET /api/v1/nisr/health-insurance` | EICV7 2023/24 ([below](#eicv7-202324-poverty-and-health-insurance)) | National Institute of Statistics of Rwanda (NISR) |

The two surveys have different populations, definitions and methods (see
[EICV7 vs FinScope](#eicv7-vs-finscope-2024)). Don't present one as the other.

> **Status: contract v0.3, agreed.** These endpoints are contract v0.3 (§10 of
> `docs/architecture/api-contract-proposal.md`), agreed by the frontend teammate on
> 27 October 2026. That approval covers v0.3 only; v0.2 rev 2 still awaits sign-off. This guide
> is the field-level specification for these endpoints. The `/api/v1` prefix, problem+json errors
> and `X-Request-ID` behave exactly as in the contract.

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
- FinScope percentages are **integers exactly as printed** in the report: no recomputation, no re-rounding. The report notes that rounded percentages may not add up to 100 (p. 21), so rows can sum to 99–101. EICV7 values are decimals at full source precision (see below).
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

The list also contains `eicv7-2023-2024` (publisher NISR; fieldwork "October 2023 - October 2024";
`sampleSize` 15054 *households*; `documentFile` the NISR workbook with its SHA-256). Items are
sorted by `id`, and `meta.sourceIds` lists both.

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

## Known FinScope source issues (recorded, not resolved)

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

---

## EICV7 2023/24: poverty and health insurance

Source: **National Institute of Statistics of Rwanda (NISR)**, *Seventh Integrated Household
Living Conditions Survey (EICV7): Main Indicators Report 2023/24*. Recommended citation (report
p. 2): *"National Institute of Statistics of Rwanda (NISR) (2025) Seventh Integrated Household
Living Conditions Survey (EICV7) Report: NISR"*.

| | |
|---|---|
| Publication page | https://statistics.gov.rw/statistical-publications/poverty-and-social-protection/eicv7-main-indicators-report-202324 |
| Data file | `EICV7_Tables_MainIndicatorReport.xlsx` (NISR, last updated 28 Apr 2025), SHA-256 `8a01ec05d851d9813a855e513eb0e74046a070ca0235df9e81730560028e350d`, sheets `Table A9.23` and `Table A3.7` |
| Report PDF | `EICV7_Main Indicator Report.pdf` (2025, 111 pages), SHA-256 `6105321b6edaeac40df291d9b2450cec121cd0a0b7b750554aefabbfd5b2873c`; used for definitions and page references |
| Fieldwork | October 2023 – October 2024, 12 months in nine cycles (pp. 11, 12, 15) |
| Sample | 1,674 enumeration areas stratified by district, 9 households each; 15,054 households (62,110 people) surveyed (pp. 12, 15, 78); response rate above 99% |
| Lowest geography | district (all 30) |

Page numbers are the report's **printed** page numbers (PDF page = printed page + 2).

### `GET /api/v1/nisr/poverty`: Table A9.23 (p. 107)

**Headcount poverty rate:** the percentage of people whose consumption per adult equivalent falls below the poverty line of **RWF 560,127 per adult equivalent per year in January 2024 prices** (pp. 17, 79). The extreme poverty line is RWF 356,432 (the food poverty line), but this endpoint serves total poverty only. Denominator: all individuals in the household-based population.

The response has 38 records: national (1), `area` (urban, rural: 2), `province` (5) and `district` (30).

### `GET /api/v1/nisr/health-insurance`: Table A3.7 (p. 91)

**Population with health insurance:** the percentage of the population with any health insurance, whether community-based health insurance (Mutuelle), RSSB (formerly RAMA), employer or other (Table 3.5, p. 33). Denominator: all individuals in the household-based population, all ages.

The response has 45 records: national (1), `sex` (2), `area` (2), `province` (5), `quintile` (consumption quintiles Q1 = poorest 20% to Q5: 5) and `district` (30).

Consumption quintiles rank individuals by annual consumption per adult equivalent (p. 14).

### Response

```json
{
  "status": "available",
  "source": { "id": "eicv7-2023-2024", "publisher": "National Institute of Statistics of Rwanda (NISR)", "…": "same shape as /sources" },
  "indicator": {
    "code": "poverty_headcount_rate",
    "tableId": "A9.23",
    "label": "Headcount poverty rate",
    "definition": "Percentage of people who are poor: consumption per adult equivalent below the poverty line of RWF 560,127 …",
    "population": "All individuals in the household-based population",
    "unit": "percent",
    "surveyRound": "2023/24",
    "printedDecimals": 2,
    "citation": { "page": 107, "tableOrFigure": "Table A9.23: Headcount Poverty rate(%) by area of residence, province and district" }
  },
  "dimensions": ["national", "area", "province", "district"],
  "items": [
    {
      "indicatorCode": "poverty_headcount_rate",
      "tableId": "A9.23",
      "dimension": "national",
      "code": "rwanda",
      "label": "Poverty Rate",
      "districtCode": null,
      "estimatePct": 27.362976067289672,
      "standardErrorPct": 0.49624639004466625,
      "ciLowerPct": 26.389621090104246,
      "ciUpperPct": 28.3363310444751,
      "cvPct": 1.813568775648971,
      "designEffect": 1.8650754691612403,
      "notes": "The workbook labels this row 'Poverty Rate'; the printed table (p. 107) labels it 'Rwanda'."
    },
    {
      "indicatorCode": "poverty_headcount_rate",
      "tableId": "A9.23",
      "dimension": "district",
      "code": "nyamagabe",
      "label": "Nyamagabe",
      "districtCode": "nyamagabe",
      "estimatePct": 51.39408818367712,
      "standardErrorPct": 3.2140169282663194,
      "ciLowerPct": 45.09000328422896,
      "ciUpperPct": 57.698173083125276,
      "cvPct": 6.2536704937341385,
      "designEffect": 1.6701460450989005,
      "notes": null
    }
  ],
  "meta": { "isIllustrative": false, "dataKind": "official_published_statistics", "sourceIds": ["eicv7-2023-2024"], "count": 38 }
}
```

These excerpts are copied from a live response on the dev database (2026-10-27). For the health-insurance endpoint, the national row is `estimatePct` 85.31091707532129, CI 84.5985920667474–86.02324208389517.

**Fields:**
- **Ordering.** `items` follow the published table's row order; `dimensions` lists the dimensions present, in that order.
- **`code`** is a stable group code:
  - `rwanda`
  - `urban`, `rural`
  - `city_of_kigali`, `southern`, `western`, `northern`, `eastern`
  - `male`, `female`
  - `q1` to `q5`
  - the district code, which is the same slug as `GET /api/v1/districts`. `districtCode` is set only on district rows.
- **`label`** is the row label exactly as published.
- **Scales:**
  - `estimatePct`, `standardErrorPct`, `ciLowerPct` and `ciUpperPct` are on a 0–100 scale; the standard error is in percentage points.
  - `cvPct` is the coefficient of variation in percent.
  - `designEffect` has no unit.
- **Null values.** Every uncertainty field is `number | null`. `null` means *not published*; it is never 0 and never derived. Both tables publish all six values for every record, so no value is null today.

### Precision

- **Storage.** The workbook stores each value as an IEEE double, written with 17 significant digits (e.g. `28.336331044475099`). The database keeps that text exactly, in unconstrained `NUMERIC` columns.
- **The API.** It sends JSON numbers in the shortest form of the same double (e.g. `28.3363310444751`). Parsing it gives back exactly the workbook's value: no rounding, no precision lost.
- **Display.** The report prints these tables with two decimals (`printedDecimals: 2`). Round to that for display, e.g. 27.36 (95% CI 26.39–28.34). Headline text in the report rounds further (27.4%).
- **Cross-checks.** All 498 values, rounded to two decimals, match the printed tables on pp. 91 and 107.
- **Consistency.** Every published CI is the estimate ± 1.9614 standard errors, and CV = 100 × SE / estimate. A test checks both; neither is recomputed or served from that check.

### Methodology and comparability

- **Revised method.** EICV7 changed how consumption and poverty are measured (p. 13):
  - fewer household visits;
  - a 7-day food recall, and food eaten away from home;
  - household-level Paasche deflators to January 2024 prices;
  - a new adult-equivalence scale;
  - a poverty line built on 2,400 kcal per adult equivalent per day, valued at second-quintile consumption patterns.

  **EICV7 poverty rates are not directly comparable with earlier published EICV rates** (pp. 11, 13, 18).
- **The report's trend.** It compares 27.4% in 2023/24 with a **modelled** 2016/17 rate of 39.8%: the EICV5 data re-estimated with the EICV7 method by an OLS model with multiple imputation (95% CI 37.7–41.4, model-dependent). That is a fall of **12.4 percentage points** (pp. 18, 82, Table 9.3). The originally published EICV5 rate was 38.2% (p. 19).
  - These trend figures are in the source's `notes` but are **not served as records**.
  - Don't chart 27.4% against older published rates.
- **Health insurance.** The report says coverage rose from 74% (EICV5, 2017) to 85% (p. 32). This endpoint serves 2023/24 only.
- **Interpretation.** These are descriptive survey estimates with sampling error.
  - District estimates are less precise: CVs reach 19.3% (Kicukiro poverty), and Kigali's three districts have CVs above 15%.
  - Treat differences between groups whose confidence intervals overlap as not established.
  - Nothing here supports causal claims, for example that insurance reduces poverty.

### Known EICV7 source issues (recorded, not resolved)

1. **Gisagara.** The report text (p. 80) gives Gisagara's poverty rate as 46.6%; Table A9.23 and Figure 9.1 give 45.59 (45.6). The table value is served, with a note on that record.
2. **National row label.** In A9.23 the workbook labels the national row "Poverty Rate", while the printed table says "Rwanda". The workbook label is served, with a note.
3. **Publication date.** The report gives only the year (2025). The workbook is dated 28 April 2025 and the PDF 9–10 July 2025, so `publicationDate` is `"2025"`.
4. **Table 9.1 copy.** The workbook's Table 9.1 repeats A9.23's national, area and province rows. A few of its values differ in the last binary digit (about 1e-15), which is not visible at any printed precision. A9.23 is the source used here.

## EICV7 vs FinScope 2024

| | EICV7 2023/24 | FinScope 2024 |
|---|---|---|
| Publisher | NISR | Access to Finance Rwanda (AFR) |
| Population | Whole household population (all ages) | Adults aged 16+ |
| Topic | Consumption poverty; health insurance | Use of financial products and services |
| Uncertainty published | SE, 95% CI, CV, design effect | none |
| Precision | full workbook precision (decimals) | integers as printed |

- **Different measures.** Health insurance in EICV7 is not FinScope's "insurance" product use. EICV7 measures coverage of the whole population, mostly community-based health insurance; FinScope measures adults' use of financial products.
- **Different surveys.** The two surveys use different samples, periods and definitions. Show them side by side only with their own labels, and never combine or difference their values.

## Commands

```powershell
cd backend
uv run python -m app.db.migrate --target dev upgrade head   # to 0008
uv run python -m app.db.migrate --target dev current        # 0008 (head)
uv run python -m app.db.seed --target dev                   # applies changed datasets once; reruns skip
uv run python -m app.db.seed --target dev --check           # 11/11 datasets match
uv run uvicorn app.main:app --no-access-log                 # then open /docs

# Re-verify the EICV7 transcription against NISR's workbook (read-only; exit 0 = all values match)
uv run python -m app.data.eicv7_workbook ..\nisr\EICV7_Tables_MainIndicatorReport.xlsx

# Tests for these endpoints
uv run pytest tests/unit/test_services/test_finscope_data.py tests/api/test_nisr.py
uv run pytest tests/unit/test_services/test_eicv7_data.py tests/unit/test_eicv7_workbook.py tests/api/test_nisr_eicv7.py
```
