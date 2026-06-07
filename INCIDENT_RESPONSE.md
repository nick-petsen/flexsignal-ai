# Incident Response

## Incident Types

FlexSignal AI incident handling should cover:

- Data errors
- Model drift
- Incorrect recommendations
- Security incidents
- Logging or monitoring failures
- Availability issues

## Data Errors

Examples:

- Missing data
- Delayed data
- Incorrect units
- Timestamp errors
- Source schema changes

Response:

- Identify affected datasets and time windows.
- Mark affected forecasts as degraded where possible.
- Correct ingestion or transformation logic.
- Reprocess data after validation.
- Record incident details and follow-up actions.

## Model Drift

Examples:

- Declining backtest performance.
- Confidence scores becoming poorly calibrated.
- Increased false positives or false negatives.

Response:

- Compare current performance against baseline metrics.
- Review recent data and market condition changes.
- Disable, label, or downgrade unreliable recommendations.
- Retrain or revise the model after documented review.

## Incorrect Recommendations

Examples:

- Recommendation conflicts with forecast evidence.
- Recommendation omits important uncertainty.
- Recommendation overstates economic potential.

Response:

- Preserve forecast, input, explanation, and audit records.
- Review model output and explanation generation.
- Correct recommendation logic or prompts.
- Notify affected users where appropriate.

## Security Incidents

Examples:

- Unauthorized access.
- Credential exposure.
- Suspicious API activity.
- Unexpected changes to data or model artifacts.

Response:

- Contain the incident.
- Revoke or rotate affected credentials.
- Review Entra ID, Key Vault, API, and database logs.
- Preserve evidence.
- Notify responsible stakeholders according to policy.

## Roles

- Incident owner: Coordinates response and communication.
- Engineering owner: Investigates application, data, and model behavior.
- Security owner: Leads security investigation and containment.
- Product owner: Assesses user impact and communication needs.

## Response Process

1. Detect and classify the incident.
2. Contain immediate risk.
3. Preserve logs and evidence.
4. Assess affected users, data, forecasts, and recommendations.
5. Correct the underlying issue.
6. Validate recovery.
7. Document root cause and follow-up actions.

