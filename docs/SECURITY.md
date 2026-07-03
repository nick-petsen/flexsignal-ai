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

## Read-Only Boundary

All MVP recommendations require human review before action. The platform may
forecast, explain, report, and export decision-support artifacts, but it must
not control electricity consumption, dispatch resources, activate assets,
connect to operational energy infrastructure for control, or become a critical
operational system.

The UI label "System Status: LIVE" must not be used until staging health,
authentication, monitoring, and data freshness checks exist and have been
reviewed.
