# Product Requirements — Imibereho (preliminary)

> Derived from the Figma design. See [design-inventory.md](../figma/design-inventory.md) for screen-level detail and node IDs.
> Status: **Draft for team review.** Nothing here is confirmed beyond what the design shows.

**Evidence legend** used throughout the docs:
- **[E] Explicit**: visible in the design (node ID cited).
- **[I] Inferred**: a reasonable reading of the design, not drawn or stated.
- **[U] Unknown**: needs a decision. Tracked in [open-questions.md](./open-questions.md) as `Q-xx`.

## 1. Purpose

Imibereho ("livelihood/well-being" in Kinyarwanda) is a **household financial-resilience tool for Rwanda** with two faces:

1. **Citizen portal (mobile)**: helps a household see its monthly budget, track daily spending, compare its plan with a local reference, explore an income-shock scenario, and get seasonal food-swap ideas. [E] C1–C5
2. **Decision-maker workspace (desktop)**: a "shared view for public planning", aimed at bodies such as NISR, MINALOC and NGOs. It shows aggregate household pressure, a district vulnerability index, a cash-support policy simulator and a transparent methodology page. [E] sidebar `2:6756`

**Product posture.** Every screen describes itself as an **illustrative demo / concept blueprint** using **synthetic data**, and says it is "Not official statistics". The methodology screen has the version label "CONCEPT METHOD · v0.1". [E] `2:6373`, `2:6773`, `2:7333`, `2:6899`

The design does not say whether we are building that demo or a production system. **Q-01 is resolved (2026-10-24):** we are building the demo on synthetic, clearly labelled data, to production quality. The backend therefore serves curated synthetic data, not real data pipelines.

## 2. Users and roles

| Role | Evidence | Notes |
|---|---|---|
| **Citizen / household member** (anonymous) | [E] "Continue without an account", "No registration or phone number required" (`2:6401`, `2:6407`) | Anonymous by design. No login. |
| **Decision-maker / analyst** (public planner, NGO staff) | [E] workspace screens, "For NISR, MINALOC & NGOs" | A user avatar is shown (`2:6765`), but no sign-in exists. **Q-04 resolved:** no login for the demo. |
| Content / methodology administrator | [I] Someone must maintain benchmarks, swaps, district scores and methodology text | No admin UI is designed. **[U] Q-12** |

The design does not imply any other roles, such as district-level restrictions or approvers.

## 3. User journeys

### J1 — Citizen onboarding [E] C1
1. Open the app. The privacy promise and demo notice are shown.
2. Optionally pick a district, household size and monthly income. "All fields optional".
3. Choose **Continue without an account** or **Skip setup and explore the demo**.
4. Land on Home (C2).
- [I] With skip, demo values are used (Gasabo, 4 people, 180,000 RWF).
- [U] Where the planned expenses (150,000) and savings (60,000) used later come from. **Q-06**

### J2 — Daily tracking [E] C2
1. View the money left after this month's plan (income − planned expenses).
2. View today's spending total and the list of expense items (title, category, note, amount).
3. Tap **Add an expense**. **The screen is missing.** **Q-07**
4. Follow the nudge to the shock simulator.
- [U] Whether daily spending is deducted from "left after this month's plan" or only shown. The footnote says "Included in the monthly plan". **Q-08**

### J3 — Compare budget with local reference [E] C3
1. Pick a district and household size.
2. See the plan per category (Food, Housing, Transport, Utilities, Other essentials) beside a demo reference for that district and household size.
3. Read the generated insight ("Housing is 5,000 RWF above … food is 5,000 RWF below").
4. **Use this plan in the simulator** goes to C4.

### J4 — Household shock simulation [E] C4
1. Choose the shock type ("Monthly income falls"), the reduction % and the duration.
2. Available savings and expenses are taken from the household plan.
3. Apply the scenario. The result shows the monthly gap, savings used, savings remaining and the runway in months.
4. A practical next-step message is shown.

### J5 — Seasonal food swaps [E] C5
1. Choose a district and planning month.
2. See an illustrative swap (rice → sweet potatoes) with demo basket prices and the difference.
3. See variety advice and an "uncertain and unvalidated" caveat.

### J6 — Decision-maker overview [E] D1
1. Filter by geography, reference period and household group.
2. Read the KPIs: sample size, reference income, essentials/income ratio, and the share of households in deficit after a 20% shock.
3. View the 6-month essentials trend against the income line, and the income-source composition.
4. Jump to the policy simulator or heatmap.

### J7 — District heatmap [E] D2
1. Filter (same filters as D1).
2. Scan the 30-district alphabetical tile grid coloured by vulnerability band.
3. Select a district to see its score, the component inputs and weights, and the formula.
4. See the top-6 ranking. Follow the link to the methodology.

### J8 — Policy simulation [E] D3
1. Define the instrument (monthly cash support), income loss %, duration, support amount per household and number of eligible households.
2. Apply. Results show the direct transfer budget, the modelled gap with support, and a 3-column comparison (no shock / shock only / shock + support).

### J9 — Methodology transparency [E] D4
Read the calculation definitions, data-source requirements and their status, boundaries, and the pre-launch checklist.

## 4. Functional requirements

| ID | Requirement | Evidence | Status |
|---|---|---|---|
| FR-01 | Citizen can use every feature without an account or phone number | `2:6401`, `2:6407`, `2:6409` | [E] |
| FR-02 | Citizen can enter an optional district, household size and monthly income | `2:6383` | [E] |
| FR-03 | Citizen can skip setup and use demo household values | `2:6404` | [E] link; behaviour [I] |
| FR-04 | Home shows monthly income, planned expenses and remaining amount (income − planned expenses) | `2:6428` | [E] |
| FR-05 | Home lists today's expenses with category icon, title, category, note and amount, plus a daily total | `2:6444` | [E] |
| FR-06 | Citizen can add an expense | `2:6441` button only | [E] entry point; form [U] Q-07 |
| FR-07 | Budget advisor compares the citizen's per-category plan with a reference for the selected district and household size, with totals and per-category bars | `2:6516` | [E] |
| FR-08 | Budget advisor produces a plain-language insight on the largest category differences | `2:6571` | [E] text; generation rule [I] |
| FR-09 | Household shock simulator computes the shocked income, monthly gap, savings used over the duration, savings remaining and runway | `2:6633`, `2:6640` | [E] |
| FR-10 | Shock type is selectable. Only "Monthly income falls" is shown | `2:6610` | [E]; other types [U] Q-10 |
| FR-11 | Seasonal swaps are filtered by district and month and show item pairs with demo quantities, prices and difference | `2:6698` | [E] |
| FR-12 | Language switch EN / RW on the citizen portal | `2:6371` | [E] control; RW content [U] Q-03 |
| FR-13 | Decision-maker dashboard filters: geography, reference period, household group | `2:6774`, `2:6941` | [E]; option lists [U] Q-14 |
| FR-14 | Overview KPIs, monthly essentials trend with income reference, and income-source composition | `2:6790`, `2:6809`, `2:6861` | [E] |
| FR-15 | Vulnerability index (0–100) for all 30 districts, banded 0–39 / 40–59 / 60–69 / 70–100 | `2:6965`, `2:7061` | [E] |
| FR-16 | Selected district detail: score, the three weighted components and the formula | `2:7079` | [E] |
| FR-17 | Ranking of the top N districts by score (N = 6 in the design) | `2:7102` | [E] |
| FR-18 | Policy simulator: inputs (instrument, income loss %, duration, support/month, eligible households) and fixed cohort baseline; outputs budget, gap and comparison table | `2:7180`, `2:7224`, `2:7233` | [E] |
| FR-19 | Methodology page shows the version, calculations, data-source status, boundaries and checklist | `2:7291` | [E]; static vs managed content [U] Q-12 |
| FR-20 | Every data view carries a visible "synthetic / illustrative" disclaimer | all screens | [E] |

## 5. Non-functional and policy requirements visible in the design

- **Privacy by design**: "This prototype does not collect or save your details." and "The prototype does not collect or persist personal details. Production privacy, storage and retention policies require review." [E] `2:6407`, `2:7417`. **Q-02 resolved:** Option A, so the backend stores no citizen data, **except, since 2026-10-28, citizen accounts** (`household_accounts`, contract §11.8), implemented at the project owner's direction. That conflicts with this copy; the conflict is open as Q-34 (frontend owner and Product) and retention, deletion and consent as Q-13. The backend has not changed the copy. Open point: citizen calculations send income and savings to the server in request bodies that are processed and neither stored nor logged. Whether that fits the word "collect" is a product wording check (see `docs/development/IMPLEMENTATION_PLAN.md` §6, Q-16).
- **Transparency**: every derived number should be explainable (formulas are shown inline). [E] D3, D4, C4
- **Honesty labelling**: outputs must not be presented as official, predictive or as risk scores. [E] "This is not a risk score." `2:6645`
- **Bilingual**: English and Kinyarwanda. [E] for the toggle and the Kinyarwanda eyebrow "MURAKAZA NEZA"
- **Currency**: RWF only, whole numbers with thousands separators. Large values are abbreviated ("18m RWF"). [E]
- **Accessibility, consent and language testing** are listed as pre-launch checks. [E] `2:7415`

## 6. Out of scope (no evidence in the design)

Payments, notifications, messaging, file uploads, maps or geospatial boundaries ("Not a geographic map" `2:6964`), live price feeds ("NOT LIVE PRICES" `2:6695`), external data integrations ("No dataset has been acquired" `2:7359`), social features, and exports or reports.

## 7. Unresolved business questions (summary)

See [open-questions.md](./open-questions.md).

Resolved on 2026-10-24:
- **Q-01**: demo on synthetic data, production quality.
- **Q-02**: Option A, no server-side citizen data.
- **Q-04**: no decision-maker login.
- **Q-15**: backend stack fixed.

Still open, and blocking design work (frontend and product, not backend):
- **Q-06** / **Q-07** Missing plan, savings and add-expense screens.
