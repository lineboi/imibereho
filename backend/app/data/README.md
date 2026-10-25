# Seed data (methodology v0.1)

Everything here is **illustrative**. Every API response that uses it carries
`meta.isIllustrative: true`. None of it is official statistics or citizen data.

| Module | Datasets | Source |
|---|---|---|
| `reference.py` | `methodology`, `districts`, `expense_categories`, `reference_household`, `budget_benchmarks`, `dashboard_dimensions` | Figma design (node IDs cited in the module) and contract v0.2 rev 2 |
| `seasonal.py` | `seasonal` | Contract §4 text, citing `2:6698` and `2:6714` |
| `vulnerability.py` | `vulnerability` | Weights, bands and all 30 scores from the design (`2:7355`, `2:7061`, `2:6965`); Gasabo's components from `2:7097`. **[SYN]** the other 29 districts' components |
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
