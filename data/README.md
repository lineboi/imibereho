# Data

CSV copies of the data Imibereho uses. The platform loads the same values from `backend/app/data/`, which stays the source of truth. To regenerate these files, run this from `backend/`:

```bash
uv run python scripts/export_data.py
```

## Official published statistics

| Source | Files |
| :--- | :--- |
| NISR EICV7 Main Indicators Report 2023/24, Tables A9.23 and A3.7 | `eicv7_2023_24_survey_estimates.csv`, `eicv7_2023_24_statistical_sources.csv` |
| FinScope Rwanda 2024 report (Access to Finance Rwanda) | `finscope_2024_financial_inclusion_indicators.csv`, `finscope_2024_financial_access_strand_districts.csv`, `finscope_2024_statistical_sources.csv` |
| NISR Seasonal Agricultural Survey 2025 | `sas_2025_statistical_sources.csv` (the crop calendar and production figures are constants in `backend/app/data/sas_2025.py`) |

## Illustrative and synthetic data

These are not official statistics or citizen data. API responses that use them carry `meta.isIllustrative: true`.

| Contents | Files |
| :--- | :--- |
| 3,000 invented households | `synthetic_households.csv` |
| Vulnerability model, bands and the 30 district scores | `vulnerability_models.csv`, `vulnerability_bands.csv`, `vulnerability_district_vulnerability.csv` |
| Budget reference data | `budget_benchmarks.csv`, `reference_households.csv`, `expense_categories.csv`, `districts.csv` |
| Dashboard, seasonal and methodology reference data | `dashboard_dimensions_*.csv`, `seasonal_*.csv`, `methodology_versions.csv` |

`backend/app/data/README.md` gives the source of each dataset.
