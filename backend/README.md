# Imibereho backend

FastAPI service for the Imibereho demo: a household financial-resilience tool for Rwanda.
**Every figure it serves is synthetic, illustrative data under concept methodology v0.1, not
official statistics.** Data responses carry `meta.isIllustrative: true`.

- **Contract:** [`docs/architecture/api-contract-proposal.md`](../docs/architecture/api-contract-proposal.md)
  (v0.2 rev 2). It is authoritative for endpoints, fields and errors.
- **Plan:** [`docs/IMPLEMENTATION_PLAN.md`](../docs/IMPLEMENTATION_PLAN.md). It covers the guards,
  database lifecycle and layering.
- **Formulas:** BR-01 to BR-16 in [`docs/architecture/backend-requirements.md`](../docs/architecture/backend-requirements.md) §2.

Stack: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (typed), Alembic, PostgreSQL (18 locally,
16 in CI), psycopg 3, uv, pytest, ruff, mypy (strict). **No Docker** for local development.

## Versions (kept separate)

| Version | Value | Where |
|---|---|---|
| HTTP API path | `v1` | Every data route is under `/api/v1`. `/health` and `/ready` are at the root |
| Contract / OpenAPI | `0.2.0` | `info.version` in `/openapi.json` |
| Methodology | `0.1` | `meta.methodologyVersion` in every data response |

## Endpoints

| Method and path | Contract | Notes |
|---|---|---|
| `GET /health` | §2 | Liveness; never touches the database |
| `GET /ready` | §2 | `database`, `migrations`, `seed` checks; 503 `not-ready` otherwise |
| `GET /api/v1/districts` | §3 | 30 districts, alphabetical |
| `GET /api/v1/expense-categories` | §3 | 5 categories |
| `GET /api/v1/budget-benchmarks` | §4 | Household size 4 only ([PD] Q-32) |
| `POST /api/v1/calculations/household-shock` | §4 | Stateless; body never stored or logged |
| `GET /api/v1/seasonal-swaps` | §4 | Month 10 swap for every district ([PD] Q-32) |
| `GET /api/v1/district-vulnerability[/{districtCode}]` | §5 | 30 scores from the design |
| `POST /api/v1/calculations/policy-scenario` | §5 | Stateless |
| `GET /api/v1/dashboard/filters`, `GET /api/v1/dashboard/overview` | §5 | `geography=all` only ([PD] Q-14) |
| `POST /api/v1/calculations/budget-comparison` | §6 (optional) | See open item below |

Not built: the optional `GET /api/v1/methodology` and `GET /api/v1/demo-household` (each has a
frontend fallback, contract §6), rate limiting (optional O3), and per-district geography (O5, not
planned). There is no authentication (Q-04) and no pagination (contract §1: lists hold ≤ 30
items).

Errors are RFC 9457 `application/problem+json` (contract §1.3). Every response carries
`X-Request-ID` (a safe client-supplied value is echoed back) and `Content-Language: en`.

## Layout

```
app/
  main.py            create_app(target); `app.main:app` is resolved lazily (no settings at import)
  api/router.py      health at the root + the v1 router mounted once at /api/v1
  api/v1/            router.py (no prefix), responses.py (problem docs), endpoints/*
  core/              config (strict settings), logging (JSON, request IDs), errors, constants
  db/                session, base, guards, readiness, migrate (the only Alembic entry), seed
  models/            synthetic reference data and seed state only (no citizen data, Q-02)
  schemas/           Pydantic v2 request/response models
  repositories/      database queries only (read-only for the API)
  services/          business rules; call repositories and app/calculations.py
  calculations.py    pure BR-01–BR-14, BR-16 functions (no database or framework imports)
  data/              seed datasets (see app/data/README.md)
alembic/             env.py refuses to run unless invoked through app.db.migrate
scripts/             migrate.py, seed.py (entry points), sql/create_local_databases.sql
tests/               unit, api, integration, security, runtime
```

## Local setup (Windows, PowerShell)

Prerequisites: Python 3.12 (selected by `.python-version`), [uv](https://docs.astral.sh/uv/), the
local PostgreSQL server (managed through pgAdmin 4), and Git.

```powershell
cd backend
uv sync
```

### Database setup (one time, in pgAdmin 4)

1. Open pgAdmin 4 and connect to the local server as `postgres`.
2. Open the Query Tool and run [`scripts/sql/create_local_databases.sql`](scripts/sql/create_local_databases.sql),
   replacing the placeholder password. It creates the `NOSUPERUSER` role `imibereho` and the
   databases `imibereho`, `imibereho_test` and `imibereho_migrations`.
3. Copy `.env.example` to `.env` (git-ignored) and replace each `<password>`.

The application, tests, migrations and seeding connect as `imibereho`. The guards refuse the
`postgres` user by name, and refuse any superuser after connecting. The one exception is the
opt-in for the local dev server described under "Database safety".

### Daily workflow

```powershell
uv run python -m app.db.migrate --target dev upgrade head   # or: uv run python scripts/migrate.py ...
uv run python -m app.db.seed --target dev                   # idempotent; or: scripts/seed.py
uv run uvicorn app.main:app --reload --no-access-log
```

Open http://localhost:8000/docs. `/ready` returns 200 once migrations and seed data match this
build.

## Database safety

Each target reads exactly one variable. None falls back to another, and none has a default URL:

| Target | Variable | Database name | Host | ENVIRONMENT | Commands |
|---|---|---|---|---|---|
| `dev` | `DATABASE_URL` | `imibereho` | local | `local` | upgrade, current, check, heads, history, seed |
| `test` | `TEST_DATABASE_URL` | `imibereho_test` | local | not `production` | upgrade, check, current, seed |
| `migrations` | `MIGRATIONS_DATABASE_URL` | `imibereho_migrations` | local | not `production` | any Alembic command |
| `production` | `DATABASE_URL` | any | not local | `production` | upgrade, current, check, seed |

### Optional: `postgres` for local development (`ALLOW_LOCAL_SUPERUSER`)

The recommended setup uses the `NOSUPERUSER` role `imibereho` everywhere, as plan §2.3 specifies.
If you prefer to run the local dev server as `postgres`, set `ALLOW_LOCAL_SUPERUSER=true` in
`backend/.env`. This exception was chosen by the project owner on 2026-10-25 and is a deliberate
deviation from plan §2.3. It is honoured **only** when every one of these holds:

| Condition | Required value |
|---|---|
| Target | `dev` (the local server, `migrate --target dev`, `seed --target dev`) |
| `ENVIRONMENT` | `local` |
| Host | `localhost`, `127.0.0.1` or `::1` |

Everything else stays as it was:
- `test`, `migrations` and `production` still refuse `postgres` and any superuser, so the tests
  keep CI's non-superuser parity.
- If `ALLOW_LOCAL_SUPERUSER=true` is set with any other `ENVIRONMENT`, the configuration is
  rejected, so production refuses to start.
- Database names, hosts and commands are still checked, and downgrades on `dev` are still refused.
- The role check still fails closed if it cannot run.
- The server logs a warning at startup, and on each superuser connection, while the exception is
  active.

Caveat: tables that you migrate as `postgres` are owned by `postgres`. If you later switch `dev`
to `imibereho`, run `ALTER TABLE … OWNER TO imibereho` (or recreate the dev database) first.

- A bare `alembic upgrade head` exits with an error. Use `python -m app.db.migrate --target …`.
- Downgrades are possible only on `imibereho_migrations`. Tests never touch `DATABASE_URL`.
- Tables are created only by Alembic migrations. `create_all()` is never used.
- Writing a migration: wrap every explicit constraint name in `op.f("...")`. Without it, Alembic applies the naming convention a second time to CHECK constraints (revision `0006` repairs the names 0001–0005 created). Keep identifiers at 63 characters or fewer; `tests/unit/test_migration_names.py` enforces both rules without a database.
- API sessions are `READ ONLY` transactions. Only migrations and the seed framework write.

## Tests and quality gates

```powershell
uv run ruff check . ; uv run ruff format --check .
uv run mypy app tests alembic scripts
uv run pytest -m "not db"     # no database needed
uv run pytest                 # full suite: needs TEST_DATABASE_URL and MIGRATIONS_DATABASE_URL
uv run pytest --cov=app --cov-fail-under=85
```

Pytest uses `--tb=short` (in `pyproject.toml`): long tracebacks print each frame's arguments, which can include database URLs. `Settings` also hides its URL fields from `repr`.

DB tests are marked `db` automatically. If their variables are missing or a guard refuses, the
run **stops with exit code 2**; it never skips silently. At session start the test database is
migrated, seeded and checked (plan §2.2). The two superuser-rejection cases need
`SUPERUSER_POSTGRES_DATABASE_URL` / `SUPERUSER_ALT_DATABASE_URL`. They are optional locally and
always run in CI ([`.github/workflows/backend-ci.yml`](../.github/workflows/backend-ci.yml)).

## Logging and privacy

- App logs are JSON lines on stdout. They contain `ts`, `level`, `request_id`, `method`, the
  route template (never the query string), `status` and `duration_ms`.
- On a 500 they add the exception type and stack frames, but not the exception message.
- Request bodies, query strings and headers other than `X-Request-ID` are never logged.
- The uvicorn access log is disabled in code, as well as by `--no-access-log`.
- Money values travel only in POST bodies, never in query strings (contract §1).

## Open items that affect the backend

See the change report for the full list. These are the ones most relevant here:

- **Contract sign-off:** contract v0.2 rev 2 still awaits frontend sign-off.
- **Budget comparison errors:** contract §6 doesn't name the error codes for a missing or
  duplicated category. This build uses `required` at `plan` for a missing category and
  `unknown_value` at `plan.<i>.categoryCode` for a duplicate. This needs confirmation.
- **Deployment:** the deployed frontend origin for `CORS_ORIGINS` hasn't been supplied yet.
  Render deployment (plan A5: `render.yaml`, `scripts/start.sh`) isn't part of this build.
