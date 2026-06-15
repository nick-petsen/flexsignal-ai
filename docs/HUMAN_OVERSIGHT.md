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

`audit-event-v0` does not persist audit logs yet, write files, expose an API,
read from or write to a database, run SQL, call Energi Data Service, call
DMI/weather APIs, use ML, use LLMs, add scheduling, add Azure infrastructure,
add auth, add secrets, or perform operational behavior.

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

The preview is synthetic/local only. It does not persist audit logs yet, write
files, access a database, run SQL, expose an API, use frontend code, call
Energi Data Service, call DMI/weather APIs, use ML, use LLMs, create a
scheduler, add Azure infrastructure, add auth or secrets, or perform automatic
control, dispatch, activation, or operational functionality. It is read-only
decision-support audit structure only and must not be used for automatic
control, dispatch, or activation.

Future audit work should first document audit preview results. Database
persistence can follow only later as a separate reviewed module.
