# Implementation Plan: Imibereho Backend

> **Status: Draft v2.3.1. The v2.3 direction is approved; v2.3.1 (superuser integration test) awaits review.** No application code is written until this plan is approved. v2 applied the pre-implementation review of 2026-10-24; v2.1 the readiness check; v2.2 restored the local-development decision (local PostgreSQL managed through pgAdmin 4; Docker deferred); v2.3 adds the repositories layer, superuser rejection, and the PostgreSQL 18 / 16 version policy. §8 lists every change.
> **Base branch:** `main` at `f2d343b` ("adding project structure"). At that commit `docs/` is untracked. The first action after approval, and after push access is sorted out (see "Blockers"), is to commit `docs/` on `docs/implementation-plan` and merge it by PR.
> **Branch naming:** `feat/step-<id>-<name>` in lowercase. Each step is one branch, cut from the latest `main`, and merged by PR **before the next step starts**.
> **Scope boundary:** backend work lives in `backend/`, `render.yaml`, `.gitattributes` and `.github/workflows/backend-ci.yml`. Docker files (`backend/Dockerfile`, `docker-compose.yml`) are added only in the deferred containerisation step C1 (§4.2). **`frontend/` is never touched.**
> **Sources of truth, in order of precedence:**
> 1. The decisions recorded in [open-questions.md](open-questions.md) ("Resolutions") and the defaults in §6 once this plan is approved.
> 2. The Figma design, cited by node ID ([design-inventory.md](../figma/design-inventory.md)).
> 3. Formulas BR-01 to BR-16 ([backend-requirements.md](../architecture/backend-requirements.md) §2).
> 4. **The API contract v0.2 rev 2, [api-contract-proposal.md](../api/api-contract-proposal.md): the single authoritative frontend–backend contract.** This plan cites contract sections and never redefines a field, a status code or a validation rule. If the plan and the contract disagree, the contract wins and the plan is corrected.
> 5. FR-01 to FR-20 ([product-requirements.md](product-requirements.md)).
>
> **Format note:** `docs/reference/plan-format-example.md` is not in the repo (checked 2026-10-24), so the structure follows the task brief. There is no `CLAUDE.md`.
> **Nature of this document:** everything below is a **planned requirement**. Nothing in it (tests, CI, guards, serialisation) has been implemented or verified in code yet.

### Evidence labels

| Label | Meaning |
|---|---|
| **[E]** | Explicit in the design (node ID cited) |
| **[I]** | Inferred from the design |
| **[PD]** | Proposed default for an open Q-xx. Approving the plan accepts it |
| **[SYN]** | Invented synthetic input, not in the design. Labelled illustrative wherever it surfaces |
| **[GATE]** | A proposed quality threshold of my own, not a requirement |
| **[ASSUMPTION]** | Unverified; must be checked before relying on it |

## Decisions used

| Question | Decision (resolved 2026-10-24) | Consequence |
|---|---|---|
| Q-01 | Hackathon demo on synthetic, clearly labelled data, built to production quality | Seeded data under methodology `0.1`; `meta.isIllustrative: true` (FR-20). Confirms A-1 |
| Q-02 | Option A: no citizen data on the server, no citizen accounts. **Changed 2026-10-28** for accounts only: `household_accounts` and citizen register/login (Option C; contract §11.8), implemented at the project owner's direction; not a privacy-policy approval | Stateless for citizens except that table; request bodies are never logged (`2:6407`, `2:7417`). Q-13 is open again; Q-34 records the conflicting design copy. A-2 holds except for accounts |
| Q-04 | No decision-maker login for the demo | No decision-maker accounts or roles. The citizen `/auth/*` endpoints of contract §11.8 are a Q-02 change, not a Q-04 one. Confirms A-3 |
| Q-15 | Python 3.12, FastAPI, PostgreSQL, typed SQLAlchemy 2.0, Alembic, Pydantic v2, pytest, ruff, mypy; **local development on a local PostgreSQL server managed through pgAdmin 4, using uv**; Render for hosting; **Docker and Docker Compose deferred to the containerisation phase**. **PostgreSQL versions: 18 for local development; 16 for CI and deployment, provisionally, pending the compatibility verification in §2.11** | §2.2, §2.9, §2.11, §3, §4.2 |
| Project deadline | Demo-ready and deployed by **2026-10-28** (set by the project owner; not part of any Q-xx). One backend engineer; the frontend belongs to a teammate | §5 |

## Blockers and external decisions

None of these can be resolved by editing documents.

| Item | Blocks | Found | Needed |
|---|---|---|---|
| **Push access to `lineboi/imibereho`** | Any step branch or PR, **from the docs PR and A1 onward** | The GitHub CLI is logged in as `Tech2024ish`; the GitHub API reports `push: false, admin: false` (checked 2026-10-24) | Grant `Tech2024ish` write access, log in as an account that has it, or agree a fork-and-PR workflow |
| `uv` toolchain (part of the established local-development decision) | A1 (`uv.lock`) | **Resolved:** `uv 0.13.5` installed (verified 2026-10-24) | — |
| **Python 3.12** | A1 | `python` is 3.14.0; 3.12.8 is available as `py -3.12` | Use 3.12 explicitly (`uv python pin 3.12`). Never 3.14 |
| Local PostgreSQL server running | A3 | **Resolved:** service `postgresql-x64-18` Running, listening on port 5432, `postgres` 18.0 (verified 2026-10-24) | — |
| PostgreSQL version policy | A3 onward | **Decided (2026-10-24):** 18 for local development; 16 for CI and deployment, **provisionally** | Run the compatibility verification in §2.11. The 16 choice for CI and deployment is confirmed or revised in A5, with approval |
| **Local role and three databases** | A3 | Not created yet | One-time setup in pgAdmin 4 (§2.9): a login role `imibereho` and the databases `imibereho`, `imibereho_test` and `imibereho_migrations`, owned by that role |
| Frontend sign-off on contract v0.2 rev 2 | F3 onward (and ideally §1 before A2) | — | Accept as written |
| Render account and plan | A5 | — | A paid starter instance and database for demo week **[ASSUMPTION: check current Render terms for free-tier sleep and database lifetime]** |
| Deployed frontend origin for CORS | Browser calls from the deployed frontend (A5 onward) | — | Supplied by the teammate before 26 Oct |
| Branch protection on `main` | A4 (protection only; CI runs without it) | `Tech2024ish` is not an admin | The repo admin (`lineboi`) enables it |

---

## 1. Status table and dependencies

**Tiers:** *Core* is required for the demo. *Optional* is built only after every core step is merged, and cut from the bottom of the table upward if time runs short.

| Step | Item | Tier | Depends on | Status | Branch | Linked screens (Figma node IDs) |
|---|---|---|---|---|---|---|
| A1 | Project skeleton, config, privacy-safe logging | Core | Blockers: push access, uv, Python 3.12 | Not started | `feat/step-a1-project-skeleton` | n/a |
| A2 | Error format (including malformed JSON), envelope, number types, CORS, `/health` | Core | A1 | Not started | `feat/step-a2-errors-envelope-cors` | all screens; disclaimers `2:6373`, `2:6773`, `2:7333` |
| A3 | Database connection config, Alembic, database safety guards, test DB lifecycle, seed framework, `/ready` (local PostgreSQL via pgAdmin 4; no Docker) | Core | A2; local PostgreSQL blockers | Not started | `feat/step-a3-database` | n/a |
| A4 | CI: lint, types, isolated migrations, seed repeatability, OpenAPI snapshot, contract path test, coverage | Core | A3 | Not started | `feat/step-a4-ci` | n/a |
| A5 | Early Render deployment on Render's **native Python runtime** (no Docker), health check `/health`, auto-deploy from `main` | Core | A4; Render decision | Not started | `feat/step-a5-render-deploy` | n/a |
| F1 | Calculation module (BR-01 to BR-14, BR-16) and SQL-equivalent deficit predicate | Core | A3 (for the SQL equivalence test) | Not started | `feat/step-f1-calculations` | C2 `2:6428`; C4 `2:6633`, `2:6640`; D1 `2:6790`; D2 `2:7079`, `2:7061`; D3 `2:7224`, `2:7233`; D4 `2:7337` |
| F2 | Reference data: districts, categories, methodology version, reference household | Core | A3 | Not started | `feat/step-f2-reference-data` | C1 `2:6383`; C3 `2:6505`; C5 `2:6680`; D2 `2:6965` |
| F3 | `GET /budget-benchmarks` | Core | F2; contract sign-off | Not started | `feat/step-f3-budget-benchmarks` | C3 `2:6516` |
| F4 | `POST /calculations/household-shock` | Core | F1, A2 | Not started | `feat/step-f4-household-shock` | C4 `2:6608`, `2:6633`, `2:6640`; C2 `2:6428` |
| F5 | `GET /seasonal-swaps` | Core | F1, F2 | Not started | `feat/step-f5-seasonal-swaps` | C5 `2:6698`, `2:6714` |
| F6 | Decision-maker dataset: synthetic households, series, vulnerability model and scores | Core | F1, F2 | Not started | `feat/step-f6-dm-dataset` | D1 `2:6790`, `2:6809`, `2:6861`; D2 `2:6959`, `2:7079` |
| F7 | `GET /district-vulnerability` list and detail | Core | F6 | Not started | `feat/step-f7-district-vulnerability` | D2 `2:6959`, `2:7061`, `2:7079`, `2:7102` |
| F8 | `POST /calculations/policy-scenario` | Core | F1, F2 (reference household), F6 (sample size) | Not started | `feat/step-f8-policy-scenario` | D3 `2:7180`, `2:7224`, `2:7233` |
| F9 | `GET /dashboard/filters`, `GET /dashboard/overview` (`geography=all` only) | Core | F6, F7 (ranking service) | Not started | `feat/step-f9-dashboard-overview` | D1 `2:6774`, `2:6790`, `2:6809`, `2:6861`, `2:6882`, `2:6888` |
| F10 | Demo hardening: security headers, full smoke test, demo checklist | Core | A5, F3–F9 | Not started | `feat/step-f10-demo-hardening` | all |
| O1 | `GET /demo-household` | Optional | F2 | Not started | `feat/step-o1-demo-household` | C1 `2:6404`; C2 `2:6444` |
| O2 | `POST /calculations/budget-comparison` | Optional | F1, F3 | Not started | `feat/step-o2-budget-comparison` | C3 `2:6569` |
| O3 | Rate limiting on `POST /calculations/*` | Optional | A2 | Not started | `feat/step-o3-rate-limit` | n/a |
| O4 | `GET /methodology` | Optional | F6 | Not started | `feat/step-o4-methodology` | D4 `2:7331`, `2:7357` |
| O5 | Per-district geography on `/dashboard/overview` | **Not planned** unless Q-14 / Q-18 is decided in favour (§6) | F9 | Not planned | — | D1 `2:6774` |
| C1 | Containerisation: Dockerfile, `docker-compose.yml`, CI image build | **Deferred** (§4.2): after the demo, or earlier only as the A5 fallback | A5 | Deferred | `feat/step-c1-containerisation` | n/a |

Status values: `Not started` → `In progress` → `In review (PR #n)` → `Merged`, or `Cut`.

---

## 2. How every step is delivered

Each step goes through every item that is **active** for it (§2.1). If an item does not apply, the step's Results subsection says so.

1. **Branch.** Cut `feat/step-<id>-<name>` from up-to-date `main`.
2. **Models and migration** (steps with tables). Typed SQLAlchemy 2.0 models and one hand-reviewed Alembic revision. The local round trip runs **only** against the migrations database, selected by an explicit `--target` (§2.10); the guard (§2.3) refuses a downgrade on any other target:
   ```powershell
   uv run python -m app.db.migrate --target migrations upgrade head
   uv run python -m app.db.migrate --target migrations downgrade -1
   uv run python -m app.db.migrate --target migrations upgrade head
   uv run python -m app.db.migrate --target migrations check
   ```
3. **Pydantic v2 schemas** for every body, query string and path parameter, using the A2 types that implement contract §1 and §1.2:
   - `BodyInt`: strict JSON integers. Strings, booleans and `4.0` are rejected.
   - `QueryInt`: digits-only (`^[0-9]+$` after URL decoding), then bounds.
   - `JsonDecimal`: a `Decimal` that always serialises as a JSON number.
4. **Repositories and services** (layering, introduced in A3 and enforced by `tests/unit/test_layering.py`):
   - **Repositories** (`backend/app/repositories/`) handle **database queries only**. They take a `Session`, build and run SQLAlchemy statements, and return models or typed rows. They contain no business rules, no rounding, no HTTP concepts, and no imports from `services` or `api`.
   - **Services** (`backend/app/services/`) handle **business rules and orchestration**. They call repositories for data and F1's pure `calculations` for arithmetic, apply validation that needs data (for example, an unknown district → 404), and build response objects. They never construct SQL themselves.
   - **Routers** (`backend/app/api/`) parse the request, call one service, and return its result. They hold no logic and never touch repositories or the `Session` directly.
   - **Calculations** (`backend/app/calculations/`) stay pure: no database, no framework imports.
   - **Writers:** only Alembic migrations and the seed framework (`backend/app/seed/`) write to the database. The repositories used by the API are read-only, so the API never writes (Q-02: no citizen persistence), **except** `POST /auth/register`, which inserts one `household_accounts` row (contract §11.8, 2026-10-28). The seed framework reads `seed_state` through `repositories/seed_state.py`, which `/ready` also uses.
5. **Router** in `backend/app/api/v1/`, with `response_model`, `summary` and documented error responses.
6. **Seed data** in `backend/app/seed/data/` reproducing the design values and citing node IDs, registered with the A3 seed framework.
7. **Unit tests** pinned to the §2.4 design reference values.
8. **API tests**, one module per router. Each endpoint gets:
   - The design happy path.
   - Every 4xx path the contract lists for it, checking the status, `Content-Type: application/problem+json`, `type`, `errors[].field` and `errors[].code`.
   - The `meta` envelope.
   - The §2.5 query-integer matrix for each integer query parameter.
   - The §2.6 body-integer matrix for each integer body field.
   - The §2.7 numeric-type assertions for each numeric response field.
9. **Contract registration.** Add the step's new `(method, path)` pairs to `IMPLEMENTED_ENDPOINTS` in `tests/contract/endpoints.py` and regenerate `tests/contract/openapi.snapshot.json`. The PR shows the snapshot diff, and the contract must already describe the change (§3, A4).
10. **Quality gates:** run every gate active for this step (§2.1). A gate counts only once the step that introduces it is merged.
11. **`/docs` check:** open `http://localhost:8000/docs` and call each new endpoint once.
12. **After merge (from A5 on):** Render auto-deploys `main`; run `backend/scripts/smoke.py <render-url>` and record the result.
13. **Update this file:** the step's §1 row and its **Results** (what shipped, test count, coverage, deviations with their reasons).
14. **Suggested commit message** is given per step.
15. **Stop for approval.** The PR is merged before the next step's branch is cut.

### 2.1 Quality gates and when they become active

| Gate | Command or check | Active from | Where |
|---|---|---|---|
| Lint and format | `ruff check . && ruff format --check .` | A1 | Local from A1; CI from A4 |
| Types | `mypy app tests` (strict) | A1 | Local from A1; CI from A4 |
| Full test suite | `pytest` (every test that exists at that point) | A1 | Local from A1; CI from A4 |
| Error-format tests | `tests/api/test_errors.py` | A2 | — |
| Database guards | `tests/unit/test_db_safety.py`, plus the guards running in `conftest.py` | A3 | — |
| Migration round trip | `tests/migrations/test_round_trip.py` on `imibereho_migrations` | A3 | Local from A3; CI from A4 |
| Seed repeatability | `python -m app.seed --target test` twice, then `python -m app.seed --target test --check` | A3 (framework; trivially passes with no datasets) | Local from A3; CI from A4 |
| Container image build | `docker build backend` | **C1 only** (deferred, §4.2). Not a gate for any core step | CI, only once C1 exists |
| CI workflow | `.github/workflows/backend-ci.yml` | A4 | — |
| Coverage | `--cov-fail-under=85` **[GATE]** | A4 | CI |
| OpenAPI snapshot and contract path test | `tests/contract/` | A4 | — |
| Calculation coverage | 100% line coverage of `app/calculations` **[GATE]** | F1 | — |
| Deployed smoke test | `scripts/smoke.py <render-url>` | A5 (health, ready, CORS); each later step adds its endpoints | — |

### 2.2 Test data lifecycle

| Database | Purpose | Lifecycle |
|---|---|---|
| `imibereho` | Local development, on the **local PostgreSQL server managed through pgAdmin 4** | Created once in pgAdmin (§2.9); migrated and seeded with `--target dev` (§2.10) before running the server locally |
| `imibereho_test` | `tests/unit`, `tests/api`, `tests/contract` | Session start, in `tests/conftest.py`, in this order: (1) resolve `TEST_DATABASE_URL` and run the `test` guard (§2.3, §2.10); (2) migrate to head through `app.db.migrate`'s Python API with target `test`; (3) the full deterministic seed of every dataset in the build, with target `test`; (4) the seed check. Then each test runs inside a transaction that is rolled back, so seeded rows are never altered. Tests that read seeded data (F2 onward) depend on the session fixture, never on test order |
| `imibereho_migrations` | `tests/migrations` and the local round trip only | Freely downgraded and upgraded; holds no seed data; never shared with other tests |

All three live on the same local server, created in pgAdmin 4. In CI (A4), `imibereho_test` and `imibereho_migrations` exist on a PostgreSQL 16 service that GitHub runs (16 is provisional, §2.11); CI needs no development database. The development and test databases are never used for migration round trips, and production is never reachable from tests.

### 2.3 Database safety guards (planned requirements, enforced in code from A3)

One module, `backend/app/db/safety.py`, holds `assert_safe_target(url, purpose, command=None)`. It parses the URL and reads `ENVIRONMENT`. It refuses (raises, and the caller exits non-zero) unless every rule for the purpose holds:

| Purpose (= `--target`, §2.10) | Database name must be exactly | Allowed hosts | `ENVIRONMENT` | Allowed commands |
|---|---|---|---|---|
| `migrations` (pytest `tests/migrations`, local round trip) | `imibereho_migrations` | `localhost`, `127.0.0.1`, `::1` | Not `production` | Any |
| `test` (`tests/conftest.py`, CI seed check) | `imibereho_test` | `localhost`, `127.0.0.1`, `::1` | Not `production` | `upgrade`, `check`, `current`; seeding |
| `dev` (local server, local CLI) | `imibereho` | `localhost`, `127.0.0.1`, `::1` | `local` | `upgrade`, `current`, `check`, `heads`, `history`; seeding; **not** `downgrade` or `stamp` |
| `production` (Render `scripts/start.sh`) | Any (Render assigns it) | Any **except** `localhost`, `127.0.0.1`, `::1` | `production` | `upgrade`, `current`, `check`; seeding |

**Superuser rejection (every target, including `production`).** Two checks, both refusing the connection:
1. **Before connecting:** a URL whose user name is `postgres` is refused, with reason code `superuser_name`. No connection is opened.
2. **Immediately after connecting**, before any migration, seed, query or request is served: `SELECT rolsuper FROM pg_roles WHERE rolname = current_user`. If the result is `true`, the guard closes the connection and refuses with reason code `superuser_role`, naming the role. If the query fails or returns no row, it refuses with reason code `role_check_failed` (fail closed).

The reason codes are part of the guard's error type, so tests can prove **which** check refused a connection, not just that one did.

This covers a superuser under any name, not only `postgres`. It runs in `app.db.migrate`, `app.seed`, both conftests and `create_app` (at startup, before the app accepts requests). Application, test, migration and seed connections all use the non-superuser role `imibereho` (§2.9). Superuser access is used only by a person in pgAdmin for the one-time setup, and by CI's setup step to create the role.

The local pgAdmin-managed server and GitHub's CI service are both reached on `localhost`, so no other host is ever allowed outside production. A `migrations` or `test` target can therefore never point at the development database (wrong name) or at Render (wrong host and wrong environment).

Enforcement points:
- **Alembic runs only through `python -m app.db.migrate --target <target> <command> [args]`.**
  - The wrapper resolves the URL for that target (§2.10), runs the guard with the target **and the command it was given**, prints `target, host/dbname` (never the password), then calls Alembic's Python API, passing the URL and the target in `config.attributes`.
  - `alembic/env.py` **refuses to run** when those attributes are absent. A bare `alembic upgrade head`, for example, exits with a message pointing to the wrapper. It never reads `DATABASE_URL` or any other variable itself.
  - **Alembic therefore cannot silently use an unsafe or unintended URL**, and the guard always knows the command. There is no guessing from Alembic internals.
- **`tests/migrations/conftest.py`** resolves the `migrations` target, guards it, and calls `pytest.exit(..., returncode=2)` on refusal or when `MIGRATIONS_DATABASE_URL` is unset. It never skips silently.
- **`tests/conftest.py`** resolves the `test` target, guards it, and exits the same way. The app under test receives this URL through an explicit dependency override, never through `DATABASE_URL`.
- **`python -m app.seed --target <dev|test|production>`** resolves and guards its target the same way.
- **The running server:** `create_app(target)` takes an explicit target.
  - The module-level `app` that uvicorn loads calls `create_app` with `dev` when `ENVIRONMENT=local`, or `production` when `ENVIRONMENT=production`, resolves `DATABASE_URL`, guards it, and refuses to start for any other `ENVIRONMENT`.
  - Tests call `create_app("test")`, which resolves `TEST_DATABASE_URL`. So pytest never touches `DATABASE_URL`, and a missing `DATABASE_URL` in CI is not an error.
- **Tests of the guard itself:** `tests/unit/test_db_safety.py` covers every row and every refusal:
  - The wrong database name, including `imibereho` or `imibereho_test` given to the `migrations` target.
  - A non-local host for `migrations`, `test` or `dev`.
  - `localhost` for `production`.
  - `ENVIRONMENT=production` with any non-production target.
  - A downgrade on `dev`, `test` or `production`.
  - An unknown command.
  - A missing variable.
  - `env.py` invoked without wrapper attributes.
  - **Superuser, before connecting (stubbed):** a URL with user `postgres` is refused with `superuser_name` for every target (`dev`, `test`, `migrations`, `production`), and the stubbed connect function is **never called**. *Proves:* the name check runs first and opens no connection.
  - **Superuser, after connecting (stubbed):** a stubbed connection whose `rolsuper` query returns `true` is refused with `superuser_role` for every target, and the stub records that the connection was closed. *Proves:* the role check is wired for every target and closes what it opened.
  - **Non-superuser accepted (stubbed):** a stub returning `false` is accepted. *Proves:* the check is not over-broad.
  - **Fail closed (stubbed):** a role-check query that raises, or returns no row, is refused with `role_check_failed`. *Proves:* error paths that a real database can't easily produce still refuse.
- **Integration tests of superuser rejection against a real PostgreSQL server** (`tests/integration/test_superuser_refused.py`). Three separate cases, each with its own variable (§2.10):

  | Test | Connects as | Expected | What it proves that the stubs cannot |
  |---|---|---|---|
  | `test_postgres_username_refused_before_connect` | the built-in `postgres` superuser (`SUPERUSER_POSTGRES_DATABASE_URL`) | `app.db.migrate`, `app.seed` and `create_app` each refuse with `superuser_name`. `pg_stat_activity` shows no session opened by the test for that user | The name check holds with a real URL and a real driver, before any network connection |
  | `test_non_postgres_superuser_refused_by_rolsuper` | a **temporary CI-only superuser** whose name is not `postgres`: `imibereho_ci_superuser` (`SUPERUSER_ALT_DATABASE_URL`) | All three refuse with **`superuser_role`**, not `superuser_name`. The session is closed (absent from `pg_stat_activity` afterwards). The database is unchanged: no `alembic_version` change, no `seed_state` change | The `rolsuper` query really detects a superuser on PostgreSQL 16 (CI) and 18 (if run locally), whatever its name |
  | `test_application_role_accepted` | `imibereho` (`TEST_DATABASE_URL`) | The guard passes; `rolsuper` is `false` | The real check does not falsely refuse the non-superuser application role |

  - **CI:** all three always run (A4); a skip in CI fails the job.
  - **Locally:** the two superuser cases are optional. When their variable is absent, each reports as skipped **with the reason printed**. A local skip does not count as evidence; the CI run does.
  - **Credentials:** neither superuser credential is ever committed. `.env.example` shows the variable names with placeholders only.

### 2.4 Design reference values (the only values tests may call "design values")

| Value | Rule | Node |
|---|---|---|
| 30,000 | BR-01 | `2:6430`, `2:7343` |
| 144,000 | BR-02 | `2:6636`, `2:7349` |
| 6,000; 0 with 6,000 support | BR-03 | `2:6635`, `2:7231` |
| 18,000 used / 42,000 left | BR-04 / BR-05 | `2:6638`, `2:6639` |
| 10 months | BR-06 | `2:6644` |
| 150,000 / 42,000 / 60,000 | BR-07 | `2:7276`–`2:7278` |
| 18,000,000 | BR-08 | `2:7228` |
| 46 for Gasabo, from 50 / 40 / 50 | BR-09 | `2:7097` |
| 46 → band 2 | BR-10 | `2:7061` |
| 83.3% (0.8333) | BR-11 | `2:6801` |
| 33.3% (0.3333), 1,000 of 3,000 | BR-12 | `2:6805` |
| Housing +5,000, Food −5,000 | BR-13 | `2:6571` |
| 400 | BR-14 | `2:6712` |
| 6,500 | BR-15 (frontend only) | `2:6449` |
| 30 D2 scores; top 6 74 / 71 / 68 / 66 / 64 / 63 | BR-09 data | `2:6965`, `2:7102` |
| 1,200 / 1,050 / 750 | Income sources | `2:6864` |
| 138,000 to 150,000 and 180,000 | Trend | `2:6826` |

Inputs such as 180,001 or 45,000 ÷ 6,000 are **derived test inputs**, and tests name them that way.

### 2.5 Query-integer matrix (contract §1.2), for every integer query parameter

| Raw query value | Expected |
|---|---|
| `4` | 200 (or the endpoint's normal result) |
| `%34` (decodes to `4`) | Same as `4` |
| `04` | Same as `4` |
| `4.0`, `4.5`, `4e0`, `+4`, `-1`, `%204` (leading space), `0x4`, `abc`, empty | 422 `not_integer` |
| A digit string outside the bounds (e.g. `21` for `householdSize`) | 422 `out_of_range` |
| Missing, where the parameter is required | 422 `required` |
| An extra parameter the endpoint does not define | 400 `unknown-parameter`, `errors[0].code = unknown_field` |

### 2.6 Body-integer matrix (contract §1.2), for every integer body field

| JSON value | Expected |
|---|---|
| `180000` | Accepted |
| `"180000"`, `1.5`, `4.0`, `true`, `false` | 422 `not_integer` at that field's path |
| `null`, or the field missing (required fields) | 422 `required` |
| Out of bounds | 422 `out_of_range` |

### 2.7 Numeric-type assertions (contract §1, "Numbers in responses")

Tests parse the **raw response text** with `json.loads` and assert that each numeric field is an `int` or a `float`, never a `str`. They also assert the field's exact value, and that the OpenAPI schema types the field as `integer` or `number`. Fields covered:
- Ratios and shares: `essentialsToIncomeRatio`, `shockDeficit.share`, `incomeSources[].share`.
- `runwayMonths`.
- Weights: `model.weights.*` and `components[].weight`.
- Swap quantities: `from.quantity` and `to.quantity`.
- Every money, count and score field.

### 2.8 What logs may contain

| Log source | Contains | Never contains |
|---|---|---|
| App JSON logs (A1) | `ts`, `level`, `request_id`, `method`, route **path without query string**, `status`, `duration_ms`; on 500, an exception type and traceback (no local variable values) | Request bodies, query strings, headers other than `X-Request-ID` |
| Uvicorn access log | **Disabled** with `--no-access-log`, both in `backend/scripts/start.sh` (Render) and in the documented local run command (§2.9) | — |
| Render platform HTTP logs | The full request URL, **including query strings**: `district`, `householdSize`, `month`, `geography`, `period`, `householdGroup`, `sort`, `limit` and `topN` values. No money values are ever sent in query strings (contract §1) | Request bodies |
| PostgreSQL | Server defaults: errors and connection events. No statement logging is configured; `log_statement` stays `none` **[ASSUMPTION: Render's managed default, and the local server's default unless changed in pgAdmin; confirm in A3 (local) and A5 (Render)]** | — |

### 2.9 Local development setup (no Docker)

**Prerequisites:**
- Python 3.12 (through `uv python pin 3.12`).
- `uv`.
- The local PostgreSQL server, running.
- pgAdmin 4 (bundled with the local PostgreSQL install).
- Git.

**Docker is not required for any core step.**

**One-time database setup in pgAdmin 4** (Query Tool, connected as the `postgres` superuser). The script is committed in A3 as `backend/scripts/sql/create_local_databases.sql`, for copying into pgAdmin:
```sql
CREATE ROLE imibereho LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '<choose locally; never commit>';
CREATE DATABASE imibereho            OWNER imibereho;
CREATE DATABASE imibereho_test       OWNER imibereho;
CREATE DATABASE imibereho_migrations OWNER imibereho;
```
The application connects as `imibereho`, never as `postgres`.

**Daily local workflow (PowerShell, from `backend/`):**
```powershell
uv sync
uv run python -m app.db.migrate --target dev upgrade head
uv run python -m app.seed --target dev
uv run uvicorn app.main:app --reload --no-access-log
uv run pytest            # uses imibereho_test and imibereho_migrations only
```

### 2.10 Database connection configuration (one source, no fallbacks)

| Variable | Used by | Target | Required when |
|---|---|---|---|
| `DATABASE_URL` | the running server; `app.db.migrate --target dev` or `--target production`; `app.seed --target dev` or `--target production` | `dev` (local) or `production` (Render) | Running the server, or migrating or seeding dev or production |
| `TEST_DATABASE_URL` | `tests/conftest.py`; `app.db.migrate --target test`; `app.seed --target test` | `test` | Running pytest, or the CI seed check |
| `MIGRATIONS_DATABASE_URL` | `tests/migrations/conftest.py`; `app.db.migrate --target migrations` | `migrations` | Running pytest, or a local round trip |
| `SUPERUSER_POSTGRES_DATABASE_URL` | `tests/integration/test_superuser_refused.py` **only**: the `postgres` user-name case, as a negative input that must be refused | none (never a valid target) | Always in CI; optional locally |
| `SUPERUSER_ALT_DATABASE_URL` | `tests/integration/test_superuser_refused.py` **only**: the non-`postgres` superuser case (`rolsuper` path), as a negative input that must be refused | none (never a valid target) | Always in CI; optional locally |

**Rules:**
- The two `SUPERUSER_*` variables are never mapped to any target, and are not fields of `Settings`. No application, migration or seed code reads them, and `test_layering.py` asserts that only the integration test file references them. Even if one were misused, the §2.3 guard would refuse it.
- The three target URLs are read by one `Settings` class (`app/core/config.py`). Process environment variables take precedence over `backend/.env`. `backend/.env` is git-ignored; `backend/.env.example` is committed with placeholder values only.
- Each consumer reads **only** the variable mapped to its target. **No variable falls back to another**, and none has a default URL. A missing variable is an error that names the variable.
- Every URL is passed through the §2.3 guard for its target before any connection is opened.
- `postgres://` and `postgresql://` URLs (Render's format) are normalised to `postgresql+psycopg://`. Normalisation is the only transformation applied.

**Local `.env.example`:**
```
ENVIRONMENT=local
DATABASE_URL=postgresql+psycopg://imibereho:<password>@localhost:5432/imibereho
TEST_DATABASE_URL=postgresql+psycopg://imibereho:<password>@localhost:5432/imibereho_test
MIGRATIONS_DATABASE_URL=postgresql+psycopg://imibereho:<password>@localhost:5432/imibereho_migrations
CORS_ORIGINS=http://localhost:5173
# Optional, for the superuser-rejection integration tests only (never used by the app):
# SUPERUSER_POSTGRES_DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5432/imibereho_test
# SUPERUSER_ALT_DATABASE_URL=postgresql+psycopg://<temporary superuser>:<password>@localhost:5432/imibereho_test
```
The port is the local PostgreSQL 18 server's port, 5432 (verified 2026-10-24). Both `SUPERUSER_*` variables are optional locally (§2.3 integration tests) and must never appear with real credentials in a committed file. **Creating a temporary non-`postgres` superuser locally is not required**: the `rolsuper` path is proven in CI.

### 2.11 PostgreSQL version policy and compatibility verification

| Where | Version | Status |
|---|---|---|
| Local development and local tests | **18** (the installed server: `postgres` 18.0) | Decided |
| CI (`services: postgres`) | **16** | **Provisional** |
| Deployment (Render database) | **16** | **Provisional**; confirmed or revised in A5 |

**Compatibility rules:**
- Application SQL, migrations and seed code use only features available in **both 16 and 18**. In particular they avoid features added in 17 or 18 (for example `JSON_TABLE`, `MERGE … RETURNING`, `uuidv7()`, virtual generated columns). The PR review checklist includes this rule.
- Nothing may depend on a version-specific default. Migrations name every constraint and index explicitly, using the A3 naming convention.

**Compatibility verification (evidence required):**

| When | Check | Evidence recorded in Results |
|---|---|---|
| A3 | The full local suite, including the migration round trip and the seed repeatability check, passes on 18 | `SELECT version()` output from the test database, and the pytest summary |
| A4 onward, every PR | The same suite passes in CI on 16 | The CI run link, showing the `postgres:16` service version |
| A3 | On startup, `create_app` logs the server's major version (`server_version_num`) once | The log line from a local run |
| A5 | Render's database version is read with `SELECT version()` and recorded | Output in A5 Results |
| A5 | **Decision point:** if Render cannot provide 16, or if CI on 16 and local 18 disagree on any test, stop and ask for approval to revise the provisional choice | A note in A5 Results |

From A4 onward, a merge requires **both** the local 18 run and the CI 16 run to pass. The CI result on 16 is the gate for merging; the local 18 result is required evidence, not a substitute for it. Before A4 (A1–A3), CI does not exist yet, so the local 18 run is the only evidence, and **16-compatibility is unverified until the first CI run in A4**. A4's Results must state the outcome explicitly.

---

## 3. Foundation steps

Target layout:

```
backend/
  pyproject.toml, uv.lock, .python-version (3.12), alembic.ini, README.md
  .env.example                  # committed placeholders; .env is git-ignored
  app/
    main.py                     # create_app(target)
    core/config.py, core/logging.py, core/errors.py, core/cors.py, core/types.py
    core/methodology.py         # CURRENT_METHODOLOGY_VERSION = "0.1"
    db/base.py, db/session.py, db/safety.py, db/migrate.py   # migrate = the only Alembic entry point
    models/                     # typed SQLAlchemy 2.x tables
    repositories/               # database queries only, read-only for the API (§2 item 4)
    services/                   # business rules and orchestration
    calculations/               # pure BR functions
    schemas/                    # Pydantic v2 request/response models
    seed/                       # seed framework and data (the only writer besides migrations)
    api/health.py               # /health, /ready
    api/v1/                     # routers under /api/v1
  alembic/env.py, alembic/versions/
  scripts/start.sh              # Render start command (migrate → seed → uvicorn)
  scripts/sql/create_local_databases.sql   # one-time pgAdmin setup (§2.9)
  scripts/smoke.py, scripts/dump_openapi.py
  tests/conftest.py, tests/unit/, tests/api/, tests/contract/, tests/integration/, tests/migrations/conftest.py, tests/migrations/
render.yaml
.gitattributes                  # *.sh text eol=lf
.github/workflows/backend-ci.yml
# Added only in deferred step C1 (§4.2): backend/Dockerfile, backend/.dockerignore, docker-compose.yml
```

### A1. Project skeleton, config, privacy-safe logging
**Builds**
- Project definition:
  - Runtime dependencies: `fastapi>=0.115` (needed for query-parameter models), `uvicorn[standard]`, `pydantic>=2`, `pydantic-settings`, `sqlalchemy>=2`, `psycopg[binary]>=3`, `alembic`.
  - Dev dependencies: `pytest`, `pytest-cov`, `httpx`, `ruff`, `mypy`.
  - Python `>=3.12,<3.13`.
- ruff: line length 100, rule sets `E,F,I,B,UP,SIM,RUF,S`. mypy: strict with the pydantic plugin.
- `Settings` fields:
  - `ENVIRONMENT`: no default. One of `local`, `ci`, `production`.
  - `DATABASE_URL`, `TEST_DATABASE_URL`, `MIGRATIONS_DATABASE_URL`: no defaults and no fallbacks between them (§2.10). In A1 they are declared and parsed only; nothing connects until A3.
  - `CORS_ORIGINS` (default `http://localhost:5173`), `LOG_LEVEL`, `RATE_LIMIT_PER_MINUTE` (used only by O3).
  - Sources: process environment, then `backend/.env`.
- `backend/.env.example`, `.python-version` (`3.12`), and `.gitignore` entries for `.env` and `.venv`.
- `backend/README.md`, section "Local setup": the §2.9 prerequisites and commands. **No Docker.**
- JSON request logging exactly as §2.8; `X-Request-ID` is echoed back or generated.
- OpenAPI `info.version = "0.2.0"` (contract §0).

**Tests:** `tests/unit/test_config.py` (URL normalisation; a missing variable raises an error naming it; `TEST_DATABASE_URL` is never derived from `DATABASE_URL`; a process environment value beats `.env`); `tests/api/test_request_id.py`; `tests/api/test_logging_privacy.py` (a POST body and a query string sent to a test route never appear in the captured app logs).
**Commit:** `chore(backend): scaffold FastAPI project with config and privacy-safe logging`
**Results:** _to be filled in after the step is built._

### A2. Errors, envelope, number types, CORS, `/health`
**Builds**
- `core/types.py`:
  - `BodyInt`: Pydantic strict `int`, rejecting `str`, `float` (including `4.0`) and `bool`.
  - `QueryInt`: a `str` matched against `^[0-9]+$` and then converted to `int`; a failed match is reported as `not_integer`.
  - `JsonDecimal`: `Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]`, so a `Decimal` is always emitted as a JSON number. The value is quantised before conversion, so the emitted number has no more decimal places than the contract allows.
- `BodyModel` and `QueryModel` (`extra="forbid"`), `ApiModel` for responses, `Meta` (`isIllustrative: Literal[True]`), and `ItemList[T]`, all per contract §1.1.
- Problem+json handlers implementing contract §1.3:

  | Source | Result |
  |---|---|
  | **`json_invalid` → 400 `malformed-request`**, with exactly the body shown in contract §1.3 and no `errors` | 400 |
  | `extra_forbidden` in a query | 400 `unknown-parameter` with `unknown_field` |
  | `extra_forbidden` in a body | 422 `unknown_field` |
  | `missing`, or `null` on a required field | 422 `required` |
  | `greater_than*`, `less_than*` | 422 `out_of_range` |
  | `int_type`, `int_parsing`, `int_from_float`, and the `QueryInt` pattern failure | 422 `not_integer` |
  | `enum`, `literal_error` | 422 `unknown_value` |
  | `string_too_long` | 422 `too_long` |
  | Unknown route / wrong method / unhandled exception | 404 `not-found` / 405 `method-not-allowed` / 500 `internal` |

  Validation runs before any lookup (contract §1.3, evaluation order).
- `Content-Language: en` on every response (contract §1).
- CORS: allowlist from `CORS_ORIGINS`; methods `GET, POST, OPTIONS`; request headers `Content-Type`, `X-Request-ID`; exposed header `X-Request-ID`; no credentials.
- `GET /health` (contract §2).

**Tests**
- `tests/api/test_errors.py`, on throwaway test routes:
  - **Malformed JSON:** the body `{"a":` → status 400, `Content-Type: application/problem+json`, and a body exactly equal to the contract §1.3 `malformed-request` object, with no `errors` key.
  - Every other row of the table above. The 503 and 429 rows are tested in A3 and O3, where they first exist.
- `tests/api/test_query_parsing.py`: the full §2.5 matrix on a test route with a `QueryInt` parameter.
- `tests/api/test_body_parsing.py`: the full §2.6 matrix on a test route, including `true` and `false`.
- `tests/unit/test_json_decimal.py`: `Decimal("0.8333")`, `Decimal("10.0")`, `Decimal("0.40")` serialise to the JSON numbers `0.8333`, `10.0`, `0.4`; the raw text contains no quotes around them; the OpenAPI type is `number`.
- `tests/unit/test_envelope.py`; `tests/api/test_cors.py`; `tests/api/test_health.py::test_health`.

**Commit:** `feat(api): add problem+json errors, strict number types, illustrative envelope, CORS and /health`
**Results:** _to be filled in after the step is built._

### A3. Database connection, Alembic, safety guards, test lifecycle, seed framework, `/ready`
**Runs against:** the local PostgreSQL server managed through pgAdmin 4 (§2.9). **No Docker.** Prerequisites: the server is running; the role and three databases exist; `backend/.env` holds the three URLs.

**Builds**
- Declarative base with a constraint naming convention; a synchronous engine built from the URL resolved for the explicit target (§2.10).
- Migration `0001_seed_state`: the table `seed_state` (`dataset` PK, `methodology_version`, `content_hash`, `applied_at`).
- `app/db/safety.py`; `app/db/migrate.py` (the only Alembic entry point); `alembic/env.py`, which refuses to run without the wrapper's attributes; wired into both conftests, the seed CLI and `create_app`, exactly as §2.3 and §2.10.
- `backend/scripts/sql/create_local_databases.sql` (the §2.9 script, for pgAdmin's Query Tool; the role is `NOSUPERUSER`; the password is a placeholder).
- **Superuser rejection** in `app/db/safety.py` (§2.3): the user-name check before connecting, and the `rolsuper` check after connecting, failing closed.
- **Layering scaffold** (§2 item 4): the `app/repositories/` package with `seed_state.py`, the first repository (read the stored hashes; the seed framework writes them). `app/services/readiness.py` composes the `/ready` checks from the repositories and the guard; the router only calls it.
- **Startup version log** (§2.11): `create_app` logs `server_version_num` once, after the guard passes.
- **Seed framework** (`app/seed/`), run as `python -m app.seed --target <dev|test|production> [--check]` (the target is required):
  - Datasets are registered in code. Each one is Python literals, or is generated with `random.Random(20261024)`.
  - Each dataset's content hash is SHA-256 over its sorted, canonicalised rows.
  - One transaction per run, under `pg_advisory_xact_lock`. Version-scoped tables: delete the rows for version `0.1` (children first), then insert the full set. Global tables: upsert, then delete rows absent from the seed set. A delete blocked by a foreign key aborts the whole run.
  - When a dataset's stored hash already equals its code hash, it is skipped, so a run with nothing changed commits nothing.
  - `seed_state` is updated in the same transaction.
  - `--check` recomputes the hash **from the table contents**, not from `seed_state`, and exits non-zero on any mismatch.
- **`GET /ready`** (contract §2):
  - `database`: `SELECT 1` succeeds.
  - `migrations`: the database revision equals the head revision.
  - `seed`: every dataset registered in this build has a `seed_state` row with the expected hash.
  - **Pre-seed:** before F2, no datasets are registered, so `seed` is `ok` and `/ready` returns 200.
- `backend/scripts/start.sh`, Render's start command from A5 on (not used locally on Windows):
  ```
  set -eu
  python -m app.db.migrate --target production upgrade head   # guarded (§2.3)
  python -m app.seed --target production                     # guarded; idempotent
  exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --no-access-log --proxy-headers
  ```
  Any failure stops startup, so the process never answers `/health`. Local development uses the §2.9 PowerShell commands instead, with the same `--no-access-log`.
- `.gitattributes` forces LF on `*.sh`.
- `tests/conftest.py` and `tests/migrations/conftest.py` follow §2.2, §2.3 and §2.10.
- `backend/README.md` gains the pgAdmin setup steps and the migrate and seed commands.

**Tests**
- `tests/unit/test_db_safety.py`: every §2.3 rule and refusal, **including the superuser cases** (a `postgres` user name for every target; a stubbed `rolsuper = true` for every target; the role-check query failing or returning no row → refused).
- `tests/integration/test_superuser_refused.py`: the three real-server cases in §2.3. `postgres` is refused by name before connecting; the temporary non-`postgres` superuser is refused by `rolsuper` after connecting; `imibereho` is accepted. Each refusal is checked in `app.db.migrate`, `app.seed` and `create_app`, with the database left unchanged. All three run in CI from A4; the superuser cases are optional locally.
- `tests/unit/test_layering.py`, an AST import scan:
  - `api` imports nothing from `repositories` or `db.session`.
  - `repositories` import nothing from `services` or `api`.
  - `calculations` import nothing from `db`, `repositories`, `services`, `api`, `fastapi` or `sqlalchemy`.
  - Only `tests/integration/test_superuser_refused.py` mentions `SUPERUSER_POSTGRES_DATABASE_URL` or `SUPERUSER_ALT_DATABASE_URL`.
- **PostgreSQL 18 evidence (§2.11):** `SELECT version()` on `imibereho_test` and the full pytest summary are recorded in Results. 16-compatibility is explicitly marked "unverified until A4".
- `tests/migrations/test_round_trip.py`: `upgrade head` → `downgrade base` → `upgrade head`, then an empty autogenerate diff, on `imibereho_migrations` only.
- `tests/unit/test_seed_framework.py`, with a toy dataset registered in the test: second run is a no-op; a hand-inserted stale row is removed; a forced failure rolls back fully; `--check` detects drift; hashes are stable across runs.
- `tests/api/test_health.py`: `/ready` returns 200 with `checks` all `ok`; returns 503 problem+json `not-ready` with `"database":"failed"` when the session raises; and returns 503 with `"seed":"failed"` when a registered toy dataset's hash does not match.

**Commit:** `feat(db): add guarded database setup, seed framework, test lifecycle and /ready`
**Results:** _to be filled in after the step is built._

### A4. CI workflow
**Builds:** `.github/workflows/backend-ci.yml`, on `pull_request` and `push` to `main`, filtered to `backend/**`, `render.yaml`, `.gitattributes` and the workflow file.

**Database in CI:** a GitHub Actions `services: postgres` entry using the `postgres:16` image, with its port mapped to `localhost:5432`. GitHub runs that service on its own hosted runner. **It needs no Docker on any developer machine and adds no Docker files to the repo.** A setup step, connected as the service's built-in `postgres` superuser, creates:
- the `imibereho` role (`NOSUPERUSER NOCREATEDB NOCREATEROLE`), and the `imibereho_test` and `imibereho_migrations` databases owned by it;
- **a temporary CI-only superuser** `imibereho_ci_superuser` (`LOGIN SUPERUSER`), which exists only to prove the `rolsuper` rejection path with a name other than `postgres`.

**Temporary superuser credentials:**
- The password is **generated inside the job at run time** (e.g. `openssl rand -hex 32`). It is never written in the workflow file and never stored in GitHub Secrets or the repository.
- It is masked in logs with `::add-mask::` and exported only to later steps of the same job through `$GITHUB_ENV`, as `SUPERUSER_ALT_DATABASE_URL`.
- It exists only on the job's ephemeral service database, which GitHub destroys when the job ends. A final `if: always()` step also runs `DROP ROLE IF EXISTS imibereho_ci_superuser` for hygiene.
- **No application step uses it:** it is not a target (§2.10), the guard refuses it anyway, and `test_layering.py` confines it to the integration test file.

`SUPERUSER_POSTGRES_DATABASE_URL` uses the service's built-in `postgres` user.
- **Its password works differently from the temporary superuser's.** GitHub starts service containers before any job step runs, so the built-in password must be set in the workflow's service definition (`POSTGRES_PASSWORD`). That makes it **visible in the committed workflow file**: a throwaway value valid only for that job's ephemeral container, which is reachable only from the runner and destroyed at job end.
- If the repo admin prefers, it can instead be read from a GitHub Actions secret (`${{ secrets.CI_PG_PASSWORD }}`); the tests are unaffected.
- It is not a development, test or production credential, and the application never uses it.

Environment for the test steps: `ENVIRONMENT=ci`; `TEST_DATABASE_URL` and `MIGRATIONS_DATABASE_URL` pointing at `localhost` **as `imibereho`**; and the two `SUPERUSER_*` variables, so all three superuser integration cases always run. The CI job log records the service's `SELECT version()` (16) as §2.11 evidence. **`DATABASE_URL` is deliberately unset in CI**, so nothing can reach a development or production database.

Steps:
1. `astral-sh/setup-uv`, then `uv python install 3.12`, then `uv sync --frozen`.
2. `uv run ruff check`, `uv run ruff format --check`.
3. `uv run mypy app tests`.
4. Migration round trip (guarded): `app.db.migrate --target migrations`: `upgrade head` → `downgrade base` → `upgrade head` → `check`.
5. Seed repeatability: `app.db.migrate --target test upgrade head`; `app.seed --target test` twice (the second must report every dataset skipped); `app.seed --target test --check`.
6. `uv run pytest --cov=app --cov-fail-under=85` **[GATE]**, including `tests/migrations` and `tests/contract`.

There is no image build step: that belongs to C1 (§4.2).

**Contract tests (introduced here)**
- `tests/contract/endpoints.py` holds two constants:
  - `CONTRACT_ENDPOINTS`: every `(method, path)` pair in contract v0.2 rev 2 §2–§6, core and optional, transcribed once and updated only when the contract changes.
  - `IMPLEMENTED_ENDPOINTS`: the pairs shipped so far. In A4 that is `GET /health` and `GET /ready`; each later step appends its own.
- `test_contract_paths.py` asserts:
  1. The app's routes (excluding `/docs`, `/redoc` and `/openapi.json`) **equal `IMPLEMENTED_ENDPOINTS`**, so a step cannot ship an unregistered route.
  2. **`IMPLEMENTED_ENDPOINTS ⊆ CONTRACT_ENDPOINTS`**, so every shipped path is documented.

  It never requires future endpoints to exist.
- `test_openapi_snapshot.py` compares `app.openapi()`, as normalised JSON, with `openapi.snapshot.json`, which is regenerated deliberately by `scripts/dump_openapi.py`.

Branch protection requires the repo admin (see "Blockers").
**Commit:** `ci(backend): run lint, types, guarded migrations, seed repeatability, contract tests and coverage`
**Results:** _to be filled in after the step is built._

### A5. Early Render deployment
**Builds**
- `render.yaml`:
  - Web service `imibereho-api` on Render's **native Python runtime** (`runtime: python`; **no Docker**):
    - `rootDir: backend`.
    - `buildCommand: pip install uv && uv sync --frozen --no-dev` **[ASSUMPTION: confirm in A5 whether Render installs from `uv.lock` natively; this command works either way]**.
    - `startCommand: bash scripts/start.sh`.
    - Environment variable `PYTHON_VERSION=3.12.8`.
    - Region `frankfurt` **[ASSUMPTION: confirm the closest available region]**.
    - **`healthCheckPath: /health`**.
    - `numInstances: 1`.
    - Auto-deploy on every push to `main`.
  - Database `imibereho-db`: PostgreSQL 16.
  - Environment: `ENVIRONMENT=production`, `DATABASE_URL` from the database, and `CORS_ORIGINS` = `http://localhost:5173` plus the frontend origin once supplied.
- **Docker is not needed for A5.** If the native runtime cannot build or run the service, and only then, C1 (§4.2) is pulled forward as the A5 fallback, with your approval.
- **Why `/health`:** `scripts/start.sh` runs migrations and the seed before uvicorn starts, so `/health` answering already proves startup succeeded. A failed migration or seed means `/health` never answers and Render keeps the previous deploy. `/ready` (200 pre-seed, contract §2) is checked by the smoke test, not by Render, so a readiness failure can never block a deploy by itself.
- `scripts/smoke.py <base-url>`, in A5: `/health` returns 200; `/ready` returns 200 with all checks `ok`; a CORS preflight from `http://localhost:5173` succeeds. Each later step adds its endpoint with the §2.4 values.
- Confirm the PostgreSQL logging default (§2.8).
- Record Render's `SELECT version()` and confirm that its database user has `rolsuper = false` (§2.3, §2.11). If the version is not 16, or the user is a superuser, stop at the §2.11 decision point and ask for approval.

**Tests:** the smoke script against the live URL, with its output recorded in Results.
**Commit:** `feat(deploy): add Render blueprint with liveness health check, auto-deploy and smoke script`
**Results:** _to be filled in after the step is built._

---

## 4. Feature steps (core, in build order)

Every step also performs §2 item 9 (adds its endpoints to `IMPLEMENTED_ENDPOINTS` and regenerates the snapshot) and extends `smoke.py`.

### F1. Calculation module
**Endpoints:** none. **Tables:** none.
Pure functions in `app/calculations/`. Money is `int`; ratios and runway are `Decimal` with `ROUND_HALF_UP`, emitted later through `JsonDecimal`. Rounding is **[PD] Q-17**; the BR formulas are unchanged.

| Function | Rule | Exact specification |
|---|---|---|
| `monthly_balance(income, essentials, support=0)` | BR-01 | `income + support − essentials` |
| `shocked_income(income, pct)` | BR-02 | `(income * (100 - pct) + 50) // 100` (integer half up; every operand ≥ 0) |
| `monthly_gap(essentials, shocked, support=0)` | BR-03 | `max(0, essentials − (shocked + support))` |
| `savings_drawdown(savings, gap, months)` | BR-04, BR-05 | `used = min(savings, gap*months)`; `remaining = savings − used`; `exhausted = gap*months > savings` |
| `runway_months(savings, gap)` | BR-06 | `None` if `gap == 0`, else `Decimal(savings)/gap` quantised to `0.1`, half up |
| `savings_after_horizon(savings, net, months)` | BR-07 | `savings + months*net`, as written; may be negative (contract §5) |
| `direct_transfer_budget(support, households, months)` | BR-08 | the product of the three |
| `vulnerability_score(components, weights)` | BR-09, BR-16 | `Σ weight × value`; the weights must sum to exactly `Decimal("1.00")` |
| `vulnerability_band(score, bands)` | BR-10 | the band whose `min ≤ score ≤ max` |
| `ratio(num, den)` | BR-11, BR-12 | `None` if `den == 0`, else quantised to `0.0001`, half up |
| `budget_comparison(plan, reference)` | BR-13 | used only by O2; ties by category order **[PD] Q-09** |
| `swap_difference(price_from, price_to)` | BR-14 | `price_from − price_to` |
| `is_in_deficit(income, essentials, pct)` | BR-03 / BR-12 helper | `monthly_gap(essentials, shocked_income(income, pct)) > 0` |

**SQL equivalence.** The only aggregate computed in SQL is the deficit count. Its predicate:
```sql
monthly_essentials > (monthly_income::bigint * (100 - :pct) + 50) / 100
```
Postgres integer division truncates, which equals floor for non-negative operands, matching the Python `//`. Ratios are never computed in SQL.

**Tests**
- `tests/unit/test_calc_*.py`: a `test_design_values` test for every §2.4 value, plus the derived edge cases:
  - Reductions of 0% and 100%.
  - Income 180,001 at 20% → 144,001.
  - Gap 0 → runway `None`.
  - Savings 0 with a gap → runway 0.0 and exhausted.
  - 45,000 ÷ 6,000 → 7.5; 10,000 ÷ 3,000 → 3.3.
  - Negative BR-07 returned unchanged.
  - Weights summing to 0.99 → error.
  - Band boundaries 0, 39, 40, 59, 60, 69, 70, 100.
  - A zero denominator → `None`.
  - BR-13 ties.
  - BR-08 at 100,000,000 × 3,000 × 24.
- `tests/unit/test_calc_sql_equivalence.py`, on `imibereho_test` through the §2.2 fixture. It compares the SQL predicate with `is_in_deficit` row by row over the derived boundary set: income 180,001 with essentials 144,001 and 144,002; essentials equal to shocked income; income 0; pct 0 and 100; income 100,000,000.

**Commit:** `feat(calc): add methodology v0.1 calculations with SQL-equivalent rounding`
**Results:** _to be filled in after the step is built._

### F2. Reference data
**Endpoints** (contract §3): `GET /api/v1/districts`, `GET /api/v1/expense-categories`.

**Tables (migration `0002_reference_data`)**

| Table | Columns and constraints |
|---|---|
| `methodology_versions` | `version` PK; `status` CHECK `'concept'`; `status_note`; `is_current` with a partial unique index |
| `districts` | `code` PK CHECK `^[a-z]+$`; `name` UNIQUE; `name_rw` NULL; `province` NULL; `sort_order` UNIQUE |
| `expense_categories` | `code` PK; `name_en`; `name_rw` NULL; `icon` NULL; `sort_order` UNIQUE |
| `reference_households` | PK/FK `methodology_version`; `district_code` FK; `household_size` 1–20; `monthly_income`, `monthly_essentials`, `savings` ≥ 0 |

**Seed datasets** (registered from F2 on, so `/ready` now covers them):
- Methodology `0.1` with the status note from `2:7331`.
- The 30 districts in `2:6965` order.
- The 5 categories (`2:6530`–`2:6558`), with icons per contract §3 **[PD] Q-11**.
- The reference household: Gasabo, 4 people, 180,000 / 150,000 / 60,000 ([E] `2:6430`, `2:6440`, `2:6628`, `2:7209`).

**Tests:** contract §3 examples; 30 items starting with `bugesera`; the category order and icons; any query parameter → 400 `unknown-parameter`; `meta.count` is an integer; seed idempotence for these datasets; `/ready` still 200 after seeding.
**Commit:** `feat(reference): add districts, expense categories and reference household`
**Results:** _to be filled in after the step is built._

### F3. Budget benchmarks
**Endpoint** (contract §4): `GET /api/v1/budget-benchmarks`.
**Table (migration `0003_budget_benchmarks`):** `budget_benchmarks` with PK (`district_code`, `household_size`, `category_code`, `methodology_version`) and FKs; `monthly_amount` ≥ 0.
**Seed:** the `2:6534` column for every district at household size 4 **[PD] Q-32**; every seeded pair has all 5 categories.
**Tests:**
- The design values.
- Unknown district → 404 `district-not-found`.
- Size 3 → 404 `benchmark-not-available`.
- The §2.5 matrix on `householdSize` (including `21` → `out_of_range`).
- Missing `district` → 422 `required`.
- **Size 0 with an unknown district → 422, not 404** (validation before lookup).

**Commit:** `feat(citizen): add budget benchmarks endpoint`
**Results:** _to be filled in after the step is built._

### F4. Household shock
**Endpoint** (contract §4): `POST /api/v1/calculations/household-shock`. **Tables:** none.
**Rules:** contract §4; BR-01 to BR-06 via F1; `savingsExhausted` **[PD]**; runway **[PD] Q-17**; `type` accepts `income_fall` only **[PD] Q-10**.
**Tests:**
- Design values: 30,000 / 144,000 / 6,000 / 18,000 / 42,000 / 10.0 / `false`.
- Reduction 0 → gap 0 and `runwayMonths: null`.
- Savings 0 → runway 0.0 and `savingsExhausted: true`.
- The §2.6 matrix on all five integer fields (including `true` and `false` → `not_integer`).
- `incomeReductionPct` 101 → 422 at `shock.incomeReductionPct`.
- `type: "price_rise"` → `unknown_value`.
- An extra body field → `unknown_field`.
- Malformed JSON → the exact 400 body.
- §2.7: `runwayMonths` is a JSON number (`10.0`) and every money field is an integer.
- Privacy: the body never appears in the app logs.

**Commit:** `feat(citizen): add household shock calculation endpoint`
**Results:** _to be filled in after the step is built._

### F5. Seasonal swaps
**Endpoint** (contract §4): `GET /api/v1/seasonal-swaps`.

**Tables (migration `0004_seasonal`)**
- `seasonal_swaps`: slug PK; `methodology_version` FK; `district_code` FK NULL (NULL means all districts); `month` 1–12; text fields; from/to `name`, `quantity` NUMERIC(6,2) > 0, `unit`, `price` INT ≥ 0; `sort_order`. Index (`month`, `district_code`).
- `seasonal_tips`: the same keys, with a nullable `month`.

**Seed:** the rice → sweet potato swap, month 10, district NULL, text verbatim from `2:6698`; the tip from `2:6714` **[PD] Q-32**.
**Tests:**
- Gasabo in month 10 → the design values with `difference` 400.
- Nyagatare in month 10 → the same swap.
- Month 3 → `items: []` plus the tip.
- Unknown district → 404.
- The §2.5 matrix on `month` (`13` → `out_of_range`).
- §2.7: `quantity` is a JSON number (`1`, `2`).

**Commit:** `feat(citizen): add seasonal swaps endpoint`
**Results:** _to be filled in after the step is built._

### F6. Decision-maker dataset
**Endpoints:** none.

**Tables (migration `0005_dm_dataset`)**
- `reference_periods`, `household_groups`.
- `synthetic_households`: `id`; `methodology_version`; `district_code`; `household_size`; `primary_income_source` ENUM; `monthly_income`, `monthly_essentials`, `savings` INT ≥ 0.
- `monthly_series`.
- `vulnerability_models`: three NUMERIC(3,2) weights, CHECK sum = 1.00 (BR-16).
- `vulnerability_bands`.
- `district_vulnerability`: three components 0–100, `score` NUMERIC(5,2) 0–100, and an index for ranking.

**Seed: values from the design**
- Period `2026-10`, "Demo month · October" (`2:6783`; the year is **[ASSUMPTION]**).
- Group `all` (`2:6788`).
- Trend from `2:6826` **[PD] Q-33**.
- Weights from `2:7355`.
- Bands from `2:7061`.
- The 30 scores from `2:6965`.
- Gasabo's components, 50 / 40 / 50 (`2:7079`).

**Seed: invented synthetic inputs [SYN]** (labelled in the seed file header and covered by `meta.isIllustrative`)
- **Components for the 29 other districts:** integer triples (a, b, c), each 0–100, with `2a + 2b + c = 5 × score`, so that BR-09 reproduces each design score. The design itself says "Inputs and weights are invented for this prototype" (`2:7097`).
- **3,000 households** (`2:6793`), generated with `random.Random(20261024)`:
  1. **District:** 100 per district (an arbitrary even split).
  2. **Income source:** a seeded shuffle, then slices of 1,200 `wage`, 1,050 `agriculture` and 750 `informal_enterprise` (`2:6864`), independent of district.
  3. **Deficit flag:** a separate seeded shuffle picks exactly 1,000 households (`2:6805`), **independent of district, vulnerability score and income source**. Nothing in the generator reads vulnerability data.
  4. **Amounts:** household size 1–8; income 40,000–600,000 in steps of 1,000; savings 0–300,000 in steps of 1,000. Essentials are drawn so that `is_in_deficit(income, essentials, 20)` equals the flag from step 3. All ranges here are **[SYN]**.
- **Seed aborts** unless: the counts are 3,000 / 1,200 / 1,050 / 750 / 1,000; every D2 score is reproduced by BR-09; Gasabo's components are 50 / 40 / 50; the weights sum to 1.00; the bands cover 0–100 with no gaps.

**Tests:**
- `tests/unit/test_synthetic.py`: the counts; a deterministic hash; independence (the generator module does not import the vulnerability seed data); every row's flag matches `is_in_deficit`.
- `tests/unit/test_dm_seed.py`: the design values above, read from the seeded `imibereho_test`.

**Commit:** `feat(dm): add synthetic household sample, demo series and vulnerability model v0.1`
**Results:** _to be filled in after the step is built._

### F7. District vulnerability
**Endpoints** (contract §5): the list and the detail.
**Rules:** scores are integers **[PD] Q-17**; ties are broken by name; band keys only.
**Tests:**
- All 30 scores and bands, alphabetically.
- `sort=-score&limit=6` matches `2:7102`.
- The Gasabo detail (`2:7079`).
- `sort=score` → 422 `unknown_value`.
- The §2.5 matrix on `limit` (`31` → `out_of_range`).
- **`period=2026-09` → 422 `unknown_value`, and `householdGroup=wage` → 422 `unknown_value`, on both the list and the detail.**
- Detail with an invalid `period` **and** an unknown district → 422 (validation before lookup).
- Unknown district → 404.
- `Gasabo` (upper case) → 404.
- §2.7: `score` is an integer; `weights.*` and `components[].weight` are JSON numbers (`0.4`).

**Commit:** `feat(dm): add district vulnerability endpoints`
**Results:** _to be filled in after the step is built._

### F8. Policy scenario
**Endpoint** (contract §5): `POST /api/v1/calculations/policy-scenario`.
**Rules:** contract §5. BR-07 as written (may be negative); `eligibleHouseholds` bounded by the seeded sample size (3,000); an omitted `baseline` uses the reference household **[PD] Q-23**; nothing stored **[PD] Q-19**.
**Tests:**
- The full `2:7233` matrix plus 18,000,000 and 0.
- `baselineUsed.source` for an omitted and a supplied baseline.
- A derived negative-savings case.
- `eligibleHouseholds` 3,001 → `out_of_range`.
- The §2.6 matrix on every integer field, including the nested `baseline` fields (`true` → `not_integer`).
- `instrument: true` → 422 `unknown_value`.
- `unknown_field`.
- Malformed JSON → the exact 400 body.

**Commit:** `feat(dm): add policy scenario calculation endpoint`
**Results:** _to be filled in after the step is built._

### F9. Dashboard filters and overview
**Endpoints** (contract §5), `geography=all` only **[PD] Q-14**.
**Rules:** counts come from SQL in `repositories/dashboard.py` (the deficit count uses the F1 predicate); `services/dashboard.py` turns them into shares and ratios with Python `ratio()`; the reference household, trend and insight come from F2 and F6; `topDistricts` reuses the F7 ranking.
**Tests:**
- Design values: 3,000; 0.8333; 1,000 / 0.3333; 1,200 / 1,050 / 750 with 0.4 / 0.35 / 0.25; insight 30,000 / 6,000; Nyagatare 74 and Bugesera 71.
- `/dashboard/filters` returns `code` in every list (`periods[0].code == "2026-10"`).
- `geography=gasabo` → 422 `unknown_value`; `geography=atlantis` → 422 `unknown_value` (never 404).
- `period=2026-09` → 422; `householdGroup=wage` → 422.
- The §2.5 matrix on `topN`.
- §2.7: every ratio and share is a JSON number.
- **SQL equivalence over the seeded data:** the SQL deficit count equals the number of seeded rows where Python `is_in_deficit` is true, both 1,000.

**Commit:** `feat(dm): add dashboard filters and overview endpoints`
**Results:** _to be filled in after the step is built._

### F10. Demo hardening
**Builds:**
- Security headers: `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and `Cache-Control: no-store` on POST calculation endpoints.
- `smoke.py` covers every core endpoint with the §2.4 values.
- A demo checklist in `backend/README.md`: warm the service and check `/ready` before the demo; the expected values per screen; the rollback steps.
- The final CORS origins are confirmed.

The Render health check stays on `/health`.
**Tests:** `tests/api/test_security_headers.py`; a smoke run against Render, recorded in Results.
**Commit:** `feat(deploy): harden headers and add full smoke test`
**Results:** _to be filled in after the step is built._

## 4.1 Optional steps (only after F10 is merged; cut from the bottom of §1 upward)

| Step | Scope (contract §6) | Tables | Key tests |
|---|---|---|---|
| O1 `GET /demo-household` **[PD] Q-05/Q-06** | profile, plan and expenses | `demo_plan_lines`, `demo_expenses` (version-scoped seed datasets) | The `2:6533` plan totals 150,000, equal to the reference essentials; the 3 expenses from `2:6444` |
| O2 `POST /calculations/budget-comparison` **[PD] Q-09** | differences, largest above and below | none | Design: Housing +5,000 and Food −5,000 (`2:6571`); a duplicate or missing category → 422; an unknown `district` → 404; the §2.6 matrix |
| O3 Rate limiting | in-memory per-IP fixed window, 60 a minute, on `POST /calculations/*`; single instance | none | The 61st request → 429 problem+json `rate-limited` with `Retry-After` (this is where the contract §1.3 429 row is first tested) |
| O4 `GET /methodology` **[PD] Q-12** | structured data only | `methodology_data_sources` | The 4 rows from `2:7357` with their statuses; weights and bands equal to F7's; §2.7 numbers |

O5 (per-district geography) is **not planned** without a decision on Q-14 / Q-18.

## 4.2 Containerisation phase (deferred)

**Which steps actually require Docker:**

| Step | Requires Docker? | Why |
|---|---|---|
| A1–A3, F1–F10, O1–O4 | **No** | Local development uses uv and the pgAdmin-managed local PostgreSQL server (§2.9) |
| A4 (CI) | **No local Docker** | GitHub runs the `postgres:16` service on its own hosted runner; no Docker files are in the repo |
| A5 (Render) | **No** | Render's native Python runtime builds with uv and runs `scripts/start.sh` |
| C1 | Yes | This is the containerisation step itself |

**C1. Containerisation** (branch `feat/step-c1-containerisation`), **deferred**:
- **When:** after the demo by default. Before the freeze only if the A5 native runtime fails and you approve pulling it forward as the fallback.
- **Prerequisite:** Docker Desktop on the development machine (not needed before C1).
- **Builds:**
  - `backend/Dockerfile`: multi-stage, Python 3.12 slim, `uv sync --frozen --no-dev`, non-root user, `CMD ["bash", "scripts/start.sh"]`.
  - `backend/.dockerignore`.
  - `docker-compose.yml` with `api` and `postgres:16` for local parity with Render. Compose database URLs must still satisfy the §2.3 guards: database names exact, host `localhost` through a mapped port.
  - CI gains a `docker build backend` step.
  - Optionally, `render.yaml` switches to `runtime: docker`.
- **Unchanged by C1:** the stack, the API contract, the guards, `--no-access-log` and every security requirement.
- **Tests:** the image builds in CI; the smoke test passes against a locally run container.

---

## 5. Schedule

Small PRs throughout. Approving A1–A3 as a batch on day 1 is recommended.

| Day (2026) | Steps | End-of-day target |
|---|---|---|
| **Sat 24 Oct** | Resolve the blockers (push access; install uv; Python 3.12; start the local PostgreSQL server; create the role and three databases in pgAdmin; decide on 18 vs 16); plan approval; docs PR; A1, A2, A3 | The server runs locally with `uv run uvicorn` against the pgAdmin-managed `imibereho` database; the guards and the seed framework are tested. **No Docker involved** |
| **Sun 25 Oct** | A4, **A5 (deployed by midday)**, F1, F2 | The Render URL is live with `/health`, `/ready`, `/districts` and `/expense-categories`; the URL and the contract go to the teammate |
| **Mon 26 Oct** | F3, F4, F5, F6 | All citizen endpoints live; the DM dataset seeded on Render |
| **Tue 27 Oct** | F7, F8, F9, F10 | **The core demo is complete and deployed**; the full smoke test passes |
| **Wed 28 Oct** | Integration fixes until 12:00; then O1 → O4 as time allows; **code freeze 16:00** | Demo-ready |

**If the push-access blocker is not resolved on 24 Oct, every date shifts.** A1–A3 can still be written locally, but none can be merged, and A5 cannot deploy from `main`.
**Cut line:** O4, then O3, then O2, then O1. Each has a frontend fallback (contract §6).
**Smallest acceptable demo:** A1–A5 and F1–F9 deployed with CORS and smoke-tested. The frontend hardcodes D4, the demo household and the C3 differences.

---

## 6. Open questions with proposed defaults

**Approving the plan accepts each default.** Each one is safe: overturning it later is additive or data-only, with no schema rework.

| ID | Proposed default **[PD]** | Rework if overturned |
|---|---|---|
| Q-03 | **English only; `name_rw` columns exist but are NULL; `Accept-Language` is ignored; responses carry `Content-Language: en`.** | Data only |
| Q-05 / Q-06 | **The demo household is served by optional O1; otherwise the frontend bundles it.** | None |
| Q-09 | **Largest above and below by absolute difference, ties by category order; the frontend writes the sentence.** | O2 only |
| Q-10 | **`income_fall` and `monthly_cash_support` only.** | Enum addition |
| Q-11 | **One fixed list of 5 categories; `icon: null` for Housing and Other essentials.** | Data only |
| Q-12 | **D4 prose is frontend copy; structured data comes from optional O4.** | O4 only |
| Q-14 | **Period `2026-10`, group `all`, geography `all` only. O5 is not planned.** | O5 is additive |
| Q-16 | **Citizen calculations run on the server, statelessly, with no body logging. The frontend computes BR-01 and BR-15 for display. Product to confirm the C1 wording "does not collect" (`2:6407`).** | None for the backend |
| Q-17 | **Integer half-up for money (identical in Python and SQL); runway to 1 dp, `null` at gap 0; ratios to 4 dp; integer scores; BR-07 as written (may be negative); `savingsExhausted` on household-shock; every number emitted as a JSON number.** | Serialisation only |
| Q-18 | **Store the 3,000 synthetic households and count in SQL.** | — |
| Q-19 | **Scenarios are never stored.** | — |
| Q-20 | **Household size 1–20; percentages 0–100; duration 1–24; money 0–100,000,000; eligible households 0–3,000; integer formats per contract §1.2.** | Bounds only |
| Q-21 | **No provinces.** | Data only |
| Q-22 | **The frontend selects Gasabo by default.** | None |
| Q-23 | **An optional baseline override; the reference household otherwise.** | — |
| Q-24 | **Public workspace with a CORS allowlist; rate limiting is optional (O3).** | — |
| Q-32 | **One illustrative benchmark set at household size 4 for every district; swaps apply to every district.** | Data only |
| Q-33 | **One reference-household trend series.** | Data only |

Questions with **no backend impact** under the resolved decisions: Q-07, Q-08, Q-25 and Q-31 (device-only data under Q-02); Q-13 (open again since the 2026-10-28 citizen accounts; see open-questions); Q-27, Q-28, Q-29 and Q-30 (frontend).

---

## 7. Risks and notes

| Risk | Impact | Mitigation |
|---|---|---|
| **No push access** (`push: false`) | No PR can be opened, so the schedule cannot start | Resolve before A1 (Blockers) |
| The F6 generator misses an exact count | D1 values drift from the design | Counts assigned by construction; the seed aborts on any mismatch |
| Python and SQL deficit logic diverge | D1 shows a count other than 1,000 | One rounding expression, BIGINT operands, equivalence tests in F1 and F9 |
| Decimals serialised as strings | The frontend receives `"0.8333"` | `JsonDecimal` (A2) and the §2.7 raw-text assertions in every step |
| A migration or downgrade hits the wrong database | Data loss | §2.3 guards in `env.py`, both conftests and the seed CLI; tested by `test_db_safety.py` |
| Synthetic numbers read as findings | Misleading planning signals | **[SYN]** labels; `meta.isIllustrative`; no per-district aggregates; the design's caveats (`2:7083`, `2:6861`) |
| Render setup issues | Late deployment | A5 on 25 Oct; liveness health check; auto-deploy; C1 as the fallback if the native runtime fails |
| Local PostgreSQL 18 vs provisional 16 for CI and Render | A version-specific behaviour difference | §2.11: SQL limited to features common to 16 and 18; CI on 16 gates every merge from A4; version evidence recorded in A3, A4 and A5; decision point in A5 |
| A superuser connection slips through (for example a misconfigured `.env` or a Render default role) | Over-privileged access; accidental DDL outside migrations | §2.3 two-stage superuser rejection, failing closed; unit and integration tests; the role created as `NOSUPERUSER`. **[ASSUMPTION: Render's default database user is not a superuser; confirm in A5, because the guard would refuse to start otherwise]** |
| Local server stopped, or databases missing | A3 cannot run tests | One-time pgAdmin setup (§2.9); the guards fail with a message naming the missing database or variable |
| Free-tier sleep or database expiry **[ASSUMPTION]** | Cold start during the demo | A paid instance for demo week, or warm before the demo |
| Late frontend integration | Mismatches on 28 Oct | The contract and the live URL from 25 Oct; snapshot and path tests |
| Review latency on 15 core PRs | Steps queue up | Small PRs; batch approval of A1–A3 |
| C1 privacy wording vs transient processing (Q-16) | Product credibility | No storage and no body or query logging (§2.8); product confirms the wording |
| Query strings in the Render platform logs | Household size and district visible to the platform | No money values in query strings (contract §1); documented in §2.8 |
| Seed text drift from Figma | Wording differences | Re-check the F5 strings against `2:6698` and `2:6714` before freeze |
| The format example is missing | The format may differ from what you expected | Re-align when it is added |

---

## 8. Change log

### v2.3.1 (superuser integration test, 2026-10-24)
Draft v2.3 direction approved. One narrow change to the test plan:
1. The real-server integration test is split into three cases: the `postgres` user name refused before connecting (`superuser_name`); a **temporary CI-only superuser with a non-`postgres` name** refused by the `rolsuper` check (`superuser_role`); and the `imibereho` role accepted (§2.3, A3).
2. The guard's refusals carry reason codes (`superuser_name`, `superuser_role`, `role_check_failed`), so tests prove which check fired.
3. `SUPERUSER_DATABASE_URL` is replaced by `SUPERUSER_POSTGRES_DATABASE_URL` and `SUPERUSER_ALT_DATABASE_URL`. Both are test-only, never targets, and not `Settings` fields (§2.10).
4. CI creates the temporary superuser with a password generated and masked at run time, never committed or stored, and dropped at job end (A4).
5. The stubbed unit tests are kept, and each now states what it proves (§2.3).

### v2.3 (architecture and database adjustments, 2026-10-24)
No change to the API contract, the feature scope or the security requirements; the security requirements are strengthened.
1. **Repositories layer:** `app/repositories/` holds database queries only, read-only for the API. Services handle business rules and orchestration; routers call services only; calculations stay pure. Enforced by `tests/unit/test_layering.py` from A3 (§2 item 4, §3, A3, F9).
2. **Superuser rejection:** the guard refuses PostgreSQL superusers for every target, by user name before connecting and by `rolsuper` after connecting, failing closed. Unit tests for every target, plus an integration test that always runs in CI with a real superuser (§2.3, §2.10, A3, A4). The local role SQL now states `NOSUPERUSER NOCREATEDB NOCREATEROLE`.
3. **PostgreSQL versions:** 18 for local development (decided); 16 for CI and deployment (provisional), with compatibility rules and recorded evidence in A3, A4 and A5, and a decision point in A5 (§2.11).
4. Blockers updated with verified facts: uv 0.13.5 installed; the local PostgreSQL 18 service running on port 5432. Push access is unchanged (not re-verified in this pass).

### v2.2 (local-development correction, 2026-10-24)
Restores the established decision: local PostgreSQL managed through pgAdmin 4 for development; Docker and Compose deferred. No change to the stack, the API contract, the feature scope or the security requirements.
1. Docker and Compose removed from A1–A3, A4 and A5. They now live only in the deferred C1 step (§4.2), which also records which steps need Docker (none of the core steps).
2. New §2.9 for local setup: Python 3.12, uv, the local PostgreSQL server, and the pgAdmin one-time SQL for the role and three databases.
3. New §2.10 for connection configuration: three variables, each mapped to one target; no defaults; no fallbacks; one `Settings` source; `create_app(target)`.
4. §2.3 guards: hosts restricted to `localhost`, `127.0.0.1` and `::1` outside production; production must **not** be local. Alembic runs only through `app.db.migrate --target`, and `env.py` refuses to run without it. This removes the earlier reliance on reading the command from Alembic internals.
5. A5 uses Render's native Python runtime; `docker/start.sh` becomes `backend/scripts/start.sh`.
6. CI uses GitHub's hosted PostgreSQL 16 service with `DATABASE_URL` unset; the image build step moves to C1.
7. Blockers updated: local server stopped, PostgreSQL 18 installed vs 16 agreed, role and databases not yet created; uv is required (the pip fallback is removed).

### v2.1 (readiness check, 2026-10-24)
1. `/ready` reconciled with the contract: a `checks` object; a pre-seed build passes the seed check trivially; the seed check covers only the datasets registered in the build (backed by the `seed_state` table). Render's health check is `/health`, so `/ready` can never block a deploy.
2. A2 maps `json_invalid` → 400 `malformed-request` with an exact-body test.
3. `JsonDecimal` guarantees JSON numbers, tested on raw response text (§2.7). `QueryInt` enforces `^[0-9]+$`, with the full §2.5 matrix.
4. The contract path test is now incremental: routes equal `IMPLEMENTED_ENDPOINTS`, which is a subset of `CONTRACT_ENDPOINTS`.
5. `--no-access-log` in `start.sh` (v2.2: in `backend/scripts/start.sh` for Render and in the local run command; Compose deferred to C1). §2.8 documents what each log source may contain.
6. 404 `district-not-found` is narrowed to the `district` and `districtCode` parameters; `geography` is always 422; validation runs before lookup.
7. Tests added for booleans in integer fields (§2.6; F4, F8), invalid `period` and `householdGroup` (F7 list and detail, F9), and `geography=atlantis` (F9).
8. Enforceable database guards (§2.3) in Alembic `env.py`, both conftests and the seed CLI, with their own tests. An unknown target or command is refused.
9. Test data lifecycle (§2.2): migrate, then seed, then check, before any test. Quality gates have explicit start steps (§2.1).
10. Blockers section added: push access, uv, Python 3.12.
11. `fastapi>=0.115` pinned for query-parameter models.

### v2 (pre-implementation review, 2026-10-24)
1. CORS moved into A2.
2. A5: an early Render deployment.
3. Optional features moved behind core as O1–O4; O5 not planned.
4. Python and SQL rounding unified.
5. Deficit selection made independent of vulnerability scores.
6. Lax query integers and strict body integers.
7. An isolated migrations database.
8. Seed framework with version-scoped replace.
9. OpenAPI snapshot.
10. Labels added; BR-07 kept as written.
11. Dependency column; schedule.
12. The contract made the single source of truth.
