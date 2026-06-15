# Human Oversight

## Audit Event Foundation

`audit-event-v0` is an in-memory/data-structure foundation for future
compliance and audit logging of read-only decision-support actions. It can
represent events such as forecast preview requested, current risk viewed,
report summary built, report Markdown rendered, and report PDF exported.

The builder records caller-provided actor, resource, action, outcome,
timestamp, and safe metadata fields only. It produces deterministic event ids,
requires timezone-aware timestamps, rejects empty required fields, rejects
unknown event, actor, and outcome values, and rejects secret-like metadata
keys.

Every event includes a safety boundary:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

An audit-event database persistence foundation now exists for later explicit
read-only flows. Alembic migration `0002_audit_events.py` defines an
`audit_events` table with `event_id` as the primary/idempotency key, event
version/type, actor, occurrence time, resource, action, outcome,
`decision_support_only`, JSONB `safety_boundary`, JSONB `metadata`, and
indexes for occurrence time, event type, resource, and actor. The repository
module builds parameterized `ON CONFLICT (event_id) DO NOTHING` insert SQL and
does not interpolate user values into SQL.

This foundation is not wired into runtime behavior yet. It does not
automatically persist audit logs, write files, expose an API, add frontend UI,
connect report/PDF flows, run scheduled logging, connect to auth/Entra, call
Energi Data Service, call DMI/weather APIs, use ML, use LLMs, add Azure
infrastructure, add auth, add secrets, or perform operational behavior.

The audit foundation is designed to support later reviewability and
traceability while preserving the `v0.1` read-only decision-support boundary.
It must not be used for automatic control, dispatch, activation, closed-loop
workflows, live control signals, autonomous decisions, or operational
energy-system integration.

`scripts/audit_event_preview.py` is a manual synthetic local preview for
`audit-event-v0`. It imports `build_audit_event(...)`, uses fixed
`occurred_at_utc=2026-01-01T00:00:00Z`, uses synthetic/caller-provided fields
only, and prints compact JSON by default or indented JSON with `--pretty`.

```bash
python3 scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py --pretty
python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty
```

The default `--event-type` is `all`, which prints an `events` array. A single
event type prints an `event` object. Supported event types are
`forecast_preview_requested`, `current_risk_viewed`,
`report_summary_built`, `report_markdown_rendered`, and
`report_pdf_exported`.

The preview is synthetic/local only. It does not persist audit logs, write
files, access a database, run SQL, expose an API, use frontend code, call
Energi Data Service, call DMI/weather APIs, use ML, use LLMs, create a
scheduler, add Azure infrastructure, add auth or secrets, or perform automatic
control, dispatch, activation, or operational functionality. It is read-only
decision-support audit structure only and must not be used for automatic
control, dispatch, or activation.

## Observed Audit Event Preview Results

Manual local validation covered these commands:

```bash
python3 -m py_compile scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py
python3 scripts/audit_event_preview.py --pretty
python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_event_preview.py --event-type invalid-event
```

Observed results:

- `py_compile` passed.
- The default command printed compact JSON with an `events` array.
- `--pretty` printed indented JSON.
- `--event-type report_pdf_exported` printed one event.
- `--event-type forecast_preview_requested` printed one event.
- `--event-type invalid-event` failed safely with exit code `2` and a clear
  argparse invalid-choice validation error.
- Forbidden-pattern grep on `scripts/audit_event_preview.py` returned no
  matches.
- `git diff --check` passed.

The preview covered `forecast_preview_requested`, `current_risk_viewed`,
`report_summary_built`, `report_markdown_rendered`, and
`report_pdf_exported`. Generated events included
`event_version=audit-event-v0`, deterministic `audit_evt_...` event ids,
fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, and `local_only=true`.

Each generated event included a `safety_boundary` with read-only decision
support, no automatic control, no dispatch, no activation, no operational
energy-system integration, and human review required all set to `true`.

Interpretation: audit-event preview works locally with
synthetic/caller-provided data and demonstrates the audit-event shape for
read-only decision-support actions. The schema/repository persistence
foundation now exists, but no API, frontend, report/PDF, scheduled logging, or
auth flow automatically writes events yet. It does not connect to auth or
actor identity providers, create operational logs, or provide production audit
persistence.

Future audit work can wire explicit read-only flows to audit persistence only
as a separate reviewed module.

## Audit DB Persistence Foundation Validation

The `audit-event-v0` foundation and manual audit-event preview documentation
were already present before PR #87. PR #87 added the audit database
persistence foundation only: an Alembic `audit_events` schema/migration and a
repository SQL builder for explicit future use. It did not wire persistence
into FastAPI endpoints, frontend behavior, report/PDF flows, automatic audit
logging, schedulers, auth, or operational workflows.

The schema uses `event_id` as the primary/idempotency key and records
`event_version`, `event_type`, `actor_type`, `actor_id`,
`occurred_at_utc`, `resource_type`, `resource_id`, `action`, `outcome`,
`decision_support_only`, JSONB `safety_boundary`, JSONB `metadata`, and
`created_at_utc` with a default. It adds indexes for occurrence time, event
type, resource lookup, and actor lookup. The repository validates events before
persistence planning and builds parameterized
`ON CONFLICT (event_id) DO NOTHING` INSERT SQL. Validation did not perform
live database writes.

Initial PR validation documented `310 passed, 1 warning` for backend tests,
successful `py_compile` for `backend/app/audit/events.py` and
`backend/app/audit/repository.py`, safety-boundary grep matches only for
`no_automatic_control`, `no_dispatch`, and `no_activation`, and a passing
`git diff --check`.

GitHub backend-tests initially failed before merge in
`tests/test_api_energy.py::test_app_exposes_no_mutating_write_methods` and
`tests/test_api_risk.py::test_app_import_without_database_url_still_exposes_current_risk_route`.
The missing exposed routes in CI/import context were `/api/risk/current`,
`/api/risk/preview`, and `/api/forecast/preview`. The issue was interpreted as
route exposure under newer FastAPI/Starlette behavior in the test context, not
as live database writes or audit persistence execution. The branch was not
merged while backend-tests were red.

The fix updated `backend/app/main.py` with a small route-registration helper
so `app.routes` exposes concrete paths under the test environment.
`DATABASE_URL` validation remains request-time only, endpoint logic was not
changed, and no new API behavior, DB writes, scheduler, frontend, or control
behavior was added.

Post-fix validation documented focused route tests passing with
`2 passed, 1 warning`, the full backend suite passing with
`310 passed, 1 warning`, `git diff --check` passing, a PR diff check excluding
`.pyc`, virtualenv, cache, and generated files, and green GitHub backend-tests
before merge. PR #87 was merged only after backend-tests were green.

The final merged files were
`backend/alembic/versions/0002_audit_events.py`,
`backend/app/audit/repository.py`, `backend/app/main.py`,
`backend/tests/test_audit_event_repository.py`, `README.md`,
`docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`,
`docs/BACKTEST_RESULTS.md`, and `CHANGELOG.md`.

Interpretation: this is schema/repository readiness only. It prepares for
future explicit audited read-only flows, but it does not yet prove production
audit persistence or identify real users through Entra ID. Future wiring
should remain manual and reviewed. Future controlled repository execution
would require an explicit database connection and tests, and automatic audit
logging and frontend/report-download persistence wiring should not be added
until explicit review.

## Audit Persistence Dry-Run Preview

`scripts/audit_persistence_preview.py` is a manual local dry-run preview for
the audit persistence plan. It builds one synthetic/caller-provided
`audit-event-v0` with fixed `occurred_at_utc=2026-01-01T00:00:00Z`, then calls
the repository SQL builder to preview the parameterized insert plan for
`audit_events`.

```bash
python3 scripts/audit_persistence_preview.py
python3 scripts/audit_persistence_preview.py --pretty
python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty
```

The output explicitly includes `dry_run=true`,
`database_write_performed=false`, `requires_database_url=false`,
`decision_support_only=true`, `read_only_decision_support=true`,
`no_automatic_control=true`, `no_dispatch=true`, `no_activation=true`,
`no_operational_energy_system_integration=true`, and
`human_review_required=true`.

This preview does not persist audit events, access a database, require
`DATABASE_URL`, run SQL, expose an API, use frontend code, write files,
generate PDFs, call EDS/DMI, use ML, use LLMs, add scheduling, add Azure
infrastructure, add auth, add secrets, or add automatic audit logging. Future
controlled repository execution would require an explicit database connection
and tests in a separate reviewed module.

Observed manual validation covered these commands/checks:

```bash
python3 -m py_compile scripts/audit_persistence_preview.py
python3 scripts/audit_persistence_preview.py
python3 scripts/audit_persistence_preview.py --pretty
python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty
python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty
python3 scripts/audit_persistence_preview.py --event-type invalid-event
```

Observed results:

- `py_compile` passed.
- The default command printed compact JSON.
- `--pretty` printed indented JSON.
- `forecast_preview_requested` dry-run passed.
- `report_pdf_exported` dry-run passed.
- `invalid-event` failed safely with exit code `2` and argparse
  invalid-choice output.
- Forbidden-pattern grep on `scripts/audit_persistence_preview.py` returned
  no matches.
- `git diff --check` passed.

The output included `dry_run=true`, `database_write_performed=false`,
`requires_database_url=false`, `event`, and `persistence_plan`. The event
included `event_version=audit-event-v0`, a deterministic `audit_evt_...`
event id, fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
`actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
`decision_support_only=true`, safe metadata only,
`synthetic_preview_only=true`, and `local_only=true`. The persistence plan
included the `audit_events` table target, SQL/SQL preview, parameter
keys/params, `event_id` as the idempotency key, and
`ON CONFLICT (event_id) DO NOTHING` conflict behavior.

Interpretation: this dry-run preview works locally with
synthetic/caller-provided data and demonstrates transformation from
`audit-event-v0` to a parameterized persistence plan. It does not prove live
DB persistence, perform live database writes, run SQL, connect to a database,
expose API/frontend/report/PDF flows, or add automatic audit logging. Future
controlled local audit persistence write testing must be a separate reviewed
module, and report/PDF/frontend/API flows should not be connected to audit
persistence until explicit review.

## Audit DB Write Smoke

`scripts/audit_db_write_smoke.py` is a manual local-only smoke script for one
deterministic synthetic `audit-event-v0` database write. It defaults to
dry-run and does not connect to a database unless a human passes both
`--execute` and an explicit local `--database-url`.

```bash
python3 scripts/audit_db_write_smoke.py --pretty
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty
```

The script accepts only local database URLs by default, such as
`postgresql://localhost/flexsignal_ai`,
`postgresql://127.0.0.1/flexsignal_ai`, or
`postgresql:///flexsignal_ai`. It refuses obvious remote/cloud database URLs
and does not print the raw database URL.

When explicitly executed, the script writes only to `audit_events`, performs
the same idempotent repository insert twice with
`ON CONFLICT (event_id) DO NOTHING`, commits, and optionally reads the row
back by `event_id` only. The event preserves the human-review safety boundary:
read-only decision support, no automatic control, no dispatch, no activation,
no operational energy-system integration, and human review required.

This smoke script does not write energy, forecast, or report data; expose an
API; add frontend code; add automatic audit logging; connect report/PDF/API or
frontend flows; run a scheduler; use Azure infrastructure; add auth or
secrets; call Energi Data Service; call DMI/weather APIs; use ML; use LLMs; or
add control, dispatch, activation, or operational functionality.

## Observed Audit DB Write Smoke Results

Manual validation observed these commands and checks:

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

Observed results:

- `py_compile` passed.
- Focused smoke tests passed with `7 passed`.
- Full backend suite passed with `317 passed, 1 warning`.
- Default dry-run, `--pretty` dry-run, and
  `forecast_preview_requested` dry-run passed.
- `--execute` without `--database-url` failed safely with exit code `2`.
- The remote database URL command failed safely with exit code `2`.
- Forbidden-pattern grep on the script and test returned no matches.
- `git diff --check` passed.
- No live DB writes were performed during those earlier guardrail checks.

Observed output includes `dry_run`, `execute_requested`,
`database_write_performed`, `verify_read_performed`,
`local_database_only`, `event_id`, `event_type`, `table: audit_events`,
`inserted_attempts`, `conflict_behavior`, `safety_boundary`, and `warnings`.
The raw `DATABASE_URL` is not printed. The `event_id` is deterministic.

The safety boundary remained:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Interpretation: the local audit DB write smoke script is implemented and
unit-tested. Dry-run behavior, execute guardrails, and remote DB rejection are
validated.

### Manual Local Audit DB Write Smoke Result

After the `audit-event-v0` foundation, `audit_events` schema/repository,
dry-run preview script, manual local DB write smoke script, and prior full
backend unit validation existed, a human ran the first actual local Postgres
audit-event write smoke.

Observed manual commands:

```bash
DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty
```

Alembic used `PostgresqlImpl`, assumed transactional DDL, ran migration
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
database/session timezone rendering of the stored `timestamptz` instant and is
not a blocker for the smoke result. Future code may normalize read-back
display to UTC if needed.

The smoke output preserved the human-review safety boundary:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Interpretation: local `audit_events` DB write is now manually verified. The
repository insert path works against local Postgres, idempotency works via
`ON CONFLICT (event_id) DO NOTHING`, verify-read by `event_id` works, and the
raw `DATABASE_URL` was not printed. This does not mean production audit
persistence is enabled, does not add automatic audit logging, and does not
connect audit persistence to API, frontend, report, or PDF flows.

Non-goals remain unchanged: no FastAPI endpoint, frontend behavior, automatic
audit logging, report/PDF flow integration, scheduler, Azure infrastructure,
auth/Entra integration, live EDS/DMI calls, ML/LLM use, control, dispatch,
activation, or operational functionality. A future module may add a read-only
API-side audit logging design or manual API audit dry-run. Do not wire
automatic audit persistence into runtime flows yet, and do not add production
DB writes without explicit review.
