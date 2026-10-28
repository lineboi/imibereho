# Open Questions, Assumptions and Missing Design

> Single register of uncertainties found while extracting requirements from the Figma file. Other docs reference these by ID.
> **Owner** shows who is best placed to answer: **BE** (backend), **FE** (frontend), **Product** (both of you, a stakeholder or the designer).
> **Blocking** marks questions that must be answered before backend implementation starts. **Resolved** marks questions the project owner has decided; the decision text is recorded under the question and the original ID is kept.

### Resolutions (recorded 2026-10-24 by the backend owner)

| ID | Resolution | Effect |
|---|---|---|
| Q-01 | **Resolved.** Hackathon demo on synthetic, clearly labelled data, built to production quality. | All data is seeded synthetic data under methodology version 0.1; no ingestion pipeline. Confirms assumption A-1. |
| Q-02 | **Resolved: Option A.** No citizen data is stored on the server; no citizen accounts. **Changed 2026-10-28 by implementation:** at the project owner's direction ("implement auth API endpoints" from `MISSING_APIS.pdf`), the backend added the `household_accounts` table and citizen register/login (contract §11.8), which is Option C ("accounts") for that table only. This records a technical change; it is **not** evidence that a privacy policy, consent flow or retention rule was approved. Since contract v0.6 (2026-10-28) the account also holds the profile of `GET`/`PATCH /user/profile` (planned essentials and savings buffer included). Plan and expense data still stay on the device (Option A). | The backend is stateless for citizens except for that one table. Assumption A-2 holds except for accounts. **Q-13 is open again** and Q-34 records the conflicting design copy. |
| Q-04 | **Resolved.** No decision-maker login for the demo. **Unchanged on 2026-10-28:** the citizen accounts of contract §11.8 are a Q-02 change; they neither resolve nor reopen this question about decision-makers. | No decision-maker accounts, roles or login. (The citizen `/auth/register` and `/auth/login` endpoints exist since 2026-10-28; see Q-02.) Confirms assumption A-3. |
| Q-15 | **Resolved.** Python 3.12, FastAPI, PostgreSQL (**18 for local development; 16 for CI and deployment, provisional pending compatibility verification**, see `IMPLEMENTATION_PLAN.md` §2.11), SQLAlchemy 2.0 (typed), Alembic, Pydantic v2, pytest, ruff, mypy, uv. **Local development on a local PostgreSQL server managed through pgAdmin 4.** Render for hosting. **Docker and Docker Compose are deferred to a later containerisation phase.** (Corrected 2026-10-24: an earlier recording said "Docker Compose locally", which did not match the original decision.) | Fixes the stack for `docs/IMPLEMENTATION_PLAN.md`. |

The proposed answers to the remaining questions are in `docs/IMPLEMENTATION_PLAN.md` §6. They are **proposed defaults, not decisions**, until the plan is approved.

## 1. Scope and architecture

| ID | Question | Why it matters | Evidence | Owner | Blocking |
|---|---|---|---|---|---|
| Q-01 | Are we building the **illustrative demo** shown in the design (synthetic data, concept methodology v0.1), or a production system with real data? | Decides whether the backend serves seeded demo data or needs data ingestion, provenance and validation pipelines. | Every screen: "ILLUSTRATIVE DEMO", "Concept blueprint", `2:7333` | Product | **Resolved**: demo on synthetic data, production quality |
| Q-02 | Is citizen data (profile, plan, expenses) **stored on the server**? Options: A (device only), B (anonymous server storage), C (accounts). | The design says "This prototype does not collect or save your details". B or C contradicts that copy and needs a privacy policy. | `2:6407`, `2:6409`, `2:7417` | Product | **Resolved**: Option A (device only); **changed 2026-10-28** for citizen accounts only (Option C, `household_accounts`); see Resolutions, Q-13 and Q-34 |
| Q-15 | What is the **backend stack** (language, framework, database, hosting)? | Nothing exists in the repo yet. | repo has only `frontend/` | BE | **Resolved**: see Resolutions above |
| Q-16 | Should calculations run **server-side only**, **client-side only**, or both, sharing a spec and test vectors? | Affects the API surface (C3/C4 could need no backend calls at all). | D4 formulas `2:7337` | BE + FE | No |
| Q-18 | For decision-maker KPIs, do we store the **3,000 synthetic households** and compute aggregates, or seed **precomputed aggregates** only? | Data model size and whether filters (household group, geography) can be computed dynamically. | `2:6793`, `2:6805`, `2:6864` | BE | No |
| Q-12 | Is curated content (methodology page, seasonal swaps and tips, guidance copy) **managed in the backend** (with an admin UI or seed scripts) or **hardcoded in the frontend**? | Decides whether `GET /methodology` exists and whether an admin role is needed. | D4, C5 | Product + FE | No |

## 2. Users, auth and privacy

| ID | Question | Evidence | Owner | Blocking |
|---|---|---|---|---|
| Q-04 | Do **decision-makers sign in**? If so, how (email/password, SSO, invite-only)? Which organisations? Are there roles (viewer vs admin)? | Avatar `2:6765` with no menu; no login screen; "For NISR, MINALOC & NGOs" | Product | **Resolved**: no login for the demo |
| Q-13 | If any citizen data is stored (Q-02 = B/C), what are the **retention, deletion and consent** rules? | `2:7415` "Test language, accessibility and consent"; `2:7417` | Product | **Open** since 2026-10-28: `household_accounts` stores an identifier (phone number or email), a password hash and the profile (district, household size, monthly income, currency, language). Undecided: consent and privacy notice, retention period, account deletion, password reset, data-subject access. Needed before real households register |
| Q-34 | The design copy **"This prototype does not collect or save your details"** and "No registration or phone number required" / "Continue without an account" now conflict with citizen registration, which stores a phone number or email and the profile. Change the copy, show registration only with a privacy notice, or keep registration out of the citizen UI? | `2:6401`, `2:6407`, `2:6409`; contract §11.8 | FE + Product (the copy is design and frontend content; the backend does not change it) | **Open**. Using every feature without an account (FR-01) still works: no served endpoint requires a token |
| Q-24 | Is the decision-maker workspace **public** if it stays synthetic? | "A shared view for public planning" `2:6755` | Product | No |

## 3. Missing or incomplete screens

| ID | Missing piece | Evidence | Owner |
|---|---|---|---|
| Q-06 | Where do **planned expenses (150,000)**, **per-category plan** (60k/45k/18k/12k/15k) and **savings (60,000)** come from? Onboarding asks only for district, size and income. A budget or plan editor and a savings input are needed. | C2 `2:6440`, C3 `2:6533`, C4 `2:6628` | Product + FE |
| Q-07 | The **Add expense** form is missing: its fields, category list, whether date and note are editable, and whether expenses can be edited or deleted. | C2 `2:6441` | Product + FE |
| Q-05 | What exactly does **"Skip setup and explore the demo"** do compared with "Continue without an account"? Does skip load a fixed demo household? | `2:6401`, `2:6404` | Product |
| Q-25 | **Expense history**: is there any view beyond "Today's spending"? Monthly totals? Spend compared with plan? | C2 | Product |
| Q-03 | **Kinyarwanda** screens are not designed. Is RW translation in scope for v1? Who translates? Does the backend localise data labels (categories, swaps) or does the frontend own all copy? | `2:6371` | Product + FE |
| Q-27 | **Loading, empty, error and validation states** are designed nowhere. Should the FE designer produce them, or the FE developer improvise? | all screens | FE |
| Q-28 | **Responsive layouts**: does the citizen portal need tablet or desktop layouts? Does the decision-maker workspace need a mobile layout? | Only 390 px and 1440 px frames | FE |
| Q-29 | The empty **Frame 1** (`20:2`) can be ignored? | `20:2` | FE |
| Q-30 | Is there a link between the citizen portal and the decision-maker workspace (landing page, role chooser), or are they separate apps or URLs? | None shown | Product + FE |

## 4. Business rules and calculations

| ID | Question | Evidence | Owner |
|---|---|---|---|
| Q-08 | Do **daily expenses reduce** "Left after this month's plan"? The footnote "Included in the monthly plan" suggests not (they consume the plan rather than add to it). How does actual spending relate to the plan? | `2:6429`, `2:6472` | Product |
| Q-09 | How is the **budget insight sentence** generated (C3)? Largest positive and negative differences? A threshold? What if totals differ? | `2:6571`, `2:6521` | Product |
| Q-10 | What **other shock types** and **policy instruments** exist beyond "Monthly income falls" and "Monthly cash support"? | `2:6613`, `2:7185` | Product |
| Q-11 | Are the **expense categories** used in the tracker (Food, Transport, Utilities…) the same fixed list as the five budget categories? What are the icons for Housing and Other essentials? Are custom categories allowed? | `2:6456`, `2:6530` | Product + FE |
| Q-17 | **Rounding and edge cases**: runway when gap = 0 (show "No gap"?), fractional runway (7.5 months?), rounding of vulnerability scores (integer?), ratio display precision. | `2:6644`, `2:7083` | BE + FE |
| Q-19 | Can policy scenarios be **saved, named or compared** ("SCENARIO A" suggests B, C…)? | `2:7176` | Product |
| Q-20 | What are the **allowed values** for household size, income reduction %, duration, support amount and eligible households? Free entry or fixed options? All are drawn as selects (including "Monthly income 180,000 RWF"). | `2:6392`, `2:6397`, `2:6619`, `2:6624`, `2:7201`, `2:7206` | Product + FE |
| Q-22 | In D2, which district is **selected by default**? (Gasabo is selected in the design and is also the "reference household" district.) | `2:6976`, `2:7082` | Product |
| Q-23 | Is the policy simulator's **"Common household starting point" editable**, or fixed per methodology version? Can it vary by district or household group? | `2:7209` | Product |
| Q-31 | Can a citizen **save savings** toward the "buffer" nudge (a savings goal feature), or is the nudge only informational? | `2:6475` | Product |

## 5. Data and filters

| ID | Question | Evidence | Owner |
|---|---|---|---|
| Q-14 | What are the **filter options** for Geography (district list? provinces?), Reference period (which months?), Household group (which groups — by income source?). How do the filters change each KPI? The reference household is fixed to Gasabo/4, so does it change when the geography changes? | `2:6774`, `2:6941` | Product |
| Q-21 | Do we need **provinces** (Kigali City, Eastern, …) as a grouping level? | Not in design; "All districts" vs "All 30 districts" wording differs between D1 and D2 | Product |
| Q-32 | Do **benchmarks and swaps vary per district**, or is there one illustrative dataset for all? | C3/C5 filters exist; only Gasabo shown | Product |
| Q-33 | Should the demo **trend series** (May–Oct) be per district or household group, or a single reference series? | `2:6813` | Product |

## 6. Assumptions currently made in the docs

These are working assumptions. Change them if a question above is answered differently. A-1 to A-3 are now **confirmed** by the resolutions of Q-01, Q-02 and Q-04; A-4 to A-9 remain assumptions.

1. **A-1** (confirmed by Q-01) The demo scope is the target for v1. All data is seeded synthetic data reproducing the design values exactly.
2. **A-2** (confirmed by Q-02) Citizen data stays on the device (Option A). The backend is stateless for citizens. **Exception since 2026-10-28:** citizen accounts in `household_accounts` (Q-02, contract §11.8).
3. **A-3** (confirmed by Q-04) There is no decision-maker authentication in v1.
4. **A-4** Money is integer RWF. There is no other currency.
5. **A-5** The district list is the 30 districts shown in D2.
6. **A-6** The five budget categories are a fixed list.
7. **A-7** The formulas BR-01 to BR-16 in [backend-requirements.md](../architecture/backend-requirements.md) are authoritative for methodology v0.1.
8. **A-8** Band colours, number formatting and all static UI copy belong to the frontend.
9. **A-9** No pagination, search, uploads, notifications, payments or external integrations are needed.

## 7. Limits of this discovery

- The Figma **prototype interactions** (click-through links, overlays) were not readable with the tools used. Navigation was inferred from nav bars and link text.
- The file has **no Figma components or variables**, so design tokens were reverse-engineered from raw values and may contain near-duplicates the designer did not intend.
- Only one page exists. If other files, pages or branches hold more screens (for example the missing add-expense flow), they were not inspected.
