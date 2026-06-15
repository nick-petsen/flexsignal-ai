# Backtest Results

## Status

FlexSignal AI now includes a pure Python backtest evaluator for
`rule-engine-v0`. It is a synthetic/local evaluator only: callers provide a
list of local row dictionaries, and each valid row is passed to
`calculate_surplus_risk`.

Local read-only database backtests have been run against DK1 and DK2
EDS-derived rows after the manual `limit 50` import. This supports a local
technical MVP demo only. It does not claim production readiness, validated
commercial forecasting performance, predictive accuracy, or statistical
calibration.

## Current MVP Backtest Status

The current backtest work is a read-only technical validation layer for
`rule-engine-v0`. It confirms that the local sample data can be read, composed,
paired with `nearest_timestamp_v0_1`, scored, and summarized. It does not
validate commercial performance or operational readiness.

Latest documented local DB backtest results after the confirmed manual EDS
historical batch write:

| Area | Spot prices read | Power balance read | Composed rows | Backtest risk counts | Average risk score |
| --- | ---: | ---: | ---: | --- | ---: |
| DK1 | 53 | 53 | 53 | low=1, medium=52, high=0 | 34.5283 |
| DK2 | 50 | 50 | 50 | low=42, medium=8, high=0 | 21.8 |

Current read-only foundation:

- Synthetic backtest preview exists for local smoke validation.
- Local PostgreSQL read-only backtest exists for existing local rows.
- Backtest row pairing uses `nearest_timestamp_v0_1`.
- `forecast-window-v0` exists as deterministic pure Python aggregation over
  caller-provided rows for `0-24h`, `24-48h`, and `48-72h` windows.
- `report-summary-v0` exists as a deterministic pure Python data-structure
  builder over caller-provided current-risk and forecast-window outputs.
- `report-summary-v0` Markdown rendering exists as deterministic pure Python
  formatting over caller-provided report dictionaries.
- Manual local PDF export v0 exists for synthetic/caller-provided report
  previews through an explicit `--output` path only.
- `audit-event-v0` exists as a deterministic pure Python in-memory
  data-structure foundation for read-only decision-support audit events.
- Manual local audit-event preview exists for synthetic/caller-provided
  `audit-event-v0` structures and prints JSON only.
- Audit-event database persistence foundation exists through an Alembic
  `audit_events` schema and pure repository SQL builder, but no runtime flow
  automatically writes audit events yet.
- Manual local audit persistence dry-run preview exists for one synthetic
  audit event and repository SQL plan without database access or execution.
- `POST /api/forecast/preview` exposes that aggregation for caller-provided
  rows only.
- The frontend dashboard has a manual read-only forecast preview card that
  calls `POST /api/forecast/preview` with deterministic
  synthetic/caller-provided demo rows only.
- DK1 and DK2 local DB backtests complete with no failed rows on the expanded
  local samples documented below.
- Results are descriptive summaries of deterministic rule-engine outputs.
- Latest local dataset status is `spot_prices` DK1 `53`, `spot_prices` DK2
  `50`, `power_balance` DK1 `53`, and `power_balance` DK2 `50`.

Still preview / not production:

- Dataset is still small.
- No full historical backtest has been run.
- No outcome labels are available.
- No production 24-72 hour forecast has been validated.
- `forecast-window-v0` and `POST /api/forecast/preview` are not ML, not LLM
  based, not DMI/weather based yet, do not fetch EDS or DMI data, do not read
  or write a database, and are not production forecast validation. The
  frontend card does not change that validation status.
- No DMI/weather data is included.
- No statistical calibration or predictive accuracy claim is made.
- Manual synthetic JSON, Markdown, and PDF preview scripts exist for
  `report-summary-v0`. The PDF preview writes one local file only when an
  explicit `--output` path is provided and refuses overwrite without
  `--force`.
- `audit-event-v0` and the manual audit-event preview have a schema/repository
  persistence foundation available for later explicit reviewed wiring, but do
  not automatically persist audit logs, write files, expose an API, add
  frontend UI, connect report/PDF flows, run scheduled logging, connect to
  auth/Entra, call EDS or DMI/weather APIs, use ML, use LLMs, or validate
  production forecast performance.
- `report-summary-v0` and its local preview script do not fetch data, read or
  write a database, expose an API, use ML, use LLMs, or validate production
  forecast performance.
- No scheduled ingestion jobs, production database, Azure deployment, auth, ML
  training, LLM decisioning, automatic control, dispatch, activation, or
  operational workflow exists.

Recommended next MVP audit/reporting step: keep PDF export and audit-event
preview manual/local for now. A future reviewed module can wire explicit
read-only flows to audit persistence. Do not add automatic scheduled report
generation, do not fetch data from the report builder, do not use an LLM as
the forecast or reporting engine, and do not add control, dispatch, or
activation behavior.

## Audit Event Boundary

`audit-event-v0` is not a backtest, forecast model, API endpoint, database
reader, database writer, data ingester, or operational workflow. It is a
deterministic in-memory audit event dictionary builder for future compliance
and audit logging of read-only decision-support actions.

The builder accepts caller-provided fields only, validates explicit event,
actor, and outcome values, requires timezone-aware event time, rejects empty
required fields, preserves safe JSON-compatible metadata, rejects secret-like
metadata keys, and returns a deterministic `audit_evt_...` event id. It always
includes safety fields for read-only decision support, no automatic control, no
dispatch, no activation, no operational energy-system integration, and human
review required.

An audit-event database persistence foundation now exists. Alembic migration
`0002_audit_events.py` defines the `audit_events` table and indexes, and
`backend/app/audit/repository.py` validates event dictionaries, preserves the
required read-only safety boundary, serializes JSONB fields as parameters, and
builds idempotent `ON CONFLICT (event_id) DO NOTHING` insert SQL.

It does not automatically persist audit logs, write files, expose an API, add
frontend UI, connect report/PDF flows, run scheduled logging, connect to
auth/Entra, call Energi Data Service, call DMI/weather APIs, use ML, use LLMs,
add scheduling, add Azure infrastructure, add auth, add secrets, or perform
automatic control, dispatch, activation, closed-loop workflows, asset
connections, plant/device commands, live control signals, or autonomous
decisions.

`scripts/audit_event_preview.py` is a manual synthetic local preview for the
same audit event structure. It imports `build_audit_event(...)`, uses fixed
`occurred_at_utc=2026-01-01T00:00:00Z`, safe synthetic metadata only, and
prints compact JSON by default or indented JSON with `--pretty`.

```bash
python3 scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py --pretty
python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty
```

The default `--event-type all` prints an `events` array. Single event types
print one `event` object. This preview does not persist audit logs, write
files, access a database, expose an API, use frontend code, call EDS/DMI, use
ML, use LLMs, perform operational integration, or add automatic control,
dispatch, or activation. Future audit work can wire explicit read-only flows
to the audit persistence foundation only after review.

### Audit Event Preview Validation Results

The manual audit-event preview was validated locally with
synthetic/caller-provided data only. It did not persist events, write files,
access a database, run SQL, expose an API, use frontend code, call Energi Data
Service, call DMI/weather APIs, use ML, use LLMs, or create operational logs.

Commands observed:

```bash
python3 -m py_compile scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py --pretty
python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_event_preview.py --event-type invalid-event
```

Observed compact summary:

| Check | Result |
| --- | --- |
| `py_compile` | Passed. |
| Default preview | Printed compact JSON with an `events` array. |
| `--pretty` | Printed indented JSON. |
| `report_pdf_exported` event type | Printed one event. |
| `forecast_preview_requested` event type | Printed one event. |
| Invalid event type | Failed safely with exit code `2` and a clear argparse invalid-choice validation error. |
| Forbidden-pattern grep | Returned no matches. |
| `git diff --check` | Passed. |

Covered event types were `forecast_preview_requested`,
`current_risk_viewed`, `report_summary_built`,
`report_markdown_rendered`, and `report_pdf_exported`. Generated events
included `event_version=audit-event-v0`, deterministic `audit_evt_...` event
ids, fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, and `local_only=true`.

Each event included a `safety_boundary` with
`read_only_decision_support=true`, `no_automatic_control=true`,
`no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Interpretation: audit-event preview works locally and demonstrates the
audit-event shape for read-only decision-support actions. The persistence
foundation now defines database schema and SQL builder behavior, but no
API/frontend/report/scheduled/auth flow writes events automatically. It does
not connect to auth or actor identity providers, create operational logs, or
provide production audit persistence. Explicit persistence wiring can be
considered next, but only as a separate reviewed module. Do not add automatic
control, dispatch, activation, scheduler, or operational functionality.

### Audit DB Persistence PR Validation Results

The audit DB persistence foundation was added in PR #87 after the
`audit-event-v0` builder, manual preview script, and preview-result docs
already existed. The PR added schema/repository readiness only: an Alembic
`audit_events` migration and repository SQL builder using validated events and
parameterized `ON CONFLICT (event_id) DO NOTHING` INSERT SQL. It did not add
FastAPI audit endpoints, frontend behavior, automatic audit logging,
report/PDF integration, scheduler behavior, auth/Entra integration, live
EDS/DMI calls, ML/LLM behavior, live database writes, or control, dispatch,
activation, or operational functionality.

The schema records `event_id` as the primary/idempotency key,
`event_version`, `event_type`, `actor_type`, `actor_id`,
`occurred_at_utc`, `resource_type`, `resource_id`, `action`, `outcome`,
`decision_support_only`, JSONB `safety_boundary`, JSONB `metadata`, and
`created_at_utc` with a default. It adds indexes for occurrence time, event
type, resource lookup, and actor lookup. Validation planned persistence only;
it did not perform live database writes.

Initial local validation before PR review documented:

- Backend tests passed with `310 passed, 1 warning`.
- `py_compile` passed for `backend/app/audit/events.py` and
  `backend/app/audit/repository.py`.
- Safety-boundary grep matched only expected terms:
  `no_automatic_control`, `no_dispatch`, and `no_activation`.
- `git diff --check` passed.

GitHub backend-tests initially failed before merge because newer
FastAPI/Starlette CI/test route exposure did not list `/api/risk/current`,
`/api/risk/preview`, and `/api/forecast/preview` in `app.routes`. The failing
tests were `tests/test_api_energy.py::test_app_exposes_no_mutating_write_methods`
and
`tests/test_api_risk.py::test_app_import_without_database_url_still_exposes_current_risk_route`.
This was not caused by live database writes or audit persistence execution,
and the branch was not merged while backend-tests were red.

The fix updated `backend/app/main.py` with a small route-registration helper
for concrete paths under the test environment. `DATABASE_URL` validation
remains request-time only, endpoint logic was not changed, and no new API
behavior, DB writes, scheduler, frontend behavior, or control behavior was
added.

Post-fix validation documented:

- Focused route tests passed with `2 passed, 1 warning`.
- Full backend suite passed with `310 passed, 1 warning`.
- `git diff --check` passed.
- The PR diff contained no `.pyc`, virtualenv, cache, or generated files.
- GitHub backend-tests were re-run and green before merge.
- PR #87 was merged only after backend-tests were green.

Final merged files were
`backend/alembic/versions/0002_audit_events.py`,
`backend/app/audit/repository.py`, `backend/app/main.py`,
`backend/tests/test_audit_event_repository.py`, `README.md`,
`docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`,
`docs/BACKTEST_RESULTS.md`, and `CHANGELOG.md`.

Interpretation: the audit DB persistence foundation prepares for future
explicit audited read-only flows. It does not prove production audit
persistence, identify real users through Entra ID, or automatically write
events. Future work may add controlled repository execution with an explicit
database connection and tests, but automatic audit logging and frontend/report
download persistence wiring should remain deferred until explicit review.

### Audit Persistence Dry-Run Preview

`scripts/audit_persistence_preview.py` is a manual local dry-run preview for
audit persistence planning. It builds one synthetic/caller-provided
`audit-event-v0`, calls the repository SQL builder, and prints JSON containing
`dry_run=true`, `database_write_performed=false`,
`requires_database_url=false`, the event, and a persistence plan for
`audit_events` with `ON CONFLICT (event_id) DO NOTHING`.

```bash
python3 scripts/audit_persistence_preview.py
python3 scripts/audit_persistence_preview.py --pretty
python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty
```

The preview does not persist audit events, access a database, require
`DATABASE_URL`, run SQL, expose an API, use frontend code, write files,
generate PDFs, call EDS/DMI, use ML, use LLMs, add scheduler or Azure
infrastructure, add auth, add secrets, or add automatic audit logging. It does
not change backtest validity or model performance claims.

Observed dry-run validation:

| Command/check | Observed result |
| --- | --- |
| `python3 -m py_compile scripts/audit_persistence_preview.py` | Passed. |
| `python3 scripts/audit_persistence_preview.py` | Printed compact JSON. |
| `python3 scripts/audit_persistence_preview.py --pretty` | Printed indented JSON. |
| `python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty` | Dry-run passed. |
| `python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty` | Dry-run passed. |
| `python3 scripts/audit_persistence_preview.py --event-type invalid-event` | Failed safely with exit code `2` and argparse invalid-choice output. |
| Forbidden-pattern grep on `scripts/audit_persistence_preview.py` | Returned no matches. |
| `git diff --check` | Passed. |

Observed output included `dry_run=true`,
`database_write_performed=false`, `requires_database_url=false`, `event`, and
`persistence_plan`. The event used `event_version=audit-event-v0`,
deterministic `audit_evt_...` event id,
`occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, `local_only=true`, and the read-only/no-control
human-review safety boundary. The persistence plan included the
`audit_events` table target, SQL/SQL preview, parameter keys/params,
`event_id` idempotency key, and
`ON CONFLICT (event_id) DO NOTHING` conflict behavior.

Interpretation: the preview demonstrates how `audit-event-v0` can become a
parameterized persistence plan, but it does not prove live DB persistence,
perform database writes, run SQL, connect to a database, expose API/frontend
behavior, integrate report/PDF flows, add automatic audit logging, or affect
backtest results. A future controlled local write test must be a separate
reviewed module.

### Audit DB Write Smoke

`scripts/audit_db_write_smoke.py` is a manual local-only write smoke for one
deterministic synthetic `audit-event-v0`. It is not a backtest, forecasting
model, calibration step, or production audit system. It defaults to dry-run
and does not connect to a database unless `--execute` and an explicit local
`--database-url` are provided.

```bash
python3 scripts/audit_db_write_smoke.py --pretty
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty
```

The script writes only to `audit_events` when explicitly executed. It does not
write energy, forecast, backtest, or report data, and it does not change any
documented backtest result. It accepts only local database URLs by default,
refuses obvious remote/cloud URLs, does not print the raw database URL, runs
the idempotent repository insert twice, commits, and can verify the row by
`event_id`.

It does not expose an API, add frontend code, add automatic audit logging,
integrate report/PDF/API/frontend flows, schedule work, use Azure
infrastructure, add auth or secrets, call EDS/DMI, use ML, use LLMs, or add
control, dispatch, activation, or operational functionality.

Observed audit DB write smoke validation:

| Command/check | Observed result |
| --- | --- |
| `python3 -m py_compile scripts/audit_db_write_smoke.py backend/tests/test_audit_db_write_smoke.py` | Passed. |
| `python -m pytest tests/test_audit_db_write_smoke.py -q` | Focused smoke tests passed: `7 passed`. |
| `python -m pytest` | Full backend suite passed: `317 passed, 1 warning`. |
| `python3 scripts/audit_db_write_smoke.py` | Default dry-run passed. |
| `python3 scripts/audit_db_write_smoke.py --pretty` | Pretty dry-run passed. |
| `python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty` | `forecast_preview_requested` dry-run passed. |
| `python3 scripts/audit_db_write_smoke.py --execute` | Failed safely with exit code `2`. |
| `python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://remote.example.com/flexsignal_ai` | Failed safely with exit code `2`. |
| Forbidden-pattern grep on script and test | Returned no matches. |
| `git diff --check` | Passed. |

No live DB writes were performed during those earlier guardrail checks.

Later manual local Postgres validation ran:

```bash
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
```

Alembic used `PostgresqlImpl`, assumed transactional DDL, migrated
`0001_initial_schema` to `0002_audit_events`, added the audit-event-v0
persistence foundation, and succeeded.

The first smoke result reported
`event_id=audit_evt_f8ea1513efa7fa0067b0ca04`,
`event_type=report_pdf_exported`, `dry_run=false`,
`execute_requested=true`, `database_write_performed=true`,
`local_database_only=true`, `table=audit_events`, `inserted_attempts=2`,
`rowcount_first_insert=1`, `rowcount_second_insert=0`,
`conflict_behavior=ON CONFLICT (event_id) DO NOTHING`,
`verify_read_performed=true`, `warnings=[]`, and `verified_row` returned by
`event_id`. The second run used the same event id and event type, returned
`rowcount_first_insert=0` and `rowcount_second_insert=0`, and returned
`verified_row`, confirming idempotency across repeated script executions.

The verified row included `event_version=audit-event-v0`,
`action=preview_report_pdf_export`, `actor_type=local_developer`,
`actor_id=local-dev`, `outcome=success`, `decision_support_only=true`,
`resource_type=report_pdf`,
`resource_id=report-summary-v0:DK1:synthetic-pdf`, and metadata
`local_only=true`, `output_format=pdf`, `price_area=DK1`,
`report_version=report-summary-v0`, and `synthetic_preview_only=true`. The
returned `occurred_at_utc` value was `2026-01-01T01:00:00+01:00`, interpreted
as database/session timezone rendering of the stored `timestamptz` instant.

The raw `DATABASE_URL` was not printed, and the safety boundary preserved
`read_only_decision_support=true`, `no_automatic_control=true`,
`no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

Interpretation: local `audit_events` DB write is manually verified, the
repository insert path works against local Postgres, idempotency works via
`ON CONFLICT (event_id) DO NOTHING`, and verify-read by `event_id` works. This
does not change backtest results, model validation, API/frontend behavior,
report/PDF behavior, or automatic audit logging status. It does not enable
production audit persistence and does not add FastAPI endpoints, frontend
behavior, scheduler, Azure infrastructure, auth/Entra integration, live
EDS/DMI calls, ML/LLM use, control, dispatch, activation, or operational
functionality. A future module may add a read-only API-side audit logging
design or manual API audit dry-run, but automatic audit persistence must not
be wired into runtime flows yet.

## Report Summary Boundary

`report-summary-v0` is not a backtest, forecast model, API endpoint, database
reader, database writer, or API renderer. It is a deterministic payload
builder that accepts caller-provided current-risk output and
caller-provided `forecast-window-v0` output only.

`render_report_summary_markdown(...)` is the separate Markdown renderer for
`report-summary-v0`. It converts a caller-provided report dictionary into a
deterministic Markdown string and renders unavailable current-risk or forecast
summaries clearly when the supplied mapping is incomplete. It does not generate
PDF files, write files, fetch data, access a database, expose an API, use
frontend code, use ML, or use LLMs.

`render_report_markdown_pdf_bytes(...)` renders caller-provided Markdown into
PDF bytes for manual local preview use. It does not write files, fetch data,
access a database, expose an API, use frontend code, use ML, or use LLMs. It
uses simple ReportLab rendering only.

It always marks the output as read-only decision support, requires human
review, includes safety notes against automatic control, dispatch, and
activation, and records limitations including no production forecast
validation, no outcome labels, no DMI/weather data yet, no ML training, no LLM
use, caller-provided data only, no database read/write, and no live API calls.

`scripts/report_summary_preview.py` is a manual synthetic local JSON preview
for this report payload. It uses fixed `generated_at_utc` output and
in-script caller-provided current-risk and forecast-window data only. It does
not establish model validity, statistical calibration, production readiness, or
operational fitness.

`scripts/report_markdown_preview.py` is a manual synthetic local Markdown
preview for the same report payload. It uses fixed `generated_at_utc` output,
in-script caller-provided current-risk and forecast-window data only, calls
`build_report_summary(...)`, calls `render_report_summary_markdown(...)`, and
prints Markdown to stdout. It does not write files, generate PDF files, fetch
data, access a database, expose an API, use frontend code, use ML, use LLMs,
or establish model validity, statistical calibration, production readiness, or
operational fitness.

`scripts/report_pdf_preview.py` is a manual synthetic local PDF preview for
the same report payload. It uses fixed `generated_at_utc` output, in-script
caller-provided current-risk and forecast-window data only, builds
`report-summary-v0`, renders Markdown, renders PDF bytes, and writes exactly
one local PDF only to an explicit `--output PATH`. It refuses overwrite unless
`--force` is provided. It does not fetch data, access a database, run SQL,
expose an API, add frontend download behavior, use ML, use LLMs, or establish
model validity, statistical calibration, production readiness, or operational
fitness.

## Forecast Preview API Boundary

`POST /api/forecast/preview` accepts caller-provided DK1/DK2 rows and returns
the deterministic `forecast-window-v0` `0-24h`, `24-48h`, and `48-72h`
summaries. It is read-only decision support only.

The frontend dashboard now includes a manual "Forecast preview" card for this
endpoint. It uses deterministic synthetic/caller-provided rows only, includes a
timezone-aware `generated_at_utc`, uses only the backend API base URL helper,
does not auto-load or poll, does not fetch EDS/DMI data from the browser, and
does not read or write a database.

The endpoint does not fetch Energi Data Service data, call DMI/weather APIs,
read or write a database, persist rows, start jobs, train ML models, use LLMs,
or perform automatic control, dispatch, activation, closed-loop workflows,
asset connections, plant/device commands, or live control signals.

### Forecast Preview API Smoke Test Results

`POST /api/forecast/preview` was smoke-tested manually with the backend started
without `DATABASE_URL`. This confirms that the endpoint does not require
database access for caller-provided forecast rows. No frontend was used, and no
ingestion, database writes, SQL, live Energi Data Service calls, DMI/weather
calls, scheduler, Azure infrastructure, auth, secrets, ML training, LLM use,
control, dispatch, activation, or operational functionality was used.

Valid DK1 request:

| Field | Observed value |
| --- | --- |
| HTTP | `200` |
| `price_area` | `DK1` |
| `generated_at_utc` | `2026-01-01T00:00:00Z` |
| `model_version` | `rule-engine-v0+forecast-window-v0` |
| `decision_support_only` | `true` |
| Windows returned | `3` |

Valid DK1 window results:

| Window | Row count | Risk level | Max risk score | Average risk score | Notes |
| --- | ---: | --- | ---: | ---: | --- |
| `0-24h` | 1 | low | 30 | 30.0 | top reason codes included `MODERATE_PRICE` and `MODERATE_RENEWABLE_SHARE` |
| `24-48h` | 1 | high | 75 | 75.0 | top reason codes included `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE` |
| `48-72h` | 0 | unknown | null | null | `average_confidence_score=0.0` |

High-risk DK2 request:

- HTTP `200`
- `price_area`: `DK2`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- `24-48h` returned `row_count=1`, `risk_level=high`,
  `max_risk_score=75`, `average_risk_score=75.0`, and top reason codes
  including `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`.
- `0-24h` and `48-72h` were `unknown` because `row_count=0`.

Validation requests:

- `price_area=SE3` returned a validation error indicating that input should be
  `DK1` or `DK2`.
- Timezone-naive `generated_at_utc` returned a validation error indicating that
  `generated_at_utc` must be timezone-aware.

Interpretation:

- `POST /api/forecast/preview` works for caller-provided rows.
- It returns deterministic `0-24h`, `24-48h`, and `48-72h` forecast windows.
- It demonstrates max-risk aggregation.
- It handles empty windows as `unknown`.
- It validates DK1/DK2 and timezone-aware `generated_at_utc`.
- It is read-only decision support and requires human review.
- It is not production forecast validation.

### Frontend Forecast Preview Smoke Test After CORS Fix

The frontend Forecast preview card was smoke-tested manually from `main` after
the local CORS preflight fix was merged. The backend was started without
`DATABASE_URL`, and the frontend was started locally. The smoke test used only
the Forecast preview card; spot prices, power balance, and current surplus risk
cards were not used. No ingestion, database access, SQL, database writes, live
Energi Data Service calls, DMI/weather calls, scheduler, Azure infrastructure,
auth, secrets, ML training, LLM use, automatic control, dispatch, activation,
or operational functionality was run or added.

Frontend behavior observed:

- Forecast preview card was visible.
- Read-only badge was visible.
- Synthetic/caller-provided preview warning was visible.
- No forecast data appeared before clicking the manual button.
- Manual "Load forecast preview" button triggered the preview.
- The card displayed `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, `generated_at_utc=2026-01-01T00:00:00Z`, and
  three windows: `0-24h`, `24-48h`, and `48-72h`.

DK1 frontend result:

| Window | Row count | Risk level | Max risk score | Average risk score | Top reason codes observed |
| --- | ---: | --- | ---: | ---: | --- |
| `0-24h` | 1 | low | 30 | 30 | `EXCHANGE_NET_NOT_USED_V0`, `MODERATE_PRICE`, `MODERATE_RENEWABLE_SHARE` |
| `24-48h` | 1 | high | 75 | 75 | `EXCHANGE_NET_NOT_USED_V0`, `HIGH_RENEWABLE_SHARE`, `NEGATIVE_PRICE`; recommended human action required human review |
| `48-72h` | 1 | low | 10 | 10 | `ELEVATED_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0`, `NORMAL_PRICE` |

DK2 frontend result:

- The selected price area was switched to `DK2`.
- Manual "Load forecast preview" returned forecast-window data again.
- The card displayed the same three forecast windows and decision-support-only
  fields without frontend error.
- This confirmed the selected price area can be used by the frontend helper
  for the forecast preview flow.

CORS interpretation: the previous browser error was caused by `OPTIONS`
preflight returning `400`. After the CORS fix, the frontend successfully loaded
forecast preview data from `POST /api/forecast/preview`, practically
confirming the local CORS preflight path for the Forecast preview card.

Interpretation:

- The frontend forecast preview card works locally.
- It manually calls `POST /api/forecast/preview`.
- It displays deterministic `0-24h`, `24-48h`, and `48-72h` windows.
- It uses synthetic/caller-provided demo rows only.
- It is not production forecast validation, not ML, not LLM based, and not
  DMI/weather based yet.
- It does not fetch EDS/DMI data from the browser.
- It does not read or write a database.
- It does not auto-load or poll.
- It remains local frontend/backend smoke-test documentation only, read-only
  decision support only, and requires human review.

## Planned Historical Local Sample Backtest Validation

This is a documentation-only plan for using larger local EDS-derived samples to
improve read-only technical backtest coverage. The current manual batch wrapper
defaults to `limit 10` and now supports explicit `limit 50` for manual local
validation. It does not add backend or frontend behavior, run database writes,
run live API polling, add scheduled jobs, add Azure infrastructure, add
secrets, add auth, add ML training, use LLMs, or add control, dispatch,
activation, closed-loop, or operational functionality.

The proposed local import source remains limited to:

- `DayAheadPrices` for `DK1` and `DK2`.
- `ElectricityProdex5MinRealtime` for `DK1` and `DK2`.

The larger batch progression is:

| Stage | Limit per dataset and price area | Required action before next stage |
| --- | ---: | --- |
| 1 | 50 | Confirmed local write, repeated-import idempotency, and DK1/DK2 local DB backtest results are documented below. |
| 2 | 100 | Repeat the same checks and confirm counts do not duplicate unexpectedly. |
| 3 | 500 maximum | Run only after smaller batches pass without mapping, normalization, or idempotency issues. |

The `100` and `500` stages still require a future explicit enhancement before
the manual wrapper can run them. The wrapper must not bypass the child script
safety gate.

After each batch, rerun the local DB read-only backtest for both `DK1` and
`DK2` and document:

- `spot_price_rows_read`
- `power_balance_rows_read`
- `composed_rows`
- `backtest_summary.risk_level_counts`
- `backtest_summary.average_risk_score`
- `backtest_summary.failed_rows`
- `backtest_summary.missing_price_count`
- `backtest_summary.missing_generation_data_count`

Any future larger local sample imported through the manual batch wrapper should
be followed by DK1 and DK2 local DB backtest reruns before drawing conclusions
from the expanded data.

Stop the local validation flow if any import produces duplicate explosion,
uses a non-local database URL, writes without explicit confirmation, fails
normalization, reveals unexpected source field mapping, or introduces control,
dispatch, activation, closed-loop, or operational behavior.

Even after these larger local samples are imported, the results remain
technical validation only. They are not full model validation because there are
no outcome labels, no DMI/weather data, no production-validated 24-72 hour
forecast, no statistical calibration, and `rule-engine-v0` remains
deterministic and simple.

## Confirmed Local Batch Backtest Results

The following local DB backtests were run after the manual EDS historical batch
wrapper performed confirmed local writes for `DayAheadPrices` and
`ElectricityProdex5MinRealtime` across `DK1` and `DK2`.

Counts before the confirmed batch write:

| Table | DK1 | DK2 |
| --- | ---: | ---: |
| `spot_prices` | 13 | 10 |
| `power_balance` | 13 | 12 |

Confirmed batch write command:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --confirm-local-db-write --continue-on-error
```

Confirmed batch summary:

- `child_exit_codes`: `[0, 0, 0, 0]`
- `commands_planned`: `4`
- `commands_succeeded`: `4`
- `commands_failed`: `0`
- `confirmed_local_write`: `true`
- `dry_run`: `false`
- `limit`: `50`
- `local_only`: `true`
- `decision_support_only`: `true`
- `price_areas`: `DK1`, `DK2`
- `datasets`: `DayAheadPrices`, `ElectricityProdex5MinRealtime`

Child confirmed write observations:

| Dataset | PriceArea | HTTP | Raw | Normalized | SQL commands | Table | Committed |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `DayAheadPrices` | `DK1` | 200 | 50 | 50 | 50 | `spot_prices` | `true` |
| `DayAheadPrices` | `DK2` | 200 | 50 | 50 | 50 | `spot_prices` | `true` |
| `ElectricityProdex5MinRealtime` | `DK1` | 200 | 50 | 50 | 50 | `power_balance` | `true` |
| `ElectricityProdex5MinRealtime` | `DK2` | 200 | 50 | 50 | 50 | `power_balance` | `true` |

Counts after the confirmed batch write:

| Table | DK1 | DK2 |
| --- | ---: | ---: |
| `spot_prices` | 53 | 50 |
| `power_balance` | 53 | 50 |

The same confirmed batch command was run a second time as an idempotency
check. The second run reported `child_exit_codes: [0, 0, 0, 0]`,
`commands_planned: 4`, `commands_succeeded: 4`, `commands_failed: 0`,
`confirmed_local_write: true`, `dry_run: false`, `limit: 50`, and
`local_only: true`. Counts remained unchanged after the second run:
`spot_prices` DK1 `53`, `spot_prices` DK2 `50`, `power_balance` DK1 `53`, and
`power_balance` DK2 `50`. No duplicate explosion was observed, and the
repeated import was idempotent for the same 50-record batch.

### DK1 Result After Confirmed Batch Write

Command:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK1 --limit 100 --pretty
```

Observed output:

- `price_area`: `DK1`
- `read_only`: `true`
- `decision_support_only`: `true`
- `pairing_strategy`: `nearest_timestamp_v0_1`
- `spot_price_rows_read`: `53`
- `power_balance_rows_read`: `53`
- `composed_rows`: `53`
- `backtest_summary.total_rows`: `53`
- `backtest_summary.evaluated_rows`: `53`
- `backtest_summary.failed_rows`: `0`
- `backtest_summary.risk_level_counts.low`: `1`
- `backtest_summary.risk_level_counts.medium`: `52`
- `backtest_summary.risk_level_counts.high`: `0`
- `backtest_summary.average_risk_score`: `34.5283`
- `backtest_summary.average_confidence_score`: `1.0`
- `backtest_summary.reason_code_counts.NORMAL_PRICE`: `53`
- `backtest_summary.reason_code_counts.HIGH_RENEWABLE_SHARE`: `52`
- `backtest_summary.reason_code_counts.EXCHANGE_NET_NOT_USED_V0`: `53`
- `backtest_summary.reason_code_counts.ELEVATED_RENEWABLE_SHARE`: `1`
- `backtest_summary.missing_price_count`: `0`
- `backtest_summary.missing_generation_data_count`: `0`
- `backtest_summary.model_version`: `rule-engine-v0`

### DK2 Result After Confirmed Batch Write

Command:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK2 --limit 100 --pretty
```

Observed output:

- `price_area`: `DK2`
- `read_only`: `true`
- `decision_support_only`: `true`
- `pairing_strategy`: `nearest_timestamp_v0_1`
- `spot_price_rows_read`: `50`
- `power_balance_rows_read`: `50`
- `composed_rows`: `50`
- `backtest_summary.total_rows`: `50`
- `backtest_summary.evaluated_rows`: `50`
- `backtest_summary.failed_rows`: `0`
- `backtest_summary.risk_level_counts.low`: `42`
- `backtest_summary.risk_level_counts.medium`: `8`
- `backtest_summary.risk_level_counts.high`: `0`
- `backtest_summary.average_risk_score`: `21.8`
- `backtest_summary.average_confidence_score`: `1.0`
- `backtest_summary.reason_code_counts.NORMAL_PRICE`: `50`
- `backtest_summary.reason_code_counts.MODERATE_RENEWABLE_SHARE`: `39`
- `backtest_summary.reason_code_counts.HIGH_RENEWABLE_SHARE`: `8`
- `backtest_summary.reason_code_counts.ELEVATED_RENEWABLE_SHARE`: `3`
- `backtest_summary.reason_code_counts.EXCHANGE_NET_NOT_USED_V0`: `50`
- `backtest_summary.missing_price_count`: `0`
- `backtest_summary.missing_generation_data_count`: `0`
- `backtest_summary.model_version`: `rule-engine-v0`

Interpretation:

- The batch wrapper successfully performed confirmed local writes for all
  supported DK1/DK2 dataset combinations.
- The import was idempotent for the repeated 50-record batch.
- DK1 remained mostly medium risk on the expanded local sample.
- DK2 now includes both low and medium risk on the expanded local sample.
- This is stronger technical validation than the 10-row sample.
- This is still technical validation and not full model validation.
- Dataset size is still small and has no outcome labels.

Safety notes:

- Local PostgreSQL only.
- Manual confirmed write only.
- Explicit `--confirm-local-db-write` was required.
- Backtests were read-only.
- No production database.
- No Azure resources.
- No scheduler.
- No live API polling.
- No backend startup ingestion.
- No frontend-triggered ingestion.
- No automatic polling loop.
- No ML training.
- No LLM use.
- No automatic control, dispatch, activation, or operational functionality.

## Read-Only API And Frontend Smoke Test After Limit 50 Local Import

After local PostgreSQL had been populated by the manual `limit 50` EDS
confirmed local write documented above, the read-only current-risk API and
frontend dashboard were smoke-tested against the larger local sample. No
ingestion or writes were run during this smoke-test. This was a local MVP
smoke-test only, not production validation or model-performance validation.

API commands:

```bash
curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK1"
curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK2"
```

Observed API results:

| Area | HTTP | Timestamp | Risk level | Risk score | Confidence | Reason codes | Model | Decision support only |
| --- | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| DK1 | 200 | `2026-06-10T17:00:00+02:00` | medium | 35 | 1.0 | `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | `rule-engine-v0` | true |
| DK2 | 200 | `2026-06-10T17:00:00+02:00` | low | 20 | 1.0 | `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | `rule-engine-v0` | true |

Both API responses reported `metadata.source_tables_used` as `spot_prices` and
`power_balance`, with `metadata.spot_price_row_found=true` and
`metadata.power_balance_row_found=true`.

Frontend smoke-test URL:

```text
http://localhost:3000
```

Observed frontend results:

| Area | Spot prices manual load | Power balance manual load | Current risk manual load | Read-only badge |
| --- | --- | --- | --- | --- |
| DK1 | 5 `spot_prices` rows | 5 `power_balance` rows | `risk_level=medium`, `risk_score=35`, `confidence_score=1`; reason codes included `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | visible |
| DK2 | 5 `spot_prices` rows | 5 `power_balance` rows | `risk_level=low`, `risk_score=20`, `confidence_score=1`; reason codes included `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | visible |

Interpretation:

- The read-only dashboard works for DK1 and DK2 after the `limit 50` local
  import.
- The frontend still requires manual button clicks.
- No automatic loading, polling, dispatch, activation, or control behavior was
  observed.
- The current-risk endpoint still reads from local PostgreSQL and returns
  decision-support-only results.
- These observations are compatible with the local DB backtest summaries, but
  they do not add outcome labels, statistical calibration, DMI/weather data, or
  a validated 24-72 hour forecast.

Safety notes:

- Local PostgreSQL only.
- Read-only API/UI smoke-test only.
- No ingestion was run.
- No database writes were run.
- No live Energi Data Service polling was run.
- No Azure resources.
- No scheduler.
- No backend startup ingestion.
- No frontend-triggered ingestion.
- No automatic polling loop.
- No ML training.
- No LLM use.
- No automatic control, dispatch, activation, or operational functionality.

## Synthetic Preview Script

`scripts/risk_backtest_preview.py` provides a manual local preview of
`evaluate_risk_backtest(rows)` using a tiny hardcoded synthetic dataset. The
sample rows are included only to exercise low-, medium-, and high-like
rule-engine outputs, missing-data counters, and one invalid row captured in
`failed_rows`.

Run it manually:

```bash
python3 scripts/risk_backtest_preview.py
python3 scripts/risk_backtest_preview.py --pretty
```

The script prints a JSON summary of the evaluator output. It does not read a
historical dataset and does not establish model validity.

This preview is not a real historical backtest, not model validation, not
statistical calibration, and not evidence of production performance. It is only
a local smoke preview of existing deterministic aggregation behavior.

## Report Summary Synthetic Preview Script

`scripts/report_summary_preview.py` provides a manual synthetic local JSON
preview of `report-summary-v0` using fixed `generated_at_utc` output and
in-script caller-provided current-risk and forecast-window data only. It calls
`build_report_summary(...)` and prints compact JSON by default.

Run it manually:

```bash
python3 scripts/report_summary_preview.py
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

The `standard` scenario includes medium current risk and three forecast
windows. The `high-risk` scenario includes high current risk and a high
forecast window. The missing-input scenarios demonstrate unavailable
current-risk and forecast-window summaries without unsafe generation.

This preview is not a historical backtest, not model validation, not
statistical calibration, and not evidence of production performance. It does
not require `DATABASE_URL`, generate PDF files, read or write a database, run
SQL, fetch Energi Data Service data, call DMI/weather APIs, expose an API
endpoint, run frontend code, create ingestion jobs, use Azure, add secrets,
add auth, train ML models, use LLMs, control assets, dispatch, activate, or
perform operational functionality.

### Observed Report Summary Synthetic Preview Results

The following local synthetic commands were run:

```bash
python3 scripts/report_summary_preview.py --pretty
python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty
python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty
```

All four runs printed the synthetic-only warning, used
`generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`. Each payload included safety notes and
limitations. Safety notes prohibited automatic control, dispatch, and
activation. Limitations documented caller-provided data only, no database
read/write, no live API calls, no ML training in the report builder, and no
LLM use in the report builder.

Standard scenario, command
`python3 scripts/report_summary_preview.py --pretty`, returned
`price_area=DK1`. `current_risk_summary` was available with
`risk_level=medium` and `risk_score=45`. `forecast_window_summary` was
available with three windows. Key findings reported medium current risk, no
high-risk forecast window, and caller-provided data only. Recommended human
actions included reviewing local operating context, routine monitoring,
reviewing the medium-risk window, required human review before operational
planning, source-context verification, and no automatic control, dispatch, or
activation.

High-risk scenario, command
`python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty`,
returned `price_area=DK2`. `current_risk_summary` was available with
`risk_level=high` and `risk_score=75`. The forecast summary was available
with three windows, including `24-48h` as high risk with
`max_risk_score=80`. Key findings mentioned both current high risk and a
high-risk forecast window. Recommended actions required escalation and human
review before planning, and safety notes still prohibited automatic control,
dispatch, and activation.

Missing-current-risk scenario, command
`python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty`,
returned `price_area=DK1`. `current_risk_summary.status` was `unavailable`.
The forecast summary remained available with three windows. Limitations added
`missing or incomplete current risk input`, and report generation remained
safe with decision-support-only and human-review flags.

Missing-forecast scenario, command
`python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty`,
returned `price_area=DK1`. `forecast_window_summary.status` was
`unavailable` with zero windows. The current-risk summary remained available
with `risk_level=medium` and `risk_score=45`. Limitations added
`missing or incomplete forecast input`, and report generation remained safe
with decision-support-only and human-review flags.

Interpretation:

- `report-summary-v0` preview works locally with synthetic/caller-provided data.
- It creates deterministic report payloads.
- It does not generate PDF files yet.
- It does not fetch data.
- It does not read or write a database.
- It does not expose an API.
- It does not use frontend code.
- It does not use ML or LLMs.
- It is read-only decision support only.
- It must not be used for automatic control, dispatch, or activation.

## Report Markdown Synthetic Preview Script

`scripts/report_markdown_preview.py` provides a manual synthetic local
Markdown preview of `report-summary-v0` using fixed `generated_at_utc` output
and in-script caller-provided current-risk and forecast-window data only. It
calls `build_report_summary(...)`, calls
`render_report_summary_markdown(...)`, and prints Markdown to stdout.

Run it manually:

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

The `standard` scenario includes current risk and three forecast windows. The
`high-risk` scenario includes high current risk and a high forecast window.
The missing-input scenarios demonstrate unavailable current-risk and
forecast-window summaries without unsafe generation.

This preview is not a historical backtest, not model validation, not
statistical calibration, and not evidence of production performance. It does
not require `DATABASE_URL`, generate PDF files, write files, read or write a
database, run SQL, fetch Energi Data Service data, call DMI/weather APIs,
expose an API endpoint, run frontend code, create ingestion jobs, use Azure,
add secrets, add auth, train ML models, use LLMs, control assets, dispatch,
activate, or perform operational functionality.

### Observed Report Markdown Synthetic Preview Results

The following local synthetic commands were run:

```bash
python3 scripts/report_markdown_preview.py
python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk
python3 scripts/report_markdown_preview.py --scenario missing-current-risk
python3 scripts/report_markdown_preview.py --scenario missing-forecast
```

All four runs printed the synthetic-only warning to stderr, printed Markdown
to stdout, and used `generated_at_utc=2026-01-01T00:00:00Z`,
`report_version=report-summary-v0`, `decision_support_only=true`, and
`human_review_required=true`.

Observed compact summary:

| Command | Price area | Current risk summary | Forecast summary | Markdown result |
| --- | --- | --- | --- | --- |
| `python3 scripts/report_markdown_preview.py` | DK1 | available, medium, score 45 | available, 3 windows | Rendered title, metadata, summaries, no high-risk forecast-window finding, safety notes, limitations, and source notes. |
| `python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk` | DK2 | available, high, score 75 | available, 3 windows | Rendered high current risk, high-risk `24-48h` forecast window with `max_risk_score=80`, and human-review escalation actions. |
| `python3 scripts/report_markdown_preview.py --scenario missing-current-risk` | DK1 | unavailable | available, 3 windows | Rendered current-risk summary as unavailable and kept the forecast-window summary available. |
| `python3 scripts/report_markdown_preview.py --scenario missing-forecast` | DK1 | available, medium, score 45 | unavailable, 0 windows | Rendered forecast-window summary as unavailable and kept the current-risk summary available. |

Interpretation:

- `report-summary-v0` Markdown preview works locally with
  synthetic/caller-provided data.
- It prints Markdown to stdout only.
- It does not write files.
- It does not generate PDF files.
- It does not fetch data.
- It does not read or write a database.
- It does not expose an API.
- It does not use frontend code.
- It does not use ML or LLMs.
- It is read-only decision support only.
- It must not be used for automatic control, dispatch, or activation.

PDF export v0 now uses the stable report-summary and Markdown rendering path.
It remains manual, local, and read-only only.

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

## Forecast Window Synthetic Preview Script

`scripts/forecast_window_preview.py` provides a manual synthetic local preview
of `forecast-window-v0` using fixed `generated_at_utc` output and in-script
caller-provided rows only. It calls `build_forecast_window_forecast(...)` and
prints compact JSON by default.

Run it manually:

```bash
python3 scripts/forecast_window_preview.py
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

The `balanced` scenario covers all three windows with mixed low/medium-like
scores. The `high-risk` scenario includes a negative-price and
high-renewable-share row to demonstrate max-risk window aggregation. The
`empty-window` scenario leaves a matching-price-area window empty, returning
`risk_level` `unknown`.

This preview is not a historical backtest, not model validation, not statistical
calibration, and not evidence of production performance. It does not require
`DATABASE_URL`, read or write a database, run SQL, fetch Energi Data Service
data, call DMI/weather APIs, expose an API endpoint, run frontend code, create
ingestion jobs, use Azure, add secrets, add auth, train ML models, use LLMs,
control assets, dispatch, activate, or perform operational functionality.

### Observed Forecast Window Synthetic Preview Results

The following local synthetic commands were run:

```bash
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

All three outputs printed the synthetic-only warning and reported
`generated_at_utc=2026-01-01T00:00:00Z`,
`model_version=rule-engine-v0+forecast-window-v0`, and
`decision_support_only=true`.

Balanced scenario, `price_area=DK1`:

| Window | Row count | Risk level | Max risk score | Top reason codes |
| --- | ---: | --- | ---: | --- |
| `0-24h` | 2 | medium | 45 | `EXCHANGE_NET_NOT_USED_V0:2`, `LOW_PRICE:1`, `LOW_RENEWABLE_SHARE:1`, `MODERATE_RENEWABLE_SHARE:1`, `NORMAL_PRICE:1` |
| `24-48h` | 2 | low | 30 | `EXCHANGE_NET_NOT_USED_V0:2`, `ELEVATED_RENEWABLE_SHARE:1`, `MODERATE_PRICE:1`, `MODERATE_RENEWABLE_SHARE:1`, `NORMAL_PRICE:1` |
| `48-72h` | 2 | medium | 35 | `EXCHANGE_NET_NOT_USED_V0:2`, `ELEVATED_RENEWABLE_SHARE:1`, `LOW_PRICE:1`, `LOW_RENEWABLE_SHARE:1`, `NORMAL_PRICE:1` |

High-risk scenario, `price_area=DK2`: the `24-48h` window became `high` risk
with `row_count=2` and `max_risk_score=75`. The top reason codes showed the
intended high-risk inputs, including `NEGATIVE_PRICE:1` and
`HIGH_RENEWABLE_SHARE:1`, and demonstrated that the window risk level is based
on the maximum observed row risk score.

Empty-window scenario, `price_area=DK1`: the `24-48h` window had
`row_count=0`, `risk_level=unknown`, `average_risk_score=null`,
`max_risk_score=null`, and `top_reason_codes=[]`. This demonstrates the
insufficient caller-provided data path for an empty forecast window.

Interpretation:

- `forecast-window-v0` preview works locally with synthetic rows.
- It returns `0-24h`, `24-48h`, and `48-72h` windows.
- It is deterministic aggregation over caller-provided rows.
- It is not ML.
- It is not DMI/weather based yet.
- It does not fetch data.
- It does not read or write a database.
- `POST /api/forecast/preview` exposes the same caller-provided aggregation
  boundary for JSON requests only.
- It is not production forecast validation.

Safety notes:

- Synthetic local preview only.
- Read-only decision support only.
- Human review required.
- No database access.
- No live Energi Data Service polling.
- No DMI/weather calls.
- No backend or frontend servers.
- No scheduler.
- No Azure resources.
- No ML or LLM use.
- Must not be used for automatic control, dispatch, or activation.

## Local DB Read-Only Backtest Script

`scripts/risk_backtest_local_db.py` provides a manual local PostgreSQL
read-only backtest preview for `rule-engine-v0` using existing local
`spot_prices` and `power_balance` rows.

Run it manually against a local DB-API PostgreSQL URL:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/risk_backtest_local_db.py --price-area DK1
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/risk_backtest_local_db.py --price-area DK2 --limit 100 --pretty
```

The script:

- requires `DATABASE_URL`
- accepts only `postgresql://...` DB-API URLs
- refuses non-local hosts and allows only `localhost` or `127.0.0.1`
- reads latest rows from `spot_prices` and `power_balance` through existing
  SELECT-only query builders
- composes rows with `nearest_timestamp_v0_1` pairing through
  `compose_surplus_risk_input(...)`
- runs `evaluate_risk_backtest(rows)`
- prints compact JSON by default and indented JSON with `--pretty`
- reports `pairing_strategy: nearest_timestamp_v0_1`
- reports `decision_support_only: true` and `read_only: true`

Row pairing now uses deterministic `nearest_timestamp_v0_1` behavior. The
power-balance rows are the primary timeline, and each power-balance row is
paired with the nearest spot-price row by `timestamp_utc`. Ties are resolved by
the earlier spot-price timestamp, then original row order. If one table is
empty, remaining rows from the other table are still composed with the missing
side omitted. This improves on list-order pairing but remains a simple timestamp
pairing strategy, not audited historical alignment.

This is still a local technical validation helper, not full model validation,
not statistical calibration, and not evidence of production performance. It
does not fetch, clean, label, or audit a complete historical dataset.

### Observed Local DK1 Result After Nearest-Timestamp Pairing

The local read-only DB backtest was rerun against actual locally stored
EDS-derived rows for DK1 after `nearest_timestamp_v0_1` pairing was merged.

Local table counts before the backtest:

- `spot_prices`: `3`
- `power_balance`: `3`

Command run:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK1 --limit 10 --pretty
```

Observed output:

- `price_area`: `DK1`
- `limit`: `10`
- `read_only`: `true`
- `decision_support_only`: `true`
- `spot_price_rows_read`: `3`
- `power_balance_rows_read`: `3`
- `composed_rows`: `3`
- `pairing_strategy`: `nearest_timestamp_v0_1`
- `backtest_summary.total_rows`: `3`
- `backtest_summary.evaluated_rows`: `3`
- `backtest_summary.failed_rows`: `0`
- `backtest_summary.risk_level_counts.low`: `1`
- `backtest_summary.risk_level_counts.medium`: `2`
- `backtest_summary.risk_level_counts.high`: `0`
- `backtest_summary.average_risk_score`: `26.6667`
- `backtest_summary.average_confidence_score`: `1.0`
- `backtest_summary.reason_code_counts.NORMAL_PRICE`: `3`
- `backtest_summary.reason_code_counts.EXCHANGE_NET_NOT_USED_V0`: `3`
- `backtest_summary.reason_code_counts.HIGH_RENEWABLE_SHARE`: `2`
- `backtest_summary.reason_code_counts.ELEVATED_RENEWABLE_SHARE`: `1`
- `backtest_summary.missing_price_count`: `0`
- `backtest_summary.missing_generation_data_count`: `0`
- `backtest_summary.model_version`: `rule-engine-v0`

Interpretation:

- `nearest_timestamp_v0_1` pairing is active.
- On the tiny local DK1 sample, the risk distribution remained unchanged
  compared with the previous simple pairing run.
- This is expected because the local dataset only contains 3 composed rows.
- This is still technical validation, not full model validation.
- A larger historical dataset is required before drawing performance
  conclusions.

Safety notes:

- Local PostgreSQL only.
- SELECT/read-only only.
- No database writes.
- No live EDS polling.
- No backend or frontend server.
- No startup migrations.
- No production database.
- No Azure resources.
- No ML training.
- No LLM use.
- No automatic control, dispatch, activation, or operational functionality.

### Observed Local DK2 Result After Manual Local Ingest

DK2 was manually validated with tiny local Energi Data Service samples before
running the current-risk smoke test and local read-only DB backtest.

Local EDS dry-run validation:

- `DayAheadPrices` DK2 returned HTTP `200`.
- `DayAheadPrices` raw record count: `2`.
- `DayAheadPrices` normalized record count: `2`.
- `DayAheadPrices` SQL command count: `2`.
- `DayAheadPrices` committed: `false`.
- `ElectricityProdex5MinRealtime` DK2 returned HTTP `200`.
- `ElectricityProdex5MinRealtime` raw record count: `2`.
- `ElectricityProdex5MinRealtime` normalized record count: `2`.
- `ElectricityProdex5MinRealtime` SQL command count: `2`.
- `ElectricityProdex5MinRealtime` committed: `false`.

Confirmed local write validation:

- `DayAheadPrices` DK2 committed: `true`.
- `ElectricityProdex5MinRealtime` DK2 committed: `true`.
- Local PostgreSQL only.
- Manual confirmed local write only.

Local row counts after DK2 ingest:

- `spot_prices`:
  - `DK1`: `3`
  - `DK2`: `2`
- `power_balance`:
  - `DK1`: `3`
  - `DK2`: `2`

Current risk API smoke test:

```text
GET /api/risk/current?price_area=DK2
```

Observed result:

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

Command run:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK2 --limit 10 --pretty
```

Observed output:

- `price_area`: `DK2`
- `limit`: `10`
- `read_only`: `true`
- `decision_support_only`: `true`
- `pairing_strategy`: `nearest_timestamp_v0_1`
- `spot_price_rows_read`: `2`
- `power_balance_rows_read`: `2`
- `composed_rows`: `2`
- `backtest_summary.total_rows`: `2`
- `backtest_summary.evaluated_rows`: `2`
- `backtest_summary.failed_rows`: `0`
- `backtest_summary.risk_level_counts.low`: `2`
- `backtest_summary.risk_level_counts.medium`: `0`
- `backtest_summary.risk_level_counts.high`: `0`
- `backtest_summary.average_risk_score`: `20.0`
- `backtest_summary.average_confidence_score`: `1.0`
- `backtest_summary.reason_code_counts.NORMAL_PRICE`: `2`
- `backtest_summary.reason_code_counts.MODERATE_RENEWABLE_SHARE`: `2`
- `backtest_summary.reason_code_counts.EXCHANGE_NET_NOT_USED_V0`: `2`
- `backtest_summary.missing_price_count`: `0`
- `backtest_summary.missing_generation_data_count`: `0`
- `backtest_summary.model_version`: `rule-engine-v0`

Interpretation:

- DK2 local read-only path is now validated.
- The DK2 current risk endpoint returned low risk on the tiny local sample.
- The DK2 local DB backtest returned low risk for both composed rows.
- This is still technical validation, not full model validation.
- The dataset is tiny and not enough for performance conclusions.

Safety notes:

- Local PostgreSQL only.
- Manual validation only.
- SELECT/read-only backtest only.
- No production database.
- No Azure resources.
- No startup migrations.
- No automated ingestion job.
- No live polling loop.
- No ML training.
- No LLM use.
- No automatic control, dispatch, activation, or operational functionality.

## Reported Metrics

`evaluate_risk_backtest(rows)` reports:

- `total_rows`: number of supplied rows
- `evaluated_rows`: rows successfully evaluated by `rule-engine-v0`
- `failed_rows`: rows rejected by validation or other row-level errors
- `risk_level_counts`: counts for `low`, `medium`, and `high`
- `average_risk_score`: average score across evaluated rows
- `average_confidence_score`: average confidence across evaluated rows
- `reason_code_counts`: aggregate reason-code frequencies
- `missing_price_count`: evaluated rows with missing price data
- `missing_generation_data_count`: evaluated rows with missing production or
  renewable generation data
- `failed_row_errors`: row index, error type, and error message for failed rows
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`

Invalid rows do not stop the whole evaluation. The evaluator captures row-level
errors and continues with remaining rows.

## Limitations

- The evaluator only summarizes deterministic `rule-engine-v0` outputs.
- It does not fetch, clean, or validate a historical dataset.
- The local DB backtest script reads local rows only and pairs spot-price and
  power-balance rows with simple nearest-timestamp matching.
- No outcome labels are used, so the backtest cannot measure predictive
  correctness.
- Tiny local samples can be useful for smoke validation but are too small for
  statistical conclusions.
- It does not train a model or tune thresholds.
- It does not calculate precision, recall, false positives, false negatives,
  MAE, RMSE, or calibrated probabilities because no labeled historical
  evaluation dataset has been run.
- Results depend entirely on the caller-provided local rows and the current
  rule-engine behavior.
- Average scores are descriptive summaries of evaluated rows, not forecasts.

## Safety Boundary

The evaluator is read-only decision-support tooling. It does not connect to a
database, execute SQL, call live APIs, poll external services, create ingestion
jobs, or use LLMs.

It does not perform or trigger automatic control, dispatch, activation,
closed-loop workflows, asset connections, plant/device commands, or live
control signals.

The synthetic preview script follows the same boundary: it uses hardcoded local
rows only and does not require `DATABASE_URL`, fetch live Energi Data Service
data, call HTTP APIs, run backend or frontend servers, use Azure, train ML
models, or add operational behavior.

The local DB backtest script narrows the database exception to manual local
PostgreSQL reads only. It executes generated `SELECT` queries only, refuses
non-local database hosts, performs no writes, does not call live Energi Data
Service APIs, does not poll external services, does not add FastAPI endpoints,
does not modify backend startup, does not add frontend code, does not create
ingestion jobs, and does not perform control, dispatch, activation, or
operational workflows.

## Audit Writer Service Boundary

An audit writer service foundation now exists at `backend/app/audit/writer.py`
for explicit `audit-event-v0` inserts. It is outside the backtest path and does
not change backtest behavior, scoring, forecasting, report generation, or
frontend behavior.

The writer requires an explicit database connection, does not create database
connections, does not read `DATABASE_URL`, and validates
`decision_support_only` plus the full read-only human-review safety boundary
before executing the existing repository-built parameterized insert. It is not
wired to API, frontend, report, PDF, scheduler, or automatic audit logging
flows.

Writer unit tests use fake connection and cursor objects only. No live database
writes are performed by those tests.

## Runtime Audit Event Factory Boundary

`backend/app/audit/runtime_events.py` now provides pure constructors for
standardized `audit-event-v0` dictionaries for future runtime read-only
actions. It is outside the backtest path and does not change backtest behavior,
scoring, forecasting, reporting, PDF generation, API behavior, or frontend
behavior.

The factory does not access a database, does not write audit events, does not
call the audit writer service, does not expose an endpoint, and does not add
automatic audit logging. Runtime integration remains deferred.
