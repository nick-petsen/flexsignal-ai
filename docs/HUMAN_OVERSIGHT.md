# Human Oversight

## Frontend Report Summary Preview

The dashboard includes a Report summary preview card for the existing
`POST /api/report/summary/preview` endpoint. It appears as JSON preview only
after the manual `Load report summary preview` button is clicked.

The frontend posts an empty JSON body `{}` through the existing backend API
base URL helper. It displays `report_preview_generated`, `pdf_generated`,
`file_written`, `database_query_executed`, `database_write_performed`,
`requires_database_url`, `decision_support_only`, report title, `price_area`,
`generated_at_utc`, current risk summary, forecast window summary,
`key_findings`, `recommended_human_actions`, `safety_notes`, `limitations`,
`explanation`, and `safety_boundary`.

Safety interpretation: the card is read-only decision support for human
review. It does not auto-load, poll, generate PDF output, write files, access
a database from the frontend, run SQL, call live Energi Data Service or
DMI/weather APIs, add backend endpoints, change backend behavior, add ML/LLM
behavior, write audit events, or add operational behavior. It prepares a
future PDF export UI flow without performing PDF generation.

Observed manual frontend report summary preview smoke:

- Backend was started locally.
- Frontend was started locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend.
- Browser opened the local dashboard.
- Report summary preview was loaded manually by button click.
- No auto-load or polling was observed.
- The Report summary preview card was displayed.
- The manual button called `POST /api/report/summary/preview`.
- The preview displayed `report_preview_generated=true`,
  `pdf_generated=false`, `file_written=false`,
  `database_query_executed=false`, `database_write_performed=false`,
  `requires_database_url=false`, and `decision_support_only=true`.
- The displayed report content included the report title, `price_area=DK1`,
  `generated_at_utc`, current risk summary, forecast window summary, `0-24h`,
  `24-48h`, and `48-72h` forecast windows, `key_findings`,
  `recommended_human_actions`, `safety_notes`, `limitations`, `explanation`,
  and `safety_boundary`.

Manual smoke safety interpretation: the frontend shows JSON preview only. No
PDF was generated, no file was written, no database query or write was
performed by this preview, no SQL was executed from the frontend, no live
EDS/DMI API was called, no ML/LLM behavior was added, and no control,
dispatch, or activation behavior occurred. Human review remains required.

## Frontend Report Markdown Preview

The dashboard includes a Report Markdown preview card for the existing
`POST /api/report/markdown/preview` endpoint. It appears as Markdown preview
only after the manual `Load report Markdown preview` button is clicked.

The frontend posts an empty JSON body `{}` through the existing backend API
base URL helper. It displays `markdown_preview_generated`, `pdf_generated`,
`file_written`, `database_query_executed`, `database_write_performed`,
`requires_database_url`, `decision_support_only`, report title, `price_area`,
`generated_at_utc`, rendered Markdown text, and `safety_boundary`.

Safety interpretation: the card is read-only decision support for human
review. It does not auto-load, poll, generate PDF output, write files, access
a database from the frontend, run SQL, call live Energi Data Service or
DMI/weather APIs, add backend endpoints, change backend behavior, add ML/LLM
behavior, or write audit events. It prepares a future PDF export UI flow
without performing PDF generation.

Observed manual frontend Report Markdown preview smoke:

- Backend was started locally.
- Frontend was started locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend.
- Browser opened the local dashboard.
- Report Markdown preview was loaded manually by button click.
- No auto-load or polling was observed.
- The Report Markdown preview card was displayed.
- The manual button called `POST /api/report/markdown/preview`.
- The preview displayed `markdown_preview_generated=true`,
  `pdf_generated=false`, `file_written=false`,
  `database_query_executed=false`, `database_write_performed=false`,
  `requires_database_url=false`, and `decision_support_only=true`.
- The displayed report content included the report title, `price_area=DK1`,
  `generated_at_utc`, rendered Markdown text block, and `safety_boundary`.
- No download button was shown.
- No PDF export button was shown.
- No file generation behavior was visible.

Manual smoke safety interpretation: the frontend shows Markdown preview only.
No PDF was generated, no file was written, no database query or write was
performed by this preview, no SQL was executed from the frontend, no live
EDS/DMI API was called, no ML/LLM behavior was added, and no control,
dispatch, or activation behavior occurred. Human review remains required.

## Backend Report Markdown Preview API

`POST /api/report/markdown/preview` returns a JSON/Markdown preview for
`report-summary-v0` using deterministic synthetic or caller-provided preview
data only. The response includes `markdown_preview_generated=true`,
`pdf_generated=false`, `file_written=false`,
`database_query_executed=false`, `database_write_performed=false`,
`requires_database_url=false`, `decision_support_only=true`, Markdown,
`report_summary`, and the safety boundary.

Safety interpretation: this backend endpoint is read-only decision support for
human review. It prepares a future PDF export flow but does not generate PDF
output, write files, access a database, run SQL, call live Energi Data Service
or DMI/weather APIs, use ML/LLM behavior, add auth, scheduler/Azure
infrastructure, audit writes, or operational functionality. The frontend can
display the returned Markdown preview through a manual button without changing
backend behavior.

Observed manual backend Markdown preview API smoke:

- Command: `POST http://127.0.0.1:8000/api/report/markdown/preview`.
- Request used `Content-Type: application/json` and body `{}`.
- HTTP response returned valid JSON.
- Response included `markdown_preview_generated=true`,
  `pdf_generated=false`, `file_written=false`,
  `database_query_executed=false`, `database_write_performed=false`,
  `requires_database_url=false`, and `decision_support_only=true`.
- `markdown` was a non-empty string.
- `report_summary` was present.
- `safety_boundary` was present.
- Observed Markdown content included the report title, report metadata,
  `price_area=DK1`, `generated_at_utc=2026-01-01T00:00:00Z`, current risk
  summary, forecast window summary, `0-24h`, `24-48h`, and `48-72h` forecast
  windows, key findings, recommended human actions, safety notes,
  limitations, source notes, and read-only / human-review wording.

Manual smoke safety interpretation: the endpoint works without
`DATABASE_URL` and uses deterministic synthetic/caller-provided preview data.
Markdown preview was generated. No PDF was generated, no file was written, no
database query was executed, no database write was performed, no SQL was
executed, no live EDS/DMI API was called, no ML/LLM behavior was used, and no
control, dispatch, or activation behavior occurred. Human review remains
required.

## Frontend Report PDF Dry-Run Preview

The dashboard includes a Report PDF dry-run preview card for the existing
`POST /api/report/pdf/preview` endpoint. It appears as PDF dry-run preview
only after a manual button click. The frontend posts JSON body `{}` through
`NEXT_PUBLIC_API_BASE_URL`.

Required human oversight wording shown in the card:

- PDF dry-run preview only.
- No PDF generated.
- No file written.
- No download available.
- Read-only decision support.
- Human review required.

Displayed fields include `pdf_preview_planned`, `pdf_generated`,
`file_written`, `markdown_preview_generated`, `database_query_executed`,
`database_write_performed`, `requires_database_url`,
`decision_support_only`, `planned_source`, `planned_output_format`,
`markdown_character_count`, optional `markdown_excerpt`, warnings, report
title, `price_area`, `generated_at_utc`, and `safety_boundary`.

Safety interpretation: the frontend display does not modify backend behavior,
add endpoints, generate PDF output, add download behavior, write files,
access a database from the frontend, run SQL, call live EDS/DMI APIs,
auto-load, poll, add auth, add Azure infrastructure, add ML/LLM, or add audit
writes. It prepares a future controlled PDF export flow while keeping the
v0.1 read-only decision-support boundary.

Observed manual frontend Report PDF dry-run preview smoke:

- Backend was started locally.
- Frontend was started locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend.
- Browser opened the local dashboard.
- Report PDF dry-run preview was loaded manually by button click.
- No auto-load or polling was observed.
- The Report PDF dry-run preview card was displayed.
- The manual button called `POST /api/report/pdf/preview`.
- The preview displayed `pdf_preview_planned=true`,
  `pdf_generated=false`, `file_written=false`,
  `markdown_preview_generated=true`, `database_query_executed=false`,
  `database_write_performed=false`, `requires_database_url=false`, and
  `decision_support_only=true`.
- The displayed report content included
  `planned_source=report-summary-v0 + markdown preview`,
  `planned_output_format=pdf`, `markdown_character_count=3621`, report
  title, `price_area=DK1`, `generated_at_utc`, `markdown_excerpt`,
  warnings, and `safety_boundary`.
- No download button was shown.
- No PDF export/generation button was shown.
- No file generation behavior was visible.

Manual smoke safety interpretation: the frontend shows PDF dry-run preview
only. No PDF was generated, no file was written, no download was available,
no database query or write was performed by this preview, no SQL was executed
from the frontend, no live EDS/DMI API was called, no ML/LLM behavior was
added, and no control, dispatch, or activation behavior occurred. Human
review remains required.

## Backend Report PDF Dry-Run Preview API

`POST /api/report/pdf/preview` returns a structured JSON dry-run preview for a
future PDF output path. It uses deterministic synthetic or caller-provided
preview data only, builds `report-summary-v0`, renders Markdown preview
context, and reports `pdf_preview_planned=true`, `pdf_generated=false`,
`file_written=false`, `markdown_preview_generated=true`,
`database_query_executed=false`, `database_write_performed=false`,
`requires_database_url=false`, `decision_support_only=true`,
`planned_source=report-summary-v0 + markdown preview`,
`planned_output_format=pdf`, `report_summary`, Markdown preview metadata,
warnings, and the safety boundary.

Safety interpretation: this endpoint is read-only decision support for human
review and prepares future PDF export only. It does not generate PDF bytes,
write files, access a database, run SQL, call live Energi Data Service or
DMI/weather APIs, use ML/LLM behavior, add auth, scheduler/Azure
infrastructure, audit writes, or operational functionality. It must not be
used for automatic control, dispatch, or activation.

## Backend Report PDF In-Memory Export API

`POST /api/report/pdf/export` returns a read-only `application/pdf` response
for synthetic or caller-provided preview data. It builds `report-summary-v0`,
renders Markdown, and renders non-empty PDF bytes in memory only. The response
uses an attachment filename of `flexsignal-report-preview.pdf` and includes
headers stating decision support only, no file written, no database query, no
database write, and no `DATABASE_URL` requirement.

Safety interpretation: this endpoint is still decision support for human
review only. It does not write files, return a file path, access a database,
run SQL, call live Energi Data Service or DMI/weather APIs, use ML/LLM
behavior, add frontend download behavior, add audit writes, or perform
automatic control, dispatch, activation, or operational functionality.

## Backend Audited Report PDF In-Memory Export API

`POST /api/report/pdf/export/audited` returns the existing report PDF as an
`application/pdf` response and persists one audit event in the same request.
It requires `DATABASE_URL` at request time, while app import and route exposure
still work without `DATABASE_URL`. Missing configuration returns safe HTTP 503
without exposing the raw URL.

On success, the endpoint creates a `report_pdf_export_requested`
`audit-event-v0` event with `action=manual_pdf_export`,
`resource_type=report`, default `price_area=DK1`,
`decision_support_only=true`, `human_review_required=true`,
`pdf_generated_in_memory=true`, `server_side_file_written=false`,
`database_query_executed=false`, underlying PDF-action
`database_write_performed=false`, and
`no_control_dispatch_activation=true`. It writes one row to `audit_events`
only, then generates PDF bytes in memory and returns the attachment filename
`flexsignal-report-preview.pdf`.

Safety interpretation: this endpoint writes no server-side files, accesses no
energy data tables, calls no live EDS/DMI APIs, uses no ML/LLM behavior, adds
no scheduler, Azure, auth, frontend wiring, control, dispatch, activation, or
operational functionality. The top-level response may report
`database_write_performed=true` only because the audit row was persisted to
`audit_events`; the existing unaudited `POST /api/report/pdf/export` endpoint
remains available and unchanged with `database_write_performed=false`.

## Backend Manual PDF Export Audit Preview

`POST /api/audit/preview` supports
`event_type=report_pdf_export_requested` for previewing the audit event that
would describe a manual report PDF export user action. The preview creates an
in-memory `audit-event-v0` style event with `action=manual_pdf_export`,
`resource_type=report`, default `price_area=DK1`, decision support only, and
human review required.

The response is dry-run only and states `dry_run=true`,
`audit_event_created=true`, `audit_event_persisted=false`,
`database_write_performed=false`, and `requires_database_url=false`. It does
not persist audit events, generate a PDF, write files, access a database,
require `DATABASE_URL`, run SQL, call live EDS/DMI APIs, or add control,
dispatch, or activation. Real audit persistence remains a later reviewed step.

Observed manual backend PDF export audit preview API smoke:

- Command: `POST http://127.0.0.1:8000/api/audit/preview`.
- Request used `Content-Type: application/json`.
- Request body was
  `{"event_type":"report_pdf_export_requested","price_area":"DK1"}`.
- Response included `dry_run=true`, `audit_event_created=true`,
  `audit_event_persisted=false`, `database_write_performed=false`, and
  `requires_database_url=false`.
- Response included `event_type=report_pdf_export_requested`,
  `action=manual_pdf_export`, `resource_type=report`,
  `resource_id=report-summary-v0-DK1-872ff94f403e4ddd`,
  `decision_support_only=true`, `price_area=DK1`, and
  `output_format=pdf`.
- Response included `pdf_generated_in_memory=true`,
  `server_side_file_written=false`, `database_query_executed=false`,
  `database_write_performed=false`, and
  `no_control_dispatch_activation=true`.
- `persistence_plan.table` was `audit_events`.
- `persistence_plan.operation` was `insert_audit_event_v0`.
- `conflict_behavior` was `ON CONFLICT (event_id) DO NOTHING`.
- `execution_performed` was `false`.
- Warnings stated dry-run only and no database write.

Manual smoke safety interpretation: the audit preview creates an in-memory
`audit-event-v0` style event only. The audit event was not persisted, SQL was
previewed only and not executed, no database write was performed, no
`DATABASE_URL` was required, no PDF was generated by this audit preview, no
file was written, no live EDS/DMI API was called, no ML/LLM behavior was
used, and no control, dispatch, or activation occurred. Runtime audit
persistence remains a later separately reviewed step. Human review remains
required.

## Backend Manual PDF Export Audit Persistence

`POST /api/audit/pdf-export/persist` persists the reviewed manual PDF export
request audit event. It creates a `report_pdf_export_requested`
`audit-event-v0` event with `action=manual_pdf_export`,
`resource_type=report`, default `price_area=DK1`,
`resource_id=report-summary-v0-DK1-872ff94f403e4ddd`, decision support only,
human review required, `pdf_generated_in_memory=true`,
`server_side_file_written=false`, `database_query_executed=false`, and
`no_control_dispatch_activation=true`.

The endpoint requires `DATABASE_URL` at request time only. App import and
route exposure still work without `DATABASE_URL`; a missing value returns a
safe HTTP 503 response without exposing the raw URL. On success, the endpoint
writes one row to `audit_events` only through the audit writer/repository
foundation, uses `ON CONFLICT (event_id) DO NOTHING`, and returns
`audit_event_created=true`, `audit_event_persisted=true`,
`database_write_performed=true`, `requires_database_url=true`, `event_id`,
`event_type`, `table=audit_events`, `conflict_behavior`, and the preserved
safety boundary.

Safety interpretation: this is audit persistence only. It does not generate a
PDF, write files, provide a frontend download, access energy data tables,
read or write `spot_prices`, `power_balance`, forecast, or other energy
tables, call live EDS/DMI APIs, add a scheduler, add Azure infrastructure,
add auth, use ML/LLMs, or control, dispatch, or activate anything. Human
review remains required. Frontend automatic PDF-download audit persistence
wiring is not added yet.

## Frontend Manual PDF Export Audit Persistence Smoke

The dashboard includes a manual `Audit PDF export persistence` card for
`POST /api/audit/pdf-export/persist`. It appears as an explicit smoke path
only after the user clicks `Persist audit event`.

The frontend posts JSON body `{"price_area":"DK1"}` through the existing
`NEXT_PUBLIC_API_BASE_URL` helper. It displays
`audit_event_created`, `audit_event_persisted`,
`database_query_executed`, `database_write_performed`,
`requires_database_url`, `event_id`, `event_type`, `table`,
`conflict_behavior`, `event.action`, `event.resource_type`,
`event.resource_id`, and warnings. If the backend returns HTTP 503 because
`DATABASE_URL` is missing at request time, the card shows the safe backend
error text and does not expose the raw database URL.

Required human oversight wording shown in the card:

- Audit DB write only.
- Writes only to audit_events.
- Does not generate PDF.
- Does not write files.
- Does not read/write energy data tables.
- Does not call live EDS/DMI APIs.
- Does not control, dispatch, or activate anything.
- Human review remains required.

Safety interpretation: this frontend card is manual audit logging only. It is
not automatically wired to PDF download yet. It does not modify backend,
database, migration, or PDF export endpoint code; does not add auth or Azure
infrastructure; does not call live EDS/DMI APIs; does not add ML/LLM
behavior; and does not add control, dispatch, activation, or operational
functionality.

Observed manual frontend Audit PDF export persistence smoke:

- Frontend opened `http://127.0.0.1:3000`.
- Dashboard card used: `Audit PDF export persistence`.
- Button clicked: `Persist audit event`.
- UI response displayed `audit_event_created=true`,
  `audit_event_persisted=true`, `database_query_executed=false`,
  `database_write_performed=true`, and `requires_database_url=true`.
- UI response displayed
  `event_id=audit_evt_06e3fef85a37a66f24b6a4fb`.
- UI response displayed `event_type=report_pdf_export_requested`.
- UI response displayed `table=audit_events`.
- UI response displayed
  `conflict_behavior=ON CONFLICT (event_id) DO NOTHING`.
- UI response displayed `event.action=manual_pdf_export`,
  `event.resource_type=report`, and
  `event.resource_id=report-summary-v0-DK1-872ff94f403e4ddd`.
- Warnings stated that one `audit-event-v0` row was persisted to
  `audit_events` only, no PDF was generated, no file was written, and no
  energy data tables were read or written.

Observed database confirmation queried:

```sql
select event_id, event_type, action, resource_type, occurred_at_utc
from audit_events
order by occurred_at_utc desc
limit 5;
```

Observed latest row:

- `event_id`: `audit_evt_06e3fef85a37a66f24b6a4fb`
- `event_type`: `report_pdf_export_requested`
- `action`: `manual_pdf_export`
- `resource_type`: `report`
- `occurred_at_utc`: `2026-06-28 23:24:30.534349+02`

Manual frontend smoke safety interpretation: the frontend can manually
trigger an `audit_events`-only database write through the backend. The
`event_id` shown in the UI matched the latest persisted database row,
validating the local frontend-to-backend-to-PostgreSQL audit persistence
path. The action remains manual and isolated, is not automatically wired to
PDF download yet, generated no PDF, wrote no file, read or wrote no energy
data tables, called no live EDS/DMI APIs, used no ML/LLM behavior, and
performed no control, dispatch, activation, or operational energy-system
integration. Human review remains required.

LAN note: a temporary attempt to expose the local dev UI over LAN allowed page
loading, but API actions were not validated over LAN. LAN sharing is out of
MVP scope until CORS, origin, and auth strategy are handled separately. The
verified smoke path is local `127.0.0.1`.

Observed manual backend PDF export audit persistence smoke:

- Command:
  `POST http://127.0.0.1:8000/api/audit/pdf-export/persist`.
- Request used `Content-Type: application/json`.
- Request body was `{"price_area":"DK1"}`.
- HTTP response returned `HTTP/1.1 200 OK`.
- Response `content-type` was `application/json`.
- Response included `audit_event_created=true`,
  `audit_event_persisted=true`, `database_query_executed=false`,
  `database_write_performed=true`, and `requires_database_url=true`.
- Response included `event_type=report_pdf_export_requested`.
- Response included `event_id=audit_evt_b0fb4e51563ca068ab4c2bba`.
- Response included `table=audit_events`.
- Response included
  `conflict_behavior=ON CONFLICT (event_id) DO NOTHING`.
- Response included `action=manual_pdf_export`,
  `resource_type=report`, and
  `resource_id=report-summary-v0-DK1-872ff94f403e4ddd`.
- Response included `decision_support_only=true`,
  `read_only_decision_support=true`, `no_automatic_control=true`,
  `no_dispatch=true`, `no_activation=true`,
  `no_operational_energy_system_integration=true`, and
  `human_review_required=true`.
- Response included `pdf_generated_in_memory=true`,
  `server_side_file_written=false`, and
  `no_control_dispatch_activation=true`.

Observed database confirmation queried:

```sql
select event_id, event_type, action, resource_type, occurred_at_utc
from audit_events
order by occurred_at_utc desc
limit 5;
```

Observed latest row:

- `event_id`: `audit_evt_b0fb4e51563ca068ab4c2bba`
- `event_type`: `report_pdf_export_requested`
- `action`: `manual_pdf_export`
- `resource_type`: `report`
- `occurred_at_utc`: `2026-06-27 00:39:47.295648+02`

Manual smoke safety interpretation: this was the first verified runtime
audit DB write and was limited to `audit_events` only. The endpoint required
`DATABASE_URL` at request time and persisted an audit event for a manual PDF
export request. No PDF was generated by this endpoint, no file was written,
no energy data tables were read or written, no live EDS/DMI APIs were called,
no ML/LLM behavior was used, and no control, dispatch, activation, or
operational energy-system integration occurred. Human review remains
required, and frontend automatic PDF-download audit persistence wiring is
still absent.

Clarification: top-level `database_write_performed=true` describes the
`audit_events` persistence operation. `event.metadata.database_write_performed=false`
describes the underlying PDF export action, which did not itself perform a
database write.

Local smoke note: Alembic with SQLAlchemy/psycopg3 may require a
`postgresql+psycopg://` URL for migration commands. Runtime smoke used
`postgresql://$(whoami)@localhost:5432/flexsignal_ai`. The `audit_events`
timestamp column is `occurred_at_utc`, not `created_at`.

Observed manual backend PDF in-memory export API smoke:

- Command: `POST http://127.0.0.1:8000/api/report/pdf/export`.
- Request used `Content-Type: application/json` and body `{}`.
- HTTP response returned status `200`.
- `content-type` was `application/pdf`.
- `content-disposition` was
  `attachment; filename="flexsignal-report-preview.pdf"`.
- `x-flexsignal-decision-support-only` was `true`.
- `x-flexsignal-file-written` was `false`.
- `x-flexsignal-database-query-executed` was `false`.
- `x-flexsignal-database-write-performed` was `false`.
- `x-flexsignal-requires-database-url` was `false`.
- `byte_length` was `9950`.
- Response body started with `%PDF`.

Manual smoke safety interpretation: the endpoint generated PDF bytes in
memory. No PDF file was written, no file path was returned, no database query
was executed, no database write was performed, no `DATABASE_URL` was required,
no SQL was executed, no live EDS/DMI API was called, no ML/LLM behavior was
used, no audit write occurred, no frontend download UI was added, and no
control, dispatch, or activation behavior occurred. Human review remains
required.

## Frontend Report PDF Manual Download Smoke

The dashboard Report PDF export card uses the existing
`POST /api/report/pdf/export` endpoint only after the user clicks
`Download PDF report`. The download is manual and user-triggered.

Observed manual frontend smoke:

- Backend was started locally.
- Frontend was started locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend.
- Browser opened the local dashboard.
- Report PDF export card was used manually.
- Button clicked: `Download PDF report`.
- Browser downloaded `flexsignal-report-preview.pdf`.
- The downloaded file opened successfully as a PDF.
- No auto-download or polling was observed.

Observed frontend values:

- `download_filename`: `flexsignal-report-preview.pdf`
- `content-type`: `application/pdf`
- `content-disposition`:
  `attachment; filename="flexsignal-report-preview.pdf"`
- `byteLength`: `9950`
- `decision_support_only` header: `true`
- `file_written` header: `false`
- `database_query_executed` header: `false`
- `database_write_performed` header: `false`
- `requires_database_url` header: `false`

Manual smoke safety interpretation: the frontend download is manual and
user-triggered. The backend generated PDF bytes in memory. No server-side file
was written, no file path was returned, no database query was executed by the
PDF export, no database write was performed, no `DATABASE_URL` was required,
no SQL was executed, no live EDS/DMI API was called, no ML/LLM behavior was
used, no audit write occurred, and no control, dispatch, or activation
behavior occurred. Human review remains required.

Other DB-backed dashboard cards may show `DATABASE_URL`-related errors when
started without `DATABASE_URL`. That is expected for those DB-backed endpoints
and is separate from the PDF export smoke result.

Observed manual backend PDF dry-run preview API smoke:

- Command: `POST http://127.0.0.1:8000/api/report/pdf/preview`.
- Request used `Content-Type: application/json` and body `{}`.
- HTTP response returned valid JSON.
- Response included `pdf_preview_planned=true`, `pdf_generated=false`,
  `file_written=false`, `markdown_preview_generated=true`,
  `database_query_executed=false`, `database_write_performed=false`,
  `requires_database_url=false`, and `decision_support_only=true`.
- Response included `planned_source=report-summary-v0 + markdown preview`.
- Response included `planned_output_format=pdf`.
- `report_summary` was present.
- `markdown_excerpt` was present.
- `markdown_character_count=3621`.
- `warnings` was present.
- `safety_boundary` was present.

Observed warnings:

- dry-run preview only.
- no PDF generated.
- no file written.
- no database read/write.
- no live EDS/DMI calls.
- no control, dispatch, or activation.

Manual smoke safety interpretation: the endpoint works without
`DATABASE_URL` and only plans a future PDF export. No PDF bytes were
generated, no PDF renderer was called, no file path or download was returned,
no file was written, no database query was executed, no database write was
performed, no SQL was executed, no live EDS/DMI API was called, no ML/LLM
behavior was used, and no control, dispatch, or activation behavior occurred.
Human review remains required.

## Frontend Forecast Window Visual

The Forecast preview card includes a simple visual for the existing
`forecast-window-v0` response. It appears only after the existing manual
`Load forecast preview` request returns data.

The visual uses only the deterministic synthetic/caller-provided preview
response already returned by the backend. It displays the `0-24h`, `24-48h`,
and `48-72h` windows with `risk_level`, max risk score as a 0-100 score, a
visible horizontal risk bar, `top_reason_codes`, and
`recommended_human_action`. Raw/text forecast details remain visible below
the visual.

Observed manual frontend forecast window visual smoke:

- Backend was started locally.
- Frontend was started locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend.
- Browser opened the local dashboard.
- Forecast preview was loaded manually by button click.
- No auto-load or polling was observed.
- The forecast window visual was displayed.
- The `0-24h` window displayed `risk_level=low` and max risk score `30/100`.
- The `24-48h` window displayed `risk_level=high` and max risk score
  `75/100`.
- The `48-72h` window displayed `risk_level=low` and max risk score `10/100`.
- Each window displayed a visible horizontal risk bar, `top_reason_codes`,
  and `recommended_human_action`.
- Raw/text forecast details remained visible below the visual.
- The response displayed `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, and
  `generated_at_utc=2026-01-01T00:00:00Z`.

Manual smoke safety interpretation: the visual uses only the existing manual
`Load forecast preview` response. The forecast preview uses
synthetic/caller-provided preview data and is deterministic preview for
read-only decision support. Human review remains required. It adds no new
backend endpoint, changes no backend behavior, performs no database write,
executes no SQL, calls no live EDS/DMI API, uses no ML/LLM behavior, performs
no automatic control, performs no dispatch, and performs no activation.

## Frontend Current Risk Score Visual

The Current surplus risk card includes a simple visual labeled
`Decision-support risk score`. It appears only after the existing manual
`Load current risk` request returns a risk result.

The visual uses only the current-risk response already returned by the
backend. It displays valid `risk_score` values as a 0-100 HTML/CSS bar,
displays `risk_level`, keeps the raw text/details visible below the visual,
and handles missing or invalid score/level fields safely.

The UI wording remains explicit: `Decision-support risk score`,
`Read-only recommendation context`, and `Human review required`.

Safety interpretation: the visual is dashboard readability only. It does not
auto-load, poll, forecast by itself, trigger recommendations by itself, add a
backend endpoint, change backend behavior, execute SQL, write to the database,
call Energi Data Service or DMI/weather APIs from the browser, use ML/LLM
behavior, write audit events, wire report/PDF flows, or add automation,
control, dispatch, activation, closed-loop, live-control, or operational
functionality. Human review remains required.

Observed validation:

- `npm run build` passed after `npm ci` installed frontend dependencies from
  the existing lockfile.
- `git diff --check` passed.
- `npm run lint` did not exist.
- `npm run typecheck` did not exist.
- `npm audit` reported 2 moderate findings, but dependency files were not
  changed in this scoped UI/docs task.
- No backend server was started.
- No database was accessed.
- No SQL was executed.
- No live Energi Data Service or DMI/weather APIs were called.

Observed manual frontend risk score visual smoke:

- Backend was started locally.
- Frontend was started locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend.
- Browser opened the local dashboard.
- Current surplus risk was loaded manually by button click.
- No auto-load or polling was observed.
- DK1 displayed `price_area=DK1`, `risk_score=35/100`,
  `risk_level=medium`, the visible `Decision-support risk score` box, a
  visible 0-100 horizontal bar, `Human review required`, raw/text risk
  details below the visual, and `decision_support_only=true`.
- DK2 displayed `price_area=DK2`, `risk_score=20/100`, `risk_level=low`, the
  visible `Decision-support risk score` box, a visible 0-100 horizontal bar,
  `Human review required`, raw/text risk details below the visual, and
  `decision_support_only=true`.

Manual smoke safety interpretation: the visual uses only the existing manual
`Load current risk` response. It adds no new backend endpoint, changes no
backend behavior, performs no database write, executes no SQL, calls no live
EDS/DMI API, uses no ML/LLM behavior, performs no automatic control, performs
no dispatch, and performs no activation. Human review remains required.

Next step: a future module may improve dashboard layout and visual hierarchy.
That follow-up should not add ingestion, automation, database writes, backend
changes, ML/LLM behavior, or operational functionality without explicit
review.

## Frontend Read-Only Trend Charts

The Spot prices card includes a simple SVG chart labeled `Spot price trend`.
It plots EUR/MWh over timestamp order using only manual read-only spot price
rows already returned by the existing backend `Load spot prices` request. It
appears only when returned spot price rows exist, keeps the existing table,
and uses the currently selected `DK1` or `DK2` result through the existing
price-area selector.

The Power balance card includes a simple SVG chart labeled
`Power balance trend`. It plots production MW over timestamp order using only
manual read-only power balance rows already returned by the existing backend
`Load power balance` request. It appears only when returned power balance rows
exist, keeps the existing table, and uses the currently selected `DK1` or
`DK2` result through the existing price-area selector.

The charts use lightweight inline SVG/HTML/CSS and do not add a charting
dependency. They handle empty, single-point, multi-point, missing, and invalid
values safely.

Together these charts complete the first MVP pair of read-only dashboard
visualizations: spot price and power balance / production. They are both
driven by existing manual load actions and existing backend responses.

The charts are read-only dashboard visualization only. They do not forecast,
trade, control assets, auto-load, poll, call a new endpoint, call Energi Data
Service or DMI/weather APIs from the browser, execute SQL, write to the
database, add migrations, add auth, add Azure infrastructure, use ML/LLM
behavior, write audit events, wire report/PDF flows, or add control,
dispatch, activation, closed-loop, live-control, or operational functionality.

Safety wording in the UI remains read-only: `Manual read-only spot price rows`
or `Manual read-only power balance rows`, plus
`Trend from loaded backend rows`.

Observed manual frontend dashboard chart smoke:

- Backend was started locally.
- Frontend was started locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend.
- Browser opened the local dashboard.
- Requests were manual button clicks only.
- No auto-load or polling was observed.
- DK1 spot prices loaded; the spot price table and spot price trend chart were
  displayed.
- DK1 power balance loaded; the power balance table and power balance trend
  chart were displayed.
- After switching the price area to DK2, DK2 spot prices loaded; the spot
  price table and spot price trend chart were displayed.
- DK2 power balance loaded; the power balance table and power balance trend
  chart were displayed.
- Existing tables remained visible, and charts used only manually loaded
  backend rows.

Manual chart smoke safety interpretation: the frontend charts remain
lightweight inline visualization, add no charting dependency, add no backend
endpoint, make no browser call to Energi Data Service, make no DMI/weather
call, execute no SQL from the frontend, write nothing to the database, execute
no forecast logic from the chart itself, and do not dispatch, activate, poll,
control energy assets, automate workflows, or add operational behavior.

Observed validation:

- `npm run build` passed.
- `git diff --check` passed.
- `npm run lint` did not exist.
- `npm run typecheck` did not exist.
- No backend server was started.
- No database was accessed.
- No SQL was executed.
- No live Energi Data Service or DMI/weather APIs were called.

Future dashboard layout and chart readability work, or a manual local frontend
smoke test for both charts, must not add ingestion, automation, backend
changes, database writes, SQL execution, live API calls, or operational
behavior without explicit review.

## DB-Backed Energy Freshness Read API

`GET /api/energy/freshness/read?price_area=DK1|DK2` exposes the controlled
DB-backed read path for `eds-data-freshness-read-model-v0`. It is read-only
decision support for future dashboard live data trust indicators.

The endpoint supports only `DK1` and `DK2`; invalid `price_area` values return
HTTP 400.

The endpoint requires `DATABASE_URL` only when the request is executed; app
import still exposes the route without that environment variable. If
`DATABASE_URL` is missing at request time, the API returns HTTP 503 with a
safe warning and does not expose the raw value. When configured, it opens a
request-scoped database connection, delegates to
`backend/app/db/repositories/energy_freshness_reader.py`, and returns spot
price and power balance freshness summaries for `DK1` or `DK2`.

The API executes SELECT-only freshness reads against stored data. It does not
write to the database, add migrations, fetch new Energi Data Service data,
call weather APIs, trigger ingestion, schedule jobs, write audit events,
modify the frontend, or perform control, dispatch, activation, closed-loop,
live-control, or operational functionality.

The response includes `price_area`, `dry_run=false`,
`database_query_executed=true` on success,
`database_write_performed=false`, `requires_database_url=true`,
`freshness_result`, `spot_price_freshness`, `power_balance_freshness`,
warnings, and the explicit read-only human-review safety boundary:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Observed validation:

- Focused API freshness read tests passed: `9 passed, 1 warning`.
- Full backend suite passed: `483 passed, 1 warning`.
- `py_compile` passed.
- Forbidden-pattern grep matched only defensive/negative assertions in tests.
- `git diff --check` passed.
- Tests used mocked database connections only.
- No live DB writes were performed.

Observed local API smoke:

The backend was started locally with
`DATABASE_URL=postgresql://localhost/flexsignal_ai` and the DB-backed
freshness read endpoint was called for `DK1`, `DK2`, and invalid `SE3`.
The endpoint performed SELECT-only freshness reads, no database writes were
performed, no live EDS/DMI calls were made, no ingestion was triggered, and no
frontend changes were involved.

| Area | HTTP | `dry_run` | `database_query_executed` | `database_write_performed` | `requires_database_url` | Spot price rows | Spot price latest timestamp | Power balance rows | Power balance latest timestamp |
| --- | ---: | --- | --- | --- | --- | ---: | --- | ---: | --- |
| DK1 | 200 | false | true | false | true | 53 | `2026-06-11T21:45:00+02:00` | 53 | `2026-06-10T17:00:00+02:00` |
| DK2 | 200 | false | true | false | true | 50 | `2026-06-11T21:45:00+02:00` | 50 | `2026-06-10T17:00:00+02:00` |

Invalid `price_area=SE3` returned HTTP 400 with `Unsupported price_area`.
The read-only human-review safety boundary was preserved. This proves local
DB-backed API freshness reads work against the observed local data. It does
not mean production monitoring or Azure deployment exists, and it prepares
manual frontend data trust display only.

Interpretation: this is the first controlled DB-backed freshness API. It
performs read-only SELECT execution only, improves MVP data trust readiness,
does not perform ingestion, and does not verify production freshness yet. The
frontend can now manually display this endpoint through the backend API only;
it does not execute SQL, write to the database, fetch live EDS/DMI data, or
imply production monitoring exists.

## Frontend DB-Backed Energy Freshness Read Wiring

The dashboard freshness card now supports a manual DB-backed read mode while
preserving the existing dry-run preview path. The frontend helper
`fetchEnergyFreshnessRead(priceArea)` calls
`GET /api/energy/freshness/read?price_area=DK1|DK2` through the backend API
base URL helper. The existing `fetchEnergyFreshness()` helper continues to
call the dry-run preview endpoint at
`GET /api/energy/freshness?price_area=DK1|DK2`.

The DB-backed card display is SELECT-only result presentation. It shows
`price_area`, `dry_run`, `database_query_executed`,
`database_write_performed`, `requires_database_url`,
`spot_price_freshness.latest_timestamp`,
`spot_price_freshness.row_count`,
`power_balance_freshness.latest_timestamp`,
`power_balance_freshness.row_count`, warnings, and the read-only
human-review safety boundary. If the backend returns HTTP 503 because
`DATABASE_URL` is missing, the UI maps that to
`DB-backed freshness read requires backend DATABASE_URL.`

Safety interpretation: the browser does not execute SQL, access the database
directly, write to the database, trigger ingestion, call live Energi Data
Service, or call DMI/weather APIs. It only displays stored/configured
freshness data returned by the backend. This remains read-only decision
support for human review, not production monitoring and not operational
control.

Observed frontend wiring validation:

- `npm run build` passed.
- `git diff --check` passed.
- `npm run lint` did not exist.
- `npm run typecheck` did not exist.
- No backend server was started.
- No frontend dev server was started.
- No database was accessed.
- No SQL was executed.
- No live Energi Data Service or DMI/weather APIs were called.

Observed manual frontend plus backend smoke:

The backend was started locally with
`DATABASE_URL=postgresql://localhost/flexsignal_ai`, the frontend was started
locally with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`, and the local
dashboard was opened in a browser. Requests were manual button clicks only;
no automatic loading or polling was observed.

The dashboard loaded spot prices, power balance, current surplus risk,
forecast preview, DB-backed energy freshness reads, and dry-run freshness
query-plan previews for DK1 and DK2. The DB-backed card wording identified
the path as a DB-backed freshness read and SELECT-only read, showed no
database write performed, described freshness of stored local/configured
database data, did not imply ingestion had run, and stated that it does not
fetch new EDS/DMI data.

| Area | `dry_run` | `database_query_executed` | `database_write_performed` | `requires_database_url` | Spot price rows | Spot price latest timestamp | Power balance rows | Power balance latest timestamp |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- |
| DK1 | false | true | false | true | 53 | `2026-06-11T21:45:00+02:00` | 53 | `2026-06-10T17:00:00+02:00` |
| DK2 | false | true | false | true | 50 | `2026-06-11T21:45:00+02:00` | 50 | `2026-06-10T17:00:00+02:00` |

The dry-run freshness preview returned `dry_run=true`,
`database_query_executed=false`, `database_write_performed=false`, and
`requires_database_url=false`; spot price and power balance query plans were
present, and no SQL was executed by the dry-run endpoint. The read-only
human-review safety boundary was preserved for both DB-backed and dry-run
paths.

Non-goals: this documentation step did not change backend behavior, add a new
backend endpoint, add database code, execute SQL from the frontend, write to a
database, add migrations, call live Energi Data Service, call DMI/weather
APIs, add auth, add Azure infrastructure, add ML/LLM behavior, write audit
events, wire report/PDF flows, or add control, dispatch, activation, or
operational functionality.

Next steps may document a manual frontend/backend smoke guide for running the
backend and frontend together locally, or separately improve dashboard graphs.
Those future modules must not add ingestion, automation, or database writes
without explicit review.

## DB-Executed Energy Freshness Reader

`backend/app/db/repositories/energy_freshness_reader.py` now provides a
backend-only read-only reader for `eds-data-freshness-read-model-v0`. It uses
the existing query-plan builders in
`backend/app/db/repositories/energy_freshness.py`, defensively validates those
plans as parameterized SELECT-only SQL, and executes them only through an
explicit caller-provided database connection.

The reader returns structured dictionaries for spot price freshness, power
balance freshness, and a combined summary. Results include `price_area`,
`database_query_executed=true`, `database_write_performed=false`, source
label, earliest/latest timestamps, row count, empty-row warnings, and the
explicit read-only human-review safety boundary.

Implemented reader functions:

- `read_spot_price_freshness`
- `read_power_balance_freshness`
- `read_energy_freshness_summary`

SQL safety is enforced before cursor execution. Query plans must be
parameterized and must start with `SELECT`; mutating SQL tokens are blocked
before execution, including `INSERT`, `UPDATE`, `DELETE`, `UPSERT`, `CREATE`,
`ALTER`, `DROP`, `TRUNCATE`, and `MERGE`. Price areas outside `DK1` and `DK2`
are rejected. No write behavior is implemented.

The combined summary includes `spot_price_freshness`,
`power_balance_freshness`, `warnings`, and the same safety boundary. The
safety boundary is:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Boundary: this reader does not create database connections, read
`DATABASE_URL`, call live Energi Data Service, call DMI/weather APIs, write to
the database, add migrations, modify the frontend, schedule jobs, add
Azure/auth behavior, use ML/LLMs, write audit events, wire report/PDF flows,
or add control, dispatch, activation, closed-loop, live-control, or
operational functionality. The FastAPI read endpoint now creates the
request-scoped connection and calls this reader for SELECT-only freshness
reads.

Observed validation:

- Focused energy freshness reader tests passed: `24 passed`.
- Full backend suite passed: `466 passed, 1 warning`.
- `py_compile` passed.
- Forbidden-pattern grep matched only safety-boundary keys, defensive
  blocked-token validation, and negative assertions/unsafe-plan tests.
- `git diff --check` passed.
- Tests used fake connection/cursor objects only.
- No live DB writes were performed.

Interpretation: this reader now has a controlled DB-backed read API wrapper.
It proves read-only freshness SELECT execution through explicit database
connections, but it is not connected to the frontend yet, does not fetch new
data, and does not write data. A future module may add frontend wiring to the
DB-backed read endpoint without adding DB writes, ingestion, automation, or
operational behavior.

## Manual Energy Freshness DB Smoke

`scripts/energy_freshness_db_smoke.py` provides the controlled local DB
freshness smoke script for the reader above. It defaults to dry-run JSON using
`backend/app/db/repositories/energy_freshness.py` and only performs DB reads
when a human supplies both `--execute` and an explicit local `--database-url`.

Usage:

```bash
python3 scripts/energy_freshness_db_smoke.py --price-area DK1 --pretty
python3 scripts/energy_freshness_db_smoke.py --price-area DK1 --execute --database-url postgresql://localhost/flexsignal_ai --pretty
```

Local URL validation accepts localhost, `127.0.0.1`, and local socket-style
PostgreSQL URLs such as `postgresql:///flexsignal_ai`. Remote/cloud URLs are
refused, and raw database URLs are not printed.

The script performs SELECT-only freshness reads through
`read_energy_freshness_summary(...)`, writes no data, does not fetch EDS/DMI
data, does not expose a FastAPI endpoint, does not modify the frontend, does
not add migrations or jobs, and does not add auth, Azure, ML/LLM, audit
writes, report/PDF wiring, control, dispatch, activation, or operational
energy-system integration.

Observed local DB smoke results:

| Area | DB query executed | DB write performed | Spot price rows | Spot price latest timestamp | Power balance rows | Power balance latest timestamp | Warnings |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
| DK1 | true | false | 53 | `2026-06-11T21:45:00+02:00` | 53 | `2026-06-10T17:00:00+02:00` | `[]` |
| DK2 | true | false | 50 | `2026-06-11T21:45:00+02:00` | 50 | `2026-06-10T17:00:00+02:00` | `[]` |

The observed smoke used explicit `--execute` and a local `--database-url`.
Reads were SELECT-only, no database writes were performed, no live Energi Data
Service or DMI/weather calls were made, and no backend or frontend server was
started. The result proves local DB-backed freshness reads work against the
observed local data. It does not mean production freshness monitoring exists;
it prepares future DB-backed API/dashboard freshness indicators only.

## EDS Data Freshness Preview API

`GET /api/energy/freshness?price_area=DK1|DK2` exposes a read-only preview of
`eds-data-freshness-read-model-v0` for data freshness indicators. It
exists because product work has moved back toward data/dashboard readiness
while preserving the v0.1 human-review boundary.

The implementation in `backend/app/db/repositories/energy_freshness.py`
builds pure query-plan objects for DK1/DK2 stored energy data. The FastAPI
wrapper in `backend/app/api/energy_freshness.py` returns those plans with
focused coverage in `backend/tests/test_energy_freshness.py` and
`backend/tests/test_api_energy_freshness.py`. Implemented previews include:

- Spot price freshness summary.
- Power balance freshness summary.
- Combined energy freshness summary.

The API returns query-plan previews only. It includes `price_area`,
`dry_run=true`, `database_query_executed=false`,
`database_write_performed=false`, `requires_database_url=false`, the combined
`freshness_plans`, `spot_price_freshness_plan`,
`power_balance_freshness_plan`, warnings, and the explicit safety boundary.
Plans include parameterized SELECT SQL, params, source labels,
earliest/latest timestamp fields, row count fields, and empty-row warnings.
Price areas are limited to `DK1` and `DK2`; invalid values outside those areas
return HTTP 400.

This is a read-only foundation for human oversight. The frontend dashboard has
a manual energy freshness card backed by `fetchEnergyFreshness()`. The card
calls this endpoint for `DK1`/`DK2` through the existing
`NEXT_PUBLIC_API_BASE_URL` pattern and displays the dry-run query-plan
preview, `database_query_executed`, `database_write_performed`,
`requires_database_url`, spot price and power balance freshness plan status,
warnings, and the safety boundary. The card does not claim that live data
freshness has been measured.

Safety boundary: the preview API and frontend card do not call live Energi
Data Service, call DMI/weather APIs, connect to a database, read
`DATABASE_URL`, execute SQL, write to a database, schedule jobs, add Azure
infrastructure, add auth, use ML/LLMs, write audit events, or perform
automatic control, dispatch, activation, closed-loop workflows, live control
signals, or operational functionality.

Observed validation:

- Focused energy freshness API tests passed: `12 passed, 1 warning`.
- Focused energy freshness tests passed: `21 passed`.
- Full backend suite passed: `442 passed, 1 warning`.
- `py_compile` passed.
- Forbidden-pattern grep matched only required safety flags and
  negative/safety assertions in tests.
- `git diff --check` passed.
- No live DB writes were performed.

Observed frontend card validation:

- `npm run build` passed.
- `git diff --check` passed.
- `npm run lint` did not exist.
- `npm run typecheck` did not exist.
- No backend server was started.
- No frontend dev server was started.
- No database was accessed.
- No SQL was executed.
- No live Energi Data Service or DMI/weather APIs were called.

Interpretation: this remains a dry-run preview only. It does not fetch new
data, execute queries, prove live data freshness, or enable live ingestion or
control behavior. The frontend card prepares dashboard trust indicators by
showing the reviewed query plans and safety flags for human review. UI wording
explicitly communicates freshness query plan preview only, no database query
executed, no database write performed, no new EDS/DMI fetch, and read-only
decision support.

Non-goals: this documentation step did not change backend behavior, add a
backend endpoint, add database code, execute SQL, write to a database, add
migrations, call live Energi Data Service, call DMI/weather APIs, add auth,
add Azure infrastructure, add ML/LLM behavior, write audit events, wire
report/PDF flows, or add control, dispatch, activation, closed-loop,
live-control, or operational functionality. DB-backed SELECT execution now
exists through the backend read endpoint, and the dashboard has a manual
display path for those read results. Live ingestion remains deferred.

## Report Summary Preview API Smoke

Observed manual API smoke command:

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

Observed report summary:

- `report_version=report-summary-v0`
- `price_area=DK1`
- `generated_at_utc=2026-01-01T00:00:00Z`
- `current_risk_summary.status=available`
- `current_risk_summary.risk_level=medium`
- `forecast_window_summary.status=available`
- `forecast_window_summary.model_version=rule-engine-v0+forecast-window-v0`
- Forecast windows were present for `0-24h`, `24-48h`, and `48-72h`.

Safety interpretation: the endpoint works without `DATABASE_URL` and uses
deterministic synthetic/caller-provided preview data. No PDF was generated, no
file was written, no database query was executed, no database write was
performed, no SQL was executed, no live EDS/DMI API was called, no ML/LLM
behavior was used, and no control, dispatch, or activation behavior occurred.
Human review remains required.

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

## Audit API Dry-Run Preview

`POST /api/audit/preview` exposes a read-only FastAPI wrapper around the
runtime audit persistence planner for these explicit event types:
`current_risk_viewed`, `forecast_preview_requested`,
`report_summary_built`, `report_markdown_rendered`, and
`report_pdf_exported`.

The endpoint accepts caller-provided event metadata such as `price_area`,
optional actor fields, optional request/source identifiers, optional
`occurred_at_utc`, and relevant report or forecast version fields. It rejects
unsupported event types and price areas outside `DK1`/`DK2` with HTTP 400.
When actor fields are omitted, the API uses `actor_type=local_user` and
`actor_id=unknown-local-user`. `local_user` is an allowed audit actor type.

The response is a dry-run persistence plan only. It includes `dry_run=true`,
`database_write_performed=false`, `requires_database_url=false`, `event`,
`persistence_plan`, `event_id`, `event_type`, `table=audit_events`,
`conflict_behavior`, `safety_boundary`, and `warnings`. The plan is built by
`backend/app/audit/runtime_plan.py`, targets `audit_events`, uses `event_id`
as the idempotency key, and previews
`ON CONFLICT (event_id) DO NOTHING`.

This API does not write to the database, call the audit writer service, create
database connections, read `DATABASE_URL`, run SQL, write files, add automatic
audit logging, call EDS/DMI, generate reports or PDFs, modify frontend
behavior, use ML or LLMs, add scheduler/auth/Azure behavior, or connect to
report/PDF/forecast/risk runtime flows. It is a preview endpoint for future
reviewed audit integration only.

Validation behavior:

- Unsupported `event_type` returns HTTP 400.
- Unsupported `price_area` outside `DK1`/`DK2` returns HTTP 400.
- Responses contain no raw `DATABASE_URL`, secrets, tokens, full headers, or
  full request bodies.
- The read-only decision-support safety boundary is preserved.

Observed validation:

- Route allowlist was updated so `/api/audit/preview` is treated as an allowed
  read-only preview POST.
- Focused mutating-route check passed: `1 passed, 1 warning`.
- Focused audit preview API tests passed: `16 passed, 1 warning`.
- Full backend suite passed: `409 passed, 1 warning`.
- `py_compile` passed.
- `git diff --check` passed.
- No live DB writes were performed.

Interpretation: the audit preview API is a reviewed read-only preview
endpoint. It exposes audit persistence plans for inspection only. It does not
enable production audit persistence, add automatic audit logging, or connect
audit persistence to forecast, risk, report, PDF, or frontend runtime flows.
Future runtime audit persistence remains deferred and requires explicit
review.

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

Non-goals remain unchanged for production persistence: no automatic audit
logging, report/PDF flow integration, scheduler, Azure infrastructure,
auth/Entra integration, live EDS/DMI calls, ML/LLM use, control, dispatch,
activation, or operational functionality. The reviewed API audit dry-run
preview is documented separately and remains inspection-only. Do not wire
automatic audit persistence into runtime flows yet, and do not add production
DB writes without explicit review.

## Audit Writer Service Foundation

`backend/app/audit/writer.py` adds an explicit audit writer service foundation
for `audit-event-v0`. The service requires a caller-provided database
connection object, uses the existing audit repository insert SQL builder, and
executes one parameterized `audit_events` insert only after validating the
decision-support safety boundary.

The writer does not create database connections, does not read `DATABASE_URL`,
does not add FastAPI endpoints, and is not wired into API, frontend, report,
PDF, scheduler, auth, or automatic audit logging flows. It returns a structured
result with the event id, event type, table, row count, conflict behavior,
write-performed flag, safety-boundary-preserved flag, and warnings.

The public writer entry point is `write_audit_event(conn, event)`.
`execute_audit_event_insert` is an alias for the same behavior. The explicit
connection object is required so the service does not create database
connections and does not read `DATABASE_URL`.

Before executing SQL, the writer validates `audit-event-v0`,
`decision_support_only=true`, and the complete safety boundary:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Invalid events raise `ValueError` and execute no SQL. Valid events return a
structured result containing `event_id`, `event_type`, `table`,
`database_write_performed`, `rowcount`, `conflict_behavior`,
`safety_boundary_preserved`, and `warnings`.

Observed audit writer validation:

- Focused audit writer tests passed: `14 passed`.
- Full backend suite passed: `331 passed, 1 warning`.
- `py_compile` passed for `backend/app/audit/writer.py` and
  `backend/tests/test_audit_writer.py`.
- Grep matched only safety-boundary strings and negative/static assertions.
- `git diff --check` passed.
- Tests used fake connection and cursor objects only.
- No live database writes were performed.

Interpretation: the writer is a backend foundation only. It proves a testable
write boundary around the repository insert path, but it does not enable
production audit persistence, add automatic audit logging, expose an API,
modify frontend behavior, connect report/PDF flows to audit persistence, or
create runtime integration.

Non-goals remain unchanged for the writer itself: no frontend behavior,
automatic audit logging, report/PDF flow integration, scheduler, Azure
infrastructure, auth/Entra integration, live EDS/DMI calls, ML/LLM use,
control, dispatch, activation, or operational functionality. The reviewed API
audit dry-run preview is documented separately and remains inspection-only.
Do not wire automatic audit persistence into runtime flows yet, and do not add
production DB writes without explicit review.

## Runtime Audit Event Factory

`backend/app/audit/runtime_events.py` adds a pure backend factory for
standardized future runtime `audit-event-v0` dictionaries. It constructs
events for current-risk views, forecast-preview requests, report-summary
builds, report Markdown rendering, and report PDF export previews.

The implemented factory functions are:

- `build_current_risk_viewed_event`
- `build_forecast_preview_requested_event`
- `build_report_summary_built_event`
- `build_report_markdown_rendered_event`
- `build_report_pdf_exported_event`

The factory only returns dictionaries built through `build_audit_event(...)`.
It accepts explicit primitive inputs, standardizes event/action/resource
mapping, and adds minimal safe metadata with
`runtime_factory_version=audit-runtime-event-factory-v0`.

Standardized mappings:

| Event type | Action | Resource type | Resource id includes |
| --- | --- | --- | --- |
| `current_risk_viewed` | `view_current_risk` | `risk_snapshot` | `price_area` |
| `forecast_preview_requested` | `preview_forecast` | `forecast_preview` | `price_area`, `forecast-window-v0` |
| `report_summary_built` | `build_report_summary` | `report_summary` | `price_area`, `report-summary-v0` |
| `report_markdown_rendered` | `render_report_markdown` | `report_markdown` | `price_area`, `report-summary-v0` |
| `report_pdf_exported` | `preview_report_pdf_export` | `report_pdf` | `price_area`, `report-summary-v0` |

Metadata may include:

- `price_area`
- `request_id` if provided
- `source` if provided
- `forecast_window_version` where relevant
- `report_version` where relevant
- `output_format` where relevant
- optional forecast `model_version` if provided
- `runtime_factory_version`

Metadata must not include raw `DATABASE_URL`, secrets, tokens, raw user
claims, full request headers, or full request bodies.

Every generated event preserves:

- `event_version: audit-event-v0`
- `decision_support_only: true`
- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

Observed validation:

- Focused runtime event tests passed: `30 passed`.
- Full backend suite passed: `361 passed, 1 warning`.
- `py_compile` passed for `runtime_events` and tests.
- Forbidden-pattern grep returned no matches.
- `git diff --check` passed.
- Tests were pure unit tests only.
- No live DB writes were performed.

Interpretation: the runtime audit event factory is a backend foundation only.
It standardizes future runtime audit-event-v0 construction, but it does not
enable production audit persistence, add automatic audit logging, call the
audit writer, create database connections, read `DATABASE_URL`, write files,
perform API calls, expose FastAPI routes, import FastAPI/APIRouter, modify
frontend behavior, or connect report/PDF/API/frontend flows.

Non-goals remain unchanged for the factory itself: no automatic audit logging,
no audit writer call, no database write, no database connection, no
`DATABASE_URL` handling, no migrations, no report/PDF runtime wiring, no
scheduler, no Azure infrastructure, no auth/Entra integration, no live
EDS/DMI calls, no ML/LLM use, and no control, dispatch, activation, or
operational functionality.

The reviewed API audit dry-run preview is documented separately. Do not wire
automatic audit persistence into runtime flows yet, and do not add production
DB writes without explicit review.

## Runtime Audit Persistence Dry-Run Planner

`backend/app/audit/runtime_plan.py` adds a pure backend dry-run planner for
future runtime audit persistence. It combines the runtime event factory in
`backend/app/audit/runtime_events.py` with the repository INSERT SQL builder
in `backend/app/audit/repository.py` and returns a dictionary plan only.

Implemented planner functions:

- `build_current_risk_viewed_audit_plan`
- `build_forecast_preview_requested_audit_plan`
- `build_report_summary_built_audit_plan`
- `build_report_markdown_rendered_audit_plan`
- `build_report_pdf_exported_audit_plan`

Each output includes `dry_run=true`,
`database_write_performed=false`, `requires_database_url=false`, `event`,
`persistence_plan`, `event_id`, `event_type`, `table=audit_events`,
`conflict_behavior`, `safety_boundary`, and `warnings`.

The persistence plan exposes the repository-built SQL preview, parameter
keys/params, `event_id` idempotency key, target table, operation, and explicit
non-execution status. The target table is `audit_events`; the idempotency key
is `event_id`; conflict behavior is
`ON CONFLICT (event_id) DO NOTHING`. SQL and parameters are previewed only, and
no SQL is executed.

Metadata remains safe and minimal. Planner output does not include raw
`DATABASE_URL`, secrets, tokens, raw user claims, full request headers, or full
request bodies. Every event preserves:

- `read_only_decision_support: true`
- `no_automatic_control: true`
- `no_dispatch: true`
- `no_activation: true`
- `no_operational_energy_system_integration: true`
- `human_review_required: true`

This planner does not write to the database, call the audit writer service,
create database connections, read `DATABASE_URL`, execute SQL, modify frontend
behavior, write files, add migrations, integrate with report/PDF/frontend
flows, add scheduler/auth/Azure infrastructure, call EDS/DMI, use ML/LLMs, or
add control, dispatch, activation, or operational functionality. It prepared
the reviewed API audit dry-run preview path documented above.

Observed runtime dry-run planner validation:

- Focused runtime plan tests passed: `32 passed`.
- Full backend suite passed: `393 passed, 1 warning`.
- `py_compile` passed for `runtime_plan` and tests.
- Forbidden-pattern grep matched only safety/negative assertions in tests.
- `git diff --check` passed.
- Tests were pure unit tests only.
- No live DB writes were performed.

Interpretation: the runtime dry-run planner is a backend foundation only. It
supports the reviewed API audit dry-run preview, but it does not enable
production audit persistence, add automatic audit logging, call the audit
writer, modify frontend behavior, or connect report/PDF flows.

Non-goals remain unchanged for runtime persistence: no automatic audit
logging, no audit writer call, no database write, no database connection, no
`DATABASE_URL` handling, no migrations, no report/PDF runtime wiring, no
scheduler, no Azure infrastructure, no auth/Entra integration, no live EDS/DMI
calls, no ML/LLM use, and no control, dispatch, activation, or operational
functionality. Do not wire automatic audit persistence into runtime flows yet,
and do not add production DB writes without explicit review.
