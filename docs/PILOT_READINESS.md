# Customer Pilot Readiness

## Purpose

N&O Predict / FlexSignal AI has a public DK1/DK2 backtest that shows the
deterministic signal can identify historical surplus-risk windows at the
public system and market level.

For pilot readiness, that public backtest is evidence that the signal works at
the public DK1/DK2 system and market level. It is not evidence of
customer-specific value by itself.

A customer pilot has a different purpose: it tests whether those public signal
windows are relevant for a specific customer when compared with that
customer's load, assets, constraints, price context, and operational reality.
The customer pilot is the evidence step for whether the signal creates
validated potential value for that specific customer.

The pilot remains read-only decision support. It prepares analysis and
recommendations for human review only.

The customer-facing intake template is available in
[PILOT_INTAKE_TEMPLATE.md](PILOT_INTAKE_TEMPLATE.md). A structured request
sheet is available at
[templates/customer_pilot_data_request.csv](templates/customer_pilot_data_request.csv).
Use these materials after the public proof-of-work report when requesting
customer data for a read-only pilot.

The manual operator flow is documented in
[PILOT_OPERATOR_RUNBOOK.md](PILOT_OPERATOR_RUNBOOK.md). Use
[PILOT_ACCEPTANCE_CHECKLIST.md](PILOT_ACCEPTANCE_CHECKLIST.md) for internal
review and customer-sharing sign-off.

Validate local CSV intake files before any pilot or backtest analysis:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_intake_validate.py
```

Optional customer-type examples:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_CUSTOMER_TYPE=producer python scripts/customer_pilot_intake_validate.py
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_CUSTOMER_TYPE=flexible_consumption python scripts/customer_pilot_intake_validate.py
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_CUSTOMER_TYPE=grid_dso python scripts/customer_pilot_intake_validate.py
```

The v0 validator accepts CSV only and checks required common columns, DK1/DK2
price areas, sampled timestamps, timezone presence, row minimums,
energy/flexibility columns, customer-type recommended fields, and secret-like
column names. It is local read-only validation only. It writes no files, writes
no database records, calls no external APIs, calculates no customer-specific
savings, revenue, or profit, and adds no control, dispatch, activation, live
control signals, or asset integration.

After validation, preview whether the customer rows overlap the canonical
public surplus-risk windows:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_signal_match.py
```

The v0 signal match preview accepts CSV only and compares DK1/DK2 customer
timestamps with the public surplus-risk snapshot. It reports matched public
risk windows, customer row counts, whether load/generation/flexibility data is
present, optional availability counts, optional operational note counts,
warnings, and the read-only safety boundary. It writes no files, writes no
database records, calls no external APIs, calculates no customer-specific
savings, profit, or revenue, and adds no control, dispatch, activation, live
control signals, or asset integration.

After validation and signal matching, preview a bounded indicative gross
opportunity signal:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_opportunity_estimate.py
```

The v0 opportunity estimate preview accepts CSV only and calculates:

```text
matched_flexible_energy_mwh x public_opportunity_signal_eur_per_mwh
```

This is public price signal only. It is not customer savings, not profit, not
revenue, and not financial advice. Customer-specific value requires tariff,
constraints, operating costs, and human validation. The preview writes no
files, writes no database records, calls no external APIs, remains read-only
decision support, requires human review, and adds no automatic control,
dispatch, activation, live control signals, or asset integration. Customer
data and customer pilot CSV files must not be committed to git.

To run the local read-only chain end-to-end, use the workflow preview:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_workflow_preview.py
```

The workflow preview runs validation, signal matching, indicative gross
opportunity signal estimation, and human-review preparation in one CLI step.
It accepts CSV only for v0, writes no files, writes no database records, calls
no external APIs, and prints a consolidated summary with workflow status,
component statuses, matched rows, matched flexible MWh, candidate windows,
warnings, next human review steps, and the read-only safety boundary. It uses
public price signal only. It is not customer savings, not profit, not revenue,
and not financial advice. Customer-specific value requires tariff,
constraints, operating costs, and human validation.

To export a local Markdown report for the same customer pilot workflow
preview:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_report_export.py
```

To write the report explicitly:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_REPORT_WRITE=true CUSTOMER_PILOT_REPORT_OUTPUT_PATH=artifacts/customer-pilots/customer-pilot-preview.md python scripts/customer_pilot_report_export.py
```

The v0 report exporter accepts CSV only, reuses the workflow preview, prints
Markdown to stdout when no output path is set, and writes only the configured
Markdown file when report writing is explicitly enabled. It writes no other
files, writes no database records, calls no external APIs, and remains
read-only report export for human review. Human-facing Markdown reports round
matched flexible energy, public opportunity signal, and indicative gross
opportunity signal values to 2 decimals for readability. This is formatting
only; the underlying workflow numeric values are unchanged. The output remains
an indicative gross opportunity signal, not financial advice, not a
customer-specific monetary benefit claim, and not a commercial outcome
calculation. Customer-specific assessment requires tariff, constraints,
operating costs, and human validation. Customer data and generated customer
reports should not be committed to git unless explicitly anonymized and
approved.

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

The v0 PDF exporter accepts CSV only through the existing workflow preview,
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

The artifact pack accepts CSV only for v0 and reuses the workflow preview,
Markdown report export, and PDF report export. In default dry-run mode it
prints a summary and writes no files. In write mode it creates exactly one
sanitized run folder under `CUSTOMER_PILOT_ARTIFACT_DIR` (default
`artifacts/customer-pilots`) with `workflow-summary.json`,
`customer-pilot-preview.md`, `customer-pilot-preview.pdf`, `README.txt`, and
`MANIFEST.json`. `MANIFEST.json` is for audit and reproducibility: it records
the input file hash, input file size, workflow statuses, and generated file
hashes without storing the raw input path or raw customer data. Generated
artifacts are ignored by git. Raw customer data must never be committed. The
artifact pack uses public price signal only and presents an indicative gross
opportunity signal only. It is not financial advice and not customer-specific
savings. Customer-specific assessment requires tariff, constraints, operating
costs, and human validation. Human review is required before sharing any
generated PDF externally.

## Artifact Safety

Customer pilot inputs and generated customer reports are local artifacts. They
must stay outside git unless the artifact has been explicitly anonymized and
approved for commit.

Recommended local paths:

- Use `/tmp` for smoke-test customer pilot inputs and throwaway report output.
- Use local untracked `artifacts/customer-pilots/` for temporary generated
  Markdown reports or PDFs that need to remain in the workspace briefly.
- Use local untracked `customer-data/` or `pilot-data/` only for temporary
  customer input files that cannot live in `/tmp`.

Never commit raw customer files, customer pilot input files, or generated
customer reports. Local gitignore patterns cover customer pilot artifact
folders, `*.customer.csv`, `*.customer.xlsx`, `*.customer.parquet`,
`*customer-pilot-preview*.md`, and `*customer-pilot-report*.md`. Generated PDF
ignores also cover `*customer-pilot-preview*.pdf` and
`*customer-pilot-report*.pdf`. These ignores do not apply to the committed
public request template at
`docs/templates/customer_pilot_data_request.csv` or the committed public demo
snapshot at `frontend/src/data/public-surplus-risk-backtest-snapshot.json`.

Artifact handling does not change the pilot boundary. Customer pilot reports
remain read-only pilot analysis for human review. They must not include
customer-specific savings claims, profit claims, revenue claims, financial
advice, automatic control, dispatch, activation, live control signals, or asset
integration.

`MANIFEST.json` supports audit and reproducibility for a local artifact pack.
It records hashes and sizes for the input file and generated artifacts, not raw
customer rows or raw customer file contents.

The pilot flow is:

1. Validate customer intake CSV.
2. Match customer data to public risk windows.
3. Estimate indicative gross opportunity signal.
4. Export a local Markdown workflow preview report if needed.
5. Export a local PDF workflow preview report if explicitly needed.
6. Create a local artifact pack if explicitly needed.
7. Human review.
8. Only later produce customer-specific assessment if data and contract
   support it.

## Pilot Scope

- Read-only analysis.
- No automatic control.
- No dispatch.
- No activation.
- No live control signals.
- No asset integration.
- Human review required for all recommendations.

## Required Customer Data

| Data category | Examples | Preferred format | Required/optional | Why it is needed |
| --- | --- | --- | --- | --- |
| Historical electricity load/consumption time series | Site import/export, process load, metered consumption | CSV, Parquet, or Excel with timestamp, timezone, value, unit, and meter/site id | Required | Compares public risk windows with actual customer demand and timing. |
| Asset/flexible load capacity in MW/MWh | Flexible process load, thermal storage, battery capacity, interruptible load range | Structured table with asset name, max MW, usable MWh, duration, and site id | Required | Estimates the flexible energy volume that could be considered during candidate windows. |
| Operating constraints | Minimum run times, ramp limits, product quality limits, comfort limits, restart limits | Structured table or documented operating rules | Required | Filters public signal windows against practical operating limits. |
| Operating schedule or availability windows | Production shifts, opening hours, batch windows, planned idle periods | Calendar export, CSV, or table with start/end timestamps and timezone | Required | Identifies when flexibility could realistically be reviewed. |
| Tariff/price agreement context | Spot exposure, fixed-price components, grid tariffs, taxes, fees, imbalance terms | Contract summary or structured tariff table | Required | Determines which price or opportunity signal is economically relevant. |
| Historical production/consumption decisions if available | Previous curtailment, batch timing, load-shift decisions | CSV, operations log export, or annotated timeline | Required if available | Helps validate whether candidate windows align with prior operational choices. |
| Site/location/price area mapping | Site address, metering point, DK1/DK2 price area, grid connection context | Site list or mapping table | Required | Ensures the public DK1/DK2 signal is matched to the right customer area. |
| Contact person for operational interpretation | Operations lead, energy manager, production planner | Name, role, email, phone, review availability | Required | Provides human validation of assumptions, constraints, and interpretation. |
| Asset telemetry | State of charge, temperature, process state, availability flags | Time series export with timestamps and units | Optional | Improves validation of actual asset availability during candidate windows. |
| Planned maintenance | Maintenance windows, outages, known downtime | Calendar export or table with start/end timestamps | Optional | Excludes windows where flexibility was unavailable for non-market reasons. |
| Internal forecast | Customer load, production, or availability forecasts | CSV, Parquet, API export, or forecast report | Optional | Compares public signal timing with the customer's own planning view. |
| Curtailment/constraint logs | Grid constraints, local constraints, process interruptions | Log export or annotated timeline | Optional | Explains why apparently attractive windows may not have been actionable. |
| Operational notes | Shift notes, planning notes, exceptions, known anomalies | Text export, spreadsheet, or reviewed notes | Optional | Adds context for interpreting false positives and missed opportunities. |
| Commercial settlement assumptions | Settlement period, currency, fees, internal allocation rules | Contract summary or structured assumptions table | Optional | Supports a more precise customer-specific potential estimate when validated. |

## Minimum Pilot Dataset

A practical first pilot can start with:

- 3-12 months of historical hourly or sub-hourly load data.
- Confirmed DK1/DK2 price area.
- Rough flexible MWh estimate.
- Known operational constraints.
- Tariff or price context if available.

This minimum dataset supports an initial read-only comparison. It does not
support customer-specific conclusions until the data has been checked with the
customer reviewer.

## Pilot Success Criteria

The pilot should be evaluated with measurable criteria:

- Number of public risk windows matched to customer availability.
- Number of actionable candidate windows after constraints are applied.
- False positive review rate.
- Missed opportunity review.
- Estimated gross market opportunity per flexible MWh.
- Customer-specific potential only after customer data is validated.

## Economic Potential Method

The pilot estimates economic potential in a controlled, auditable sequence:

1. The public DK1/DK2 signal identifies historical surplus-risk or
   price-opportunity windows.
2. Customer data estimates usable flexible MWh during those windows.
3. Indicative gross opportunity signal equals:

   ```text
   matched_flexible_energy_mwh x public_opportunity_signal_eur_per_mwh
   ```

4. Customer-specific value requires validated tariff terms, operating
   constraints, operating costs, and customer review.

This method is public price signal only and is a read-only decision-support
preview. It is not customer savings, not profit, not revenue, and not
financial advice. It must be reviewed with the customer before any later
customer-specific assessment.

The local workflow command for this sequence is:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_workflow_preview.py
```

## Deliverables

- Pilot input checklist.
- Public-vs-customer signal comparison.
- Candidate opportunity windows.
- Customer-specific potential estimate if the validated data supports it.
- Final pilot report.
- Recommendation for next phase.

## Security And Data Handling

- Use least-privilege access for all customer data.
- Keep customer data and generated customer reports outside git unless
  explicitly anonymized and approved.
- Use `/tmp` for smoke tests and untracked `artifacts/customer-pilots/` for
  temporary generated reports.
- Do not commit secrets to the repository.
- Do not commit customer data to git.
- Do not commit customer pilot CSV files to git.
- Do not commit generated customer reports to git unless explicitly
  anonymized and approved.
- Minimize collected data to what the pilot needs.
- Delete or anonymize customer data after the pilot unless the contract says
  otherwise.
- Keep customer data separate from public demo artifacts.

## Human Oversight

- All outputs are decision support.
- A customer reviewer must approve interpretation of results.
- No automatic operational action is performed or implied.

## Out Of Scope

- Production deployment.
- Autonomous control.
- Dispatch or activation.
- Live asset integration.
- Guaranteed savings.
- Financial advice.
- Grid operation responsibility.
