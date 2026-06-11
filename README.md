# FlexSignal AI

FlexSignal AI is an Azure-hosted forecasting and decision-support platform for the Danish electricity system, initially focused on DK1 and DK2.

Version `v0.1` is read-only decision support. The platform may forecast, visualize, explain, and recommend actions for human review, but it must not automatically control electricity consumption or send control signals to assets, plants, devices, or energy infrastructure.

## MVP Scope

- Forecast electricity surplus risk for DK1 and DK2.
- Visualize forecast windows, confidence, and expected economic potential.
- Explain model output and recommendations in clear text.
- Support human decision-making with auditable recommendations.
- Keep LLM usage limited to explanation, reporting, and recommendation text.

## Current MVP Status

FlexSignal AI is ready for a local technical MVP demo. It is not ready for
production, is not a validated commercial forecasting product, and must remain
read-only decision support for human review only.

Working read-only core:

- Local PostgreSQL schema and Alembic baseline exist.
- Manual local Energi Data Service ingestion exists for `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`.
- Local PostgreSQL contains validated DK1 and DK2 sample data from manual
  confirmed local EDS writes after the `limit 50` import.
- Manual batch wrapper validation works with `limit 50`.
- Repeating the same `limit 50` import was idempotent for the tested batch.
- Read-only energy API endpoints exist for `spot_prices` and `power_balance`.
- Frontend dashboard can manually load spot prices, power balance, current
  surplus risk, and a forecast-window preview.
- Frontend dashboard behavior has been manually checked for DK1 and DK2.
- `rule-engine-v0` exists for deterministic surplus-risk scoring.
- `forecast-window-v0` exists as pure backend Python aggregation over
  caller-provided rows for 0-24h, 24-48h, and 48-72h windows.
- `report-summary-v0` exists as pure backend Python data-structure logic over
  caller-provided current-risk and forecast-window outputs.
- `report-summary-v0` Markdown rendering exists as pure backend Python logic
  that converts caller-provided report dictionaries into Markdown strings.
- `POST /api/forecast/preview` exposes `forecast-window-v0` for
  caller-provided JSON rows only.
- `GET /api/risk/current` works for DK1 and DK2 from existing local rows.
- Synthetic backtest preview exists.
- Local DB read-only backtest exists.
- Backtest row pairing uses `nearest_timestamp_v0_1`.

Latest documented local DB backtest results after the confirmed manual EDS
historical batch write:

| Area | Spot prices read | Power balance read | Local DB backtest | Average risk score |
| --- | ---: | ---: | --- | ---: |
| DK1 | 53 rows | 53 rows | low=1, medium=52, high=0 | 34.5283 |
| DK2 | 50 rows | 50 rows | low=42, medium=8, high=0 | 21.8 |

Latest read-only API/UI smoke-test observations:

- DK1 current-risk API returned medium risk with score `35`.
- DK2 current-risk API returned low risk with score `20`.
- Forecast preview API returned deterministic caller-provided DK1/DK2 window
  summaries without `DATABASE_URL`, including high-risk max aggregation,
  empty-window `unknown` handling, DK1/DK2 validation, and timezone-aware
  `generated_at_utc` validation.
- Frontend forecast preview card manually calls `POST /api/forecast/preview`
  with deterministic synthetic/caller-provided demo rows only.
- Frontend manually loaded DK1 and DK2 spot prices, power balance, and current
  surplus risk.
- The read-only badge and disclaimer were visible.
- No automatic loading, polling, control, dispatch, or activation behavior was
  observed.

Still preview / not production:

- Dataset is still small and no full historical backtest has been run.
- No outcome labels or statistical calibration exist.
- The 24-72 hour forecast-window preview API is deterministic aggregation only;
  it uses caller-provided rows, is not ML, is not LLM based, is not DMI/weather
  based yet, does not fetch EDS or DMI data, does not read or write a database,
  and is not production forecast validation. The frontend card is a manual
  preview surface for the same synthetic/caller-provided boundary only.
- The report-summary foundation is a data structure only, with a manual
  synthetic local JSON preview script, a pure Markdown string renderer, and a
  manual synthetic local Markdown preview script. It does not generate PDF
  files yet, write files, fetch data, read or write a database, expose an API,
  use frontend code, use ML, or use LLMs.
- No DMI/weather ingestion exists yet.
- No PDF report export exists yet; the current manual report previews are
  stdout-only JSON and Markdown.
- No auth, Azure deployment, scheduled ingestion jobs, or production database
  exist.
- No monitoring or observability setup exists yet.
- No human approval workflow exists beyond documentation and disclaimers.

Recommended next MVP reporting step: keep the deterministic report-summary
foundation read-only while validating the Markdown preview script, followed
later by PDF export. Do not fetch data in the report builder, do not use an
LLM as the forecast or reporting engine, and do not add control, dispatch, or
activation behavior.

## Report Summary Foundation

`report-summary-v0` builds a deterministic structured report payload from
caller-provided current-risk output and caller-provided `forecast-window-v0`
output. It returns report metadata, current-risk and forecast-window summaries,
model versions, key findings, recommended human actions, safety notes,
limitations, and source notes.

This foundation is backend Python logic only. It does not generate PDF files
yet, fetch data, read or write a database, expose an API, call Energi Data
Service, call DMI/weather APIs, train ML models, use LLMs, add auth, add
scheduler behavior, or add Azure infrastructure. It is read-only decision
support only and must not be used for automatic control, dispatch, activation,
closed-loop workflows, asset connections, plant/device commands, live control
signals, or autonomous decisions.

`render_report_summary_markdown(...)` converts a caller-provided
`report-summary-v0` dictionary into a deterministic Markdown string. It renders
report metadata, current-risk summary, forecast-window summary, key findings,
recommended human actions, safety notes, limitations, and source notes. Missing
current-risk or forecast summaries are rendered as clear unavailable sections
instead of crashing, and optional missing fields use safe fallback text.

The Markdown renderer is pure backend Python formatting logic only. It does
not generate PDF files, write files, fetch data, access a database, expose an
API, use frontend code, use ML, or use LLMs. The rendered Markdown remains
read-only decision support only, requires human review, and must not be used
for automatic control, dispatch, activation, or autonomous decisions.

`scripts/report_summary_preview.py` is a manual synthetic local JSON preview
for `report-summary-v0`. It uses fixed `generated_at_utc=2026-01-01T00:00:00Z`
and in-script caller-provided current-risk and forecast-window data only.

```bash
python3 scripts/report_summary_preview.py
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

The script does not generate PDF files, fetch data, access the database, run
SQL, expose an API, run frontend code, use ML, use LLMs, or perform automatic
control, dispatch, activation, or operational functionality. It is synthetic
read-only decision support only and requires human review before planning.

`scripts/report_markdown_preview.py` is a manual synthetic local Markdown
preview for `report-summary-v0`. It uses the same fixed
`generated_at_utc=2026-01-01T00:00:00Z` boundary and in-script
caller-provided current-risk and forecast-window data only. It calls
`build_report_summary(...)`, then `render_report_summary_markdown(...)`, and
prints Markdown to stdout without writing files.

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

The Markdown preview supports `standard`, `high-risk`,
`missing-current-risk`, and `missing-forecast` scenarios. The output includes
title, report metadata, current-risk summary, forecast-window summary, key
findings, recommended human actions, safety notes, limitations, and source
notes. Missing current-risk or forecast inputs render as unavailable sections
while preserving the remaining available summary.

The Markdown preview uses synthetic/caller-provided data only. It does not
generate PDF files, write files, fetch data, access the database, run SQL,
expose an API, use frontend code, use ML, use LLMs, or perform automatic
control, dispatch, activation, or operational functionality. It is read-only
decision support only, requires human review before planning, and must not be
used for automatic control, dispatch, or activation.

### Report Summary Preview Results

The manual report-summary preview script was run locally with synthetic
caller-provided data only:

```bash
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

All four runs printed the synthetic-only warning, used
`generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`. Safety notes were present in every payload and
explicitly prohibited automatic control, dispatch, and activation. Limitations
were present and included caller-provided data only, no database read/write,
no live API calls, no ML training in the report builder, and no LLM use in the
report builder.

Observed synthetic results:

| Scenario | Command | Price area | Current risk summary | Forecast summary | Key result |
| --- | --- | --- | --- | --- | --- |
| `standard` | `python3 scripts/report_summary_preview.py --pretty` | DK1 | available, medium, score 45 | available, 3 windows | Key findings reported medium current risk, no high-risk forecast window, and caller-provided data only; recommended actions included routine monitoring, review of the medium-risk window, required human review, source-context verification, and no control/dispatch/activation use. |
| `high-risk` | `python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty` | DK2 | available, high, score 75 | available, 3 windows | Current risk was high and the `24-48h` forecast window was high risk with `max_risk_score=80`; key findings mentioned high risk and actions required human review before planning. |
| `missing-current-risk` | `python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty` | DK1 | unavailable | available, 3 windows | The payload remained safe, added the limitation `missing or incomplete current risk input`, and still included the forecast-window summary. |
| `missing-forecast` | `python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty` | DK1 | available, medium, score 45 | unavailable, 0 windows | The payload remained safe, added the limitation `missing or incomplete forecast input`, and still included the current-risk summary. |

Interpretation: `report-summary-v0` preview works locally with synthetic
caller-provided data and creates deterministic report payloads. It does not
generate PDF files yet, fetch data, read or write a database, expose an API,
use the frontend, use ML, or use LLMs. It remains read-only decision support
only and must not be used for automatic control, dispatch, or activation.

### Report Markdown Preview Results

The manual report Markdown preview script was run locally with synthetic
caller-provided data only:

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

All four runs printed the synthetic-only warning to stderr and rendered
Markdown to stdout only. All reports used
`generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`. The rendered Markdown included the title, report
metadata, current-risk summary, forecast-window summary, key findings,
recommended human actions, safety notes, limitations, and source notes.

Observed Markdown results:

| Scenario | Command | Price area | Current risk summary | Forecast summary | Observed Markdown result |
| --- | --- | --- | --- | --- | --- |
| `standard` | `python3 scripts/report_markdown_preview.py` | DK1 | available, medium, score `45` | available, 3 windows | Rendered the report title, metadata, current risk, all three forecast windows, key findings, recommended human actions, safety notes, limitations, and source notes. |
| `high-risk` | `python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk` | DK2 | available, high, score `75` | available, 3 windows | Rendered high current risk, a high-risk `24-48h` forecast finding with `max_risk_score=80`, human-review actions, and safety notes prohibiting automatic control, dispatch, and activation. |
| `missing-current-risk` | `python3 scripts/report_markdown_preview.py --scenario missing-current-risk` | DK1 | unavailable | available, 3 windows | Rendered current risk as unavailable, kept the forecast summary available, included `missing or incomplete current risk input`, and did not crash. |
| `missing-forecast` | `python3 scripts/report_markdown_preview.py --scenario missing-forecast` | DK1 | available, medium, score `45` | unavailable | Rendered the forecast window summary as unavailable, kept the current-risk summary available, included `missing or incomplete forecast input`, and did not crash. |

Interpretation: Markdown preview works locally with synthetic/caller-provided
data, renders `report-summary-v0` to readable Markdown, prints to stdout only,
does not write files, does not generate PDF yet, does not fetch data, does not
read or write a database, does not expose an API, does not use frontend code,
and does not use ML or LLMs. It is read-only decision support only and must
not be used for automatic control, dispatch, or activation.

PDF export v0 can now be built using the stable report-summary and Markdown
rendering path. PDF export should still remain manual, local, and read-only
first.

## Forecast Preview API

`POST /api/forecast/preview` returns deterministic `0-24h`, `24-48h`, and
`48-72h` forecast-window summaries from caller-provided DK1/DK2 rows.

The frontend dashboard includes a manual "Forecast preview" card that calls
`POST /api/forecast/preview` only after the user clicks "Load forecast
preview". It posts deterministic synthetic/caller-provided demo rows with a
timezone-aware `generated_at_utc`, uses only the backend API base URL helper,
does not auto-load or poll, does not call Energi Data Service or DMI/weather
APIs from the browser, and does not read or write a database.

The endpoint is read-only decision support only. It does not fetch Energi Data
Service data, call DMI/weather APIs, read or write a database, persist payloads,
start jobs, train ML models, use LLMs, require secrets, or perform automatic
control, dispatch, or activation. It is not production forecast validation and
must not be used for automatic control, dispatch, activation, closed-loop
workflows, asset connections, plant/device commands, or live control signals.

## Forecast Window Preview Results

The synthetic forecast-window preview script was run locally with:

```bash
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

All three runs used `generated_at_utc=2026-01-01T00:00:00Z`,
`model_version=rule-engine-v0+forecast-window-v0`, and
`decision_support_only=true`.

Observed synthetic results:

| Scenario | Price area | Key result |
| --- | --- | --- |
| `balanced` | DK1 | Returned `0-24h`, `24-48h`, and `48-72h` windows with row counts `2`, `2`, and `2`; risk levels `medium`, `low`, and `medium`; max risk scores `45`, `30`, and `35`. |
| `high-risk` | DK2 | The `24-48h` window became `high` risk with `max_risk_score=75`; reason codes included `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`, demonstrating max-risk aggregation. |
| `empty-window` | DK1 | The `24-48h` window had `row_count=0`, `risk_level=unknown`, `average_risk_score=null`, and `max_risk_score=null`, demonstrating insufficient caller-provided data handling. |

These are synthetic local preview results only. The script aggregates
caller-provided rows deterministically, does not use ML or LLMs, is not
DMI/weather based yet, does not fetch data, does not read or write a database,
and is not production forecast validation. The backend preview API now exposes
the same caller-provided aggregation boundary for JSON requests only. It
remains read-only decision support for human review and must not be used for
automatic control, dispatch, or activation.

### Forecast Preview API Smoke Test Results

`POST /api/forecast/preview` was smoke-tested manually with the backend started
without `DATABASE_URL`. This confirms the endpoint can summarize
caller-provided forecast rows without database access. No frontend was used,
and no ingestion, database writes, SQL, live Energi Data Service calls,
DMI/weather calls, scheduler, Azure infrastructure, auth, secrets, ML
training, LLM use, control, dispatch, activation, or operational functionality
was used or added.

Valid DK1 forecast preview request:

- HTTP `200`
- `price_area`: `DK1`
- `generated_at_utc`: `2026-01-01T00:00:00Z`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- windows returned: `3`

Observed DK1 windows:

| Window | Row count | Risk level | Max risk score | Average risk score | Top reason codes observed |
| --- | ---: | --- | ---: | ---: | --- |
| `0-24h` | 1 | low | 30 | 30.0 | `MODERATE_PRICE`, `MODERATE_RENEWABLE_SHARE` |
| `24-48h` | 1 | high | 75 | 75.0 | `HIGH_RENEWABLE_SHARE`, `NEGATIVE_PRICE` |
| `48-72h` | 0 | unknown | null | null | none; `average_confidence_score=0.0` |

High-risk DK2 forecast preview request:

- HTTP `200`
- `price_area`: `DK2`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- `24-48h` returned `row_count=1`, `risk_level=high`,
  `max_risk_score=75`, `average_risk_score=75.0`, and reason codes including
  `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`.
- `0-24h` and `48-72h` were `unknown` because `row_count=0`.

Validation observations:

- A request using `price_area=SE3` returned a validation error indicating that
  input should be `DK1` or `DK2`.
- A request using timezone-naive `generated_at_utc` returned a validation error
  indicating that `generated_at_utc` must be timezone-aware.

Interpretation: the forecast preview API works for caller-provided rows,
returns deterministic `0-24h`, `24-48h`, and `48-72h` windows, demonstrates
max-risk aggregation, handles empty windows as `unknown`, and validates DK1/DK2
plus timezone-aware `generated_at_utc`. This is read-only decision support for
human review, not production forecast validation.

### Frontend Forecast Preview Smoke Test After CORS Fix

The frontend "Forecast preview" card was smoke-tested manually from `main`
after the local CORS preflight fix was merged. The backend was started without
`DATABASE_URL`, and the frontend was started locally. The test used only the
Forecast preview card; spot prices, power balance, and current surplus risk
cards were not used. No ingestion, database writes, SQL, live Energi Data
Service calls, DMI/weather calls, scheduler, Azure infrastructure, auth,
secrets, ML training, LLM use, automatic control, dispatch, activation, or
operational functionality was run or added.

Observed frontend behavior:

- The Forecast preview card was visible.
- The read-only badge was visible.
- The synthetic/caller-provided preview warning was visible.
- No forecast data appeared before clicking the manual button.
- Clicking "Load forecast preview" triggered the preview request.
- The card displayed `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, `generated_at_utc=2026-01-01T00:00:00Z`, and
  three windows: `0-24h`, `24-48h`, and `48-72h`.

Observed DK1 frontend result:

| Window | Row count | Risk level | Max risk score | Average risk score | Notes |
| --- | ---: | --- | ---: | ---: | --- |
| `0-24h` | 1 | low | 30 | 30 | top reason codes included `EXCHANGE_NET_NOT_USED_V0`, `MODERATE_PRICE`, and `MODERATE_RENEWABLE_SHARE` |
| `24-48h` | 1 | high | 75 | 75 | top reason codes included `EXCHANGE_NET_NOT_USED_V0`, `HIGH_RENEWABLE_SHARE`, and `NEGATIVE_PRICE`; recommended human action required human review |
| `48-72h` | 1 | low | 10 | 10 | top reason codes included `ELEVATED_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0`, and `NORMAL_PRICE` |

Observed DK2 frontend result:

- The selected price area was switched to `DK2`.
- Clicking "Load forecast preview" returned forecast-window data again.
- The card displayed the same three forecast windows and decision-support-only
  fields without frontend error.
- This confirmed that the selected price area can be used by the frontend
  helper for the forecast preview flow.

The previous browser error was caused by `OPTIONS` preflight returning `400`.
After the CORS fix, the frontend successfully loaded forecast preview data from
`POST /api/forecast/preview`, practically confirming the local CORS preflight
path for the Forecast preview card.

Interpretation: the frontend forecast preview card works locally, manually
calls `POST /api/forecast/preview`, displays deterministic `0-24h`, `24-48h`,
and `48-72h` windows, and uses synthetic/caller-provided demo rows only. This
is not production forecast validation, not ML, not LLM based, not DMI/weather
based yet, does not fetch EDS/DMI data from the browser, does not read or write
a database, and does not auto-load or poll. It remains local frontend/backend
smoke-test documentation only, read-only decision support only, and requires
human review.

## Historical Local EDS Import Plan

A documentation-only plan now defines how to expand local EDS-derived samples
for safer read-only backtesting without changing runtime behavior.

Planned local validation scope:

- Datasets: `DayAheadPrices` and `ElectricityProdex5MinRealtime`.
- Price areas: `DK1` and `DK2`.
- Batch size: `limit 50` per dataset and price area is validated for explicit
  manual confirmed local writes. `100` and `500` still require future explicit
  enhancement.
- Validation: row counts by `price_area`, distinct `source_record_id` counts,
  repeated-import idempotency, and local DB read-only backtests for `DK1` and
  `DK2` documenting `risk_level_counts` and `average_risk_score`.

Safety gates:

- Local PostgreSQL only, with `DATABASE_URL` targeting `localhost` or
  `127.0.0.1`.
- Dry-run before confirmed writes.
- Confirmed writes require explicit `--confirm-local-db-write`.
- No production database, Azure database, scheduled job, backend startup
  ingestion, frontend-triggered ingestion, or automatic polling loop.
- No code, backend behavior, frontend behavior, secrets, auth, ML training,
  LLM use, control, dispatch, activation, or operational workflow is added by
  this plan.

This larger local sample would still not be full model validation. Outcome
labels, DMI/weather data, and a 24-72 hour forecast remain absent, and
`rule-engine-v0` remains deterministic and simple.

### Manual EDS Historical Batch Dry-Run

The manual historical batch wrapper dry-run was documented with:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --continue-on-error
```

Observed wrapper result:

- `dry_run=true`, `confirmed_local_write=false`, `local_only=true`, and
  `decision_support_only=true`.
- `limit=50`, `price_areas=DK1, DK2`, and datasets
  `DayAheadPrices`, `ElectricityProdex5MinRealtime`.
- `commands_planned=4`, `commands_succeeded=4`, `commands_failed=0`, and
  `child_exit_codes=[0, 0, 0, 0]`.
- Child dry-runs returned HTTP `200` for `DayAheadPrices` DK1/DK2 and
  `ElectricityProdex5MinRealtime` DK1/DK2, with `50` raw records, `50`
  normalized records, `50` SQL commands, and `committed=false` for each
  combination.

Limit 50 dry-run is validated for all supported DK1/DK2 dataset combinations.
No database writes were committed. This validates command orchestration and the
normalization path only. Confirmed writes still require explicit
`--confirm-local-db-write`, and `100` and `500` still require future explicit
enhancement.

Safety notes: local PostgreSQL dry-run only; no committed writes, production
database, Azure resources, scheduler, live API polling, backend startup ingestion,
frontend-triggered ingestion, automatic polling loop, ML training, LLM use,
automatic control, dispatch, activation, or operational functionality.

### Manual EDS Historical Batch Confirmed Local Write

The manual historical batch wrapper was also run as a confirmed local
PostgreSQL write with explicit confirmation:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --confirm-local-db-write --continue-on-error
```

Before the confirmed batch write, `spot_prices` contained DK1 `13` and DK2
`10` rows, and `power_balance` contained DK1 `13` and DK2 `12` rows. The
confirmed batch summary reported `child_exit_codes=[0, 0, 0, 0]`,
`commands_planned=4`, `commands_succeeded=4`, `commands_failed=0`,
`confirmed_local_write=true`, `dry_run=false`, `limit=50`,
`local_only=true`, and `decision_support_only=true` for `DK1`/`DK2` and
`DayAheadPrices`/`ElectricityProdex5MinRealtime`.

Each child confirmed write returned HTTP `200`, with `50` raw records, `50`
normalized records, `50` SQL commands, and `committed=true`. The target tables
were `spot_prices` for `DayAheadPrices` and `power_balance` for
`ElectricityProdex5MinRealtime`.

After the confirmed batch write, counts were:

| Table | DK1 | DK2 |
| --- | ---: | ---: |
| `spot_prices` | 53 | 50 |
| `power_balance` | 53 | 50 |

The same confirmed batch command was run a second time. The second run again
reported `child_exit_codes=[0, 0, 0, 0]`, `commands_planned=4`,
`commands_succeeded=4`, `commands_failed=0`, `confirmed_local_write=true`,
`dry_run=false`, `limit=50`, and `local_only=true`. Counts remained unchanged,
so no duplicate explosion was observed and the repeated import was idempotent
for the same 50-record batch.

Read-only local DB backtests after the confirmed batch write observed:

| Area | Command limit | Spot prices read | Power balance read | Risk counts | Average risk score |
| --- | ---: | ---: | ---: | --- | ---: |
| DK1 | 100 | 53 | 53 | low=1, medium=52, high=0 | 34.5283 |
| DK2 | 100 | 50 | 50 | low=42, medium=8, high=0 | 21.8 |

Interpretation: the wrapper successfully performed confirmed local writes for
all supported DK1/DK2 dataset combinations, the repeated import was idempotent,
DK1 remained mostly medium risk on the expanded local sample, and DK2 now
includes both low and medium risk. This is stronger technical validation than
the 10-row sample, but still not full model validation because the dataset is
still small and has no outcome labels.

Safety notes: local PostgreSQL only; manual confirmed write only; explicit
`--confirm-local-db-write` was required; no production database, Azure
resources, scheduler, live API polling, backend startup ingestion,
frontend-triggered ingestion, automatic polling loop, ML training, LLM use,
automatic control, dispatch, activation, or operational functionality.

### Read-Only API And Frontend Smoke Test After Limit 50 Local Import

After the manual `limit 50` EDS confirmed local write populated local
PostgreSQL, read-only API and frontend behavior were smoke-tested against the
larger local sample. No ingestion, database writes, live Energi Data Service
polling, tests, or server startup were run by this documentation update.

API commands observed:

```bash
curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK1"
curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK2"
```

Observed API results:

| Area | HTTP | Timestamp | Risk level | Risk score | Confidence | Reason codes | Source rows |
| --- | ---: | --- | --- | ---: | ---: | --- | --- |
| DK1 | 200 | `2026-06-10T17:00:00+02:00` | medium | 35 | 1.0 | `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | `spot_prices=true`, `power_balance=true` |
| DK2 | 200 | `2026-06-10T17:00:00+02:00` | low | 20 | 1.0 | `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | `spot_prices=true`, `power_balance=true` |

Both responses used `model_version=rule-engine-v0`,
`decision_support_only=true`, and `metadata.source_tables_used` containing
`spot_prices` and `power_balance`.

Frontend smoke-test at `http://localhost:3000` observed:

- DK1 manual Load spot prices returned 5 `spot_prices` rows.
- DK1 manual Load power balance returned 5 `power_balance` rows.
- DK1 manual Load current risk showed `risk_level=medium`, `risk_score=35`,
  `confidence_score=1`, and reason codes including `NORMAL_PRICE`,
  `HIGH_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`.
- DK2 manual Load spot prices returned 5 `spot_prices` rows.
- DK2 manual Load power balance returned 5 `power_balance` rows.
- DK2 manual Load current risk showed `risk_level=low`, `risk_score=20`,
  `confidence_score=1`, and reason codes including `NORMAL_PRICE`,
  `MODERATE_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`.
- The read-only badge was visible for both price areas.

Interpretation: the read-only dashboard works for DK1 and DK2 after the
`limit 50` local import, and the frontend still requires manual button clicks.
No automatic loading, polling, dispatch, activation, or control behavior was
observed. The current-risk endpoint still reads from local PostgreSQL and
returns decision-support-only results. This is a local MVP smoke-test, not
production validation.

Safety notes: local PostgreSQL only; read-only API/UI smoke-test only; no
ingestion, database writes, live Energi Data Service polling, Azure resources,
scheduler, backend startup ingestion, frontend-triggered ingestion, automatic
polling loop, ML training, LLM use, automatic control, dispatch, activation, or
operational functionality.

## Not Included in v0.1

- Automatic activation of consumption or flexibility.
- Live control signals to any assets, plants, devices, or energy infrastructure.
- Critical operational system responsibilities.
- LLMs as the primary forecasting engine or sole decision-making component.
- Production infrastructure deployment.
- Production runtime database integration or automatic startup migrations.
- Production-ready frontend workflows.
- Dispatch, activation, closed-loop workflows, or operational energy system
  integration.
- LLM use as a decision engine or autonomous decision-maker.

## Technology Stack

- Frontend: Next.js and TypeScript
- Backend: Python FastAPI
- Database: PostgreSQL with TimescaleDB
- Data jobs: Azure Functions or Azure Container Apps Jobs
- Hosting: Azure App Service or Azure Container Apps
- Secrets: Azure Key Vault
- Logs: Application Insights and Log Analytics
- Auth: Microsoft Entra ID
- AI/LLM: explanation and report generation only

## Database Schema

A documented PostgreSQL/TimescaleDB schema baseline is available in
[`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md). The schema is not yet wired
into the FastAPI application and no database migrations are run in `v0.1`.

## Backend Local Development

The current backend is a minimal FastAPI API plus pure Python decision-support
logic for `v0.1`. It does not include control endpoints, authentication,
runtime forecast data ingestion, forecast-window API exposure, or
infrastructure deployment.

`backend/app/forecast/window_forecast.py` provides the current
`forecast-window-v0` foundation as pure Python logic only. It accepts
caller-provided rows, reuses `rule-engine-v0` scoring, returns
decision-support-only window summaries, and must not be used for automatic
control, dispatch, or activation.

`scripts/forecast_window_preview.py` provides a manual synthetic local preview
of `forecast-window-v0` with fixed `generated_at_utc` output and in-script
caller-provided rows only:

```bash
python3 scripts/forecast_window_preview.py
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

The preview does not require `DATABASE_URL`, read or write a database, run SQL,
fetch Energi Data Service data, call DMI/weather APIs, expose an API endpoint,
run frontend code, train ML/LLM components, schedule jobs, use Azure, or add
control, dispatch, activation, or operational functionality.

From the `backend/` directory:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Backend tests also run in GitHub Actions on pull requests and pushes to `main`.

Start the API locally:

```bash
uvicorn app.main:app --reload
```

### Local risk preview API smoke test

Manual local validation was documented with the backend started manually:

```bash
python -m uvicorn app.main:app --reload
```

The valid smoke test posted caller-provided JSON only to
`POST /api/risk/preview`:

```json
{
  "price_area": "DK1",
  "timestamp_utc": "2026-06-09T21:45:00+02:00",
  "price_dkk_per_mwh": -10,
  "production_mw": 1000,
  "wind_onshore_mw": 500,
  "wind_offshore_mw": 350,
  "solar_mw": 50,
  "consumption_mw": 900
}
```

Observed local result:

- `risk_level`: `high`
- `risk_score`: `75`
- `confidence_score`: `1.0`
- `reason_codes` included `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`

An invalid input smoke test using `price_area` `SE3` returned a validation
error. Only `DK1` and `DK2` are accepted.

Important boundary notes:

- The risk preview endpoint used caller-provided JSON only.
- No database connection was used.
- No database writes were performed.
- No live Energi Data Service polling was performed.
- No LLM or ML model was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

### Local DK2 EDS ingestion validation

Manual local DK2 ingestion validation used tiny Energi Data Service samples
only.

Dry-run validation observed:

- `DayAheadPrices` DK2 returned HTTP `200`.
- `DayAheadPrices` raw record count was `2`.
- `DayAheadPrices` normalized record count was `2`.
- `DayAheadPrices` SQL command count was `2`.
- `DayAheadPrices` committed was `false`.
- `ElectricityProdex5MinRealtime` DK2 returned HTTP `200`.
- `ElectricityProdex5MinRealtime` raw record count was `2`.
- `ElectricityProdex5MinRealtime` normalized record count was `2`.
- `ElectricityProdex5MinRealtime` SQL command count was `2`.
- `ElectricityProdex5MinRealtime` committed was `false`.

Confirmed local write validation observed:

- `DayAheadPrices` DK2 committed was `true`.
- `ElectricityProdex5MinRealtime` DK2 committed was `true`.
- The writes were local PostgreSQL only.
- The writes were manual confirmed local writes only.

Local row counts after DK2 ingest:

- `spot_prices` DK1: `3`
- `spot_prices` DK2: `2`
- `power_balance` DK1: `3`
- `power_balance` DK2: `2`

Important boundary notes:

- Local PostgreSQL only.
- Manual validation only.
- No production database was used.
- No Azure resources were used.
- No startup migrations were run.
- No automated ingestion job was added.
- No live polling loop was added.
- No ML training was performed.
- No LLM was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

### Local current risk API smoke test

Manual local validation was documented with the backend started manually:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

The smoke test called the current-risk endpoint for DK1:

```text
GET /api/risk/current?price_area=DK1
```

Observed local result:

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

The smoke test also called the current-risk endpoint for DK2:

```text
GET /api/risk/current?price_area=DK2
```

Observed local result:

- backend returned HTTP `200`
- `price_area`: `DK2`
- `risk_level`: `low`
- `risk_score`: `20`
- `confidence_score`: `1.0`
- `reason_codes` included `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`
- `metadata.source_tables_used` included `spot_prices` and `power_balance`
- `metadata.spot_price_row_found`: `true`
- `metadata.power_balance_row_found`: `true`

An invalid input smoke test called:

```text
GET /api/risk/current?price_area=SE3
```

The observed result was a validation error. Only `DK1` and `DK2` are accepted.

Important boundary notes:

- The endpoint read from local PostgreSQL only.
- The endpoint used the existing read-only query path.
- No database writes were performed.
- No live Energi Data Service polling was performed.
- No startup migrations were run.
- No Azure resources were used.
- No production database was used.
- No LLM or ML model was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

### Local DK2 read-only DB risk backtest result

Manual local read-only risk backtest validation was run for DK2 using existing
local PostgreSQL rows only. Before the backtest, local table counts were:

- `spot_prices` DK1: `3`
- `spot_prices` DK2: `2`
- `power_balance` DK1: `3`
- `power_balance` DK2: `2`

The command run was:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK2 --limit 10 --pretty
```

Observed local result:

- `price_area` was `DK2`.
- `limit` was `10`.
- `read_only` was `true`.
- `decision_support_only` was `true`.
- `pairing_strategy` was `nearest_timestamp_v0_1`.
- `spot_price_rows_read` was `2`.
- `power_balance_rows_read` was `2`.
- `composed_rows` was `2`.
- `backtest_summary.total_rows` was `2`.
- `backtest_summary.evaluated_rows` was `2`.
- `backtest_summary.failed_rows` was `0`.
- `backtest_summary.risk_level_counts.low` was `2`.
- `backtest_summary.risk_level_counts.medium` was `0`.
- `backtest_summary.risk_level_counts.high` was `0`.
- `backtest_summary.average_risk_score` was `20.0`.
- `backtest_summary.average_confidence_score` was `1.0`.
- `backtest_summary.reason_code_counts` included `NORMAL_PRICE: 2`,
  `MODERATE_RENEWABLE_SHARE: 2`, and `EXCHANGE_NET_NOT_USED_V0: 2`.
- `backtest_summary.missing_price_count` was `0`.
- `backtest_summary.missing_generation_data_count` was `0`.
- `backtest_summary.model_version` was `rule-engine-v0`.

Interpretation:

- DK2 local read-only path is now validated.
- The DK2 current risk endpoint returned low risk on the tiny local sample.
- The DK2 local DB backtest returned low risk for both composed rows.
- This is still technical validation, not full model validation.
- The dataset is tiny and not enough for performance conclusions.

Important boundary notes:

- Local PostgreSQL only.
- SELECT/read-only backtest only.
- No database writes were performed by the backtest.
- No live EDS polling was performed by the backtest.
- No backend or frontend server was started for the backtest.
- No startup migrations were run.
- No production database was used.
- No Azure resources were used.
- No ML training was performed.
- No LLM was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

### Local read-only DB risk backtest result after nearest-timestamp pairing

Manual local read-only risk backtest validation was rerun after
`nearest_timestamp_v0_1` pairing was merged, using existing local PostgreSQL
rows only. Before the backtest, local table counts were:

- `spot_prices`: `3`
- `power_balance`: `3`

The command run was:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK1 --limit 10 --pretty
```

Observed local result:

- `price_area` was `DK1`.
- `limit` was `10`.
- `read_only` was `true`.
- `decision_support_only` was `true`.
- `pairing_strategy` was `nearest_timestamp_v0_1`.
- `spot_price_rows_read` was `3`.
- `power_balance_rows_read` was `3`.
- `composed_rows` was `3`.
- `backtest_summary.total_rows` was `3`.
- `backtest_summary.evaluated_rows` was `3`.
- `backtest_summary.failed_rows` was `0`.
- `backtest_summary.risk_level_counts.low` was `1`.
- `backtest_summary.risk_level_counts.medium` was `2`.
- `backtest_summary.risk_level_counts.high` was `0`.
- `backtest_summary.average_risk_score` was `26.6667`.
- `backtest_summary.average_confidence_score` was `1.0`.
- `backtest_summary.reason_code_counts` included `NORMAL_PRICE: 3`,
  `EXCHANGE_NET_NOT_USED_V0: 3`, `HIGH_RENEWABLE_SHARE: 2`, and
  `ELEVATED_RENEWABLE_SHARE: 1`.
- `backtest_summary.missing_price_count` was `0`.
- `backtest_summary.missing_generation_data_count` was `0`.
- `backtest_summary.model_version` was `rule-engine-v0`.

Interpretation:

- `nearest_timestamp_v0_1` pairing is active.
- On the tiny local DK1 sample, the risk distribution remained unchanged
  compared with the previous simple pairing run.
- This is expected because the local dataset only contains 3 composed rows.
- This is still technical validation, not full model validation.
- A larger historical dataset is required before drawing performance
  conclusions.

Important boundary notes:

- Local PostgreSQL only.
- SELECT/read-only only.
- No database writes were performed.
- No live EDS polling was performed.
- No backend or frontend server was started.
- No startup migrations were run.
- No production database was used.
- No Azure resources were used.
- No ML training was performed.
- No LLM was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

## Frontend Local Development

The frontend is a minimal Next.js dashboard for `v0.1` read-only decision
support. It includes a DK1/DK2 selector and manual buttons for loading recent
spot prices, power balance rows, and the current surplus risk from existing
backend read-only API endpoints. It does not fetch automatically on page load,
poll live endpoints, call Energi Data Service directly, forecast, dispatch,
activate, or control energy assets.

From the `frontend/` directory:

```bash
npm install
npm run build
npm run dev
```

The frontend uses a backend API base URL helper for manual read-only API
requests. It defaults to `http://127.0.0.1:8000` and can be overridden with
`NEXT_PUBLIC_API_BASE_URL`.

Manual frontend requests use:

- `GET /api/energy/spot-prices?price_area=DK1|DK2&limit=5`
- `GET /api/energy/power-balance?price_area=DK1|DK2&limit=5`
- `GET /api/risk/current?price_area=DK1|DK2`

The read-only disclaimer remains visible in the dashboard:
`Read-only decision support — no automatic control`.

### Local frontend dashboard shell smoke test

Manual local frontend validation was performed by starting the dashboard shell
from the `frontend/` directory:

```bash
npm install
npm run build
npm run dev
```

`next build` completed successfully, TypeScript passed, and the static `/`
route was generated.

The browser smoke-test opened `http://127.0.0.1:3000` and confirmed:

- FlexSignal AI title visible.
- Read-only decision support -- no automatic control badge visible.
- DK1/DK2 selector visible.
- Spot prices card visible.
- Power balance card visible.
- Manual Load spot prices button visible.
- Manual Load power balance button visible.
- Idle, loading, error, row count, and compact result table states available.
- Backend API base URL helper visible as `http://127.0.0.1:8000`.
- Browser copy states that the frontend does not call Energi Data Service
  directly.
- No error screen.

The frontend makes no automatic page-load API requests, direct Energi Data
Service calls, polling requests, database writes, auth calls, Azure resource
changes, forecasting/model calls, or control, dispatch, activation, or
operational functionality. Backend API requests are made only when a user
presses one of the manual load buttons.

Known local development note: opening the Next.js dev server through
`127.0.0.1` showed a development-only cross-origin warning for dev resources.
Use `http://localhost:3000` during local development unless `allowedDevOrigins`
is configured later. This warning did not block the page render.

### Local frontend-to-backend read-only smoke test

Manual local frontend-to-backend validation was performed with the backend
started manually from the `backend/` directory:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

The frontend was started manually from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The browser opened `http://localhost:3000`. The manual read-only UI actions
were:

- Selected DK1.
- Clicked Load spot prices.
- Clicked Load power balance.
- Clicked Load current risk.

Observed local result:

- Spot prices displayed 3 rows for DK1.
- Power balance displayed 3 rows for DK1.
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
- Backend logs showed HTTP 200 for both read-only API calls.
- The local-development CORS fix worked.

Important boundary notes:

- The frontend only called the backend API helper.
- No direct Energi Data Service calls were made from the frontend.
- No polling or automatic refresh was used.
- No database writes were performed.
- No live EDS polling was performed.
- No startup migrations were run.
- No Azure resources were used.
- No production database was used.
- No LLM or ML model was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

## Compliance Principles

- Read-only decision support in `v0.1`.
- Human review before any operational action.
- No autonomous control.
- No control signals to energy infrastructure.
- Auditability for forecasts, recommendations, explanations, and user actions.
- Least-privilege access to systems and data.
- LLMs are limited to explanation and reporting, not core forecasting or final decision-making.
