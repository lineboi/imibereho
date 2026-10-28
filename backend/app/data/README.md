# Seed data

**Official published statistics**, served only by `/api/v1/nisr/*` with `isIllustrative: false`
(see `backend/docs/api/nisr-financial-inclusion.md`):
- `finscope_2024.py`: values transcribed from the FinScope Rwanda 2024 report (Access to Finance
  Rwanda), each with its page and figure.
- `eicv7_2023_24.py`: NISR's EICV7 2023/24 annex Tables A9.23 (poverty) and A3.7 (health
  insurance), extracted verbatim from NISR's workbook by `eicv7_workbook.py` (which uses the
  stdlib reader `xlsx_reader.py`). Re-check against the workbook with
  `uv run python -m app.data.eicv7_workbook <path to EICV7_Tables_MainIndicatorReport.xlsx>`.
- `sas_2025.py`: NISR's Seasonal Agricultural Survey 2025 (season calendar, Table 0 crop
  production by season) for `/api/v1/agro/harvest-calendar`. Only the source row is seeded; the
  calendar and production figures are versioned constants with their provenance.

Each official dataset owns only its own source's rows in the shared tables (`TableRows.partition`),
so adding a source never deletes or re-hashes another one.

**Illustrative (methodology v0.1):** every other module here. Every API response that uses it carries
`meta.isIllustrative: true`. None of it is official statistics or citizen data.

| Module | Datasets | Source |
|---|---|---|
| `reference.py` | `methodology`, `districts`, `expense_categories`, `reference_household`, `budget_benchmarks`, `dashboard_dimensions` | Figma design (node IDs cited in the module) and contract v0.2 rev 2 |
| `seasonal.py` | `seasonal` | Contract §4 text, citing `2:6698` and `2:6714` |
| `vulnerability.py` | `vulnerability` | Weights, bands and all 30 scores from the design (`2:7355`, `2:7061`, `2:6965`); Gasabo's components from `2:7097`. **[SYN]** the other 29 districts' components |
| `finscope_2024.py` | `finscope_2024` | **Official published statistics**: FinScope Rwanda 2024 report, pp. 25, 27, 31, 69 (not illustrative) |
| `eicv7_2023_24.py` | `eicv7_2023_24` | **Official published statistics**: NISR EICV7 Main Indicators Report 2023/24, Tables A9.23 (p. 107) and A3.7 (p. 91), from the NISR workbook (not illustrative) |
| `sas_2025.py` | `sas_2025` | **Official published statistics**: NISR Seasonal Agricultural Survey 2025, annual tables (Table 0) and summary p. 2 (not illustrative) |
| `synthetic_households.py` | `synthetic_households` | **[SYN]** 3,000 invented households; only the totals come from the design (`2:6793`, `2:6864`, `2:6805`) |

`registry.py` defines datasets and the canonical SHA-256 content hash that the seed framework
(`app/db/seed.py`) and `/ready` compare.

## Rules

- Values from the design are cited by Figma node ID. Invented inputs are marked **[SYN]** and
  are generated deterministically from a fixed seed (`20261024`).
- Never add a value that the design, the contract or an approved decision does not provide.
  If a value is missing, record it as an open question; don't invent it.
- A change to any dataset changes its hash. The next `python -m app.db.seed --target …` reapplies
  it, and `/ready` reports `seed: failed` until it does.
