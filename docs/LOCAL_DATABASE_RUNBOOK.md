# Local Database Runbook

This runbook documents the manual local PostgreSQL validation flow for
FlexSignal AI `v0.1`. The application does not open a real database connection,
run migrations automatically, or write data to PostgreSQL.

`v0.1` remains read-only decision support. Local database validation must not add
control signals, dispatch instructions, activation workflows, closed-loop
control, or operational asset connectivity.

## Current Status

- A PostgreSQL schema baseline exists in `backend/app/db/schema.sql`.
- An Alembic baseline migration exists under `backend/alembic/`.
- A pure SQL builder exists in `backend/app/db/sql_builder.py`.
- Mocked executor and transaction boundaries exist for generated SQL command
  dictionaries, using caller-provided fake cursors or connections.
- An explicit manual local smoke-test script exists at
  `scripts/local_db_smoke_test.py`.
- Explicit manual local EDS ingest validation scripts exist at
  `scripts/manual_eds_local_db_ingest.py` and
  `scripts/manual_eds_historical_batch_import.py`.
- An explicit manual local read-preview script exists at
  `scripts/manual_local_db_read_preview.py`.
- The backend dev dependency set includes `psycopg[binary]` for local/manual
  PostgreSQL validation only.
- No application runtime database connection is implemented.
- No FastAPI startup migration, startup write, ingestion job, or API endpoint
  writes to PostgreSQL.
- Manual local PostgreSQL migration and smoke-test validation has been completed
  against a developer-created local database only, with results documented below.

## Manual Local Validation Results

These results document manual local validation runs. No Azure database,
production database, FastAPI startup integration, automatic ingestion job,
control workflow, dispatch workflow, activation workflow, or operational
functionality was used or added.

### Local PostgreSQL Readiness

- PostgreSQL 16.14 was installed locally via Homebrew.
- `psql` and `createdb` were available.
- The local database `flexsignal_ai` was created manually.

### Alembic Migration

Command:

```bash
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" python -m alembic -c alembic.ini upgrade head
```

Result:

- Migration succeeded.
- Alembic ran upgrade to `0001_initial_schema`.
- `alembic_version` contained `0001_initial_schema`.

Tables verified:

- `alembic_version`
- `audit_log`
- `ingestion_runs`
- `power_balance`
- `spot_prices`
- `surplus_risk_forecasts`
- `weather_observations`

### Manual Local DB Smoke-Test Dry-Run

Command:

```bash
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" python ../scripts/local_db_smoke_test.py
```

Result:

- Dry-run only.
- Command count: `2`.
- Tables: `power_balance`, `spot_prices`.
- `committed`: `false`.
- `rolled_back`: `false`.

### Manual Local DB Smoke-Test Write

Command:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python ../scripts/local_db_smoke_test.py --confirm-local-db-write
```

Result:

- `committed`: `true`.
- `rolled_back`: `false`.
- `spot_prices` count increased from `0` to `1`.
- `power_balance` count increased from `0` to `1`.

### Idempotency And Upsert Validation

Running the same smoke-test write a second time did not create duplicates:

- `spot_prices` total remained `1`.
- `spot_prices` distinct `source_record_id` remained `1`.
- `power_balance` total remained `1`.
- `power_balance` distinct `source_record_id` remained `1`.

### Manual Live EDS Local DB Write Validation

The following confirmed writes were run manually against local PostgreSQL only.
No Azure database or production database was used. No FastAPI startup
integration, scheduled ingestion job, automatic write path, control workflow,
dispatch workflow, activation workflow, or operational functionality was added.
Both commands used `--limit 2`, `DK1`, and the explicit
`--confirm-local-db-write` confirmation flag.

Command:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_local_db_ingest.py --dataset DayAheadPrices --price-area DK1 --limit 2 --confirm-local-db-write
```

Result:

- HTTP status: `200`.
- Raw record count: `2`.
- Normalized record count: `2`.
- SQL command count: `2`.
- Table: `spot_prices`.
- `committed`: `true`.
- `rolled_back`: `false`.
- `spot_prices` count increased from `1` to `3`.

Observed rows included:

- `DayAheadPrices:DK1:2026-06-09T21:45:00`.
- `DayAheadPrices:DK1:2026-06-09T21:30:00`.

Command:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_local_db_ingest.py --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 2 --confirm-local-db-write
```

Result:

- HTTP status: `200`.
- Raw record count: `2`.
- Normalized record count: `2`.
- SQL command count: `2`.
- Table: `power_balance`.
- `committed`: `true`.
- `rolled_back`: `false`.
- `power_balance` count increased from `1` to `3`.

Observed rows included:

- `ElectricityProdex5MinRealtime:DK1:2026-06-08T23:25:00`.
- `ElectricityProdex5MinRealtime:DK1:2026-06-08T23:20:00`.

### Manual Local Read-Only API Smoke Test

The local FastAPI server was started manually against local PostgreSQL only:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

Health check:

```text
GET /health
```

Result:

```json
{"status":"ok","service":"flexsignal-ai-api","version":"0.1.0"}
```

Read-only spot prices endpoint:

```text
GET /api/energy/spot-prices?price_area=DK1&limit=5
```

Result:

- Table: `spot_prices`.
- Price area: `DK1`.
- Row count: `3`.

Read-only power balance endpoint:

```text
GET /api/energy/power-balance?price_area=DK1&limit=5
```

Result:

- Table: `power_balance`.
- Price area: `DK1`.
- Row count: `3`.

This was read-only API validation only. No database writes were performed, no
live Energi Data Service polling was performed, no startup migrations were run,
no ingestion jobs were added, no Azure resources were used, no production
database was used, and no control, dispatch, activation, or operational
functionality was added.

### URL Format Notes

- Alembic uses the SQLAlchemy URL format:
  `postgresql+psycopg://localhost/flexsignal_ai`.
- The manual smoke-test script uses the DB-API URL format:
  `postgresql://localhost/flexsignal_ai`.

## Manual Local Validation Flow

This flow is for explicit local smoke tests only. It should be run by a
developer from a shell, against a manually created local PostgreSQL database.

1. Create a local PostgreSQL database manually.

   Example database name:

   ```text
   flexsignal_ai
   ```

   The repository must not create databases automatically, provision Azure
   databases, or assume a production database exists.

2. Set `DATABASE_URL` manually in the shell for the current command or terminal
   session only.

   Use a local PostgreSQL URL controlled by the developer. For Alembic with
   psycopg v3, use the explicit SQLAlchemy driver name:

   ```bash
   export DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai"
   ```

   Do not commit the value, add it to tracked config, add it to examples
   containing real credentials, or store it in the repository.

3. Run the Alembic migration manually from the `backend/` directory.

   ```bash
   cd backend
   DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head
   ```

   Migrations must never run automatically during FastAPI startup, tests, import
   time, or API request handling.

4. Run the explicit manual persistence smoke test.

   The smoke test uses two hardcoded DK1 normalized sample records only:
   one `DayAheadPrices`-like record for `spot_prices` and one
   `ElectricityProdex5MinRealtime`-like record for `power_balance`. It does not
   use live Energi Data Service data or make HTTP requests.

   Dry-run is the default. The smoke-test script uses DB-API URL format:

   ```bash
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/local_db_smoke_test.py
   ```

   Do not use `--confirm-local-db-write` until the manual Alembic migration has
   succeeded against the same local database.

   To execute writes after a successful manual migration, pass the explicit
   confirmation flag:

   ```bash
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/local_db_smoke_test.py --confirm-local-db-write
   ```

   The script refuses to run unless `DATABASE_URL` is set and its parsed host is
   `localhost` or `127.0.0.1`. The write path requires an already available
   PostgreSQL DB-API driver; the backend dev dependency set provides psycopg v3
   for this local/manual validation path.

5. Optionally run the explicit manual EDS local DB ingest validation script.

   This script fetches a tiny live Energi Data Service sample for one supported
   dataset and one DK1/DK2 price area, normalizes records, builds write-plan
   entries, builds SQL commands, and defaults to dry-run. It supports only
   `DayAheadPrices` and `ElectricityProdex5MinRealtime`, and only `DK1` and
   `DK2`. The default limit is `2`; the hard maximum is `10`.

   Dry-run is the default and still requires a local `DATABASE_URL` safety gate:

   ```bash
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/manual_eds_local_db_ingest.py --dataset DayAheadPrices --price-area DK1
   ```

   Do not use `--confirm-local-db-write` until the manual Alembic migration has
   succeeded against the same local database.

   To execute writes after a successful manual migration, pass the explicit
   confirmation flag:

   ```bash
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/manual_eds_local_db_ingest.py --dataset DayAheadPrices --price-area DK1 --confirm-local-db-write
   ```

   The manual EDS ingest script uses DB-API URL format only:
   `postgresql://localhost/flexsignal_ai`. Do not use the Alembic SQLAlchemy
   URL format `postgresql+psycopg://...` with this script. The script refuses
   non-local database hosts, does not read secrets from files, and does not run
   automatically.

6. Run the staged manual historical local EDS batch wrapper.

   `scripts/manual_eds_historical_batch_import.py` is a manual local-only batch
   wrapper around `scripts/manual_eds_local_db_ingest.py`. It prints the exact
   child command plan, invokes the child script with the current Python
   executable, and does not bypass the child script's safety gates.

   Goal:

   - Expand local EDS-derived samples for `DK1` and `DK2`.
   - Improve local read-only backtest coverage.
   - Keep the flow as manual local technical validation only.

   Scope:

   - Datasets: `DayAheadPrices` and `ElectricityProdex5MinRealtime`.
   - Price areas: `DK1` and `DK2`.
   - Local targets: `spot_prices` and `power_balance`.

   Current wrapper batch size:

   - Use `limit 10` or lower. The wrapper default is `10` and the wrapper hard
     maximum is `10` to match the current child script safety gate.

   Future larger batch progression:

   - Start with `limit 50` per dataset and price area.
   - Increase to `limit 100` only after validation passes.
   - Increase to a maximum of `limit 500` only after row counts, idempotency,
     and backtest outputs remain explainable at smaller batch sizes.
   - These larger `50`/`100`/`500` imports require a future explicit
     `scripts/manual_eds_local_db_ingest.py` child-script enhancement. The
     wrapper must not bypass the child script safety gate.

   Required safety gates:

   - `DATABASE_URL` must use DB-API format:
     `postgresql://localhost/flexsignal_ai`.
   - The parsed host must be `localhost` or `127.0.0.1`.
   - Dry-run must be run before every confirmed write batch.
   - Confirmed writes must require explicit `--confirm-local-db-write`.
   - No production database, Azure database, scheduled job, backend startup
     ingestion, frontend-triggered ingestion, or automatic polling loop.

   Dry-run first:

   ```bash
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/manual_eds_historical_batch_import.py --limit 10
   ```

   Confirmed local write only after the dry-run plan and child outputs are
   reviewed:

   ```bash
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/manual_eds_historical_batch_import.py --limit 10 --confirm-local-db-write
   ```

   Required validation after each batch:

   - Check row counts by `price_area`.
   - Check distinct `source_record_id` counts.
   - Repeat the same import to confirm idempotency.
   - Confirm counts do not duplicate unexpectedly.
   - Run the local DB read-only backtest for `DK1` and `DK2`.
   - Document `risk_level_counts` and `average_risk_score`.

   Example row-count checks:

   ```sql
   SELECT price_area, COUNT(*) FROM spot_prices GROUP BY price_area ORDER BY price_area;
   SELECT price_area, COUNT(*) FROM power_balance GROUP BY price_area ORDER BY price_area;
   SELECT price_area, COUNT(DISTINCT source_record_id) FROM spot_prices GROUP BY price_area ORDER BY price_area;
   SELECT price_area, COUNT(DISTINCT source_record_id) FROM power_balance GROUP BY price_area ORDER BY price_area;
   ```

   Idempotency check:

   - Re-run the same wrapper command with the same dataset, price area, limit,
     and confirmation mode.
   - Re-run the row-count and distinct `source_record_id` checks.
   - Confirm totals do not duplicate unexpectedly.

   DK1/DK2 local DB backtest reruns:

   ```bash
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/risk_backtest_local_db.py --price-area DK1 --limit 100 --pretty
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/risk_backtest_local_db.py --price-area DK2 --limit 100 --pretty
   ```

   Stop immediately if any duplicate explosion, non-local database URL, write
   without explicit confirmation, failed normalization, unexpected source field
   mapping, control behavior, dispatch behavior, activation behavior, or
   operational workflow appears.

7. Optionally run the explicit manual local DB read-preview script.

   This script reads recent rows from an existing local PostgreSQL table using
   the backend read-only query builders. It supports only `spot_prices` and
   `power_balance`, only `DK1` and `DK2`, defaults to limit `10`, and rejects
   limits above `100`.

   The read-preview script uses DB-API URL format only:
   `postgresql://localhost/flexsignal_ai`. Do not use the Alembic SQLAlchemy
   URL format `postgresql+psycopg://...` with this script.

   ```bash
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/manual_local_db_read_preview.py --table spot_prices --price-area DK1
   DATABASE_URL="postgresql://localhost/flexsignal_ai" python3 ../scripts/manual_local_db_read_preview.py --table power_balance --price-area DK2 --limit 25
   ```

   It prints the target host, table, price area, row count, and compact JSON
   lines for returned rows. It does not write to the database, fetch live Energi
   Data Service data, create ingestion jobs, import FastAPI, expose endpoints,
   forecast, dispatch, activate, or control energy assets.

8. Review and document the result.

   Record the command used, local-only target, row counts or preview counts,
   rollback/error behavior observed, and confirmation that no startup integration
   or automatic ingestion was added.

## Safety Boundaries

- No Azure database exists for this validation flow.
- No production database should be used.
- No automatic ingestion jobs should be added.
- No secrets should be committed.
- No `DATABASE_URL` value should be stored in the repository.
- No migrations or writes should run automatically during FastAPI startup.
- FastAPI must not run migrations or perform database writes at startup.
- No API endpoint should trigger local validation writes.
- `scripts/local_db_smoke_test.py` must not be run automatically by tests,
  startup hooks, schedulers, or ingestion workflows.
- `scripts/manual_eds_local_db_ingest.py` must not be run automatically by
  tests, startup hooks, schedulers, or ingestion workflows.
- `scripts/manual_eds_historical_batch_import.py` must not be run automatically
  by tests, startup hooks, schedulers, or ingestion workflows.
- `scripts/manual_local_db_read_preview.py` must not be run automatically by
  tests, startup hooks, schedulers, or ingestion workflows.
- No control, dispatch, activation, closed-loop, or operational functionality
  should be added.

## Acceptance Checklist For Manual DB Write Code

For `scripts/local_db_smoke_test.py`, all of the following must remain true:

- Local DB only.
- Manual command only.
- Explicit `DATABASE_URL` required.
- Host restricted to `localhost` or `127.0.0.1`.
- Explicit `--confirm-local-db-write` flag required for writes.
- Hardcoded sample records only.
- Audit/log result documented.
- No FastAPI startup integration.
- Do not use `--confirm-local-db-write` until Alembic migration succeeds.

For `scripts/manual_eds_local_db_ingest.py`, these additional checks apply:

- Dry-run is the default.
- `--confirm-local-db-write` is required for writes.
- `DATABASE_URL` is required for dry-run and write mode.
- `DATABASE_URL` must use DB-API format:
  `postgresql://localhost/flexsignal_ai`.
- `DATABASE_URL` host must be `localhost` or `127.0.0.1`.
- Supported datasets are limited to `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`.
- Supported price areas are limited to `DK1` and `DK2`.
- Limit defaults to `2` and must not exceed `10`.
- The script must print the final request URL, HTTP status, raw count,
  normalized count, SQL command count, target tables, committed status, and
  rolled-back status.
- No confirmed writes should be performed by automated tests.

For `scripts/manual_eds_historical_batch_import.py`, these additional checks
apply:

- Documentation must preserve the manual local technical validation boundary.
- Dry-run is the default.
- `DATABASE_URL` is required in dry-run and write mode.
- `DATABASE_URL` must use DB-API format:
  `postgresql://localhost/flexsignal_ai`.
- `DATABASE_URL` host must be `localhost` or `127.0.0.1`.
- Supported datasets are limited to `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`, or `all`.
- Supported price areas are limited to `DK1`, `DK2`, or `all`.
- Limit defaults to `10` and the wrapper must reject values above `10`.
- Larger staged imports of `limit 50` per dataset and price area, then `100`,
  then maximum `500`, require a future explicit child-script enhancement before
  the wrapper can support them.
- Dry-run must be run before confirmed write mode for each batch.
- Confirmed writes must require explicit `--confirm-local-db-write`.
- The wrapper must pass `--confirm-local-db-write` to child commands only when
  the wrapper receives that flag.
- The wrapper must stop on the first child failure unless
  `--continue-on-error` is passed.
- The wrapper must print the child command plan and final compact JSON summary.
- Row counts by `price_area` and distinct `source_record_id` counts must be
  documented after each batch.
- Repeating the same batch must not create unexpected duplicate rows.
- Local DB read-only backtests for `DK1` and `DK2` must be rerun after each
  batch and the `risk_level_counts` plus `average_risk_score` documented.
- The enhancement must not add scheduled jobs, backend startup ingestion,
  frontend-triggered ingestion, automatic polling, production database access,
  Azure database access, secrets, auth, ML training, LLM use, control,
  dispatch, activation, closed-loop behavior, or operational workflows.

For `scripts/manual_local_db_read_preview.py`, these additional checks apply:

- Read-only `SELECT` execution only.
- `DATABASE_URL` is required.
- `DATABASE_URL` must use DB-API format:
  `postgresql://localhost/flexsignal_ai`.
- `DATABASE_URL` host must be `localhost` or `127.0.0.1`.
- Supported tables are limited to `spot_prices` and `power_balance`.
- Supported price areas are limited to `DK1` and `DK2`.
- Limit defaults to `10` and must not exceed `100`.
- The script must print target host, table, price area, row count, and compact
  JSON lines for returned rows.
- It must not fetch live Energi Data Service data or execute database writes.
