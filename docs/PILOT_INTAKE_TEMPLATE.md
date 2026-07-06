# Customer Pilot Intake Template

## Introduction

N&O Predict / FlexSignal AI has a public DK1/DK2 backtest that demonstrates
system-level and market-level surplus-risk signal behavior using public Danish
electricity data.

A customer pilot tests a different question: whether the public signal matches
the customer's operational reality. The pilot compares public surplus-risk
windows with customer data, operating constraints, price context, and human
operational interpretation.

The pilot remains read-only decision support. It does not perform automatic
control, dispatch, activation, live control signaling, or asset integration.

## Pilot Purpose

- Compare public DK1/DK2 surplus-risk windows with customer data.
- Identify candidate windows for human review.
- Estimate customer-specific potential only after customer data is validated.
- Keep the pilot as read-only decision support for human review.

## Common Minimum Data

This section applies to all pilot customers.

Please provide the following data where available:

- Site name or anonymized site id.
- DK1/DK2 price area.
- Historical timestamped electricity load, production, or relevant energy time
  series.
- Timestamp timezone.
- MWh/kWh or MW/kW units.
- Flexible capacity estimate.
- Flexible energy estimate.
- Operating constraints.
- Operating schedule or availability windows.
- Tariff or price agreement context if available.
- Historical operational decisions or events if available.
- Contact person for operational interpretation.

Minimum dataset for an initial pilot:

- 3-12 months of historical hourly or sub-hourly data.
- Price area.
- Timestamp timezone and units.
- Rough flexible MW/MWh estimate.
- Known operating constraints.
- Tariff or price context if available.

## Producer / Asset-Owner / Developer Add-On

This add-on applies to wind farms, solar parks, hybrid parks, batteries, PtX,
energy parks, renewable developers, and European Energy-like actors.

Please provide the following data where available:

- Asset generation time series.
- Asset type: wind, solar, battery, PtX, or hybrid.
- Installed capacity MW.
- Available flexible capacity MW/MWh.
- Curtailment logs.
- Negative price handling rules.
- PPA or merchant exposure context.
- Forecast vs actual production if available.
- Grid connection or export constraints.
- Maintenance or outage periods.
- Operational notes.

This tests whether the public signal could have supported human review of
production planning, curtailment, PtX or battery operation, negative-price
exposure, or market decision timing.

## Flexible Consumption / Industrial Load Add-On

This add-on applies to industrial consumers, data centers, cold storage,
electrolyzers, PtX consumption, heat pumps, electric boilers, district heating
plants, and large buildings or campuses.

Please provide the following data where available:

- Load or consumption time series.
- Flexible load capacity MW.
- Flexible energy volume MWh.
- Minimum and maximum runtime.
- Ramp limits.
- Lead time.
- Comfort or process constraints.
- Storage capacity if relevant.
- Heat or process demand if relevant.
- Historical flexibility activations if available.
- Operating cost assumptions if available.

This tests whether the customer could realistically increase, reduce, or shift
consumption during public surplus-risk or low/negative-price windows.

## Grid / DSO Add-On

This add-on applies to Radius, Cerius, N1, DSOs, grid areas, transformer areas,
local congestion teams, and planning teams.

Please provide the following data where available:

- Aggregated load or generation per area.
- Anonymized grid area or transformer area id.
- Local generation/load balance.
- Transformer or grid-area capacity if shareable.
- Known congestion or bottleneck events.
- Flexible customer categories in the area.
- Historical operational notes.
- Planned outages or constraints if relevant.
- Local renewable generation context.

This tests whether the public signal could have supported human review of
planning, risk warning, flexibility needs, local grid stress, or area-level
operational awareness.

## Later-Stage Customer Types

Aggregators, balance responsible parties, traders, and portfolio operators may
be relevant in later stages. They are not the first pilot intake focus for this
template.

## Data Format Requirements

Preferred file formats:

- CSV.
- Excel.
- Parquet.

The v0 local intake validator accepts CSV only:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_intake_validate.py
```

Customer-type examples:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_CUSTOMER_TYPE=producer python scripts/customer_pilot_intake_validate.py
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_CUSTOMER_TYPE=flexible_consumption python scripts/customer_pilot_intake_validate.py
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_CUSTOMER_TYPE=grid_dso python scripts/customer_pilot_intake_validate.py
```

The validator checks structure before any pilot/backtest analysis is attempted.
It is validation only, not customer-specific savings, revenue, or profit
calculation. It writes no files, writes no database records, calls no external
APIs, performs no automatic control, and sends no dispatch, activation, or live
control signals.

After the CSV validates, run the local read-only signal match preview:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_signal_match.py
```

The preview compares customer DK1/DK2 rows with the canonical public
surplus-risk snapshot and reports which public risk windows overlap with the
customer data and availability fields. It is signal matching only. It does not
calculate customer-specific savings, profit, revenue, or financial advice. It
writes no files, writes no database records, calls no external APIs, performs
no automatic control, and sends no dispatch, activation, or live control
signals. Customer data and customer pilot CSV files must not be committed to
git.

After validation and signal matching, run the local read-only indicative gross
opportunity signal preview:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_opportunity_estimate.py
```

The preview uses the bounded formula:

```text
matched_flexible_energy_mwh x public_opportunity_signal_eur_per_mwh
```

It uses public price signal only. It is not customer savings, not profit, not
revenue, and not financial advice. Customer-specific value requires tariff,
constraints, operating costs, and human validation. It writes no files, writes
no database records, calls no external APIs, remains read-only decision
support, requires human review, performs no automatic control, and sends no
dispatch, activation, or live control signals. Customer data and customer
pilot CSV files must not be committed to git.

To run validation, signal matching, indicative gross opportunity signal
estimation, and human-review preparation in one local CLI step:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_workflow_preview.py
```

The workflow preview accepts CSV only for v0, writes no files, writes no
database records, calls no external APIs, and prints a consolidated summary.
It uses public price signal only. It is not customer savings, not profit, not
revenue, and not financial advice. Customer-specific value requires tariff,
constraints, operating costs, and human validation.

To export the same workflow preview as a local Markdown report:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_report_export.py
```

To write the Markdown report explicitly:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_REPORT_WRITE=true CUSTOMER_PILOT_REPORT_OUTPUT_PATH=artifacts/customer-pilots/customer-pilot-preview.md python scripts/customer_pilot_report_export.py
```

The report exporter accepts CSV only for v0, prints Markdown to stdout by
default, and writes only the configured Markdown file when
`CUSTOMER_PILOT_REPORT_WRITE=true`. It is report export only, not financial
advice, not a customer value claim, and not customer-specific savings, profit,
or revenue calculation. Customer-specific assessment requires tariff,
constraints, operating costs, and human validation. Customer data and generated
customer reports should not be committed to git unless explicitly anonymized
and approved.

To export the same workflow preview as a local PDF report:

Install backend dependencies first:

```bash
cd backend && python -m pip install -e '.[dev]' && cd ..
```

Then run the exporter from the repository root with the same Python
environment:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_PDF_WRITE=true CUSTOMER_PILOT_PDF_OUTPUT_PATH=/tmp/customer-pilot-preview.pdf python scripts/customer_pilot_pdf_export.py
```

The PDF exporter accepts CSV only through the existing workflow preview,
prints a safe no-write summary unless PDF writing is explicitly enabled, and
writes only the configured PDF file when
`CUSTOMER_PILOT_PDF_WRITE=true`. It writes no other files, writes no database
records, calls no external APIs, and remains PDF export only. The generated
PDF is a professional human-review pilot preview for customer discussion, not
a customer value claim. It is not financial advice and not customer-specific
savings. Customer-specific assessment requires tariff, constraints, operating
costs, and human validation. Customer data and generated customer PDFs must
not be committed to git unless anonymized and explicitly approved.
If `reportlab` is missing at runtime, install the backend dependencies from
`backend/pyproject.toml` before rerunning.

To create a complete local read-only pilot artifact pack:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_artifact_pack.py
```

To write the artifact pack explicitly:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_ARTIFACT_WRITE=true CUSTOMER_PILOT_ARTIFACT_RUN_ID=pilot-demo-001 python scripts/customer_pilot_artifact_pack.py
```

The artifact pack accepts CSV only for v0, prints a dry-run summary by
default, and writes files only when `CUSTOMER_PILOT_ARTIFACT_WRITE=true`. In
write mode it creates one sanitized run folder under
`artifacts/customer-pilots` by default with the workflow summary, Markdown
preview, PDF preview, and README. Generated artifacts are ignored by git. Raw
customer data must never be committed. The pack is public price signal only,
an indicative gross opportunity signal only, not financial advice, and not
customer-specific savings. Customer-specific assessment requires tariff,
constraints, operating costs, and human validation.

Local artifact handling:

- Use `/tmp` for smoke-test customer pilot inputs and throwaway generated
  reports.
- Use local untracked `artifacts/customer-pilots/` for temporary Markdown
  reports or PDFs that need to remain in the workspace briefly.
- Keep raw customer files outside git. If a temporary workspace-local path is
  unavoidable, use untracked `customer-data/` or `pilot-data/`.
- Never commit raw customer files, customer pilot input files, or generated
  customer reports unless explicitly anonymized and approved.
- The committed public request template
  `docs/templates/customer_pilot_data_request.csv` and committed public demo
  snapshot `frontend/src/data/public-surplus-risk-backtest-snapshot.json` are
  public artifacts and should remain trackable.

Generated reports are read-only pilot analysis for human review. They must not
make customer-specific savings claims, profit claims, revenue claims, financial
advice, or imply automatic control, dispatch, activation, live control signals,
or asset integration.

Preferred structure:

- One row per timestamp.
- ISO timestamp if possible.
- Explicit timezone.
- Explicit unit columns.
- No secrets or API keys.
- No personal data unless contractually required and approved.

Example time series columns:

- `site_id`
- `price_area`
- `timestamp`
- `timezone`
- `load_mwh`
- `generation_mwh`
- `flexible_capacity_mw`
- `flexible_energy_mwh`
- `availability_flag`
- `operational_note`

## Security And Data-Handling Notes

- Keep customer data and generated customer reports outside git unless
  explicitly anonymized and approved.
- Use `/tmp` for smoke tests and untracked `artifacts/customer-pilots/` for
  temporary generated reports.
- Do not commit customer data to git.
- Do not commit customer pilot CSV files to git.
- Do not commit generated customer reports to git unless explicitly
  anonymized and approved.
- Use least-privilege access.
- Minimize collected data to what the pilot needs.
- Keep customer data separate from public demo artifacts.
- Anonymize where possible.
- Delete or archive data according to the pilot agreement.
- Do not provide passwords, API keys, secrets, or control credentials.

## What N&O Predict Will Return

- Public-vs-customer signal comparison.
- Candidate opportunity windows.
- Indicative gross opportunity signal preview where validated inputs support
  it.
- False positive and missed opportunity review.
- Operational interpretation notes.
- Customer-specific potential estimate only if the data supports it.
- Final pilot report.
- Recommendation for next phase.

## Out Of Scope

- Guaranteed savings.
- Profit claims.
- Financial advice.
- Production deployment.
- Automatic control.
- Dispatch.
- Activation.
- Live control signals.
- Asset integration.
- Grid operation responsibility.
