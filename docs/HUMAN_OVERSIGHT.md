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

The next audit step should be a manual/local audit preview script. Database
persistence can follow only as a separate reviewed module.
