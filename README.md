# FlexSignal AI

FlexSignal AI is an Azure-hosted forecasting and decision-support platform for the Danish electricity system, initially focused on DK1 and DK2.

Version `v0.1` is read-only decision support. The platform may forecast, visualize, explain, and recommend actions for human review, but it must not automatically control electricity consumption or send control signals to assets, plants, devices, or energy infrastructure.

## MVP Scope

- Forecast electricity surplus risk for DK1 and DK2.
- Visualize forecast windows, confidence, and expected economic potential.
- Explain model output and recommendations in clear text.
- Support human decision-making with auditable recommendations.
- Keep LLM usage limited to explanation, reporting, and recommendation text.

## Current MVP Status

FlexSignal AI is ready for a local technical MVP demo. It is not ready for
production, is not a validated commercial forecasting product, and must remain
read-only decision support for human review only.

Working read-only core:

- Local PostgreSQL schema and Alembic baseline exist.
- Manual local Energi Data Service ingestion exists for `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`.
- Local PostgreSQL contains validated DK1 and DK2 sample data from manual
  confirmed local EDS writes after the `limit 50` import.
- Manual batch wrapper validation works with `limit 50`.
- Repeating the same `limit 50` import was idempotent for the tested batch.
- Read-only energy API endpoints exist for `spot_prices` and `power_balance`.
- Frontend dashboard can manually load spot prices, power balance, current
  surplus risk, a forecast-window preview, an energy freshness dry-run
  query-plan preview, and a DB-backed freshness read from stored
  local/configured database data.
- Frontend dashboard behavior has been manually checked for DK1 and DK2.
- `rule-engine-v0` exists for deterministic surplus-risk scoring.
- `forecast-window-v0` exists as pure backend Python aggregation over
  caller-provided rows for 0-24h, 24-48h, and 48-72h windows.
- `report-summary-v0` exists as pure backend Python data-structure logic over
  caller-provided current-risk and forecast-window outputs.
- `report-summary-v0` Markdown rendering exists as pure backend Python logic
  that converts caller-provided report dictionaries into Markdown strings.
- Manual local PDF export v0 exists for synthetic/caller-provided
  `report-summary-v0` previews through an explicit `--output` path only.
- `audit-event-v0` exists as a pure backend Python in-memory event
  data-structure foundation for read-only decision-support actions.
- An audit-event database persistence foundation exists: Alembic defines an
  `audit_events` table and `backend/app/audit/repository.py` builds
  parameterized idempotent insert SQL for explicit future use.
- An audit writer service foundation exists in `backend/app/audit/writer.py`
  for explicitly executing validated `audit-event-v0` inserts through a
  caller-provided database connection.
- A runtime audit event factory foundation exists in
  `backend/app/audit/runtime_events.py` for constructing standardized
  `audit-event-v0` dictionaries for future read-only runtime actions.
- A runtime audit persistence dry-run planner exists in
  `backend/app/audit/runtime_plan.py` for building standardized runtime
  `audit-event-v0` dictionaries plus repository INSERT plans without executing
  SQL, opening database connections, reading `DATABASE_URL`, calling the audit
  writer, exposing API routes, or modifying frontend behavior.
- An EDS data freshness read-model foundation exists in
  `backend/app/db/repositories/energy_freshness.py`, and
  `GET /api/energy/freshness` exposes those DK1/DK2 query plans as a
  read-only dry-run preview for dashboard freshness indicators. The API does
  not connect to a database, read `DATABASE_URL`, execute SQL, call live
  Energi Data Service, call DMI/weather APIs, schedule jobs, or write data.
- A DB-executed energy freshness reader foundation exists in
  `backend/app/db/repositories/energy_freshness_reader.py` with focused tests
  in `backend/tests/test_energy_freshness_reader.py`. It requires an explicit
  caller-provided database connection, validates parameterized SELECT-only
  query plans before cursor execution, rejects invalid price areas outside
  `DK1`/`DK2`, returns structured dictionaries only, and does not create
  connections, read `DATABASE_URL`, call live EDS/DMI APIs, write data, or
  modify frontend behavior.
- `GET /api/energy/freshness/read?price_area=DK1|DK2` now exposes the
  controlled DB-backed energy freshness read path for future dashboard live
  data trust indicators. It requires `DATABASE_URL` at request time, returns a
  safe HTTP 503 if it is missing, rejects invalid price areas with HTTP 400,
  executes SELECT-only freshness reads through
  `backend/app/db/repositories/energy_freshness_reader.py`, and does not write
  to the database, fetch new EDS/DMI data, trigger ingestion, modify the
  database schema, or add operational behavior. The frontend can display these
  read results through the backend API only; it does not execute SQL or access
  the database directly.
- Manual local energy freshness DB smoke now exists at
  `scripts/energy_freshness_db_smoke.py`. It defaults to dry-run query-plan
  JSON, does not connect to a database unless `--execute` is provided, and
  requires an explicit local `--database-url` for DB-executed freshness reads.
  It performs SELECT-only reads through the existing freshness reader, writes
  no data, never prints the raw database URL, does not call EDS/DMI APIs, and
  does not add API, frontend, scheduler, Azure, auth, ML/LLM, audit-write,
  report/PDF, control, dispatch, activation, or operational behavior.
- Observed manual local energy freshness DB smoke results confirm local
  DB-backed freshness reads work for stored DK1/DK2 data using explicit
  `--execute` and a local `--database-url`. Reads were SELECT-only, no
  database writes were performed, no live EDS/DMI calls were made, and no
  backend or frontend server was started.
- Observed local API smoke results confirm
  `GET /api/energy/freshness/read?price_area=DK1|DK2` can perform DB-backed
  SELECT-only freshness reads when the backend is started locally with
  `DATABASE_URL=postgresql://localhost/flexsignal_ai`. DK1 and DK2 returned
  HTTP 200 with `dry_run=false`, `database_query_executed=true`,
  `database_write_performed=false`, and `requires_database_url=true`; invalid
  `SE3` returned HTTP 400 `Unsupported price_area`. No database writes, live
  EDS/DMI calls, ingestion, or frontend changes were involved.
- `POST /api/audit/preview` exists as a reviewed read-only audit persistence
  dry-run preview API. It exposes runtime planner output for inspection only
  and does not add automatic audit logging or wire audit persistence into
  forecast, risk, report, or PDF runtime flows.
- Manual local audit persistence dry-run preview exists for building one
  synthetic `audit-event-v0` and repository SQL plan without database access
  or execution.
- Manual local audit DB write smoke exists for one deterministic synthetic
  `audit-event-v0`, defaults to dry-run, writes only to `audit_events` when
  `--execute` and an explicit local `--database-url` are provided, and has now
  been manually verified against local Postgres.
- `POST /api/forecast/preview` exposes `forecast-window-v0` for
  caller-provided JSON rows only.
- `GET /api/risk/current` works for DK1 and DK2 from existing local rows.
- Synthetic backtest preview exists.
- Local DB read-only backtest exists.
- Backtest row pairing uses `nearest_timestamp_v0_1`.

Latest documented local DB backtest results after the confirmed manual EDS
historical batch write:

| Area | Spot prices read | Power balance read | Local DB backtest | Average risk score |
| --- | ---: | ---: | --- | ---: |
| DK1 | 53 rows | 53 rows | low=1, medium=52, high=0 | 34.5283 |
| DK2 | 50 rows | 50 rows | low=42, medium=8, high=0 | 21.8 |

Latest read-only API/UI smoke-test observations:

- DK1 current-risk API returned medium risk with score `35`.
- DK2 current-risk API returned low risk with score `20`.
- Forecast preview API returned deterministic caller-provided DK1/DK2 window
  summaries without `DATABASE_URL`, including high-risk max aggregation,
  empty-window `unknown` handling, DK1/DK2 validation, and timezone-aware
  `generated_at_utc` validation.
- Audit preview API returned dry-run audit persistence plans without
  `DATABASE_URL`, database connections, SQL execution, audit writer calls,
  external API calls, file writes, report/PDF generation, or frontend changes.
- Audit preview API validation covered allowed event types, DK1/DK2 price-area
  validation, safe local-user actor defaults, HTTP 400 responses for
  unsupported inputs, and response output without raw database URLs, secrets,
  tokens, full headers, or full request bodies.
- Energy freshness preview API validation covered
  `GET /api/energy/freshness?price_area=DK1`, DK1/DK2 support, HTTP 400
  responses for unsupported price areas, dry-run query-plan output, and no
  `DATABASE_URL`, database connection, SQL execution, live EDS/DMI call, data
  write, frontend behavior, scheduler, or operational functionality.
- Frontend energy freshness card validation covered the new
  `fetchEnergyFreshness()` helper and manual calls to
  `GET /api/energy/freshness?price_area=DK1|DK2` through the existing
  `NEXT_PUBLIC_API_BASE_URL` pattern. The card displays `dry_run`,
  `database_query_executed`, `database_write_performed`,
  `requires_database_url`, spot price and power balance freshness plan
  status, warnings, and the human-review safety boundary. It explicitly
  communicates freshness query plan preview only, no database query executed,
  no database write performed, no new EDS/DMI fetch, and read-only decision
  support. It does not prove production data freshness.
- Frontend DB-backed energy freshness card wiring uses
  `fetchEnergyFreshnessRead()` to manually call
  `GET /api/energy/freshness/read?price_area=DK1|DK2` through the same
  backend API base URL helper. The card displays SELECT-only read results from
  stored local/configured database data: `price_area`, `dry_run`,
  `database_query_executed`, `database_write_performed`,
  `requires_database_url`, `spot_price_freshness.latest_timestamp`,
  `spot_price_freshness.row_count`,
  `power_balance_freshness.latest_timestamp`,
  `power_balance_freshness.row_count`, warnings, and the read-only
  human-review safety boundary. If the backend returns HTTP 503 because
  `DATABASE_URL` is missing, the UI shows
  `DB-backed freshness read requires backend DATABASE_URL.` The frontend does
  not execute SQL, write to the database, fetch live EDS/DMI data, trigger
  ingestion, or imply production monitoring exists.
- Frontend DB-backed energy freshness read wiring validation recorded that
  `npm run build` passed and `git diff --check` passed. `npm run lint` and
  `npm run typecheck` scripts did not exist. No backend server was started,
  no frontend dev server was started, no database was accessed, no SQL was
  executed, and no live Energi Data Service or DMI/weather APIs were called.
  The validation was documentation-only for the dashboard read display path:
  no backend behavior changed, no new endpoint was added, no database code or
  migrations were added, no writes or audit writes were performed, no auth,
  Azure, ML/LLM, report/PDF, control, dispatch, activation, or operational
  functionality was added.
- Manual frontend plus backend energy freshness smoke was observed with the
  backend started locally using
  `DATABASE_URL=postgresql://localhost/flexsignal_ai`, the frontend started
  locally using `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`, and the
  browser opened to the local dashboard. Requests were manual button clicks
  only; no auto-load or polling was observed. Spot prices, power balance,
  current surplus risk, forecast preview, DB-backed energy freshness reads,
  and dry-run freshness query-plan previews loaded for DK1 and DK2.
- In that manual dashboard smoke, DB-backed freshness read wording remained
  explicit: DB-backed freshness read, SELECT-only read, no database write
  performed, freshness of stored local/configured database data, no new
  EDS/DMI data fetch, and no implication that ingestion has run. Observed
  DK1 DB-backed freshness returned `dry_run=false`,
  `database_query_executed=true`, `database_write_performed=false`,
  `requires_database_url=true`, spot price `row_count=53`, spot price latest
  timestamp `2026-06-11T21:45:00+02:00`, power balance `row_count=53`, and
  power balance latest timestamp `2026-06-10T17:00:00+02:00`. Observed DK2
  returned the same execution flags, spot price `row_count=50`, spot price
  latest timestamp `2026-06-11T21:45:00+02:00`, power balance
  `row_count=50`, and power balance latest timestamp
  `2026-06-10T17:00:00+02:00`. Dry-run freshness preview returned
  `dry_run=true`, `database_query_executed=false`,
  `database_write_performed=false`, `requires_database_url=false`, and spot
  price and power balance query plans without executing SQL. The read-only
  safety boundary was preserved.
- DB-executed energy freshness reader validation covered
  `read_spot_price_freshness`, `read_power_balance_freshness`, and
  `read_energy_freshness_summary`. Focused reader tests passed with
  `24 passed`; the full backend suite passed with `466 passed, 1 warning`;
  `py_compile` passed; forbidden-pattern grep matched only safety-boundary
  keys, defensive blocked-token validation, and negative assertions/unsafe-plan
  tests; `git diff --check` passed. Tests used fake connection/cursor objects
  only, and no live database writes were performed.
- DB-backed energy freshness read API validation covered
  `GET /api/energy/freshness/read?price_area=DK1`, DK1/DK2 support, HTTP 400
  responses for invalid `price_area`, safe HTTP 503 behavior when
  `DATABASE_URL` is missing at request time, app import and route exposure
  without `DATABASE_URL`, omission of the raw database URL from responses, and
  SELECT-only freshness reads with mocked database connections only. Focused
  API freshness read tests passed with `9 passed, 1 warning`; the full backend
  suite passed with `483 passed, 1 warning`; `py_compile` passed;
  forbidden-pattern grep matched only defensive/negative assertions in tests;
  `git diff --check` passed; no live DB writes were performed.
- Local DB-backed energy freshness read API smoke used a locally started
  backend with `DATABASE_URL=postgresql://localhost/flexsignal_ai` and called
  `GET /api/energy/freshness/read?price_area=DK1`, `DK2`, and `SE3`. DK1 and
  DK2 returned HTTP 200 with SELECT-only freshness results; `SE3` returned
  HTTP 400 `Unsupported price_area`. No writes, live EDS/DMI calls, ingestion,
  or frontend changes were involved.
- Frontend forecast preview card manually calls `POST /api/forecast/preview`
  with deterministic synthetic/caller-provided demo rows only.
- Frontend manually loaded DK1 and DK2 spot prices, power balance, and current
  surplus risk.
- The read-only badge and disclaimer were visible.
- No automatic loading, polling, control, dispatch, or activation behavior was
  observed.

Still preview / not production:

- Dataset is still small and no full historical backtest has been run.
- No outcome labels or statistical calibration exist.
- The 24-72 hour forecast-window preview API is deterministic aggregation only;
  it uses caller-provided rows, is not ML, is not LLM based, is not DMI/weather
  based yet, does not fetch EDS or DMI data, does not read or write a database,
  and is not production forecast validation. The frontend card is a manual
  preview surface for the same synthetic/caller-provided boundary only.
- The report-summary foundation now has manual synthetic local JSON, Markdown,
  and PDF preview scripts. PDF export v0 writes a PDF only when an explicit
  local `--output` path is provided. It does not fetch data, read or write a
  database, expose an API, add frontend download behavior, use ML, or use LLMs.
- `audit-event-v0` now has a schema/repository persistence foundation, a
  manual local DB write smoke script, a backend writer service foundation,
  runtime event factory and runtime dry-run planner foundations, and a
  reviewed read-only `POST /api/audit/preview` dry-run preview endpoint. The
  endpoint returns audit persistence plans for inspection only; it does not
  enable production audit persistence, add automatic audit logging, or connect
  audit persistence to forecast, risk, report, PDF, or frontend runtime flows.
  The runtime planner builds runtime events and repository INSERT plans, but
  returns dry-run dictionaries only. The API/planner path does not execute
  SQL, write to the database, call the audit writer service, create database
  connections, read `DATABASE_URL`, call Energi Data Service, call
  DMI/weather APIs, use ML, use LLMs, write files, generate PDFs, or perform
  automatic control, dispatch, activation, or operational energy-system
  integration. The manual audit persistence preview only prints a dry-run SQL
  plan. The write smoke script defaults to dry-run and only writes one
  synthetic event to a local `audit_events` table when explicitly executed
  with a local database URL. A manual local Postgres write smoke has verified
  repository insert, idempotency, and verify-read by `event_id` locally. The
  writer service validates and executes through a supplied connection only.
  Future runtime audit persistence remains deferred and requires explicit
  review.
- No DMI/weather ingestion exists yet.
- No auth, Azure deployment, scheduled ingestion jobs, or production database
  exist.
- No monitoring or observability setup exists yet.
- No human approval workflow exists beyond documentation and disclaimers.

Recommended next MVP direction: the audit foundation is now sufficient for the
MVP foundation. Move product work back toward stable data ingestion,
DMI/weather ingestion, dashboard graphs, forecast UI, dashboard data trust
indicators, and PDF export from the UI. Do not add production audit writes
yet, do not add automatic scheduled report generation, do not fetch data in
the report builder, do not use an LLM as the forecast or reporting engine, and
do not add control, dispatch, or activation behavior.

Future documentation modules may add a manual local smoke guide for running
the backend and frontend together against the controlled DB-backed freshness
read path. Dashboard graph improvements may also be handled separately. These
future steps must not add ingestion, automation, database writes, or
operational control behavior without explicit review.

## EDS Data Freshness Preview API

`GET /api/energy/freshness?price_area=DK1|DK2` is a read-only preview API for
future freshness indicators over stored Energi Data Service-derived data. It
exists because product work has moved back toward data/dashboard readiness
while preserving the `v0.1` human-review boundary.

The endpoint is implemented in `backend/app/api/energy_freshness.py` and uses
the query-plan builders in
`backend/app/db/repositories/energy_freshness.py`, with focused API coverage
in `backend/tests/test_api_energy_freshness.py`. It supports only `DK1` and
`DK2`; unsupported `price_area` values return HTTP 400.

The response is preview JSON only and includes:

- `price_area`
- `dry_run: true`
- `database_query_executed: false`
- `database_write_performed: false`
- `requires_database_url: false`
- `freshness_plans`
- `spot_price_freshness_plan`
- `power_balance_freshness_plan`
- `warnings`
- `safety_boundary`

The preview plans include spot price freshness, power balance freshness, and
combined energy freshness summaries. They return parameterized SELECT SQL
plans only, including params, source labels, earliest/latest timestamp fields,
row count fields, and empty-row warnings.

Safety boundary: the preview API does not call live Energi Data Service, call
DMI/weather APIs, connect to a database, read `DATABASE_URL`, execute SQL,
write to a database, add migrations, schedule jobs, add Azure infrastructure,
add auth, use ML/LLMs, write audit events, add report/PDF wiring, or perform
control, dispatch, activation, closed-loop workflows, live control signals, or
operational functionality.

Observed validation:

- Focused API energy freshness tests passed: `12 passed, 1 warning`.
- Full backend suite passed: `442 passed, 1 warning`.
- `py_compile` passed.
- Forbidden-pattern grep matched only required safety flags and
  negative/safety assertions in tests.
- `git diff --check` passed.
- No live DB writes were performed.

The frontend dashboard keeps an energy freshness dry-run action backed by
`fetchEnergyFreshness()`. The card manually calls this endpoint for the
selected `DK1`/`DK2` price area through the existing
`NEXT_PUBLIC_API_BASE_URL` pattern. It displays `dry_run`,
`database_query_executed`, `database_write_performed`,
`requires_database_url`, spot price and power balance freshness plan status,
warnings, and the safety boundary. UI wording explicitly labels the response
as a freshness query plan preview only, with no database query executed, no
database write performed, no new EDS/DMI fetch, and read-only decision
support.

Observed frontend validation:

- `npm run build` passed.
- `git diff --check` passed.
- `npm run lint` did not exist.
- `npm run typecheck` did not exist.
- No backend server was started.
- No frontend dev server was started.
- No database was accessed.
- No SQL was executed.
- No live Energi Data Service or DMI/weather APIs were called.

## Manual Energy Freshness DB Smoke

`scripts/energy_freshness_db_smoke.py` is a manual/local smoke script for
DB-executed freshness reads over stored energy data. It reuses
`backend/app/db/repositories/energy_freshness.py` for dry-run query-plan JSON
and `backend/app/db/repositories/energy_freshness_reader.py` for explicit
DB-executed SELECT reads.

Dry-run:

```bash
python3 scripts/energy_freshness_db_smoke.py --price-area DK1 --pretty
```

Local read:

```bash
python3 scripts/energy_freshness_db_smoke.py --price-area DK1 --execute --database-url postgresql://localhost/flexsignal_ai --pretty
```

Default behavior is dry-run only. Real DB reads require both `--execute` and
an explicit local `--database-url`; localhost, `127.0.0.1`, and local
socket-style PostgreSQL URLs are accepted, while remote/cloud URLs are
rejected. The script prints JSON with dry-run/execution flags, no-write flags,
freshness plan or result, warnings, and the read-only human-review safety
boundary. It writes no data, does not fetch EDS/DMI data, does not expose an
API, does not add frontend behavior, and must not be used for automatic
control, dispatch, or activation.

Observed local DB smoke results:

| Area | DB query executed | DB write performed | Spot price rows | Spot price latest timestamp | Power balance rows | Power balance latest timestamp | Warnings |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
| DK1 | true | false | 53 | `2026-06-11T21:45:00+02:00` | 53 | `2026-06-10T17:00:00+02:00` | `[]` |
| DK2 | true | false | 50 | `2026-06-11T21:45:00+02:00` | 50 | `2026-06-10T17:00:00+02:00` | `[]` |

The observed smoke used explicit `--execute` and a local `--database-url`.
Reads were SELECT-only through the existing freshness reader. No database
writes were performed, no live Energi Data Service or DMI/weather calls were
made, and no backend or frontend server was started. This proves local
DB-backed freshness reads work against the observed local database contents.
It does not yet mean production freshness monitoring exists; it prepares
future DB-backed API/dashboard freshness indicators only.

Manual freshness smoke non-goals: this documentation step did not change
backend behavior, modify frontend behavior, add a backend endpoint, add
database code, write to a database, add migrations, call live Energi Data
Service, call DMI/weather APIs, add auth, add Azure infrastructure, add ML/LLM
behavior, write audit events, wire report/PDF flows, or add control,
dispatch, activation, closed-loop, live-control, or operational functionality.

Interpretation: the energy freshness preview API and frontend dry-run action
are read-only and expose query-plan previews only. The manual local DB smoke
proves the existing reader can execute local DB-backed freshness SELECTs when a
human explicitly supplies `--execute` and a local `--database-url`, but it
does not create production freshness monitoring, fetch new data, or write
data. The controlled DB-backed read API now executes those freshness SELECT
queries for `DK1`/`DK2` when `DATABASE_URL` is configured at request time, and
the frontend can display those read results through the backend API only. Live
ingestion remains deferred.

## DB-Backed Energy Freshness Read API

`GET /api/energy/freshness/read?price_area=DK1|DK2` is the first controlled
DB-backed freshness API for stored energy data. It prepares future dashboard
live data trust indicators while preserving the `v0.1` read-only
decision-support boundary.

The endpoint supports only `DK1` and `DK2`; invalid `price_area` values return
HTTP 400. `DATABASE_URL` is required at request time only. The app can import
and expose the route without `DATABASE_URL`; if the variable is missing during
request execution, the endpoint returns a safe HTTP 503 and does not return the
raw database URL.

The endpoint uses `backend/app/db/repositories/energy_freshness_reader.py` and
executes SELECT-only freshness reads. It does not write to the database, fetch
new Energi Data Service data, call DMI/weather APIs, trigger ingestion, add
database migrations, add audit writes, add scheduler/Azure/auth/report/PDF
wiring, or perform control, dispatch, activation, closed-loop, live-control,
or operational functionality. The frontend can manually display the endpoint
response, but it does not execute SQL or access the database directly.

Successful responses include:

- `price_area`
- `dry_run: false`
- `database_query_executed: true`
- `database_write_performed: false`
- `requires_database_url: true`
- `freshness_result`
- `spot_price_freshness`
- `power_balance_freshness`
- `warnings`
- `safety_boundary`

The safety boundary is:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Observed validation:

- Focused API freshness read tests passed: `9 passed, 1 warning`.
- Full backend suite passed: `483 passed, 1 warning`.
- `py_compile` passed.
- Forbidden-pattern grep matched only defensive/negative assertions in tests.
- `git diff --check` passed.
- Tests used mocked database connections only.
- No live DB writes were performed.

Observed local API smoke:

The backend was started locally with
`DATABASE_URL=postgresql://localhost/flexsignal_ai` and the DB-backed read
endpoint was called directly. The endpoint performed SELECT-only freshness
reads, no database writes were performed, no live EDS/DMI calls were made, no
ingestion was triggered, and no frontend changes were involved.

| Endpoint price area | HTTP | `dry_run` | `database_query_executed` | `database_write_performed` | `requires_database_url` | Spot price rows | Spot price latest timestamp | Power balance rows | Power balance latest timestamp |
| --- | ---: | --- | --- | --- | --- | ---: | --- | ---: | --- |
| DK1 | 200 | false | true | false | true | 53 | `2026-06-11T21:45:00+02:00` | 53 | `2026-06-10T17:00:00+02:00` |
| DK2 | 200 | false | true | false | true | 50 | `2026-06-11T21:45:00+02:00` | 50 | `2026-06-10T17:00:00+02:00` |

Invalid `price_area=SE3` returned HTTP 400 with `Unsupported price_area`.
The read-only human-review safety boundary was preserved. This proves local
DB-backed API freshness reads work against the observed local data. It does
not yet mean production monitoring or Azure deployment exists, and it prepares
manual frontend data trust display only.

Frontend wiring: the dashboard energy freshness card now has a manual
`Load DB-backed read` action backed by `fetchEnergyFreshnessRead()`. It uses
the existing `NEXT_PUBLIC_API_BASE_URL` pattern to call
`GET /api/energy/freshness/read?price_area=DK1|DK2` and displays SELECT-only
read results from stored local/configured database data: `price_area`,
`dry_run`, `database_query_executed`, `database_write_performed`,
`requires_database_url`, `spot_price_freshness.latest_timestamp`,
`spot_price_freshness.row_count`,
`power_balance_freshness.latest_timestamp`,
`power_balance_freshness.row_count`, warnings, and the read-only human-review
safety boundary. If the backend returns HTTP 503 because `DATABASE_URL` is
missing, the UI shows
`DB-backed freshness read requires backend DATABASE_URL.`

Interpretation: this API and frontend display path are read-only SELECT
execution only. They improve MVP data trust readiness, still do not perform
ingestion, and do not verify production freshness or production monitoring.

## DB-Executed Energy Freshness Reader

`backend/app/db/repositories/energy_freshness_reader.py` is a backend
foundation for future DB-backed freshness indicators over stored EDS-derived
energy data. It implements:

- `read_spot_price_freshness`
- `read_power_balance_freshness`
- `read_energy_freshness_summary`

The reader uses the existing EDS freshness query-plan read model and executes
SELECT-only plans through an explicit caller-provided database connection. It
does not create database connections, read `DATABASE_URL`, call live Energi
Data Service, call DMI/weather APIs, write data, expose a FastAPI endpoint, or
connect to the frontend.

SQL safety: every plan must be parameterized and must start with `SELECT`.
Unsafe SQL is rejected before cursor execution. Blocked mutating tokens
include `INSERT`, `UPDATE`, `DELETE`, `UPSERT`, `CREATE`, `ALTER`, `DROP`,
`TRUNCATE`, and `MERGE`. No write behavior is implemented.

Reader outputs are structured dictionaries only. Spot price and power balance
results include `price_area`, `database_query_executed=true`,
`database_write_performed=false`, `source_label`, `earliest_timestamp`,
`latest_timestamp`, `row_count`, an empty-row warning when no rows are present,
and the read-only human-review `safety_boundary`. The combined summary
includes `spot_price_freshness`, `power_balance_freshness`, `warnings`, and
the same safety boundary.

Safety boundary:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Observed validation recorded `24 passed` focused reader tests,
`466 passed, 1 warning` for the full backend suite, passing `py_compile`, and
passing `git diff --check`. Forbidden-pattern grep matched only
safety-boundary keys, defensive blocked-token validation, and negative
assertions/unsafe-plan tests. The tests used fake connection/cursor objects
only; no live DB writes were performed.

Interpretation: the DB-executed freshness reader, observed manual local DB
smoke, controlled DB-backed read API, and frontend card wiring prove the
system can display read-only freshness SELECT results for `DK1`/`DK2`. The
path does not fetch new data, does not write data, and does not add
automation.

## Audit Event Foundation

`audit-event-v0` builds deterministic audit event dictionaries for read-only
decision-support actions such as forecast previews, current-risk reviews,
report summary builds, Markdown rendering, and PDF export requests. It accepts
only caller-provided fields, validates explicit event, actor, and outcome
values, requires timezone-aware `occurred_at_utc`, rejects empty required
resource/action fields, and rejects secret-like metadata keys.

The event id is deterministic and derived from event version, event type, actor
type, actor id, occurrence time, resource type, resource id, action, and
outcome. The builder always includes a safety boundary declaring read-only
decision support, no automatic control, no dispatch, no activation, no
operational energy-system integration, and human review required.

The database persistence foundation for `audit-event-v0` is present but not
wired into runtime flows. Alembic migration `0002_audit_events.py` defines an
`audit_events` table with `event_id` as the primary/idempotency key,
timestamp, actor, resource/action/outcome fields, `decision_support_only`,
JSONB `safety_boundary`, JSONB `metadata`, and useful lookup indexes.
`backend/app/audit/repository.py` validates event dictionaries from
`build_audit_event(...)`, preserves the required read-only safety boundary,
serializes JSON fields as parameters, and builds `ON CONFLICT (event_id) DO
NOTHING` insert SQL.

This foundation does not automatically persist audit logs, write files, expose
a FastAPI endpoint, add frontend UI, connect report/PDF flows, run scheduled
logging, connect to auth/Entra, call Energi Data Service, call DMI/weather
APIs, use ML, use LLMs, add Azure infrastructure, add secrets, or perform live
database writes by itself. It is designed for future compliance and audit
logging while preserving the `v0.1` read-only decision-support boundary. It
must not be used for automatic control, dispatch, activation, closed-loop
workflows, live control signals, or operational energy-system integration.

`scripts/audit_event_preview.py` is a manual synthetic local JSON preview for
`audit-event-v0`. It uses fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
imports `build_audit_event(...)`, uses synthetic/caller-provided fields only,
and prints compact JSON by default or indented JSON with `--pretty`.

```bash
python3 scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py --pretty
python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty
```

Supported event types are `forecast_preview_requested`,
`current_risk_viewed`, `report_summary_built`,
`report_markdown_rendered`, `report_pdf_exported`, and `all`. The default is
`all`, which prints an `events` array. Single-event previews print one `event`
object. The preview uses safe metadata only, such as `price_area`, relevant
`report_version`, relevant `output_format`, `synthetic_preview_only=true`, and
`local_only=true`.

The audit preview does not persist audit logs, write files, access a database,
expose an API, use frontend code, call EDS/DMI, use ML, use LLMs, or perform
automatic control, dispatch, or activation. It is read-only decision-support
audit structure only. Future audit work can wire explicit read-only flows to
the audit persistence foundation only after review.

Observed manual audit-event preview validation:

- `python3 -m py_compile scripts/audit_event_preview.py` passed.
- `python3 scripts/audit_event_preview.py` printed compact JSON with an
  `events` array.
- `python3 scripts/audit_event_preview.py --pretty` printed indented JSON.
- `python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty`
  printed one `report_pdf_exported` event.
- `python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty`
  printed one `forecast_preview_requested` event.
- `python3 scripts/audit_event_preview.py --event-type invalid-event` failed
  safely with exit code `2` and a clear argparse invalid-choice validation
  error.
- Forbidden-pattern grep on `scripts/audit_event_preview.py` returned no
  matches.
- `git diff --check` passed.

Generated preview events covered `forecast_preview_requested`,
`current_risk_viewed`, `report_summary_built`,
`report_markdown_rendered`, and `report_pdf_exported`. Observed events used
`event_version=audit-event-v0`, deterministic `audit_evt_...` event ids,
fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, and `local_only=true`.

Each event included a `safety_boundary` with
`read_only_decision_support=true`, `no_automatic_control=true`,
`no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Interpretation: the audit-event preview works locally with
synthetic/caller-provided data and demonstrates the audit-event shape for
read-only decision-support actions. The persistence foundation now defines the
schema and SQL builder, but preview/API/frontend/report flows do not
automatically persist events, connect to auth or actor identity providers,
create operational logs, or provide production audit persistence. Explicit
read-only wiring can be considered next only as a separate reviewed module,
without adding automatic control, dispatch, activation, scheduling, or
operational functionality.

### Audit DB Persistence Foundation Validation

The `audit-event-v0` data-structure foundation, manual audit-event preview
script, and preview-result documentation existed before the audit database
persistence foundation was added in PR #87. PR #87 added schema/repository
readiness only: an Alembic migration for `audit_events` and
`backend/app/audit/repository.py`, without wiring audit persistence into API,
frontend, report/PDF flows, automatic logging, or live execution paths.

The migration defines `event_id` as the primary/idempotency key and stores
`event_version`, `event_type`, `actor_type`, `actor_id`,
`occurred_at_utc`, `resource_type`, `resource_id`, `action`, `outcome`,
`decision_support_only`, JSONB `safety_boundary`, JSONB `metadata`, and
`created_at_utc` with a database default. Indexes support lookup by
`occurred_at_utc`, `event_type`, resource, and actor. The repository validates
events before persistence planning, preserves the required read-only safety
boundary, uses parameterized INSERT construction, and adds
`ON CONFLICT (event_id) DO NOTHING`. Validation did not perform live database
writes.

Initial local validation before PR review documented:

- Backend tests passed with `310 passed, 1 warning`.
- `py_compile` passed for `backend/app/audit/events.py` and
  `backend/app/audit/repository.py`.
- Safety-boundary grep matched only expected terms:
  `no_automatic_control`, `no_dispatch`, and `no_activation`.
- `git diff --check` passed.

GitHub backend-tests initially failed before merge because route exposure under
the newer FastAPI/Starlette CI/test context did not list these concrete paths
in `app.routes`: `/api/risk/current`, `/api/risk/preview`, and
`/api/forecast/preview`. The observed failing tests were
`tests/test_api_energy.py::test_app_exposes_no_mutating_write_methods` and
`tests/test_api_risk.py::test_app_import_without_database_url_still_exposes_current_risk_route`.
This was interpreted as a route-registration exposure issue in the test/import
context, not as live database writes or audit persistence execution. The
branch was not merged while backend-tests were red.

The fix updated `backend/app/main.py` with a small route-registration helper
so `app.routes` exposes concrete paths under the test environment.
`DATABASE_URL` validation remains request-time only. Endpoint logic was not
changed, and no new API behavior, DB writes, scheduler, frontend behavior,
control behavior, or operational functionality was added.

Post-fix validation documented:

- Focused route tests passed with `2 passed, 1 warning`.
- Full backend suite passed with `310 passed, 1 warning`.
- `git diff --check` passed.
- The PR diff was checked to ensure no `.pyc`, virtualenv, cache, or generated
  files were included.
- GitHub backend-tests were re-run and green before merge.
- PR #87 was merged only after backend-tests were green.

The final merged audit DB persistence PR included:

- `backend/alembic/versions/0002_audit_events.py`
- `backend/app/audit/repository.py`
- `backend/app/main.py`
- `backend/tests/test_audit_event_repository.py`
- `README.md`
- `docs/HUMAN_OVERSIGHT.md`
- `docs/MODEL_CARD.md`
- `docs/BACKTEST_RESULTS.md`
- `CHANGELOG.md`

Interpretation: the audit DB persistence foundation is schema/repository
readiness for future explicit audited read-only flows. It does not yet prove
production audit persistence, identify real users through Entra ID, or create
runtime audit logs. Future wiring should remain manual and reviewed; a future
module may add controlled repository execution with an explicit database
connection and tests. Do not add automatic audit logging yet, and do not
connect frontend or report-download flows to persistence until explicit
review.

### Audit Persistence Dry-Run Preview

`scripts/audit_persistence_preview.py` is a manual local dry-run preview for
audit persistence planning. It imports `build_audit_event(...)` and
`build_audit_event_insert_sql(...)`, uses synthetic/caller-provided fields
only, and prints compact JSON by default or indented JSON with `--pretty`.

```bash
python3 scripts/audit_persistence_preview.py
python3 scripts/audit_persistence_preview.py --pretty
python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty
```

The default event type is `report_pdf_exported`. The output includes
`dry_run=true`, `database_write_performed=false`,
`requires_database_url=false`, the `audit-event-v0` dictionary, and a
repository-built persistence plan for the `audit_events` table with
`ON CONFLICT (event_id) DO NOTHING`.

The script does not persist audit events, access a database, require
`DATABASE_URL`, run SQL, expose an API, use frontend code, write files,
generate PDFs, call EDS/DMI, use ML, use LLMs, add scheduling, add Azure
infrastructure, add auth, add secrets, or add automatic audit logging. It is
read-only decision-support audit persistence preview only. Future controlled
repository execution would require an explicit database connection and tests
in a separate reviewed module.

Observed manual audit persistence dry-run validation:

| Command/check | Observed result |
| --- | --- |
| `python3 -m py_compile scripts/audit_persistence_preview.py` | Passed. |
| `python3 scripts/audit_persistence_preview.py` | Printed compact JSON. |
| `python3 scripts/audit_persistence_preview.py --pretty` | Printed indented JSON. |
| `python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty` | Built a dry-run `forecast_preview_requested` audit event and persistence plan. |
| `python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty` | Built a dry-run `report_pdf_exported` audit event and persistence plan. |
| `python3 scripts/audit_persistence_preview.py --event-type invalid-event` | Failed safely with exit code `2` and argparse invalid-choice output. |
| Forbidden-pattern grep on `scripts/audit_persistence_preview.py` | Returned no matches. |
| `git diff --check` | Passed. |

Observed output included `dry_run=true`,
`database_write_performed=false`, `requires_database_url=false`, `event`, and
`persistence_plan`. The event included
`event_version=audit-event-v0`, a deterministic `audit_evt_...` event id,
fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, and `local_only=true`. The event safety
boundary preserved `read_only_decision_support=true`,
`no_automatic_control=true`, `no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Observed `persistence_plan` output included the `audit_events` table target,
SQL/SQL preview, parameter keys/params, `event_id` as the idempotency key, and
`ON CONFLICT (event_id) DO NOTHING` conflict behavior.

Interpretation: the audit persistence preview works locally with
synthetic/caller-provided data and demonstrates how `audit-event-v0` can be
transformed into a parameterized persistence plan. It does not prove live DB
persistence, perform live database writes, run SQL, connect to a database,
expose an API, use frontend code, integrate with report/PDF flows, generate
PDFs, call EDS/DMI, use ML/LLM behavior, add scheduling/Azure/auth/secrets, or
add control, dispatch, activation, automatic audit logging, or operational
functionality. A future module may add a controlled local audit persistence
write test against a local database, but that must be separate and reviewed.
Do not connect report/PDF/frontend/API flows to audit persistence until
explicit review.

### Audit DB Write Smoke

`scripts/audit_db_write_smoke.py` is a manual local-only smoke script for one
deterministic synthetic `audit-event-v0` write. It imports
`build_audit_event(...)` and the audit repository SQL builder, uses fixed
`occurred_at_utc=2026-01-01T00:00:00Z`, safe metadata only, and defaults to
dry-run without connecting to a database.

```bash
python3 scripts/audit_db_write_smoke.py --pretty
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty
```

Real writes require both `--execute` and an explicit local `--database-url`.
Accepted local URL examples include `postgresql://localhost/flexsignal_ai`,
`postgresql://127.0.0.1/flexsignal_ai`, and
`postgresql:///flexsignal_ai`. Remote/cloud-style URLs are refused by default,
and the raw database URL is not printed.

When executed, the script writes only to `audit_events`, runs the same
parameterized `ON CONFLICT (event_id) DO NOTHING` insert twice to confirm
idempotency, commits, and can read the row back by `event_id` with
`--verify-read`.

This smoke script does not write energy, forecast, or report data; expose an
API; add frontend code; add automatic audit logging; integrate report/PDF/API
or frontend flows; create a scheduler; use Azure infrastructure; add auth or
secrets; call EDS/DMI; use ML or LLMs; or add control, dispatch, activation,
or operational functionality.

Observed manual audit DB write smoke validation:

| Command/check | Observed result |
| --- | --- |
| `python3 -m py_compile scripts/audit_db_write_smoke.py backend/tests/test_audit_db_write_smoke.py` | Passed. |
| `python -m pytest tests/test_audit_db_write_smoke.py -q` | Focused smoke tests passed: `7 passed`. |
| `python -m pytest` | Full backend suite passed: `317 passed, 1 warning`. |
| `python3 scripts/audit_db_write_smoke.py` | Default dry-run passed. |
| `python3 scripts/audit_db_write_smoke.py --pretty` | Pretty dry-run passed. |
| `python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty` | `forecast_preview_requested` dry-run passed. |
| `python3 scripts/audit_db_write_smoke.py --execute` | Failed safely with exit code `2` because no explicit `--database-url` was provided. |
| `python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://remote.example.com/flexsignal_ai` | Failed safely with exit code `2` because remote/cloud-style URLs are rejected by default. |
| Forbidden-pattern grep on script and test | Returned no matches. |
| `git diff --check` | Passed. |

Those earlier checks did not perform live DB writes. A later manual local
Postgres smoke did perform the first actual local `audit_events` write for the
deterministic synthetic event.

Observed manual local audit DB write commands:

```bash
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
```

Alembic used `PostgresqlImpl`, assumed transactional DDL, ran migration
`0001_initial_schema` to `0002_audit_events`, added the audit-event-v0
persistence foundation, and succeeded.

First smoke result:

- `conflict_behavior`: `ON CONFLICT (event_id) DO NOTHING`
- `database_write_performed`: `true`
- `dry_run`: `false`
- `execute_requested`: `true`
- `event_id`: `audit_evt_f8ea1513efa7fa0067b0ca04`
- `event_type`: `report_pdf_exported`
- `inserted_attempts`: `2`
- `local_database_only`: `true`
- `rowcount_first_insert`: `1`
- `rowcount_second_insert`: `0`
- `table`: `audit_events`
- `verify_read_performed`: `true`
- `warnings`: `[]`
- `verified_row` was returned by `event_id`

Second smoke result:

- The same `event_id` and `event_type` were used.
- `database_write_performed`: `true`
- `rowcount_first_insert`: `0`
- `rowcount_second_insert`: `0`
- `verify_read_performed`: `true`
- `verified_row` was returned.
- This confirms idempotency across repeated script executions.

The verified row included `event_version=audit-event-v0`,
`event_type=report_pdf_exported`, `action=preview_report_pdf_export`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, `resource_type=report_pdf`,
`resource_id=report-summary-v0:DK1:synthetic-pdf`, and metadata
`local_only=true`, `output_format=pdf`, `price_area=DK1`,
`report_version=report-summary-v0`, and `synthetic_preview_only=true`.

The event was constructed deterministically. The verified row returned
`occurred_at_utc` as `2026-01-01T01:00:00+01:00`; interpret this as
database/session timezone rendering of the stored `timestamptz` instant, not
as a blocker for the smoke result. Future code may normalize read-back display
to UTC if needed.

The output preserved `read_only_decision_support=true`,
`no_automatic_control=true`, `no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`. The raw `DATABASE_URL` was not printed.

Interpretation: local `audit_events` DB write is now manually verified.
Repository insert works against local Postgres, idempotency works via
`ON CONFLICT (event_id) DO NOTHING`, and verify-read by `event_id` works. This
does not mean production audit persistence is enabled, does not add automatic
audit logging, and does not connect audit persistence to API, frontend,
report, or PDF flows. No FastAPI endpoint, frontend behavior, scheduler,
Azure infrastructure, auth/Entra integration, live EDS/DMI calls, ML/LLM use,
control, dispatch, activation, or operational functionality was added. A
future module may add a read-only API-side audit logging design or manual API
audit dry-run, but automatic audit persistence must not be wired into runtime
flows yet and production DB writes require explicit review.

### Audit Writer Service Foundation Validation

`backend/app/audit/writer.py` adds a backend foundation for explicitly writing
validated `audit-event-v0` records through the existing repository insert
path. It provides `write_audit_event(conn, event)` and the
`execute_audit_event_insert` alias. Both require an explicit caller-provided
database connection object. The service does not create database connections,
does not read `DATABASE_URL`, and is not wired into FastAPI, frontend,
report/PDF, scheduler, auth, or automatic audit logging flows.

Before executing SQL, the writer validates the event as `audit-event-v0`,
requires `decision_support_only=true`, and preserves the full read-only safety
boundary:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

The writer uses the existing audit repository insert SQL builder. Invalid
events raise `ValueError` and execute no SQL. Valid events return a structured
result containing `event_id`, `event_type`, `table`,
`database_write_performed`, `rowcount`, `conflict_behavior`,
`safety_boundary_preserved`, and `warnings`.

Observed audit writer validation:

- Focused audit writer tests passed: `14 passed`.
- Full backend suite passed: `331 passed, 1 warning`.
- `py_compile` passed for the writer and tests.
- Grep matched only safety-boundary strings and negative/static assertions.
- `git diff --check` passed.
- Tests used fake connection/cursor objects only.
- No live database writes were performed.

Interpretation: the audit writer service is a backend foundation only. It
proves a testable write boundary around the repository insert path, but it
does not enable production audit persistence, add automatic audit logging,
expose an API, modify frontend behavior, or connect report/PDF flows to audit
persistence. Runtime integration remains intentionally deferred. The reviewed
API audit dry-run preview is documented separately and remains inspection-only.
Do not wire automatic audit persistence into runtime flows yet, and do not add
production DB writes without explicit review.

### Runtime Audit Event Factory Validation

`backend/app/audit/runtime_events.py` adds a pure backend factory for
standardized future runtime `audit-event-v0` dictionaries. It uses existing
`build_audit_event(...)`, explicit primitive inputs, minimal safe metadata,
and `runtime_factory_version=audit-runtime-event-factory-v0`.

Implemented factory functions:

- `build_current_risk_viewed_event`
- `build_forecast_preview_requested_event`
- `build_report_summary_built_event`
- `build_report_markdown_rendered_event`
- `build_report_pdf_exported_event`

Standardized mappings:

| Event type | Action | Resource type | Resource id includes |
| --- | --- | --- | --- |
| `current_risk_viewed` | `view_current_risk` | `risk_snapshot` | `price_area` |
| `forecast_preview_requested` | `preview_forecast` | `forecast_preview` | `price_area`, `forecast-window-v0` |
| `report_summary_built` | `build_report_summary` | `report_summary` | `price_area`, `report-summary-v0` |
| `report_markdown_rendered` | `render_report_markdown` | `report_markdown` | `price_area`, `report-summary-v0` |
| `report_pdf_exported` | `preview_report_pdf_export` | `report_pdf` | `price_area`, `report-summary-v0` |

Runtime factory metadata may include `price_area`, `request_id`, `source`,
`forecast_window_version`, `report_version`, `output_format`, optional
forecast `model_version`, and `runtime_factory_version`. It must not include
raw `DATABASE_URL`, secrets, tokens, raw user claims, full request headers, or
full request bodies.

Each generated event preserves `event_version=audit-event-v0`,
`decision_support_only=true`, `read_only_decision_support=true`,
`no_automatic_control=true`, `no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Observed validation documented focused runtime event tests passing with
`30 passed`, the full backend suite passing with `361 passed, 1 warning`,
`py_compile` passing for `runtime_events` and tests, forbidden-pattern grep
returning no matches, and `git diff --check` passing. Tests were pure unit
tests only, and no live database writes were performed.

Interpretation: the runtime audit event factory is a backend foundation only.
It standardizes future runtime audit-event construction but does not enable
production audit persistence, add automatic audit logging, call the audit
writer, create database connections, read `DATABASE_URL`, expose an API,
modify frontend behavior, write files, call EDS/DMI, use ML/LLMs, connect
report/PDF flows, add scheduler/auth/Azure infrastructure, or add control,
dispatch, activation, or operational functionality. Runtime integration
remains intentionally deferred. The reviewed API audit dry-run preview is
documented separately and remains inspection-only; automatic audit persistence
must not be wired into runtime flows yet and production DB writes require
explicit review.

### Runtime Audit Persistence Dry-Run Planner Validation

`backend/app/audit/runtime_plan.py` adds a pure backend dry-run planner for
future runtime audit persistence. The planner combines the runtime event
factory with the audit repository INSERT-plan builder and returns dictionaries
only. It is not wired into FastAPI routes, frontend behavior, report/PDF
flows, the audit writer service, or automatic logging.

Implemented planner functions:

- `build_current_risk_viewed_audit_plan`
- `build_forecast_preview_requested_audit_plan`
- `build_report_summary_built_audit_plan`
- `build_report_markdown_rendered_audit_plan`
- `build_report_pdf_exported_audit_plan`

Each plan includes `dry_run=true`, `database_write_performed=false`,
`requires_database_url=false`, `event`, `persistence_plan`, `event_id`,
`event_type`, `table=audit_events`, `conflict_behavior`, `safety_boundary`,
and `warnings`. The persistence plan previews the repository INSERT for
`audit_events`; `event_id` is the idempotency key and conflict behavior is
`ON CONFLICT (event_id) DO NOTHING`. SQL and parameters are previewed only,
and no SQL is executed.

Metadata remains minimal and safe. The planner output does not include raw
`DATABASE_URL`, secrets, tokens, full request headers, or full request bodies.
Every generated event preserves `read_only_decision_support=true`,
`no_automatic_control=true`, `no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Observed validation:

- Focused runtime plan tests passed: `32 passed`.
- Full backend suite passed: `393 passed, 1 warning`.
- `py_compile` passed for `runtime_plan` and tests.
- Forbidden-pattern grep matched only safety/negative assertions in tests.
- `git diff --check` passed.
- Tests were pure unit tests only.
- No live database writes were performed.

Interpretation: the runtime planner prepared the reviewed API audit dry-run
preview path documented below. It does not enable production audit
persistence, automatic audit logging, audit writer calls, database writes,
database connections, `DATABASE_URL` handling, frontend behavior,
report/PDF runtime wiring, migrations, schedulers, Azure infrastructure,
auth/Entra integration, live EDS/DMI calls, ML/LLM behavior, control,
dispatch, activation, or operational functionality. Do not wire automatic
audit persistence into runtime flows yet, and do not add production DB writes
without explicit review.

### Audit API Dry-Run Preview Validation

`POST /api/audit/preview` exposes the runtime audit persistence dry-run
planner through a reviewed read-only preview API. It accepts only these
supported event types:

- `current_risk_viewed`
- `forecast_preview_requested`
- `report_summary_built`
- `report_markdown_rendered`
- `report_pdf_exported`

The endpoint accepts only `DK1` and `DK2` price areas. When actor fields are
omitted, it defaults to `actor_type=local_user` and
`actor_id=unknown-local-user`; `local_user` is an allowed audit actor type.

The response is a dry-run plan only. It includes `dry_run=true`,
`database_write_performed=false`, `requires_database_url=false`, `event`,
`persistence_plan`, `event_id`, `event_type`, `table=audit_events`,
`conflict_behavior`, `safety_boundary`, and `warnings`. The persistence plan
comes from `backend/app/audit/runtime_plan.py`, targets `audit_events`, uses
`event_id` as the idempotency key, and previews
`ON CONFLICT (event_id) DO NOTHING`.

The endpoint does not execute SQL, write to the database, call the audit
writer service, create database connections, read `DATABASE_URL`, call
external APIs, write files, trigger report/PDF generation, modify frontend
behavior, add automatic audit logging, or connect audit persistence to
forecast/risk/report/PDF runtime flows.

Validation behavior:

- Unsupported `event_type` returns HTTP 400.
- Unsupported `price_area` outside `DK1`/`DK2` returns HTTP 400.
- Responses contain no raw `DATABASE_URL`, secrets, tokens, full headers, or
  full request bodies.
- The read-only decision-support safety boundary is preserved.

Observed validation:

- Route allowlist was updated so `/api/audit/preview` is treated as an allowed
  read-only preview POST.
- Focused mutating-route check passed: `1 passed, 1 warning`.
- Focused audit preview API tests passed: `16 passed, 1 warning`.
- Full backend suite passed: `409 passed, 1 warning`.
- `py_compile` passed.
- `git diff --check` passed.
- No live DB writes were performed.

Interpretation: the audit preview API is a reviewed read-only preview
endpoint. It exposes audit persistence plans for inspection only. It does not
enable production audit persistence, add automatic audit logging, or connect
audit persistence to forecast, risk, report, PDF, or frontend runtime flows.
Future runtime audit persistence remains deferred and requires explicit
review.

## Report Summary Foundation

`report-summary-v0` builds a deterministic structured report payload from
caller-provided current-risk output and caller-provided `forecast-window-v0`
output. It returns report metadata, current-risk and forecast-window summaries,
model versions, key findings, recommended human actions, safety notes,
limitations, and source notes.

This foundation is backend Python logic only. It does not fetch data, read or
write a database, expose an API, call Energi Data Service, call DMI/weather
APIs, train ML models, use LLMs, add auth, add
scheduler behavior, or add Azure infrastructure. It is read-only decision
support only and must not be used for automatic control, dispatch, activation,
closed-loop workflows, asset connections, plant/device commands, live control
signals, or autonomous decisions.

`render_report_summary_markdown(...)` converts a caller-provided
`report-summary-v0` dictionary into a deterministic Markdown string. It renders
report metadata, current-risk summary, forecast-window summary, key findings,
recommended human actions, safety notes, limitations, and source notes. Missing
current-risk or forecast summaries are rendered as clear unavailable sections
instead of crashing, and optional missing fields use safe fallback text.

The Markdown renderer is pure backend Python formatting logic only. It does
not write files, fetch data, access a database, expose an API, use frontend
code, use ML, or use LLMs. The rendered Markdown remains read-only decision
support only, requires human review, and must not be used for automatic
control, dispatch, activation, or autonomous decisions.

`scripts/report_summary_preview.py` is a manual synthetic local JSON preview
for `report-summary-v0`. It uses fixed `generated_at_utc=2026-01-01T00:00:00Z`
and in-script caller-provided current-risk and forecast-window data only.

```bash
python3 scripts/report_summary_preview.py
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

The script does not generate PDF files, fetch data, access the database, run
SQL, expose an API, run frontend code, use ML, use LLMs, or perform automatic
control, dispatch, activation, or operational functionality. It is synthetic
read-only decision support only and requires human review before planning.

`scripts/report_markdown_preview.py` is a manual synthetic local Markdown
preview for `report-summary-v0`. It uses the same fixed
`generated_at_utc=2026-01-01T00:00:00Z` boundary and in-script
caller-provided current-risk and forecast-window data only. It calls
`build_report_summary(...)`, then `render_report_summary_markdown(...)`, and
prints Markdown to stdout without writing files.

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

The Markdown preview supports `standard`, `high-risk`,
`missing-current-risk`, and `missing-forecast` scenarios. The output includes
title, report metadata, current-risk summary, forecast-window summary, key
findings, recommended human actions, safety notes, limitations, and source
notes. Missing current-risk or forecast inputs render as unavailable sections
while preserving the remaining available summary.

The Markdown preview uses synthetic/caller-provided data only. It does not
generate PDF files, write files, fetch data, access the database, run SQL,
expose an API, use frontend code, use ML, use LLMs, or perform automatic
control, dispatch, activation, or operational functionality. It is read-only
decision support only, requires human review before planning, and must not be
used for automatic control, dispatch, or activation.

`render_report_markdown_pdf_bytes(...)` converts caller-provided Markdown into
simple PDF bytes using ReportLab. The renderer returns bytes only; it does not
write files, fetch data, access a database, expose an API, use frontend code,
use ML, use LLMs, or perform automatic control, dispatch, activation, or
operational functionality. The PDF layout is intentionally simple: headings,
wrapped paragraphs, bullet/list-like lines, and page breaks as needed. It uses
built-in fonts only and no images, charts, remote resources, HTML/browser
rendering, CSS, templates, or custom font files.

`scripts/report_pdf_preview.py` is a manual synthetic local PDF preview for
`report-summary-v0`. It uses fixed
`generated_at_utc=2026-01-01T00:00:00Z`, builds the report with
`build_report_summary(...)`, renders Markdown with
`render_report_summary_markdown(...)`, renders PDF bytes with
`render_report_markdown_pdf_bytes(...)`, and writes exactly one local PDF file
only when `--output PATH` is explicitly provided.

```bash
python3 scripts/report_pdf_preview.py --output /tmp/flexsignal_report_preview.pdf
python3 scripts/report_pdf_preview.py --price-area DK2 --scenario high-risk --output /tmp/flexsignal_report_high_risk.pdf
python3 scripts/report_pdf_preview.py --scenario missing-current-risk --output /tmp/flexsignal_report_missing_current.pdf
python3 scripts/report_pdf_preview.py --scenario missing-forecast --output /tmp/flexsignal_report_missing_forecast.pdf
```

The PDF preview refuses to overwrite an existing output path unless `--force`
is provided. It supports `standard`, `high-risk`, `missing-current-risk`, and
`missing-forecast` scenarios. It prints a compact JSON summary to stdout and a
safety warning to stderr. It does not expose an API, add frontend download
behavior, fetch data, access the database, run SQL, call Energi Data Service,
call DMI/weather APIs, use ML, use LLMs, or perform automatic control,
dispatch, activation, or operational functionality. It is synthetic local
preview only, read-only decision support only, and requires human review.

### Report Summary Preview Results

The manual report-summary preview script was run locally with synthetic
caller-provided data only:

```bash
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

All four runs printed the synthetic-only warning, used
`generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`. Safety notes were present in every payload and
explicitly prohibited automatic control, dispatch, and activation. Limitations
were present and included caller-provided data only, no database read/write,
no live API calls, no ML training in the report builder, and no LLM use in the
report builder.

Observed synthetic results:

| Scenario | Command | Price area | Current risk summary | Forecast summary | Key result |
| --- | --- | --- | --- | --- | --- |
| `standard` | `python3 scripts/report_summary_preview.py --pretty` | DK1 | available, medium, score 45 | available, 3 windows | Key findings reported medium current risk, no high-risk forecast window, and caller-provided data only; recommended actions included routine monitoring, review of the medium-risk window, required human review, source-context verification, and no control/dispatch/activation use. |
| `high-risk` | `python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty` | DK2 | available, high, score 75 | available, 3 windows | Current risk was high and the `24-48h` forecast window was high risk with `max_risk_score=80`; key findings mentioned high risk and actions required human review before planning. |
| `missing-current-risk` | `python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty` | DK1 | unavailable | available, 3 windows | The payload remained safe, added the limitation `missing or incomplete current risk input`, and still included the forecast-window summary. |
| `missing-forecast` | `python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty` | DK1 | available, medium, score 45 | unavailable, 0 windows | The payload remained safe, added the limitation `missing or incomplete forecast input`, and still included the current-risk summary. |

Interpretation: `report-summary-v0` preview works locally with synthetic
caller-provided data and creates deterministic report payloads. It does not
generate PDF files yet, fetch data, read or write a database, expose an API,
use the frontend, use ML, or use LLMs. It remains read-only decision support
only and must not be used for automatic control, dispatch, or activation.

### Report Markdown Preview Results

The manual report Markdown preview script was run locally with synthetic
caller-provided data only:

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

All four runs printed the synthetic-only warning to stderr and rendered
Markdown to stdout only. All reports used
`generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`. The rendered Markdown included the title, report
metadata, current-risk summary, forecast-window summary, key findings,
recommended human actions, safety notes, limitations, and source notes.

Observed Markdown results:

| Scenario | Command | Price area | Current risk summary | Forecast summary | Observed Markdown result |
| --- | --- | --- | --- | --- | --- |
| `standard` | `python3 scripts/report_markdown_preview.py` | DK1 | available, medium, score `45` | available, 3 windows | Rendered the report title, metadata, current risk, all three forecast windows, key findings, recommended human actions, safety notes, limitations, and source notes. |
| `high-risk` | `python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk` | DK2 | available, high, score `75` | available, 3 windows | Rendered high current risk, a high-risk `24-48h` forecast finding with `max_risk_score=80`, human-review actions, and safety notes prohibiting automatic control, dispatch, and activation. |
| `missing-current-risk` | `python3 scripts/report_markdown_preview.py --scenario missing-current-risk` | DK1 | unavailable | available, 3 windows | Rendered current risk as unavailable, kept the forecast summary available, included `missing or incomplete current risk input`, and did not crash. |
| `missing-forecast` | `python3 scripts/report_markdown_preview.py --scenario missing-forecast` | DK1 | available, medium, score `45` | unavailable | Rendered the forecast window summary as unavailable, kept the current-risk summary available, included `missing or incomplete forecast input`, and did not crash. |

Interpretation: Markdown preview works locally with synthetic/caller-provided
data, renders `report-summary-v0` to readable Markdown, prints to stdout only,
does not write files, does not fetch data, does not read or write a database,
does not expose an API, does not use frontend code, and does not use ML or
LLMs. PDF export v0 is now available only as a manual local explicit-output
script over the same report-summary and Markdown rendering path. It remains
read-only decision support only and must not be used for automatic control,
dispatch, or activation.

### Report PDF Smoke-Test Results

Manual/local PDF export v0 was validated after `report-summary-v0`, Markdown
rendering, the Markdown preview script, and Markdown preview result
documentation. It uses synthetic/caller-provided report data, builds
`report-summary-v0`, renders Markdown, then renders local PDF bytes. It writes
a PDF only when an explicit `--output` path is provided and requires `--force`
before overwriting an existing output path. No API endpoint or frontend
download exists.

Observed validation:

- Backend tests passed: `257 passed, 1 warning`.
- `py_compile` passed.
- `git diff --check` passed.
- Manual PDF preview runs passed.
- PDF byte/header check passed.
- Temporary PDFs were removed.
- Repository PDF check passed: no PDF files were left in the repository.
- Grep found only required safety wording and no forbidden integration imports.

Observed temporary PDF artifacts:

| Scenario | Output path | Bytes |
| --- | --- | ---: |
| `standard` | `/tmp/flexsignal_report_preview.pdf` | 9697 |
| `high-risk` | `/tmp/flexsignal_report_high_risk.pdf` | 9930 |
| `missing-current-risk` | `/tmp/flexsignal_report_missing_current.pdf` | 9263 |
| `missing-forecast` | `/tmp/flexsignal_report_missing_forecast.pdf` | 6918 |

All generated files started with `%PDF`, were larger than `1000` bytes, were
temporary validation artifacts, were removed after validation, and were not
committed to the repository.

Interpretation: PDF export v0 works for manual/local synthetic report
previews and proves the `report-summary-v0` to Markdown to PDF path. It is not
production report export, is not connected to live data or frontend, is not
exposed as an API, is not scheduled, does not use ML or LLMs, does not read or
write database data, and does not call Energi Data Service or DMI/weather
APIs. It remains read-only decision support only, requires human review, and
must not be used for automatic control, dispatch, activation, autonomous
decisions, operational energy-system integration, or automatic report jobs.

## Forecast Preview API

`POST /api/forecast/preview` returns deterministic `0-24h`, `24-48h`, and
`48-72h` forecast-window summaries from caller-provided DK1/DK2 rows.

The frontend dashboard includes a manual "Forecast preview" card that calls
`POST /api/forecast/preview` only after the user clicks "Load forecast
preview". It posts deterministic synthetic/caller-provided demo rows with a
timezone-aware `generated_at_utc`, uses only the backend API base URL helper,
does not auto-load or poll, does not call Energi Data Service or DMI/weather
APIs from the browser, and does not read or write a database.

The endpoint is read-only decision support only. It does not fetch Energi Data
Service data, call DMI/weather APIs, read or write a database, persist payloads,
start jobs, train ML models, use LLMs, require secrets, or perform automatic
control, dispatch, or activation. It is not production forecast validation and
must not be used for automatic control, dispatch, activation, closed-loop
workflows, asset connections, plant/device commands, or live control signals.

## Forecast Window Preview Results

The synthetic forecast-window preview script was run locally with:

```bash
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

All three runs used `generated_at_utc=2026-01-01T00:00:00Z`,
`model_version=rule-engine-v0+forecast-window-v0`, and
`decision_support_only=true`.

Observed synthetic results:

| Scenario | Price area | Key result |
| --- | --- | --- |
| `balanced` | DK1 | Returned `0-24h`, `24-48h`, and `48-72h` windows with row counts `2`, `2`, and `2`; risk levels `medium`, `low`, and `medium`; max risk scores `45`, `30`, and `35`. |
| `high-risk` | DK2 | The `24-48h` window became `high` risk with `max_risk_score=75`; reason codes included `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`, demonstrating max-risk aggregation. |
| `empty-window` | DK1 | The `24-48h` window had `row_count=0`, `risk_level=unknown`, `average_risk_score=null`, and `max_risk_score=null`, demonstrating insufficient caller-provided data handling. |

These are synthetic local preview results only. The script aggregates
caller-provided rows deterministically, does not use ML or LLMs, is not
DMI/weather based yet, does not fetch data, does not read or write a database,
and is not production forecast validation. The backend preview API now exposes
the same caller-provided aggregation boundary for JSON requests only. It
remains read-only decision support for human review and must not be used for
automatic control, dispatch, or activation.

### Forecast Preview API Smoke Test Results

`POST /api/forecast/preview` was smoke-tested manually with the backend started
without `DATABASE_URL`. This confirms the endpoint can summarize
caller-provided forecast rows without database access. No frontend was used,
and no ingestion, database writes, SQL, live Energi Data Service calls,
DMI/weather calls, scheduler, Azure infrastructure, auth, secrets, ML
training, LLM use, control, dispatch, activation, or operational functionality
was used or added.

Valid DK1 forecast preview request:

- HTTP `200`
- `price_area`: `DK1`
- `generated_at_utc`: `2026-01-01T00:00:00Z`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- windows returned: `3`

Observed DK1 windows:

| Window | Row count | Risk level | Max risk score | Average risk score | Top reason codes observed |
| --- | ---: | --- | ---: | ---: | --- |
| `0-24h` | 1 | low | 30 | 30.0 | `MODERATE_PRICE`, `MODERATE_RENEWABLE_SHARE` |
| `24-48h` | 1 | high | 75 | 75.0 | `HIGH_RENEWABLE_SHARE`, `NEGATIVE_PRICE` |
| `48-72h` | 0 | unknown | null | null | none; `average_confidence_score=0.0` |

High-risk DK2 forecast preview request:

- HTTP `200`
- `price_area`: `DK2`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- `24-48h` returned `row_count=1`, `risk_level=high`,
  `max_risk_score=75`, `average_risk_score=75.0`, and reason codes including
  `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`.
- `0-24h` and `48-72h` were `unknown` because `row_count=0`.

Validation observations:

- A request using `price_area=SE3` returned a validation error indicating that
  input should be `DK1` or `DK2`.
- A request using timezone-naive `generated_at_utc` returned a validation error
  indicating that `generated_at_utc` must be timezone-aware.

Interpretation: the forecast preview API works for caller-provided rows,
returns deterministic `0-24h`, `24-48h`, and `48-72h` windows, demonstrates
max-risk aggregation, handles empty windows as `unknown`, and validates DK1/DK2
plus timezone-aware `generated_at_utc`. This is read-only decision support for
human review, not production forecast validation.

### Frontend Forecast Preview Smoke Test After CORS Fix

The frontend "Forecast preview" card was smoke-tested manually from `main`
after the local CORS preflight fix was merged. The backend was started without
`DATABASE_URL`, and the frontend was started locally. The test used only the
Forecast preview card; spot prices, power balance, and current surplus risk
cards were not used. No ingestion, database writes, SQL, live Energi Data
Service calls, DMI/weather calls, scheduler, Azure infrastructure, auth,
secrets, ML training, LLM use, automatic control, dispatch, activation, or
operational functionality was run or added.

Observed frontend behavior:

- The Forecast preview card was visible.
- The read-only badge was visible.
- The synthetic/caller-provided preview warning was visible.
- No forecast data appeared before clicking the manual button.
- Clicking "Load forecast preview" triggered the preview request.
- The card displayed `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, `generated_at_utc=2026-01-01T00:00:00Z`, and
  three windows: `0-24h`, `24-48h`, and `48-72h`.

Observed DK1 frontend result:

| Window | Row count | Risk level | Max risk score | Average risk score | Notes |
| --- | ---: | --- | ---: | ---: | --- |
| `0-24h` | 1 | low | 30 | 30 | top reason codes included `EXCHANGE_NET_NOT_USED_V0`, `MODERATE_PRICE`, and `MODERATE_RENEWABLE_SHARE` |
| `24-48h` | 1 | high | 75 | 75 | top reason codes included `EXCHANGE_NET_NOT_USED_V0`, `HIGH_RENEWABLE_SHARE`, and `NEGATIVE_PRICE`; recommended human action required human review |
| `48-72h` | 1 | low | 10 | 10 | top reason codes included `ELEVATED_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0`, and `NORMAL_PRICE` |

Observed DK2 frontend result:

- The selected price area was switched to `DK2`.
- Clicking "Load forecast preview" returned forecast-window data again.
- The card displayed the same three forecast windows and decision-support-only
  fields without frontend error.
- This confirmed that the selected price area can be used by the frontend
  helper for the forecast preview flow.

The previous browser error was caused by `OPTIONS` preflight returning `400`.
After the CORS fix, the frontend successfully loaded forecast preview data from
`POST /api/forecast/preview`, practically confirming the local CORS preflight
path for the Forecast preview card.

Interpretation: the frontend forecast preview card works locally, manually
calls `POST /api/forecast/preview`, displays deterministic `0-24h`, `24-48h`,
and `48-72h` windows, and uses synthetic/caller-provided demo rows only. This
is not production forecast validation, not ML, not LLM based, not DMI/weather
based yet, does not fetch EDS/DMI data from the browser, does not read or write
a database, and does not auto-load or poll. It remains local frontend/backend
smoke-test documentation only, read-only decision support only, and requires
human review.

## Historical Local EDS Import Plan

A documentation-only plan now defines how to expand local EDS-derived samples
for safer read-only backtesting without changing runtime behavior.

Planned local validation scope:

- Datasets: `DayAheadPrices` and `ElectricityProdex5MinRealtime`.
- Price areas: `DK1` and `DK2`.
- Batch size: `limit 50` per dataset and price area is validated for explicit
  manual confirmed local writes. `100` and `500` still require future explicit
  enhancement.
- Validation: row counts by `price_area`, distinct `source_record_id` counts,
  repeated-import idempotency, and local DB read-only backtests for `DK1` and
  `DK2` documenting `risk_level_counts` and `average_risk_score`.

Safety gates:

- Local PostgreSQL only, with `DATABASE_URL` targeting `localhost` or
  `127.0.0.1`.
- Dry-run before confirmed writes.
- Confirmed writes require explicit `--confirm-local-db-write`.
- No production database, Azure database, scheduled job, backend startup
  ingestion, frontend-triggered ingestion, or automatic polling loop.
- No code, backend behavior, frontend behavior, secrets, auth, ML training,
  LLM use, control, dispatch, activation, or operational workflow is added by
  this plan.

This larger local sample would still not be full model validation. Outcome
labels, DMI/weather data, and a 24-72 hour forecast remain absent, and
`rule-engine-v0` remains deterministic and simple.

### Manual EDS Historical Batch Dry-Run

The manual historical batch wrapper dry-run was documented with:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --continue-on-error
```

Observed wrapper result:

- `dry_run=true`, `confirmed_local_write=false`, `local_only=true`, and
  `decision_support_only=true`.
- `limit=50`, `price_areas=DK1, DK2`, and datasets
  `DayAheadPrices`, `ElectricityProdex5MinRealtime`.
- `commands_planned=4`, `commands_succeeded=4`, `commands_failed=0`, and
  `child_exit_codes=[0, 0, 0, 0]`.
- Child dry-runs returned HTTP `200` for `DayAheadPrices` DK1/DK2 and
  `ElectricityProdex5MinRealtime` DK1/DK2, with `50` raw records, `50`
  normalized records, `50` SQL commands, and `committed=false` for each
  combination.

Limit 50 dry-run is validated for all supported DK1/DK2 dataset combinations.
No database writes were committed. This validates command orchestration and the
normalization path only. Confirmed writes still require explicit
`--confirm-local-db-write`, and `100` and `500` still require future explicit
enhancement.

Safety notes: local PostgreSQL dry-run only; no committed writes, production
database, Azure resources, scheduler, live API polling, backend startup ingestion,
frontend-triggered ingestion, automatic polling loop, ML training, LLM use,
automatic control, dispatch, activation, or operational functionality.

### Manual EDS Historical Batch Confirmed Local Write

The manual historical batch wrapper was also run as a confirmed local
PostgreSQL write with explicit confirmation:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --confirm-local-db-write --continue-on-error
```

Before the confirmed batch write, `spot_prices` contained DK1 `13` and DK2
`10` rows, and `power_balance` contained DK1 `13` and DK2 `12` rows. The
confirmed batch summary reported `child_exit_codes=[0, 0, 0, 0]`,
`commands_planned=4`, `commands_succeeded=4`, `commands_failed=0`,
`confirmed_local_write=true`, `dry_run=false`, `limit=50`,
`local_only=true`, and `decision_support_only=true` for `DK1`/`DK2` and
`DayAheadPrices`/`ElectricityProdex5MinRealtime`.

Each child confirmed write returned HTTP `200`, with `50` raw records, `50`
normalized records, `50` SQL commands, and `committed=true`. The target tables
were `spot_prices` for `DayAheadPrices` and `power_balance` for
`ElectricityProdex5MinRealtime`.

After the confirmed batch write, counts were:

| Table | DK1 | DK2 |
| --- | ---: | ---: |
| `spot_prices` | 53 | 50 |
| `power_balance` | 53 | 50 |

The same confirmed batch command was run a second time. The second run again
reported `child_exit_codes=[0, 0, 0, 0]`, `commands_planned=4`,
`commands_succeeded=4`, `commands_failed=0`, `confirmed_local_write=true`,
`dry_run=false`, `limit=50`, and `local_only=true`. Counts remained unchanged,
so no duplicate explosion was observed and the repeated import was idempotent
for the same 50-record batch.

Read-only local DB backtests after the confirmed batch write observed:

| Area | Command limit | Spot prices read | Power balance read | Risk counts | Average risk score |
| --- | ---: | ---: | ---: | --- | ---: |
| DK1 | 100 | 53 | 53 | low=1, medium=52, high=0 | 34.5283 |
| DK2 | 100 | 50 | 50 | low=42, medium=8, high=0 | 21.8 |

Interpretation: the wrapper successfully performed confirmed local writes for
all supported DK1/DK2 dataset combinations, the repeated import was idempotent,
DK1 remained mostly medium risk on the expanded local sample, and DK2 now
includes both low and medium risk. This is stronger technical validation than
the 10-row sample, but still not full model validation because the dataset is
still small and has no outcome labels.

Safety notes: local PostgreSQL only; manual confirmed write only; explicit
`--confirm-local-db-write` was required; no production database, Azure
resources, scheduler, live API polling, backend startup ingestion,
frontend-triggered ingestion, automatic polling loop, ML training, LLM use,
automatic control, dispatch, activation, or operational functionality.

### Read-Only API And Frontend Smoke Test After Limit 50 Local Import

After the manual `limit 50` EDS confirmed local write populated local
PostgreSQL, read-only API and frontend behavior were smoke-tested against the
larger local sample. No ingestion, database writes, live Energi Data Service
polling, tests, or server startup were run by this documentation update.

API commands observed:

```bash
curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK1"
curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK2"
```

Observed API results:

| Area | HTTP | Timestamp | Risk level | Risk score | Confidence | Reason codes | Source rows |
| --- | ---: | --- | --- | ---: | ---: | --- | --- |
| DK1 | 200 | `2026-06-10T17:00:00+02:00` | medium | 35 | 1.0 | `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | `spot_prices=true`, `power_balance=true` |
| DK2 | 200 | `2026-06-10T17:00:00+02:00` | low | 20 | 1.0 | `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | `spot_prices=true`, `power_balance=true` |

Both responses used `model_version=rule-engine-v0`,
`decision_support_only=true`, and `metadata.source_tables_used` containing
`spot_prices` and `power_balance`.

Frontend smoke-test at `http://localhost:3000` observed:

- DK1 manual Load spot prices returned 5 `spot_prices` rows.
- DK1 manual Load power balance returned 5 `power_balance` rows.
- DK1 manual Load current risk showed `risk_level=medium`, `risk_score=35`,
  `confidence_score=1`, and reason codes including `NORMAL_PRICE`,
  `HIGH_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`.
- DK2 manual Load spot prices returned 5 `spot_prices` rows.
- DK2 manual Load power balance returned 5 `power_balance` rows.
- DK2 manual Load current risk showed `risk_level=low`, `risk_score=20`,
  `confidence_score=1`, and reason codes including `NORMAL_PRICE`,
  `MODERATE_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`.
- The read-only badge was visible for both price areas.

Interpretation: the read-only dashboard works for DK1 and DK2 after the
`limit 50` local import, and the frontend still requires manual button clicks.
No automatic loading, polling, dispatch, activation, or control behavior was
observed. The current-risk endpoint still reads from local PostgreSQL and
returns decision-support-only results. This is a local MVP smoke-test, not
production validation.

Safety notes: local PostgreSQL only; read-only API/UI smoke-test only; no
ingestion, database writes, live Energi Data Service polling, Azure resources,
scheduler, backend startup ingestion, frontend-triggered ingestion, automatic
polling loop, ML training, LLM use, automatic control, dispatch, activation, or
operational functionality.

## Not Included in v0.1

- Automatic activation of consumption or flexibility.
- Live control signals to any assets, plants, devices, or energy infrastructure.
- Critical operational system responsibilities.
- LLMs as the primary forecasting engine or sole decision-making component.
- Production infrastructure deployment.
- Production runtime database integration or automatic startup migrations.
- Production-ready frontend workflows.
- Dispatch, activation, closed-loop workflows, or operational energy system
  integration.
- LLM use as a decision engine or autonomous decision-maker.

## Technology Stack

- Frontend: Next.js and TypeScript
- Backend: Python FastAPI
- Database: PostgreSQL with TimescaleDB
- Data jobs: Azure Functions or Azure Container Apps Jobs
- Hosting: Azure App Service or Azure Container Apps
- Secrets: Azure Key Vault
- Logs: Application Insights and Log Analytics
- Auth: Microsoft Entra ID
- AI/LLM: explanation and report generation only

## Database Schema

A documented PostgreSQL/TimescaleDB schema baseline is available in
[`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md). The schema is not yet wired
into the FastAPI application and no database migrations are run in `v0.1`.

## Backend Local Development

The current backend is a minimal FastAPI API plus pure Python decision-support
logic for `v0.1`. It does not include control endpoints, authentication,
runtime forecast data ingestion, forecast-window API exposure, or
infrastructure deployment.

`backend/app/forecast/window_forecast.py` provides the current
`forecast-window-v0` foundation as pure Python logic only. It accepts
caller-provided rows, reuses `rule-engine-v0` scoring, returns
decision-support-only window summaries, and must not be used for automatic
control, dispatch, or activation.

`scripts/forecast_window_preview.py` provides a manual synthetic local preview
of `forecast-window-v0` with fixed `generated_at_utc` output and in-script
caller-provided rows only:

```bash
python3 scripts/forecast_window_preview.py
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

The preview does not require `DATABASE_URL`, read or write a database, run SQL,
fetch Energi Data Service data, call DMI/weather APIs, expose an API endpoint,
run frontend code, train ML/LLM components, schedule jobs, use Azure, or add
control, dispatch, activation, or operational functionality.

From the `backend/` directory:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Backend tests also run in GitHub Actions on pull requests and pushes to `main`.

Start the API locally:

```bash
uvicorn app.main:app --reload
```

### Local risk preview API smoke test

Manual local validation was documented with the backend started manually:

```bash
python -m uvicorn app.main:app --reload
```

The valid smoke test posted caller-provided JSON only to
`POST /api/risk/preview`:

```json
{
  "price_area": "DK1",
  "timestamp_utc": "2026-06-09T21:45:00+02:00",
  "price_dkk_per_mwh": -10,
  "production_mw": 1000,
  "wind_onshore_mw": 500,
  "wind_offshore_mw": 350,
  "solar_mw": 50,
  "consumption_mw": 900
}
```

Observed local result:

- `risk_level`: `high`
- `risk_score`: `75`
- `confidence_score`: `1.0`
- `reason_codes` included `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`

An invalid input smoke test using `price_area` `SE3` returned a validation
error. Only `DK1` and `DK2` are accepted.

Important boundary notes:

- The risk preview endpoint used caller-provided JSON only.
- No database connection was used.
- No database writes were performed.
- No live Energi Data Service polling was performed.
- No LLM or ML model was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

### Local DK2 EDS ingestion validation

Manual local DK2 ingestion validation used tiny Energi Data Service samples
only.

Dry-run validation observed:

- `DayAheadPrices` DK2 returned HTTP `200`.
- `DayAheadPrices` raw record count was `2`.
- `DayAheadPrices` normalized record count was `2`.
- `DayAheadPrices` SQL command count was `2`.
- `DayAheadPrices` committed was `false`.
- `ElectricityProdex5MinRealtime` DK2 returned HTTP `200`.
- `ElectricityProdex5MinRealtime` raw record count was `2`.
- `ElectricityProdex5MinRealtime` normalized record count was `2`.
- `ElectricityProdex5MinRealtime` SQL command count was `2`.
- `ElectricityProdex5MinRealtime` committed was `false`.

Confirmed local write validation observed:

- `DayAheadPrices` DK2 committed was `true`.
- `ElectricityProdex5MinRealtime` DK2 committed was `true`.
- The writes were local PostgreSQL only.
- The writes were manual confirmed local writes only.

Local row counts after DK2 ingest:

- `spot_prices` DK1: `3`
- `spot_prices` DK2: `2`
- `power_balance` DK1: `3`
- `power_balance` DK2: `2`

Important boundary notes:

- Local PostgreSQL only.
- Manual validation only.
- No production database was used.
- No Azure resources were used.
- No startup migrations were run.
- No automated ingestion job was added.
- No live polling loop was added.
- No ML training was performed.
- No LLM was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

### Local current risk API smoke test

Manual local validation was documented with the backend started manually:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

The smoke test called the current-risk endpoint for DK1:

```text
GET /api/risk/current?price_area=DK1
```

Observed local result:

- `risk_level`: `medium`
- `risk_score`: `35`
- `confidence_score`: `1.0`
- `reason_codes` included `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`
- `metadata.source_tables_used` included `spot_prices` and `power_balance`
- `metadata.spot_price_row_found`: `true`
- `metadata.power_balance_row_found`: `true`

The smoke test also called the current-risk endpoint for DK2:

```text
GET /api/risk/current?price_area=DK2
```

Observed local result:

- backend returned HTTP `200`
- `price_area`: `DK2`
- `risk_level`: `low`
- `risk_score`: `20`
- `confidence_score`: `1.0`
- `reason_codes` included `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`
- `metadata.source_tables_used` included `spot_prices` and `power_balance`
- `metadata.spot_price_row_found`: `true`
- `metadata.power_balance_row_found`: `true`

An invalid input smoke test called:

```text
GET /api/risk/current?price_area=SE3
```

The observed result was a validation error. Only `DK1` and `DK2` are accepted.

Important boundary notes:

- The endpoint read from local PostgreSQL only.
- The endpoint used the existing read-only query path.
- No database writes were performed.
- No live Energi Data Service polling was performed.
- No startup migrations were run.
- No Azure resources were used.
- No production database was used.
- No LLM or ML model was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

### Local DK2 read-only DB risk backtest result

Manual local read-only risk backtest validation was run for DK2 using existing
local PostgreSQL rows only. Before the backtest, local table counts were:

- `spot_prices` DK1: `3`
- `spot_prices` DK2: `2`
- `power_balance` DK1: `3`
- `power_balance` DK2: `2`

The command run was:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK2 --limit 10 --pretty
```

Observed local result:

- `price_area` was `DK2`.
- `limit` was `10`.
- `read_only` was `true`.
- `decision_support_only` was `true`.
- `pairing_strategy` was `nearest_timestamp_v0_1`.
- `spot_price_rows_read` was `2`.
- `power_balance_rows_read` was `2`.
- `composed_rows` was `2`.
- `backtest_summary.total_rows` was `2`.
- `backtest_summary.evaluated_rows` was `2`.
- `backtest_summary.failed_rows` was `0`.
- `backtest_summary.risk_level_counts.low` was `2`.
- `backtest_summary.risk_level_counts.medium` was `0`.
- `backtest_summary.risk_level_counts.high` was `0`.
- `backtest_summary.average_risk_score` was `20.0`.
- `backtest_summary.average_confidence_score` was `1.0`.
- `backtest_summary.reason_code_counts` included `NORMAL_PRICE: 2`,
  `MODERATE_RENEWABLE_SHARE: 2`, and `EXCHANGE_NET_NOT_USED_V0: 2`.
- `backtest_summary.missing_price_count` was `0`.
- `backtest_summary.missing_generation_data_count` was `0`.
- `backtest_summary.model_version` was `rule-engine-v0`.

Interpretation:

- DK2 local read-only path is now validated.
- The DK2 current risk endpoint returned low risk on the tiny local sample.
- The DK2 local DB backtest returned low risk for both composed rows.
- This is still technical validation, not full model validation.
- The dataset is tiny and not enough for performance conclusions.

Important boundary notes:

- Local PostgreSQL only.
- SELECT/read-only backtest only.
- No database writes were performed by the backtest.
- No live EDS polling was performed by the backtest.
- No backend or frontend server was started for the backtest.
- No startup migrations were run.
- No production database was used.
- No Azure resources were used.
- No ML training was performed.
- No LLM was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

### Local read-only DB risk backtest result after nearest-timestamp pairing

Manual local read-only risk backtest validation was rerun after
`nearest_timestamp_v0_1` pairing was merged, using existing local PostgreSQL
rows only. Before the backtest, local table counts were:

- `spot_prices`: `3`
- `power_balance`: `3`

The command run was:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK1 --limit 10 --pretty
```

Observed local result:

- `price_area` was `DK1`.
- `limit` was `10`.
- `read_only` was `true`.
- `decision_support_only` was `true`.
- `pairing_strategy` was `nearest_timestamp_v0_1`.
- `spot_price_rows_read` was `3`.
- `power_balance_rows_read` was `3`.
- `composed_rows` was `3`.
- `backtest_summary.total_rows` was `3`.
- `backtest_summary.evaluated_rows` was `3`.
- `backtest_summary.failed_rows` was `0`.
- `backtest_summary.risk_level_counts.low` was `1`.
- `backtest_summary.risk_level_counts.medium` was `2`.
- `backtest_summary.risk_level_counts.high` was `0`.
- `backtest_summary.average_risk_score` was `26.6667`.
- `backtest_summary.average_confidence_score` was `1.0`.
- `backtest_summary.reason_code_counts` included `NORMAL_PRICE: 3`,
  `EXCHANGE_NET_NOT_USED_V0: 3`, `HIGH_RENEWABLE_SHARE: 2`, and
  `ELEVATED_RENEWABLE_SHARE: 1`.
- `backtest_summary.missing_price_count` was `0`.
- `backtest_summary.missing_generation_data_count` was `0`.
- `backtest_summary.model_version` was `rule-engine-v0`.

Interpretation:

- `nearest_timestamp_v0_1` pairing is active.
- On the tiny local DK1 sample, the risk distribution remained unchanged
  compared with the previous simple pairing run.
- This is expected because the local dataset only contains 3 composed rows.
- This is still technical validation, not full model validation.
- A larger historical dataset is required before drawing performance
  conclusions.

Important boundary notes:

- Local PostgreSQL only.
- SELECT/read-only only.
- No database writes were performed.
- No live EDS polling was performed.
- No backend or frontend server was started.
- No startup migrations were run.
- No production database was used.
- No Azure resources were used.
- No ML training was performed.
- No LLM was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

## Frontend Local Development

The frontend is a minimal Next.js dashboard for `v0.1` read-only decision
support. It includes a DK1/DK2 selector and manual buttons for loading recent
spot prices, power balance rows, and the current surplus risk from existing
backend read-only API endpoints. It does not fetch automatically on page load,
poll live endpoints, call Energi Data Service directly, forecast, dispatch,
activate, or control energy assets.

From the `frontend/` directory:

```bash
npm install
npm run build
npm run dev
```

The frontend uses a backend API base URL helper for manual read-only API
requests. It defaults to `http://127.0.0.1:8000` and can be overridden with
`NEXT_PUBLIC_API_BASE_URL`.

Manual frontend requests use:

- `GET /api/energy/spot-prices?price_area=DK1|DK2&limit=5`
- `GET /api/energy/power-balance?price_area=DK1|DK2&limit=5`
- `GET /api/risk/current?price_area=DK1|DK2`

The read-only disclaimer remains visible in the dashboard:
`Read-only decision support — no automatic control`.

### Local frontend dashboard shell smoke test

Manual local frontend validation was performed by starting the dashboard shell
from the `frontend/` directory:

```bash
npm install
npm run build
npm run dev
```

`next build` completed successfully, TypeScript passed, and the static `/`
route was generated.

The browser smoke-test opened `http://127.0.0.1:3000` and confirmed:

- FlexSignal AI title visible.
- Read-only decision support -- no automatic control badge visible.
- DK1/DK2 selector visible.
- Spot prices card visible.
- Power balance card visible.
- Manual Load spot prices button visible.
- Manual Load power balance button visible.
- Idle, loading, error, row count, and compact result table states available.
- Backend API base URL helper visible as `http://127.0.0.1:8000`.
- Browser copy states that the frontend does not call Energi Data Service
  directly.
- No error screen.

The frontend makes no automatic page-load API requests, direct Energi Data
Service calls, polling requests, database writes, auth calls, Azure resource
changes, forecasting/model calls, or control, dispatch, activation, or
operational functionality. Backend API requests are made only when a user
presses one of the manual load buttons.

Known local development note: opening the Next.js dev server through
`127.0.0.1` showed a development-only cross-origin warning for dev resources.
Use `http://localhost:3000` during local development unless `allowedDevOrigins`
is configured later. This warning did not block the page render.

### Local frontend-to-backend read-only smoke test

Manual local frontend-to-backend validation was performed with the backend
started manually from the `backend/` directory:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

The frontend was started manually from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The browser opened `http://localhost:3000`. The manual read-only UI actions
were:

- Selected DK1.
- Clicked Load spot prices.
- Clicked Load power balance.
- Clicked Load current risk.

Observed local result:

- Spot prices displayed 3 rows for DK1.
- Power balance displayed 3 rows for DK1.
- Current surplus risk displayed `risk_level` `medium`.
- `risk_score` was `35`.
- `confidence_score` was `1`.
- `reason_codes` included `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`.
- `model_version` was `rule-engine-v0`.
- `decision_support_only` was `true`.
- `metadata.source_tables_used` showed `spot_prices` and `power_balance`.
- `metadata.spot_price_row_found` was `true`.
- `metadata.power_balance_row_found` was `true`.
- No Failed to fetch error appeared.
- Backend logs showed HTTP 200 for both read-only API calls.
- The local-development CORS fix worked.

Important boundary notes:

- The frontend only called the backend API helper.
- No direct Energi Data Service calls were made from the frontend.
- No polling or automatic refresh was used.
- No database writes were performed.
- No live EDS polling was performed.
- No startup migrations were run.
- No Azure resources were used.
- No production database was used.
- No LLM or ML model was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

## Compliance Principles

- Read-only decision support in `v0.1`.
- Human review before any operational action.
- No autonomous control.
- No control signals to energy infrastructure.
- Auditability for forecasts, recommendations, explanations, and user actions.
- Least-privilege access to systems and data.
- LLMs are limited to explanation and reporting, not core forecasting or final decision-making.
