# Database Schema Baseline

`schema.sql` is the initial PostgreSQL-compatible schema baseline for FlexSignal AI `v0.1`.
It is intended for review and planning only and is not wired into the FastAPI application.

The current backend remains read-only decision support. No runtime database connection,
ingestion job, migration runner, control workflow, dispatch workflow, or asset activation
logic is implemented here.

## Files

- `schema.sql`: baseline table definitions, constraints, indexes, comments, and TimescaleDB TODOs.
- `__init__.py`: package marker for future database-related modules.

## TODO

- Add Alembic once runtime database ownership and migration workflow are defined.
- Add local PostgreSQL/TimescaleDB setup instructions.
- Confirm final dataset field mappings and units before applying the schema.
- Decide TimescaleDB hypertable usage, chunk intervals, and retention policies.
- Add migration and rollback testing before any environment uses the schema.
