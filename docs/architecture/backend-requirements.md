# Backend Requirements — Imibereho (preliminary)

> Derived from the Figma design ([inventory](../figma/design-inventory.md), [product requirements](../development/product-requirements.md)).
> Evidence tags: **[E]** explicit in design · **[I]** inferred · **[U]** unknown (see `Q-xx` in [open-questions.md](../development/open-questions.md)).
> No backend code or database exists in the repo yet (it holds only the Vite + React + TS template in `frontend/`).
> **Resolved 2026-10-24:** Q-01 (demo on synthetic data, production quality), Q-02 (Option A), Q-04 (no decision-maker login), Q-15 (Python 3.12 / FastAPI / PostgreSQL: 18 local, 16 CI and deployment, provisional pending compatibility verification / SQLAlchemy 2.0 / Alembic / Pydantic v2 / uv; local PostgreSQL managed through pgAdmin 4 for development; Render for hosting; Docker deferred to a later containerisation phase). Rows marked **(Option B only)** or "Not built" below are out of scope for v1 and kept only for traceability.
> **Changed 2026-10-28 (implementation at the project owner's direction, not a policy approval):** Q-02 for one table: citizen register/login accounts in `household_accounts` (Option C; contract §11.8). Q-04 (decision-maker login) is unchanged. Q-13 (retention, deletion, consent) and Q-34 (the "does not collect or save your details" copy) are open.
> **Superseded sections:** §4 (tables), §5 (API resources) and §6 (validation) were written before the API contract existed. They are kept for history and each is marked **SUPERSEDED** with a pointer. For endpoints, parameters, fields, status codes and validation, **only [api-contract-proposal.md](../api/api-contract-proposal.md) is authoritative**. For tables, see `IMPLEMENTATION_PLAN.md` §3–§4. §2 (BR-01 to BR-16) remains authoritative for formulas.
> The authoritative API contract is [api-contract-proposal.md](../api/api-contract-proposal.md) (contract v0.2 rev 2). The build sequence is [IMPLEMENTATION_PLAN.md](../development/IMPLEMENTATION_PLAN.md).

## 1. What the design implies the backend actually does

The design does not show a CRUD-heavy app. Most of what it shows falls into three groups:

1. **Reference / curated data**: districts, expense categories, budget benchmarks, seasonal swaps, district vulnerability scores, overview aggregates and methodology content. All of it is labelled synthetic. It is read-only for end users.
2. **Deterministic calculations**: the household balance, shock and runway, the vulnerability index, the policy comparison and the transfer budget. The formulas are printed on screen ([E] D4 `2:7337`).
3. **Possibly, citizen household data** (profile, plan, expenses). The design says **"This prototype does not collect or save your details"** ([E] `2:6407`), so server-side storage of this data is **not** supported by the design (**Q-02**).

### Architecture options for citizen data (Q-02, resolved 2026-10-24: Option A)

| Option | Description | Fits design? |
|---|---|---|
| **A. Client-held (recommended for the demo)** | Household profile, plan and expenses live on the device (e.g. localStorage). The backend is stateless for citizens and only serves reference data and calculations. | Yes. Matches "does not collect or save your details". |
| B. Anonymous server persistence | The backend issues an anonymous household ID or device token and stores the profile, plan and expenses. | Contradicts the privacy copy unless that copy changes. Needs a retention policy (Q-13). |
| C. Account-based | Citizen accounts. | Contradicts "No account. No phone number." |

**Q-02 is resolved as Option A.** The Option B additions marked **(Option B only)** are not built. **Since 2026-10-28, Option C exists for accounts only:** `POST /auth/register` and `POST /auth/login` store citizen accounts (contract §11.8), and the account's profile, tracker transactions and saved resilience plan are stored with it (§11.9–§11.11). This contradicts the design copy quoted above; the conflict is open as Q-34, and retention, deletion and consent as Q-13.

### Where calculations run (decision needed: Q-16)

The arithmetic is simple enough for the frontend. A shared backend implementation is still recommended because (a) the decision-maker views need it server-side anyway, (b) the methodology is versioned ("v0.1"), and (c) one source of truth avoids the citizen and decision-maker screens disagreeing. **[I]**

## 2. Domain rules and formulas

All of these are taken from on-screen text and verified against the demo numbers.

| ID | Rule | Formula | Demo check | Evidence |
|---|---|---|---|---|
| BR-01 | Monthly balance | `balance = income + support − essentials` | 180,000 + 0 − 150,000 = 30,000 | [E] `2:7343`, `2:6430` |
| BR-02 | Shocked income | `shockedIncome = income × (1 − reductionPct/100)` | 180,000 × 0.8 = 144,000 | [E] `2:7349`, `2:6636` |
| BR-03 | Monthly gap | `gap = max(0, essentials − (shockedIncome + support))` | 150,000 − 144,000 = 6,000 | [E] `2:6635`; clamping at 0 [I] (D3 shows "0 RWF" `2:7231`) |
| BR-04 | Savings used over duration | `savingsUsed = min(savings, gap × months)` | 6,000 × 3 = 18,000 | [E] `2:6638`; cap at savings [I] |
| BR-05 | Savings remaining | `savings − savingsUsed` | 60,000 − 18,000 = 42,000 | [E] `2:6639` |
| BR-06 | Runway (months) | `savings ÷ gap`; **undefined when gap = 0** | 60,000 ÷ 6,000 = 10 | [E] `2:6644`; gap=0 handling [U] Q-17; rounding [U] |
| BR-07 | Savings after N months (policy table) | `savings + N × netBalance`, where net balance may be negative | No shock: 60k + 3×30k = 150k · Shock: 60k − 18k = 42k · Support: 60k + 0 = 60k | [E] `2:7276`–`2:7278`, footnote `2:7280` |
| BR-08 | Direct transfer budget | `supportPerMonth × eligibleHouseholds × months` | 6,000 × 1,000 × 3 = 18,000,000 | [E] `2:7228` |
| BR-09 | Vulnerability index | `0.4 × incomeInstability + 0.4 × essentialCostPressure + 0.2 × lowBufferExposure`, inputs 0–100 | 0.4×50 + 0.4×40 + 0.2×50 = 46 | [E] `2:7097`, `2:7355`; rounding [U] |
| BR-10 | Vulnerability band | 0–39 / 40–59 / 60–69 / 70–100 | Gasabo 46 → band 2 | [E] `2:7061`; band labels/names [U] |
| BR-11 | Essentials-to-income ratio | `essentials ÷ income` as a %, 1 dp | 150k ÷ 180k = 83.3% | [E] `2:6801` |
| BR-12 | Share of households in deficit after shock | `count(households with gap > 0) ÷ sample size` | 1,000 ÷ 3,000 = 33.3% | [E] `2:6805`; per-household data needed [I] |
| BR-13 | Budget comparison difference | `plan[cat] − reference[cat]` per category; totals compared | Housing +5,000, Food −5,000 | [E] `2:6571`; insight text rule [U] Q-09 |
| BR-14 | Swap difference | `priceA − priceB` for the demo baskets (quantities differ) | 2,000 − 1,600 = 400 | [E] `2:6712` |
| BR-15 | Daily spending total | `Σ expense.amount where date = day` | 3,500 + 1,000 + 2,000 = 6,500 | [E] `2:6449` |
| BR-16 | Vulnerability weights must sum to 1.0 | Validation | 0.4 + 0.4 + 0.2 | [I] |
| BR-17 | Lump-sum shock spread (contract v0.4) | `shockCostMonthly = round_half_up(amount ÷ durationMonths)`, added to essentials | 45,000 ÷ 3 = 15,000 | MISSING_APIS.pdf p. 9; spreading follows the frontend simulator [I] |
| BR-18 | Net monthly gap after coping levers (v0.4) | `netGap = max(0, rawGap − Σ monthly lever relief)`; `buffer = savings + Σ one-off lever support`; `runwayMonths = round_half_up(buffer ÷ rawGap, 1 dp)`, `null` only when rawGap is 0 (how long the buffer lasts if the levers do not work) | max(0, 6,000 − 17,200) = 0; 60,000 + 25,000 = 85,000; 85,000 ÷ 6,000 = 14.2 | MISSING_APIS.pdf p. 9; runway basis approved by the project owner on 2026-10-27 (it was buffer ÷ net gap) |
| BR-19 | Resilience score, illustrative (v0.4) | `baseline = clamp(70 − round_half_up(rawGap ÷ 2,000), 45, 75)`; `score = min(95, baseline + 7 × levers + (8 if levers close a rawGap > 0))`; `scoreChange = score − baseline` | 6,000 gap, 3 levers, gap closed: 67 → 95 (+28); no gap, no levers: 70 → 70 (0) | Based on the frontend simulator's heuristic [I], except that the +8 needs a closed gap (the frontend also gives it with no gap and no levers); not validated. The PDF states no formula; its example (88, "+26") would need a baseline of 62, which neither the PDF nor the frontend produces, so it is not reproduced (contract §11.1) |
| BR-20 | Agro-savings projection (v0.4) | `monthly = round_half_up(perMealSaving × mealsPerWeek × 52 ÷ 12)`, with `perMealSaving` from BR-14 | 400 × 3 × 52 ÷ 12 = 5,200 | MISSING_APIS.pdf p. 10. 52/12 is the exact mean weeks per month; the frontend's 4.33 gives 5,196 |
| BR-21 | Stress-test increase (v0.4) | `increase = Σ round_half_up(line × pct ÷ 100)` over the scenario's categories; `stressed = baseline + increase` | food 65,000 × 15% = 9,750; 150,000 → 159,750 | MISSING_APIS.pdf p. 8 |
| BR-22 | Buffer impact in months (v0.4) | `−round_half_up(12 × increase ÷ baselineTotal, 1 dp)`: a year of the increase, in months of the baseline basket; `null` if the basket is 0 | −(12 × 9,750 ÷ 150,000) = −0.8 | Defined by the backend [I]: the PDF states no formula, and its −1.2 cannot be derived from its request (no savings, income or buffer); the other three example figures are reproduced (contract §11.3) |
| BR-23 | District comparison (v0.4) | `net = totalB − totalA`; `pct = round_half_up(net ÷ totalA × 100, 1 dp)`; per-category `B − A`; `multiplier = round_half_up(totalB ÷ totalA, 3 dp)`; ratios `null` if totalA is 0 | PDF baskets: −35,000, −23.3, 0.767 | MISSING_APIS.pdf p. 7 |
| BR-24 | Household-size scaling of the district basket (v0.4) | each line `round_half_up(line(4) × √(n ÷ 4))`; the total is the sum of scaled lines | size 5: 65,000 × 1.118034 = 72,672; total 167,705 | OECD square-root equivalence scale, approved by the project owner on 2026-10-27; used by `district-comparison` and `stress-test`; also, approved on 2026-10-27, the Gasabo `shopping-checklist` at sizes other than 4: item prices and the two basket totals scaled the same way, `estimatedSavings` = scaled unoptimized − scaled total, quantities `round_half_up(q × √(n ÷ 4), 0.1)` in the same unit (size 5: 3 kg → 3.4 kg, 2,400 → 2,683; total 6,988), labelled `modelled_from_pdf_example` |
| BR-25 | Purchasing-power equivalents (v0.4) | `count = ⌊max(0, monthlyProjectedSavings) ÷ unitCost⌋` per item; unit costs implied by the PDF example: water 2,600 RWF a week, bus ride 650, egg 200 | 5,200 → 2 weeks, 8 rides, 26 eggs; 1,733 → 0, 2, 8 | MISSING_APIS.pdf p. 10, owner-approved illustrative values (2026-10-27); unit costs are 5,200 ÷ the example counts, not market prices |
| BR-26 | Tracker budget health (v0.7) | `exceeded` if spent > planned; `caution` if spent × daysInMonth > planned × daysElapsed; else `normal`; `null` without a plan | 118,400 by day 26 of 31 against 150,000 → normal (pace 125,806) | Backend rule, contract §11.10: the PDF shows `"normal"` with no formula |
| BR-27 | Tracker burn rate (v0.7) | `average = round_half_up(spent ÷ elapsed)`; `projected = round_half_up(spent × daysInMonth ÷ elapsed)`; `projectedVsPlan = projected − planned` | 118,400 over 26 days → 4,554 a day, 141,169 projected, −8,831 vs 150,000 | Backend rule, contract §11.10: the PDF lists burn-rate with no body |
| BR-28 | District price model (v0.8) | `price(d) = round_half_up(price(Gasabo) × food(d) ÷ food(Gasabo))`, the food lines at household size 4 (Gasabo 65,000); for the checklist, applied before BR-24; quantities unchanged | Musanze (food 50,000): 750 → 577, 800 → 615, 850 → 654; checklist 2,400 → 1,846, 8,650 → 6,654. Benchmark districts (food 65,000) keep Gasabo's prices | Owner decision 2026-10-28 (contract §11.3, §11.5): models `basket-details` staple prices and the `shopping-checklist` for the 29 districts the PDF does not cover. A model, not observed prices; market hubs are not modelled (`null`) |

**Money** is whole RWF integers ([E] no decimals anywhere). **Percentages** shown to users are integers (20%) or 1-dp ratios (83.3%). Rounding modes are **[U] Q-17**.

**Proposed rounding defaults for Q-17 (not decided; see `IMPLEMENTATION_PLAN.md` §6).** The formulas above are unchanged. These defaults only say how a non-whole result is rounded, and none of them alters a design value.
- BR-02 is computed in integer arithmetic, rounding half up to whole RWF: `shockedIncome = (income × (100 − reductionPct) + 50) div 100`. SQL uses the identical expression with BIGINT operands, and tests prove Python and SQL agree.
- BR-06 runway is rounded half up to 1 decimal place.
- BR-11 and BR-12 ratios are rounded half up to 4 decimal places, and are computed only in Python from integer counts.
- BR-09 scores are returned as integers, rounded half up.
- BR-07 as written can produce negative savings when gaps exceed savings. The design never shows that case, so the BR-07 formula itself stays as written; how a negative result is presented is an open Q-17 item, recorded in the plan as a proposed default, not as a rule change.

## 3. Candidate domain entities

### 3.1 Reference data (server-owned, read-only to users)

| Entity | Attributes | Evidence |
|---|---|---|
| **District** | `code` (slug), `name`, `province` [U], `sortOrder` | [E] 30 names in `2:6965`; province not shown |
| **ExpenseCategory** | `code`, `name` (EN/RW), `icon` | [E] Food, Housing, Transport, Utilities, Other essentials (`2:6530`–`2:6558`). Icons for 3 of them: shopping-basket, bus, zap. [U] Whether advisor categories and tracker categories are the same list (Q-11) |
| **BudgetBenchmark** | `districtCode`, `householdSize`, `categoryCode`, `monthlyAmount`, `isIllustrative`, `methodologyVersion` | [E] Demo column `2:6534`…; the key by district + size is [I] from the filters `2:6505` |
| **SeasonalSwap** | `id`, `districtCode` (nullable = all), `month` (1–12), `title`, `description`, `fromItem{name, quantity, unit, price}`, `toItem{…}`, `difference`, `notes`, `isIllustrative` | [E] `2:6698`; per-district variation [U] |
| **SeasonalTip** | `title`, `body`, `district?`, `month?` | [E] "Keep variety on the plate." `2:6714` |
| **ReferencePeriod** | `id`, `label` ("Demo month · October"), `startDate` | [E] `2:6783`; options [U] Q-14 |
| **HouseholdGroup** | `id`, `label` ("All sample households") | [E] `2:6788`; other groups [U] Q-14 |
| **DistrictVulnerability** | `districtCode`, `periodId`, `householdGroupId`?, `score`, `components{incomeInstability, essentialCostPressure, lowBufferExposure}`, `methodologyVersion` | [E] `2:7079` |
| **VulnerabilityModel** | `version`, `weights{…}`, `bands[]` | [E] weights `2:7355`, bands `2:7061` |
| **SyntheticHousehold** | `id`, `districtCode`, `householdSize`, `primaryIncomeSource` (wage / agriculture / informal_enterprise), `monthlyIncome`, `monthlyEssentials`, `savings` | [I] Needed to compute 3,000-sample KPIs (`2:6793`, `2:6805`, `2:6864`). An alternative is storing precomputed aggregates (Q-18) |
| **MonthlySeriesPoint** | `periodMonth`, `essentials`, `income`, `scope` (reference household) | [E] `2:6826` |
| **Methodology** | `version` ("v0.1"), `status`, `calculations[]`, `dataSources[]{content, validationNeed, status}`, `boundaries[]`, `checklist[]{text, done}`, `privacyNote` | [E] D4; whether this is content in the DB or static frontend copy [U] Q-12 |
| **PolicyInstrument** | `code` ("monthly_cash_support"), `label` | [E] `2:7185`; others [U] Q-10 |

### 3.2 Citizen data (client-held under Option A)

| Entity | Attributes | Evidence |
|---|---|---|
| **HouseholdProfile** | `districtCode?`, `householdSize?`, `monthlyIncome?`, `savings` [U], `isDemo` | [E] `2:6383` (all optional); savings source [U] Q-06 |
| **BudgetPlan** | `month`, `lines[]{categoryCode, plannedAmount}` → `plannedTotal` | [I] from "Planned expenses 150,000" `2:6440` and the YOU column `2:6533`. No edit screen exists (Q-06) |
| **Expense** | `id`, `date`, `title`, `categoryCode`, `note`, `amount` | [E] `2:6451`; the input form is missing (Q-07) |

### 3.3 Scenario objects (computed, not stored unless Q-19 says so)

- **HouseholdShockScenario**: inputs `shockType`, `incomeReductionPct`, `durationMonths`, plus the baseline `{income, essentials, savings}`. Outputs per BR-02 to BR-06. [E] C4
- **PolicyScenario**: inputs `instrument`, `incomeLossPct`, `durationMonths`, `supportPerHouseholdMonthly`, `eligibleHouseholds`, plus the cohort baseline. Outputs per BR-07 and BR-08 and the comparison matrix. [E] D3. Saving or naming scenarios ("SCENARIO A") is [U] Q-19.

### 3.4 Users (decision-makers)

- **User** {`id`, `name`, `email`, `organisation`?, `role`}: **not built.** Q-04 is resolved as no decision-maker login for the demo. The only evidence is the avatar `2:6765`. Citizen accounts are a different entity (`household_accounts`, contract §11.8, a Q-02 change) and are not decision-maker users.

### 3.5 Relationships

```
District 1─* BudgetBenchmark *─1 ExpenseCategory
District 1─* DistrictVulnerability *─1 ReferencePeriod
DistrictVulnerability *─1 VulnerabilityModel (by version)
District 1─* SyntheticHousehold
District 0..1─* SeasonalSwap
Methodology (version) 1─* calculations / dataSources / boundaries / checklist
[Option B] Household 1─1 HouseholdProfile, 1─* BudgetPlan 1─* BudgetPlanLine, 1─* Expense
```

## 4. Candidate database tables — SUPERSEDED

> **SUPERSEDED by `IMPLEMENTATION_PLAN.md` §3–§4**, which lists the tables actually planned per step. Known differences: weights are three NUMERIC columns, not JSON; household groups are keyed by `code`; tables are keyed by `methodology_version`; a `seed_state` table is added. The original candidate list is kept below for history only.

| Table | Key columns and constraints |
|---|---|
| `districts` | `code` PK (slug), `name` UNIQUE NOT NULL, `name_rw`?, `province`?, `sort_order` |
| `expense_categories` | `code` PK, `name_en`, `name_rw`, `icon`, `sort_order` |
| `budget_benchmarks` | PK(`district_code`, `household_size`, `category_code`, `methodology_version`), `monthly_amount` INT ≥ 0, FK to districts and categories, CHECK `household_size` ≥ 1 |
| `seasonal_swaps` | `id` PK, `district_code` NULL FK, `month` SMALLINT CHECK 1–12, item columns, `price_*` INT ≥ 0. Index (`district_code`, `month`) |
| `reference_periods` | `id` PK, `label`, `period_month` DATE UNIQUE |
| `household_groups` | `id` PK, `code` UNIQUE, `label` |
| `vulnerability_models` | `version` PK, `weights` JSON (CHECK sum = 1), `bands` JSON, `published_at` |
| `district_vulnerability` | PK(`district_code`, `period_id`, `household_group_id`, `model_version`), `score` NUMERIC(5,2) CHECK 0–100, three component columns CHECK 0–100. Index (`period_id`, `score` DESC) for ranking |
| `synthetic_households` | `id` PK, `district_code` FK, `household_size`, `primary_income_source` enum, `monthly_income`, `monthly_essentials`, `savings`. Index (`district_code`) |
| `monthly_series` | PK(`series_code`, `period_month`), `essentials`, `income` |
| `methodology_versions` + child tables, or one JSON document | Depends on Q-12 |
| `users` | Not built as such. Since 2026-10-28 `household_accounts` holds register/login accounts (contract §11.8; a Q-02 change for that table, Option C; Q-04 unchanged) |
| `households`, `budget_plans`, `budget_plan_lines`, `expenses` | **(Option B only)** |

Seeding: all demo values in the design should become a **seed dataset** so the frontend can reproduce the designs exactly. **[I]**

## 5. API resources — SUPERSEDED

> **SUPERSEDED by [api-contract-proposal.md](../api/api-contract-proposal.md) (contract v0.2 rev 2), the single authoritative definition of endpoints, parameters, fields and errors.** The table below is only an index to the contract. It deliberately carries no parameters or fields, so it cannot contradict the contract.

| Resource (under `/api/v1`) | Methods | Tier (contract) | Screens | Evidence |
|---|---|---|---|---|
| `/districts` | GET | Core §3 | C1, C3, C5, D2 | [E] |
| `/expense-categories` | GET | Core §3 | C2, C3 | [E] |
| `/budget-benchmarks` | GET | Core §4 | C3 | [E] |
| `/calculations/household-shock` | POST | Core §4 | C4, C2 nudge | [E] |
| `/seasonal-swaps` | GET | Core §4 | C5 | [E] |
| `/dashboard/filters` | GET | Core §5 | D1, D2 | [E] filters; options are [PD] Q-14 |
| `/dashboard/overview` | GET (filters: `geography`, `period`, `householdGroup`; `geography` is `all` only, [PD] Q-14) | Core §5 | D1 | [E] |
| `/district-vulnerability`, `/district-vulnerability/{districtCode}` | GET | Core §5 | D2, D1 "look next" | [E] |
| `/calculations/policy-scenario` | POST | Core §5 | D3 | [E] |
| `/methodology` | GET | **Optional** §6 (structured data only, [PD] Q-12) | D4 | [E] |
| `/calculations/budget-comparison` | POST | **Optional** §6 | C3 | [I] |
| `/demo-household` | GET | **Optional** §6 | C1, C2 | [I] |
| `/health`, `/ready` (root, not under `/api/v1`) | GET | Core §2 | — | — |
| `/auth/*`, `/me` | `POST /auth/register`, `POST /auth/login`; `GET`/`PATCH /user/profile` | Built 2026-10-28 (contract §11.8, §11.9; the profile plays the role of `/me`) | Avatar | — |
| `/households/*`, `/expenses` | — | Not built (Q-02 resolved as Option A) | C1, C2 | — |

No search, sorting UI or pagination is designed. Lists are bounded (30 districts, 5 categories, a few swaps). The ranking is "top N by score desc". **[E]/[I]**

## 6. Validation rules — SUPERSEDED

> **SUPERSEDED by the per-endpoint field tables and §1.2 (number parsing) of [api-contract-proposal.md](../api/api-contract-proposal.md).** The bounds there are [PD] Q-20: household size 1–20; money 0–100,000,000; percentages 0–100; duration 1–24; eligible households 0–3,000. The original table is kept for history only; the Q-xx reference for percentage options is corrected to Q-20. The expense rows apply only to device-held data (Q-02 Option A).

| Field | Rule | Evidence |
|---|---|---|
| `householdSize` | Integer 1–20 [U upper bound] | [E] "4 people" select; bounds [U] Q-20 |
| `monthlyIncome`, `essentials`, `savings`, amounts | Integer RWF ≥ 0, with an upper sanity limit [U] | [E] RWF integers |
| `incomeReductionPct` / `incomeLossPct` | Integer 0–100 (options shown as a select: 20%) | [E]; options [U] Q-20 |
| `durationMonths` | Integer 1–24 [U] | [E] "3 months" |
| `supportPerHouseholdMonthly` | Integer ≥ 0 | [E] |
| `eligibleHouseholds` | Integer 0 … sample size (3,000) | [I] |
| `district` | Must be one of the 30 district codes | [E] |
| `month` | 1–12 | [E] "October" |
| Expense `amount` | Integer > 0 | [I] |
| Expense `title` | 1–80 chars [U] | [I] |

All field-level failures return 422 in the shared error format (see the API contract).

## 7. Security, privacy and integrity

| Concern | Requirement | Evidence |
|---|---|---|
| No personal data collection (citizen) | Citizen endpoints must not require identity and must not log request bodies containing income or expense data. No analytics that identify a household without consent. **Exception since 2026-10-28:** `POST /auth/register` stores a citizen account (contract §11.8); no served endpoint requires a token. Q-13 and Q-34 are open. | [E] `2:6407`, `2:7417` |
| Decision-maker access | Public for the demo (Q-04 resolved). Real data would need authentication and role-based access. | Q-04, Q-24 |
| Read-only reference data | Mutating endpoints exist only for admins (Q-12), or seeding is done by migration or script. | [I] |
| Rate limiting | Calculation endpoints are unauthenticated and CPU-cheap; basic per-IP limits are desirable. Planned as **optional** step O3, not core. | [I], Q-24 |
| CORS | Allow only the frontend origin(s). | [I] |
| Input hardening | Strict schema validation; reject unknown fields; integers only for money. | [I] |
| Versioned methodology | Every computed or curated response carries `methodologyVersion` and `isIllustrative: true` so the UI can show disclaimers. Results must be reproducible for a given version. | [E] "v0.1", disclaimers |
| Consistency | Benchmarks per (district, size) must cover every category. Vulnerability scores must be recomputed when the weights change (store `model_version`). Overview KPIs must be derived from the same dataset as the heatmap. | [I] |
| Concurrency / transactions | Mostly read-only. Seed or import loads should be transactional, all-or-nothing per version. Option B expense writes are single-row and have no contention. | [I] |
| Localisation | Content-bearing entities need EN and RW text, or the frontend owns all copy. | [U] Q-03 |

## 8. Workflows and state

- **Household scenario** (C4): `draft inputs → applied → result`. The button label changes to "Scenario applied", which implies a client-side state. No server state is needed. [E]/[I]
- **Policy scenario** (D3): same pattern, "Comparison applied". [E]/[I]
- **Methodology data-source status**: enum `not_connected | to_confirm | not_validated`. Possibly also `validated` (not shown). [E] `2:7369`, `2:7375`, `2:7387`
- **Checklist item**: `done: boolean`. All unchecked in the design. [E] `2:7403`
- **Methodology version lifecycle**: `concept (v0.1) → … → production`. [I]
- Nothing in the design suggests approval flows, notifications or scheduled jobs.

## 9. Capabilities explicitly **not** needed (per design)

No evidence exists for: file uploads (images are static design assets), payments, notifications or SMS ("No phone number"), maps or GIS, live price feeds, third-party data integrations (D4: "No dataset has been acquired … or integrated"), search, or exports. Do not build these without a new requirement.

## 10. Suggested implementation order

1. ~~Decide Q-01, Q-02, Q-04, Q-15.~~ **Done 2026-10-24.** The order below is superseded by the corrected sequence in [IMPLEMENTATION_PLAN.md](../development/IMPLEMENTATION_PLAN.md) §1 and §5.
2. **Project skeleton**: health endpoint, config, error format, CORS, OpenAPI generation, CI.
3. **Reference data + seed** reproducing every demo value: districts, categories, benchmarks, periods, groups.
4. **Calculation module** (pure functions, BR-01 to BR-16) with unit tests pinned to the design numbers (30,000 / 144,000 / 6,000 / 18,000 / 42,000 / 10 / 18m / 46 / 83.3%).
5. **Citizen endpoints**: benchmarks, household-shock, seasonal swaps.
6. **Decision-maker data**: synthetic households or aggregates, vulnerability model and scores, monthly series.
7. **Decision-maker endpoints**: filters, overview, district vulnerability, policy scenario.
8. **Methodology endpoint**, or hand that content to the frontend (Q-12).
9. ~~Auth and household persistence~~: citizen register/login built on 2026-10-28 (contract §11.8; a Q-02 change for accounts only). Decision-maker login (Q-04) and persistence of profile, plan and expenses are not built.
10. Localisation of content (Q-03).

Dependencies: 4 depends on nothing and can start immediately. 5 and 7 depend on 3 and 4. 6 depends on Q-18. 9 depends on its decisions.
