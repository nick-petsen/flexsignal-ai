# Incident Response

FlexSignal AI `v0.1` is local/manual decision support only. Incidents in this
phase are handled by disabling or stopping affected access, preserving evidence,
and documenting the limitation before any external test-user session continues.

## Immediate Actions

For any safety, data, or availability incident:

- Stop external test-user access or the affected smoke session.
- Preserve relevant request IDs, timestamps, screenshots, exported reports,
  audit-event IDs, logs, and configuration names without copying secrets.
- Confirm that no automatic control, dispatch, activation, live control signal,
  or asset integration occurred.
- Mark affected recommendations, reports, exports, or dashboard views as not
  approved for action until reviewed.
- Record whether `DK1`, `DK2`, report, audit, or export flows were affected.

## Incorrect Recommendation

If a recommendation appears wrong, unsafe, unsupported, or inconsistent:

- Treat it as advisory text only and do not act on it.
- Compare the recommendation with the source dashboard inputs, report preview,
  audit metadata, and any available DK1/DK2 source records.
- Document the expected output, observed output, timestamp, price area, and
  endpoint or UI flow.
- Require human review before the recommendation is reused or shown to test
  users again.

## Stale Data

If dashboard data, report output, or export content appears stale:

- Do not label the system live.
- Mark the affected view or artifact as stale or not approved for action.
- Check data freshness indicators and the known staging database migration and
  ingestion status.
- Smoke-test `DK1` and `DK2` dashboard paths again after the source issue is
  understood.

## Failed Data Ingestion

If ingestion fails or the staging database lacks expected source data:

- Do not create fake replacement data.
- Do not infer missing operational facts with an LLM.
- Record the dataset, price area, time window, error, and whether any partial
  records were written.
- Keep affected recommendations, reports, audits, and exports under human
  review until source coverage is known.

## Unavailable API

If the API is unavailable or returns unexpected errors:

- Stop the affected external test-user flow.
- Check staging `NEXT_PUBLIC_API_BASE_URL`, allowed CORS origins, API health,
  and whether `DATABASE_URL` is configured for DB-backed flows.
- Preserve the visible error, status code, timestamp, endpoint, and price area.
- Resume only after the API health and required smoke checks pass.

## Live Status Restriction

The label "System Status: LIVE" must not be used during these incidents or in
the current MVP. It may be considered only after staging health, auth,
monitoring, and data freshness checks exist and have been reviewed.
