# API Contract — Imibereho (contract v0.2)

> **This is the single authoritative frontend–backend API contract.** If any other document (`backend-requirements.md`, `IMPLEMENTATION_PLAN.md`, the project document) disagrees with it, this file wins and the other document is corrected.
> **Status: v0.2, backend proposal, awaiting frontend sign-off.** Nothing here is implemented yet. Once frontend and backend agree, the status becomes "agreed". After that, changes need a new contract version and a note in §9.
> **Basis:** the Figma screens ([design-inventory.md](../figma/design-inventory.md)), [backend-requirements.md](./backend-requirements.md), and the resolutions of Q-01, Q-02, Q-04 and Q-15 in [open-questions.md](../requirements/open-questions.md).
>
> **Evidence labels** (same as the other docs, plus one):
> - **[E]** shown in the design (node ID cited)
> - **[I]** inferred from the design
> - **[PD]** proposed default for an open Q-xx; it becomes binding only when `IMPLEMENTATION_PLAN.md` is approved and the frontend signs off.

## 0. Versions

Three version numbers exist. They are independent.

| Version | Value | Changes when |
|---|---|---|
| API path | `/api/v1` | A breaking change after the demo |
| Contract (this document) | `0.2` | Any change to a field, an endpoint or the error behaviour. Mirrored in OpenAPI `info.version` = `0.2.0` |
| Methodology | `"0.1"` | Calculation rules or seeded data change. Returned in `meta.methodologyVersion` ([E] "CONCEPT METHOD · v0.1", `2:7333`) |

## 1. Conventions

| Topic | Rule |
|---|---|
| Base URL | `/api/v1`. The health checks `/health` and `/ready` are at the root, outside `/api/v1`. |
| Format | JSON, UTF-8. Field names are `camelCase`. |
| Auth | None. Q-04 is resolved: the demo has no login. |
| Citizen data | Never stored (Q-02 resolved, Option A). Request bodies are processed and then discarded, never logged. Money values travel only in POST bodies, never in query strings, because hosting-platform access logs record full URLs. |
| Money | Integer RWF, e.g. `180000`. The frontend formats `180,000 RWF` and `18m RWF`. |
| Numbers in responses | Every numeric field is a **JSON number, never a string**. Integers (money, counts, scores, months) are written without a decimal point. Fractional fields are written with no more decimal places than listed: ratios and shares 4 (`0.8333`), `runwayMonths` 1 (`7.5`, `10.0`), weights 2 (`0.4`), swap quantities 2 (`1`, `2`). |
| Percent inputs | Integer 0–100. `20` means 20%. |
| Ratios in outputs | A decimal fraction rounded half up to 4 places, e.g. `0.8333`. The frontend rounds for display (83.3%). [PD] Q-17 |
| Dates and months | ISO 8601: `2026-10-07`; a month is `2026-10`. **The year 2026 is an assumption [I]:** the design shows only "October" and "7 October" (`2:6444`, `2:6783`). |
| IDs | Stable lowercase slugs: districts `gasabo`, categories `food`. |
| Language | English only in v1 [PD] Q-03. `Accept-Language` is ignored and responses carry `Content-Language: en`. |
| Lists | `{ "items": [...], "meta": {...} }`. No pagination: every list holds 30 items or fewer. |
| Request IDs | Every response carries an `X-Request-ID` header. A client-supplied `X-Request-ID` is echoed back. |
| CORS | Browsers may call the API only from allow-listed origins. `http://localhost:5173` (Vite dev) is allowed from the first deploy. **The deployed frontend origin must be supplied by the frontend team.** |

### 1.1 Response envelope

Every **data or calculation** response, including `/dashboard/filters` and `/methodology`, carries:

```json
"meta": { "isIllustrative": true, "methodologyVersion": "0.1" }
```

`isIllustrative` is always `true` (FR-20; every screen is labelled illustrative). List responses may add `"count"` inside `meta`. Error responses and the health checks do not carry `meta`.

### 1.2 Number parsing

| Where | Accepted | Rejected with 422 `not_integer` | Then |
|---|---|---|---|
| Query string integers | After URL decoding, the value must match `^[0-9]+$`: `householdSize=4`, `householdSize=%34` (decodes to `4`), `householdSize=04` | `4.0`, `4.5`, `4e0`, `+4`, `-1`, ` 4` (leading space), `0x4`, `abc`, an empty value | A value that parses but is outside the field's bounds → 422 `out_of_range` |
| JSON body integers | JSON integer tokens: `180000` | Strings (`"180000"`), fractions (`1.5`), numbers written with a decimal point (`4.0`), booleans (`true`, `false`), `null` on a required field (→ `required`) | Out of bounds → 422 `out_of_range` |

A negative query value such as `-1` fails the digit pattern and is reported as `not_integer`, not `out_of_range`.

### 1.3 Error format (RFC 9457 problem details)

Content type: `application/problem+json`.

```json
{
  "type": "https://imibereho.example/errors/validation",
  "title": "Invalid request",
  "status": 422,
  "detail": "One or more fields are invalid.",
  "errors": [
    { "field": "shock.incomeReductionPct", "code": "out_of_range", "message": "Must be between 0 and 100." }
  ]
}
```

`errors[].field` is the camelCase dotted path to the field. `errors` is present only on 400 `unknown-parameter` and on 422. Every problem body carries exactly `type`, `title`, `status` and `detail`, plus `errors` where listed, plus `checks` on 503 `not-ready`.

**Evaluation order:** request validation (400, 422) happens before any lookup (404). A request with both an invalid `householdSize` and an unknown `district` gets 422.

| Status | `type` slug | When | `errors[].code` |
|---|---|---|---|
| 400 | `malformed-request` | The body is not valid JSON (FastAPI's `json_invalid`). Body: `{"type":"https://imibereho.example/errors/malformed-request","title":"Malformed request","status":400,"detail":"The request body is not valid JSON."}` | — (no `errors`) |
| 400 | `unknown-parameter` | A query parameter the endpoint does not define | `unknown_field` |
| 404 | `district-not-found` | **Only** for an unknown value in the `district` query parameter (`/budget-benchmarks`, `/seasonal-swaps`, and the optional `/calculations/budget-comparison` body field `district`) or the `districtCode` path parameter (`/district-vulnerability/{districtCode}`). An invalid **`geography`** filter value is **not** a 404: it is 422 `unknown_value` (§5) | — |
| 404 | `benchmark-not-available` | No benchmark exists for this district and household size | — |
| 404 | `not-found` | Unknown route | — |
| 405 | `method-not-allowed` | Wrong HTTP method | — |
| 422 | `validation` | Field-level failures | `required`, `out_of_range`, `not_integer`, `unknown_value` (a bad enum or filter value), `too_long`, `unknown_field` (an extra body field) |
| 429 | `rate-limited` | Too many calculation requests; includes a `Retry-After` header. **Optional step**; may not ship | — |
| 500 | `internal` | Unexpected error. No internal detail is returned; quote `X-Request-ID` when reporting | — |
| 503 | `not-ready` | Only from `/ready`; carries a `checks` member (§2) | — |

## 2. Health checks (root, not under `/api/v1`)

| Endpoint | Meaning | Response |
|---|---|---|
| `GET /health` | **Liveness:** the process is up and serving HTTP. Never touches the database. **This is the hosting platform's health-check path.** | Always `200 {"status":"ok"}` while the process runs |
| `GET /ready` | **Readiness:** this build can serve correct data | `200 {"status":"ready","checks":{"database":"ok","migrations":"ok","seed":"ok"}}`, or `503` problem+json `not-ready` with the same `checks` object, where each failing check is `"failed"` |

**`/ready` checks:**
- `database`: `SELECT 1` succeeds.
- `migrations`: the database's Alembic revision equals the build's head revision.
- `seed`: every seed dataset **defined in this build** is loaded at its expected content hash.

**Pre-seed behaviour:** a build that defines no seed datasets passes the `seed` check trivially, so `/ready` is 200 from the very first deployment. From the build that introduces methodology `0.1` and its reference data onward, those datasets are part of the check.

Neither endpoint carries `meta`. The server applies migrations and seeds **before** it starts accepting requests, so once `/health` answers, startup migration and seeding have already succeeded.

## 3. Reference data (core)

### `GET /api/v1/districts`
Used by the C1 district select (`2:6384`), the C3 and C5 district filters (`2:6505`, `2:6680`), and the D2 tiles (`2:6965`).
```json
{
  "items": [
    { "code": "bugesera", "name": "Bugesera", "province": null },
    { "code": "gasabo",   "name": "Gasabo",   "province": null }
  ],
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1", "count": 30 }
}
```
- Districts are listed alphabetically, matching the D2 grid caption "Alphabetical tile grid" [E] `2:6959`.
- `province` is always `null` [PD] Q-21.
- Query parameters: none. Any parameter → 400.

### `GET /api/v1/expense-categories`
Used by the C2 expense icons (`2:6456`) and the C3 rows (`2:6530`).
```json
{
  "items": [
    { "code": "food",             "name": "Food",             "icon": "shopping-basket" },
    { "code": "housing",          "name": "Housing",          "icon": null },
    { "code": "transport",        "name": "Transport",        "icon": "bus" },
    { "code": "utilities",        "name": "Utilities",        "icon": "zap" },
    { "code": "other_essentials", "name": "Other essentials", "icon": null }
  ],
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1", "count": 5 }
}
```
- `icon` is a Lucide icon name.
- Housing and Other essentials have no icon in the design, so `icon` is `null` and the frontend chooses one [PD] Q-11.

## 4. Citizen endpoints (core)

### `GET /api/v1/budget-benchmarks?district={code}&householdSize={int}`
Used by the C3 "Demo reference" column (`2:6534`).

| Parameter | Rule | Failure |
|---|---|---|
| `district` | Required; a known district code | missing → 422 `required`; unknown → 404 `district-not-found` |
| `householdSize` | Required; integer 1–20 [PD] Q-20 | 422 `required`, `not_integer` or `out_of_range` |

```json
{
  "district": { "code": "gasabo", "name": "Gasabo" },
  "householdSize": 4,
  "lines": [
    { "categoryCode": "food",             "monthlyAmount": 65000 },
    { "categoryCode": "housing",          "monthlyAmount": 40000 },
    { "categoryCode": "transport",        "monthlyAmount": 20000 },
    { "categoryCode": "utilities",        "monthlyAmount": 10000 },
    { "categoryCode": "other_essentials", "monthlyAmount": 15000 }
  ],
  "total": 150000,
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1" }
}
```
- **Coverage [PD] Q-32:** one illustrative benchmark set, for household size 4, is returned for every district. The design shows only Gasabo with 4 people and calls the comparison "invented … not a district average" (`2:6572`).
- Any other household size → 404 `benchmark-not-available`. The frontend either limits the C3 size picker to 4 or shows an empty state (Q-27).
- The per-category comparison and the insight sentence (`2:6571`) are computed by the frontend from these lines (BR-13, Q-09), unless the optional `POST /calculations/budget-comparison` (§6) ships.

### `POST /api/v1/calculations/household-shock`
Used by C4 (`2:6608`, `2:6633`, `2:6640`). It can also supply the C2 balance (`2:6428`).

Request:
```json
{
  "baseline": { "monthlyIncome": 180000, "monthlyEssentials": 150000, "savings": 60000 },
  "shock":    { "type": "income_fall", "incomeReductionPct": 20, "durationMonths": 3 }
}
```

| Field | Rule |
|---|---|
| `baseline.monthlyIncome`, `baseline.monthlyEssentials`, `baseline.savings` | Integer 0–100,000,000 [PD] Q-20 |
| `shock.type` | `income_fall` only [PD] Q-10; any other value → `unknown_value` |
| `shock.incomeReductionPct` | Integer 0–100 |
| `shock.durationMonths` | Integer 1–24 [PD] Q-20 |

Response `200`:
```json
{
  "baselineMonthlyBalance": 30000,
  "shockedMonthlyIncome": 144000,
  "monthlyGap": 6000,
  "savingsUsed": 18000,
  "savingsRemaining": 42000,
  "savingsExhausted": false,
  "runwayMonths": 10.0,
  "assumptions": ["expenses_held_constant", "no_new_borrowing", "no_additional_shocks"],
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1" }
}
```

| Field | Rule |
|---|---|
| `baselineMonthlyBalance` | BR-01 |
| `shockedMonthlyIncome` | BR-02, whole RWF rounded half up [PD] Q-17 |
| `monthlyGap` | BR-03; `0` when shocked income covers essentials |
| `savingsUsed`, `savingsRemaining` | BR-04 and BR-05. `savingsUsed` is capped at `savings` [I], so `savingsRemaining` is never negative |
| `savingsExhausted` | `true` when `monthlyGap × durationMonths > savings` (that is, when the BR-04 cap applies) [PD] |
| `runwayMonths` | BR-06, rounded half up to 1 decimal place. `null` when `monthlyGap` is 0 [PD] Q-17; the frontend shows a "no gap" state (not designed). With `savings` 0 and a gap above 0, it is `0.0` |
| `assumptions` | Fixed codes mirroring the C4 assumption text in `2:6608` |

Errors: 400 malformed JSON; 422 with the codes above.

### `GET /api/v1/seasonal-swaps?district={code}&month={1-12}`
Used by C5 (`2:6698`, `2:6714`). Both parameters are required: an unknown district → 404; `month` outside 1–12 → 422.
```json
{
  "items": [
    {
      "id": "rice-to-sweet-potato",
      "title": "Try a different staple",
      "description": "For one household meal, consider sweet potatoes instead of rice. Pair with beans and leafy vegetables.",
      "from": { "name": "Rice",           "quantity": 1, "unit": "kg", "price": 2000 },
      "to":   { "name": "Sweet potatoes", "quantity": 2, "unit": "kg", "price": 1600 },
      "difference": 400,
      "footnote": "Different quantities; not a nutritional equivalent. Prices are invented, not market observations."
    }
  ],
  "tips": [
    { "title": "Keep variety on the plate.", "body": "Beans, amaranth leaves (dodo) and a locally available staple can offer variety. Consider cooking fuel, storage, dietary needs and portions for your household." }
  ],
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1" }
}
```
- `difference` is computed by BR-14.
- The seeded swap applies to every district, in month 10 only [PD] Q-32. Any other month returns `items: []` with the tips; the empty state is not designed (Q-27).
- The hero image and caption (`2:6691`, `2:6692`) are static frontend content [PD] Q-12.

## 5. Decision-maker endpoints (core)

### `GET /api/v1/dashboard/filters`
Used by the D1 and D2 filter selects (`2:6774`, `2:6941`).
```json
{
  "geographies":     [{ "code": "all",     "label": "All districts",          "isDefault": true }],
  "periods":         [{ "code": "2026-10", "label": "Demo month · October",   "isDefault": true }],
  "householdGroups": [{ "code": "all",     "label": "All sample households",  "isDefault": true }],
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1" }
}
```
- **[PD] Q-14:** only the defaults shown in the design (`2:6783`, `2:6788`) exist. Geography offers `all` only.
- Per-district geography is an optional step that needs a decision first (§6, and plan §6). If it ships, the 30 districts are added to `geographies`.

### `GET /api/v1/dashboard/overview?geography=all&period=2026-10&householdGroup=all&topN=2`
Used by D1 (`2:6790`, `2:6809`, `2:6861`, `2:6882`, `2:6888`).

| Parameter | Default | Rule |
|---|---|---|
| `geography` | `all` | Must be a `code` listed in `geographies` by `/dashboard/filters`, else 422 `unknown_value`. This applies to district codes too (`gasabo`) and to unknown strings (`atlantis`): never 404 |
| `period` | `2026-10` | Must be a `code` listed in `periods`, else 422 `unknown_value` |
| `householdGroup` | `all` | Must be a `code` listed in `householdGroups`, else 422 `unknown_value` |
| `topN` | `2` | Integer 1–30 (§1.2) |

```json
{
  "kpis": {
    "sampleSize": 3000,
    "referenceHousehold": { "districtCode": "gasabo", "householdSize": 4, "monthlyIncome": 180000, "monthlyEssentials": 150000, "savings": 60000 },
    "essentialsToIncomeRatio": 0.8333,
    "shockDeficit": { "incomeReductionPct": 20, "householdsInDeficit": 1000, "share": 0.3333 }
  },
  "essentialsTrend": {
    "unit": "RWF",
    "incomeReference": 180000,
    "points": [
      { "month": "2026-05", "essentials": 138000 },
      { "month": "2026-06", "essentials": 140000 },
      { "month": "2026-07", "essentials": 143000 },
      { "month": "2026-08", "essentials": 145000 },
      { "month": "2026-09", "essentials": 148000 },
      { "month": "2026-10", "essentials": 150000 }
    ]
  },
  "incomeSources": [
    { "code": "wage",                "label": "Wage income",         "households": 1200, "share": 0.4 },
    { "code": "agriculture",         "label": "Agriculture",         "households": 1050, "share": 0.35 },
    { "code": "informal_enterprise", "label": "Informal enterprise", "households": 750,  "share": 0.25 }
  ],
  "insight": { "baselineMonthlyBalance": 30000, "shockMonthlyGap": 6000, "incomeReductionPct": 20 },
  "topDistricts": [
    { "code": "nyagatare", "name": "Nyagatare", "score": 74, "band": "band4" },
    { "code": "bugesera",  "name": "Bugesera",  "score": 71, "band": "band4" }
  ],
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1" }
}
```
- Trend values are in RWF; the chart axis shows thousands, so the frontend divides by 1,000 ([E] `2:6826`).
- The 3,000-household sample is **invented synthetic data** [E] "Demo households · not representative" (`2:6793`). Only the totals above come from the design.
- `topDistricts` is ordered by score descending, with ties broken by name.

### `GET /api/v1/district-vulnerability?period=2026-10&householdGroup=all&sort=name&limit=30`
Used by the D2 grid, legend and ranking (`2:6959`, `2:7061`, `2:7102`).

| Parameter | Default | Rule |
|---|---|---|
| `period` | `2026-10` | As for overview: an unlisted value → 422 `unknown_value` |
| `householdGroup` | `all` | As for overview: an unlisted value → 422 `unknown_value` |
| `sort` | `name` | `name` (the grid order) or `-score` (the ranking); anything else → 422 `unknown_value` |
| `limit` | `30` | Integer 1–30 (§1.2) |

```json
{
  "model": {
    "version": "0.1",
    "weights": { "incomeInstability": 0.4, "essentialCostPressure": 0.4, "lowBufferExposure": 0.2 },
    "bands": [
      { "key": "band1", "min": 0,  "max": 39 },
      { "key": "band2", "min": 40, "max": 59 },
      { "key": "band3", "min": 60, "max": 69 },
      { "key": "band4", "min": 70, "max": 100 }
    ]
  },
  "items": [
    { "districtCode": "bugesera", "name": "Bugesera", "score": 71, "band": "band4" },
    { "districtCode": "gasabo",   "name": "Gasabo",   "score": 46, "band": "band2" }
  ],
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1", "count": 30 }
}
```
- `score` is an integer [PD] Q-17.
- The band colours stay in the frontend (A-8).
- `sort=-score&limit=6` reproduces `2:7102`. Ties are broken by name.

### `GET /api/v1/district-vulnerability/{districtCode}?period=2026-10&householdGroup=all`
Used by the D2 "Selected district" panel (`2:7079`).
- An unknown `districtCode`, including a wrongly cased one such as `Gasabo`, → 404 `district-not-found`.
- `period` and `householdGroup` follow the list endpoint's rules: an unlisted value → 422 `unknown_value`, checked before the district lookup.
```json
{
  "districtCode": "gasabo",
  "name": "Gasabo",
  "score": 46,
  "band": "band2",
  "components": [
    { "code": "incomeInstability",     "label": "Income instability",      "weight": 0.4, "value": 50 },
    { "code": "essentialCostPressure", "label": "Essential-cost pressure", "weight": 0.4, "value": 40 },
    { "code": "lowBufferExposure",     "label": "Low-buffer exposure",     "weight": 0.2, "value": 50 }
  ],
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1" }
}
```
- The frontend builds the formula text "0.4 × 50 + …" from `components`.
- Gasabo's components come from the design ([E] `2:7097`). **The other 29 districts' components are invented synthetic inputs**, chosen only so that BR-09 reproduces each D2 score; the design says "Inputs and weights are invented for this prototype".
- The default selected district (Gasabo) is a frontend choice [PD] Q-22.

### `POST /api/v1/calculations/policy-scenario`
Used by D3 (`2:7180`, `2:7224`, `2:7233`).

Request:
```json
{
  "instrument": "monthly_cash_support",
  "incomeLossPct": 20,
  "durationMonths": 3,
  "supportPerHouseholdMonthly": 6000,
  "eligibleHouseholds": 1000,
  "baseline": { "monthlyIncome": 180000, "monthlyEssentials": 150000, "savings": 60000 }
}
```

| Field | Rule |
|---|---|
| `instrument` | `monthly_cash_support` only [PD] Q-10 |
| `incomeLossPct` | Integer 0–100 |
| `durationMonths` | Integer 1–24 |
| `supportPerHouseholdMonthly` | Integer 0–100,000,000 |
| `eligibleHouseholds` | Integer 0–3,000, the sample size [I] |
| `baseline` | Optional; same shape and rules as household-shock. When it is omitted, the reference household ([E] `2:7209`) is used [PD] Q-23 |

Response `200`:
```json
{
  "directTransferBudget": 18000000,
  "modelledMonthlyGapWithSupport": 0,
  "horizonMonths": 3,
  "baselineUsed": { "monthlyIncome": 180000, "monthlyEssentials": 150000, "savings": 60000, "source": "reference" },
  "comparison": {
    "columns": ["no_shock", "shock_only", "shock_with_support"],
    "rows": {
      "incomePerMonth":      { "no_shock": 180000, "shock_only": 144000, "shock_with_support": 144000 },
      "supportPerMonth":     { "no_shock": 0,      "shock_only": 0,      "shock_with_support": 6000 },
      "expensesPerMonth":    { "no_shock": 150000, "shock_only": 150000, "shock_with_support": 150000 },
      "netMonthlyBalance":   { "no_shock": 30000,  "shock_only": -6000,  "shock_with_support": 0 },
      "savingsAfterHorizon": { "no_shock": 150000, "shock_only": 42000,  "shock_with_support": 60000 }
    }
  },
  "assumptions": ["surpluses_saved", "gaps_paid_from_savings", "no_interest", "no_debt", "no_admin_costs", "no_further_shocks", "no_behavioural_effects"],
  "meta": { "isIllustrative": true, "methodologyVersion": "0.1" }
}
```
- `baselineUsed.source` is `"reference"` or `"request"`.
- `netMonthlyBalance` can be negative. The frontend shows it with a "−" sign in the warning colour (`#94602b`).
- `savingsAfterHorizon` follows **BR-07 as written**: savings + horizon × net balance. It **can be negative** when gaps exceed savings; the design never shows that case, and its presentation is an open Q-17 item.
- The calculation is deterministic and never stored [PD] Q-19.

## 6. Optional endpoints

These ship only if the core endpoints are done in time. Each one has a frontend fallback, so the frontend must work without them. They are listed in the order they would be cut (first listed, first cut).

| Endpoint | Purpose | Frontend fallback if it does not ship |
|---|---|---|
| `GET /api/v1/methodology` | D4 structured data: `version`, `status`, `statusNote` (`2:7331`), `weights`, `bands`, `referenceHousehold`, `dataSources[{content, validationNeed, status}]` (`2:7357`; status is `not_connected`, `to_confirm` or `not_validated`), plus `meta`. **Prose is not served** [PD] Q-12 | Hardcode D4 entirely |
| `POST /api/v1/calculations/budget-comparison` | Body `{district, householdSize, plan:[{categoryCode, plannedAmount}]}`, with each of the 5 categories exactly once. Returns `lines[{categoryCode, planned, reference, difference}]`, `totals{planned, reference, difference}`, `largestAbove`, `largestBelow` (each `{categoryCode, difference}` or `null`), plus `meta`. Ties are broken by category order [PD] Q-09 | Compute BR-13 in the frontend from `/budget-benchmarks` |
| `GET /api/v1/demo-household` | The data behind "Skip setup" (`2:6404`) [PD] Q-05/Q-06: `profile{districtCode:"gasabo", householdSize:4, monthlyIncome:180000, savings:60000}`, `month:"2026-10"`, `plan{lines (60,000 / 45,000 / 18,000 / 12,000 / 15,000), plannedTotal:150000}`, `expenses` (the three `2:6444` items dated `2026-10-07`), plus `meta` | Bundle these values in the frontend |
| Geography filter on `/dashboard/overview` | `geography={districtCode}` would change `sampleSize`, `shockDeficit` and `incomeSources`. **Needs a decision first** (plan §6, Q-14 / Q-18), because it presents per-district figures drawn from invented data | `geography=all` only |

Rate limiting (429) is also optional. Every other code in §1.3 applies to all endpoints.

## 7. Screen → data matrix

| Screen | Core endpoints | Computed or held by the frontend | States the frontend must design (none exist in Figma, Q-27) |
|---|---|---|---|
| C1 Welcome | `/districts` | Profile on the device | District list fails to load → allow continuing without a district |
| C2 Home | `/expense-categories`; optionally `household-shock` | Balance (BR-01), daily total (BR-15), expenses on the device | No expenses today; no profile |
| C3 Budget advisor | `/budget-benchmarks`, `/districts` | BR-13 differences and the insight sentence (if the optional endpoint is absent) | 404 `benchmark-not-available`; no plan entered |
| C4 Resilience simulator | `household-shock` | Form state | Calculating; `monthlyGap = 0` with `runwayMonths = null`; 422 errors |
| C5 Agro swaps | `/seasonal-swaps`, `/districts` | — | `items: []`; loading |
| D1 Overview | `/dashboard/filters`, `/dashboard/overview` | Number formatting, chart scaling | Loading; error |
| D2 Heatmap | `/district-vulnerability`, `/district-vulnerability/{code}` | Selected district; band colours | Detail loading |
| D3 Policy simulator | `policy-scenario` | Form state, the "applied" state | Validation errors; negative savings |
| D4 Methodology | Optional `/methodology` | All prose (A-8, Q-12) | — |

## 8. Owned by the frontend

- All UI copy and guidance notes (A-8).
- Band colours and the heatmap grid layout.
- Number formatting (`180,000 RWF`, `18m RWF`, `83.3%`).
- The daily expense total (BR-15) and all device-held citizen data (Q-02).
- Loading, empty and error states (Q-27).

## 9. Change log

| Version | Date | Changes |
|---|---|---|
| 0.1 | 2026-10-24 | First proposal, drafted from the Figma design. |
| 0.2 rev 2 | 2026-10-24 | Pre-sign-off corrections; v0.2 has not yet been agreed, so the version number is kept. Changes: `/health` is the platform health check; `/ready` gains a `checks` object and an explicit pre-seed rule (§2). Malformed-JSON body fixed exactly (§1.3). Validation runs before lookup. The 404 `district-not-found` rule is narrowed to the `district` and `districtCode` parameters; `geography` is always 422. Query-integer pattern `^[0-9]+$` and body booleans rejected (§1.2). Every numeric field is a JSON number (§1). `/dashboard/filters` periods use `code` instead of `id`. The `period` and `householdGroup` rules are spelled out for both vulnerability endpoints. |
| 0.2 | 2026-10-24 | Q-01, Q-02, Q-04 and Q-15 resolved; the Option B and auth variants removed. `meta` added to every data response, including `/dashboard/filters` and `/methodology`. Error format reconciled: `unknown_field` added; unknown district → 404 (narrowed in rev 2 to the `district` and `districtCode` parameters); unknown filter or enum value → 422 `unknown_value`; `benchmark-not-available` and `not-ready` added. Number parsing rules added (§1.2). Household-shock gains `savingsExhausted`, and `runwayMonths` is 1 dp or `null`. Policy-scenario gains `baselineUsed`; `savingsAfterHorizon` stays BR-07 as written and can be negative. Benchmarks cover household size 4 only. Scores are integers with `band1`–`band4` keys. `/dashboard/filters` offers defaults only; per-district geography is optional and needs a decision. `/methodology` returns structured data only and is optional. `budget-comparison` and `demo-household` added as optional. `/health` and `/ready` added at the root. `X-Request-ID`, CORS and an English-only response language added. |
