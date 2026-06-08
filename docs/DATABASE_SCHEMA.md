# Database Schema

FlexSignal AI `v0.1` uses PostgreSQL with TimescaleDB as the intended database
foundation. The current schema is a documented baseline with a matching Alembic
initial migration. It is not connected to the FastAPI app and migrations are not
run automatically.

`v0.1` remains read-only decision support. The database stores source data,
forecast outputs, explanations, and audit events for human review. It does not
store control signals, dispatch instructions, asset activation data, live control
state, or closed-loop operational workflows.

## Schema Location

- Baseline SQL: `backend/app/db/schema.sql`
- Alembic configuration: `backend/alembic.ini`
- Initial migration: `backend/alembic/versions/0001_initial_schema.py`
- Backend database notes: `backend/app/db/README.md`
- Future local validation runbook: `docs/LOCAL_DATABASE_RUNBOOK.md`

Source-to-schema field mapping is documented in `docs/DATA_FIELD_MAPPING.md`.

`schema.sql` is the human-readable baseline for review and planning. Alembic is
the reproducible migration path for creating the same schema in a PostgreSQL
database when migrations are run manually.

## Tables

### `spot_prices`

Stores DK1 and DK2 electricity spot prices by UTC market interval. The table
keeps both EUR/MWh and DKK/MWh values as internal MWh-based market units so
downstream reporting can use the same audited source records without
recalculating canonical storage values. Sources using kWh units, such as
Elprisenligenu, must be explicitly converted before ingestion.

Key fields include `price_area`, `timestamp_utc`, `price_eur_per_mwh`,
`price_dkk_per_mwh`, `source`, `source_record_id`, and `ingested_at_utc`.

### `power_balance`

Stores production, consumption, import/export, and related energy-system
measurements for DK1 and DK2. Nullable measurement columns allow the MVP to
ingest partial source records while preserving source and timestamp traceability.

Key fields include `production_mw`, `consumption_mw`, `wind_onshore_mw`,
`wind_offshore_mw`, `solar_mw`, and `exchange_net_mw`.

### `weather_observations`

Stores weather features relevant for baseline forecasting and backtesting. The
schema starts with weather inputs that are explainable and commonly useful for
renewable generation and surplus-risk analysis: wind speed, wind direction,
temperature, and cloud cover.

Locations are represented by `location_id` until final station, grid-cell, or
price-area mapping is decided.

### `surplus_risk_forecasts`

Stores model outputs for human review. Each row records the price area, forecast
creation time, forecast window, risk level, confidence score, expected surplus,
economic potential, model identity, optional explanation text, and optional input
data window.

`recommended_action` is human-readable decision-support text only. It is not a
control command, dispatch instruction, activation request, or operational signal.

### `ingestion_runs`

Audits ingestion job attempts by source and dataset. The table records start and
finish times, status, processed record counts, and optional error messages. It is
included to support traceability before ingestion runtime code exists.

### `audit_log`

Audits user-visible forecasts, explanations, and human review actions. Flexible
`details_json` storage allows the application to capture trace context while the
MVP shape is still settling, without adding operational control data.

## How The Schema Supports The MVP

The schema supports ingestion by preserving source names, optional source record
identifiers, ingestion timestamps, and ingestion run status. This makes source
coverage, duplicate handling, and data-quality review possible.

The Energi Data Service dry-run ingestion module is a controlled validation
helper only. It returns normalized records and summary counts in memory and does
not write to `spot_prices`, `power_balance`, `ingestion_runs`, or any other
schema table.

`backend/app/db/repositories/eds_records.py` provides pure repository-boundary
helpers for mapping normalized Energi Data Service records into insert payload
dictionaries for `spot_prices` and `power_balance`. These helpers validate
required normalized fields and supported dataset/table targets, but they do not
open database connections, execute SQL, schedule ingestion jobs, or modify
FastAPI startup.

`backend/app/db/write_plan.py` provides a pure dry-run write-plan builder for
normalized Energi Data Service records. It returns in-memory dictionaries with
`table`, `operation`, `conflict_key`, and `payload` fields only. The operation is
always `upsert_preview`. `DayAheadPrices` records target `spot_prices`, and
`ElectricityProdex5MinRealtime` records target `power_balance`. Conflict keys
preview the intended schema uniqueness: `source` plus `source_record_id` when a
source record ID is available, otherwise `price_area`, `timestamp_utc`, and
`source`. The write plan does not connect to PostgreSQL, execute SQL, perform
writes, add ingestion jobs, or modify application startup.

Manual read-only write-plan preview validation confirmed that `DayAheadPrices`
maps to `spot_prices` and `ElectricityProdex5MinRealtime` maps to
`power_balance` for both DK1 and DK2 sample records. The
`ElectricityProdex5MinRealtime` preview payloads currently leave
`consumption_mw` null because that realtime production dataset does not provide
a clear consumption field. Consumption must be sourced from a separate validated
dataset before surplus-risk scoring depends on consumption values.

`backend/app/db/sql_builder.py` provides a pure parameterized PostgreSQL SQL
builder for individual Energi Data Service write-plan preview entries. It
supports `upsert_preview` SQL generation for `spot_prices` and `power_balance`
only, returning SQL text, a params mapping, table name, and operation. When
`source_record_id` is present, generated upserts use the `(source,
source_record_id)` conflict target. When it is absent, generated upserts use the
write-plan fallback conflict target `(price_area, timestamp_utc, source)`. The
builder validates required payload fields and rejects unsupported tables or
operations, but it does not connect to PostgreSQL, execute SQL, perform writes,
require `DATABASE_URL`, schedule ingestion jobs, or modify application startup.

`backend/app/db/executor.py` provides a narrow manual execution boundary for
supported Energi Data Service write-plan entries. It accepts a caller-provided
DB-API-style cursor, validates and builds the full batch of parameterized SQL
statements before submitting the first statement, then calls `cursor.execute`
for each statement. It does not create database connections, read
`DATABASE_URL`, commit transactions, run migrations, schedule ingestion jobs,
or modify FastAPI startup. Connection management and transaction handling remain
the responsibility of explicit manual tooling or future reviewed application
code.

`backend/app/db/transaction.py` provides a small mocked transaction boundary for
already generated SQL command dictionaries. It accepts only an injected
connection object, validates every command before opening a cursor, calls
`cursor.execute(sql, params)` for each command, commits only after the full batch
succeeds, and rolls back when command execution fails. It returns command and
table counts for tests and dry-run plumbing only. It does not create database
connections, read `DATABASE_URL`, import database drivers, require PostgreSQL,
schedule ingestion jobs, execute HTTP requests, add API endpoints, or modify
FastAPI startup.

`backend/app/ingestion/eds_persistence_dry_run.py` provides a pure orchestration
helper that chains normalized Energi Data Service records through the write-plan
builder and parameterized SQL builder. With no executor, it returns preview
counts, target tables, write-plan entries, and SQL command dictionaries only.
With an injected fake executor, it passes those generated SQL command
dictionaries to the caller boundary and reports the submitted count. It supports
only `DayAheadPrices` to `spot_prices` and
`ElectricityProdex5MinRealtime` to `power_balance`, rejects malformed records
with `ValueError`, and does not create connections, read `DATABASE_URL`, perform
HTTP requests, require PostgreSQL, schedule ingestion jobs, or modify FastAPI
startup.

It supports forecasting by separating raw market, system-balance, and weather
inputs from forecast output rows. Forecast rows include model name, model version,
confidence, forecast windows, and input data windows so outputs can be compared
across model versions.

It supports backtesting by indexing timestamped observations and forecast windows.
Historical forecasts can be joined with observed prices, power balance, and
weather records for later evaluation once backtesting workflows are implemented.

It supports auditability by keeping model outputs, explanation text, ingestion
runs, and human review events traceable. The `audit_log` table is intentionally
generic for the MVP, while the schema comments and documentation preserve the
read-only decision-support boundary.

## Constraints And Indexes

The baseline SQL includes `DK1`/`DK2` checks where `price_area` is present,
`low`/`medium`/`high` checks for forecast risk level, confidence bounds, basic
weather bounds, timestamp-window checks, source uniqueness constraints, and
indexes on timestamps, price area, source, and forecast windows.

TimescaleDB hypertables are intentionally left as TODO comments in `schema.sql`.
No extension commands, hypertable commands, triggers, or stored procedures are
included yet.

## Manual Local Validation

Manual local PostgreSQL validation is documented in
`docs/LOCAL_DATABASE_RUNBOOK.md`. The current status is:

- Schema baseline exists.
- Alembic baseline exists.
- SQL builder exists.
- Mocked executor and transaction boundaries exist.
- `scripts/local_db_smoke_test.py` exists as an explicit manual local-only smoke
  test for hardcoded DK1 sample records.
- No application runtime database connection is implemented.
- Manual local PostgreSQL migration and smoke-test validation has been completed
  against a developer-created local PostgreSQL 16.14 database only.

Alembic commands should be run from the `backend/` directory only by a developer
using a manually configured local PostgreSQL database. The migration environment
reads `DATABASE_URL` for manual usage and does not require that environment
variable during normal backend tests.

```bash
cd backend
DATABASE_URL='<local-postgresql-url>' alembic upgrade head
```

To review generated SQL without connecting to a database:

```bash
cd backend
DATABASE_URL='<local-postgresql-url>' alembic upgrade head --sql
```

Migrations and database writes must never run automatically during FastAPI
startup, tests, import time, or API request handling. The manual persistence
smoke test is an explicit local command, requires `DATABASE_URL`, refuses
non-local hosts, defaults to dry-run, requires `--confirm-local-db-write` for
writes, uses hardcoded DK1 sample records only, prints audit-style summary
output, and remains separate from FastAPI startup.

### Recorded Local Validation Results

Local PostgreSQL readiness was verified with PostgreSQL 16.14 installed via
Homebrew, `psql` and `createdb` available, and a manually created
`flexsignal_ai` local database.

The manual Alembic command succeeded:

```bash
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" python -m alembic -c alembic.ini upgrade head
```

Alembic upgraded to `0001_initial_schema`, and `alembic_version` contained
`0001_initial_schema`. The verified tables were `alembic_version`, `audit_log`,
`ingestion_runs`, `power_balance`, `spot_prices`, `surplus_risk_forecasts`, and
`weather_observations`.

The manual local smoke-test dry-run command was recorded as:

```bash
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" python ../scripts/local_db_smoke_test.py
```

It remained dry-run only, produced `2` commands for `power_balance` and
`spot_prices`, and reported `committed: false` and `rolled_back: false`.

The explicit manual local smoke-test write command was recorded as:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python ../scripts/local_db_smoke_test.py --confirm-local-db-write
```

It reported `committed: true` and `rolled_back: false`. `spot_prices` increased
from `0` to `1`, and `power_balance` increased from `0` to `1`.

Running the same smoke-test write a second time validated idempotency and upsert
behavior: `spot_prices` total remained `1`, `spot_prices` distinct
`source_record_id` remained `1`, `power_balance` total remained `1`, and
`power_balance` distinct `source_record_id` remained `1`.

Alembic uses SQLAlchemy URL format:
`postgresql+psycopg://localhost/flexsignal_ai`. The manual smoke-test script
uses DB-API URL format for the write path:
`postgresql://localhost/flexsignal_ai`.

There is no Azure database, production database, automatic ingestion job,
committed secret, repository-stored `DATABASE_URL`, control workflow, dispatch
workflow, activation workflow, or operational database functionality in `v0.1`.

## Open Questions And TODOs

- Confirm final source datasets and source-specific field mappings.
- Decide the canonical sign convention for `exchange_net_mw`.
- Decide whether weather locations should map to stations, grid cells, price
  areas, or a separate location dimension table.
- Define ingestion status values once ingestion jobs are designed.
- Decide whether forecast `recommended_action` needs a stricter controlled
  vocabulary while remaining human-review text only.
- Define local PostgreSQL/TimescaleDB setup, retention, and backup assumptions.
