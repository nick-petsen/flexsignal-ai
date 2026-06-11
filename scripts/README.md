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
maximum is `50` for explicit manual local validation.

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

## Manual EDS Historical Batch Import

`manual_eds_historical_batch_import.py` is a manual local-only batch wrapper
around `manual_eds_local_db_ingest.py`. It builds explicit dataset and price
area command combinations, prints the exact child command plan, and invokes the
child script with the current Python executable.

The wrapper is dry-run by default. It requires `DATABASE_URL`, refuses to run
unless the parsed host is `localhost` or `127.0.0.1`, accepts only DB-API URL
format such as `postgresql://localhost/flexsignal_ai`, and passes
`--confirm-local-db-write` to child commands only when the wrapper receives that
same flag. It defaults to `--limit 10`, accepts explicit `--limit 50`, rejects
limits above `50`, and does not bypass the child ingest script safety gate.
Larger staged imports such as `100` or `500` records per dataset and price area
still require a future explicit enhancement before the wrapper can support
them.

It supports only `DayAheadPrices` and `ElectricityProdex5MinRealtime`, filtered
to `DK1`, `DK2`, or both. It does not schedule itself, run automatically, read
secrets from files, import FastAPI, create jobs, expose endpoints, forecast,
dispatch, activate, or control energy assets.

Dry-run all supported datasets and DK1/DK2 with limit 50:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/manual_eds_historical_batch_import.py --limit 50
```

Confirmed local write for all supported datasets and DK1/DK2 with limit 10,
only after dry-run and local migration validation:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/manual_eds_historical_batch_import.py --limit 10 --confirm-local-db-write
```

DK1 only:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/manual_eds_historical_batch_import.py --price-area DK1
```

One dataset only:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/manual_eds_historical_batch_import.py --dataset DayAheadPrices
```

Use `--continue-on-error` only when a failed child command should not stop
remaining planned manual validation commands. The wrapper prints a compact JSON
summary with planned, succeeded, and failed child command counts.

### Historical Batch Wrapper Dry-Run Result

The following wrapper dry-run validated command orchestration and normalization
path behavior for all supported DK1/DK2 dataset combinations only. It did not
write to the database.

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --continue-on-error
```

Wrapper result:

- `dry_run`: `true`
- `confirmed_local_write`: `false`
- `local_only`: `true`
- `decision_support_only`: `true`
- `limit`: `50`
- `price_areas`: `DK1`, `DK2`
- `datasets`: `DayAheadPrices`, `ElectricityProdex5MinRealtime`
- `commands_planned`: `4`
- `commands_succeeded`: `4`
- `commands_failed`: `0`
- `child_exit_codes`: `[0, 0, 0, 0]`

Child dry-run observations:

| Dataset | PriceArea | HTTP | Raw | Normalized | SQL commands | Table | Committed |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `DayAheadPrices` | `DK1` | 200 | 50 | 50 | 50 | `spot_prices` | `false` |
| `DayAheadPrices` | `DK2` | 200 | 50 | 50 | 50 | `spot_prices` | `false` |
| `ElectricityProdex5MinRealtime` | `DK1` | 200 | 50 | 50 | 50 | `power_balance` | `false` |
| `ElectricityProdex5MinRealtime` | `DK2` | 200 | 50 | 50 | 50 | `power_balance` | `false` |

Interpretation: limit 50 dry-run is validated for all supported DK1/DK2
dataset combinations. No database writes were committed. This validates command
orchestration and normalization path only. Confirmed writes still require
explicit `--confirm-local-db-write`, and `100` and `500` still require future
explicit enhancement. This remains local PostgreSQL dry-run validation only:
no committed writes, production database, Azure resources, scheduler, live API
polling, backend startup ingestion, frontend-triggered ingestion, automatic
polling loop, ML training, LLM use, or automatic control, dispatch,
activation, or operational functionality.

## Forecast Window Synthetic Preview

`forecast_window_preview.py` is a manual synthetic local preview for
`forecast-window-v0`. It uses only in-script caller-provided sample rows, calls
`build_forecast_window_forecast(...)`, and prints JSON for the `0-24h`,
`24-48h`, and `48-72h` forecast windows. `generated_at_utc` is fixed for stable
output.

```bash
python3 scripts/forecast_window_preview.py
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

Scenarios:

- `balanced`: rows across all three windows with mixed low/medium-like scores.
- `high-risk`: includes a negative-price and high-renewable-share row to show
  max-risk window aggregation.
- `empty-window`: leaves at least one matching-price-area window empty so that
  window returns `risk_level` `unknown`.

The script prints a scope warning and JSON including `price_area`,
`generated_at_utc`, `model_version`, `decision_support_only`, safety text, and
per-window counts, scores, reason codes, human-review action, explanation, and
decision-support-only flag.

This is synthetic/caller-provided preview-only. It does not require
`DATABASE_URL`, connect to a database, execute SQL, fetch live Energi Data
Service data, call DMI/weather APIs, add or use FastAPI endpoints, run frontend
code, create ingestion jobs, use Azure, add secrets, add auth, train ML models,
use LLMs, control assets, dispatch, activate, or perform operational
functionality.

## Report Summary Synthetic Preview

`report_summary_preview.py` is a manual synthetic local preview for
`report-summary-v0`. It uses only in-script caller-provided current-risk and
forecast-window sample data, calls `build_report_summary(...)`, and prints the
structured report payload as compact JSON by default. `generated_at_utc` is
fixed for stable output.

```bash
python3 scripts/report_summary_preview.py
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

Scenarios:

- `standard`: medium current risk with three forecast windows and one medium
  forecast window.
- `high-risk`: high current risk plus a high forecast window to demonstrate key
  findings and recommended human actions.
- `missing-current-risk`: incomplete current-risk input, which produces
  `current_risk_summary.status=unavailable`.
- `missing-forecast`: incomplete forecast input, which produces
  `forecast_window_summary.status=unavailable`.

The output includes `report_id`, `title`, `price_area`, `generated_at_utc`,
`report_version=report-summary-v0`, `decision_support_only=true`,
`human_review_required=true`, current-risk and forecast-window summaries,
model versions, key findings, recommended human actions, safety notes,
limitations, and source notes.

This is synthetic/caller-provided local preview-only. It does not generate PDF
files, fetch data, access a database, run SQL, expose an API, run frontend
code, call Energi Data Service, call DMI/weather APIs, create a scheduler, use
Azure, add secrets, add auth, train ML models, use LLMs, control assets,
dispatch, activate, or perform operational functionality. It is read-only
decision support only, must not be used for automatic control, dispatch, or
activation, and requires human review before planning.

### Observed Report Summary Preview Results

The following commands were run locally against synthetic in-script data only:

```bash
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

All four runs printed the synthetic-only warning and returned
`generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`. Safety notes were present and explicitly
prohibited automatic control, dispatch, and activation. Limitations were
present and included no database read/write, no live API calls, no ML training
in the report builder, no LLM use in the report builder, and caller-provided
data only.

Observed compact summary:

| Command | Price area | Current risk summary | Forecast summary | Result |
| --- | --- | --- | --- | --- |
| `python3 scripts/report_summary_preview.py --pretty` | DK1 | available, medium, score 45 | available, 3 windows | Key findings reported medium current risk, no high-risk forecast window, and caller-provided data only. |
| `python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty` | DK2 | available, high, score 75 | available, 3 windows | High-risk current risk and a high-risk `24-48h` forecast window were observed; key findings mentioned high risk and actions required human review. |
| `python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty` | DK1 | unavailable | available, 3 windows | Limitations added `missing or incomplete current risk input`; report generation remained safe. |
| `python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty` | DK1 | available, medium, score 45 | unavailable, 0 windows | Limitations added `missing or incomplete forecast input`; report generation remained safe. |

Interpretation: `report-summary-v0` preview works locally with
synthetic/caller-provided data and creates deterministic report payloads. It
does not generate PDF files yet, fetch data, read or write a database, expose
an API, use frontend code, use ML, or use LLMs. It is read-only decision
support only and must not be used for automatic control, dispatch, or
activation.

Next step: add Markdown report rendering after the JSON report payload is
stable. PDF export should come after Markdown/report rendering is stable.

### Observed Forecast Window Preview Results

The following commands were run locally against synthetic in-script rows only:

```bash
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

All three runs printed the synthetic-only warning, used
`generated_at_utc=2026-01-01T00:00:00Z`,
`model_version=rule-engine-v0+forecast-window-v0`, and
`decision_support_only=true`. The rows were caller-provided by the script only;
no database, SQL, live Energi Data Service, DMI/weather API, backend server,
frontend server, scheduler, Azure resource, secret, auth, ML, LLM, control,
dispatch, activation, or operational functionality was used.

Balanced scenario, command
`python3 scripts/forecast_window_preview.py --pretty`, returned
`price_area=DK1`:

| Window | Row count | Risk level | Max risk score | Top reason codes |
| --- | ---: | --- | ---: | --- |
| `0-24h` | 2 | medium | 45 | `EXCHANGE_NET_NOT_USED_V0:2`, `LOW_PRICE:1`, `LOW_RENEWABLE_SHARE:1`, `MODERATE_RENEWABLE_SHARE:1`, `NORMAL_PRICE:1` |
| `24-48h` | 2 | low | 30 | `EXCHANGE_NET_NOT_USED_V0:2`, `ELEVATED_RENEWABLE_SHARE:1`, `MODERATE_PRICE:1`, `MODERATE_RENEWABLE_SHARE:1`, `NORMAL_PRICE:1` |
| `48-72h` | 2 | medium | 35 | `EXCHANGE_NET_NOT_USED_V0:2`, `ELEVATED_RENEWABLE_SHARE:1`, `LOW_PRICE:1`, `LOW_RENEWABLE_SHARE:1`, `NORMAL_PRICE:1` |

High-risk scenario, command
`python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty`,
returned `price_area=DK2`. The `24-48h` window became `high` risk with
`row_count=2` and `max_risk_score=75`, demonstrating max-risk aggregation. Its
top reason codes included `NEGATIVE_PRICE:1` and
`HIGH_RENEWABLE_SHARE:1`, alongside `EXCHANGE_NET_NOT_USED_V0:2`,
`LOW_PRICE:1`, and `MODERATE_RENEWABLE_SHARE:1`.

Empty-window scenario, command
`python3 scripts/forecast_window_preview.py --scenario empty-window --pretty`,
returned `price_area=DK1`. The `24-48h` window had `row_count=0`,
`risk_level=unknown`, `average_risk_score=null`, `max_risk_score=null`,
`top_reason_codes=[]`, and an explanation that there was not enough
caller-provided data for the window. This demonstrates insufficient
caller-provided data handling.

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
`DK2`, composes those rows through nearest-timestamp pairing and
`compose_surplus_risk_input(...)`, and prints a JSON summary from
`evaluate_risk_backtest(rows)`.

The script requires `DATABASE_URL`, refuses to run unless the parsed host is
`localhost` or `127.0.0.1`, and accepts only DB-API URL format such as
`postgresql://localhost/flexsignal_ai`. It validates that generated SQL is
`SELECT` only and refuses forbidden operations including `INSERT`, `UPDATE`,
`DELETE`, `ALTER`, `DROP`, `CREATE`, and `TRUNCATE`.

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/risk_backtest_local_db.py --price-area DK1
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/risk_backtest_local_db.py --price-area DK2 --limit 100 --pretty
```

Rows are paired deterministically with `nearest_timestamp_v0_1`. Power-balance
rows are the primary timeline; each power-balance row is composed with the
nearest spot-price row by `timestamp_utc`. If distances tie, the earlier
spot-price timestamp wins, then original row order. If one table is empty,
remaining rows from the other table are still composed with the missing side
omitted. This is a technical local validation helper, not full historical model
validation.

The script prints a manual-use warning and writes only JSON summary output to
stdout. It does not write to the database, fetch live Energi Data Service data,
call HTTP APIs, create ingestion jobs, import or modify FastAPI startup, add
frontend code, use Azure, add secrets, add auth, train ML models, use LLMs,
control assets, dispatch, activate, or perform operational functionality.
