# Model Card: rule-engine-v0

## Overview

`rule-engine-v0` is a deterministic, rule-based surplus-risk scorer for DK1 and
DK2 electricity areas. It is not a machine-learning model and does not use LLM
reasoning. The implementation is pure Python decision-support logic.

## Intended Use

The model estimates low, medium, or high surplus electricity production risk for
human review. It is read-only decision support for `v0.1`; it must not be used
as an autonomous decision-maker or critical operational system.

`POST /api/risk/preview` wraps `rule-engine-v0` for caller-provided JSON data
only. The preview API does not fetch live data, read from a database, write to a
database, or connect to assets or operational systems in this step.

`POST /api/forecast/preview` wraps `forecast-window-v0` for caller-provided
DK1/DK2 rows only. It returns deterministic `0-24h`, `24-48h`, and `48-72h`
window summaries and does not fetch EDS or DMI/weather data, read or write a
database, start jobs, use ML, use LLMs, or perform operational actions.

`GET /api/risk/current?price_area=DK1|DK2` wraps the same rule engine for the
latest existing local database rows. It lazily requires `DATABASE_URL` only when
the endpoint is called, reads the most recent `spot_prices` and `power_balance`
rows for the requested price area through existing read-only query paths,
returns source-table metadata, and does not write to the database, fetch live
Energi Data Service data, schedule ingestion, or connect to operational
systems.

## Current MVP Status

`rule-engine-v0` is the current read-only scoring baseline for the technical
MVP foundation. It is simple, deterministic, testable, and explainable. It is
not a trained forecasting model, not an LLM decision engine, and not validated
for production operations.

The frontend spot price and power balance trend charts are not part of
`rule-engine-v0` and do not change scoring, forecasting, backtest pairing,
thresholds, input composition, or predictive-performance claims. They are
lightweight read-only dashboard visualizations in/near the existing Spot
prices and Power balance cards. The spot price chart uses only rows returned
by the existing manual `Load spot prices` action. The power balance chart uses
only rows returned by the existing manual `Load power balance` action and
plots production MW over timestamp order. Both support `DK1` and `DK2`
through the existing selected price area, render only when returned rows
exist, keep the existing tables visible, and use inline SVG/HTML/CSS without a
charting dependency.

The charts safely handle empty, single-point, multi-point, missing, and
invalid values. They do not auto-load, poll, add a backend endpoint, forecast,
trade, control assets, dispatch, activate, automate anything, execute SQL,
write to the database, call live Energi Data Service, call DMI/weather APIs,
use ML/LLMs, write audit events, or wire report/PDF behavior.

Together, the spot price chart and power balance / production chart complete
the first MVP pair of read-only dashboard visualizations. They are display
surfaces only and are not forecasting models or model inputs.

The Forecast preview card includes a simple visual for existing
`forecast-window-v0` output. It is not part of `rule-engine-v0` and does not
change scoring, thresholds, input composition, row pairing, forecasting
logic, or backtest interpretation. It appears only after the existing manual
`Load forecast preview` response exists, uses only that deterministic
synthetic/caller-provided preview response, displays `0-24h`, `24-48h`, and
`48-72h` windows with `risk_level`, max risk score as a 0-100 score, visible
horizontal risk bars, `top_reason_codes`, and `recommended_human_action`, and
keeps raw/text forecast details visible below the visual.

Observed manual frontend forecast window visual smoke started the backend
locally, started the frontend locally with `NEXT_PUBLIC_API_BASE_URL`
pointing to the backend, and opened the local dashboard in a browser.
Forecast preview was loaded manually by button click only; no auto-load or
polling was observed. The visual displayed `0-24h` as low with max risk score
`30/100`, `24-48h` as high with max risk score `75/100`, and `48-72h` as low
with max risk score `10/100`. Each window displayed a visible horizontal risk
bar, `top_reason_codes`, and `recommended_human_action`; raw/text forecast
details remained visible below the visual. The displayed response included
`model_version=rule-engine-v0+forecast-window-v0`,
`decision_support_only=true`, and
`generated_at_utc=2026-01-01T00:00:00Z`.

The manual smoke does not change `rule-engine-v0`, scoring thresholds, input
composition, backtest pairing, predictive-performance claims, or production
forecast validation status. The visual uses only the existing manual
`Load forecast preview` response with synthetic/caller-provided preview data.
It adds no new backend endpoint, changes no backend behavior, performs no
database write, executes no SQL, calls no live EDS/DMI API, uses no ML/LLM
behavior, and adds no automatic control, dispatch, activation, or operational
functionality. Human review remains required.

The Current surplus risk card also includes a simple visual
decision-support risk score. It is not part of `rule-engine-v0` and does not
change scoring, thresholds, input composition, pairing, forecasting, or
backtest interpretation. It appears only after the existing manual
`Load current risk` response exists, uses only that response, displays valid
`risk_score` values as a 0-100 HTML/CSS bar, displays `risk_level`, keeps the
raw risk details visible, and handles missing or invalid score/level fields
safely. It adds no endpoint, backend behavior, ML/LLM behavior, database
write, audit write, report/PDF wiring, automation, control, dispatch,
activation, or operational functionality. It does not forecast by itself or
trigger recommendations by itself; human review remains required.

Observed manual frontend dashboard chart smoke started the backend locally,
started the frontend locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
backend, and opened the local dashboard in a browser. Requests were manual
button clicks only; no auto-load or polling was observed. For DK1, spot prices
loaded, the spot price table remained visible, the spot price trend chart
displayed, power balance loaded, the power balance table remained visible, and
the power balance trend chart displayed. After switching the price area to
DK2, the same spot price and power balance table/chart behavior was observed.
The charts used only manually loaded backend rows.

The manual chart smoke did not change `rule-engine-v0` and did not execute
forecasting logic from the chart itself. The frontend chart path uses
lightweight inline charts with no charting dependency, no new backend
endpoint, no browser call to Energi Data Service, no DMI/weather call, no SQL
execution from the frontend, no database writes, and no control, dispatch,
activation, polling, energy-asset control, or automation. UI wording remains
read-only: `Manual read-only spot price rows`, `Manual read-only power
balance rows`, and `Trend from loaded backend rows`.

Observed frontend chart validation recorded `npm run build`
passing and `git diff --check` passing. `npm run lint` and
`npm run typecheck` scripts did not exist. No backend server was started, no
database was accessed, no SQL was executed, and no live EDS/DMI APIs were
called. This includes the observed frontend power balance chart validation. A
future module may improve dashboard layout and chart readability or add a
manual local frontend smoke test for both charts without adding ingestion,
automation, DB writes, or backend changes.

Observed frontend risk score visual validation recorded `npm run build`
passing after `npm ci` installed frontend dependencies from the existing
lockfile. `git diff --check` passed. `npm run lint` and
`npm run typecheck` scripts did not exist. No backend server was started, no
database was accessed, no SQL was executed, and no live EDS/DMI APIs were
called. `npm audit` reported 2 moderate findings, but dependency files were
not changed in this scoped UI/docs task. This validation did not change
`rule-engine-v0` behavior or add a backend endpoint. A future module may
manually smoke-test the risk visual in the local frontend/backend dashboard,
and another future module may improve dashboard layout and visual hierarchy
without adding ingestion, automation, database writes, backend changes,
ML/LLM behavior, or operational functionality.

Observed manual frontend risk score visual smoke started the backend locally,
started the frontend locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
backend, and opened the local dashboard in a browser. Current surplus risk
was loaded manually by button click only; no auto-load or polling was
observed.

DK1 displayed `price_area=DK1`, `risk_score=35/100`, `risk_level=medium`, the
visible `Decision-support risk score` box, a visible 0-100 horizontal bar,
`Human review required`, raw/text risk details below the visual, and
`decision_support_only=true`. DK2 displayed `price_area=DK2`,
`risk_score=20/100`, `risk_level=low`, the same visual box, 0-100 horizontal
bar, human-review wording, raw/text risk details below the visual, and
`decision_support_only=true`.

The manual smoke does not change `rule-engine-v0`, scoring thresholds, input
composition, backtest pairing, or predictive-performance claims. The visual
uses only the existing manual `Load current risk` response. It adds no new
backend endpoint, changes no backend behavior, performs no database write,
executes no SQL, calls no live EDS/DMI API, uses no ML/LLM behavior, and adds
no automatic control, dispatch, activation, or operational functionality.
Human review remains required.

`GET /api/energy/freshness?price_area=DK1|DK2` now exposes a read-only preview
of `eds-data-freshness-read-model-v0` for future freshness indicators. It
returns parameterized SELECT query plans for DK1/DK2 `spot_prices` and
`power_balance` summaries with earliest/latest timestamps, row counts, source
labels, and empty-result warnings. It does not execute SQL, connect to a
database, read `DATABASE_URL`, call live EDS or DMI/weather APIs, write data,
or affect the forecasting model. Its purpose is MVP data trust and debugging
only.

The preview also includes a combined energy freshness summary plan. All plans
return parameterized SELECT SQL only, include params and source labels, and
reject invalid `price_area` values outside `DK1`/`DK2` with HTTP 400. The API
response includes `price_area`, `dry_run=true`,
`database_query_executed=false`, `database_write_performed=false`,
`requires_database_url=false`, `freshness_plans`,
`spot_price_freshness_plan`, `power_balance_freshness_plan`, warnings, and the
explicit read-only human-review safety boundary. Observed validation recorded
focused energy freshness API tests passing with `12 passed, 1 warning`, the
full backend suite passing with `442 passed, 1 warning`, `py_compile`
passing, forbidden-pattern grep matching only required safety flags and
negative/safety assertions in tests, `git diff --check` passing, and no live
DB writes.

Interpretation: this read model is not part of `rule-engine-v0`, is not a
forecasting engine, and does not change scoring behavior. The frontend
dashboard has a manual energy freshness card backed by
`fetchEnergyFreshness()`. The card calls the API through the existing
`NEXT_PUBLIC_API_BASE_URL` pattern and displays dry-run query-plan previews,
`database_query_executed`, `database_write_performed`,
`requires_database_url`, spot price and power balance freshness plan status,
warnings, and the human-review safety boundary. UI wording explicitly
communicates freshness query plan preview only, no database query executed, no
database write performed, no new EDS/DMI fetch, and read-only decision
support. It does not prove production data freshness, fetch new EDS data,
execute queries, schedule jobs, add Azure/auth infrastructure, use ML/LLMs,
write audit events, or add control, dispatch, activation, or operational
functionality.

A backend-only DB-executed energy freshness reader now exists at
`backend/app/db/repositories/energy_freshness_reader.py`, and
`GET /api/energy/freshness/read?price_area=DK1|DK2` now exposes that reader
through a controlled FastAPI route. This DB-backed API is separate from the
dry-run query-plan preview. It requires `DATABASE_URL` at request time, opens
a request-scoped database connection, validates `DK1`/`DK2`, returns HTTP 400
for invalid price areas, executes SELECT-only freshness reads, and returns
structured dictionaries with `price_area`, `dry_run=false`,
`database_query_executed=true` on success,
`database_write_performed=false`, `requires_database_url=true`,
`freshness_result`, `spot_price_freshness`, `power_balance_freshness`,
warnings, and the same read-only human-review safety boundary. App import
still exposes the route without `DATABASE_URL`. If `DATABASE_URL` is missing
during request execution, it returns a safe HTTP 503 warning without exposing
raw connection details.

The reader and API do not fetch new EDS data, call DMI/weather APIs, write to
the database, add migrations, schedule jobs, add Azure/auth behavior, use
ML/LLMs, write audit events, wire report/PDF flows, or add control, dispatch,
activation, closed-loop, live-control, or operational functionality. The
frontend can manually display the endpoint response through the backend API
only; it does not execute SQL or access the database directly. They prepare
dashboard data trust indicators only and do not change `rule-engine-v0`
scoring.
Implemented functions are `read_spot_price_freshness`,
`read_power_balance_freshness`, and `read_energy_freshness_summary`.
SQL safety requires parameterized plans that start with `SELECT`; mutating
tokens including `INSERT`, `UPDATE`, `DELETE`, `UPSERT`, `CREATE`, `ALTER`,
`DROP`, `TRUNCATE`, and `MERGE` are blocked before cursor execution. The
combined summary returns `spot_price_freshness`, `power_balance_freshness`,
`warnings`, and the safety boundary. Observed DB-backed API validation
recorded focused API freshness read tests passing with
`9 passed, 1 warning`, the full backend suite passing with
`483 passed, 1 warning`, `py_compile` passing, forbidden-pattern grep matching
only defensive/negative assertions in tests, `git diff --check` passing,
mocked database connections only, and no live DB writes. The DB-backed read
API uses fake/monkeypatched database connections in tests only; no live DB is
required for automated validation.

Observed local DB-backed freshness read API smoke started the backend locally
with `DATABASE_URL=postgresql://localhost/flexsignal_ai` and called
`GET /api/energy/freshness/read?price_area=DK1`, `DK2`, and invalid `SE3`.
DK1 returned HTTP 200 with `dry_run=false`,
`database_query_executed=true`, `database_write_performed=false`,
`requires_database_url=true`, spot price `row_count=53`, spot price latest
timestamp `2026-06-11T21:45:00+02:00`, power balance `row_count=53`, and
power balance latest timestamp `2026-06-10T17:00:00+02:00`. DK2 returned
HTTP 200 with the same execution flags, spot price `row_count=50`, spot price
latest timestamp `2026-06-11T21:45:00+02:00`, power balance `row_count=50`,
and power balance latest timestamp `2026-06-10T17:00:00+02:00`. Invalid
`SE3` returned HTTP 400 with `Unsupported price_area`.

The local API smoke performed SELECT-only freshness reads, preserved the
read-only human-review safety boundary, performed no database writes, made no
live EDS/DMI calls, and triggered no ingestion. It proves local DB-backed API
freshness reads work for the observed local data. It does not change
`rule-engine-v0`, establish production monitoring, create an Azure deployment,
or validate predictive performance. The frontend can now display this
DB-backed read result manually for dashboard data trust indicators.

`scripts/energy_freshness_db_smoke.py` is that controlled manual local DB
freshness smoke. It defaults to dry-run query-plan JSON and performs
DB-executed freshness SELECTs only when both `--execute` and an explicit local
`--database-url` are supplied. Example commands:

```bash
python3 scripts/energy_freshness_db_smoke.py --price-area DK1 --pretty
python3 scripts/energy_freshness_db_smoke.py --price-area DK1 --execute --database-url postgresql://localhost/flexsignal_ai --pretty
```

This smoke script does not change `rule-engine-v0`, train a model, fetch
EDS/DMI data, write data, expose API/frontend behavior, add scheduled jobs,
add Azure/auth infrastructure, use ML/LLMs, write audit events, wire
report/PDF flows, or add control, dispatch, activation, or operational
functionality. It is manual/local read-only freshness validation only.

Observed local DB smoke results:

| Area | DB query executed | DB write performed | Spot price rows | Spot price latest timestamp | Power balance rows | Power balance latest timestamp | Warnings |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
| DK1 | true | false | 53 | `2026-06-11T21:45:00+02:00` | 53 | `2026-06-10T17:00:00+02:00` | `[]` |
| DK2 | true | false | 50 | `2026-06-11T21:45:00+02:00` | 50 | `2026-06-10T17:00:00+02:00` | `[]` |

The observed smoke used explicit `--execute` and a local `--database-url`.
Reads were SELECT-only. No database writes were performed, no live EDS/DMI
calls were made, and no backend or frontend server was started. This proves
local DB-backed freshness reads work for the observed local data, but it does
not change `rule-engine-v0`, establish production freshness monitoring, or
validate predictive performance. It prepares future DB-backed API/dashboard
freshness indicators only.

Observed frontend freshness card validation:

- `npm run build` passed.
- `git diff --check` passed.
- `npm run lint` did not exist.
- `npm run typecheck` did not exist.
- No backend server was started.
- No frontend dev server was started.
- No database was accessed.
- No SQL was executed.
- No live Energi Data Service or DMI/weather APIs were called.

Frontend DB-backed energy freshness read wiring validation is documentation
of the display path only. `fetchEnergyFreshnessRead(priceArea)` exists and
manually calls
`GET /api/energy/freshness/read?price_area=DK1|DK2`; the existing
`fetchEnergyFreshness()` dry-run preview helper remains available for
`GET /api/energy/freshness?price_area=DK1|DK2`. The dashboard card provides
controls for both DB-backed read mode and dry-run preview mode.

The DB-backed read card displays SELECT-only freshness fields returned by the
backend: latest timestamps and row counts for spot price and power balance,
`database_query_executed`, `database_write_performed`,
`requires_database_url`, warnings, and the read-only human-review safety
boundary. Missing backend `DATABASE_URL` HTTP 503 responses are mapped to
`DB-backed freshness read requires backend DATABASE_URL.` The frontend does
not execute SQL, access the database directly, write to the database, trigger
ingestion, call live EDS/DMI APIs, or change `rule-engine-v0`. It only
displays stored/configured DB freshness returned by the backend and remains
read-only decision support, not production monitoring or operational control.

This documentation step did not change backend behavior, add backend
endpoints, add database code, execute SQL, write to a database, add
migrations, call live Energi Data Service, call DMI/weather APIs, add auth,
add Azure infrastructure, add ML/LLM behavior, write audit events, wire
report/PDF flows, or add control, dispatch, activation, closed-loop,
live-control, or operational functionality. Frontend DB-backed freshness
display is a separate manual dashboard action and remains read-only.

Observed manual frontend plus backend energy freshness smoke:

- Backend local configuration:
  `DATABASE_URL=postgresql://localhost/flexsignal_ai`.
- Frontend local configuration:
  `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`.
- Browser opened the local dashboard.
- Requests were manual button clicks only.
- No auto-load or polling was observed.
- DK1 and DK2 spot prices loaded.
- DK1 and DK2 power balance loaded.
- DK1 and DK2 current surplus risk loaded.
- Forecast preview loaded.
- The energy freshness card loaded DB-backed SELECT-only read results.
- The energy freshness card also loaded dry-run query-plan previews.

Observed DB-backed freshness read results:

| Area | `dry_run` | `database_query_executed` | `database_write_performed` | `requires_database_url` | Spot price rows | Spot price latest timestamp | Power balance rows | Power balance latest timestamp |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- |
| DK1 | false | true | false | true | 53 | `2026-06-11T21:45:00+02:00` | 53 | `2026-06-10T17:00:00+02:00` |
| DK2 | false | true | false | true | 50 | `2026-06-11T21:45:00+02:00` | 50 | `2026-06-10T17:00:00+02:00` |

Observed dry-run freshness plan results: `dry_run=true`,
`database_query_executed=false`, `database_write_performed=false`,
`requires_database_url=false`, spot price query plan present, power balance
query plan present, and no SQL executed by the dry-run endpoint.

UI safety wording remained aligned with the model boundary: DB-backed
freshness read, SELECT-only read, no database write performed, freshness of
stored local/configured database data, does not fetch new EDS/DMI data, and
does not imply ingestion has run. This smoke does not change
`rule-engine-v0`, does not establish production monitoring, does not fetch
new data, does not write to the database, does not deploy Azure
infrastructure, and does not add automatic control, dispatch, activation, or
operational behavior.

Working read-only paths around the model:

- `POST /api/risk/preview` scores caller-provided DK1/DK2 JSON.
- `POST /api/forecast/preview` summarizes caller-provided DK1/DK2 rows into
  three forecast windows.
- `GET /api/risk/current` scores the latest existing local DK1/DK2 rows.
- The frontend can manually request current risk and forecast-window previews
  through the backend API.
- The frontend can manually request energy freshness dry-run query-plan
  previews through `GET /api/energy/freshness`.
- The frontend can manually request
  `GET /api/energy/freshness/read` for DB-backed SELECT-only freshness reads
  from stored local/configured database data.
- Synthetic and local DB read-only backtest previews exist.
- Local DB backtest row pairing uses `nearest_timestamp_v0_1`.

Validated local sample results:

| Area | Current risk API smoke-test | Local DB rows | Local DB backtest | Average risk score |
| --- | --- | --- | --- | ---: |
| DK1 | medium, score 35 | 53 spot prices, 53 power-balance rows | low=1, medium=52, high=0 | 34.5283 |
| DK2 | low, score 20 | 50 spot prices, 50 power-balance rows | low=42, medium=8, high=0 | 21.8 |

The latest local validation confirms that the read-only API, frontend manual
loads, local DB backtest, and deterministic scoring path work for DK1 and DK2
after the `limit 50` local import. It supports a local technical MVP demo only.
It does not establish predictive accuracy, statistical calibration, commercial
validity, production readiness, or operational fitness.

## Inputs

- `price_area`: `DK1` or `DK2`
- `timestamp_utc`: required string
- `price_dkk_per_mwh`: optional spot price
- `production_mw`: optional total production
- `consumption_mw`: optional consumption context
- `wind_onshore_mw`, `wind_offshore_mw`, `solar_mw`: optional renewable
  production fields
- `exchange_net_mw`: optional exchange context

## Method

The score starts at `0` and is capped at `100`.

- Negative prices add high risk.
- Low positive prices add medium risk.
- Moderately low prices add low risk.
- Higher renewable share, calculated from wind and solar over total production,
  increases risk.
- Missing price, production, or renewable fields reduce confidence.

Risk levels are:

- `low`: 0-34
- `medium`: 35-69
- `high`: 70-100

Confidence starts at `1.0`, is reduced for missing key data, has a floor of
`0.2`, and is rounded to two decimals.

## Risk Input Composer

`compose_surplus_risk_input` is a deterministic mapper from existing
`spot_prices` and `power_balance` row dictionaries into the `rule-engine-v0`
input shape. It does not score risk by itself, connect to a database, execute
SQL, call live APIs, perform ML or LLM logic, or perform control, dispatch, or
activation.

## Backtest Evaluator

`evaluate_risk_backtest` is a pure Python local evaluator for
`rule-engine-v0` outputs. It passes each supplied row dictionary to
`calculate_surplus_risk`, aggregates risk-level counts, average scores,
confidence, reason codes, missing-data counts, and row-level validation errors.

The evaluator is not ML training, threshold tuning, forecasting, or autonomous
decision-making. It does not connect to a database, execute SQL, call live APIs,
poll services, ingest data, use LLMs, or perform control, dispatch, activation,
or operational workflows.

## Forecast Window Aggregation

`forecast-window-v0` is a pure Python deterministic aggregation layer over
caller-provided surplus-risk input rows. It groups matching DK1/DK2 rows into
three non-overlapping windows: `0-24h`, `24-48h`, and `48-72h`, then reuses
`calculate_surplus_risk` from `rule-engine-v0` for row-level scoring.

The window risk level is based on the maximum observed row risk score in the
window, not the average alone. Empty windows return `unknown` with no risk
score and an explanation that there is not enough caller-provided data.

`forecast-window-v0` is not a machine-learning model, not DMI/weather based
yet, not production forecast validation, and not an LLM forecast engine. The
`POST /api/forecast/preview` API exposes this aggregation for caller-provided
rows only. It does not fetch data, write data, call live Energi Data Service,
call DMI/weather APIs, connect to a database, schedule jobs, train models, or
use secrets, auth, Azure infrastructure, or operational integrations.

The frontend dashboard includes a manual read-only forecast preview card that
calls `POST /api/forecast/preview` only after a button click. It sends
deterministic synthetic/caller-provided demo rows with timezone-aware
`generated_at_utc`, uses only the backend API base URL helper, does not
auto-load or poll, does not call Energi Data Service or DMI/weather APIs from
the browser, and does not read or write a database. It is a preview surface
only, not production forecast validation.

All outputs are read-only decision support only and must not be used for
automatic control, dispatch, activation, closed-loop workflows, asset
connections, plant/device commands, or live control signals.

## Report Summary Foundation

`report-summary-v0` is a pure Python data-structure builder for read-only
decision-support reporting. It combines caller-provided current-risk output and
caller-provided `forecast-window-v0` output into a deterministic structured
payload used by Markdown rendering and manual local PDF preview generation.

The report summary builder does not fetch data, read from or write to a
database, expose a FastAPI endpoint, call Energi Data Service, call DMI/weather
APIs, train ML models, or use LLMs. It only normalizes supplied dictionaries
or compatible objects into report fields, model-version metadata,
deterministic key findings, required human-review actions, safety notes,
limitations, and source notes.

`render_report_summary_markdown(...)` is the Markdown renderer for
`report-summary-v0`. It accepts a caller-provided report dictionary and returns
a deterministic Markdown string with report metadata, current-risk summary,
forecast-window summary, key findings, recommended human actions, safety
notes, limitations, and source notes. Missing current-risk or forecast-window
summaries render as clear unavailable sections, and optional missing fields use
safe fallback text.

The Markdown renderer does not write files, fetch data, access a database,
expose an API, use frontend code, use ML, or use LLMs. It is read-only
decision support only, requires human review, and must not be used for
automatic control, dispatch, activation, or autonomous decisions.

`render_report_markdown_pdf_bytes(...)` is the manual PDF renderer for
caller-provided Markdown report content. It returns PDF bytes and does not
write files, fetch data, access a database, expose an API, use frontend code,
use ML, or use LLMs. It uses simple ReportLab rendering with built-in fonts,
headings, wrapped text, bullets, and page breaks only.

`scripts/report_pdf_preview.py` is a manual synthetic local PDF preview. It
uses fixed `generated_at_utc=2026-01-01T00:00:00Z`, in-script
caller-provided data, `build_report_summary(...)`,
`render_report_summary_markdown(...)`, and
`render_report_markdown_pdf_bytes(...)`. It requires an explicit
`--output PATH`, refuses overwrite unless `--force` is provided, and writes
only that one local PDF file. It does not expose an API, add frontend download
behavior, fetch data, access a database, run SQL, call Energi Data Service,
call DMI/weather APIs, train ML models, use LLMs, add scheduler/auth/Azure
behavior, or perform automatic control, dispatch, activation, or operational
functionality.

`report-summary-v0` is read-only decision support only. It must not be used for
automatic control, dispatch, activation, closed-loop workflows, asset
connections, plant/device commands, live control signals, or autonomous
decisions. PDF export should remain manual/local for now. A future controlled
read-only API/export flow can be considered only after separate review and only
if the explicit read-only boundary is preserved.

## Audit Event Foundation

`audit-event-v0` is a pure Python in-memory audit event builder for future
compliance and audit logging of read-only decision-support actions. It is not a
forecasting model, not ML, not an LLM, and not a decision engine. It builds a
deterministic event dictionary from caller-provided fields for events such as
forecast preview requested, current risk viewed, report summary built, report
Markdown rendered, and report PDF exported.

The builder validates explicit event types, actor types, outcomes, timezone
awareness, required resource/action fields, and JSON-compatible metadata. It
rejects secret-like metadata keys and always includes a safety boundary for
read-only decision support, no automatic control, no dispatch, no activation,
no operational energy-system integration, and human review required.

An audit-event database persistence foundation now exists for future explicit
read-only wiring. The Alembic schema defines `audit_events`; the repository
validates `build_audit_event(...)` dictionaries, preserves the full read-only
safety boundary, serializes JSONB fields as parameters, and builds
parameterized `ON CONFLICT (event_id) DO NOTHING` insert SQL.

`POST /api/audit/preview` is a read-only API wrapper for the runtime audit
persistence planner. It returns dry-run audit persistence plans for reviewed
event types only: `current_risk_viewed`, `forecast_preview_requested`,
`report_summary_built`, `report_markdown_rendered`, and
`report_pdf_exported`. It accepts only `DK1`/`DK2`, defaults omitted actor
fields to `actor_type=local_user` and `actor_id=unknown-local-user`, and
returns `dry_run=true`, `database_write_performed=false`,
`requires_database_url=false`, `event`, `persistence_plan`, `event_id`,
`event_type`, `table=audit_events`, `conflict_behavior`, `safety_boundary`,
and `warnings`.

The audit preview API uses `backend/app/audit/runtime_plan.py` dry-run
planners. It does not write to the database, execute SQL, call the audit
writer service, create database connections, read `DATABASE_URL`, add
automatic audit logging, generate reports/PDFs, call EDS/DMI, write files,
modify frontend behavior, or wire audit persistence into risk, forecast,
report, or PDF runtime flows. Unsupported event types and unsupported price
areas outside `DK1`/`DK2` return HTTP 400. Responses contain no raw
`DATABASE_URL`, secrets, tokens, full headers, or full request bodies.
Observed validation recorded the route allowlist update for this read-only
preview POST, focused mutating-route check passing with
`1 passed, 1 warning`, focused API tests passing with
`16 passed, 1 warning`, the full backend suite passing with
`409 passed, 1 warning`, `py_compile` passing, `git diff --check` passing,
and no live DB writes.

This foundation does not automatically persist audit logs, write files, expose
runtime audit writes, write files, add frontend UI, connect report/PDF flows,
run scheduled logging, connect to auth/Entra, call Energi Data Service, call
DMI/weather APIs, use ML, use LLMs, add Azure infrastructure, add auth, add
secrets, or perform operational behavior. It must not be used for automatic
control, dispatch, activation, closed-loop workflows, asset connections,
plant/device commands, live control signals, or autonomous decisions.

`scripts/audit_event_preview.py` is a manual synthetic local JSON preview for
`audit-event-v0`. It imports `build_audit_event(...)`, uses fixed
`occurred_at_utc=2026-01-01T00:00:00Z`, uses
`actor_type=local_developer`, defaults `actor_id` to `local-dev`, uses
`outcome=success`, sets `decision_support_only=true`, and prints compact JSON
by default or indented JSON with `--pretty`.

```bash
python3 scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py --pretty
python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty
```

Supported event types are `forecast_preview_requested`,
`current_risk_viewed`, `report_summary_built`,
`report_markdown_rendered`, `report_pdf_exported`, and `all`. The default
`all` prints one object with an `events` array; a single event type prints one
object with an `event` field. The preview metadata is safe synthetic metadata
only, such as `price_area=DK1`, relevant
`report_version=report-summary-v0`, relevant `output_format`, and
`synthetic_preview_only=true`.

The audit preview is not model training, not forecasting, not an LLM workflow,
not persistence execution, and not an operational integration. It does not
write files, access a database, expose an API, use frontend code, call
EDS/DMI, use ML, use LLMs, or perform automatic control, dispatch, or
activation. Future audit work can wire explicit read-only flows to the audit
persistence foundation only in a separate reviewed module.

Observed manual audit-event preview validation:

| Command | Observed result |
| --- | --- |
| `python3 -m py_compile scripts/audit_event_preview.py` | Passed. |
| `python3 scripts/audit_event_preview.py` | Printed compact JSON with an `events` array. |
| `python3 scripts/audit_event_preview.py --pretty` | Printed indented JSON. |
| `python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty` | Printed one `report_pdf_exported` event. |
| `python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty` | Printed one `forecast_preview_requested` event. |
| `python3 scripts/audit_event_preview.py --event-type invalid-event` | Failed safely with exit code `2` and a clear argparse invalid-choice validation error. |
| Forbidden-pattern grep on `scripts/audit_event_preview.py` | Returned no matches. |
| `git diff --check` | Passed. |

The preview covered `forecast_preview_requested`, `current_risk_viewed`,
`report_summary_built`, `report_markdown_rendered`, and
`report_pdf_exported`. Generated events included
`event_version=audit-event-v0`, deterministic `audit_evt_...` event ids,
fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, and `local_only=true`.

Every observed event included a `safety_boundary` with
`read_only_decision_support=true`, `no_automatic_control=true`,
`no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Interpretation: the audit preview demonstrates local synthetic event shape
only. It does not persist events, prove database audit logging, connect to
auth or actor identity providers, create operational logs, or provide
production audit persistence. The audit preview API is a reviewed read-only
inspection endpoint only; future runtime audit persistence remains deferred
and requires explicit review.

### Audit DB Persistence Validation

PR #87 added the audit DB persistence foundation after the existing
`audit-event-v0` builder, preview script, and preview-result documentation.
The change added `backend/alembic/versions/0002_audit_events.py` and
`backend/app/audit/repository.py`, plus focused repository tests and docs. It
did not wire persistence into API, frontend, report/PDF flows, automatic
logging, schedulers, auth, ML/LLM behavior, live API calls, live database
writes, or control/dispatch/activation behavior.

The `audit_events` schema uses `event_id` as the primary/idempotency key and
stores event version/type, actor, occurrence time, resource, action, outcome,
`decision_support_only`, JSONB safety boundary, JSONB metadata, and
`created_at_utc`. Indexes cover occurrence time, event type, resource lookup,
and actor lookup. The repository validates events before persistence planning,
uses parameterized INSERT construction, and adds
`ON CONFLICT (event_id) DO NOTHING`. Validation did not execute live database
writes.

Initial validation documented `310 passed, 1 warning` for the backend suite,
successful `py_compile` for audit event and repository modules, expected-only
safety-boundary grep matches for `no_automatic_control`, `no_dispatch`, and
`no_activation`, and a passing `git diff --check`.

GitHub backend-tests initially failed before merge because CI/test route
exposure did not include `/api/risk/current`, `/api/risk/preview`, and
`/api/forecast/preview` under newer FastAPI/Starlette behavior. The observed
failures were
`tests/test_api_energy.py::test_app_exposes_no_mutating_write_methods` and
`tests/test_api_risk.py::test_app_import_without_database_url_still_exposes_current_risk_route`.
The fix updated `backend/app/main.py` with a small route-registration helper
so `app.routes` exposes concrete paths in the test environment while keeping
`DATABASE_URL` validation request-time only. Endpoint logic was not changed.

Post-fix validation documented focused route tests passing with
`2 passed, 1 warning`, the full backend suite passing with
`310 passed, 1 warning`, `git diff --check` passing, no `.pyc`, virtualenv,
cache, or generated files in the PR diff, and green GitHub backend-tests
before merge. PR #87 was merged only after backend-tests were green. The final
merged files were the migration, audit repository, `backend/app/main.py`,
`backend/tests/test_audit_event_repository.py`, `README.md`,
`docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`,
`docs/BACKTEST_RESULTS.md`, and `CHANGELOG.md`.

Interpretation: audit DB persistence is schema/repository readiness only. It
does not prove production audit persistence, identify real users through Entra
ID, or create runtime audit logs. Future reviewed modules may add controlled
repository execution with an explicit database connection and tests, but
automatic audit logging and frontend/report-download persistence wiring remain
out of scope until explicit review.

`scripts/audit_persistence_preview.py` is now available as that manual local
dry-run persistence preview. It builds one synthetic `audit-event-v0`, calls
the repository SQL builder, and prints the dry-run event plus `audit_events`
SQL plan. It does not connect to a database, require `DATABASE_URL`, execute
SQL, persist events, expose an API, use frontend code, write files, generate
PDFs, call EDS/DMI, use ML, use LLMs, add auth, add secrets, schedule work, or
add automatic audit logging. It is read-only decision-support audit
persistence preview only; future controlled execution would require explicit
database connection handling and tests.

Observed audit persistence dry-run validation:

| Command/check | Observed result |
| --- | --- |
| `python3 -m py_compile scripts/audit_persistence_preview.py` | Passed. |
| `python3 scripts/audit_persistence_preview.py` | Printed compact JSON. |
| `python3 scripts/audit_persistence_preview.py --pretty` | Printed indented JSON. |
| `python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty` | Passed as a dry-run preview. |
| `python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty` | Passed as a dry-run preview. |
| `python3 scripts/audit_persistence_preview.py --event-type invalid-event` | Failed safely with exit code `2` and argparse invalid-choice output. |
| Forbidden-pattern grep on `scripts/audit_persistence_preview.py` | Returned no matches. |
| `git diff --check` | Passed. |

Observed output included `dry_run=true`,
`database_write_performed=false`, `requires_database_url=false`, `event`, and
`persistence_plan`. The event had `event_version=audit-event-v0`, a
deterministic `audit_evt_...` id, fixed
`occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, `local_only=true`, and the full read-only human
review safety boundary. The persistence plan showed the `audit_events` target,
SQL/SQL preview, parameter keys/params, `event_id` idempotency key, and
`ON CONFLICT (event_id) DO NOTHING`.

Interpretation: the preview demonstrates persistence planning only. It is not
model validation, forecasting validation, live DB persistence, SQL execution,
API/frontend/report/PDF integration, automatic audit logging, or operational
functionality. Future local write testing must be separate and reviewed.

`scripts/audit_db_write_smoke.py` is a manual local-only audit DB write smoke
script for one deterministic synthetic `audit-event-v0`. It is not a model,
forecasting engine, LLM, decision engine, production audit logger, or runtime
integration. It defaults to dry-run and requires both `--execute` and an
explicit local `--database-url` before it opens a database connection.

```bash
python3 scripts/audit_db_write_smoke.py --pretty
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty
```

The script accepts local database URLs such as
`postgresql://localhost/flexsignal_ai`,
`postgresql://127.0.0.1/flexsignal_ai`, and
`postgresql:///flexsignal_ai`, refuses obvious remote/cloud URLs by default,
and never prints the raw database URL. When explicitly executed, it writes
only to `audit_events`, runs the same parameterized idempotent insert twice,
commits, and optionally verifies the row by `event_id`.

This smoke script does not write energy, forecast, or report data; expose an
API; add frontend code; add automatic audit logging; integrate with report,
PDF, API, or frontend flows; schedule work; use Azure infrastructure; add auth
or secrets; call EDS/DMI; use ML; use LLMs; or add control, dispatch,
activation, or operational functionality.

Observed manual validation results for `audit_db_write_smoke.py`:

| Command/check | Observed result |
| --- | --- |
| `python3 -m py_compile scripts/audit_db_write_smoke.py backend/tests/test_audit_db_write_smoke.py` | Passed. |
| `python -m pytest tests/test_audit_db_write_smoke.py -q` | Focused smoke tests passed: `7 passed`. |
| `python -m pytest` | Full backend suite passed: `317 passed, 1 warning`. |
| `python3 scripts/audit_db_write_smoke.py` | Default dry-run passed. |
| `python3 scripts/audit_db_write_smoke.py --pretty` | Pretty dry-run passed. |
| `python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty` | Event-specific dry-run passed. |
| `python3 scripts/audit_db_write_smoke.py --execute` | Failed safely with exit code `2` because an explicit `--database-url` is required. |
| `python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://remote.example.com/flexsignal_ai` | Failed safely with exit code `2` because remote/cloud-style database URLs are rejected by default. |
| Forbidden-pattern grep on script and test | Returned no matches. |
| `git diff --check` | Passed. |

No live DB writes were performed during those earlier guardrail checks. Output
behavior includes `dry_run`, `execute_requested`,
`database_write_performed`, `verify_read_performed`, `local_database_only`,
`event_id`, `event_type`, `table: audit_events`, `inserted_attempts`,
`conflict_behavior`, `safety_boundary`, and `warnings`. The raw
`DATABASE_URL` is not printed, and the `event_id` is deterministic.

The preserved safety boundary is `read_only_decision_support=true`,
`no_automatic_control=true`, `no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Later manual local Postgres validation documented the first actual
`audit_events` write:

```bash
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
```

Alembic used `PostgresqlImpl`, assumed transactional DDL, migrated
`0001_initial_schema` to `0002_audit_events`, added the audit-event-v0
persistence foundation, and succeeded.

The first write smoke used
`event_id=audit_evt_f8ea1513efa7fa0067b0ca04`,
`event_type=report_pdf_exported`, `dry_run=false`,
`execute_requested=true`, `database_write_performed=true`,
`local_database_only=true`, `table=audit_events`,
`inserted_attempts=2`, `rowcount_first_insert=1`,
`rowcount_second_insert=0`,
`conflict_behavior=ON CONFLICT (event_id) DO NOTHING`,
`verify_read_performed=true`, `warnings=[]`, and returned `verified_row` by
`event_id`. The second run used the same event id and event type, returned
`rowcount_first_insert=0` and `rowcount_second_insert=0`, and verified the row
again, confirming idempotency across repeated script executions.

The verified row included `event_version=audit-event-v0`,
`action=preview_report_pdf_export`, `actor_type=local_developer`,
`actor_id=local-dev`, `outcome=success`, `decision_support_only=true`,
`resource_type=report_pdf`,
`resource_id=report-summary-v0:DK1:synthetic-pdf`, and metadata
`local_only=true`, `output_format=pdf`, `price_area=DK1`,
`report_version=report-summary-v0`, and `synthetic_preview_only=true`.
`occurred_at_utc` was returned as `2026-01-01T01:00:00+01:00`, interpreted as
database/session timezone rendering of the stored `timestamptz` instant. This
is not a blocker; future code may normalize read-back display to UTC if
needed.

Interpretation: the local audit DB write is manually verified for the
repository insert path, idempotency via
`ON CONFLICT (event_id) DO NOTHING`, and verify-read by `event_id`. This does
not affect model quality, forecast performance, or production readiness. It
does not enable production audit persistence, automatic audit logging, API,
frontend, report/PDF integration, scheduler, Azure infrastructure, auth/Entra
integration, live EDS/DMI calls, ML/LLM use, control, dispatch, activation, or
operational functionality. Future work may add a read-only API-side audit
logging design or manual API audit dry-run, but automatic audit persistence
must not be wired into runtime flows yet.

`scripts/report_summary_preview.py` is a manual synthetic local JSON preview
for `report-summary-v0`. It uses fixed `generated_at_utc` output and only
in-script caller-provided current-risk and forecast-window data for
`standard`, `high-risk`, `missing-current-risk`, and `missing-forecast`
scenarios. It calls `build_report_summary(...)` and prints compact JSON by
default or indented JSON with `--pretty`.

```bash
python3 scripts/report_summary_preview.py
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

The report-summary preview script does not generate PDF files, fetch data,
access a database, run SQL, expose a FastAPI endpoint, run frontend code, call
Energi Data Service, call DMI/weather APIs, train ML models, use LLMs, add
scheduler/auth/Azure behavior, or perform automatic control, dispatch,
activation, or operational functionality.

### Report Summary Preview API Smoke

Observed manual API smoke called:

```bash
curl -X POST http://127.0.0.1:8000/api/report/summary/preview \
  -H 'Content-Type: application/json' \
  -d '{}'
```

The HTTP response returned valid JSON with
`report_preview_generated=true`, `pdf_generated=false`,
`file_written=false`, `database_query_executed=false`,
`database_write_performed=false`, `requires_database_url=false`, and
`decision_support_only=true`. The response included `report_summary`,
recommendations, explanation, and `safety_boundary`.

Observed `report_summary` output used `report_version=report-summary-v0`,
`price_area=DK1`, and `generated_at_utc=2026-01-01T00:00:00Z`.
`current_risk_summary` was available with `risk_level=medium`.
`forecast_window_summary` was available with
`model_version=rule-engine-v0+forecast-window-v0`, and forecast windows were
present for `0-24h`, `24-48h`, and `48-72h`.

Interpretation: this API smoke confirms the preview endpoint can return the
deterministic report-summary payload without `DATABASE_URL`. It does not
change `rule-engine-v0`, train or validate a model, generate a PDF, write a
file, query or write a database, execute SQL, call live EDS/DMI APIs, use
ML/LLM behavior, or perform control, dispatch, or activation. Human review
remains required.

`scripts/report_markdown_preview.py` is a manual synthetic local Markdown
preview for `report-summary-v0`. It uses fixed `generated_at_utc` output and
only in-script caller-provided current-risk and forecast-window data for
`standard`, `high-risk`, `missing-current-risk`, and `missing-forecast`
scenarios. It calls `build_report_summary(...)`, calls
`render_report_summary_markdown(...)`, and prints Markdown to stdout.

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

The Markdown preview output includes a title, report metadata, current-risk
summary, forecast-window summary, key findings, recommended human actions,
safety notes, limitations, and source notes. Missing current-risk or forecast
inputs render as unavailable sections while preserving the available summary.

The Markdown preview script does not generate PDF files, write files, fetch
data, access a database, run SQL, expose a FastAPI endpoint, run frontend
code, call Energi Data Service, call DMI/weather APIs, train ML models, use
LLMs, add scheduler/auth/Azure behavior, or perform automatic control,
dispatch, activation, or operational functionality. It uses
synthetic/caller-provided data only, is read-only decision support only, and
requires human review before planning.

### Report Summary Preview Results

The manual synthetic report-summary preview was observed with:

```bash
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

All outputs used `generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`. Safety notes were present and explicitly stated
that the report must not be used for automatic control, dispatch, or
activation. Limitations were present and documented no production forecast
validation, no outcome labels, no DMI/weather data yet, no ML training in the
report builder, no LLM use in the report builder, caller-provided data only,
no database read/write, and no live API calls.

Observed scenarios:

| Scenario | Price area | Current risk | Forecast windows | Finding |
| --- | --- | --- | ---: | --- |
| `standard` | DK1 | `status=available`, `risk_level=medium`, `risk_score=45` | 3 | Key findings reported medium current risk and no high-risk forecast window; recommended actions required human review and prohibited automatic control, dispatch, or activation. |
| `high-risk` | DK2 | `status=available`, `risk_level=high`, `risk_score=75` | 3 | Key findings reported high current risk and a high-risk `24-48h` forecast window with `max_risk_score=80`; actions required escalation for human review. |
| `missing-current-risk` | DK1 | `status=unavailable` | 3 | The report stayed safe, kept the forecast summary available, and added `missing or incomplete current risk input` to limitations. |
| `missing-forecast` | DK1 | `status=available`, `risk_level=medium`, `risk_score=45` | 0 | The report stayed safe, marked the forecast summary unavailable, and added `missing or incomplete forecast input` to limitations. |

Interpretation: the report-summary preview creates deterministic payloads from
synthetic/caller-provided current-risk and forecast-window inputs. It does not
generate PDF files yet, fetch data, read or write a database, expose an API,
use frontend code, use ML, or use LLMs. Markdown report rendering now exists
as a pure string renderer over the report dictionary, and the Markdown preview
script exercises that renderer locally without writing files. PDF export should
follow after Markdown/report rendering is stable.

### Report Markdown Preview Results

The manual synthetic report Markdown preview was observed with:

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

All outputs used `generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`. The rendered Markdown included title, report
metadata, current-risk summary, forecast-window summary, key findings,
recommended human actions, safety notes, limitations, and source notes.

Observed scenarios:

| Scenario | Price area | Current risk | Forecast windows | Markdown result |
| --- | --- | --- | ---: | --- |
| `standard` | DK1 | `status=available`, `risk_level=medium`, `risk_score=45` | 3 | Markdown rendered medium current risk, no high-risk forecast-window finding, safety notes, limitations, and source notes. |
| `high-risk` | DK2 | `status=available`, `risk_level=high`, `risk_score=75` | 3 | Markdown rendered high current risk, a high-risk `24-48h` forecast window with `max_risk_score=80`, human-review escalation actions, and safety notes prohibiting automatic control, dispatch, and activation. |
| `missing-current-risk` | DK1 | `status=unavailable` | 3 | Markdown rendered the current-risk summary as unavailable, kept the forecast-window summary available, included the `missing or incomplete current risk input` limitation, and did not crash. |
| `missing-forecast` | DK1 | `status=available`, `risk_level=medium`, `risk_score=45` | 0 | Markdown rendered the forecast-window summary as unavailable, kept the current-risk summary available, included the `missing or incomplete forecast input` limitation, and did not crash. |

Interpretation: the Markdown preview uses synthetic/caller-provided data only.
It does not generate PDF files, write files, fetch data, read or write a
database, expose an API, use frontend code, use ML, or use LLMs. It is
read-only decision support only and must not be used for automatic control,
dispatch, or activation. PDF export v0 now uses the stable report-summary and
Markdown rendering path, and remains manual, local, and read-only only.

### Report PDF Smoke-Test Results

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

`scripts/forecast_window_preview.py` is a manual synthetic local preview for
`forecast-window-v0`. It uses fixed `generated_at_utc` output and only
in-script caller-provided rows for `balanced`, `high-risk`, and `empty-window`
scenarios. It calls `build_forecast_window_forecast(...)` and prints compact
JSON by default or indented JSON with `--pretty`.

The preview script does not require `DATABASE_URL`, read or write a database,
run SQL, fetch Energi Data Service data, call DMI/weather APIs, expose a FastAPI
endpoint, run frontend code, create a scheduler, use Azure, add secrets, add
auth, train ML models, use LLMs, or perform control, dispatch, activation, or
operational functionality.

### Forecast Window Preview Results

The synthetic preview script was run with:

```bash
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

All observed outputs used `generated_at_utc=2026-01-01T00:00:00Z`,
`model_version=rule-engine-v0+forecast-window-v0`, and
`decision_support_only=true`.

Balanced synthetic rows for `price_area=DK1` returned the three expected
windows: `0-24h` had `row_count=2`, `risk_level=medium`, and
`max_risk_score=45`; `24-48h` had `row_count=2`, `risk_level=low`, and
`max_risk_score=30`; `48-72h` had `row_count=2`, `risk_level=medium`, and
`max_risk_score=35`. Top reason codes were deterministic and included
`EXCHANGE_NET_NOT_USED_V0` in all three windows, with price and renewable-share
codes reflecting the in-script rows.

The high-risk synthetic DK2 run demonstrated max-risk aggregation: the
`24-48h` window became `high` risk with `max_risk_score=75`. Its top reason
codes included `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`.

The empty-window synthetic run demonstrated insufficient caller-provided data
handling: the `24-48h` window had `row_count=0`, `risk_level=unknown`,
`average_risk_score=null`, `max_risk_score=null`, and no top reason codes.

These results are local synthetic preview results only. They are deterministic
aggregation over caller-provided rows, not ML, not DMI/weather based yet, not
production forecast validation, and not evidence of predictive accuracy. The
script does not fetch data, read or write a database, expose an API, run
backend or frontend servers, schedule jobs, use Azure, use ML or LLMs, or
perform control, dispatch, activation, closed-loop, or operational behavior.

### Forecast Preview API Smoke Test Results

Manual smoke testing of `POST /api/forecast/preview` was documented with the
backend started without `DATABASE_URL`. This confirms that caller-provided
forecast rows can be summarized without database access. No frontend,
ingestion, database writes, SQL, live Energi Data Service calls, DMI/weather
calls, scheduler, Azure infrastructure, auth, secrets, ML training, LLM use,
control, dispatch, activation, or operational functionality was used.

Valid DK1 request observations:

- HTTP `200`
- `price_area`: `DK1`
- `generated_at_utc`: `2026-01-01T00:00:00Z`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- windows returned: `3`
- `0-24h`: `row_count=1`, `risk_level=low`, `max_risk_score=30`,
  `average_risk_score=30.0`; top reason codes included `MODERATE_PRICE` and
  `MODERATE_RENEWABLE_SHARE`
- `24-48h`: `row_count=1`, `risk_level=high`, `max_risk_score=75`,
  `average_risk_score=75.0`; top reason codes included
  `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`
- `48-72h`: `row_count=0`, `risk_level=unknown`, `max_risk_score=null`,
  `average_risk_score=null`, and `average_confidence_score=0.0`

High-risk DK2 request observations:

- HTTP `200`
- `price_area`: `DK2`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- `24-48h`: `row_count=1`, `risk_level=high`, `max_risk_score=75`,
  `average_risk_score=75.0`; top reason codes included
  `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`
- `0-24h` and `48-72h` were `unknown` because `row_count=0`

Validation observations:

- `price_area=SE3` returned a validation error indicating that input should be
  `DK1` or `DK2`.
- Timezone-naive `generated_at_utc` returned a validation error indicating that
  `generated_at_utc` must be timezone-aware.

Interpretation: the API returns deterministic forecast-window summaries for
caller-provided rows, demonstrates max-risk aggregation, handles empty windows
as `unknown`, and validates supported price areas plus timezone-aware
`generated_at_utc`. These observations do not establish predictive accuracy,
statistical calibration, production readiness, or operational fitness.

### Frontend Forecast Preview Smoke Test After CORS Fix

The frontend Forecast preview card was smoke-tested manually from `main` after
the local CORS preflight fix was merged. The backend was started without
`DATABASE_URL`, and the frontend was started locally. The test exercised only
the Forecast preview card; spot prices, power balance, and current surplus risk
cards were not used. No ingestion, database access, SQL, database writes, live
Energi Data Service calls, DMI/weather calls, scheduler, Azure infrastructure,
auth, secrets, ML training, LLM use, automatic control, dispatch, activation,
or operational functionality was run or added.

The frontend card was visible along with the read-only badge and the
synthetic/caller-provided preview warning. No forecast data appeared before
clicking the manual "Load forecast preview" button. After the button click,
the card displayed `model_version=rule-engine-v0+forecast-window-v0`,
`decision_support_only=true`, `generated_at_utc=2026-01-01T00:00:00Z`, and
the three expected windows: `0-24h`, `24-48h`, and `48-72h`.

Observed DK1 frontend windows:

| Window | Row count | Risk level | Max risk score | Average risk score | Top reason codes observed |
| --- | ---: | --- | ---: | ---: | --- |
| `0-24h` | 1 | low | 30 | 30 | `EXCHANGE_NET_NOT_USED_V0`, `MODERATE_PRICE`, `MODERATE_RENEWABLE_SHARE` |
| `24-48h` | 1 | high | 75 | 75 | `EXCHANGE_NET_NOT_USED_V0`, `HIGH_RENEWABLE_SHARE`, `NEGATIVE_PRICE`; recommended human action required human review |
| `48-72h` | 1 | low | 10 | 10 | `ELEVATED_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0`, `NORMAL_PRICE` |

After switching the selected price area to `DK2`, the manual preview request
returned forecast-window data again. The card displayed the same three forecast
windows and decision-support-only fields without frontend error, confirming
that the selected price area can be used by the frontend helper for this
preview flow.

The earlier browser failure was caused by `OPTIONS` preflight returning `400`.
After the CORS fix, the frontend successfully loaded forecast preview data from
`POST /api/forecast/preview`, which practically confirms the local CORS
preflight path for the Forecast preview card.

These observations confirm local frontend behavior only. The card manually
calls `POST /api/forecast/preview`, displays deterministic forecast-window
summaries over synthetic/caller-provided demo rows, does not fetch EDS/DMI data
from the browser, does not read or write a database, and does not auto-load or
poll. This is not production forecast validation, not ML, not LLM based, and
not DMI/weather based yet. It remains read-only decision support for human
review and must not be used for automatic control, dispatch, activation,
closed-loop workflows, asset connections, plant/device commands, or live
control signals.

## Limitations

- This is a simple baseline for traceable decision support, not a validated
  forecasting system.
- Missing consumption data limits interpretation of actual surplus conditions;
  `consumption_mw` is recorded as context but does not drive v0 scoring.
- `exchange_net_mw` is validated but does not drive v0 scoring because exchange
  sign conventions can be ambiguous across source systems and require explicit
  validation before use.
- The model does not account for weather forecasts, outages, grid constraints,
  curtailment, balancing markets, or operational conditions.
- Confidence scores are deterministic data-completeness indicators, not
  statistically calibrated probabilities.
- The current validated local dataset is tiny and no full historical backtest
  with outcome labels has been run.
- A deterministic 24-72 hour caller-provided forecast-window aggregation
  foundation exists, but it is not production forecast validation and does not
  fetch, persist, or ingest forecast data.
- No DMI/weather ingestion exists. Manual synthetic JSON, Markdown, and PDF
  preview scripts exist for `report-summary-v0`, but no production report
  export, API export, frontend download, auth, Azure deployment, scheduled
  ingestion job, or production database exists yet.
- No monitoring or observability setup exists yet.
- No human approval workflow exists beyond documentation and disclaimers.

Recommended next MVP step: keep `rule-engine-v0` and `forecast-window-v0` as
explainable read-only baselines while adding explicit validation and
caller-provided/local data composition before any production data path. Do not
use an LLM as the forecast engine.

## Human Oversight and Safety

Outputs require human review. `rule-engine-v0` must not perform or trigger
automatic control, dispatch, activation, closed-loop workflows, asset
connections, plant/device commands, or live control signals.

The preview API is not autonomous and cannot trigger control actions. It returns
the same read-only decision-support output shape as the pure rule engine.

The current-risk API is also not autonomous. It reads existing local data only
and returns read-only decision support plus metadata indicating whether the
latest `spot_prices` and `power_balance` rows were found.

## Local API Smoke Test Results

Manual local API smoke testing was documented for `POST /api/risk/preview` with
the backend started manually:

```bash
python -m uvicorn app.main:app --reload
```

A valid caller-provided JSON payload used `price_area` `DK1`,
`timestamp_utc` `2026-06-09T21:45:00+02:00`, `price_dkk_per_mwh` `-10`,
`production_mw` `1000`, `wind_onshore_mw` `500`, `wind_offshore_mw` `350`,
`solar_mw` `50`, and `consumption_mw` `900`.

Observed output:

- `risk_level`: `high`
- `risk_score`: `75`
- `confidence_score`: `1.0`
- `reason_codes` included `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`

An invalid input smoke test using `price_area` `SE3` returned a validation
error. Only `DK1` and `DK2` are accepted.

The smoke test used caller-provided JSON only. No database connection was used,
no database writes were performed, no live Energi Data Service polling was
performed, no LLM or ML model was used, and no automatic control, dispatch,
activation, or operational functionality exists.

Manual local API smoke testing was also documented for
`GET /api/risk/current?price_area=DK1` with the backend started manually:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

Observed output:

- `risk_level`: `medium`
- `risk_score`: `35`
- `confidence_score`: `1.0`
- `reason_codes` included `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`
- `metadata.source_tables_used` included `spot_prices` and `power_balance`
- `metadata.spot_price_row_found`: `true`
- `metadata.power_balance_row_found`: `true`

An invalid input smoke test using
`GET /api/risk/current?price_area=SE3` returned a validation error. Only `DK1`
and `DK2` are accepted.

The current-risk smoke test read from local PostgreSQL only through the existing
read-only query path. No database writes were performed, no live Energi Data
Service polling was performed, no startup migrations were run, no Azure
resources were used, no production database was used, no LLM or ML model was
used, and no automatic control, dispatch, activation, or operational
functionality exists.

## Local Frontend Current-Risk Smoke Test Results

Manual local frontend current-risk smoke testing was documented with the backend
started manually:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

The frontend was started manually:

```bash
cd frontend
npm install
npm run dev
```

The browser opened `http://localhost:3000`. The manual read-only UI actions
were selecting DK1, clicking Load spot prices, clicking Load power balance, and
clicking Load current risk.

Observed frontend output:

- Spot prices displayed 3 rows.
- Power balance displayed 3 rows.
- Current surplus risk displayed `risk_level` `medium`.
- `risk_score` was `35`.
- `confidence_score` was `1`.
- `reason_codes` included `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`.
- `model_version` was `rule-engine-v0`.
- `decision_support_only` was `true`.
- `metadata.source_tables_used` showed `spot_prices` and `power_balance`.
- `metadata.spot_price_row_found` was `true`.
- `metadata.power_balance_row_found` was `true`.
- No Failed to fetch error appeared.

The frontend used only the backend API helper and did not call Energi Data
Service directly. No polling or automatic refresh was used, no database writes
were performed, no live EDS polling was performed, no startup migrations were
run, no Azure resources were used, no production database was used, no LLM or
ML model was used, and no automatic control, dispatch, activation, or
operational functionality exists.

## Audit Writer Service Foundation

`backend/app/audit/writer.py` is a backend service foundation for explicitly
writing validated `audit-event-v0` records. It is not a model, not a
forecasting component, not an LLM decision component, and not operational
automation. The writer requires an explicit database connection from its
caller, uses the existing audit repository parameterized insert SQL builder,
and validates that `decision_support_only` and the full human-review safety
boundary are true before executing SQL.

The writer does not create database connections, does not read `DATABASE_URL`,
does not expose an endpoint, and is not wired to API, frontend, report, PDF, or
automatic audit logging flows. Its unit tests use fake connections only, so the
test suite performs no live audit database writes.

The public function is `write_audit_event(conn, event)`;
`execute_audit_event_insert` is an alias. The writer uses the existing audit
repository insert SQL builder and validates `audit-event-v0`,
`decision_support_only=true`, and the complete safety boundary before SQL is
executed:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Invalid events raise `ValueError` and execute no SQL. Valid events return
`event_id`, `event_type`, `table`, `database_write_performed`, `rowcount`,
`conflict_behavior`, `safety_boundary_preserved`, and `warnings`.

Observed audit writer validation recorded focused tests passing with
`14 passed`, the full backend suite passing with `331 passed, 1 warning`,
`py_compile` passing for the writer and tests, safety-boundary grep matching
only expected strings and negative/static assertions, and `git diff --check`
passing. The writer tests used fake connection/cursor objects only and
performed no live database writes.

Interpretation: this is a backend audit foundation, not model validation,
forecasting validation, runtime audit persistence, automatic audit logging,
API/frontend/report/PDF integration, scheduler, Azure infrastructure,
auth/Entra integration, live EDS/DMI behavior, ML/LLM behavior, control,
dispatch, activation, or operational functionality. Runtime integration
remains intentionally deferred.

## Runtime Audit Event Factory

`backend/app/audit/runtime_events.py` standardizes future read-only runtime
audit event mapping for `audit-event-v0`. It is not a forecasting model, not an
LLM workflow, not a decision engine, and not operational automation.

The factory only constructs audit dictionaries through `build_audit_event(...)`
for current-risk views, forecast-preview requests, report-summary builds,
report Markdown rendering, and report PDF export previews. It does not write to
the database, does not call the audit writer service, does not expose an API,
does not modify frontend behavior, and is not integrated with report, PDF, API,
scheduler, auth, Azure, EDS, DMI, control, dispatch, activation, or operational
flows. Runtime wiring remains deferred.

`backend/app/audit/runtime_plan.py` adds the next pure backend dry-run layer:
runtime audit persistence planning. The planner calls the runtime event
factory, then calls the repository INSERT SQL builder, and returns a dictionary
only. It does not write to the database, call the audit writer service, create
database connections, read `DATABASE_URL`, execute SQL, modify frontend
behavior, or integrate with report/PDF/frontend flows.

Implemented planner functions are
`build_current_risk_viewed_audit_plan`,
`build_forecast_preview_requested_audit_plan`,
`build_report_summary_built_audit_plan`,
`build_report_markdown_rendered_audit_plan`, and
`build_report_pdf_exported_audit_plan`.

Planner outputs include `dry_run=true`,
`database_write_performed=false`, `requires_database_url=false`, the event, a
repository-built `persistence_plan`, `event_id`, `event_type`,
`table=audit_events`, conflict behavior
`ON CONFLICT (event_id) DO NOTHING`, the preserved safety boundary, and
warnings. The persistence plan includes SQL preview, params/parameter keys,
and the `event_id` idempotency key. SQL and parameters are previewed only; no
SQL is executed. It supports the reviewed API audit dry-run preview documented
above; runtime persistence and automatic audit logging remain deferred.

Implemented factory functions:

| Function | Event type | Action | Resource type |
| --- | --- | --- | --- |
| `build_current_risk_viewed_event` | `current_risk_viewed` | `view_current_risk` | `risk_snapshot` |
| `build_forecast_preview_requested_event` | `forecast_preview_requested` | `preview_forecast` | `forecast_preview` |
| `build_report_summary_built_event` | `report_summary_built` | `build_report_summary` | `report_summary` |
| `build_report_markdown_rendered_event` | `report_markdown_rendered` | `render_report_markdown` | `report_markdown` |
| `build_report_pdf_exported_event` | `report_pdf_exported` | `preview_report_pdf_export` | `report_pdf` |

Resource ids include `price_area`; forecast-preview resource ids include
`forecast-window-v0`; report summary, Markdown, and PDF resource ids include
`report-summary-v0`.

Metadata is minimal and safe. It may include `price_area`, optional
`request_id`, optional `source`, `forecast_window_version` where relevant,
`report_version` where relevant, `output_format` where relevant, optional
forecast `model_version`, and
`runtime_factory_version=audit-runtime-event-factory-v0`. It must not include
raw `DATABASE_URL`, secrets, tokens, raw user claims, full request headers, or
full request bodies.

Every generated event preserves `event_version=audit-event-v0`,
`decision_support_only=true`, and the full human-review safety boundary:
`read_only_decision_support=true`, `no_automatic_control=true`,
`no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Observed validation documented focused runtime event tests passing with
`30 passed`, the full backend suite passing with `361 passed, 1 warning`,
`py_compile` passing for `runtime_events` and tests, forbidden-pattern grep
returning no matches, and `git diff --check` passing. These were pure unit
tests only and did not perform live database writes.

Observed runtime dry-run planner validation documented focused runtime plan
tests passing with `32 passed`, the full backend suite passing with
`393 passed, 1 warning`, `py_compile` passing for `runtime_plan` and tests,
forbidden-pattern grep matching only safety/negative assertions in tests, and
`git diff --check` passing. Planner tests were pure unit tests only and
performed no live database writes.

Interpretation: the runtime factory does not affect model quality, forecast
performance, statistical calibration, production readiness, or operational
fitness. It standardizes future audit-event construction only. It does not
enable production audit persistence, automatic audit logging, audit writer
calls, database writes, database connections, `DATABASE_URL` handling,
migrations, frontend behavior, report/PDF runtime wiring, schedulers, Azure
infrastructure, auth/Entra integration, live EDS/DMI calls, ML/LLM behavior,
control, dispatch, activation, or operational functionality. The reviewed API
audit dry-run preview remains inspection-only; production DB writes require
explicit review.
