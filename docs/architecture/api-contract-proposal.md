# API Contract — Imibereho (contract v0.2 rev 2, with the v0.3 and v0.4 extensions)

> **This is the single authoritative frontend–backend API contract.** If any other document (`backend-requirements.md`, `IMPLEMENTATION_PLAN.md`, the project document) disagrees with it, this file wins and the other document is corrected.
> **Status: v0.2, backend proposal, awaiting frontend sign-off.** Nothing here is implemented yet. Once frontend and backend agree, the status becomes "agreed". After that, changes need a new contract version and a note in §9.
> **Status of v0.3 (§10, official published statistics): agreed.** v0.3 was agreed by the frontend teammate on 27 October 2026. The approval covers contract v0.3 only; it does not cover v0.2 rev 2, whose status above is unchanged.
> **Status of v0.4 (§11, from `MISSING_APIS.pdf`): implemented by the backend at the project owner's direction (2026-10-27); frontend sign-off pending.**
> **Status of v0.5 (§11.8, household accounts: register and login): implemented by the backend at the project owner's direction (2026-10-28); frontend sign-off pending.** It changes **Q-02 for one table**: citizen accounts (Option C) in `household_accounts`. **Q-04** (decision-maker login) is **unchanged**. Q-13 (retention, deletion, consent) and Q-34 (the design copy "does not collect or save your details") are open; see §11.8.
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
| Contract (this document) | `0.2` (rev 2, §1–§8; not yet agreed) and `0.3` (§10; agreed 2026-10-27) | Any change to a field, an endpoint or the error behaviour. Mirrored in OpenAPI `info.version` = `0.2.0`; the build still reports `0.2.0` after v0.3 was agreed (open item in §10) |
| Methodology | `"0.1"` | Calculation rules or seeded data change. Returned in `meta.methodologyVersion` ([E] "CONCEPT METHOD · v0.1", `2:7333`) |

## 1. Conventions

| Topic | Rule |
|---|---|
| Base URL | `/api/v1`. The health checks `/health` and `/ready` are at the root, outside `/api/v1`. |
| Format | JSON, UTF-8. Field names are `camelCase`. |
| Auth | `POST /auth/register` and `POST /auth/login` issue bearer tokens (v0.5, §11.8): citizen accounts, a Q-02 change made at the project owner's direction on 2026-10-28; Q-04 (decision-maker login) is unchanged. A current-account dependency verifies tokens for future protected routes, but no served endpoint requires a token; every endpoint stays public. |
| Citizen data | Never stored (Q-02 resolved, Option A), with one exception since v0.5: `POST /auth/register` stores a household account (§11.8). Request bodies are processed and then discarded, never logged. Money values travel only in POST bodies, never in query strings, because hosting-platform access logs record full URLs. |
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
| 401 | `invalid-credentials` | `POST /auth/login` only: unknown identifier or wrong password (one answer for both); carries `WWW-Authenticate: Bearer` (§11.8) | — |
| 401 | `not-authenticated` | A protected route only (none is served yet): a missing, malformed, wrongly signed or expired bearer token, or one whose account no longer exists (one answer for all); carries `WWW-Authenticate: Bearer` (§11.8) | — |
| 409 | `identifier-taken` | `POST /auth/register` only: an account already uses this identifier (§11.8) | — |
| 422 | `validation` | Field-level failures | `required`, `out_of_range`, `not_integer`, `unknown_value` (a bad enum or filter value), `too_long`, `unknown_field` (an extra body field); for the account endpoints only (§11.8), also `too_short` and `invalid_format` |
| 429 | `rate-limited` | Too many calculation requests; includes a `Retry-After` header. **Optional step**; may not ship | — |
| 500 | `internal` | Unexpected error. No internal detail is returned; quote `X-Request-ID` when reporting | — |
| 503 | `not-ready` | Only from `/ready`; carries a `checks` member (§2) | — |
| 503 | `auth-not-configured` | `POST /auth/register` and `POST /auth/login` only: the server has no `JWT_SECRET_KEY` (§11.8) | — |

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
| 0.3 | 2026-10-27 | **Agreed** by the frontend teammate on 27 October 2026. The approval covers v0.3 only; v0.2 rev 2 is not covered and still awaits sign-off. Adds §10: the official published statistics endpoints `GET /api/v1/nisr/sources`, `/nisr/financial-inclusion/national`, `/nisr/financial-inclusion/districts`, `/nisr/poverty` and `/nisr/health-insurance`, with the official-statistics `meta` (`isIllustrative: false`, `dataKind`, `sourceIds`); `printedDecimals` for display rounding; NISR attribution for EICV7 and AFR attribution for FinScope; EICV7 and FinScope kept as separate datasets in charts and filters. |
| 0.4 | 2026-10-27 | **Implemented by the backend at the project owner's direction; frontend sign-off pending.** Adds §11 from `MISSING_APIS.pdf`: `GET /api/v1/shocks/catalog` and `POST /api/v1/calculations/resilience-simulation` (§11.1); `POST /api/v1/calculations/agro-savings-projection` (§11.2); new 404 slug `swap-not-found`; `POST /api/v1/calculations/stress-test`, `GET /api/v1/calculations/district-comparison` (snake_case query parameters, as in the PDF) and `GET /api/v1/districts/{code}/basket-details` (§11.3); twelve account and tracker endpoints recorded as blocked by Q-02/Q-04 (§11.4); `nutrition/indyo-yuzuye`, `agro/harvest-calendar` and `market/shopping-checklist` served as `awaiting_validated_data` (§11.5); reconciliation of all 21 PDF endpoints (§11.6). Later on 2026-10-27, with the project owner's approval: BR-24 household-size scaling for `district-comparison` and `stress-test`; the PDF's `runwayMonths` (buffer ÷ raw gap); `agro/harvest-calendar` served from NISR SAS 2025 (new source `sas-2025`). Then, with the project owner's approval of the PDF's example values as illustrative data: §11.7 and `meta.provenance`; Gasabo and Musanze example baskets; Gasabo staple prices and market hub; purchasing-power equivalents (BR-25); the balanced plate; the Gasabo size-4 checklist; `harvest_disruption` in the shock catalogue; the score and buffer-impact deviations documented with their evidence. Then `status` added to `basket-details`, and the open decisions for #13 and #21 listed (§11.7). Then BR-24 scaling of the Gasabo checklist to sizes 1–20 with `valueBasis`, and the district price evidence recorded (§11.5, §11.7). |
| 0.5 | 2026-10-28 | **Implemented by the backend at the project owner's direction; frontend sign-off pending.** Adds §11.8: `POST /api/v1/auth/register` (201) and `POST /api/v1/auth/login` (200), with the PDF's fields exactly; the `household_accounts` table (migration 0009), Argon2id password hashes and HS256 bearer tokens valid for 86,400 s; new problem types `invalid-credentials` (401), `identifier-taken` (409) and `auth-not-configured` (503); new 422 codes `too_short` and `invalid_format` for these two endpoints. A Q-02 change for that table only (citizen accounts, Option C); Q-04 unchanged (§1, §11.4). |
| 0.5 rev 1 | 2026-10-28 | Security review fixes, frontend sign-off still pending. Identifiers are ASCII only: lookalikes (non-ASCII digits, invisible or fullwidth characters) are rejected, not normalised. A current-account dependency for future protected routes (new 401 `not-authenticated`; HS256 only; `sub`, `iat`, `exp` required; the account must exist); CORS allows `Authorization`. The Q-02/Q-04 wording is corrected and the open privacy decisions are listed (Q-13, Q-34). No endpoint added or changed in shape. |

## 10. Official published statistics (contract v0.3)

**Status: agreed.** Contract v0.3 was agreed by the frontend teammate on 27 October 2026. The approval covers contract v0.3 only; it does not cover v0.2 rev 2 (§1–§8 remain a proposal awaiting sign-off).

**Approved scope.** The five endpoints proposed for v0.3 in `backend/README.md`, with the field-level specification in [`backend/docs/api/nisr-financial-inclusion.md`](../../backend/docs/api/nisr-financial-inclusion.md), which is part of this contract for these endpoints:

| Endpoint | Source | Publisher to credit |
|---|---|---|
| `GET /api/v1/nisr/sources` | both sources, each with full provenance | per item (`publisher`) |
| `GET /api/v1/nisr/financial-inclusion/national` | FinScope Rwanda 2024 | Access to Finance Rwanda (AFR) |
| `GET /api/v1/nisr/financial-inclusion/districts` | FinScope Rwanda 2024 | Access to Finance Rwanda (AFR) |
| `GET /api/v1/nisr/poverty` | EICV7 2023/24, Table A9.23 | National Institute of Statistics of Rwanda (NISR) |
| `GET /api/v1/nisr/health-insurance` | EICV7 2023/24, Table A3.7 | National Institute of Statistics of Rwanda (NISR) |

The approval explicitly includes:
- **`printedDecimals`** (EICV7 `indicator.printedDecimals`, currently 2): values carry full source precision, and the frontend rounds to this many decimals for display.
- **Attribution:** EICV7 figures are credited to NISR; FinScope figures are credited to AFR (NISR is FinScope's sponsor and distributor, not its publisher).
- **Separation:** EICV7 and FinScope are separate datasets. They are not combined in one chart series or filter; each keeps its own source label.

The endpoints follow §1 conventions (`/api/v1` prefix, problem+json errors, `X-Request-ID`), except that their `meta` is the official-statistics envelope (`isIllustrative: false`, `dataKind: "official_published_statistics"`, `sourceIds`, `count`) instead of §1.1's illustrative one.

**Not covered by this approval (open):**
- Contract v0.2 rev 2 (§1–§8) still awaits frontend sign-off.
- §0 says the contract version is mirrored in OpenAPI `info.version`; the build still reports `0.2.0`. Whether it should report `0.3.0` while v0.2 rev 2 is unagreed is undecided.
- The FinScope endpoints sit under the `/nisr/` path although AFR is FinScope's publisher; the response's `source.publisher` is authoritative for attribution.

## 11. Contract v0.4: endpoints from `MISSING_APIS.pdf` (frontend sign-off pending)

**Status.** Implemented by the backend at the project owner's direction on 2026-10-27, following the project owner's specification `MISSING_APIS.pdf` (26 October 2026). The frontend has not signed it off. Conventions are those of §1. The response envelope adds `meta` (`isIllustrative: true`, `methodologyVersion`) to the PDF's shapes. All values are illustrative calculations, not observations, except the harvest calendar (official NISR data, §11.5). Where a response serves `MISSING_APIS.pdf` example values (§11.7), its `meta` also carries `provenance: "MISSING_APIS.pdf example, owner-approved"` (`null` when it serves none). The request bodies are processed and discarded (Q-02). There is no login (Q-04).

Where the PDF's example and the implementation differ, the PDF's field names are kept and the smallest correction is listed under each endpoint.

### 11.1 Resilience simulator

**`GET /api/v1/shocks/catalog`.** No query parameters (any parameter gives 400 `unknown-parameter`).
- **Response:** `{items, copingLevers, meta}`.
  - **`items`** has the PDF's three example shocks, `income_drop` (`defaultPct` 20, `defaultDuration` 3), `medical_emergency` (`defaultAmount` 45,000) and `school_fees` (`defaultAmount` 60,000), plus `harvest_disruption` ("Harvest disruption"), which the PDF's description names without values. Each item carries `id`, `title`, `isLumpSum`, `defaultPct`, `defaultDuration` and `defaultAmount`, with `null` where a field doesn't apply.
  - **`harvest_disruption`** (owner-approved on 2026-10-27) is an income shock with all defaults `null`: the PDF gives none, so the caller supplies `incomeReductionPct` and `durationMonths`. Treating a lost harvest as lost income is a stated modelling assumption (`harvest_disruption_modelled_as_a_loss_of_income` in the simulation's `assumptions`), not a fact about harvests.
  - **`copingLevers`** is an addition to the PDF: `{id, title, kind: monthly_relief | one_off_support, amount}`. The levers are `trim_non_essentials` (12,000 per month), `seasonal_agro_swaps` (5,200 per month) and `ibimina_tontine` (25,000 once).
  - **`meta`** includes `count` and `provenance`.
- **Provenance:** the values come from the PDF's examples (page 9). `seasonal_agro_swaps` equals the §11.2 projection for the seeded swap at 3 meals a week; `trim_non_essentials` is 17,200 − 5,200. They live in `backend/app/core/resilience_catalog.py`.

**`POST /api/v1/calculations/resilience-simulation`.**
- **Request:** `{baseline{monthlyIncome, monthlyEssentials, savings}, shock{type, incomeReductionPct?, durationMonths, amount?}, activeCopingLevers[]}`.
  - `incomeReductionPct` is required for the income shocks (`income_drop`, `harvest_disruption`) and rejected for lump-sum shocks.
  - `amount` (lump-sum shocks only) defaults to the catalogue value.
  - `durationMonths` is required for every shock.
  - Each lever may appear once.
  - Lever amounts, totals and scores are never accepted from the client (extra field: `unknown_field`).
- **Response:** the PDF's `rawMonthlyGap`, `copingReliefMonthly`, `lumpSumSupport`, `netMonthlyGap`, `totalEffectiveBuffer`, `runwayMonths`, `resilienceScore` and `scoreChange`. Additions: `shockCostMonthly`, `savingsUsed`, `savingsRemaining`, `savingsExhausted` (BR-04/05 over the duration), `assumptions` and `meta`.
- **Formulas:** BR-02/03/04/06 and BR-17 to BR-19 (backend-requirements §2); `runwayMonths` per BR-18.
- **Corrections to the PDF example:**
  1. `runwayMonths` follows the PDF: `totalEffectiveBuffer ÷ rawMonthlyGap` (85,000 ÷ 6,000 = 14.2 for the example), `null` only when there is no raw gap (approved by the project owner on 2026-10-27). It therefore differs from `household-shock`, whose runway is savings ÷ gap.
  2. **Score (selected behaviour: BR-19).** The PDF states no score formula. BR-19 is the frontend simulator's own heuristic (`ResilienceSimulatorPage.tsx`: `clamp(70 − round(gap ÷ 2,000), 45, 75)`, then `+7` per lever and `+8` when the gap is closed), with one fix: the +8 needs a gap that levers closed. For the PDF's request it gives baseline 67, `min(95, 67 + 21 + 8)` = **95** and `scoreChange` **28**, the same values the frontend computes today. The PDF's 88 and "+26" would need a baseline of 62; neither the PDF nor the frontend has a formula that produces it, so the PDF's figures are not served. `assumptions` says so (`resilience_score_is_br_19_the_pdf_example_figures_are_not_derivable`).
  3. `scoreChange` is an integer, not the string "+26" (§1; the project owner chose the integer on 2026-10-27).
- **Errors:** 400 `malformed-request` or `unknown-parameter`; 405; 422 `validation` (`required`, `out_of_range`, `not_integer`, `unknown_value` for an unknown shock type or an unknown or duplicate lever, `unknown_field`).
- **Unchanged:** `POST /calculations/household-shock`, with its `income_fall` type.

### 11.2 Agro-savings projection

**`POST /api/v1/calculations/agro-savings-projection`.**
- **Request:** `{swapId, mealsPerWeek, householdSize}`, all required.
  - `swapId`: 1–64 characters.
  - `mealsPerWeek`: integer 1–21.
  - `householdSize`: integer 1–20.
- **Response:** the PDF's `swapId`, `perMealSavings` (BR-14 on the seeded swap's prices), `monthlyProjectedSavings` (BR-20) and `purchasingPowerEquivalents` (BR-25). Additions: `purchasingPowerStatus`, `assumptions` and `meta` (with `provenance`).
- **Decisions, documented in `assumptions`:**
  - **Rounding:** the month is the exact 52/12 weeks, rounded half up to whole RWF. That gives the PDF's 5,200; the frontend's 4.33 approximation gives 5,196.
  - **Household size:** validated but not used to scale. The swap is priced per household meal, and there is no sourced scaling rule.
  - **Months:** a swap resolves by `swapId` whatever its seeded month.
  - **Purchasing power (BR-25, owner-approved on 2026-10-27):** `purchasingPowerEquivalents` lists the PDF's three items with `purchasingPowerStatus: "available"`. Each count is `⌊monthlyProjectedSavings ÷ unit cost⌋`, with the unit costs implied by the PDF's example (5,200 ÷ its counts): **2,600 RWF a week of water**, **650 a bus ride**, **200 an egg**. The example therefore gives exactly 2 weeks, 8 rides and 26 eggs. These are not market prices (`assumptions` says so). Each item sets only its PDF key (`coversWeeks`, `ridesCount` or `quantity`); the other two are `null`. A projection of 0 or less buys 0 of each.
- **Prices:** the seeded swap's prices are invented in the design ("not market observations").
- **Errors:** 400 `malformed-request` or `unknown-parameter`; 404 `swap-not-found` (a new slug; validation runs first, so an invalid request with an unknown swap gives 422); 405; 422 `validation`.

### 11.3 District Budget Advisor

All three endpoints are illustrative. **Gasabo and Musanze** use the PDF's example baskets (page 7, owner-approved on 2026-10-27; §11.7): Gasabo 65,000 / 40,000 / 20,000 / 10,000 / 15,000 = 150,000 (equal to the seeded benchmark) and Musanze 50,000 / 28,000 / 14,000 / 9,000 / 14,000 = 115,000. **Every other district** uses the one seeded benchmark basket, the same for every district at household size 4 ([PD] Q-32), because the PDF gives no other district. `assumptions` names which applies (`gasabo_and_musanze_baskets_are_missing_apis_pdf_examples`, `benchmark_is_one_illustrative_basket_for_every_district`), `meta.provenance` is set when an example basket is used, and nothing is presented as observed district data. `/budget-benchmarks` keeps the seeded benchmark for every district, so for Musanze it still shows 150,000 (a known difference, §11.7). `district-comparison` and `stress-test` accept any `householdSize` 1–20 and scale the size-4 basket line by line with the square-root equivalence scale (BR-24, approved by the project owner on 2026-10-27). `basket-details` has no size parameter and stays at size 4; `/budget-benchmarks` is unchanged (size 4 only).

**`POST /api/v1/calculations/stress-test`.**
- **Request:** `{district, householdSize (1–20), scenario}`. `scenario` is `food_inflation_15` (food +15%) or `rent_surge_10` (housing +10%), from the PDF's page 8 text.
- **Response:** the PDF's `baselineTotal`, `stressedTotal`, `monthlyIncrease` (BR-21) and `bufferImpactMonths` (BR-22), plus `assumptions` and `meta`.
- **`bufferImpactMonths` (selected behaviour: BR-22).** The PDF states no formula, and its request has no savings, income or buffer. BR-22, `−(12 × monthlyIncrease ÷ baselineTotal)` (a year of the increase in months of the baseline basket), gives **−0.8** for the example (12 × 9,750 ÷ 150,000 = 0.78). Evidence that the PDF's −1.2 is not derivable: with only the basket in the request, −1.2 would need 12 × 9,750 ÷ 97,500 or 18 × 9,750 ÷ 150,000, neither of which matches any quantity the PDF defines, and the frontend has no stress-test buffer formula. The PDF's other three figures (150,000, 159,750 and 9,750) are reproduced exactly. `assumptions` says so (`buffer_impact_is_br_22_the_pdf_example_figure_is_not_derivable`).
- **Errors:** 400; 404 `district-not-found` or `benchmark-not-available` (after validation); 405; 422 (`unknown_value` for an unknown scenario).

**`GET /api/v1/calculations/district-comparison?district_a=&district_b=&household_size=`.**
- **Query:** the PDF's snake_case names are kept, an exception to §1's camelCase rule. Any other parameter, including `districtA`, gives 400 `unknown-parameter`.
- **Response:** the PDF's `districtA`/`districtB` `{code, name, total, breakdown{food, housing, transport, utilities, other}}` (`other` is the `other_essentials` category), `variance{netDifference, percentageDifference, categoryDifferences}` and `costOfLivingMultiplier` (BR-23), plus `assumptions` and `meta`.
- **The PDF example is reproduced exactly:** Gasabo vs Musanze at size 4 gives 150,000 vs 115,000, `netDifference` −35,000, `percentageDifference` −23.3 and `costOfLivingMultiplier` 0.767.
- **One addition:** `categoryDifferences` lists all five categories (`utilities` −1,000 and `other` −1,000 in the example); the PDF's example lists three.
- Two districts without a PDF basket show no difference (0 and 1.0).
- **Errors:** 400; 404 `district-not-found` or `benchmark-not-available`; 405; 422.

**`GET /api/v1/districts/{code}/basket-details`.** No query parameters.
- **Response:**
  - `status` (an addition): `"available"` when every field has a value (Gasabo only); `"awaiting_validated_data"` when any field in `unavailableFields` is `null`. Unavailable numbers are `null`, never 0.
  - `districtCode`, plus `householdSize` (always 4).
  - `referenceRentIndex` and `referenceTransitPass`: the district basket's housing and transport lines (Gasabo 40,000 and 20,000, the PDF's example values; Musanze 28,000 and 14,000 from its example basket; elsewhere the benchmark's 40,000 and 20,000).
  - `staplePriceIndex{irishPotatoesPerKg, sweetPotatoesPerKg, redBeansPerKg}` and `primaryMarketHub`: the PDF's example for **Gasabo only** (750, 800, 850 RWF per kg; "Kimironko Market"). Every other district gets **`null`**, because the PDF gives no other values; `unavailableFields` lists the null fields (`[]` for Gasabo).
  - `assumptions` and `meta`.
- **Errors:** 400; 404 `district-not-found`; 405.

### 11.4 Blocked by Q-02 and Q-04 (not served)

These ten PDF endpoints need server-side storage of a household's own data beyond its account, and ownership checks on top of the current-account dependency (§11.8). Q-02 (citizen data is never stored, except the account table of §11.8) still applies to them, so the routes aren't registered and an unknown path gives 404 `not-found`. Under Q-02 the tracker, profile and plan data stay on the device. A test (`test_privacy_blocked_pdf_endpoints_are_not_served`) keeps the routes out.

| Endpoint | Needs |
|---|---|
| `GET /api/v1/user/profile`, `PUT /api/v1/user/profile` | a stored household profile tied to an account (Q-02, Q-04) |
| `GET /api/v1/tracker/overview`, `GET /api/v1/tracker/daily-trend`, `GET /api/v1/tracker/burn-rate` | aggregates of stored transactions (Q-02) |
| `GET /api/v1/tracker/transactions`, `POST /api/v1/tracker/transactions`, `PUT /api/v1/tracker/transactions/{id}`, `DELETE /api/v1/tracker/transactions/{id}` | stored transactions (Q-02) |
| `POST /api/v1/user/resilience-plan` | a stored plan (Q-02) |

Register and login moved out of this list in v0.5 (§11.8), which supplies the accounts and tokens. Serving the others needs the project owner to reopen Q-02 for their data, plus a privacy policy, consent (Q-13), the current-account dependency of §11.8 on each request, and ownership checks.

### 11.5 Content endpoints

Each answers 200 with a `status`: `"available"` with content, or `"awaiting_validated_data"` with the PDF's fields present but empty (`[]`) or `null`. Both carry `assumptions` and `meta`. Nothing is filled in beyond the sources named below.

- **`GET /api/v1/nutrition/indyo-yuzuye`** (no query parameters) serves the **PDF's example** (page 10, owner-approved on 2026-10-27, §11.7): `standard` "Indyo Yuzuye"; `plateComponents` energy 50% (Sweet potatoes, Cassava), protective 25% (Dodo amaranth, Isombe) and protein 25% (Red beans, Groundnuts); and the `energyTip` "Boiling sweet potatoes alongside beans saves 35% charcoal fuel." It is illustrative (`meta.isIllustrative: true`, `provenance` set). It is **not** presented as MINAGRI or MINISANTE guidance, and the 35% figure is not verified; `assumptions` says both. No official national adult dietary guideline was found to cite.
- **`GET /api/v1/agro/harvest-calendar`** (no query parameters) is **official data, not a placeholder** (since 2026-10-27; source `sas-2025`, NISR Seasonal Agricultural Survey 2025, listed by `/nisr/sources`):
  - Fields: `activeSeason` (`A`/`B`/`C`, from the current month in Kigali), `seasonName` (`Season A`), `monthsRange` (`September – February`, `March – June`, `July – September`, NISR's definitions), and `harvestHighlights` (the active season's three largest seasonal crops by 2025 production, e.g. "Sweet potato: 656,320 tonnes produced in Season A 2025 (NISR SAS 2025)").
  - Additions: `month`, `seasons` (all three definitions), `source`, `assumptions`; `meta` is the official-statistics envelope (`isIllustrative: false`).
  - September belongs to both Season A (which starts) and Season C (which ends); it is reported as A, like the PDF. Kinyarwanda season names are omitted because sources disagree (the PDF's "Season A (Umuhindo)" becomes "Season A"). Without the source row, `status` is `awaiting_validated_data`.
- **`GET /api/v1/market/shopping-checklist?district=&household_size=`** (the PDF's snake_case names). The district is validated (404 `district-not-found`) and `household_size` must be 1–20 (422).
  - **Gasabo, household size 4** serves the **PDF's example** (page 11, owner-approved on 2026-10-27): three items (Fresh Sweet Potatoes 3 kg 2,400; Local Red Kidney Beans 2 kg 1,700; Fresh Amaranth Greens (Dodo) 3 bundles 650), `totalEstimatedBasket` 6,250, `unoptimizedBasket` 8,650 and `estimatedSavings` 2,400, with `provenance` set.
  - **The PDF's totals are served as given.** Its three items sum to 4,750, not 6,250, and the PDF does not say what else the basket holds, so the totals are not derived from the items; `assumptions` says so (`totals_are_the_pdf_figures_not_the_sum_of_the_listed_items`). `estimatedSavings` = `unoptimizedBasket − totalEstimatedBasket` holds.
  - **Gasabo, any other household size** (approved by the project owner on 2026-10-27) serves the size-4 example scaled by BR-24, factor √(`household_size` ÷ 4), with `valueBasis: "modelled_from_pdf_example"`. Each `estPrice` and the `totalEstimatedBasket` and `unoptimizedBasket` are the PDF figures × factor, rounded half up to whole RWF; `estimatedSavings` = scaled `unoptimizedBasket` − scaled `totalEstimatedBasket`; each quantity is the PDF amount × factor, rounded half up to 0.1 in the same unit ("3 kg" at size 5 is "3.4 kg"; ".0" is dropped). Prices are scaled from the PDF price, not recomputed from the rounded quantity. Supported sizes are the validated 1–20. The scaled total keeps the PDF's unexplained gap (at size 4, 6,250 against items summing to 4,750); no item is added. `assumptions` names the model and the rounding; these are model outputs, not market observations.
  - **`valueBasis`** (an addition): `"pdf_example"` at size 4, `"modelled_from_pdf_example"` at other sizes, `null` when awaiting data.
  - **Every other district** answers `awaiting_validated_data` with `items` `[]`, null totals and `valueBasis` `null`: the PDF gives no other checklist and no checked source publishes one (`docs/architecture/district-price-evidence.md`).

When a cited source is added, `status` becomes `"available"` and the fields fill in without any shape change.

### 11.6 Reconciliation with `MISSING_APIS.pdf` (21 endpoints)

| # | Endpoint | Outcome |
|---|---|---|
| 1–2 | `POST /auth/register`, `POST /auth/login` | Complete (v0.5, §11.8): the PDF's request and response fields exactly; validation rules, errors and token claims set by the backend because the PDF gives none |
| 3–4 | `GET`/`PUT /user/profile` | Blocked: Q-02/Q-04 (§11.4) |
| 5–11 | `/tracker/*` (overview, transactions ×4, daily-trend, burn-rate) | Blocked: Q-02 (§11.4) |
| 12 | `GET /calculations/district-comparison` | Complete (illustrative): the PDF example exactly (Gasabo vs Musanze, §11.7); any household size (BR-24); districts without a PDF basket use the shared benchmark |
| 13 | `GET /districts/{code}/basket-details` | Partial: the PDF example exactly for Gasabo; other districts have rent and transit but `null` staple prices and market hub (the PDF gives none) |
| 14 | `POST /calculations/stress-test` | Complete with one documented deviation: totals as in the PDF; `bufferImpactMonths` is BR-22 (−0.8), not the PDF's −1.2, which no stated formula produces (§11.3) |
| 15 | `GET /shocks/catalog` | Complete (illustrative): the PDF's three example shocks, plus `harvest_disruption` with `null` defaults (the PDF gives none, §11.1) |
| 16 | `POST /calculations/resilience-simulation` | Complete with one documented deviation: the PDF's gaps, buffer and runway (14.2) exactly; score is BR-19 (95 / +28, integer), not the PDF's 88 / "+26", which no stated formula produces (§11.1) |
| 17 | `POST /user/resilience-plan` | Blocked: Q-02 (§11.4) |
| 18 | `POST /calculations/agro-savings-projection` | Complete (illustrative): the PDF example exactly, including 2 weeks / 8 rides / 26 eggs (BR-25, §11.2) |
| 19 | `GET /nutrition/indyo-yuzuye` | Complete (illustrative): the PDF example, not presented as official guidance (§11.5) |
| 20 | `GET /agro/harvest-calendar` | Complete with official NISR SAS 2025 data (§11.5); Kinyarwanda season name omitted |
| 21 | `GET /market/shopping-checklist` | Partial: the PDF example for Gasabo at size 4 (totals as given) and BR-24-modelled for Gasabo at sizes 1–20; other districts `awaiting_validated_data` (§11.5) |

### 11.7 Owner-approved PDF example values (illustrative)

On 2026-10-27 the project owner approved serving the example values in `MISSING_APIS.pdf` as illustrative data for frontend integration, labelled `meta.isIllustrative: true` and `meta.provenance: "MISSING_APIS.pdf example, owner-approved"`. They live in `backend/app/core/pdf_examples.py` (with `backend/app/core/resilience_catalog.py` for the shocks and levers), copied exactly from the PDF and pinned by tests. They are not observations, market prices or official guidance.

| Values (PDF page) | Served by | Scope |
|---|---|---|
| Gasabo and Musanze baskets (p. 7) | `district-comparison`, `stress-test`, `basket-details` (rent and transit) | those two districts; others use the shared benchmark |
| Gasabo staple prices and "Kimironko Market" (p. 7) | `basket-details` | Gasabo only; others `null` |
| Shock defaults and lever amounts (p. 9) | `shocks/catalog`, `resilience-simulation` | as listed in §11.1 |
| Purchasing-power items, as unit costs implied by the example (p. 10) | `agro-savings-projection` | every swap and frequency (BR-25) |
| Balanced plate and energy tip (p. 10) | `nutrition/indyo-yuzuye` | always |
| Checklist items and totals (p. 11) | `market/shopping-checklist` | Gasabo; size 4 as given, other sizes modelled by BR-24 (`valueBasis`) |

**Not extended.** Nothing is invented for districts or items the PDF does not show: those fields stay `null` or `[]`, or the response says `awaiting_validated_data`. The one extension is the owner-approved BR-24 scaling of the Gasabo checklist to other household sizes, labelled `modelled_from_pdf_example`.

**Inconsistencies in the PDF, and what is served:**
- `stress-test` `bufferImpactMonths` −1.2 and `resilience-simulation` score 88 / "+26": no stated formula produces them; BR-22 and BR-19 are served, with the evidence in §11.3 and §11.1.
- Checklist: the items sum to 4,750 but the total is 6,250; the totals are served as given.
- `harvestHighlights` in the PDF ("Plentiful sweet potatoes & cassava"…) are not served, because the harvest calendar is official NISR data (§11.5) and is not mixed with example text.
- `/budget-benchmarks` (contract §4) is unchanged and still returns the shared benchmark for Musanze (150,000), while the v0.4 advisor uses the PDF's 115,000.

**Open decisions (owner or data needed).** These keep #13 and #21 partial; the responses say `awaiting_validated_data` until one is closed. The sources checked for them (WFP market prices on HDX, NISR CPI, MINAGRI e-Soko) and the candidate values found are recorded in `docs/architecture/district-price-evidence.md`; none is served.
1. **#13 staple prices and market hub for the 29 districts other than Gasabo.** Needs, per district: price per kg of Irish potatoes, sweet potatoes and red beans, and a named market, either from a citable source (publisher, title, date, URL or file hash, geography) or as values the owner supplies and approves as illustrative. The WFP data has current Irish-potato and dry-bean prices for five districts only, no sweet-potato price since 2015 and no primary-market attribute (evidence §3 and §5).
2. **#21 checklist for districts other than Gasabo.** Needs, per district: item names, quantities and prices, `totalEstimatedBasket`, `unoptimizedBasket` and `estimatedSavings`, from the same kinds of source, plus a definition of `unoptimizedBasket` (the PDF does not define it).
3. ~~**#21 household sizes other than 4.**~~ Closed on 2026-10-27: the owner approved BR-24 scaling of the Gasabo example (§11.5).
4. **#21 the 4,750 vs 6,250 discrepancy.** Needs the owner to say whether the example list is partial (and give the missing items) or which figure is wrong. Until then the total is served as 6,250 (scaled at other sizes) and no item is invented.

### 11.8 Household accounts: register and login (contract v0.5)

**Status.** Implemented on 2026-10-28 at the project owner's direction ("implement auth API endpoints ... follow the request and response as shown on MISSING_APIS.pdf"); frontend sign-off pending. This is a **Q-02 change for the `household_accounts` table only**: citizen accounts, Q-02's Option C, where Q-02 otherwise stays Option A (profile, plan and expenses remain on the device). It is an implemented technical change, **not** a privacy-policy approval. **Q-04** (decision-maker login) is a different question and is **unchanged**. Every other endpoint is unchanged: public, and storing nothing. The profile and tracker endpoints stay unserved (§11.4).

**What the PDF fixes and what the backend chose.** The PDF (page 4) gives the paths, the request and response fields, `201` for register, "Argon2/bcrypt", a JWT and `expiresIn: 86400`. It gives no validation rules, error responses, token claims or id format; those below are the backend's choices, made with the usual conventions of §1.

**`POST /api/v1/auth/register`** → `201`
- Request (the PDF's fields; camelCase; unknown fields → 422 `unknown_field`; no query parameters):
  - `identifier`: a Rwandan mobile number in E.164 form, `+2507` and 8 digits (`+250788123456`), or an email address in ASCII (a local part of printable ASCII other than space and `@`, one `@`, and a domain of ASCII letters, digits and hyphens with at least one dot; at most 254 characters). Only ASCII whitespace is trimmed from the ends, and an email is lower-cased; the stored and returned identifier is that normalised form. **Non-ASCII characters are rejected, never transformed:** Arabic-Indic or fullwidth digits, fullwidth or Cyrillic letters, zero-width and no-break spaces all give 422 `invalid_format`, so one identifier can never be registered twice in another form, and such a string at login is answered like an unknown identifier. Anything else that does not match → 422 `invalid_format`; over 254 characters → `too_long`.
  - `password`: 8–128 characters (`too_short`, `too_long`). Stored only as an Argon2id hash; never logged, stored or returned, and never echoed in an error.
  - `profile.district`: a district code (case-sensitive, §5) → else 404 `district-not-found`, after validation. `profile.householdSize`: integer 1–20. `profile.monthlyIncome`: integer RWF 0–100,000,000. `profile.currency`: `"RWF"` only. `profile.preferredLanguage`: `"EN"` or `"RW"`, the frontend's two languages.
- Response: `{"token", "tokenType": "bearer", "expiresIn": 86400, "user": {"id", "identifier", "district", "householdSize"}}`, as in the PDF.
- An identifier that already has an account → 409 `identifier-taken` (an email in another case is the same identifier). This tells a caller that an account exists for that identifier; the PDF's flow needs it, and it is recorded here as a known trade-off.

**`POST /api/v1/auth/login`** → `200`
- Request: `{"identifier", "password"}`, at most 254 and 128 characters; the identifier is normalised as above.
- Response: `{"token", "tokenType": "bearer", "user": {"id", "district"}}`, exactly the PDF's (no `expiresIn`; the token still expires after 86,400 s).
- Unknown identifier, malformed identifier or wrong password → the same 401 `invalid-credentials` with `WWW-Authenticate: Bearer`, after the same Argon2 work, so the answer does not reveal which part was wrong.

**Both endpoints.** Validation (400, 422) comes first. Then, if the server has no `JWT_SECRET_KEY` (at least 32 characters, set in the environment or `backend/.env`), 503 `auth-not-configured`, and nothing is stored. Neither endpoint is rate-limited yet (§1.3 lists 429 as optional).

**Tokens.** JWT, HS256 (the PDF example's header), claims `sub` (the account id), `iat` and `exp` = `iat` + 86,400. Account ids are `usr_` + a ULID (26 Crockford base32 characters), the form of the PDF's `usr_01JBCDEFGH`.

**Current-account dependency (for future protected routes; no served endpoint uses it yet).** `app/services/current_account.py` provides `CurrentAccountDep`. It reads `Authorization: Bearer <token>` (scheme case-insensitive), verifies the signature with `JWT_SECRET_KEY` using **HS256 only** (the token header's `alg` is not trusted, so `none` and other algorithms fail), and requires `sub` (an account id), `iat` and `exp` as integers, with `iat` not in the future, `exp` in the future (no leeway) and a lifetime of at most 86,400 s. The subject must be an existing account, so a token stops working when its account is deleted. Every failure (missing header, another scheme, malformed token, wrong signature, expired, missing or ill-typed claim, unknown account) gets the same 401 `not-authenticated` with `WWW-Authenticate: Bearer`; nothing about the token, the secret or the cause is returned or logged. Without `JWT_SECRET_KEY` the answer is 503 `auth-not-configured`. It returns the account's id, identifier, district, household size, monthly income, currency and language, never the password hash. CORS allows the `Authorization` header (§1). The profile endpoints (§11.4) would be the first users.

**Stored (`household_accounts`, migration 0009).** `id`, `identifier`, `password_hash` (Argon2id), `district_code`, `household_size`, `monthly_income`, `currency`, `preferred_language`, `created_at`. No name and nothing finer than a district. Seeding never touches the table. Request bodies are still never logged (§1). Not yet provided, and needed before real households use it: a privacy notice and consent, account deletion, password reset, rate limiting on login, and a retention rule.

**Open decisions (not approved; recorded in `docs/requirements/open-questions.md`):**
- **Q-13 (Product): retention, deletion and consent** for the stored accounts. Open again since this table exists.
- **Q-34 (frontend owner and Product): the design copy** "This prototype does not collect or save your details" and "No registration or phone number required" (`2:6401`, `2:6407`, `2:6409`) now conflicts with registration. The copy is design and frontend content, so the backend has not changed it; the frontend owner and Product decide whether to change the copy, show registration only with a privacy notice, or keep registration out of the citizen UI. Using the app without an account still works, because no served endpoint requires a token.
- **Frontend sign-off** on v0.5.
