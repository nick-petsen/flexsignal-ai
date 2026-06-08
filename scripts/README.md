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
