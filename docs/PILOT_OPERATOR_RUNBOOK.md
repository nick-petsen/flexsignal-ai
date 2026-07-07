# Customer Pilot Operator Runbook

## Purpose

This runbook documents the manual operator process for running a real customer
pilot CSV through the local read-only pilot workflow and artifact pack.

The workflow produces a human-review artifact pack with validation output,
signal-match output, an indicative gross opportunity signal, Markdown report,
PDF report, local run notes, and `MANIFEST.json` audit metadata. It is
read-only decision support. Human review is required before any interpretation
is shared.

This is not a customer value claim. The workflow uses public price signal only.
Customer-specific assessment requires tariff, constraints, operating costs, and
human validation.

## Scope

This runbook covers local operator steps only:

- Validate a customer CSV.
- Preview the read-only pilot workflow.
- Export a Markdown report.
- Export a PDF report.
- Create a local artifact pack.
- Review outputs before any customer sharing.

The workflow does not perform automatic control, dispatch, activation, live
control signals, asset integration, or critical operational workflows.

## Required Inputs Before Running

Confirm these inputs before running any command:

- Customer CSV path.
- Price area: `DK1` or `DK2`.
- Timestamp timezone, including whether timestamps are timezone-aware or local.
- Load field names, if present.
- Production field names, if present.
- Flexible energy field names, if present.
- Operational contact for interpreting constraints and anomalies.

If any required input is unclear, stop and resolve it with the customer contact
or internal reviewer before creating a shareable PDF.

Use the customer outreach pack before requesting or handling pilot files:

- [Pilot customer data request](PILOT_CUSTOMER_DATA_REQUEST.md)
- [Pilot customer email template](PILOT_CUSTOMER_EMAIL_TEMPLATE.md)
- [Pilot data handling notice](PILOT_DATA_HANDLING_NOTICE.md)

## Safe Local File Handling

Use local ignored paths for all customer material:

- Prefer `/tmp` for short-lived customer CSV inputs and generated reports.
- Use ignored `artifacts/customer-pilots/` for local artifact packs that need to
  remain in the workspace briefly.
- Never commit raw customer CSV files.
- Never commit generated customer reports unless they are anonymized and
  explicitly approved.
- Keep customer files separate from committed public demo artifacts.

Before committing documentation changes, run `git status --short` and confirm
that raw customer files and generated customer reports are not staged.

## Step-By-Step Commands

Run commands from the repository root.

1. Validate CSV:

   ```bash
   CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_intake_validate.py
   ```

2. Run workflow preview:

   ```bash
   CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv python scripts/customer_pilot_workflow_preview.py
   ```

3. Export Markdown report:

   ```bash
   CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_REPORT_WRITE=true CUSTOMER_PILOT_REPORT_OUTPUT_PATH=/tmp/customer-pilot-preview.md python scripts/customer_pilot_report_export.py
   ```

4. Export PDF report:

   ```bash
   CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_PDF_WRITE=true CUSTOMER_PILOT_PDF_OUTPUT_PATH=/tmp/customer-pilot-preview.pdf python scripts/customer_pilot_pdf_export.py
   ```

5. Create artifact pack:

   ```bash
   CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_ARTIFACT_WRITE=true CUSTOMER_PILOT_ARTIFACT_RUN_ID=<safe-run-id> python scripts/customer_pilot_artifact_pack.py
   ```

## Recommended One-Command Artifact Pack Flow

For a normal local pilot run, prefer the artifact pack command after input
readiness has been confirmed:

```bash
CUSTOMER_PILOT_INPUT_PATH=path/to/customer.csv CUSTOMER_PILOT_ARTIFACT_WRITE=true CUSTOMER_PILOT_ARTIFACT_RUN_ID=<safe-run-id> python scripts/customer_pilot_artifact_pack.py
```

Use a safe run id that does not include customer confidential details. The
default artifact directory is ignored `artifacts/customer-pilots/`. The written
pack contains `workflow-summary.json`, `customer-pilot-preview.md`,
`customer-pilot-preview.pdf`, `README.txt`, and `MANIFEST.json`.
`MANIFEST.json` supports audit and reproducibility by recording the input file
hash, input file size, workflow statuses, and generated file hashes. It must
not contain the raw input path, raw customer rows, or raw customer file
contents.

## Manual Review Checklist

Before sharing any output, review:

- Validation status.
- Matched windows.
- Matched customer rows.
- Matched flexible energy.
- Indicative gross opportunity signal.
- Warnings.
- Human review next steps.
- Safety boundary text.
- `MANIFEST.json` hash metadata.
- Customer contact or reviewer notes.

The review must confirm that the output remains public price signal only,
read-only decision support, and requires human validation.

## Sharing Rules

- PDF may be shared externally only after human review.
- Markdown and JSON are internal unless explicitly approved.
- Customer data must stay out of git.
- Raw CSV must not be attached to commits, issues, or public artifacts.
- Artifact pack folders must remain local unless explicitly anonymized and
  approved for transfer.

## What Not To Claim

Do not claim:

- Customer savings.
- Profit.
- Revenue.
- Guaranteed value.
- Financial advice.
- Automatic control.
- Dispatch.
- Activation.
- Live control signals.
- Asset integration.

Use "indicative gross opportunity signal" for the bounded public-price-signal
output. State that this is not a customer value claim. State that
customer-specific assessment requires tariff, constraints, operating costs, and
human validation.

## Troubleshooting

### Invalid CSV

- Confirm `CUSTOMER_PILOT_INPUT_PATH` points to a CSV file.
- Confirm required columns are present.
- Confirm `DK1` or `DK2` price area values are valid.
- Confirm timestamps are parseable and timezone handling is documented.
- Rerun validation before continuing.

### No Matches

- Confirm the customer CSV covers the same period as the public snapshot.
- Confirm the selected price area matches the customer site.
- Review timestamp timezone conversion.
- Treat no-match output as a review finding, not as a customer value claim.

### Missing Reportlab Or Dependency Environment

Install backend dependencies before PDF export:

```bash
cd backend && python -m pip install -e '.[dev]' && cd ..
```

Then rerun the PDF or artifact pack command from the repository root using the
same Python environment.

### Output Path Ignored By Git

This is expected for `artifacts/customer-pilots/` and common generated customer
report patterns. Keep generated customer reports out of git unless anonymized
and explicitly approved.

### PDF Not Generated

- Confirm `CUSTOMER_PILOT_PDF_WRITE=true` is set.
- Confirm `CUSTOMER_PILOT_PDF_OUTPUT_PATH` is set.
- Confirm the output directory exists or can be created by the script.
- Confirm backend dependencies are installed.
- Check command output for validation or workflow warnings.

## Completion Criteria

The pilot operator run is complete only when:

- Artifact pack generated.
- PDF opened manually.
- Safety boundary present.
- No forbidden commercial claims.
- Human reviewer approved next step.
- Customer data and generated customer reports are not staged in git.
