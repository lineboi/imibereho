# Backend quality audit: reliability, scalability, maintainability, robustness

> **Date:** 2026-10-29. **Scope:** `backend/` only, at `main` = `921734a` ("Merge pull request #12"). Audit only: no application code, contract or business rule was changed. **Auditor:** Claude Code, at the project owner's request.
>
> **Confidence labels:** **confirmed** (reproduced or measured here), **strongly evidenced** (code and a partial measurement agree; the end state was not reproduced), **unverified risk** (plausible from the code; no evidence of it happening).

## 1. Executive summary

The backend is in good shape for a demo: 41 operations, strict typing, RFC 9457 errors throughout, guarded database targets, privacy-safe logging, and 1,180 passing tests locally (1,182 with no skips in CI, 97.16% coverage). Account isolation holds: every account-scoped query filters on the token's account id, and tests cover cross-account access. No SQL injection surface was found (all queries are SQLAlchemy expressions or bound `text()`).

The material risks are about **resource exhaustion on public endpoints** and **deployment readiness**, not correctness:

| ID | Severity | Title | Confidence |
|---|---|---|---|
| H-1 | High | No request-size limit; the unbounded `activeCopingLevers` list amplifies a 1.9 MB request into a 10 MB response and 8.5 s of CPU, unauthenticated | confirmed |
| H-2 | High | No rate limiting or concurrency cap on `register`/`login`: each call costs 64 MiB and 81–124 ms of Argon2 work, and credential guessing is unlimited | strongly evidenced |
| M-1 | Medium | Authenticated writes hold two pooled connections, and register/login hold one during Argon2; the pool is 10 per process against 40 worker threads | confirmed (2 connections); exhaustion not load-tested |
| M-2 | Medium | No defined production start procedure (migrate, seed, serve) and no production CORS origin | confirmed |
| M-3 | Medium | The public OpenAPI description says "No account is needed and no citizen data is stored", which is false since contract v0.5 | confirmed |
| L-1 … L-6 | Low | Tracker 500 on a vanished account; 500 instead of 503 on database outage or pool timeout; no statement timeout; no `hide_parameters`; stale docstrings; stored plans tied to the current lever catalogue | see §4 |

**Recommended first fix: H-1** (small, contained, measurable; see §7).

## 2. Endpoint inventory

Generated from the application's routes and OpenAPI schema (`create_app`, stub settings) on 2026-10-29. "Bearer" means the operation declares the `bearerToken` scheme and depends on `CurrentAccountDep` (`app/services/current_account.py`). Router → service → repository → model layering is enforced by `tests/unit/test_layering.py`.

| Method | Path | Auth | Request body | Success response | Implementation |

|---|---|---|---|---|---|

| GET | `/api/v1/agro/harvest-calendar` | public | — | 200 `HarvestCalendarResponse` | `app/api/v1/endpoints/agro.py` |

| POST | `/api/v1/auth/login` | public | `LoginRequest` | 200 `LoginResponse` | `app/api/v1/endpoints/auth.py` |

| POST | `/api/v1/auth/register` | public | `RegisterRequest` | 201 `RegisterResponse` | `app/api/v1/endpoints/auth.py` |

| GET | `/api/v1/budget-benchmarks` | public | — | 200 `BudgetBenchmarkResponse` | `app/api/v1/endpoints/benchmarks.py` |

| POST | `/api/v1/calculations/agro-savings-projection` | public | `AgroSavingsProjectionRequest` | 200 `AgroSavingsProjectionResponse` | `app/api/v1/endpoints/agro.py` |

| POST | `/api/v1/calculations/budget-comparison` | public | `BudgetComparisonRequest` | 200 `BudgetComparisonResponse` | `app/api/v1/endpoints/budget.py` |

| GET | `/api/v1/calculations/district-comparison` | public | — | 200 `DistrictComparisonResponse` | `app/api/v1/endpoints/district_advisor.py` |

| POST | `/api/v1/calculations/household-shock` | public | `HouseholdShockRequest` | 200 `HouseholdShockResponse` | `app/api/v1/endpoints/shocks.py` |

| POST | `/api/v1/calculations/policy-scenario` | public | `PolicyScenarioRequest` | 200 `PolicyScenarioResponse` | `app/api/v1/endpoints/policy_scenarios.py` |

| POST | `/api/v1/calculations/resilience-simulation` | public | `ResilienceSimulationRequest` | 200 `ResilienceSimulationResponse` | `app/api/v1/endpoints/resilience.py` |

| POST | `/api/v1/calculations/stress-test` | public | `StressTestRequest` | 200 `StressTestResponse` | `app/api/v1/endpoints/district_advisor.py` |

| GET | `/api/v1/dashboard/filters` | public | — | 200 `DashboardFiltersResponse` | `app/api/v1/endpoints/dashboard.py` |

| GET | `/api/v1/dashboard/overview` | public | — | 200 `DashboardOverviewResponse` | `app/api/v1/endpoints/dashboard.py` |

| GET | `/api/v1/district-vulnerability` | public | — | 200 `VulnerabilityListResponse` | `app/api/v1/endpoints/vulnerability.py` |

| GET | `/api/v1/district-vulnerability/{districtCode}` | public | — | 200 `VulnerabilityDetailResponse` | `app/api/v1/endpoints/vulnerability.py` |

| GET | `/api/v1/districts` | public | — | 200 `DistrictList` | `app/api/v1/endpoints/benchmarks.py` |

| GET | `/api/v1/districts/{code}/basket-details` | public | — | 200 `BasketDetailsResponse` | `app/api/v1/endpoints/district_advisor.py` |

| GET | `/api/v1/expense-categories` | public | — | 200 `ExpenseCategoryList` | `app/api/v1/endpoints/benchmarks.py` |

| GET | `/api/v1/market/shopping-checklist` | public | — | 200 `ShoppingChecklistResponse` | `app/api/v1/endpoints/agro.py` |

| GET | `/api/v1/nisr/financial-inclusion/districts` | public | — | 200 `DistrictFinancialInclusion` | `app/api/v1/endpoints/nisr.py` |

| GET | `/api/v1/nisr/financial-inclusion/national` | public | — | 200 `NationalFinancialInclusion` | `app/api/v1/endpoints/nisr.py` |

| GET | `/api/v1/nisr/health-insurance` | public | — | 200 `SurveyIndicatorEstimates` | `app/api/v1/endpoints/nisr.py` |

| GET | `/api/v1/nisr/poverty` | public | — | 200 `SurveyIndicatorEstimates` | `app/api/v1/endpoints/nisr.py` |

| GET | `/api/v1/nisr/sources` | public | — | 200 `SourceList` | `app/api/v1/endpoints/nisr.py` |

| GET | `/api/v1/nutrition/indyo-yuzuye` | public | — | 200 `BalancedPlateResponse` | `app/api/v1/endpoints/agro.py` |

| GET | `/api/v1/seasonal-swaps` | public | — | 200 `SeasonalSwapResponse` | `app/api/v1/endpoints/seasonal_swaps.py` |

| GET | `/api/v1/shocks/catalog` | public | — | 200 `ShockCatalog` | `app/api/v1/endpoints/resilience.py` |

| GET | `/api/v1/tracker/burn-rate` | Bearer | — | 200 `BurnRateResponse` | `app/api/v1/endpoints/tracker.py` |

| GET | `/api/v1/tracker/daily-trend` | Bearer | — | 200 `DailyTrendResponse` | `app/api/v1/endpoints/tracker.py` |

| GET | `/api/v1/tracker/overview` | Bearer | — | 200 `TrackerOverviewResponse` | `app/api/v1/endpoints/tracker.py` |

| GET | `/api/v1/tracker/transactions` | Bearer | — | 200 `TransactionListResponse` | `app/api/v1/endpoints/tracker.py` |

| POST | `/api/v1/tracker/transactions` | Bearer | `TransactionCreate` | 201 `TransactionCreatedResponse` | `app/api/v1/endpoints/tracker.py` |

| DELETE | `/api/v1/tracker/transactions/{id}` | Bearer | — | 204 no body | `app/api/v1/endpoints/tracker.py` |

| PATCH | `/api/v1/tracker/transactions/{id}` | Bearer | `TransactionPatch` | 200 `TransactionItem` | `app/api/v1/endpoints/tracker.py` |

| GET | `/api/v1/user/profile` | Bearer | — | 200 `ProfileResponse` | `app/api/v1/endpoints/profile.py` |

| PATCH | `/api/v1/user/profile` | Bearer | `ProfilePatch` | 200 `ProfileResponse` | `app/api/v1/endpoints/profile.py` |

| DELETE | `/api/v1/user/resilience-plan` | Bearer | — | 204 no body | `app/api/v1/endpoints/resilience_plan.py` |

| GET | `/api/v1/user/resilience-plan` | Bearer | — | 200 `ResiliencePlanResponse` | `app/api/v1/endpoints/resilience_plan.py` |

| POST | `/api/v1/user/resilience-plan` | Bearer | `ResilienceSimulationRequest` | 200 — | `app/api/v1/endpoints/resilience_plan.py` |

| GET | `/health` | public | — | 200 `HealthResponse` | `app/api/v1/endpoints/health.py` |

| GET | `/ready` | public | — | 200 `ReadyResponse` | `app/api/v1/endpoints/health.py` |



41 operations.

**Architecture.** `app/api/v1/endpoints/*` (FastAPI routers, request validation via `app/schemas/*`) → `app/services/*` (business rules; pure formulas in `app/calculations.py`) → `app/repositories/*` (SQLAlchemy 2 queries) → `app/models/*` (ORM, CHECK constraints mirrored in Alembic `alembic/versions/0001`–`0012`) → PostgreSQL. Sessions: one per request from `get_read_session` (READ ONLY transactions) or `get_write_session` (`app/db/session.py:149-162`); services commit explicitly. Seed data: versioned Python datasets (`app/data/*`) applied by `app/db/seed.py` with content hashes that `/ready` compares.

## 3. Verification baseline

All of the following were **run during this audit** on Windows 11, Python 3.12.8, FastAPI 0.162.0, SQLAlchemy 2.1.6, Pydantic 2.14.1, Alembic 1.20.1, psycopg 3.3.6, local PostgreSQL. Nothing below is copied from earlier reports.

| Check | Command | Result |
|---|---|---|
| Lint | `uv run ruff check .` | passed |
| Format | `uv run ruff format --check .` | 184 files already formatted |
| Types (CI scope) | `uv run mypy app tests alembic scripts` (strict) | no issues in 181 files |
| Tests | `uv run pytest` (alone on the test databases) | **1,180 passed, 2 skipped**, 319 s, exit 0 |
| Skipped locally | `tests/security/test_superuser_refused.py` (2 cases) | need `SUPERUSER_*_DATABASE_URL`; not set locally (by design) |
| CI on `main` | GitHub run 40776858656 (`gh run view --log`) | **1,182 passed, 0 skipped**; superuser tests ran (`...`); coverage 97.16% (gate 85%) |
| Migrations | `tests/integration/test_migrations.py` (round trip, stepwise, `alembic check`) inside the suite | passed |
| Dev schema drift | not re-run in this audit; last run 2026-10-28 (`migrate --target dev check`: "No new upgrade operations") | previously reported |
| Seed repeatability | CI step "Seed repeatability" on run 40776858656 (second seed run all `skipped`) | passed in CI |
| Query and connection probe | scratch pytest under the suite lock (§5) | 20 requests measured |

Working tree before and after the audit: clean on `main`, level with `origin/main`. `MISSING_APIS.pdf` is **not present on disk** (it was untracked and was removed outside this audit; it was not touched here).

## 4. Findings

### High

#### H-1. Unbounded request bodies and an unbounded lever list (amplification on a public endpoint)
- **Status (2026-10-29):** remediated on branch `fix/request-body-limits`, awaiting review: `Field(max_length=3)` on `activeCopingLevers` and `app/core/body_limit.py` (413 `request-too-large`, default 65,536 bytes, `MAX_REQUEST_BODY_BYTES`). Tests: `tests/unit/test_body_limit.py`, `tests/api/test_request_limits.py`.
- **Known limitation (live uvicorn 0.54 / h11 0.16, loopback, Windows):** the server sends the 413 and then closes the connection without reading the rest of the body. A client that has finished sending, or that sends only a little past the limit, gets the full 413 (12 of 12 runs, 96 KiB bodies). A client still uploading a much larger body can lose the response: the unread data makes the close a TCP reset. With a separate reader thread the 413 status line arrived in 12 of 12 runs and the full body in 10 of 12; a client that reads only after sending everything (`http.client`) got a connection error in 9 of 9 runs. Either way the upload stops after about 80–600 KiB, which is the protection H-1 needs. Draining the body before closing would make delivery more reliable but spends server work on attacker data, so it was not done; a reverse proxy in front of the app (untested here) may change this behaviour.
- **Category:** robustness / security. **Confidence:** confirmed.
- **Where:** `POST /api/v1/calculations/resilience-simulation` (public) and `POST /api/v1/user/resilience-plan` (Bearer). `app/schemas/resilience.py:66` (`active_coping_levers: list[CopingLeverId]`, no `max_length`); `app/services/resilience_service.py:41-75` (`_validate` emits one 422 error per duplicate). No body-size limit exists anywhere in `app/` (searched for content-length or body limits; none).
- **Scenario:** a client posts `["ibimina_tontine"] × N`. Each duplicate becomes a field error, so the response grows with N and the work grows faster than N. Any public endpoint also reads and parses arbitrarily large bodies before rejecting them.
- **Evidence (measured, in-process `TestClient`, stub app, this machine):**

  | Levers | Request | Status | Errors | Response | Time | Peak Python memory |
  |---|---|---|---|---|---|---|
  | 3 | <0.01 MB | 422 | 2 | <0.01 MB | 0.36 s | 2.2 MB |
  | 10,000 | 0.19 MB | 422 | 9,999 | 0.99 MB | 0.25 s | 6.2 MB |
  | 100,000 | 1.90 MB | 422 | 99,999 | 9.99 MB | 8.53 s | 61.3 MB |

  A 30 MB body (padding in an unknown field) was read and parsed in full and answered 422 in 0.82 s; there is no 413.
- **Minimal correction:** (1) `active_coping_levers: Annotated[list[CopingLeverId], Field(max_length=3)]` (the catalogue has 3 levers; `budget.py:20` already does this for `plan`); (2) a small ASGI middleware that answers `413` problem+json when `Content-Length` exceeds a limit (for example 64 KiB) or the streamed body does.
- **Regression tests:** 4 levers → 422 with exactly one `too_long`-style error on `activeCopingLevers`; a 100 KiB body → 413 problem+json on a public POST; existing 3-lever cases unchanged.
- **Compatibility:** a request with more than 3 levers changes from "N duplicate errors" to one length error (still 422). 413 is a new problem type; add it to contract §1.3.

#### H-2. No rate limiting or concurrency cap on Argon2 endpoints
- **Category:** security / robustness. **Confidence:** strongly evidenced (per-call cost measured; exhaustion under load not reproduced).
- **Where:** `POST /api/v1/auth/register`, `POST /api/v1/auth/login` (`app/api/v1/endpoints/auth.py:16-33`; `app/services/auth_service.py:66,97`; `app/core/security.py:29` uses argon2-cffi defaults).
- **Evidence:** defaults are `time_cost=3, memory_cost=65536 KiB, parallelism=4`. Measured on this 16-CPU machine (n=10): hash median 81 ms, verify median 124 ms. Login always verifies (a dummy hash for unknown identifiers, `security.py:36-48`), so every login attempt costs this, valid or not. No rate limiter, lockout or semaphore exists (README "Not built: … rate limiting").
- **Scenario:** (a) unlimited password guessing against any identifier; (b) memory pressure: sync endpoints run on AnyIO's 40-thread pool, so up to 40 concurrent hashes × 64 MiB ≈ 2.5 GiB could be requested at once; on a small instance that is an out-of-memory risk. (b) is arithmetic from the defaults, not a measured crash.
- **Minimal correction:** a process-wide semaphore around hash and verify (for example 2–4 concurrent, the rest wait briefly or get 503), plus per-IP and per-identifier rate limits on login and register (429 `rate-limited`, already reserved in contract §1.3 with `Retry-After`).
- **Regression tests:** N+1 rapid logins for one identifier → 429 with `Retry-After`; a concurrency test proving no more than K hashes run at once.
- **Compatibility:** adds 429 to two endpoints (the contract already reserves it).

### Medium

#### M-1. Connection-pool pressure from two connections per authenticated write
- **Category:** scalability / reliability. **Confidence:** confirmed (connection counts); pool exhaustion under load not reproduced.
- **Where:** `app/services/current_account.py:52` loads the account through `get_read_session`; write services then take `get_write_session` (`app/services/tracker_service.py`, `resilience_plan_service.py`, `profile_service.py`). Pool: `pool_size=5, max_overflow=5, pool_timeout=10` (`app/db/session.py:58-65`).
- **Evidence (probe, §5):** peak checked-out connections per request: 2 for `POST /tracker/transactions` and `POST /user/resilience-plan`; 1 for every read. Register and login hold their connection while Argon2 runs (query first, hash after).
- **Scenario:** 6 concurrent authenticated writes need 12 connections; the pool has 10. Waiters block for up to 10 s, then SQLAlchemy raises `TimeoutError`, which surfaces as 500 `internal` (L-2).
- **Minimal correction:** let the current-account dependency use the same session as the write service for write routes (one connection per request), or commit or close the read session before the write session opens; set pool size from the production database's connection limit and the worker count.
- **Regression test:** the probe's "peak connections = 1" assertion for every write route; a concurrency test with pool size 2 and 4 parallel writes that all succeed.
- **Compatibility:** none for clients.

#### M-2. No defined production start procedure or production CORS origin
- **Category:** reliability. **Confidence:** confirmed.
- **Where:** `backend/README.md:197-198` ("Render deployment (plan A5: `render.yaml`, `scripts/start.sh`) isn't part of this build"; CORS origin not supplied). The app does not migrate or seed on startup by design (`app/main.py:1-11`); `/ready` reports `migrations: failed` or `seed: failed` until someone runs them.
- **Scenario:** a deploy that starts uvicorn without `migrate --target production upgrade head` and `seed --target production` serves 500s from every data endpoint; with no `CORS_ORIGINS` for the deployed frontend, browsers block every call.
- **Minimal correction:** a start script that runs migrate, seed and `--check`, then `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log`; `render.yaml` with the health check on `/ready`; documented `JWT_SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`.
- **Acceptance:** a fresh database plus the start script → `/ready` 200 with all checks `ok`; the smoke test passes against the deployed URL.

#### M-3. The public API description makes a false privacy claim
- **Category:** maintainability / security (privacy communication). **Confidence:** confirmed.
- **Where:** `app/main.py:42-47`: "No account is needed and no citizen data is stored: calculation bodies are processed, then discarded, never logged." Shown at `/docs` and in `/openapi.json`.
- **Fact:** since contract v0.5–v0.8 the server stores accounts, profiles, tracker transactions and resilience plans.
- **Minimal correction:** state precisely what is stored (accounts, profile, transactions, saved plan) and that calculation endpoints store nothing. Related open decisions Q-13 and Q-34 stay with the product owner.
- **Regression test:** an OpenAPI test asserting the description names the stored data.

### Low

#### L-1. Tracker POST answers 500 when the account vanishes mid-request
- **Category:** reliability. **Confidence:** confirmed (the project owner's captured run on 2026-10-29 showed `ForeignKeyViolation` on `fk_tracker_transactions_account_id` → 500, during concurrent test runs that deleted accounts).
- **Where:** `app/repositories/tracker_repository.py:85-93` re-raises any `IntegrityError` that is not the idempotency constraint; `app/services/tracker_service.py:231`. Profile and resilience-plan map the same case to 401 (`profile_service.py`, `resilience_plan_repository.py:66-73`).
- **Reachability:** only if an account is deleted out of band (no API deletes accounts today).
- **Correction:** map SQLSTATE 23503 to `NotAuthenticatedError`, as the plan repository does. **Test:** insert for a nonexistent account id → 401, not 500.

#### L-2. Database outages and pool timeouts surface as 500 instead of 503
- **Category:** robustness. **Confidence:** confirmed by code (`app/core/errors.py:387-390` registers no handler for `sqlalchemy.exc.OperationalError` or `TimeoutError`; the last-resort 500 in `app/core/logging.py:153-163` answers them). `/ready` already reports the outage correctly (`app/db/readiness.py`; `tests/integration/test_database.py::test_unreachable_database_fails_fast_and_readiness_reports_it`).
- **Correction:** a handler mapping connection errors and pool timeouts to 503 `service-unavailable` with `Retry-After`. **Test:** with an unreachable database, a data endpoint returns 503 problem+json.

#### L-3. No statement or idle-in-transaction timeout
- **Category:** robustness / scalability. **Confidence:** unverified risk (every measured query is small and indexed, §5).
- **Where:** `app/db/session.py:64` sets only `connect_timeout`.
- **Correction:** `options="-c statement_timeout=5000 -c idle_in_transaction_session_timeout=15000"` in `connect_args` (values to agree). **Test:** `SELECT pg_sleep(6)` on an app session raises `QueryCanceled`.

#### L-4. Bound SQL parameters are not hidden at the engine level
- **Category:** security (defense in depth). **Confidence:** confirmed that parameters appear in exception text (the captured pytest log shows titles, notes and amounts); **not** a production leak, because `JsonFormatter` logs frame locations only, never exception messages (`app/core/logging.py:47-57`).
- **Correction:** `create_engine(..., hide_parameters=True)`. **Test:** an `IntegrityError`'s `str()` contains no bound values.

#### L-5. Stale docstrings about write sessions
- **Category:** maintainability. **Confidence:** confirmed. `app/db/session.py:124-125` and `:156` say only "the account endpoints" write; profile, tracker and resilience-plan also do. **Correction:** update the text.

#### L-6. Stored plans are validated against the current lever catalogue on every read
- **Category:** maintainability. **Confidence:** unverified risk. `app/services/resilience_plan_service.py:36` rebuilds a `ResilienceSimulationRequest` from stored rows; if a lever or shock id is later removed from the `Literal` types, `GET /user/resilience-plan` for an older plan raises a validation error → 500. **Correction:** when the catalogue changes, ship a migration that rewrites or removes affected rows, and test it.

### Informational (no change recommended now)
- Unique-violation detection matches constraint names in exception text (`account_repository.py:32`, `tracker_repository.py:92`). It works because names are pinned by `tests/unit/test_migration_names.py`; SQLSTATE plus `diag.constraint_name` would be sturdier.
- `/docs` and `/openapi.json` are public in production; acceptable for a demo.
- Tracker accounts have no per-account transaction cap (already listed in contract §11.10).
- Test fixtures delete every account in the test database (`tests/api/test_tracker.py::_clear` and others). Safe only because of the suite lock (§6).

## 5. Performance evidence and measurement gaps

**Method.** A scratch pytest module (not committed) using the suite's fixtures, so it held the advisory lock and touched only `imibereho_test`. It built its own engine with SQLAlchemy `before_cursor_execute`, `checkout` and `checkin` listeners, ran 20 requests through `TestClient`, captured `EXPLAIN` plans (with `enable_seqscan=off`, because the tables are tiny), and deleted only the account it created.

| Request | SQL statements | Peak connections |
|---|---|---|
| `GET /ready` | 3 | 1 |
| `GET /districts` | 1 | 1 |
| `GET /budget-benchmarks` | 2 | 1 |
| `GET /dashboard/filters` | 2 | 1 |
| `GET /dashboard/overview` | 12 | 1 |
| `GET /district-vulnerability` | 5 | 1 |
| `GET /district-vulnerability/gasabo` | 6 | 1 |
| `GET /nisr/financial-inclusion/districts`, `/nisr/poverty` | 2 each | 1 |
| `GET /calculations/district-comparison`, `/districts/huye/basket-details`, `/market/shopping-checklist` | 2 each | 1 |
| `GET /user/profile` | 1 | 1 |
| `POST /tracker/transactions` | 3 | **2** |
| `GET /tracker/overview`, `/tracker/transactions`, `/tracker/daily-trend` | 2 each | 1 |
| `POST /user/resilience-plan` | 2 | **2** |
| `GET /user/resilience-plan` | 2 | 1 |
| `POST /auth/login` | 1 | 1 |

**Query plans:** the tracker month list and month total use `ix_tracker_transactions_account_id_occurred_at_id` (index scan on account and time range); the login lookup uses `uq_household_accounts_identifier`.

**Conclusions.** No N+1 pattern was found: statement counts are small constants for the seeded data sizes (30 districts). No missing index was demonstrated. No index, cache or worker is recommended.

**Gaps (not measured):** throughput and latency under concurrent load; pool exhaustion behaviour (M-1); memory under concurrent Argon2 (H-2); behaviour on the production host's CPU and memory; `dashboard/overview` with larger synthetic datasets. No throughput or capacity figure is claimed.

## 6. Test-infrastructure findings (advisory lock)

**Mechanism.** `tests/conftest.py:100-134`: the session fixture `exclusive_db_run` opens a dedicated connection to the test database and polls `pg_try_advisory_lock(0x1B1BE7E07E57)` every 2 s for up to 900 s, then holds the lock for the whole session and unlocks in `finally`. `test_database` depends on it (`:137`), and so does `migrations_settings` (`tests/integration/test_migrations.py:20`), so migration round trips are covered too. The lock is session-level on its own connection, so a crashed process releases it when the connection drops.

| Question | Answer | Evidence |
|---|---|---|
| Does every process that modifies shared databases take the lock? | Yes, for pytest: every fixture that connects (`test_database`, `db_client`, `migrations_*`) depends on it. `tests/unit/test_guards.py` only builds engines (no connection); `tests/unit/test_cli.py` checks refusals. | code inspection |
| Is it held long enough and released safely? | Held from first DB fixture to session end; released in `finally` or on disconnect. | code; experiment below |
| Do parallel runs wait, then succeed? | **Yes.** Run A (`tests/integration`, 35 tests) and run B (`test_resilience_plan.py` + `test_migrations.py`), started 8 s apart: B printed "another test run is using the test databases; waiting for it" and then passed 29 tests in 83.9 s; A passed 35 in 60.3 s. Both exit 0. | experiment, 2026-10-29 |
| The earlier "exit code 4 without a summary" | **Not a lock defect.** That invocation (2026-10-28) asked the tool for a 920,000 ms timeout, above its 600,000 ms limit. The command's trailing `echo` (which always runs) never printed, so the shell was terminated externally while B was still waiting for A, which ran 210 s. The exact source of code 4 is not verifiable. | missing `echo` line; today's successful repeat |
| Does CI run the superuser tests? | **Yes.** CI sets both `SUPERUSER_*` URLs (`.github/workflows/backend-ci.yml:81-82`), the test fails instead of skipping when `CI=true` (`tests/security/test_superuser_refused.py`), and run 40776858656 shows 1,182 passed, 0 skipped. | CI log |

**Residual gaps (informational):**
- The lock lives in the test database, so it coordinates only processes that share the same `TEST_DATABASE_URL`. Two runs with different test databases but one migrations database would not be serialized.
- CLI commands run outside pytest (`migrate --target test`, `seed --target test`) do not take the lock; CI runs them sequentially before pytest, which is safe.
- The 900 s wait limit is shorter than a slow full suite on a loaded machine, in which case the second run would exit (code 2) rather than wait.

## 7. Prioritized remediation roadmap

| # | Item | Depends on | Acceptance criteria |
|---|---|---|---|
| 1 | **H-1** lever `max_length=3` plus a body-size limit (413) | none | 100,000 levers → 422 with ≤ 1 error on `activeCopingLevers`, response under 2 KB, under 50 ms; a 100 KiB body to any public POST → 413 problem+json; full suite green; contract §1.3 lists 413 |
| 2 | **M-2** start script and `render.yaml` | owner: hosting choice, production DB, frontend origin | fresh DB + script → `/ready` 200 all `ok`; smoke test 19/19 against the deployed URL |
| 3 | **H-2** Argon2 semaphore plus login/register rate limit | decide limits (per IP and per identifier) | burst test → 429 with `Retry-After`; at most K concurrent hashes; existing auth tests green |
| 4 | **M-1** one connection per authenticated write; pool sized to the production DB | 2 (production limits known) | probe peak connections = 1 on every route; pool 2 with 4 parallel writes all succeed |
| 5 | **L-2** 503 for outages and pool timeouts | 4 | unreachable DB → 503 problem+json with `Retry-After` |
| 6 | **M-3, L-5** correct the OpenAPI description and docstrings | none (wording for Q-34 with the owner) | OpenAPI description names the stored data |
| 7 | **L-1, L-3, L-4, L-6** | none | the tests listed with each finding |

## 8. Known limitations of this audit

- No load or soak testing: concurrency effects in H-2 and M-1 are reasoned from configuration and per-request measurements, not reproduced.
- Measurements are from one Windows development machine with in-process `TestClient`; production hardware will differ.
- The production environment (host, database limits, proxy body limits) is not defined, so deploy-time behaviour (M-2) could not be tested.
- Business rules were reviewed for structure and covered by the existing tests (which pin the PDF examples); no rule was re-derived independently beyond those tests, and owner decisions (BR-19, BR-22, BR-26 to BR-28) were not re-litigated.
- `MISSING_APIS.pdf` was not available on disk, so the endpoint list was checked against the contract and earlier recorded reconciliation, not the PDF itself.
