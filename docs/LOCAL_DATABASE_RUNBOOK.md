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
- No application runtime database connection is implemented.
- No FastAPI startup migration, startup write, ingestion job, or API endpoint
  writes to PostgreSQL.

## Manual Local Validation Flow

This flow is for a future explicit local smoke test only. It should be run by a
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

   Use a local PostgreSQL URL controlled by the developer. Do not commit the
   value, add it to tracked config, add it to examples containing real
   credentials, or store it in the repository.

   ```bash
   export DATABASE_URL='<local-postgresql-url>'
   ```

3. Run the Alembic migration manually from the `backend/` directory.

   ```bash
   cd backend
   alembic upgrade head
   ```

   Migrations must never run automatically during FastAPI startup, tests, import
   time, or API request handling.

4. Run the explicit manual persistence smoke test.

   The smoke test uses two hardcoded DK1 normalized sample records only:
   one `DayAheadPrices`-like record for `spot_prices` and one
   `ElectricityProdex5MinRealtime`-like record for `power_balance`. It does not
   use live Energi Data Service data or make HTTP requests.

   Dry-run is the default:

   ```bash
   DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/local_db_smoke_test.py
   ```

   To execute writes, pass the explicit confirmation flag:

   ```bash
   DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/local_db_smoke_test.py --confirm-local-db-write
   ```

   The script refuses to run unless `DATABASE_URL` is set and its parsed host is
   `localhost` or `127.0.0.1`. The write path requires an already available
   PostgreSQL DB-API driver such as `psycopg` or `psycopg2`; no backend
   dependency is added for this manual script.

5. Review and document the result.

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
- No API endpoint should trigger local validation writes.
- `scripts/local_db_smoke_test.py` must not be run automatically by tests,
  startup hooks, schedulers, or ingestion workflows.
- No control, dispatch, activation, closed-loop, or operational functionality
  should be added.

## Acceptance Checklist For Manual DB Write Code

For manual local database write code, all of the following must remain true:

- Local DB only.
- Manual command only.
- Explicit `DATABASE_URL` required.
- Host restricted to `localhost` or `127.0.0.1`.
- Explicit `--confirm-local-db-write` flag required for writes.
- Hardcoded sample records only.
- Audit/log result documented.
- No FastAPI startup integration.
