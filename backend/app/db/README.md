# Database Schema Baseline

`schema.sql` is the initial PostgreSQL-compatible schema baseline for FlexSignal AI `v0.1`.
It is the human-readable reference for the current database shape.

The current backend remains read-only decision support. No runtime database connection,
ingestion job, automatic migration runner, control workflow, dispatch workflow, or asset activation
logic is implemented here.

## Files

- `schema.sql`: baseline table definitions, constraints, indexes, comments, and TimescaleDB TODOs.
- `../../alembic.ini`: local Alembic configuration for manual migration commands.
- `../../alembic/`: reproducible migration path for the baseline schema.
- `__init__.py`: package marker for future database-related modules.
- `write_plan.py`: pure dry-run Energi Data Service write-plan builder.
- `sql_builder.py`: pure parameterized SQL builder for supported write-plan entries.
- `executor.py`: manual execution boundary that submits supported write-plan SQL through
  a caller-provided cursor only.

`executor.py` intentionally does not create database connections, read `DATABASE_URL`,
commit transactions, run migrations, schedule ingestion, or attach to FastAPI startup.
It is a narrow adapter for tests and future manual tooling where the caller owns the
database connection and transaction scope.

## Alembic Migrations

Alembic is used to keep a reproducible migration history for the PostgreSQL schema.
The initial migration mirrors `schema.sql` and creates the `v0.1` baseline tables.

Migrations are not run automatically by the FastAPI API, tests, or application startup.
To run them manually against a local database, install the backend and run Alembic from
the `backend/` directory with a SQLAlchemy-compatible PostgreSQL URL:

```bash
cd backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/flexsignal_ai alembic upgrade head
```

To generate SQL without connecting to a database:

```bash
cd backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/flexsignal_ai alembic upgrade head --sql
```

## TODO

- Add local PostgreSQL/TimescaleDB setup instructions.
- Confirm final dataset field mappings and units before applying the schema.
- Decide TimescaleDB hypertable usage, chunk intervals, and retention policies.
- Add migration and rollback testing before any environment uses the schema.
