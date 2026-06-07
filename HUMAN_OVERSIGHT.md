# Human Oversight

## Human Review Requirement

All FlexSignal AI recommendations require human review. The platform provides read-only decision support and must not automatically activate consumption, dispatch assets, or send control signals.

## No Automatic Activation

`v0.1` must not include:

- Automatic control of electricity consumption.
- Live control signals to assets, plants, devices, or infrastructure.
- Dispatch or activation workflows.
- Closed-loop operational automation.

## Explanation Requirements

Recommendations should include:

- Forecasted surplus-risk level.
- Expected time window.
- Confidence score.
- Estimated economic potential.
- Main data or model drivers.
- Clear limitations where relevant.

## Audit Log Requirements

Audit logs should capture:

- Forecast generation timestamp.
- Model version.
- Input data references.
- Recommendation text.
- Explanation text.
- User review or acknowledgement events.
- Relevant system and data quality status.

## Operator Responsibility

Users and operators remain responsible for:

- Reviewing recommendations.
- Checking operational constraints outside the platform.
- Deciding whether to act.
- Ensuring any action complies with internal procedures and external obligations.

## Escalation Principles

- Escalate when forecasts conflict with operator expectations.
- Escalate when data quality is degraded or unknown.
- Escalate repeated incorrect recommendations.
- Escalate any suspected security incident.
- Disable or label unreliable recommendations when model or data quality is compromised.

