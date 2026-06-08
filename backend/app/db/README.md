# Database Schema Baseline

`schema.sql` is the initial PostgreSQL-compatible schema baseline for FlexSignal AI `v0.1`.
It is the human-readable reference for the current database shape.

The current backend remains read-only decision support. No runtime database connection,
ingestion job, automatic migration runner, control workflow, dispatch workflow, or asset activation
logic is implemented here.

For the future manual local PostgreSQL validation flow, see
`../../../docs/LOCAL_DATABASE_RUNBOOK.md`.

## Files

- `schema.sql`: baseline table definitions, constraints, indexes, comments, and TimescaleDB TODOs.
- `../../alembic.ini`: local Alembic configuration for manual migration commands.
- `../../alembic/`: reproducible migration path for the baseline schema.
- `__init__.py`: package marker for future database-related modules.
- `write_plan.py`: pure dry-run Energi Data Service write-plan builder.
- `sql_builder.py`: pure parameterized SQL builder for supported write-plan entries.
- `executor.py`: manual execution boundary that submits supported write-plan SQL through
  a caller-provided cursor only.
- `transaction.py`: mocked transaction boundary for generated SQL command dictionaries
  using a caller-provided connection only.

`executor.py` intentionally does not create database connections, read `DATABASE_URL`,
commit transactions, run migrations, schedule ingestion, or attach to FastAPI startup.
It is a narrow adapter for tests and future manual tooling where the caller owns the
database connection and transaction scope.

`transaction.py` intentionally does not create database connections, read
`DATABASE_URL`, import database drivers, run migrations, schedule ingestion, or attach
to FastAPI startup. It validates a non-empty batch of generated SQL command
dictionaries before opening a cursor from the injected connection, executes each
command via `cursor.execute(sql, params)`, commits only after the full batch succeeds,
and rolls back if command execution fails.

## Alembic Migrations

Alembic is used to keep a reproducible migration history for the PostgreSQL schema.
The initial migration mirrors `schema.sql` and creates the `v0.1` baseline tables.

Migrations are not run automatically by the FastAPI API, tests, or application startup.
FastAPI must not run migrations or perform database writes at startup. No real
database connection is implemented for the application runtime. To run the
baseline manually for local validation, create a local PostgreSQL database
yourself, set `DATABASE_URL` in the shell only, install the backend with dev
dependencies, and run Alembic from the `backend/` directory with the explicit
psycopg v3 SQLAlchemy URL:

```bash
cd backend
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head
```

To generate SQL without connecting to a database:

```bash
cd backend
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head --sql
```

Future manual persistence smoke tests must be explicit local commands only. They
must require `DATABASE_URL`, use small DK1/DK2-only limits, document audit/log
results, test rollback/error behavior, and stay completely separate from FastAPI
startup and API endpoints. Do not use `--confirm-local-db-write` until the
manual Alembic migration succeeds against the same local database.

Safety boundaries:

- No Azure database.
- No production database.
- No automatic ingestion jobs.
- No committed secrets or repository-stored `DATABASE_URL`.
- No database migrations or writes during FastAPI startup.
- FastAPI startup must not run migrations or database writes.
- No control, dispatch, activation, closed-loop, or operational functionality.

## TODO

- Add the future explicit local persistence smoke test after its acceptance
  checklist is reviewed.
- Confirm final dataset field mappings and units before applying the schema.
- Decide TimescaleDB hypertable usage, chunk intervals, and retention policies.
- Add migration and rollback testing before any environment uses the schema.
