# Data

CSV copies of the data Imibereho uses. The platform loads the same values from `backend/app/data/`, which stays the source of truth. To regenerate these files, run this from `backend/`:

```bash
uv run python scripts/export_data.py
```

## Official published statistics

| Folder | Source | Files |
| :--- | :--- | :--- |
| `eicv7_2023_24/` | NISR EICV7 Main Indicators Report 2023/24, Tables A9.23 and A3.7 | `survey_estimates.csv`, `statistical_sources.csv` |
| `finscope_2024/` | FinScope Rwanda 2024 report (Access to Finance Rwanda) | `financial_inclusion_indicators.csv`, `financial_access_strand_districts.csv`, `statistical_sources.csv` |
| `sas_2025/` | NISR Seasonal Agricultural Survey 2025 | `statistical_sources.csv` (the crop calendar and production figures are constants in `backend/app/data/sas_2025.py`) |

## Illustrative and synthetic data

These are not official statistics or citizen data. API responses that use them carry `meta.isIllustrative: true`.

| Folder | Contents |
| :--- | :--- |
| `synthetic_households/` | 3,000 invented households |
| `vulnerability/` | Vulnerability model, bands and the 30 district scores |
| `budget_benchmarks/`, `reference_household/`, `expense_categories/`, `districts/` | Budget reference data |
| `dashboard_dimensions/`, `seasonal/`, `methodology/` | Dashboard, seasonal and methodology reference data |

`backend/app/data/README.md` gives the source of each dataset.
