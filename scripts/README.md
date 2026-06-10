# Data Source Validation Scripts

`validate_data_sources.py` is for manual validation of candidate public data source APIs before ingestion code is implemented.

The script performs one read-only HTTP `GET` request per run. It does not store data, write to the database, create ingestion jobs, or modify application behavior.

Verified datasets and endpoints must be documented before ingestion is implemented. Any future polling frequency must respect the source update frequency and avoid unnecessary requests.

## Examples

```bash
python scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --limit 5
python scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --limit 5
python scripts/validate_data_sources.py --source elprisenligenu --date 2026-06-07 --price-area DK1
```

Energi Data Service datasets can also be manually validated with a `PriceArea`
filter:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --price-area DK1 --limit 5
python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --price-area DK2 --limit 5
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 5
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --price-area DK2 --limit 5
```

## DMI Validation

DMI Open Data validation is manual and read-only. The validator only performs a
single HTTP `GET` request against a pasted DMI Open Data URL and prints a compact
response summary. It does not store data, create ingestion jobs, or change
application behavior.

Paste a candidate DMI Open Data URL from the DMI documentation:

```bash
python scripts/validate_data_sources.py --source dmi-url --url "https://opendataapi.dmi.dk/..."
```

DMI endpoints must be documented before any ingestion implementation is added.

## Energi Data Service Normalized Preview

`preview_eds_normalized_records.py` is a manual read-only preview tool for
checking how supported Energi Data Service records normalize through the backend
normalizer functions.

This is manual read-only preview only. It performs one HTTP `GET` when a human
runs it, prints normalized JSON lines, and does not persist data. It is not an
ingestion job, does not expose an API, and must not be used for control,
dispatch, or activation.

```bash
python3 scripts/preview_eds_normalized_records.py --dataset DayAheadPrices --price-area DK1 --limit 3
python3 scripts/preview_eds_normalized_records.py --dataset DayAheadPrices --price-area DK2 --limit 3
python3 scripts/preview_eds_normalized_records.py --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 3
python3 scripts/preview_eds_normalized_records.py --dataset ElectricityProdex5MinRealtime --price-area DK2 --limit 3
```

## Energi Data Service Write-Plan Preview

`preview_eds_write_plan.py` is a manual read-only preview tool for checking how
supported Energi Data Service records would map into database write-plan
entries. It performs one HTTP `GET` when a human runs it, prints the final
request URL, HTTP status, record counts, write-plan entry count, and compact
write-plan JSON lines.

This is preview-only. It does not connect to a database, execute SQL, write
records, create ingestion jobs, expose an API, forecast, dispatch, activate, or
control energy assets.

```bash
python3 scripts/preview_eds_write_plan.py --dataset DayAheadPrices --price-area DK1 --limit 5
python3 scripts/preview_eds_write_plan.py --dataset DayAheadPrices --price-area DK2 --limit 5
python3 scripts/preview_eds_write_plan.py --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 5
python3 scripts/preview_eds_write_plan.py --dataset ElectricityProdex5MinRealtime --price-area DK2 --limit 5
```

## Local PostgreSQL Smoke Test

`local_db_smoke_test.py` is an explicit manual local-only smoke test for the
existing EDS database write path. It uses two hardcoded DK1 normalized sample
records only, builds them through the write-plan and SQL builder helpers, and
defaults to dry-run output.

The script requires `DATABASE_URL` and refuses to run unless the parsed host is
`localhost` or `127.0.0.1`. It does not read secrets from files, make HTTP
requests, use live Energi Data Service data, create ingestion jobs, import
FastAPI, expose endpoints, forecast, dispatch, activate, or control assets.

Dry-run:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/local_db_smoke_test.py
```

Real local write, only after manually running migrations against a local
database:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/local_db_smoke_test.py --confirm-local-db-write
```

The write path requires an already available PostgreSQL DB-API driver such as
`psycopg` or `psycopg2`. No backend dependency is added for this manual script.

## Manual Local PostgreSQL Read Preview

`manual_local_db_read_preview.py` is an explicit manual local-only read preview
for existing PostgreSQL tables. It uses the existing backend read-only query
builders and executes only a generated `SELECT` against a local database.

The script requires `DATABASE_URL`, refuses to run unless the parsed host is
`localhost` or `127.0.0.1`, and accepts only DB-API URL format such as
`postgresql://localhost/flexsignal_ai`. It supports only `spot_prices` and
`power_balance`, only `DK1` and `DK2`, defaults to limit `10`, and rejects
limits above `100`.

It prints the target host, table, price area, row count, and compact JSON lines
for returned rows. It does not write to the database, fetch live Energi Data
Service data, create ingestion jobs, import FastAPI, expose endpoints, forecast,
dispatch, activate, or control energy assets.

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/manual_local_db_read_preview.py --table spot_prices --price-area DK1
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/manual_local_db_read_preview.py --table power_balance --price-area DK2 --limit 25
```

## Manual EDS Local DB Ingest

`manual_eds_local_db_ingest.py` is an explicit manual local-only validation
script for fetching a tiny live Energi Data Service sample and passing it
through the existing normalization, write-plan, SQL builder, and transaction
helpers.

The script is dry-run by default. It requires `DATABASE_URL`, refuses to run
unless the parsed host is `localhost` or `127.0.0.1`, accepts only DB-API URL
format such as `postgresql://localhost/flexsignal_ai`, and writes only when
`--confirm-local-db-write` is passed. The default limit is `2` and the hard
maximum is `10`.

It supports only `DayAheadPrices` and `ElectricityProdex5MinRealtime`, filtered
to `DK1` or `DK2`. It does not run automatically, read secrets from files,
import FastAPI, create jobs, expose endpoints, forecast, dispatch, activate, or
control energy assets.

Dry-run:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/manual_eds_local_db_ingest.py --dataset DayAheadPrices --price-area DK1
```

Real local write, only after manually running migrations against the same local
database:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/manual_eds_local_db_ingest.py --dataset DayAheadPrices --price-area DK1 --confirm-local-db-write
```

The script prints a warning, final request URL, HTTP status, raw count,
normalized count, SQL command count, target tables, and committed/rolled-back
status for each run.

## Risk Backtest Synthetic Preview

`risk_backtest_preview.py` is a manual synthetic local preview for the existing
`rule-engine-v0` backtest evaluator. It uses only hardcoded sample row
dictionaries in the script, including low-, medium-, and high-like examples plus
an invalid row to demonstrate `failed_rows`.

```bash
python3 scripts/risk_backtest_preview.py
python3 scripts/risk_backtest_preview.py --pretty
```

The script prints a scope warning and a JSON summary with row counts, risk-level
counts, average scores, reason-code counts, missing data counts, model version,
and `decision_support_only`.

This is synthetic preview-only. It does not require `DATABASE_URL`, connect to a
database, execute SQL, fetch live Energi Data Service data, call HTTP APIs, add
or use FastAPI endpoints, run frontend code, create ingestion jobs, use Azure,
train ML models, use LLMs, control assets, dispatch, activate, or perform
operational functionality.

## Risk Backtest Local DB Preview

`risk_backtest_local_db.py` is a manual local-only read-only PostgreSQL
backtest preview for `rule-engine-v0`. It uses the existing backend SELECT query
builders to read recent `spot_prices` and `power_balance` rows for `DK1` or
`DK2`, composes those rows through `compose_surplus_risk_input(...)`, and prints
a JSON summary from `evaluate_risk_backtest(rows)`.

The script requires `DATABASE_URL`, refuses to run unless the parsed host is
`localhost` or `127.0.0.1`, and accepts only DB-API URL format such as
`postgresql://localhost/flexsignal_ai`. It validates that generated SQL is
`SELECT` only and refuses forbidden operations including `INSERT`, `UPDATE`,
`DELETE`, `ALTER`, `DROP`, `CREATE`, and `TRUNCATE`.

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/risk_backtest_local_db.py --price-area DK1
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/risk_backtest_local_db.py --price-area DK2 --limit 100 --pretty
```

Rows are paired deterministically by list order after each table is read by
latest `timestamp_utc` descending. If one table returns more rows than the other,
remaining rows are still composed with the missing side omitted. This is a
technical local validation helper, not full historical model validation.

The script prints a manual-use warning and writes only JSON summary output to
stdout. It does not write to the database, fetch live Energi Data Service data,
call HTTP APIs, create ingestion jobs, import or modify FastAPI startup, add
frontend code, use Azure, add secrets, add auth, train ML models, use LLMs,
control assets, dispatch, activate, or perform operational functionality.
