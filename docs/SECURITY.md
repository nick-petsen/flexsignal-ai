# Security

FlexSignal AI `v0.1` is local/manual read-only decision support. It is not a
production live system, not a critical operational system, and not ready for
external test-user access until staging security readiness is complete.

## Staging Configuration Required Before Test Users

External test users require a reviewed staging environment with these settings:

- `DATABASE_URL`: staging database connection string stored only in secret or
  environment configuration. Do not commit it, print it in logs, expose it in
  frontend code, or paste it into docs.
- `NEXT_PUBLIC_API_BASE_URL`: staging frontend setting that points only to the
  staging API base URL.
- Allowed CORS origins: the approved staging frontend origin or origins only.
  The current backend CORS setup is local-development-oriented and must not be
  treated as a staging access-control strategy.
- Future Entra ID auth settings: tenant, client/application identifiers,
  issuer/JWKS validation, API audience/scopes, redirect/origin settings, and
  allowed users/groups/roles must be defined before external auth-backed access.
  Auth is not implemented yet.

## Pre-Test-User Security Checks

Before any external test-user session, confirm:

- Backend tests pass.
- Frontend build passes.
- No secrets, tokens, raw `DATABASE_URL` values, credentials, or private keys
  are committed.
- Staging database migration status is known.
- Dashboard smoke works for `DK1` and `DK2`.
- Report, audit, and export flows are smoke-tested.
- The app still has no automatic control, dispatch, activation, live control
  signals, or asset integration.

## Staging Readiness Endpoint

Backend `GET /api/system/readiness` is a staging smoke/readiness endpoint for
MVP preparation only. It is not production monitoring, uptime monitoring, data
freshness monitoring, auth verification, or operational health automation.

The endpoint returns JSON-only safe status fields. It may report whether
`DATABASE_URL` is configured as a boolean, but it must not expose raw
`DATABASE_URL` values, environment variable values, secrets, hostnames,
passwords, tokens, connection strings, or API keys. Missing `DATABASE_URL`
returns HTTP 200 with degraded status so the backend can still start and be
smoke-checked safely.

The endpoint does not connect to the database, run migrations, write data,
call external APIs, add auth, add Azure resources, add weather/maps, add fake
data, or introduce automatic control, dispatch, activation, live control
signals, or asset integration.

## Customer Pilot Data Handling

The customer pilot readiness pack is documented in
[PILOT_READINESS.md](PILOT_READINESS.md). Customer pilot data must be handled
separately from public demo artifacts and with least-privilege access.

Security requirements for customer pilot data:

- Do not commit customer data to git.
- Do not commit customer secrets, credentials, tokens, or contract terms to the
  repository.
- Collect only the data needed for the agreed pilot analysis.
- Store customer data outside the public demo artifact path.
- Limit access to people who need the data for the pilot.
- Delete or anonymize customer data after the pilot unless the contract says
  otherwise.
- Keep all pilot outputs as read-only decision support for human review.

## Read-Only Boundary

All MVP recommendations require human review before action. The platform may
forecast, explain, report, and export decision-support artifacts, but it must
not control electricity consumption, dispatch resources, activate assets,
connect to operational energy infrastructure for control, or become a critical
operational system.

The UI label "System Status: LIVE" must not be used until staging health,
authentication, monitoring, and data freshness checks exist and have been
reviewed.

Until those checks exist and are reviewed, System Status must remain Manual
refresh mode.
