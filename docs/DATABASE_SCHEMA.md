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

## Manual Migrations

Alembic commands should be run from the `backend/` directory. The migration
environment reads `DATABASE_URL` for manual usage and does not require that
environment variable during normal backend tests.

```bash
cd backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/flexsignal_ai alembic upgrade head
```

To review generated SQL without connecting to a database:

```bash
cd backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/flexsignal_ai alembic upgrade head --sql
```

## Open Questions And TODOs

- Confirm final source datasets and source-specific field mappings.
- Decide the canonical sign convention for `exchange_net_mw`.
- Decide whether weather locations should map to stations, grid cells, price
  areas, or a separate location dimension table.
- Define ingestion status values once ingestion jobs are designed.
- Decide whether forecast `recommended_action` needs a stricter controlled
  vocabulary while remaining human-review text only.
- Define local PostgreSQL/TimescaleDB setup, retention, and backup assumptions.
