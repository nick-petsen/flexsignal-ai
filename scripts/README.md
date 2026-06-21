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

## Manual Energy Freshness Local DB Smoke

`energy_freshness_db_smoke.py` is a manual local-only smoke script for
DB-executed energy freshness reads. It uses the existing
`backend/app/db/repositories/energy_freshness.py` query-plan builders for
dry-run preview and
`backend/app/db/repositories/energy_freshness_reader.py` for explicit
DB-executed reads.

The default mode is dry-run only. It does not connect to a database, execute
SQL, write data, fetch Energi Data Service data, call weather APIs, expose an
API, add frontend behavior, or run automatically.

Dry-run:

```bash
python3 scripts/energy_freshness_db_smoke.py --price-area DK1 --pretty
```

Local read, only after a local database is available:

```bash
python3 scripts/energy_freshness_db_smoke.py --price-area DK1 --execute --database-url postgresql://localhost/flexsignal_ai --pretty
```

Real DB reads require both `--execute` and an explicit local `--database-url`.
Accepted URL shapes include `postgresql://localhost/flexsignal_ai`,
`postgresql://127.0.0.1/flexsignal_ai`, and
`postgresql:///flexsignal_ai`. Obvious remote/cloud URLs are refused and the
raw database URL is never printed.

The script performs SELECT-only freshness reads for `DK1` or `DK2`, writes no
data, does not fetch EDS/DMI data, does not expose an API, does not modify the
frontend, and must not be used for automatic control, dispatch, or activation.

Observed local DB smoke results:

| Area | DB query executed | DB write performed | Spot price rows | Spot price latest timestamp | Power balance rows | Power balance latest timestamp | Warnings |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
| DK1 | true | false | 53 | `2026-06-11T21:45:00+02:00` | 53 | `2026-06-10T17:00:00+02:00` | `[]` |
| DK2 | true | false | 50 | `2026-06-11T21:45:00+02:00` | 50 | `2026-06-10T17:00:00+02:00` | `[]` |

The observed smoke used explicit `--execute` and a local `--database-url`.
Reads were SELECT-only. No database writes were performed, no live EDS/DMI
calls were made, and no backend or frontend server was started. This proves
local DB-backed freshness reads work against the observed local data. It does
not mean production freshness monitoring exists; it prepares future DB-backed
API/dashboard freshness indicators only.

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

## Report Markdown Synthetic Preview

`report_markdown_preview.py` is a manual synthetic local Markdown preview for
`report-summary-v0`. It reuses the same scenario pattern as the JSON report
preview, imports `build_report_summary(...)` and
`render_report_summary_markdown(...)`, and prints Markdown to stdout.
`generated_at_utc` is fixed for stable output.

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

Scenarios:

- `standard`: includes current risk and a forecast summary with three windows.
- `high-risk`: includes high current risk and a high forecast window so the
  Markdown clearly shows high-risk findings and human-review actions.
- `missing-current-risk`: renders the current-risk summary as unavailable
  while keeping the forecast summary available.
- `missing-forecast`: renders the forecast-window summary as unavailable
  while keeping the current-risk summary available.

The Markdown output includes a title, report metadata, current-risk summary,
forecast-window summary, key findings, recommended human actions, safety
notes, limitations, and source notes.

This is synthetic/caller-provided local preview-only. It does not generate PDF
files, write files, fetch data, access a database, run SQL, expose an API, run
frontend code, call Energi Data Service, call DMI/weather APIs, create a
scheduler, use Azure, add secrets, add auth, train ML models, use LLMs,
control assets, dispatch, activate, or perform operational functionality. It
is read-only decision support only, must not be used for automatic control,
dispatch, or activation, and requires human review before planning.

### Observed Report Markdown Preview Results

The following commands were run locally against synthetic in-script data only:

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

All four runs printed the synthetic-only warning to stderr and printed Markdown
to stdout only. The rendered reports used
`generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`.

Observed compact summary:

| Command | Price area | Current risk summary | Forecast summary | Markdown result |
| --- | --- | --- | --- | --- |
| `python3 scripts/report_markdown_preview.py` | DK1 | available, medium, score `45` | available, 3 windows | Rendered title, report metadata, current risk, forecast windows, key findings, recommended human actions, safety notes, limitations, and source notes. |
| `python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk` | DK2 | available, high, score `75` | available, 3 windows | Rendered high current risk, high-risk `24-48h` forecast finding with `max_risk_score=80`, human-review actions, and safety notes prohibiting automatic control, dispatch, and activation. |
| `python3 scripts/report_markdown_preview.py --scenario missing-current-risk` | DK1 | unavailable | available, 3 windows | Rendered current risk as unavailable, kept the forecast summary available, included `missing or incomplete current risk input`, and did not crash. |
| `python3 scripts/report_markdown_preview.py --scenario missing-forecast` | DK1 | available, medium, score `45` | unavailable | Rendered the forecast window summary as unavailable, kept the current-risk summary available, included `missing or incomplete forecast input`, and did not crash. |

Interpretation:

- Markdown preview works locally with synthetic/caller-provided data.
- It renders `report-summary-v0` to readable Markdown.
- It prints to stdout only.
- It does not write files.
- It does not generate PDF files.
- It does not fetch data.
- It does not read or write a database.
- It does not expose an API.
- It does not use frontend code.
- It does not use ML or LLMs.
- It is read-only decision support only.
- It must not be used for automatic control, dispatch, or activation.

## Report PDF Synthetic Preview

`report_pdf_preview.py` is a manual synthetic local PDF preview for
`report-summary-v0`. It reuses the report-summary scenario pattern, calls
`build_report_summary(...)`, renders Markdown with
`render_report_summary_markdown(...)`, then renders a simple deterministic PDF
with `render_report_markdown_pdf_bytes(...)`.

```bash
python3 scripts/report_pdf_preview.py --output /tmp/flexsignal_report_preview.pdf
python3 scripts/report_pdf_preview.py --price-area DK2 --scenario high-risk --output /tmp/flexsignal_report_high_risk.pdf
python3 scripts/report_pdf_preview.py --scenario missing-current-risk --output /tmp/flexsignal_report_missing_current.pdf
python3 scripts/report_pdf_preview.py --scenario missing-forecast --output /tmp/flexsignal_report_missing_forecast.pdf
```

The script requires an explicit `--output PATH` and refuses to run without it.
It writes exactly one local PDF file to that path. If the file already exists,
the script exits non-zero unless `--force` is provided; `--force` overwrites
only the explicit output path.

The PDF output includes title, report metadata, current-risk summary,
forecast-window summary, key findings, recommended human actions, safety
notes, limitations, and source notes. It uses built-in ReportLab fonts only
and does not use browser or HTML rendering, external network resources, remote
fonts, images, CSS, templates, charts, or custom font files.

This is synthetic/caller-provided local preview-only. It does not expose an
API, add frontend download behavior, fetch data, access a database, run SQL,
call Energi Data Service, call DMI/weather APIs, create a scheduler, use
Azure, add secrets, add auth, train ML models, use LLMs, control assets,
dispatch, activate, or perform operational functionality. It is read-only
decision support only, must not be used for automatic control, dispatch, or
activation, and requires human review before planning.

### Observed Report PDF Smoke-Test Results

Manual/local PDF export v0 was validated after `report-summary-v0`, Markdown
rendering, the Markdown preview script, and Markdown preview result
documentation. It uses synthetic/caller-provided report data, builds
`report-summary-v0`, renders Markdown, then renders local PDF bytes. It writes
a PDF only when an explicit `--output` path is provided and requires `--force`
before overwriting an existing output path. No API endpoint or frontend
download exists.

Observed validation:

- Backend tests passed: `257 passed, 1 warning`.
- `py_compile` passed.
- `git diff --check` passed.
- Manual PDF preview runs passed.
- PDF byte/header check passed.
- Temporary PDFs were removed.
- Repository PDF check passed: no PDF files were left in the repository.
- Grep found only required safety wording and no forbidden integration imports.

Observed temporary PDF artifacts:

| Scenario | Output path | Bytes |
| --- | --- | ---: |
| `standard` | `/tmp/flexsignal_report_preview.pdf` | 9697 |
| `high-risk` | `/tmp/flexsignal_report_high_risk.pdf` | 9930 |
| `missing-current-risk` | `/tmp/flexsignal_report_missing_current.pdf` | 9263 |
| `missing-forecast` | `/tmp/flexsignal_report_missing_forecast.pdf` | 6918 |

All generated files started with `%PDF`, were larger than `1000` bytes, were
temporary validation artifacts, were removed after validation, and were not
committed to the repository.

Interpretation: PDF export v0 works for manual/local synthetic report
previews and proves the `report-summary-v0` to Markdown to PDF path. It is not
production report export, is not connected to live data or frontend, is not
exposed as an API, is not scheduled, does not use ML or LLMs, does not read or
write database data, and does not call Energi Data Service or DMI/weather
APIs. It remains read-only decision support only, requires human review, and
must not be used for automatic control, dispatch, activation, autonomous
decisions, operational energy-system integration, or automatic report jobs.

Keep PDF export manual/local for now. A future module may add a controlled
read-only report API or frontend download, but only after separate review. Do
not add automatic scheduled report generation yet.

## Audit Event Synthetic Preview

`audit_event_preview.py` is a manual synthetic local preview for
`audit-event-v0`. It uses fixed
`occurred_at_utc=2026-01-01T00:00:00Z`, imports
`build_audit_event(...)`, and prints deterministic audit event structures for
read-only decision-support actions. Compact JSON is printed by default, and
`--pretty` prints indented JSON.

```bash
python3 scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py --pretty
python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty
```

Supported `--event-type` values are `forecast_preview_requested`,
`current_risk_viewed`, `report_summary_built`,
`report_markdown_rendered`, `report_pdf_exported`, and `all`. The default is
`all`, which prints one object with an `events` array. A single event type
prints one object with an `event` field. Unknown event types are rejected by
CLI validation before any preview is built.

The preview uses synthetic/caller-provided fields only, including safe metadata
such as `price_area=DK1`, `report_version=report-summary-v0` where relevant,
`output_format=json|markdown|pdf` where relevant, `synthetic_preview_only=true`,
and `local_only=true`. It uses `actor_type=local_developer`,
`actor_id=local-dev` by default, `outcome=success`, and
`decision_support_only=true`.

Every generated event includes the `audit-event-v0` safety boundary:
read-only decision support, no automatic control, no dispatch, no activation,
no operational energy-system integration, and human review required.

This is synthetic/caller-provided local preview-only. It does not persist audit
logs yet, write files, access a database, run SQL, expose an API, run frontend
code, call Energi Data Service, call DMI/weather APIs, create a scheduler, use
Azure, add secrets, add auth, train ML models, use LLMs, control assets,
dispatch, activate, or perform operational functionality. It is read-only
decision-support audit structure only and must not be used for automatic
control, dispatch, or activation.

### Observed Audit Event Preview Results

The following commands were observed locally against synthetic/caller-provided
preview data only:

```bash
python3 -m py_compile scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py --pretty
python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_event_preview.py --event-type invalid-event
```

Observed compact summary:

| Command or check | Result |
| --- | --- |
| `python3 -m py_compile scripts/audit_event_preview.py` | Passed. |
| `python3 scripts/audit_event_preview.py` | Printed compact JSON with an `events` array. |
| `python3 scripts/audit_event_preview.py --pretty` | Printed indented JSON. |
| `python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty` | Printed one `report_pdf_exported` event. |
| `python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty` | Printed one `forecast_preview_requested` event. |
| `python3 scripts/audit_event_preview.py --event-type invalid-event` | Failed safely with exit code `2` and a clear argparse invalid-choice validation error. |
| Forbidden-pattern grep on `scripts/audit_event_preview.py` | Returned no matches. |
| `git diff --check` | Passed. |

Observed generated events covered `forecast_preview_requested`,
`current_risk_viewed`, `report_summary_built`,
`report_markdown_rendered`, and `report_pdf_exported`. Event content included
`event_version=audit-event-v0`, deterministic `audit_evt_...` ids, fixed
`occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, and `local_only=true`.

Every generated event included `safety_boundary` values:
`read_only_decision_support=true`, `no_automatic_control=true`,
`no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Interpretation: audit-event preview works locally with
synthetic/caller-provided data and demonstrates the future audit-event shape
for read-only decision-support actions. It does not persist events yet, prove
database audit logging, connect to auth or actor identity providers, create
operational logs, or provide production audit persistence.

Future audit work should first document audit preview results, then add
database persistence only later in a separate reviewed module.

## Audit Persistence Dry-Run Preview

`audit_persistence_preview.py` is a manual local dry-run preview for
`audit-event-v0` persistence planning. It imports `build_audit_event(...)` and
the audit repository SQL builder, uses fixed
`occurred_at_utc=2026-01-01T00:00:00Z`, builds one synthetic/caller-provided
audit event, and prints a JSON object containing the event and the
parameterized persistence plan.

```bash
python3 scripts/audit_persistence_preview.py
python3 scripts/audit_persistence_preview.py --pretty
python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty
```

Supported `--event-type` values are `forecast_preview_requested`,
`current_risk_viewed`, `report_summary_built`,
`report_markdown_rendered`, and `report_pdf_exported`. The default is
`report_pdf_exported`. Unknown event types are rejected by CLI validation.

The output includes `dry_run=true`, `database_write_performed=false`,
`requires_database_url=false`, `event`, and `persistence_plan`. The
`persistence_plan` shows the target `audit_events` table, SQL preview,
parameter keys and safe params, idempotency key/event id, and repository
conflict behavior `ON CONFLICT (event_id) DO NOTHING`.

This is dry-run only. It does not persist audit events, access a database,
require `DATABASE_URL`, run SQL, expose an API, use frontend code, write
files, generate PDFs, call Energi Data Service, call DMI/weather APIs, use ML,
use LLMs, create a scheduler, use Azure infrastructure, add auth, add
secrets, or add automatic audit logging. It is read-only decision-support
audit persistence preview only. A future module may add controlled repository
execution with an explicit database connection and tests after separate
review.

### Observed Audit Persistence Preview Results

The following commands/checks were observed:

```bash
python3 -m py_compile scripts/audit_persistence_preview.py
python3 scripts/audit_persistence_preview.py
python3 scripts/audit_persistence_preview.py --pretty
python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_persistence_preview.py --event-type invalid-event
```

Observed compact summary:

| Check | Result |
| --- | --- |
| `py_compile` | Passed. |
| Default preview | Printed compact JSON. |
| `--pretty` | Printed indented JSON. |
| `forecast_preview_requested` | Dry-run passed. |
| `report_pdf_exported` | Dry-run passed. |
| Invalid event type | Failed safely with exit code `2` and argparse invalid-choice output. |
| Forbidden-pattern grep | Returned no matches. |
| `git diff --check` | Passed. |

Observed output included `dry_run=true`,
`database_write_performed=false`, `requires_database_url=false`, `event`, and
`persistence_plan`. The event included
`event_version=audit-event-v0`, deterministic `audit_evt_...` event id,
fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, and `local_only=true`.

The event safety boundary preserved `read_only_decision_support=true`,
`no_automatic_control=true`, `no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`. The persistence plan included the
`audit_events` table target, SQL/SQL preview, parameter keys/params,
`event_id` as the idempotency key, and
`ON CONFLICT (event_id) DO NOTHING` conflict behavior.

Interpretation: the preview works locally with synthetic/caller-provided data
and demonstrates parameterized persistence planning only. It does not connect
to a database, execute SQL, persist audit events, require `DATABASE_URL`,
expose API/frontend/report/PDF flows, generate PDFs, write files, call
EDS/DMI, use ML/LLMs, add scheduling/Azure/auth/secrets, add automatic audit
logging, or add control, dispatch, activation, or operational functionality.
Future controlled local write testing must be separate and reviewed.

## Audit DB Write Smoke

`audit_db_write_smoke.py` is a manual local-only smoke script for one
deterministic synthetic `audit-event-v0` write to the `audit_events` table. It
imports `build_audit_event(...)` and the audit repository SQL builder, uses
fixed `occurred_at_utc=2026-01-01T00:00:00Z`, and defaults to dry-run output
without opening a database connection.

Dry-run:

```bash
python3 scripts/audit_db_write_smoke.py --pretty
```

Local write, only against an explicit local database:

```bash
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
```

Event type example:

```bash
python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty
```

Supported `--event-type` values are `forecast_preview_requested`,
`current_risk_viewed`, `report_summary_built`,
`report_markdown_rendered`, and `report_pdf_exported`. The default is
`report_pdf_exported`.

Real writes require both `--execute` and an explicit `--database-url`. The URL
must be local by default: `localhost`, `127.0.0.1`, or local Unix-socket style
such as `postgresql:///flexsignal_ai`. Obvious remote hosts, public IPs, and
cloud-style URLs are rejected. The script never prints the raw database URL.

When executed, the script runs the same parameterized
`ON CONFLICT (event_id) DO NOTHING` insert twice to confirm idempotency, then
commits. With `--verify-read`, it reads back the row by `event_id` only.

This is manual/local smoke only. It writes only to `audit_events` and does not
write energy, forecast, or report data. It does not expose an API, add
frontend code, add automatic audit logging, integrate report/PDF/API/frontend
flows, create a scheduler, use Azure infrastructure, add auth or secrets, call
Energi Data Service, call DMI/weather APIs, use ML, use LLMs, or add control,
dispatch, activation, or operational functionality.

### Observed Audit DB Write Smoke Results

The following commands/checks were observed:

```bash
python3 -m py_compile scripts/audit_db_write_smoke.py backend/tests/test_audit_db_write_smoke.py
python -m pytest tests/test_audit_db_write_smoke.py -q
python -m pytest
python3 scripts/audit_db_write_smoke.py
python3 scripts/audit_db_write_smoke.py --pretty
python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_db_write_smoke.py --execute
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://remote.example.com/flexsignal_ai
```

Observed compact summary:

| Check | Result |
| --- | --- |
| `py_compile` | Passed. |
| Focused smoke tests | `7 passed`. |
| Full backend suite | `317 passed, 1 warning`. |
| Default dry-run | Passed. |
| `--pretty` dry-run | Passed. |
| `forecast_preview_requested` dry-run | Passed. |
| `--execute` without `--database-url` | Failed safely with exit code `2`. |
| Remote database URL | Failed safely with exit code `2`. |
| Forbidden-pattern grep on script and test | Returned no matches. |
| `git diff --check` | Passed. |

No live DB writes were performed during those earlier guardrail checks.

### Observed Manual Local Audit DB Write Smoke Result

After the `audit-event-v0` foundation, `audit_events` schema/repository,
dry-run preview script, manual local DB write smoke script, and prior full
backend unit validation existed, a human manually ran:

```bash
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
```

Alembic used `PostgresqlImpl`, assumed transactional DDL, migrated
`0001_initial_schema` to `0002_audit_events`, added the audit-event-v0
persistence foundation, and succeeded.

First smoke output:

- `conflict_behavior`: `ON CONFLICT (event_id) DO NOTHING`
- `database_write_performed`: `true`
- `dry_run`: `false`
- `execute_requested`: `true`
- `event_id`: `audit_evt_f8ea1513efa7fa0067b0ca04`
- `event_type`: `report_pdf_exported`
- `inserted_attempts`: `2`
- `local_database_only`: `true`
- `rowcount_first_insert`: `1`
- `rowcount_second_insert`: `0`
- `table`: `audit_events`
- `verify_read_performed`: `true`
- `warnings`: `[]`
- `verified_row` was returned by `event_id`

Second smoke output used the same
`event_id=audit_evt_f8ea1513efa7fa0067b0ca04` and
`event_type=report_pdf_exported`. It reported
`database_write_performed=true`, `rowcount_first_insert=0`,
`rowcount_second_insert=0`, `verify_read_performed=true`, and returned
`verified_row`, confirming idempotency across repeated script executions.

The verified row included `event_version=audit-event-v0`,
`event_type=report_pdf_exported`, `action=preview_report_pdf_export`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, `resource_type=report_pdf`,
`resource_id=report-summary-v0:DK1:synthetic-pdf`, and metadata
`local_only=true`, `output_format=pdf`, `price_area=DK1`,
`report_version=report-summary-v0`, and `synthetic_preview_only=true`.

The event was constructed deterministically. The verified row returned
`occurred_at_utc` as `2026-01-01T01:00:00+01:00`; this is interpreted as
database/session timezone rendering of the stored `timestamptz` instant, not a
blocker for the smoke result. Future code may normalize read-back display to
UTC if needed.

The raw `DATABASE_URL` was not printed. Output preserved
`read_only_decision_support=true`, `no_automatic_control=true`,
`no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Interpretation: local `audit_events` DB write is now manually verified. The
repository insert path works against local Postgres, idempotency works via
`ON CONFLICT (event_id) DO NOTHING`, and verify-read by `event_id` works.
This does not mean production audit persistence is enabled, does not add
automatic audit logging, and does not connect audit persistence to API,
frontend, report, or PDF flows. No FastAPI endpoint, frontend behavior,
automatic audit logging, report/PDF integration, scheduler, Azure
infrastructure, auth/Entra integration, live EDS/DMI calls, ML/LLM use,
control, dispatch, activation, or operational functionality was added. A
future module may add a read-only API-side audit logging design or manual API
audit dry-run, but automatic audit persistence must not be wired into runtime
flows yet and production DB writes require explicit review.

## Audit Writer Service Foundation

`backend/app/audit/writer.py` provides `write_audit_event(conn, event)` and
the `execute_audit_event_insert` alias for explicitly writing validated
`audit-event-v0` records through a caller-provided connection. It uses the
existing audit repository insert SQL builder and does not create database
connections or read `DATABASE_URL`.

The writer validates `audit-event-v0`, `decision_support_only=true`, and the
full read-only safety boundary before executing SQL:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Invalid events raise `ValueError` and execute no SQL. Valid events return
`event_id`, `event_type`, `table`, `database_write_performed`, `rowcount`,
`conflict_behavior`, `safety_boundary_preserved`, and `warnings`.

Observed validation:

| Check | Result |
| --- | --- |
| Focused audit writer tests | `14 passed` |
| Full backend suite | `331 passed, 1 warning` |
| `py_compile` for writer and tests | Passed |
| Safety-boundary grep | Matched only safety-boundary strings and negative/static assertions |
| `git diff --check` | Passed |

The writer tests used fake connection/cursor objects only, and no live
database writes were performed.

This is a backend foundation only. It does not expose a FastAPI endpoint, add
frontend behavior, add automatic audit logging, integrate report/PDF flows,
create a scheduler, use Azure infrastructure, add auth/Entra integration, call
live EDS/DMI APIs, use ML/LLMs, or add control, dispatch, activation, or
operational functionality. Runtime integration remains intentionally deferred.

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
