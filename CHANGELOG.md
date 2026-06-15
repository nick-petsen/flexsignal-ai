# Changelog

## v0.1.0 - TODO

- Added `backend/app/audit/writer.py`, an explicit audit writer service
  foundation for `audit-event-v0`, plus `backend/tests/test_audit_writer.py`.
  The writer requires a caller-provided database connection, validates
  `event_version=audit-event-v0`, `decision_support_only=true`, required event
  identity fields, and the full read-only human-review safety boundary before
  executing SQL. It uses the existing audit repository parameterized insert SQL
  builder and returns a structured result with event id, event type, table,
  row count, conflict behavior, write-performed flag,
  safety-boundary-preserved flag, and warnings. It does not create database
  connections, does not read `DATABASE_URL`, does not add FastAPI endpoints,
  and is not wired into API, frontend, report, PDF, scheduler, auth, external
  data, automatic audit logging, control, dispatch, activation, or operational
  flows. Unit tests use fake connection/cursor objects only and perform no live
  database writes.
- Documented the manually executed local audit DB write smoke result for the
  first actual local Postgres `audit_events` write. A human ran
  `DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head`,
  then ran
  `python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty`
  twice. Alembic used `PostgresqlImpl`, assumed transactional DDL, migrated
  `0001_initial_schema` to `0002_audit_events`, added the audit-event-v0
  persistence foundation, and succeeded. The first smoke reported
  `event_id=audit_evt_f8ea1513efa7fa0067b0ca04`,
  `event_type=report_pdf_exported`, `database_write_performed=true`,
  `dry_run=false`, `execute_requested=true`, `inserted_attempts=2`,
  `local_database_only=true`, `rowcount_first_insert=1`,
  `rowcount_second_insert=0`, `table=audit_events`,
  `verify_read_performed=true`, `warnings=[]`, and
  `conflict_behavior=ON CONFLICT (event_id) DO NOTHING`; `verified_row` was
  returned by `event_id`. The second smoke used the same event id and event
  type, returned `rowcount_first_insert=0` and `rowcount_second_insert=0`,
  and returned `verified_row`, confirming idempotency across repeated script
  executions. Documented that the verified row included
  `event_version=audit-event-v0`, `action=preview_report_pdf_export`,
  `actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
  `decision_support_only=true`, `resource_type=report_pdf`,
  `resource_id=report-summary-v0:DK1:synthetic-pdf`, and metadata
  `local_only=true`, `output_format=pdf`, `price_area=DK1`,
  `report_version=report-summary-v0`, and `synthetic_preview_only=true`.
  Documented the timezone note that the deterministic event read back
  `occurred_at_utc` as `2026-01-01T01:00:00+01:00`, interpreted as
  database/session timezone rendering of the stored `timestamptz` instant and
  not a smoke blocker. Documented that the raw `DATABASE_URL` was not printed
  and the safety boundary preserved read-only decision support, no automatic
  control, no dispatch, no activation, no operational energy-system
  integration, and human review required. Clarified that local audit DB write,
  idempotency, and verify-read are now manually verified, but production audit
  persistence is not enabled, automatic audit logging was not added, and API,
  frontend, report, and PDF flows remain unwired. No code, backend behavior,
  frontend behavior, database writes, migrations, endpoints, scheduler, Azure
  infrastructure, auth, secrets, EDS/DMI calls, ML/LLM, control, dispatch,
  activation, or operational functionality was added by this documentation
  change.
- Added `scripts/audit_db_write_smoke.py`, a manual local-only audit DB write
  smoke script for one deterministic synthetic `audit-event-v0`. The script
  imports `build_audit_event(...)` and the audit repository SQL builder, uses
  fixed `occurred_at_utc=2026-01-01T00:00:00Z`, supports `--pretty`,
  `--event-type`, `--database-url`, `--execute`, and `--verify-read`, and
  defaults to dry-run without connecting to a database. Real writes require
  both `--execute` and an explicit local `--database-url`; localhost,
  127.0.0.1, and local socket-style URLs are accepted, while obvious
  remote/cloud URLs are refused. Executed smoke writes only target
  `audit_events`, run the same parameterized
  `ON CONFLICT (event_id) DO NOTHING` insert twice, commit, and optionally
  verify-read by `event_id`. Added focused unit tests and updated README,
  scripts README, human oversight, model card, and backtest docs. This does
  not add FastAPI endpoints, frontend code, automatic audit logging,
  report/PDF/API/frontend integration, scheduler behavior, Azure
  infrastructure, auth, secrets, EDS/DMI calls, ML, LLMs, control, dispatch,
  activation, or operational functionality.
- Documented observed manual local audit DB write smoke script validation
  results. The documented commands/checks were
  `python3 -m py_compile scripts/audit_db_write_smoke.py backend/tests/test_audit_db_write_smoke.py`,
  `python -m pytest tests/test_audit_db_write_smoke.py -q`,
  `python -m pytest`, `python3 scripts/audit_db_write_smoke.py`,
  `python3 scripts/audit_db_write_smoke.py --pretty`,
  `python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty`,
  `python3 scripts/audit_db_write_smoke.py --execute`,
  `python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://remote.example.com/flexsignal_ai`,
  forbidden-pattern grep on the script and test, and `git diff --check`.
  Observed results: `py_compile` passed; focused smoke tests passed with
  `7 passed`; the full backend suite passed with `317 passed, 1 warning`;
  default dry-run, `--pretty` dry-run, and
  `forecast_preview_requested` dry-run passed; `--execute` without
  `--database-url` failed safely with exit code `2`; the remote database URL
  command failed safely with exit code `2`; forbidden-pattern grep returned no
  matches; and `git diff --check` passed. Documented that no live DB writes
  were performed during those guardrail checks, the raw `DATABASE_URL` is not
  printed, `event_id` is deterministic, output includes `dry_run`,
  `execute_requested`, `database_write_performed`, `verify_read_performed`,
  `local_database_only`, `event_id`, `event_type`, `table: audit_events`,
  `inserted_attempts`, `conflict_behavior`, `safety_boundary`, and `warnings`,
  and the full read-only/human-review safety boundary is preserved. A later
  documentation-only entry records the first actual manual local Postgres
  write smoke. Production audit persistence is not enabled, no
  API/frontend/report/PDF flow is wired to audit persistence, and no automatic
  audit logging exists. Future production DB writes require explicit review.
  This change is documentation only.
- Added `scripts/audit_persistence_preview.py`, a manual local audit
  persistence dry-run preview. The script imports `build_audit_event(...)` and
  the audit repository SQL builder, uses fixed
  `occurred_at_utc=2026-01-01T00:00:00Z`, supports `--pretty`, supports
  `--event-type` values `forecast_preview_requested`,
  `current_risk_viewed`, `report_summary_built`,
  `report_markdown_rendered`, and `report_pdf_exported`, and defaults to
  `report_pdf_exported`. It prints JSON with `dry_run=true`,
  `database_write_performed=false`, `requires_database_url=false`, the event,
  and a repository-built `audit_events` persistence plan with idempotency key
  and `ON CONFLICT (event_id) DO NOTHING`. Updated README, scripts README,
  human oversight, model card, and backtest docs. This does not persist audit
  events, access a database, require `DATABASE_URL`, run SQL, expose an API,
  use frontend code, write files, generate PDFs, call EDS/DMI, use ML, use
  LLMs, add scheduling, add Azure infrastructure, add auth, add secrets, add
  automatic audit logging, or add control, dispatch, activation, or
  operational functionality.
- Documented observed manual audit persistence dry-run preview validation
  results. The documented commands/checks were
  `python3 -m py_compile scripts/audit_persistence_preview.py`,
  `python3 scripts/audit_persistence_preview.py`,
  `python3 scripts/audit_persistence_preview.py --pretty`,
  `python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty`,
  `python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty`,
  `python3 scripts/audit_persistence_preview.py --event-type invalid-event`,
  forbidden-pattern grep on `scripts/audit_persistence_preview.py`, and
  `git diff --check`. Observed results: `py_compile` passed; the default
  command printed compact JSON; `--pretty` printed indented JSON; both valid
  single-event dry-runs passed; the invalid event type failed safely with exit
  code `2` and argparse invalid-choice output; forbidden-pattern grep returned
  no matches; and `git diff --check` passed. Documented output fields
  `dry_run=true`, `database_write_performed=false`,
  `requires_database_url=false`, `event`, and `persistence_plan`, including
  `event_version=audit-event-v0`, deterministic `audit_evt_...` event id,
  fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
  `actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
  `decision_support_only=true`, safe metadata only,
  `synthetic_preview_only=true`, `local_only=true`, the full read-only
  human-review safety boundary, the `audit_events` target, SQL/SQL preview,
  parameter keys/params, `event_id` idempotency key, and
  `ON CONFLICT (event_id) DO NOTHING`. Clarified that this works locally with
  synthetic/caller-provided data and demonstrates persistence planning only;
  it does not prove live DB persistence, perform database writes, run SQL,
  connect to a database, expose API/frontend/report/PDF flows, generate PDFs,
  call EDS/DMI, use ML/LLMs, add automatic audit logging, or add operational
  functionality. Future controlled local audit persistence write testing must
  be separate and reviewed. This change is documentation only.
- Documented audit DB persistence foundation validation and CI resolution
  results for PR #87. Clarified that `audit-event-v0`, the manual audit-event
  preview script, and preview-result docs already existed before this step,
  and that PR #87 added schema/repository readiness only: Alembic migration
  `backend/alembic/versions/0002_audit_events.py` and
  `backend/app/audit/repository.py`. Documented the `audit_events` schema with
  `event_id` as the primary/idempotency key, event version/type, actor,
  occurrence time, resource, action, outcome, `decision_support_only`, JSONB
  `safety_boundary`, JSONB `metadata`, `created_at_utc`, and indexes for
  occurrence time, event type, resource lookup, and actor lookup. Documented
  repository validation before persistence planning, parameterized INSERT SQL,
  and `ON CONFLICT (event_id) DO NOTHING`, with no live database writes during
  validation.
- Documented initial PR validation for the audit DB persistence foundation:
  backend tests passed with `310 passed, 1 warning`, `py_compile` passed for
  `backend/app/audit/events.py` and `backend/app/audit/repository.py`,
  safety-boundary grep matched only `no_automatic_control`, `no_dispatch`, and
  `no_activation`, and `git diff --check` passed.
- Documented the GitHub backend-tests issue and resolution before merge. The
  initial CI failures were
  `tests/test_api_energy.py::test_app_exposes_no_mutating_write_methods` and
  `tests/test_api_risk.py::test_app_import_without_database_url_still_exposes_current_risk_route`;
  CI/import context was missing exposed routes `/api/risk/current`,
  `/api/risk/preview`, and `/api/forecast/preview`. The issue was interpreted
  as route exposure under newer FastAPI/Starlette test behavior, not live
  database writes or audit persistence execution. `backend/app/main.py` was
  updated with a small route-registration helper so `app.routes` exposes
  concrete paths in the test environment while keeping `DATABASE_URL`
  validation request-time only. Endpoint logic was not changed. No new API
  behavior, DB writes, scheduler, frontend, control, dispatch, activation, or
  operational behavior was added. The branch was not merged while
  backend-tests were red.
- Documented post-fix validation: focused route tests passed with
  `2 passed, 1 warning`, the full backend suite passed with
  `310 passed, 1 warning`, `git diff --check` passed, the PR diff was checked
  to exclude `.pyc`, virtualenv, cache, and generated files, GitHub
  backend-tests were re-run and green before merge, and PR #87 was merged only
  after backend-tests were green. Documented the final merged files:
  `backend/alembic/versions/0002_audit_events.py`,
  `backend/app/audit/repository.py`, `backend/app/main.py`,
  `backend/tests/test_audit_event_repository.py`, `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`,
  `docs/BACKTEST_RESULTS.md`, and `CHANGELOG.md`. Clarified that the audit DB
  persistence foundation does not prove production audit persistence, identify
  real users through Entra ID, or automatically write events. Future work may
  add a fake-executor/local-dry-run persistence preview, but automatic audit
  logging and frontend/report-download persistence wiring remain deferred
  until explicit review. This change is documentation only.
- Added audit-event database persistence foundation for `audit-event-v0`.
  New Alembic migration `0002_audit_events.py` defines an `audit_events`
  table with `event_id` as the primary/idempotency key, event version/type,
  actor, occurrence time, resource, action, outcome,
  `decision_support_only`, JSONB `safety_boundary`, JSONB `metadata`,
  `created_at_utc`, and indexes for occurrence time, event type, resource, and
  actor. New `backend/app/audit/repository.py` validates
  `build_audit_event(...)` dictionaries, preserves the required read-only
  safety boundary, serializes JSONB fields as parameters, and builds
  parameterized `ON CONFLICT (event_id) DO NOTHING` insert SQL. Added focused
  repository/migration tests and updated README, human oversight, model card,
  and backtest docs. This does not add FastAPI endpoints, frontend UI,
  automatic audit logging, report/PDF persistence wiring, scheduled logging,
  auth/Entra integration, Azure infrastructure, secrets, ML/LLM behavior,
  live API calls, live database writes, or control, dispatch, activation, or
  operational functionality. Future work can wire explicit read-only flows to
  audit persistence only after review.
- Documented observed manual audit-event preview validation results. The
  documented checks were
  `python3 -m py_compile scripts/audit_event_preview.py`,
  `python3 scripts/audit_event_preview.py`,
  `python3 scripts/audit_event_preview.py --pretty`,
  `python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty`,
  `python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty`,
  `python3 scripts/audit_event_preview.py --event-type invalid-event`,
  forbidden-pattern grep on `scripts/audit_event_preview.py`, and
  `git diff --check`. Observed results: `py_compile` passed; the default
  command printed compact JSON with an `events` array; `--pretty` printed
  indented JSON; the two valid single-event commands each printed one event;
  the invalid event type failed safely with exit code `2` and a clear argparse
  invalid-choice validation error; forbidden-pattern grep returned no matches;
  and `git diff --check` passed. Documented that preview events covered
  `forecast_preview_requested`, `current_risk_viewed`,
  `report_summary_built`, `report_markdown_rendered`, and
  `report_pdf_exported`; included `event_version=audit-event-v0`,
  deterministic `audit_evt_...` ids, fixed
  `occurred_at_utc=2026-01-01T00:00:00Z`,
  `actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
  `decision_support_only=true`, safe metadata only,
  `synthetic_preview_only=true`, `local_only=true`, and the full
  read-only/human-review `safety_boundary`. Clarified that audit preview works
  locally with synthetic/caller-provided data and demonstrates future
  read-only decision-support audit-event shape, but does not persist events,
  prove database audit logging, connect auth or actor identity providers,
  create operational logs, or provide production audit persistence. Audit
  persistence can be considered next only as a separate reviewed module, with
  no automatic control, dispatch, activation, scheduler, or operational
  functionality. This change is documentation only.
- Added `scripts/audit_event_preview.py`, a manual synthetic local JSON
  preview for `audit-event-v0`. The script imports `build_audit_event(...)`
  from `backend/app/audit/events.py`, uses fixed
  `occurred_at_utc=2026-01-01T00:00:00Z`, supports compact JSON by default
  plus `--pretty`, supports `--event-type` values
  `forecast_preview_requested`, `current_risk_viewed`,
  `report_summary_built`, `report_markdown_rendered`,
  `report_pdf_exported`, and `all`, defaults to `all`, and uses
  `actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`, and
  `decision_support_only=true`. The `all` mode prints an `events` array; a
  single event type prints one `event` object. Metadata is synthetic and safe
  only, including `price_area`, relevant `report_version`, relevant
  `output_format`, `synthetic_preview_only`, and `local_only`. Updated
  `scripts/README.md`, `README.md`, `docs/HUMAN_OVERSIGHT.md`,
  `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md` with usage examples,
  safety boundaries, and deferred persistence guidance. This does not persist
  audit logs yet, write files, access a database, run SQL, expose an API, use
  frontend code, call EDS or DMI/weather APIs, use ML, use LLMs, add a
  scheduler, add Azure infrastructure, add auth or secrets, or perform
  automatic control, dispatch, activation, closed-loop workflows, live control
  signals, autonomous decisions, or operational energy-system integration.
  Future audit work should document audit preview results first; database
  persistence remains a separate reviewed module.
- Added `audit-event-v0`, a pure backend Python in-memory audit event
  foundation for read-only decision-support actions. New
  `backend/app/audit/events.py` exposes `build_audit_event(...)`, validates
  explicit event types, actor types, outcomes, timezone-aware
  `occurred_at_utc`, non-empty resource/action fields, safe JSON-compatible
  metadata, and secret-like metadata keys, and returns deterministic
  `audit_evt_...` ids with an explicit safety boundary. Added focused tests and
  docs. This does not persist audit logs yet, write files, expose an API, read
  or write a database, call EDS or DMI/weather APIs, use ML, use LLMs, add
  scheduling, add Azure infrastructure, add auth or secrets, or perform
  automatic control, dispatch, activation, closed-loop workflows, live control
  signals, autonomous decisions, or operational energy-system integration.
  Manual/local audit preview is documented separately; database persistence
  should follow later only in a separate reviewed module.
- Documented observed manual/local PDF export v0 smoke-test results. The
  validation covered `standard`, `high-risk`, `missing-current-risk`, and
  `missing-forecast` synthetic/caller-provided scenarios through the
  `report-summary-v0` to Markdown to PDF path. Observed temporary outputs were
  `/tmp/flexsignal_report_preview.pdf` at `9697` bytes,
  `/tmp/flexsignal_report_high_risk.pdf` at `9930` bytes,
  `/tmp/flexsignal_report_missing_current.pdf` at `9263` bytes, and
  `/tmp/flexsignal_report_missing_forecast.pdf` at `6918` bytes. All started
  with `%PDF`, were larger than `1000` bytes, were removed after validation,
  and were not committed. Documented that backend tests passed with
  `257 passed, 1 warning`, `py_compile` passed, `git diff --check` passed,
  manual PDF preview runs passed, PDF byte/header checks passed, repository PDF
  checks passed, and grep found only required safety wording and no forbidden
  integration imports. Clarified that PDF export v0 remains manual/local
  read-only decision support only: no API endpoint, no frontend download, no
  live data, no database read/write, no EDS or DMI/weather API calls, no
  scheduler, no ML or LLM use, no automatic report jobs, and no automatic
  control, dispatch, activation, autonomous decisions, or operational
  energy-system integration. This change is documentation only.
- Added manual local PDF export v0 for `report-summary-v0`. New
  `backend/app/reporting/pdf.py` exposes
  `render_report_markdown_pdf_bytes(...)`, which accepts caller-provided
  Markdown and returns PDF bytes without writing files, fetching data, reading
  or writing a database, exposing an API, using frontend code, using ML, using
  LLMs, or adding operational behavior. New
  `scripts/report_pdf_preview.py` builds synthetic/caller-provided
  `report-summary-v0` data, renders Markdown, renders PDF bytes, requires
  explicit `--output PATH`, refuses overwrite without `--force`, and prints a
  compact JSON summary. Added focused PDF renderer and script tests, added
  `reportlab` to backend dependencies, exported the renderer from
  `app.reporting`, and updated README, scripts README, model card, and
  backtest notes. This remains manual/local read-only decision support only
  and must not be used for automatic control, dispatch, or activation.
- Added `scripts/report_markdown_preview.py`, a manual synthetic local
  Markdown preview for `report-summary-v0`. The script imports
  `build_report_summary(...)` from `backend/app/reporting/summary.py`, imports
  `render_report_summary_markdown(...)` from
  `backend/app/reporting/markdown.py`, uses fixed
  `generated_at_utc=2026-01-01T00:00:00Z`, supports
  `--price-area DK1|DK2`, and includes `standard`, `high-risk`,
  `missing-current-risk`, and `missing-forecast` scenarios over in-script
  synthetic/caller-provided sample data only. It prints Markdown to stdout,
  writes no files, generates no PDF files, fetches no data, accesses no
  database, runs no SQL, exposes no API, uses no frontend code, uses no ML or
  LLMs, and adds no scheduler, Azure, auth, secrets, control, dispatch,
  activation, or operational functionality. Updated `scripts/README.md`,
  `README.md`, `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md` with usage
  examples, safety boundaries, and observed local synthetic preview results.
- Documented observed local results from the manual synthetic
  `scripts/report_markdown_preview.py` commands only:
  `python3 scripts/report_markdown_preview.py`,
  `python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk`,
  `python3 scripts/report_markdown_preview.py --scenario missing-current-risk`,
  and
  `python3 scripts/report_markdown_preview.py --scenario missing-forecast`.
  All four runs printed the synthetic-only warning to stderr, rendered
  Markdown to stdout only, used
  `generated_at_utc=2026-01-01T00:00:00Z`,
  `report_version=report-summary-v0`, `decision_support_only=true`, and
  `human_review_required=true`, and included title, report metadata,
  current-risk summary, forecast-window summary, key findings, recommended
  human actions, safety notes, limitations, and source notes. The standard DK1
  run rendered available medium current risk with score `45` and three
  forecast windows. The high-risk DK2 run rendered available high current risk
  with score `75`, a high-risk `24-48h` forecast window with
  `max_risk_score=80`, human-review actions, and safety notes prohibiting
  automatic control, dispatch, and activation. The missing-current-risk run
  rendered current risk as unavailable, kept the forecast summary available,
  included `missing or incomplete current risk input`, and did not crash. The
  missing-forecast run rendered the forecast window summary as unavailable,
  kept current risk available, included `missing or incomplete forecast input`,
  and did not crash. Clarified that the Markdown preview works locally with
  synthetic/caller-provided data, renders `report-summary-v0` to readable
  Markdown, does not write files, does not generate PDF files, does not fetch
  data, does not read or write a database, does not expose an API, does not
  use frontend code, does not use ML or LLMs, remains read-only decision
  support only, and must not be used for automatic control, dispatch, or
  activation. Documented the next step as PDF export v0 using the stable
  report-summary and Markdown rendering path while remaining manual, local,
  and read-only first. This change is documentation only.
- Added `render_report_summary_markdown(...)`, a pure backend Python Markdown
  renderer for caller-provided `report-summary-v0` dictionaries. It returns a
  deterministic Markdown string with title, report metadata, current-risk
  summary, forecast-window summary, key findings, recommended human actions,
  safety notes, limitations, and source notes. Missing current-risk or forecast
  summaries render as clear unavailable sections, and optional missing fields
  use safe fallback text. Added tests covering title and metadata rendering,
  current-risk fields, all three forecast windows, high-risk window output,
  missing-summary handling, required safety wording, deterministic output, no
  file writing, and absence of external runtime or document-generation
  imports. Updated README, model card, and backtest notes to document that the
  renderer does not generate PDF files, write files, fetch data, access a
  database, expose an API, use frontend code, use ML, use LLMs, or add
  automatic control, dispatch, activation, or operational functionality.
- Documented observed local results from the manual synthetic
  `scripts/report_summary_preview.py` commands only:
  `python3 scripts/report_summary_preview.py --pretty`,
  `python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty`,
  `python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty`,
  and
  `python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty`.
  All runs printed the synthetic-only warning and reported
  `generated_at_utc=2026-01-01T00:00:00Z`,
  `report_version=report-summary-v0`, `decision_support_only=true`, and
  `human_review_required=true`. The standard DK1 run returned available
  medium current risk with score `45`, three forecast windows, no high-risk
  forecast window, and recommended actions requiring human review and
  prohibiting automatic control, dispatch, or activation. The high-risk DK2
  run returned available high current risk with score `75`, a high-risk
  `24-48h` forecast window with `max_risk_score=80`, high-risk key findings,
  and human-review escalation actions. The missing-current-risk run marked
  `current_risk_summary.status=unavailable`, added the limitation
  `missing or incomplete current risk input`, and kept the forecast summary
  available. The missing-forecast run marked
  `forecast_window_summary.status=unavailable`, added the limitation
  `missing or incomplete forecast input`, and kept the current-risk summary
  available. Clarified that the preview creates deterministic report payloads
  from synthetic/caller-provided data only; it does not generate PDF files,
  fetch data, read or write a database, expose an API, use frontend code, use
  ML, use LLMs, or perform automatic control, dispatch, activation, or
  operational functionality. Documented the next step as Markdown report
  rendering before later PDF export. This change is documentation only.
- Added `scripts/report_summary_preview.py`, a manual synthetic local JSON
  preview for `report-summary-v0`. The script imports
  `build_report_summary(...)` directly from `backend/app/reporting/summary.py`,
  uses fixed `generated_at_utc=2026-01-01T00:00:00Z`, supports compact JSON by
  default plus `--pretty`, supports `--price-area DK1|DK2`, and includes
  `standard`, `high-risk`, `missing-current-risk`, and `missing-forecast`
  scenarios over in-script caller-provided sample data only. The high-risk
  scenario demonstrates high-risk key findings and recommended human actions;
  the missing-input scenarios keep generation safe by marking the relevant
  summary unavailable. Documented usage in `scripts/README.md`, `README.md`,
  `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md`. This script does not
  generate PDF files, fetch data, access a database, run SQL, expose an API,
  run frontend code, call Energi Data Service, call DMI/weather APIs, add a
  scheduler, use Azure, add auth or secrets, train ML models, use LLMs, or add
  automatic control, dispatch, activation, or operational functionality.
- Added `report-summary-v0`, a pure backend Python deterministic
  data-structure builder for read-only decision-support reporting. It accepts
  caller-provided current-risk output and caller-provided `forecast-window-v0`
  output only, validates `DK1`/`DK2` and timezone-aware `generated_at_utc`,
  returns a deterministic report id based on price area, generated timestamp,
  and report version, and includes current-risk summary, forecast-window
  summary, model versions, key findings, deduplicated recommended human
  actions, safety notes, limitations, and source notes. Missing or incomplete
  current-risk or forecast input is handled as an unavailable summary with an
  explicit limitation instead of crashing. Added focused tests for valid
  reports, deterministic IDs, validation, unavailable summaries, high and
  unknown forecast findings, action deduplication, decision-support flags,
  safety notes, object inputs, and absence of DB/API/network/PDF dependencies.
  Updated README, model card, and backtest notes to document that this is a
  data structure only: it does not generate PDF files yet, fetch data, read or
  write a database, expose an API, use ML, use LLMs, add scheduler/auth/Azure
  behavior, or perform automatic control, dispatch, activation, or operational
  functionality. The next reporting step should be a Markdown/preview script,
  followed later by PDF rendering.
- Documented manual frontend Forecast preview card smoke-test results after
  the local CORS preflight fix was merged. The backend was started without
  `DATABASE_URL`, the frontend was started locally, and only the Forecast
  preview card was used; spot prices, power balance, and current surplus risk
  cards were not used. The card was visible with the read-only badge and
  synthetic/caller-provided preview warning, showed no forecast data before
  the manual "Load forecast preview" click, then displayed
  `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, `generated_at_utc=2026-01-01T00:00:00Z`, and
  `0-24h`, `24-48h`, and `48-72h` windows. DK1 returned `0-24h` low risk with
  `row_count=1`, `max_risk_score=30`, `average_risk_score=30`, and reason
  codes including `EXCHANGE_NET_NOT_USED_V0`, `MODERATE_PRICE`, and
  `MODERATE_RENEWABLE_SHARE`; `24-48h` high risk with `row_count=1`,
  `max_risk_score=75`, `average_risk_score=75`, reason codes including
  `EXCHANGE_NET_NOT_USED_V0`, `HIGH_RENEWABLE_SHARE`, and `NEGATIVE_PRICE`,
  and a recommended human action requiring human review; and `48-72h` low risk
  with `row_count=1`, `max_risk_score=10`, `average_risk_score=10`, and reason
  codes including `ELEVATED_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0`, and
  `NORMAL_PRICE`. Switching the selected price area to DK2 and clicking the
  manual button returned forecast-window data again with the same three
  windows and decision-support-only fields without frontend error, confirming
  that the selected price area can be used by the frontend helper for this
  flow. Clarified that the prior browser failure was caused by `OPTIONS`
  preflight returning `400`, and the successful frontend load from
  `POST /api/forecast/preview` practically confirms the local CORS preflight
  path for the Forecast preview card. This is local smoke-test documentation
  only: no ingestion, database access, SQL, database writes, live Energi Data
  Service calls, DMI/weather calls, scheduler, Azure infrastructure, auth,
  secrets, ML training, LLM use, automatic control, dispatch, activation, or
  operational functionality was run or added; it remains synthetic/caller-
  provided preview data only, read-only decision support for human review, and
  not production forecast validation.
- Added a manual read-only frontend "Forecast preview" dashboard card. The
  card uses the selected `DK1`/`DK2` price area, calls
  `POST /api/forecast/preview` only after the user clicks "Load forecast
  preview", posts deterministic synthetic/caller-provided demo rows with
  timezone-aware `generated_at_utc`, and displays the returned `0-24h`,
  `24-48h`, and `48-72h` windows with risk level, row count, max and average
  risk scores, top reason codes, recommended human action,
  `decision_support_only`, and `model_version`. The frontend helper uses only
  the backend API base URL helper. It does not auto-load, poll, call Energi
  Data Service or DMI/weather APIs from the browser, read or write a database,
  add backend endpoints, run SQL, schedule jobs, add Azure infrastructure,
  add auth or secrets, train ML, use LLMs, or add automatic control, dispatch,
  activation, closed-loop, or operational functionality. This remains
  synthetic/caller-provided preview data only, read-only decision support, and
  not production forecast validation.
- Documented manual smoke-test results for `POST /api/forecast/preview` only.
  The backend was started without `DATABASE_URL`, confirming that
  caller-provided forecast rows can be summarized without database access. The
  valid DK1 request returned HTTP 200 with `price_area=DK1`,
  `generated_at_utc=2026-01-01T00:00:00Z`,
  `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, and three windows: `0-24h` with
  `row_count=1`, `risk_level=low`, `max_risk_score=30`,
  `average_risk_score=30.0`, and reason codes including `MODERATE_PRICE` and
  `MODERATE_RENEWABLE_SHARE`; `24-48h` with `row_count=1`,
  `risk_level=high`, `max_risk_score=75`, `average_risk_score=75.0`, and
  reason codes including `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`; and
  `48-72h` with `row_count=0`, `risk_level=unknown`,
  `max_risk_score=null`, `average_risk_score=null`, and
  `average_confidence_score=0.0`. The high-risk DK2 request returned HTTP 200,
  `price_area=DK2`, `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, and a `24-48h` high-risk window with
  `row_count=1`, `max_risk_score=75`, `average_risk_score=75.0`, and reason
  codes including `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`; the `0-24h` and
  `48-72h` windows were `unknown` because `row_count=0`. Invalid
  `price_area=SE3` and timezone-naive `generated_at_utc` requests returned
  validation errors indicating that input should be `DK1` or `DK2` and that
  `generated_at_utc` must be timezone-aware. Clarified that this demonstrates
  deterministic caller-provided `0-24h`, `24-48h`, and `48-72h` window
  summaries, max-risk aggregation, empty-window `unknown` handling, and input
  validation only. No frontend was used; no ingestion, database access, SQL,
  database writes, live Energi Data Service calls, DMI/weather calls,
  scheduler, Azure infrastructure, auth, secrets, ML training, LLM use,
  automatic control, dispatch, activation, or operational functionality was
  used or added. This is read-only decision support, not production forecast
  validation.
- Added `POST /api/forecast/preview`, a read-only FastAPI wrapper around
  `forecast-window-v0` for caller-provided DK1/DK2 rows only. The endpoint
  returns deterministic `0-24h`, `24-48h`, and `48-72h` summaries from
  `build_forecast_window_forecast(...)`, validates supported price areas and
  timezone-aware request timestamps, allows empty caller-provided row lists to
  return three `unknown` windows, and preserves decision-support-only safety
  wording. Added API tests for valid previews, empty rows, invalid price areas,
  timezone-naive timestamps, absence of DB/API/network/job behavior, existing
  risk endpoint compatibility, and safety wording. Documented that the endpoint
  does not fetch EDS or DMI/weather data, read or write a database, persist
  payloads, start jobs, train ML, use LLMs, add frontend code, add auth, add
  Azure infrastructure, or perform automatic control, dispatch, activation, or
  operational workflows.
- Documented observed results from the synthetic local
  `scripts/forecast_window_preview.py` commands only:
  `python3 scripts/forecast_window_preview.py --pretty`,
  `python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty`,
  and
  `python3 scripts/forecast_window_preview.py --scenario empty-window --pretty`.
  All runs printed the synthetic-only warning and reported
  `generated_at_utc=2026-01-01T00:00:00Z`,
  `model_version=rule-engine-v0+forecast-window-v0`, and
  `decision_support_only=true`. The balanced DK1 run returned the three
  expected `0-24h`, `24-48h`, and `48-72h` windows with row counts `2/2/2`,
  risk levels `medium/low/medium`, and max risk scores `45/30/35`. The DK2
  high-risk run showed `24-48h` as `high` risk with `max_risk_score=75` and
  reason codes including `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`,
  demonstrating max-risk aggregation. The empty-window run showed DK1
  `24-48h` with `row_count=0`, `risk_level=unknown`,
  `average_risk_score=null`, `max_risk_score=null`, and no top reason codes,
  demonstrating insufficient caller-provided data handling. Clarified that
  this is synthetic/caller-provided local preview only, deterministic
  aggregation only, not ML, not DMI/weather based yet, not production forecast
  validation, and that no database access, SQL, live Energi Data Service
  polling, DMI/weather calls, backend/frontend servers, scheduler, Azure
  resources, secrets, auth, ML training, LLM use, automatic control, dispatch,
  activation, or operational functionality was added or used by this
  documentation update.
- Added a manual synthetic local `scripts/forecast_window_preview.py` for
  `forecast-window-v0`, with fixed `generated_at_utc`, DK1/DK2 selection,
  `balanced`, `high-risk`, and `empty-window` scenarios, compact or pretty JSON
  output, direct use of `build_forecast_window_forecast(...)`, and explicit
  synthetic-only safety warnings. Documented usage in the scripts README,
  README, model card, and backtest notes. This does not require `DATABASE_URL`,
  connect to a database, execute SQL, fetch live Energi Data Service data, call
  DMI/weather APIs, add FastAPI endpoints, modify backend startup, add frontend
  code, create ingestion jobs, use Azure, add secrets, add auth, train ML
  models, use LLMs, control, dispatch, activation, or operational
  functionality.
- Added `forecast-window-v0`, a pure backend Python deterministic aggregation
  layer for caller-provided DK1/DK2 surplus-risk rows. It returns three
  non-overlapping windows (`0-24h`, `24-48h`, `48-72h`), ignores rows before
  `generated_at_utc`, at or beyond +72h, or for another valid price area,
  rejects invalid DK areas and timezone-naive timestamps, reuses
  `calculate_surplus_risk` from `rule-engine-v0`, bases each non-empty window
  risk level on the maximum observed risk score, and includes deterministic
  averages, risk counts, top reason codes, human-review actions, and
  decision-support-only safety wording. Added forecast-window tests covering
  window assignment, ignored rows, empty windows, max-risk aggregation,
  deterministic reason-code ordering, timestamp validation, absence of DB/API
  and network dependencies in the forecast module, and required safety output.
  Updated README, model card, and backtest notes to document that this is not
  ML, not DMI/weather based yet, does not fetch data, does not write data, does
  not expose an API yet, is not production forecast validation, and must not be
  used for automatic control, dispatch, or activation. No FastAPI endpoint,
  frontend behavior, database access, SQL, live Energi Data Service calls,
  DMI/weather ingestion, scheduler, Azure infrastructure, secrets, auth, ML
  training, LLM use, control, dispatch, activation, or operational
  functionality was added.
- Added a concise MVP readiness summary across the README, local database
  runbook, model card, and backtest notes. Documented that FlexSignal AI is
  ready for a local technical MVP demo, not production ready, not a validated
  commercial forecasting product, and remains read-only decision support for
  human review only. Summarized the latest validated local dataset status
  (`spot_prices` DK1=53/DK2=50 and `power_balance` DK1=53/DK2=50), local DB
  backtest status (DK1 53 composed rows with low/medium/high 1/52/0 and
  average risk score `34.5283`; DK2 50 composed rows with low/medium/high
  42/8/0 and average risk score `21.8`), and read-only API/UI smoke-test
  status (DK1 current risk medium score 35, DK2 current risk low score 20,
  manual frontend loads for DK1/DK2 spot prices, power balance, and current
  risk, visible read-only badge/disclaimer, and no automatic loading, polling,
  control, dispatch, or activation observed). Clarified remaining gaps: no
  24-72 hour forecast, DMI/weather ingestion, full historical backtest, outcome
  labels, model performance metrics, Azure deployment, Microsoft Entra ID auth,
  audit-log implementation beyond documentation, PDF/report export, production
  database, scheduled ingestion, monitoring setup, or human approval workflow
  in product UI. Recommended the next MVP step as a simple deterministic
  24-72 hour forecast foundation using available local EDS data first, with no
  LLM forecast engine and no control, dispatch, or activation behavior. This
  change is documentation only; no code, backend behavior, frontend behavior,
  tests, servers, database writes, live API polling, scheduled jobs, Azure
  infrastructure, auth, secrets, ML training, LLM use, or operational
  functionality was added.
- Documented the read-only current-risk API and frontend smoke-test after the
  manual `limit 50` EDS confirmed local write had populated local PostgreSQL.
  API observations used
  `curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK1"` and
  `curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK2"`; DK1
  returned HTTP 200 with `timestamp_utc=2026-06-10T17:00:00+02:00`,
  `risk_level=medium`, `risk_score=35`, `confidence_score=1.0`, reason codes
  `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`,
  `model_version=rule-engine-v0`, `decision_support_only=true`, and source
  metadata showing `spot_prices` and `power_balance` rows found; DK2 returned
  HTTP 200 with the same timestamp, `risk_level=low`, `risk_score=20`,
  `confidence_score=1.0`, reason codes `NORMAL_PRICE`,
  `MODERATE_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`,
  `model_version=rule-engine-v0`, `decision_support_only=true`, and source
  metadata showing `spot_prices` and `power_balance` rows found. Frontend
  smoke-test observations at `http://localhost:3000` showed manual DK1 and DK2
  spot-price loads returning 5 `spot_prices` rows, manual DK1 and DK2
  power-balance loads returning 5 `power_balance` rows, manual current-risk
  loads matching the DK1 medium score 35 and DK2 low score 20 API results, and
  the read-only badge visible for both areas. Clarified that the dashboard
  still requires manual button clicks, no automatic loading or polling was
  observed, the current-risk endpoint still reads from local PostgreSQL and
  returns decision-support-only results, and this is local MVP smoke-test
  documentation only, not production validation. No code, backend behavior,
  frontend behavior, ingestion, database writes by this change, live Energi
  Data Service polling, tests, servers, scheduled jobs, Azure infrastructure,
  secrets, auth, ML training, LLM use, control, dispatch, activation, or
  operational functionality was added.
- Documented the manual EDS historical batch wrapper `limit 50` confirmed
  local write, repeated-run idempotency check, and DK1/DK2 local DB backtest
  results only. The confirmed command was
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --confirm-local-db-write --continue-on-error`;
  before the write, counts were `spot_prices` DK1=13 and DK2=10, and
  `power_balance` DK1=13 and DK2=12; the wrapper reported
  `child_exit_codes=[0, 0, 0, 0]`, 4 planned commands, 4 succeeded commands, 0
  failed commands, `confirmed_local_write=true`, `dry_run=false`, `limit=50`,
  `local_only=true`, `decision_support_only=true`, price areas `DK1`/`DK2`,
  and datasets `DayAheadPrices` and `ElectricityProdex5MinRealtime`; child
  confirmed writes all returned HTTP 200 with 50 raw records, 50 normalized
  records, 50 SQL commands, target tables `spot_prices` or `power_balance`,
  and `committed=true`; after the write, counts were `spot_prices` DK1=53 and
  DK2=50, and `power_balance` DK1=53 and DK2=50. Documented the repeated
  confirmed command idempotency check: the second run again reported
  `child_exit_codes=[0, 0, 0, 0]`, 4 planned commands, 4 succeeded commands, 0
  failed commands, `confirmed_local_write=true`, `dry_run=false`, `limit=50`,
  and `local_only=true`; counts remained unchanged, so no duplicate explosion
  was observed and the repeated import was idempotent for the same 50-record
  batch. Documented read-only local DB backtests after the batch: DK1 with 53
  spot-price rows read, 53 power-balance rows read, 53 composed and evaluated
  rows, 0 failed rows, low/medium/high counts of 1/52/0, average risk score
  `34.5283`, average confidence `1.0`, reason-code counts including
  `NORMAL_PRICE: 53`, `HIGH_RENEWABLE_SHARE: 52`,
  `EXCHANGE_NET_NOT_USED_V0: 53`, and `ELEVATED_RENEWABLE_SHARE: 1`; DK2 with
  50 spot-price rows read, 50 power-balance rows read, 50 composed and
  evaluated rows, 0 failed rows, low/medium/high counts of 42/8/0, average risk
  score `21.8`, average confidence `1.0`, reason-code counts including
  `NORMAL_PRICE: 50`, `MODERATE_RENEWABLE_SHARE: 39`,
  `HIGH_RENEWABLE_SHARE: 8`, `ELEVATED_RENEWABLE_SHARE: 3`, and
  `EXCHANGE_NET_NOT_USED_V0: 50`. Clarified that DK1 remained mostly medium
  risk on the expanded local sample, DK2 now includes both low and medium risk,
  and this is stronger technical validation than the 10-row sample but still
  not full model validation because the dataset is still small and has no
  outcome labels. No code, backend behavior, frontend behavior, database writes
  by this change, live API polling, scheduled jobs, Azure infrastructure,
  secrets, auth, ML training, LLM use, control, dispatch, activation, or
  operational functionality was added.
- Documented the manual EDS historical batch wrapper `limit 50` dry-run result
  only. The command was
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --continue-on-error`;
  wrapper output was `dry_run=true`, `confirmed_local_write=false`,
  `local_only=true`, `decision_support_only=true`, `limit=50`, price areas
  `DK1`/`DK2`, datasets `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`, 4 planned commands, 4 succeeded commands, 0
  failed commands, and child exit codes `[0, 0, 0, 0]`. Child dry-runs for
  `DayAheadPrices` DK1/DK2 and `ElectricityProdex5MinRealtime` DK1/DK2 all
  returned HTTP 200 with 50 raw records, 50 normalized records, 50 SQL
  commands, target tables `spot_prices` or `power_balance`, and
  `committed=false`. Clarified that limit 50 dry-run is validated for all
  supported DK1/DK2 dataset combinations, no database writes were committed,
  this validates command orchestration and normalization path only, confirmed
  writes still require explicit `--confirm-local-db-write`, and `100`/`500`
  still require future explicit enhancement. No code, backend behavior,
  frontend behavior, database writes, live API polling, scheduled jobs, Azure
  infrastructure, secrets, auth, ML training, LLM use, control, dispatch,
  activation, or operational functionality was added.
- Raised the explicit manual local Energi Data Service ingest safety cap from
  `limit 10` to `limit 50` in `scripts/manual_eds_local_db_ingest.py` and the
  `scripts/manual_eds_historical_batch_import.py` wrapper while preserving the
  conservative defaults (`2` for the child script, `10` for the wrapper),
  dry-run default, local `DATABASE_URL` safety gate, supported datasets,
  supported price areas, and required `--confirm-local-db-write` gate for
  writes. Added parser and wrapper orchestration tests for `limit 50`
  acceptance, `0`/`51` rejection, dry-run defaults, explicit confirmation
  passthrough, and non-local database URL rejection. Updated scripts and
  validation docs, the local database runbook, and backtest notes to state that
  `limit 50` is supported for manual local validation while `100` and `500`
  still require a future explicit enhancement. No scheduler, Azure
  infrastructure, backend startup ingestion, FastAPI endpoint, frontend code,
  production database support, secrets, auth, ML training, LLM use, control,
  dispatch, activation, closed-loop, or operational functionality was added.
- Documented the manual EDS historical batch confirmed local write,
  idempotency check, and DK1/DK2 local DB backtest results only. The confirmed
  command was
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 10 --confirm-local-db-write --continue-on-error`;
  before the write, counts were `spot_prices` DK1=3 and DK2=2, and
  `power_balance` DK1=3 and DK2=2; the wrapper reported
  `child_exit_codes=[0, 0, 0, 0]`, 4 planned commands, 4 succeeded commands, 0
  failed commands, `confirmed_local_write=true`, `dry_run=false`, `limit=10`,
  `local_only=true`, `decision_support_only=true`, price areas `DK1`/`DK2`,
  and datasets `DayAheadPrices` and `ElectricityProdex5MinRealtime`; child
  confirmed writes all returned HTTP 200 with 10 raw records, 10 normalized
  records, 10 SQL commands, target tables `spot_prices` or `power_balance`,
  and `committed=true`; after the write, counts were `spot_prices` DK1=13 and
  DK2=10, and `power_balance` DK1=13 and DK2=12. Documented the repeated
  confirmed command idempotency check: the second run again reported
  `child_exit_codes=[0, 0, 0, 0]`, 4 planned commands, 4 succeeded commands, 0
  failed commands, `confirmed_local_write=true`, `dry_run=false`, `limit=10`,
  and `local_only=true`; counts remained unchanged, so no duplicate explosion
  was observed. Documented read-only local DB backtests after the batch: DK1
  with 13 spot-price rows read, 13 power-balance rows read, 13 composed and
  evaluated rows, 0 failed rows, low/medium/high counts of 1/12/0, average
  risk score `33.0769`, average confidence `1.0`, reason-code counts including
  `NORMAL_PRICE: 13`, `HIGH_RENEWABLE_SHARE: 12`,
  `EXCHANGE_NET_NOT_USED_V0: 13`, and `ELEVATED_RENEWABLE_SHARE: 1`; DK2 with
  10 spot-price rows read, 12 power-balance rows read, 12 composed and
  evaluated rows, 0 failed rows, low/medium/high counts of 12/0/0, average
  risk score `20.0`, average confidence `1.0`, reason-code counts including
  `NORMAL_PRICE: 12`, `MODERATE_RENEWABLE_SHARE: 12`, and
  `EXCHANGE_NET_NOT_USED_V0: 12`. Clarified that DK1 shifted to mostly medium
  risk on the expanded local sample, DK2 remained low risk, and this is still
  technical validation only with a small dataset and no outcome labels. No
  code, backend behavior, frontend behavior, database writes by this change,
  live API polling, Azure infrastructure, secrets, auth, ML training, LLM use,
  control, dispatch, activation, or operational functionality was added.
- Documented the manual EDS historical batch wrapper dry-run result only:
  command
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 10 --continue-on-error`;
  wrapper output `dry_run=true`, `confirmed_local_write=false`,
  `local_only=true`, `decision_support_only=true`, `limit=10`, price areas
  `DK1`/`DK2`, datasets `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`, 4 planned commands, 4 succeeded commands, 0
  failed commands, and child exit codes `[0, 0, 0, 0]`; and child dry-run
  observations for all four dataset/price-area combinations showing HTTP 200,
  10 raw records, 10 normalized records, 10 SQL commands, target tables
  `spot_prices` or `power_balance`, and `committed=false`. Clarified that this
  validates command orchestration and normalization path only, did not write to
  the database, still requires explicit `--confirm-local-db-write` for
  confirmed writes, and used the wrapper default `limit 10`. No code, backend
  behavior, frontend behavior, database writes,
  live API polling, Azure infrastructure, secrets, auth, ML training, LLM use,
  control, dispatch, activation, or operational functionality was added.
- Added `scripts/manual_eds_historical_batch_import.py`, a manual local-only
  batch wrapper around `scripts/manual_eds_local_db_ingest.py` for explicit
  DK1/DK2 and `DayAheadPrices`/`ElectricityProdex5MinRealtime` validation
  batches. The wrapper requires a local DB-API `DATABASE_URL`, refuses
  non-local hosts, defaults to dry-run, passes `--confirm-local-db-write` to
  child commands only when explicitly received, prints the child command plan,
  stops on first child failure unless `--continue-on-error` is passed, defaults
  to `limit 10`, rejects limits above `50`, and emits a compact JSON summary.
  Updated scripts and validation docs, the local database runbook, and backtest
  notes to clarify that larger `100`/`500` staged imports require a future
  explicit enhancement and that the wrapper must not bypass the current child
  safety gate. No scheduler, Azure infrastructure, backend
  startup ingestion, FastAPI endpoint, frontend code, production database
  support, secrets, auth, ML training, LLM use, control, dispatch, activation,
  closed-loop, or operational functionality was added.
- Added a documentation-only historical local Energi Data Service import plan
  for expanding local DK1/DK2 samples of `DayAheadPrices` and
  `ElectricityProdex5MinRealtime` to support better read-only local backtesting.
  Documented the staged batch progression of `limit 50`, then `100`, then
  maximum `500` per dataset and price area, with `100` and `500` still
  requiring a future explicit enhancement plus row counts, distinct
  `source_record_id` counts, idempotency, and backtest outputs are checked.
  Documented required safety gates: local PostgreSQL only, `DATABASE_URL`
  targeting `localhost` or `127.0.0.1`, dry-run before confirmed write,
  explicit `--confirm-local-db-write` for confirmed writes, no production or
  Azure database, no scheduled jobs, no backend startup ingestion, no
  frontend-triggered ingestion, and no automatic polling loop. Documented
  post-batch validation expectations for row counts by `price_area`, distinct
  source IDs, repeated-import idempotency, DK1/DK2 local DB read-only backtests,
  `risk_level_counts`, and `average_risk_score`; stop conditions for duplicate
  explosion, non-local DB URLs, unconfirmed writes, failed normalization,
  unexpected field mapping, and any control/dispatch/activation behavior; and
  limitations that larger local samples are still not full model validation
  because outcome labels, DMI/weather data, and a 24-72 hour forecast are
  absent while `rule-engine-v0` remains deterministic and simple. No code,
  backend behavior, frontend behavior, database writes, live API polling, Azure
  infrastructure, secrets, auth, ML training, LLM use, control, dispatch,
  activation, or operational functionality was added.
- Added a concise MVP status documentation update covering the current
  read-only technical foundation: local PostgreSQL schema and Alembic baseline,
  manual local EDS ingestion for `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`, validated tiny DK1/DK2 local samples,
  read-only `spot_prices` and `power_balance` API paths, manual frontend loads
  for spot prices, power balance, and current risk, `rule-engine-v0`,
  `GET /api/risk/current` for DK1/DK2, synthetic and local DB read-only
  backtest previews, and `nearest_timestamp_v0_1` backtest row pairing.
  Documented validated local results only: DK1 has 3 spot-price rows, 3
  power-balance rows, current risk `medium` with score `35`, local DB backtest
  counts low/medium/high of 1/2/0, and average risk score `26.6667`; DK2 has 2
  spot-price rows, 2 power-balance rows, current risk `low` with score `20`,
  local DB backtest counts low/medium/high of 2/0/0, and average risk score
  `20.0`. Clarified that this remains preview/non-production work with a tiny
  dataset, no full historical backtest, no outcome labels, no 24-72 hour
  forecast, no DMI/weather ingestion, no production report export, no auth, no
  Azure deployment, no scheduled ingestion jobs, no production database, no
  human approval workflow beyond documentation/disclaimers, no automatic
  control, no dispatch, no activation, no operational energy system
  integration, no LLM as decision engine, and no autonomous decisions.
- Documented DK2 local Energi Data Service validation results only:
  `DayAheadPrices` DK2 and `ElectricityProdex5MinRealtime` DK2 both returned
  HTTP 200 in dry-run mode with 2 raw records, 2 normalized records, 2 SQL
  commands, and `committed=false`; both datasets were then manually confirmed
  with `committed=true` against local PostgreSQL only. Documented local row
  counts after ingest as `spot_prices` DK1=3 and DK2=2, and `power_balance`
  DK1=3 and DK2=2. This documentation preserves the local/manual boundary with
  no production database, Azure resources, startup migrations, automated
  ingestion job, live polling loop, ML training, LLM use, or automatic control,
  dispatch, activation, or operational functionality.
- Documented DK2 current-risk and local read-only DB backtest validation only:
  `GET /api/risk/current?price_area=DK2` returned HTTP 200 with
  `risk_level=low`, `risk_score=20`, `confidence_score=1.0`, reason codes
  including `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`, `model_version=rule-engine-v0`,
  `decision_support_only=true`, and source metadata showing `spot_prices` and
  `power_balance` rows found. Documented the command
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python
  scripts/risk_backtest_local_db.py --price-area DK2 --limit 10 --pretty` and
  observed read-only output with `pairing_strategy=nearest_timestamp_v0_1`, 2
  spot-price rows read, 2 power-balance rows read, 2 composed/evaluated rows, 0
  failed rows, low/medium/high risk counts of 2/0/0, average risk score `20.0`,
  average confidence score `1.0`, reason-code counts for `NORMAL_PRICE`,
  `MODERATE_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`, no missing price
  or generation data, and `model_version=rule-engine-v0`. Documented that this
  is technical validation on a tiny local sample, not full model validation or
  evidence for performance conclusions, with local PostgreSQL, manual
  validation, SELECT/read-only backtest behavior, no production database, no
  Azure resources, no startup migrations, no automated ingestion job, no live
  polling loop, no ML training, no LLM use, and no automatic control, dispatch,
  activation, or operational functionality.
- Added pure read-only nearest-timestamp risk backtest row pairing with
  `pair_rows_by_nearest_timestamp(...)`, deterministic DK1/DK2 validation,
  timezone-aware ISO timestamp parsing including trailing `Z`, power-balance
  rows as the primary timeline, deterministic tie-breaking by earlier
  spot-price timestamp then original order, unit tests, and local DB backtest
  metadata `pairing_strategy=nearest_timestamp_v0_1`. Updated the manual local
  DB backtest script and docs while preserving SELECT/read-only behavior only,
  no database writes, no live EDS polling, no API endpoint or startup changes,
  no frontend work, no ingestion jobs, no Azure resources, no secrets, no auth,
  no ML training, no LLM use, and no automatic control, dispatch, activation,
  or operational functionality.
- Documented the local read-only DB risk backtest rerun after
  `nearest_timestamp_v0_1` pairing was merged only: pre-backtest local table
  counts of 3 `spot_prices` rows and 3 `power_balance` rows, command
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python
  scripts/risk_backtest_local_db.py --price-area DK1 --limit 10 --pretty`,
  observed DK1 output with `read_only=true`, `decision_support_only=true`, 3
  `pairing_strategy=nearest_timestamp_v0_1`, 3 spot-price rows read, 3
  power-balance rows read, 3 composed rows, 3 total and evaluated rows, 0
  failed rows, low/medium/high risk counts of 1/2/0, average risk score
  `26.6667`, average confidence score `1.0`, reason-code counts for
  `NORMAL_PRICE`, `EXCHANGE_NET_NOT_USED_V0`, `HIGH_RENEWABLE_SHARE`, and
  `ELEVATED_RENEWABLE_SHARE`, 0 missing price rows, 0 missing generation-data
  rows, and `model_version=rule-engine-v0`. Documented that nearest-timestamp
  pairing is active, the tiny local DK1 risk distribution remained unchanged
  compared with the previous simple pairing run, the 3-row local sample is
  technical validation only, and a larger historical dataset is required before
  drawing performance conclusions. Confirmed documentation-only scope with
  local PostgreSQL SELECT/read-only behavior only, no database writes, no live
  EDS polling, no backend or frontend server, no startup migrations, no
  production database, no Azure resources, no ML training, no LLM use, and no
  automatic control, dispatch, activation, or operational functionality.
- Added a manual local PostgreSQL read-only `scripts/risk_backtest_local_db.py`
  backtest preview for `rule-engine-v0`, using existing SELECT query builders,
  local-only `postgresql://...` `DATABASE_URL` validation, DK1/DK2 filtering,
  latest-first list-order row pairing through `compose_surplus_risk_input`,
  compact or pretty JSON output, and documentation of the technical-validation
  limitation. This performs no database writes, live Energi Data Service
  fetches, API endpoint or startup changes, frontend work, ingestion jobs,
  Azure infrastructure, secrets, auth, ML training, LLM use, control, dispatch,
  activation, or operational functionality.
- Added a manual synthetic local `scripts/risk_backtest_preview.py` for the
  existing `rule-engine-v0` backtest evaluator, with hardcoded low-, medium-,
  high-like, missing-data, and invalid sample rows, compact or pretty JSON
  output, documentation, and explicit synthetic-only warnings. This does not
  require `DATABASE_URL`, connect to a database, execute SQL, fetch live Energi
  Data Service data, add API endpoints, modify backend startup, add frontend or
  ingestion code, use Azure, add secrets, train ML models, use LLMs, control,
  dispatch, activation, or operational functionality.
- Added pure Python `evaluate_risk_backtest` aggregation for local
  `rule-engine-v0` row dictionaries, including evaluated and failed row counts,
  low/medium/high counts, average risk and confidence scores, reason-code
  aggregation, missing price and generation-data counts, row-level error
  capture, unit tests, and documentation. This is synthetic/local
  decision-support evaluation only, with no database connections, SQL
  execution, API endpoints, FastAPI startup changes, frontend code, ingestion
  jobs, Azure infrastructure, secrets, ML training, LLM use, control, dispatch,
  activation, or operational functionality.
- Documented manual local frontend current-risk smoke-test results only:
  backend startup with `DATABASE_URL="postgresql://localhost/flexsignal_ai"
  python -m uvicorn app.main:app --reload`, frontend startup with
  `cd frontend`, `npm install`, and `npm run dev`, browser validation at
  `http://localhost:3000`, DK1 selection, manual Load spot prices, Load power
  balance, and Load current risk actions, 3 displayed spot price rows, 3
  displayed power balance rows, current surplus risk `risk_level=medium`,
  `risk_score=35`, `confidence_score=1`, `reason_codes` including
  `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`,
  `model_version=rule-engine-v0`, `decision_support_only=true`,
  `metadata.source_tables_used` showing `spot_prices` and `power_balance`,
  `metadata.spot_price_row_found=true`,
  `metadata.power_balance_row_found=true`, and no Failed to fetch error.
  Confirmed the frontend used only the backend API helper, with no direct
  Energi Data Service frontend call, polling or automatic refresh, database
  writes, live EDS polling, startup migrations, Azure resources, production
  database, LLM or ML model use, automatic control, dispatch, activation, or
  operational functionality.
- Added manual read-only frontend display for the existing current surplus risk
  API, including a third dashboard card, DK1/DK2-aware manual
  `GET /api/risk/current` fetch through the backend API base helper, loading
  and backend-unavailable error states, typed response fields for risk level,
  score, confidence, reason codes, explanation, recommended human action,
  model version, decision-support flag, and source metadata. No page-load fetch,
  polling, automatic refresh, direct Energi Data Service frontend call, backend
  code, database write, auth, Azure infrastructure, charts, forecasting/model
  logic, control, dispatch, activation, or operational functionality was added.
- Documented manual local current risk API smoke-test results for `GET
  /api/risk/current?price_area=DK1`: backend startup with
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn
  app.main:app --reload`, observed `risk_level=medium`, `risk_score=35`,
  `confidence_score=1.0`, `reason_codes` including `NORMAL_PRICE`,
  `HIGH_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`,
  `model_version=rule-engine-v0`, `decision_support_only=true`,
  `metadata.source_tables_used` including `spot_prices` and `power_balance`,
  and both `metadata.spot_price_row_found` and
  `metadata.power_balance_row_found` as `true`. Documented invalid
  `price_area=SE3` validation behavior and confirmed only DK1 and DK2 are
  accepted, with local PostgreSQL reads only through the existing read-only
  query path, no database writes, no live Energi Data Service polling, no
  startup migrations, no Azure resources, no production database, no LLM or ML
  model, and no automatic control, dispatch, activation, or operational
  functionality.
- Added read-only `GET /api/risk/current?price_area=DK1|DK2` surplus-risk API
  endpoint that lazily requires `DATABASE_URL` only when called, reads the
  latest existing local `spot_prices` and `power_balance` rows through existing
  SELECT-only query paths, composes input with `compose_surplus_risk_input`,
  scores with `rule-engine-v0`, returns source-table metadata, and includes
  mocked tests for DK1/DK2 validation, missing `DATABASE_URL`, empty rows,
  SELECT-only SQL, no live HTTP calls, unchanged preview behavior, and no
  control, dispatch, activation, ingestion, frontend, Azure, auth, ML, LLM, or
  database-write behavior.
- Added pure Python `compose_surplus_risk_input` mapping for existing
  `spot_prices` and `power_balance` row dictionaries into `rule-engine-v0`
  input, with DK1/DK2 and timestamp validation, focused unit tests, model-card
  documentation, no database connection, no SQL execution, no API/frontend/
  ingestion/Azure changes, no ML/LLM logic, and no control, dispatch,
  activation, or operational behavior.
- Documented manual local risk preview API smoke-test results for `POST
  /api/risk/preview`: backend startup with
  `python -m uvicorn app.main:app --reload`, valid caller-provided DK1 JSON
  payload at `2026-06-09T21:45:00+02:00` with negative price and high renewable
  share inputs, observed `risk_level=high`, `risk_score=75`,
  `confidence_score=1.0`, `reason_codes` including `NEGATIVE_PRICE` and
  `HIGH_RENEWABLE_SHARE`, `model_version=rule-engine-v0`, and
  `decision_support_only=true`. Documented invalid `price_area=SE3` validation
  behavior and confirmed only DK1 and DK2 are accepted, with caller-provided
  JSON only, no database connection, no database writes, no live Energi Data
  Service polling, no LLM or ML model, and no automatic control, dispatch,
  activation, or operational functionality.
- Added read-only `POST /api/risk/preview` FastAPI endpoint that validates
  caller-provided DK1/DK2 JSON payloads with Pydantic and delegates only to the
  existing pure `rule-engine-v0` surplus-risk scorer, returning the exact model
  output shape with `decision_support_only=true`, mocked API tests, no database
  dependency, no SQL execution, no live HTTP calls, no ingestion, no frontend,
  no Azure infrastructure, no LLM use, and no control, dispatch, activation, or
  operational behavior.
- Added deterministic pure Python `rule-engine-v0` surplus-risk scoring for
  DK1/DK2 read-only decision support, with validation, reason codes,
  confidence scoring, exchange-flow sign ambiguity documented as unused in v0,
  focused unit tests, and no database, API, frontend, ingestion, ML training,
  LLM, dispatch, activation, or control functionality.
- Documented manual local frontend-to-backend read-only smoke-test results:
  backend startup with `DATABASE_URL="postgresql://localhost/flexsignal_ai"
  python -m uvicorn app.main:app --reload`, frontend startup with
  `cd frontend`, `npm install`, and `npm run dev`, browser validation at
  `http://localhost:3000`, DK1 selection, manual Load spot prices and Load power
  balance actions, 3 displayed DK1 rows for both spot prices and power balance,
  no Failed to fetch error, HTTP 200 backend logs for both read-only API calls,
  and confirmed local-development CORS behavior. Confirmed the frontend only
  used the backend API helper, with no direct Energi Data Service frontend
  calls, polling, database writes, live EDS polling, startup migrations, Azure
  resources, production database, forecasting/model logic, control, dispatch,
  activation, or operational functionality.
- Added local-development-only CORS middleware for the read-only FastAPI API,
  allowing `http://localhost:3000` and `http://127.0.0.1:3000` with `GET` and
  `OPTIONS` only, no wildcard origins, no credentials, no startup migrations,
  no database writes, no live API polling, and no new write endpoints.
- Added manual read-only frontend integration for the existing backend energy
  API endpoints, including typed `limit=5` spot price and power balance fetch
  helpers, DK1/DK2 selection, manual load buttons, loading and backend
  unavailable error states, row counts, compact result tables, and visible copy
  confirming the browser uses only the backend API base URL helper and does not
  call Energi Data Service directly. No automatic page-load fetches, polling,
  charts, auth, Azure infrastructure, secrets, database writes,
  forecasting/model logic, dispatch, activation, control, backend code, or
  operational functionality were added.
- Documented manual local frontend dashboard shell smoke-test results: local
  startup via `npm install`, `npm run build`, and `npm run dev`; successful
  `next build` with TypeScript passing and static `/` route generation; browser
  validation at `http://127.0.0.1:3000` showing the FlexSignal AI title,
  read-only/no-automatic-control badge, DK1/DK2 selector, spot prices and power
  balance cards, placeholder/loading-ready/error-ready sections, backend API
  base URL helper `http://127.0.0.1:8000`, and no error screen. Confirmed the
  shell made no backend API requests, direct Energi Data Service calls, polling,
  database writes, auth, Azure resources, forecasting/model logic, control,
  dispatch, activation, or operational functionality, and noted the
  development-only `127.0.0.1` cross-origin warning with `localhost:3000` as
  the local development URL unless `allowedDevOrigins` is configured later.
- Added a minimal Next.js + TypeScript frontend dashboard shell with
  FlexSignal AI branding, the read-only/no-automatic-control scope badge, DK1
  and DK2 selector state, placeholder/loading/error-ready cards for spot prices
  and power balance, and a configurable future backend API base URL helper with
  no frontend data fetches, polling, forecasting, dispatch, activation, control,
  auth, database code, payments, Azure infrastructure, or backend ingestion
  changes.
- Documented manual local read-only FastAPI smoke-test results for `GET
  /health`, `GET /api/energy/spot-prices?price_area=DK1&limit=5`, and `GET
  /api/energy/power-balance?price_area=DK1&limit=5`, using local PostgreSQL
  only, with no database writes, live EDS polling, startup migrations, ingestion
  jobs, Azure resources, production database, forecasting, control, dispatch,
  activation, or operational functionality.
- Added read-only FastAPI energy endpoints for recent local `spot_prices` and
  `power_balance` rows, using existing SELECT query builders, lazy local-only
  `DATABASE_URL` validation, DK1/DK2 filtering, default limit `100`, hard
  maximum `1000`, mocked tests without PostgreSQL, and no writes, live EDS
  fetches, ingestion jobs, startup migrations, frontend, forecasting, control,
  dispatch, activation, or operational functionality.
- Added a manual local PostgreSQL read-preview script for existing
  `spot_prices` and `power_balance` tables using the existing read-only query
  builders, required local DB-API `DATABASE_URL`, local-host validation,
  DK1/DK2 filtering, default limit `10`, hard maximum `100`, compact JSON-line
  row output, and no writes, live EDS fetches, ingestion jobs, FastAPI imports,
  endpoints, forecasting, control, dispatch, activation, or operational
  functionality.
- Added pure read-only parameterized SELECT query builders for recent and
  time-window `spot_prices` and `power_balance` reads by DK1/DK2 `price_area`,
  with default limit `100`, hard maximum `1000`, no database connection, no SQL
  execution, no FastAPI endpoint, no ingestion job, and no operational control
  functionality.
- Documented confirmed manual live Energi Data Service to local PostgreSQL write
  validation results for `DayAheadPrices` DK1 to `spot_prices` and
  `ElectricityProdex5MinRealtime` DK1 to `power_balance`, both with `--limit 2`,
  explicit `--confirm-local-db-write`, local PostgreSQL only, and no Azure,
  production, startup, scheduled ingestion, automatic write, API endpoint,
  forecasting, control, dispatch, activation, or operational functionality.
- Added a manual local-only EDS-to-PostgreSQL ingest validation script for tiny
  live `DayAheadPrices` and `ElectricityProdex5MinRealtime` DK1/DK2 samples,
  with dry-run default, required local DB-API `DATABASE_URL`, local-host
  validation, limit maximum `10`, generated SQL preview counts, and explicit
  `--confirm-local-db-write` gating for local writes only.
- Documented manual local PostgreSQL migration and smoke-test validation
  results, including PostgreSQL 16.14 local readiness, Alembic upgrade to
  `0001_initial_schema`, verified tables, dry-run output, confirmed local write
  counts, idempotent upsert behavior, and the separate Alembic SQLAlchemy URL
  and smoke-test DB-API URL formats.
- Added psycopg v3 as a backend dev dependency for local/manual PostgreSQL
  Alembic and smoke-test validation, with docs using the explicit
  `postgresql+psycopg://localhost/flexsignal_ai` SQLAlchemy URL and preserving
  the no-startup-migrations/no-startup-writes boundary.
- Added an explicit manual local PostgreSQL smoke-test script for hardcoded DK1
  sample records through the existing write-plan, SQL builder, and transaction
  boundaries, guarded by `DATABASE_URL`, local-host validation, dry-run default,
  and `--confirm-local-db-write` for real local writes.
- Documented the future manual local PostgreSQL validation runbook, including
  local-only migration usage, explicit shell-only `DATABASE_URL`, safety
  boundaries, and the acceptance checklist required before real DB write code.
- Added a mocked database transaction boundary for generated SQL command
  dictionaries with caller-injected fake connections, pre-execution validation,
  commit-after-success, rollback-on-execute-failure, and no `DATABASE_URL`,
  database driver, PostgreSQL, startup, or ingestion side effects.
- Added a dry-run Energi Data Service persistence orchestration helper that
  chains normalized records through write-plan and SQL preview generation, with
  optional fake executor handoff and no database, HTTP, startup, or runtime
  ingestion side effects.
- Added a narrow Energi Data Service database write executor boundary that uses
  a caller-provided cursor, validates the full batch before execution, and does
  not create connections, commit transactions, schedule ingestion, or modify
  runtime startup.
- Added a pure parameterized SQL builder for Energi Data Service write-plan
  preview entries targeting `spot_prices` and `power_balance`, without database
  connections, execution, writes, ingestion jobs, or runtime startup changes.
- Documented manual read-only Energi Data Service write-plan preview validation
  for `DayAheadPrices` and `ElectricityProdex5MinRealtime` DK1/DK2 records,
  including the expected null `consumption_mw` value for the selected realtime
  production dataset.
- Added a manual read-only Energi Data Service write-plan preview script for
  `DayAheadPrices` and `ElectricityProdex5MinRealtime` DK1/DK2 records without
  database connections, SQL generation, or writes.
- Added a pure dry-run Energi Data Service database write-plan builder for
  `spot_prices` and `power_balance` preview entries without SQL generation or
  database writes.
- Added pure Energi Data Service record-to-database payload repository helpers
  for `spot_prices` and `power_balance` with mocked/unit tests and no database
  writes.
- Fixed backend package discovery so Alembic migrations are not installed as an application package.
- Added a controlled Energi Data Service dry-run ingestion module with mocked
  unit tests and no database writes.
- Added an Alembic initial migration baseline for the documented database schema.
- Initial project structure.
- Initial documentation baseline.
- Read-only decision-support scope defined.
- No frontend, database runtime, or infrastructure implementation yet.
