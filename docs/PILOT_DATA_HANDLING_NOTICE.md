# Pilot Data Handling Notice

## Plain-Language Notice

Customer pilot data is used only to run a local read-only pilot analysis and
prepare material for human review.

The pilot uses public price signal only. It is not a customer value claim.
Customer-specific assessment requires tariff, constraints, operating costs,
and human validation.

This notice is operational guidance for v0. It is not legal advice.

## Data Minimization

Request only the data needed for the pilot:

- DK1/DK2 price area.
- Timestamp and timezone.
- Load and/or production time series.
- Flexible energy or capacity, if available.
- Availability flag and operational note, if available.
- Operational contact for interpretation.

Do not request passwords, API keys, secrets, control credentials, personal
access tokens, or unnecessary personal data.

## Local And Controlled Handling

- Keep customer data local or otherwise controlled under the pilot agreement.
- Do not commit customer files to git.
- Do not commit raw CSV files.
- Do not share raw CSV externally.
- Keep customer files separate from committed public demo artifacts.
- Use `/tmp` for short-lived local checks where practical.
- Use ignored local folders such as `artifacts/customer-pilots/`,
  `customer-data/`, or `pilot-data/` only when files need to remain in the
  workspace briefly.

Generated artifacts are ignored by git. This includes local customer pilot
artifact packs, Markdown previews, and PDF previews covered by the repository
ignore rules.

## Sharing Rules

- Raw CSV must not be shared externally.
- Markdown and JSON artifacts are internal unless explicitly approved.
- PDF can be shared only after human review.
- Human review must confirm the output is read-only, uses public price signal
  only, and avoids unsupported customer claims.

## Retention

Delete or archive rules are TBD/manual for v0.

Until a pilot-specific retention rule is agreed, keep files only as long as
needed for the pilot review, then delete or archive manually according to the
pilot agreement and reviewer instruction.

## Security And Compliance Boundary

FlexSignal AI v0.1 pilot handling remains:

- Read-only.
- No control.
- No dispatch.
- No activation.
- No live control signals.
- No asset integration.

What we do not claim:

- No verified customer savings.
- No profit or revenue claim.
- No guaranteed value.
- No financial advice.

Human review is required before any PDF or interpretation is shared.
