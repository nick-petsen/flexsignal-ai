# Local Database Runbook

This runbook documents a future manual local PostgreSQL validation flow for
FlexSignal AI `v0.1`. It is documentation only. The application does not yet
open a real database connection, run migrations automatically, or write data to
PostgreSQL.

`v0.1` remains read-only decision support. Local database validation must not add
control signals, dispatch instructions, activation workflows, closed-loop
control, or operational asset connectivity.

## Current Status

- A PostgreSQL schema baseline exists in `backend/app/db/schema.sql`.
- An Alembic baseline migration exists under `backend/alembic/`.
- A pure SQL builder exists in `backend/app/db/sql_builder.py`.
- Mocked executor and transaction boundaries exist for generated SQL command
  dictionaries, using caller-provided fake cursors or connections.
- No real database connection is implemented yet.
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

4. Run a future explicit manual persistence smoke test.

   The smoke test does not exist yet. Before it is added, it must remain:

   - Local database only.
   - Manual command only.
   - Explicitly gated by `DATABASE_URL`.
   - Limited to small DK1/DK2 sample batches.
   - Auditable through documented output or logs.
   - Covered by rollback/error behavior tests.
   - Separate from FastAPI startup and API endpoints.

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
- No control, dispatch, activation, closed-loop, or operational functionality
  should be added.

## Acceptance Checklist Before Real DB Write Code

Before any real database write code is implemented, all of the following must be
true and documented in the implementing change:

- Local DB only.
- Manual command only.
- Explicit `DATABASE_URL` required.
- Small limit, DK1/DK2 only.
- Audit/log result documented.
- Rollback/error behavior tested.
- No FastAPI startup integration.

