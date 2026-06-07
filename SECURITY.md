# Security

## Secrets Management

- Store secrets in Azure Key Vault.
- Do not commit secrets, credentials, tokens, connection strings, certificates, or private keys.
- Use managed identities where practical.
- Rotate credentials according to operational policy.

## Authentication

- Use Microsoft Entra ID for user authentication.
- Require authenticated access to application views and APIs.
- Apply role-based access controls once user roles are defined.

## Logging and Monitoring

- Send logs, metrics, traces, and relevant security telemetry to Application Insights and Log Analytics.
- Log forecast, recommendation, explanation, and user review events.
- Avoid logging sensitive secrets or unnecessary personal data.

## Principle of Least Privilege

- Grant only the minimum permissions needed by services, jobs, users, and managed identities.
- Keep ingestion, API, database, and observability permissions separated.
- Review privileged access regularly.

## No Control Signals

`v0.1` must not send control signals to assets, plants, devices, or energy infrastructure. The platform is read-only decision support and must not include control, dispatch, activation, or automation interfaces.

## Auditability

- Keep traceable records for forecasts, inputs, recommendation text, model versions, and human review actions.
- Preserve enough context to investigate incorrect recommendations, data errors, and model drift.

## Data Protection

- Protect data in transit using TLS.
- Protect data at rest using managed encryption.
- Minimize personal data collection.
- Define retention policies before production use.

