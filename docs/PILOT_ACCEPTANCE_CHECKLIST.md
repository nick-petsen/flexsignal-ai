# Customer Pilot Acceptance Checklist

Use this checklist before treating a local customer pilot artifact pack as ready
for internal review or customer sharing.

The pilot output is read-only decision support. It uses public price signal
only and reports an indicative gross opportunity signal. This is not a customer
value claim. Customer-specific assessment requires tariff, constraints,
operating costs, and human validation.

## Intake Readiness

- [ ] Customer CSV path is known.
- [ ] CSV is stored in `/tmp` or ignored `artifacts/customer-pilots/`,
      `customer-data/`, or `pilot-data/`.
- [ ] Price area is confirmed as `DK1` or `DK2`.
- [ ] Timestamp timezone is documented.
- [ ] Load, production, and flexible energy fields are identified where
      available.
- [ ] Operational contact is named.
- [ ] Raw customer CSV is not committed or staged.

## Data Validation Readiness

- [ ] `scripts/customer_pilot_intake_validate.py` completed.
- [ ] Validation status is acceptable for review.
- [ ] Required columns are present or missing fields are documented.
- [ ] Timestamp parsing and timezone handling have been reviewed.
- [ ] Warnings are recorded for reviewer follow-up.
- [ ] Secret-like or unrelated sensitive columns are removed or documented.

## Signal Match Readiness

- [ ] `scripts/customer_pilot_workflow_preview.py` completed.
- [ ] Matched windows are recorded.
- [ ] Matched customer rows are recorded.
- [ ] Selected price area matches the customer site.
- [ ] No-match or low-match outcomes are documented for human review.
- [ ] Public snapshot period and customer CSV period are understood.

## Opportunity Signal Readiness

- [ ] Matched flexible energy is present or absence is documented.
- [ ] Indicative gross opportunity signal is present or unavailable status is
      documented.
- [ ] Output is described as public price signal only.
- [ ] Reviewer understands that tariff, constraints, operating costs, and human
      validation are required for customer-specific assessment.

## Report Quality Readiness

- [ ] Markdown report is generated if needed.
- [ ] PDF report is generated if needed.
- [ ] Artifact pack contains `workflow-summary.json`,
      `customer-pilot-preview.md`, `customer-pilot-preview.pdf`, `README.txt`,
      and `MANIFEST.json` when write mode is used.
- [ ] `MANIFEST.json` records input file hash and generated file hashes, not
      raw customer rows or raw customer file contents.
- [ ] PDF opens locally.
- [ ] Report warnings and next human review steps are visible.
- [ ] Safety boundary text is present.
- [ ] Markdown and JSON remain internal unless explicitly approved.

## Safety/Compliance Readiness

- [ ] Output states read-only decision support.
- [ ] Output states human review required.
- [ ] Output states public price signal only.
- [ ] Output states this is not a customer value claim.
- [ ] Output does not add automatic control behavior.
- [ ] Output does not add dispatch behavior.
- [ ] Output does not add activation behavior.
- [ ] Output does not add live control signal behavior.
- [ ] Output does not add asset integration behavior.
- [ ] Customer data is not staged in git.
- [ ] Generated customer reports are not staged in git unless anonymized and
      explicitly approved.

## Customer Review Readiness

- [ ] Internal reviewer has reviewed validation status.
- [ ] Internal reviewer has reviewed matched windows and customer rows.
- [ ] Internal reviewer has reviewed matched flexible energy.
- [ ] Internal reviewer has reviewed indicative gross opportunity signal.
- [ ] Internal reviewer has reviewed warnings.
- [ ] Internal reviewer has approved next human review step.
- [ ] Customer-facing PDF is approved before external sharing.

## Do Not Claim

Confirm the pilot materials do not claim:

- Customer savings.
- Profit.
- Revenue.
- Earnings.
- Guaranteed value.
- Financial advice.
- Automatic control.
- Dispatch.
- Activation.
- Live control signals.
- Asset integration.

## Explicit Go/No-Go Checklist

- [ ] Go: input readiness complete.
- [ ] Go: validation acceptable for review.
- [ ] Go: signal match output reviewed.
- [ ] Go: indicative gross opportunity signal wording is correct.
- [ ] Go: reports pass safety/compliance review.
- [ ] Go: customer data is outside git.
- [ ] Go: reviewer approves internal review.
- [ ] Go: reviewer separately approves customer sharing, if applicable.
- [ ] No-go: unresolved validation errors.
- [ ] No-go: unresolved customer data handling issue.
- [ ] No-go: missing human reviewer approval.
- [ ] No-go: any forbidden commercial or operational claim appears.

## Required Sign-Off Fields

Operator:

Reviewer:

Date:

Customer/pilot identifier:

Approved for internal review yes/no:

Approved for customer sharing yes/no:
