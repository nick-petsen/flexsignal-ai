# Changelog

## v0.1.0 - TODO

- Added public risk-window price context v1 for verified public surplus-risk
  windows. `scripts/public_surplus_risk_backtest.py` now includes per-window
  public DayAheadPrices context when joined source price rows are present:
  min/average/max EUR/MWh, negative/low price hour counts, availability
  status, and a deterministic public EUR/MWh opportunity signal. The signal
  uses `max(0, public low-price threshold 25 EUR/MWh - average window
  DayAheadPrices EUR/MWh)` and is public market/system-level only. The
  canonical snapshot schema and Reports risk-window table now support a
  compact `Public price signal` column using the canonical JSON artifact. The
  committed snapshot includes verified public DayAheadPrices-derived price
  context values for each top risk window.
  Added tests for deterministic signal calculation, unavailable context,
  snapshot fields, no database writes, API contract staying out of scope, and
  frontend snapshot typing. Updated README and model/backtest docs. This
  changed scripts/tests/frontend/docs only and added no backend endpoint,
  backend call from the frontend, database schema, migration, auth, Azure,
  weather/maps, polling/autoload, customer-specific calculation,
  control, dispatch, activation, live control signals, or asset integration.
- Added `scripts/customer_pilot_signal_match.py`, a scripts/tests/docs-only
  local read-only signal match preview for comparing validated customer pilot
  CSV rows with the canonical public surplus-risk snapshot at
  `frontend/src/data/public-surplus-risk-backtest-snapshot.json`. It reads
  `CUSTOMER_PILOT_INPUT_PATH`,
  `PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH`,
  `CUSTOMER_PILOT_PRICE_AREA`, `CUSTOMER_PILOT_MIN_MATCH_ROWS`, and
  `CUSTOMER_PILOT_DRY_RUN`, accepts CSV only for v0, writes no files, writes
  no database records, calls no external APIs, and prints a redacted JSON
  summary with matched DK1/DK2 public risk windows, customer row counts, data
  availability flags, optional availability and operational-note counts,
  warnings, and the read-only safety boundary. Added mocked local-only tests
  in `backend/tests/test_customer_pilot_signal_match.py` for DK1 overlap, DK2
  overlap, no overlap, missing required customer columns, invalid snapshot
  path, DK1/DK2 mismatch behavior, availability counts, limited customer data
  warnings, no file/db/external write behavior, and safety boundary text.
  Updated README and pilot docs with usage and the pilot flow: validate the
  customer intake CSV, match customer data to public risk windows, run human
  review, and only later estimate customer-specific potential if validated
  data supports it. This changed scripts/tests/docs only and added no
  frontend app code, backend API behavior, database schema, migrations, auth,
  Azure, weather/maps, fake customer data beyond tiny test fixtures,
  customer-specific savings calculation, profit/revenue calculation,
  financial advice, control, dispatch, activation, live control signals, or
  asset integration.
- Added `scripts/customer_pilot_intake_validate.py`, a scripts/tests/docs-only
  local CSV validator for customer pilot intake files before pilot/backtest
  analysis. It reads `CUSTOMER_PILOT_INPUT_PATH`,
  `CUSTOMER_PILOT_CUSTOMER_TYPE`, `CUSTOMER_PILOT_MIN_ROWS`, and
  `CUSTOMER_PILOT_DRY_RUN`, accepts CSV only for v0, prints a redacted
  validation summary, and exits non-zero for invalid input. Added mocked
  local-only tests in `backend/tests/test_customer_pilot_intake_validate.py`
  for valid common intake, missing required columns, invalid price areas, row
  minimums, secret-like column warnings, producer/flexible-consumption/grid
  warnings, no file/db/external write behavior, and safety boundary text.
  Updated README and pilot docs with usage and customer-type examples. This
  changed scripts/tests/docs only and added no frontend app code, backend API
  behavior, database schema, migrations, auth, Azure, weather/maps, fake
  customer data beyond tiny test fixtures, customer-specific savings
  calculation, profit/revenue calculation, control, dispatch, activation, live
  control signals, or asset integration.
- Added a docs-only customer pilot intake template in
  `docs/PILOT_INTAKE_TEMPLATE.md` plus a structured CSV request sheet at
  `docs/templates/customer_pilot_data_request.csv`. The template explains
  that the public DK1/DK2 backtest proves system/market-level signal behavior,
  while a customer pilot tests whether the signal matches customer operational
  reality. It covers common minimum data, producer/asset-owner/developer
  add-ons, flexible consumption/industrial load add-ons, grid/DSO add-ons,
  data format requirements, security/data-handling notes, expected pilot
  outputs, later-stage customer types, and out-of-scope boundaries. Updated
  `README.md` and `docs/PILOT_READINESS.md` to link the intake materials.
  This changed documentation/templates only and added no frontend app code,
  backend API behavior, scripts, tests, database schema, migrations, auth,
  Azure, weather/maps, fake data, customer-specific savings calculation,
  control, dispatch, activation, live control signals, or asset integration.
- Added a docs-only customer pilot readiness pack in
  `docs/PILOT_READINESS.md` and linked it from `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, and `docs/SECURITY.md`. The pack documents the
  purpose of a read-only customer pilot, pilot scope, required and optional
  customer data, minimum dataset, measurable success criteria, economic
  potential method, deliverables, data handling, human oversight, and
  out-of-scope boundaries. It states that public DK1/DK2 backtests demonstrate
  historical public system/market signal behavior, while customer-specific
  potential requires validated customer load, flexible MWh, constraints,
  tariff/price context, and human review. This changed documentation only and
  added no frontend app code, backend API behavior, scripts, tests, database
  schema, migrations, auth, Azure, weather/maps, fake data,
  customer-specific savings calculation, control, dispatch, activation, live
  control signals, or asset integration.
- Added `scripts/public_surplus_risk_snapshot_export.py`,
  `backend/tests/test_public_surplus_risk_snapshot_export.py`,
  `frontend/src/data/public-surplus-risk-backtest-snapshot.json`, and
  `frontend/src/lib/publicBacktestSnapshot.ts` to make the verified public
  DK1/DK2 surplus-risk proof-of-work reproducible as canonical JSON artifact
  v1. The artifact carries schema version
  `public_surplus_risk_snapshot.v1`, report metadata, DK1/DK2 summary metrics,
  verified top risk windows, commercial interpretation, pilot next step, and
  safety boundaries. Reports snapshot cards, the verified risk-window table,
  Markdown download, and printable report now consume the same JSON artifact
  through the typed frontend loader. Documented regeneration with
  `PUBLIC_SURPLUS_RISK_SNAPSHOT_WRITE=true /opt/homebrew/bin/python3.13 scripts/public_surplus_risk_snapshot_export.py`.
  The exporter is dry-run by default, writes only the configured JSON artifact
  when explicitly allowed, writes no database records, performs no network
  calls in tests, and does not calculate customer-specific savings. This adds
  no backend API behavior, database schema, migrations, backend endpoints,
  frontend backend calls, polling, autoload, auth, Azure, weather/maps, fake
  data, control, dispatch, activation, live control signals, or asset
  integration.
- Added `scripts/public_surplus_risk_report_export.py`, a scripts/tests/docs
  only Markdown report exporter for the verified public DK1/DK2 surplus-risk
  proof-of-work snapshot and current verified top risk-window table. It reads
  `BACKTEST_REPORT_FORMAT` (default `markdown`),
  `BACKTEST_REPORT_OUTPUT_PATH` (default empty), and
  `BACKTEST_REPORT_DRY_RUN` (default `true`), prints the report to stdout when
  no output path is set, and writes only the requested report file when an
  output path is provided. Added mocked/no-network tests for DK1/DK2 metrics,
  top risk windows, no customer-specific savings claim, safety boundary,
  dry-run no-write behavior, output-path write scope, and no database writes.
  Documented usage:
  `BACKTEST_REPORT_FORMAT=markdown python scripts/public_surplus_risk_report_export.py`
  and optional output:
  `BACKTEST_REPORT_OUTPUT_PATH=artifacts/public-surplus-risk-report.md python scripts/public_surplus_risk_report_export.py`.
  This changed scripts/tests/docs only and added no frontend app code,
  dashboard UI, backend API behavior, database schema, migrations, auth, Azure,
  weather/maps, fake data, customer-specific savings calculation, control,
  dispatch, activation, or asset integration.
- Added a scripts/tests/docs-only compact public surplus-risk window snapshot
  mode to `scripts/public_surplus_risk_backtest.py`. The script now reads
  `BACKTEST_TOP_RISK_WINDOWS` (default `10`) and
  `BACKTEST_WINDOW_SNAPSHOT_ONLY` (default `false`). When snapshot-only mode is
  enabled, it prints the top public DK1/DK2 risk windows per price area sorted
  by highest risk score, duration, and start timestamp, including timestamps,
  duration, highest and average risk scores when available, risk level,
  available negative/low-price hour counts, available renewable-share metrics,
  top reason codes, and a human-review recommendation. Missing optional metrics
  are shown as `not_calculated` and no values are invented. Added mocked tests
  for sorting, compact output, missing optional metrics, safety notes, dry-run
  no-write behavior, and recommended human-action wording. Updated README and
  backtest docs with the manual command:
  `BACKTEST_START_DATE=2026-01-01 BACKTEST_DRY_RUN=true BACKTEST_WINDOW_SNAPSHOT_ONLY=true python scripts/public_surplus_risk_backtest.py`.
  This is public market/system-level read-only decision support only, not
  customer-specific savings, and adds no frontend app code, dashboard UI,
  backend API behavior, database schema, migrations, auth, Azure, weather/maps,
  fake data, customer-specific savings, control, dispatch, activation, or asset
  integration.
- Added a docs-only public surplus-risk backtest snapshot v1 to `README.md`,
  `docs/BACKTEST_RESULTS.md`, and `docs/MODEL_CARD.md`. The snapshot records
  observed dry-run Energi Data Service `DayAheadPrices` and
  `ProductionConsumptionSettlement` results for `2026-01-01` to `now`:
  DK1 `4,208` joined hours, `233` skipped rows, `1,663` medium-risk hours,
  `174` high-risk hours, `129` risk windows, highest risk score `100`,
  `132` negative-price hours, `479` low-price hours, average renewable share
  `0.688094`, and max renewable share `1.922448`; DK2 `4,208` joined hours,
  `233` skipped rows, `288` medium-risk hours, `2` high-risk hours, `72` risk
  windows, highest risk score `85`, `78` negative-price hours, `491`
  low-price hours, average renewable share `0.38228`, and max renewable share
  `1.085669`. The documentation states that the system identified historical
  public DK1/DK2 surplus-risk windows using market price, consumption, and
  renewable production context. It also states that the result is not
  customer-specific savings, site revenue, or site profit; uses no customer
  load, asset, tariff, or operational data; and adds no automatic control,
  dispatch, activation, or asset integration. This changed documentation only
  and added no frontend app code, dashboard UI, backend API behavior, tests,
  database schema, migrations, auth, Azure, weather/maps, fake data,
  customer-specific savings, control, dispatch, activation, or asset
  integration.
- Added `scripts/public_surplus_risk_backtest.py`, a
  backend/script-only dry-run public surplus-risk backtest engine v1 for DK1
  and DK2 using only Energi Data Service `DayAheadPrices` and
  `ProductionConsumptionSettlement`. It reuses the public surplus-risk input
  foundation, reads the requested `BACKTEST_*` environment configuration,
  aggregates sub-hourly day-ahead price rows to hourly average EUR/MWh, joins
  rows by price area and hourly UTC timestamp, skips unjoinable or incomplete
  rows without inventing values, calculates renewable share and deterministic
  risk scores from transparent price/renewable rules, groups consecutive
  medium/high hours into risk windows, and prints per-area summaries with
  skipped counts and top reason codes. Added mocked tests for hourly price
  aggregation, joins, renewable-share calculation, low/medium/high scoring,
  risk-window grouping, skipped unjoinable rows, missing optional values,
  no customer-specific savings, dry-run no-write behavior, and safety notes.
  Updated README and backtest/model-card docs. This changed scripts/docs/tests
  only and added no frontend app code, dashboard UI, backend API behavior,
  database schema, migrations, auth, Azure, weather/maps, fake data,
  customer-specific savings, control, dispatch, activation, or asset
  integration.
- Added `scripts/public_surplus_risk_backtest_input.py`, a
  backend/script-only dry-run public surplus-risk backtest input foundation for
  DK1/DK2 using Energi Data Service `DayAheadPrices` and
  `ProductionConsumptionSettlement`. It reads `BACKTEST_START_DATE`,
  `BACKTEST_END_DATE`, `BACKTEST_PRICE_AREAS`, `BACKTEST_DRY_RUN`,
  `BACKTEST_EDS_REQUEST_DELAY_SECONDS`, and `BACKTEST_EDS_MAX_RETRIES`, with
  defaults of `2026-01-01`, `now`, `DK1,DK2`, dry-run mode, `1.0`, and `3`.
  The script reuses the public market input parsing, chunking, EDS host
  validation, and retry fetcher where practical; fetches both required public
  EDS datasets; normalizes rows into safe timestamped market/system-level
  structures with price, consumption, renewable generation, wind, solar,
  production-total-when-safe, and optional exchange fields; derives renewable
  generation only from available renewable fields; reports missing optional
  fields as warnings; and fails safely when a required dataset has no records
  or invalid required fields. The dry-run summary reports period, price areas,
  requested datasets, record counts, normalized row counts, dataset timestamp
  ranges, missing field warnings, source, dry-run status, and a note that this
  is public market/system-level data only and not customer-specific savings.
  Added mocked tests for default config, DK1/DK2 validation, both dataset
  normalizers, renewable derivation, missing optional field warnings, required
  dataset failure, dry-run no-write behavior, no customer-specific savings
  calculation, required dataset requests, EDS URL safety, and HTTP 429 retry
  handling. Updated README and backtest/data-source docs to state this is an
  input foundation only and that full surplus-risk scoring comes next. This
  changed scripts/docs/tests only and added no frontend app code, dashboard UI,
  backend API behavior, database schema, migrations, auth, Azure,
  weather/maps, fake data, customer-specific savings, control, dispatch,
  activation, or asset integration.
- Added public surplus-risk data source mapping v0 in `docs/DATA_SOURCES.md`
  and linked it from `README.md` and root `DATA_SOURCES.md`. The mapping
  documents candidate Energi Data Service sources beyond `DayAheadPrices` for a
  future public surplus-risk backtest: `ProductionConsumptionSettlement`,
  `ElectricityProdex5MinRealtime`, optional `ElectricityBalanceNonv`, optional
  exchange/import/export fields, and later out-of-scope DMI/weather. It lists
  purpose, expected fields, DK1/DK2 support, timestamp and area fields,
  required/optional/near-live status, and validation gaps without claiming a
  full surplus-production backtest or customer-specific savings. The required
  historical surplus-risk v1 sources are `DayAheadPrices` and
  `ProductionConsumptionSettlement`; `ElectricityProdex5MinRealtime` is
  classified as `near_live_later`, and `ElectricityBalanceNonv` is classified
  as `optional_later`. Added
  `scripts/public_surplus_data_source_check.py`, a dry-run/read-only EDS-only
  checker that validates candidate dataset availability and sample fields with
  small sequential `GET` requests, uses
  `SURPLUS_SOURCE_CHECK_REQUEST_DELAY_SECONDS` as the optional delay override
  with a `1.0` second default, treats optional/near-live HTTP 429 responses as
  warnings rather than overall failures, writes no files, writes no database
  records, calls no non-EDS APIs, and prints no raw environment values or
  secrets. This changed docs/scripts only and added no frontend app code,
  dashboard UI, backend API behavior, database schema, migrations, auth, Azure,
  weather/maps, fake data, customer-specific savings, control, dispatch,
  activation, or asset integration.
- Added a docs-only public market backtest snapshot v0 to `README.md` and
  `docs/BACKTEST_RESULTS.md`. The snapshot records observed dry-run
  Energi Data Service `DayAheadPrices` results for `2026-01-01` to `now`:
  DK1 `17,756` records, `601` negative-price records, `2,205` low-price
  records, and `94.32 EUR/MWh` opportunity signal; DK2 `17,756` records,
  `325` negative-price records, `2,234` low-price records, and
  `93.28 EUR/MWh` opportunity signal. The documentation states this is
  public DK1/DK2 market/system-level data only, not customer-specific
  savings, and that v0 uses DayAheadPrices only, not full surplus-production
  data. It also documents the commercial interpretation, limitations, and
  the next step that a customer pilot requires customer load, asset, tariff,
  and operational data. This changed documentation only and added no
  frontend app code, dashboard UI, backend API behavior, tests, database
  schema, migrations, auth, Azure, weather/maps, fake data, customer-specific
  savings, control, dispatch, activation, or asset integration.
- Added `scripts/public_market_backtest.py`, a backend/script-only dry-run
  public DK1/DK2 market price-opportunity backtest using only Energi Data
  Service `DayAheadPrices`. Usage:
  `BACKTEST_START_DATE=2026-01-01 BACKTEST_DRY_RUN=true python scripts/public_market_backtest.py`.
  It reuses the existing public market input foundation, reads
  `BACKTEST_START_DATE`, `BACKTEST_END_DATE`, `BACKTEST_PRICE_AREAS`,
  `BACKTEST_DRY_RUN`, and
  `BACKTEST_LOW_PRICE_THRESHOLD_EUR_PER_MWH` (default `25`), and reports
  per-price-area record counts, timestamp range, EUR/MWh average/min/max,
  negative-price counts, low-price counts/share, an observed-market
  EUR/MWh opportunity signal, and a clearly labelled scenario-only value per
  1 MWh. It writes no files or database rows by default or during the v0
  script path, calls no non-EDS APIs, and does not calculate revenue, profit,
  savings, site-specific value, MW, customer load, tariffs, taxes, fees, or
  asset behavior. Added mocked tests for negative and low-price counting,
  average/min/max, scenario value calculation, customer-specific savings
  warning, DayAheadPrices-only limitation wording, invalid price areas,
  missing records, invalid price values, and dry-run no-write behavior. This
  changed scripts/docs/tests only and added no frontend app code, dashboard
  UI, backend API behavior, database schema, migrations, auth, Azure,
  weather/maps, fake data, control, dispatch, activation, or asset
  integration.
- Added `scripts/public_market_backtest_input.py`, a backend/script-only
  dry-run public market input preview for DK1/DK2 backtest preparation. It
  reads `BACKTEST_START_DATE`, `BACKTEST_END_DATE`, `BACKTEST_PRICE_AREAS`,
  and `BACKTEST_DRY_RUN`; defaults to `2026-01-01`, `now`, `DK1,DK2`, and
  dry-run mode; fetches only Energi Data Service `DayAheadPrices`; normalizes
  records through the existing EDS normalizer; resolves
  `BACKTEST_END_DATE=now` to an EDS-compatible Danish-local
  `YYYY-MM-DDTHH:MM` timestamp before building requests; chunks longer date
  ranges; de-duplicates normalized rows across chunks by source record id;
  waits `BACKTEST_EDS_REQUEST_DELAY_SECONDS` seconds between EDS requests
  by default (`1.0`); retries EDS HTTP 429/transient 5xx responses up to
  `BACKTEST_EDS_MAX_RETRIES` times by default (`3`); respects `Retry-After`;
  writes no files or database rows; calls no non-EDS APIs; and prints a short
  summary that states the data is public market/system-level only and not
  customer-specific savings. Added mocked backend tests for config defaults,
  invalid price areas, dry-run no-write behavior, normalization, missing
  records, summary wording, invalid JSON handling, `now` resolution, chunking,
  duplicate suppression, default request parameter safety, 429 retry handling,
  exhausted retry failure, and inter-chunk request delay. This changed
  scripts/docs/tests only and added no frontend app code, dashboard UI,
  database schema, migrations, auth, Azure, weather/maps, fake data,
  customer-specific savings, control, dispatch, activation, or asset
  integration.
- Added `scripts/staging_smoke.py`, a script-only local/staging backend smoke
  check for MVP readiness. Usage:
  `BACKEND_BASE_URL=http://127.0.0.1:8000 python scripts/staging_smoke.py`.
  The script calls `GET /health`, `GET /api/system/readiness`, and
  `POST /api/dashboard/decision-summary/preview` for `DK1` and `DK2`; verifies
  read-only decision-support, human-review, no automatic control, no dispatch,
  and no activation flags; does not require `DATABASE_URL`; writes no files or
  database records; calls no external APIs beyond the configured backend; and
  does not print raw environment values. Added lightweight mocked tests for the
  script. This changed scripts/docs/tests only and added no frontend app code,
  backend API behavior, database schema, migrations, auth, Azure resources,
  weather/maps, fake data, control, dispatch, activation, or asset integration.
- Added backend-only staging smoke readiness endpoint
  `GET /api/system/readiness`. The endpoint returns JSON-only safe status
  fields for `flexsignal-ai-backend`, read-only decision-support and
  human-review flags, no automatic control, no dispatch, no activation,
  `database_configured`, `auth_configured=false`,
  `external_control_enabled=false`, and
  `system_status_label_allowed="Manual refresh mode"`. Missing
  `DATABASE_URL` returns HTTP 200 with degraded status and does not prevent
  app startup. Present `DATABASE_URL` is reported only as a boolean and is not
  leaked. The endpoint does not connect to the database, run migrations,
  perform writes, call external APIs, add auth, add Azure resources, add
  weather/maps, add fake data, modify frontend files, modify database schema,
  add migrations, or add control, dispatch, activation, or asset integration.
  Documentation now states this is a staging smoke/readiness endpoint, not
  production monitoring, and that System Status must remain Manual refresh
  mode until auth, staging health, monitoring, and data freshness checks exist.
- Added documentation-only staging and test-user readiness guidance in
  `README.md`, `docs/SECURITY.md`, `docs/HUMAN_OVERSIGHT.md`, and
  `docs/INCIDENT_RESPONSE.md`. The docs state that the current MVP is
  local/manual read-only decision support, not production live; list required
  staging configuration for `DATABASE_URL`, `NEXT_PUBLIC_API_BASE_URL`,
  allowed CORS origins, and future Entra ID auth settings; require backend
  tests, frontend build, secret checks, known migration status, DK1/DK2
  dashboard smoke, and report/audit/export smoke before external test users;
  restate human review before acting on recommendations; and document
  incidents for incorrect recommendations, stale data, failed ingestion, and
  unavailable API. The docs also state that "System Status: LIVE" must not be
  used until staging health, auth, monitoring, and data freshness checks exist.
  This changed documentation only and added no frontend, backend, test,
  database, migration, Azure, auth, weather, maps, fake data, control,
  dispatch, activation, or asset-integration behavior.
- Added backend-only Dashboard decision summary economic potential v0.
  `POST /api/dashboard/decision-summary/preview` now keeps
  `economic_potential` as `not_calculated` when no `forecast_rows` are
  provided or when caller-provided rows lack usable price and surplus-risk
  signals. When caller-provided rows contain usable low or negative
  DKK/MWh price data plus deterministic surplus-risk signals, the endpoint
  returns a conservative `EUR/MWh` price opportunity signal only. It is not a
  revenue forecast, site-specific savings estimate, profit estimate, automatic
  trading recommendation, control recommendation, dispatch workflow, or
  activation workflow. The endpoint still invents no forecast rows, load size,
  MW, MWh, tariffs, taxes, fees, customer assets, or fake data; calls no
  external APIs; uses no LLM/AI; changes no frontend files; and adds no
  database schema changes or migrations.
- Improved backend-only Dashboard decision summary forecast-window handling.
  `POST /api/dashboard/decision-summary/preview` now optionally accepts
  caller-provided `forecast_rows` and reuses the existing deterministic
  forecast-window preview logic to populate `next_surplus_window` when those
  rows are supplied. Missing or empty `forecast_rows` keep
  `next_surplus_window` as `not_calculated` with the honest source note. The
  endpoint does not invent forecast rows, generate fake KPI values, call
  external APIs, use LLM/AI explanations, modify the frontend, change the
  database schema, add migrations, or add control, dispatch, activation, or
  asset integration behavior.
- Documented the merged manual Dashboard decision summary cockpit flow. The
  dashboard now has a human-triggered `Load decision summary` action that
  calls `POST /api/dashboard/decision-summary/preview`; values load only
  after that manual action, with no auto-load and no polling. DK1/DK2 values
  come from existing backend read models where available, and the dashboard
  must not show fake or synthetic KPI values for this flow. Expected impact,
  economic potential, and next surplus window remain `not_calculated` unless
  backed by real backend logic. The decision summary does not use an LLM and
  remains read-only decision support requiring human review, with no
  automatic control, dispatch, activation, or operational asset integration.
  This documentation-only update changed no frontend code, backend code,
  tests, database code, migrations, API behavior, Azure, auth, ML/LLM,
  weather, maps, control, dispatch, or activation behavior.
- Added backend-only `POST /api/dashboard/decision-summary/preview` for the
  N&O Predict Dashboard cockpit decision summary. The endpoint accepts DK1/DK2
  `price_area`, returns read-only decision-support and human-review flags,
  explicitly states no automatic control, no dispatch, and no activation,
  reuses existing current-risk and freshness read paths only when available,
  and returns calm `not_available` / `not_calculated` fields otherwise.
  Expected impact and economic potential remain `not_calculated` because no
  existing real backend source provides them. This changed backend tests/docs
  only besides the new backend router registration: no frontend files,
  migrations, database schema, database writes, live EDS/DMI/weather or
  external API calls, ML/LLM decision engine, auth, Azure, control, dispatch,
  activation, or operational asset integration were added.
- Documented the merged Dashboard cockpit state wiring. Cockpit KPI tiles now
  update only after manual user clicks: `Load latest risk view` updates
  Current risk and Recommended action from the existing current risk flow when
  available, `Review forecast window` updates Next surplus window and
  Confidence from the existing forecast preview flow when available, and
  `Check data freshness` updates Data freshness from the existing freshness
  flow when available. Economic potential remains `Not calculated yet` unless
  real backend data exists. The topbar uses Manual refresh mode, not
  `System Status: LIVE`; Meteo / Weather remains placeholder-only. Observed
  manual smoke confirmed the cockpit buttons were clickable and KPI tiles
  updated after manual clicks. Example observed values may include Current
  risk `Medium`, Risk score `35/100`, Next surplus window `0-24h`,
  Confidence `100%`, Data freshness `OK`, and Economic potential
  `Not calculated yet`; these values come from existing backend/manual flows
  when available and are not fake frontend values. This documentation-only
  update changed no frontend code, backend code, database code, migrations,
  API endpoints, model logic, live weather behavior, control, dispatch,
  activation, auto-load, or polling behavior, and preserves read-only
  decision support with human review required.
- Polished the existing frontend-only navigation shell into a cleaner
  operations-grade energy intelligence UI. The visible frontend product
  branding now uses N&O Predict in the sidebar, topbar, dashboard title, and
  page metadata; technical repo, API, package, endpoint, and generated PDF
  filename names are not renamed in this step. The update keeps the deep green
  app background, sidebar sections, Manual refresh mode, existing cards, and
  all existing manual frontend flows while using cleaner neutral surfaces,
  logo-inspired green as the primary accent, refined sidebar/topbar states, a
  manual-state Decision overview cockpit, more whitespace, restrained button
  states, and a calmer `Decision support mode` safety presentation with the
  remaining safety constraints still visible. Meteo / Weather remains a
  placeholder only with no weather integration, fake maps, fake wind data, or
  fake AI congestion claims. This changed frontend UI and documentation only:
  no backend files, database code, migrations, API endpoints, API behavior,
  model behavior, live data, ML/LLM, auth, Azure infrastructure, control,
  dispatch, activation, or operational functionality changed.
- Added a frontend-only navigation shell and dark green N&O Predict /
  FlexSignal AI theme. The UI now has local-state section switching for
  Dashboard, Reports, Audit, Forecast, Data, and Meteo / Weather; a left
  sidebar; a topbar with product name and Manual refresh mode; visible
  read-only decision-support safety copy; and a Meteo / Weather placeholder
  that states weather integration is not implemented yet. Existing manual
  frontend cards remain accessible in their relevant sections. This changed
  frontend UI and documentation only: no backend files, database code,
  migrations, API endpoints, API behavior, live APIs, auth, Azure
  infrastructure, ML/LLM behavior, control, dispatch, activation, or
  operational functionality changed.
- Added a frontend-only manual `Audited PDF export` dashboard card and API
  helper for `POST /api/report/pdf/export/audited`. The helper uses
  `NEXT_PUBLIC_API_BASE_URL`, posts `{"price_area":"DK1"}`, treats successful
  responses as PDF Blob data, downloads using the `Content-Disposition`
  filename when available with `flexsignal-report-preview.pdf` as fallback,
  revokes the object URL after download, infers `starts_with_pdf` from the
  Blob prefix, and surfaces non-2xx errors visibly, including missing backend
  `DATABASE_URL` HTTP 503 responses. The card displays `content-type`,
  `content-disposition`, `byteLength`, `starts_with_pdf`, and the exposed
  audit/safety headers for decision support only, no file written, PDF
  generated in memory, audit event created/persisted/type/id/table, database
  query/write flags, database write scope, `requires_database_url`, and no
  control/dispatch/activation. The UI states that the flow generates PDF in
  memory, persists one audit event to `audit_events`, writes no server-side
  PDF file, limits database write scope to `audit_events` only, does not
  read/write energy data tables, does not call live EDS/DMI APIs, does not
  control, dispatch, or activate anything, and requires human review. This
  change is frontend plus docs only: it does not modify backend, database
  code, migrations, auth, Azure infrastructure, live API calls, ML/LLM
  behavior, control, dispatch, activation, or operational functionality, and
  it leaves the existing unaudited PDF export card available separately.
- Documented observed manual backend smoke results for audited PDF export in
  `README.md`, `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke used
  `POST http://127.0.0.1:8000/api/report/pdf/export/audited` with body
  `{"price_area":"DK1"}` and observed `HTTP/1.1 200 OK`,
  `content-type=application/pdf`,
  `content-disposition=attachment; filename="flexsignal-report-preview.pdf"`,
  `content-length=9950`, PDF document version 1.3 with 3 pages,
  `byte_length=9950`, and `starts_with_pdf=True`. Observed safety/audit
  headers included decision support only, no file written, PDF generated in
  memory, audit event created and persisted,
  `x-flexsignal-audit-event-type=report_pdf_export_requested`,
  `x-flexsignal-audit-table=audit_events`,
  `x-flexsignal-database-query-executed=false`,
  `x-flexsignal-database-write-performed=true`,
  `x-flexsignal-database-write-scope=audit_events_only`,
  `x-flexsignal-requires-database-url=true`,
  `x-flexsignal-no-control-dispatch-activation=true`, and
  `x-flexsignal-audit-event-id=audit_evt_5867f1fed9b9783d11deedda`. The
  observed database confirmation row for that event id was
  `event_type=report_pdf_export_requested`, `action=manual_pdf_export`,
  `resource_type=report`, and
  `occurred_at_utc=2026-06-29 00:08:43.304665+02`. Safety interpretation:
  backend PDF generation and audit persistence were validated in the same
  request; the PDF was generated in memory only; no server-side file was
  written; exactly one audit event was persisted to `audit_events`;
  `database_write_performed=true` refers only to the `audit_events` write;
  database write scope was `audit_events_only`; no energy data tables were
  read or written; no live EDS/DMI APIs were called; no ML/LLM behavior was
  used; no control, dispatch, activation, or operational energy-system
  integration occurred; human review remains required. The existing unaudited
  PDF export remains available separately. This documentation-only step added
  no code,
  changed no backend or frontend behavior, added no endpoint, did not run SQL
  in this workspace, did not access a database in this workspace, called no
  live APIs, generated no PDF in this workspace, wrote no generated files, and
  added no auth, Azure, ML/LLM, control, dispatch, activation, or operational
  functionality.
- Added backend-only audited report PDF export at
  `POST /api/report/pdf/export/audited`. The endpoint requires `DATABASE_URL`
  at request time while preserving app import without it, returns safe HTTP
  503 when missing, creates one `report_pdf_export_requested`
  `audit-event-v0` event, persists one row to `audit_events` only, generates
  the existing report PDF in memory, and returns `application/pdf` with
  audit/safety headers including `audit_events_only` write scope. The
  top-level database write flag is true only because the audit row was
  written; the existing unaudited `POST /api/report/pdf/export` remains
  available and unchanged with no database write. This change does not modify
  frontend wiring, migrations, energy data table access, live EDS/DMI calls,
  file writes, scheduler/Azure/auth behavior, ML/LLM behavior, or control,
  dispatch, activation, or operational functionality. Added focused backend
  tests and documentation in `README.md`, `docs/HUMAN_OVERSIGHT.md`,
  `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md`.
- Documented observed manual frontend UI smoke results for the `Audit PDF
  export persistence` card in `README.md`, `docs/HUMAN_OVERSIGHT.md`,
  `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md`. The smoke opened
  `http://127.0.0.1:3000`, used the dashboard card manually, and clicked
  `Persist audit event`. The UI displayed `audit_event_created=true`,
  `audit_event_persisted=true`, `database_query_executed=false`,
  `database_write_performed=true`, `requires_database_url=true`,
  `event_id=audit_evt_06e3fef85a37a66f24b6a4fb`,
  `event_type=report_pdf_export_requested`, `table=audit_events`,
  `conflict_behavior=ON CONFLICT (event_id) DO NOTHING`,
  `event.action=manual_pdf_export`, `event.resource_type=report`, and
  `event.resource_id=report-summary-v0-DK1-872ff94f403e4ddd`. Warnings stated
  that one `audit-event-v0` row was persisted to `audit_events` only, no PDF
  was generated, no file was written, and no energy data tables were read or
  written. The observed latest database row for
  `select event_id, event_type, action, resource_type, occurred_at_utc from
  audit_events order by occurred_at_utc desc limit 5;` matched the UI
  `event_id`, with `event_type=report_pdf_export_requested`,
  `action=manual_pdf_export`, `resource_type=report`, and
  `occurred_at_utc=2026-06-28 23:24:30.534349+02`. Safety interpretation:
  the frontend can manually trigger an `audit_events`-only DB write through
  the backend, validating the local frontend-to-backend-to-PostgreSQL audit
  persistence path. The action remains manual and isolated, is not
  automatically wired to PDF download yet, generated no PDF, wrote no file,
  read or wrote no energy data tables, called no live EDS/DMI APIs, used no
  ML/LLM behavior, and performed no control, dispatch, activation, or
  operational energy-system integration. Human review remains required. A
  temporary attempt to expose the local dev UI over LAN allowed page loading,
  but API actions were not validated over LAN; LAN sharing is out of MVP
  scope until CORS, origin, and auth strategy are handled separately. The
  verified smoke path is local `127.0.0.1`. This documentation-only step
  added no code, changed no frontend or backend behavior, added no endpoint,
  did not access a database, ran no SQL, called no live API, generated no
  PDF, wrote no generated files, and added no auth, Azure, ML/LLM, control,
  dispatch, activation, or operational functionality.
- Added a frontend-only manual `Audit PDF export persistence` smoke card for
  `POST /api/audit/pdf-export/persist`. The new API helper uses
  `NEXT_PUBLIC_API_BASE_URL`, posts JSON body `{"price_area":"DK1"}`, parses
  JSON safely, validates the expected response shape, and surfaces non-2xx
  backend errors visibly, including safe missing-`DATABASE_URL` HTTP 503
  responses. The card has a manual `Persist audit event` button, loading and
  error states, and displays `audit_event_created`,
  `audit_event_persisted`, `database_query_executed`,
  `database_write_performed`, `requires_database_url`, `event_id`,
  `event_type`, `table`, `conflict_behavior`, `event.action`,
  `event.resource_type`, `event.resource_id`, and warnings. The UI states
  that this is audit DB write only, writes only to `audit_events`, does not
  generate PDF output, does not write files, does not read/write energy data
  tables, does not call live EDS/DMI APIs, does not control, dispatch, or
  activate anything, and human review remains required. This change does not
  modify backend, database, migration, or PDF export endpoint code; does not
  automatically call audit persistence from PDF download yet; does not add
  auth, Azure infrastructure, live API calls, ML/LLM behavior, control,
  dispatch, activation, or operational functionality; and does not expose
  `DATABASE_URL` or secrets in the frontend.
- Documented observed manual local smoke results for backend audit
  persistence of manual PDF export events in `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke used
  `POST http://127.0.0.1:8000/api/audit/pdf-export/persist` with
  `Content-Type: application/json` and body `{"price_area":"DK1"}`. The HTTP
  response returned `HTTP/1.1 200 OK` with `content-type=application/json`
  and included `audit_event_created=true`,
  `audit_event_persisted=true`, `database_query_executed=false`,
  `database_write_performed=true`, `requires_database_url=true`,
  `event_type=report_pdf_export_requested`,
  `event_id=audit_evt_b0fb4e51563ca068ab4c2bba`,
  `table=audit_events`,
  `conflict_behavior=ON CONFLICT (event_id) DO NOTHING`,
  `action=manual_pdf_export`, `resource_type=report`,
  `resource_id=report-summary-v0-DK1-872ff94f403e4ddd`,
  `decision_support_only=true`, `read_only_decision_support=true`,
  `no_automatic_control=true`, `no_dispatch=true`, `no_activation=true`,
  `no_operational_energy_system_integration=true`,
  `human_review_required=true`, `pdf_generated_in_memory=true`,
  `server_side_file_written=false`, and
  `no_control_dispatch_activation=true`. The observed database confirmation
  queried `audit_events` ordered by `occurred_at_utc` and found the latest
  row `event_id=audit_evt_b0fb4e51563ca068ab4c2bba`,
  `event_type=report_pdf_export_requested`, `action=manual_pdf_export`,
  `resource_type=report`, and
  `occurred_at_utc=2026-06-27 00:39:47.295648+02`. Safety interpretation:
  this was the first verified runtime audit DB write; the write was limited
  to `audit_events` only; the endpoint required `DATABASE_URL` at request
  time; and the persisted event records a manual PDF export request. No PDF
  was generated by this endpoint, no file was written, no energy data tables
  were read or written, no live EDS/DMI APIs were called, no ML/LLM behavior
  was used, and no control, dispatch, activation, or operational
  energy-system integration occurred. Human review remains required, and the
  frontend automatic PDF-download audit persistence wiring is still absent.
  Clarified that top-level `database_write_performed=true` describes the
  `audit_events` persistence operation, while
  `event.metadata.database_write_performed=false` describes the underlying
  PDF export action, which did not itself perform a database write. Also
  documented local smoke notes: Alembic with
  SQLAlchemy/psycopg3 may require a `postgresql+psycopg://` URL for migration
  commands; runtime smoke used
  `postgresql://$(whoami)@localhost:5432/flexsignal_ai`; and the
  `audit_events` timestamp column is `occurred_at_utc`, not `created_at`.
  This documentation-only step added no code, changed no backend or frontend
  behavior, added no endpoint, did not generate a PDF, wrote no generated
  files, did not call live APIs, and added no scheduler, Azure, auth, ML/LLM,
  control, dispatch, activation, or operational functionality.
- Added backend-only manual PDF export audit persistence through
  `POST /api/audit/pdf-export/persist`. The endpoint creates the reviewed
  `report_pdf_export_requested` `audit-event-v0` event with
  `action=manual_pdf_export`, `resource_type=report`, default
  `price_area=DK1`,
  `resource_id=report-summary-v0-DK1-872ff94f403e4ddd`,
  `decision_support_only=true`, `human_review_required=true`,
  `pdf_generated_in_memory=true`, `server_side_file_written=false`,
  `database_query_executed=false`, and
  `no_control_dispatch_activation=true`, then writes one row to
  `audit_events` only through the existing audit writer/repository foundation
  with `ON CONFLICT (event_id) DO NOTHING`. It requires `DATABASE_URL` at
  request time only; app import still works without `DATABASE_URL`, and
  missing configuration returns safe HTTP 503 without exposing the raw URL.
  Successful responses include `audit_event_created=true`,
  `audit_event_persisted=true`, `database_write_performed=true`,
  `requires_database_url=true`, `event_id`, `event_type`,
  `table=audit_events`, `conflict_behavior`, and the preserved safety
  boundary. Added focused backend tests for route existence, import without
  `DATABASE_URL`, safe missing-configuration handling, invalid price-area
  handling, the single `audit_events` insert path, response flags, blocked
  PUT/PATCH/DELETE methods, and no PDF/file/external API/control behavior.
  This does not modify frontend code, generate PDFs, write files, access
  energy data tables, call live EDS/DMI APIs, add scheduler/Azure/auth
  behavior, use ML/LLMs, or add control, dispatch, activation, or operational
  functionality. Human review remains required and frontend wiring is not
  added yet.
- Documented observed manual API smoke results for manual PDF export audit
  preview in `README.md`, `docs/HUMAN_OVERSIGHT.md`,
  `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md`. The smoke used
  `POST http://127.0.0.1:8000/api/audit/preview` with `Content-Type:
  application/json` and body
  `{"event_type":"report_pdf_export_requested","price_area":"DK1"}`. The
  response returned `dry_run=true`, `audit_event_created=true`,
  `audit_event_persisted=false`, `database_write_performed=false`,
  `requires_database_url=false`, `event_type=report_pdf_export_requested`,
  `action=manual_pdf_export`, `resource_type=report`,
  `resource_id=report-summary-v0-DK1-872ff94f403e4ddd`,
  `decision_support_only=true`, `price_area=DK1`, `output_format=pdf`,
  `pdf_generated_in_memory=true`, `server_side_file_written=false`,
  `database_query_executed=false`, `no_control_dispatch_activation=true`,
  `persistence_plan.table=audit_events`,
  `persistence_plan.operation=insert_audit_event_v0`,
  `conflict_behavior=ON CONFLICT (event_id) DO NOTHING`, and
  `execution_performed=false`; warnings stated dry-run only and no database
  write. Safety interpretation: the audit preview creates an in-memory
  `audit-event-v0` style event only; the audit event was not persisted; SQL
  was previewed only, not executed; no database write was performed; no
  `DATABASE_URL` was required; no PDF was generated by this audit preview; no
  file was written; no live EDS/DMI API was called; no ML/LLM behavior was
  used; no control, dispatch, or activation occurred; runtime audit
  persistence remains a later separately reviewed step; and human review
  remains required. This documentation-only step added no code, changed no
  backend or frontend behavior, added no API endpoint, accessed no database,
  ran no SQL, called no live API, generated no PDF, wrote no generated files,
  and added no scheduler, Azure, auth, ML/LLM, audit write, control,
  dispatch, activation, or operational functionality.
- Added a backend-only dry-run audit preview for manual report PDF export
  requests through the existing `POST /api/audit/preview` endpoint. The new
  supported event type is `report_pdf_export_requested`; it creates an
  in-memory `audit-event-v0` style event with `action=manual_pdf_export`,
  `resource_type=report`,
  `resource_id=report-summary-v0-DK1-872ff94f403e4ddd` by default,
  `price_area=DK1` by default, `decision_support_only=true`,
  `human_review_required=true`, `pdf_generated_in_memory=true`,
  `server_side_file_written=false`, `database_query_executed=false`,
  `database_write_performed=false`, `requires_database_url=false`, and
  `no_control_dispatch_activation=true`. The response states
  `dry_run=true`, `audit_event_created=true`,
  `audit_event_persisted=false`, `database_write_performed=false`, and
  `requires_database_url=false`. This does not modify frontend code, persist
  audit events, generate PDFs, write files, access a database, require
  `DATABASE_URL`, run SQL, call live EDS/DMI APIs, or add scheduler, Azure,
  auth, ML/LLM, control, dispatch, activation, or operational behavior. Real
  audit persistence remains a later reviewed step.
- Documented observed manual frontend PDF download smoke results after the
  CORS exposed-header fix in `README.md`, `docs/HUMAN_OVERSIGHT.md`,
  `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md`. The smoke started the
  backend locally, started the frontend locally with
  `NEXT_PUBLIC_API_BASE_URL` pointing to the backend, opened the local
  dashboard in a browser, used the Report PDF export card manually, and
  clicked `Download PDF report`. The browser downloaded
  `flexsignal-report-preview.pdf`, and the file opened successfully as a PDF.
  No auto-download or polling was observed. Observed frontend values were
  `download_filename=flexsignal-report-preview.pdf`,
  `content-type=application/pdf`,
  `content-disposition=attachment; filename="flexsignal-report-preview.pdf"`,
  `byteLength=9950`, `decision_support_only` header `true`, `file_written`
  header `false`, `database_query_executed` header `false`,
  `database_write_performed` header `false`, and `requires_database_url`
  header `false`. Safety interpretation: the frontend download is manual and
  user-triggered; backend generated PDF bytes in memory; no server-side file
  was written; no file path was returned; no database query was executed by
  the PDF export; no database write was performed; no `DATABASE_URL` was
  required; no SQL was executed; no live EDS/DMI API was called; no ML/LLM
  behavior was used; no audit write occurred; no control, dispatch, or
  activation behavior occurred; and human review remains required. Other
  DB-backed dashboard cards may show `DATABASE_URL`-related errors when
  started without `DATABASE_URL`; that is expected for those DB-backed
  endpoints and is separate from the PDF export smoke result. This
  documentation-only step added no code, changed no frontend or backend
  behavior, added no API endpoint, did not access a database, ran no SQL,
  called no live API, generated no additional PDFs, and added no scheduler,
  Azure, auth, ML/LLM, audit write, control, dispatch, activation, or
  operational behavior.
- Added frontend manual PDF download support using the existing
  `POST /api/report/pdf/export` backend endpoint. The new API helper posts
  JSON body `{}` through the existing `NEXT_PUBLIC_API_BASE_URL` pattern,
  expects `application/pdf`, returns the PDF `Blob`, byte length, content
  type, content disposition, and explicit safety headers, and uses a generic
  non-200 error path that does not expose backend configuration values. The
  dashboard now includes a `Report PDF export` card with a manual
  `Download PDF report` button, loading and error states, browser
  Blob/Object URL download, safe `Content-Disposition` filename handling with
  `flexsignal-report-preview.pdf` fallback, and Object URL revocation after
  use. After manual click, the card displays that the PDF download was
  requested/generated from backend generated PDF bytes in memory, plus
  `content-type`, `content-disposition`, `byteLength`,
  `x-flexsignal-decision-support-only`, `x-flexsignal-file-written`,
  `x-flexsignal-database-query-executed`,
  `x-flexsignal-database-write-performed`, and
  `x-flexsignal-requires-database-url`. This frontend/docs change does not
  modify backend behavior, add endpoints, write server-side files, access a
  database from the frontend, run SQL, call live EDS/DMI APIs, add auth,
  migrations, Azure infrastructure, ML/LLM behavior, audit writes, or
  automation. It preserves manual read-only decision support with human review
  required.
- Added `POST /api/report/pdf/export` as a backend-only read-only PDF export
  endpoint. It uses deterministic synthetic or caller-provided preview data,
  builds `report-summary-v0`, renders Markdown, and returns non-empty
  `application/pdf` bytes in memory with download-safe headers and explicit
  safety headers. It writes no files, returns no file path, accesses no
  database, requires no `DATABASE_URL`, executes no SQL, calls no live
  Energi Data Service or DMI/weather APIs, uses no ML/LLM behavior, adds no
  frontend download flow, writes no audit events, and adds no control,
  dispatch, activation, or operational functionality.
- Documented observed manual API smoke results for
  `POST /api/report/pdf/export` in `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke used `Content-Type:
  application/json` and body `{}` against
  `http://127.0.0.1:8000/api/report/pdf/export`. The HTTP response returned
  status `200`, `content-type=application/pdf`,
  `content-disposition=attachment; filename="flexsignal-report-preview.pdf"`,
  `x-flexsignal-decision-support-only=true`,
  `x-flexsignal-file-written=false`,
  `x-flexsignal-database-query-executed=false`,
  `x-flexsignal-database-write-performed=false`,
  `x-flexsignal-requires-database-url=false`, `byte_length=9950`, and a body
  starting with `%PDF`. Safety interpretation: the endpoint generated PDF
  bytes in memory, wrote no PDF file, returned no file path, executed no
  database query, performed no database write, required no `DATABASE_URL`,
  executed no SQL, called no live EDS/DMI API, used no ML/LLM behavior, wrote
  no audit event, added no frontend download UI, and performed no control,
  dispatch, or activation behavior. Human review remains required. This
  documentation-only step added no code, changed no backend or frontend
  behavior, added no endpoint, accessed no database, ran no SQL, called no
  live API, and added no scheduler, Azure, auth, audit writes, control,
  dispatch, activation, or operational functionality.
- Documented observed manual frontend Report PDF dry-run preview smoke
  results in `README.md`, `docs/HUMAN_OVERSIGHT.md`,
  `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md`. The smoke started
  the backend locally, started the frontend locally with
  `NEXT_PUBLIC_API_BASE_URL` pointing to the backend, opened the local
  dashboard in a browser, and loaded the Report PDF dry-run preview by
  manual button click only. No auto-load or polling was observed. The Report
  PDF dry-run preview card was displayed, and the manual button called
  `POST /api/report/pdf/preview`. Displayed flags were
  `pdf_preview_planned=true`, `pdf_generated=false`, `file_written=false`,
  `markdown_preview_generated=true`, `database_query_executed=false`,
  `database_write_performed=false`, `requires_database_url=false`, and
  `decision_support_only=true`. Displayed content included
  `planned_source=report-summary-v0 + markdown preview`,
  `planned_output_format=pdf`, `markdown_character_count=3621`, report
  title, `price_area=DK1`, `generated_at_utc`, `markdown_excerpt`,
  warnings, and `safety_boundary`. No download button or PDF
  export/generation button was shown, and no file generation behavior was
  visible. This documentation-only step added no code, changed no frontend or
  backend behavior, added no API endpoint, did not access a database,
  executed no SQL, called no live APIs, generated no PDF, wrote no files
  beyond the requested docs, added no scheduler, Azure, auth, ML/LLM, audit
  write, control, dispatch, activation, or operational behavior, and
  preserved required human review.
- Added frontend Report PDF dry-run preview support using the existing
  `POST /api/report/pdf/preview` backend endpoint. The new API helper posts
  JSON body `{}` through the existing `NEXT_PUBLIC_API_BASE_URL` pattern and
  handles non-200 responses with the shared frontend API error handling. The
  dashboard now includes a manual `Report PDF dry-run preview` card with a
  `Load PDF dry-run preview` button, loading and error states, and no
  auto-load or polling. The card displays PDF dry-run preview only after
  manual click, including `pdf_preview_planned`, `pdf_generated`,
  `file_written`, `markdown_preview_generated`, `database_query_executed`,
  `database_write_performed`, `requires_database_url`,
  `decision_support_only`, `planned_source`, `planned_output_format`,
  `markdown_character_count`, optional `markdown_excerpt`, warnings,
  report title, `price_area`, `generated_at_utc`, and `safety_boundary`. This
  frontend/docs change does not modify backend behavior, add endpoints,
  generate PDFs, add downloads, write files, access a database from the
  frontend, run SQL, call live EDS/DMI APIs, add auth, migrations, Azure
  infrastructure, ML/LLM behavior, or audit writes. It prepares a future
  controlled PDF export flow while preserving read-only decision support and
  human review.
- Documented observed manual API smoke results for
  `POST /api/report/pdf/preview` in `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke used `Content-Type:
  application/json` and body `{}` against
  `http://127.0.0.1:8000/api/report/pdf/preview`. The HTTP response returned
  valid JSON with `pdf_preview_planned=true`, `pdf_generated=false`,
  `file_written=false`, `markdown_preview_generated=true`,
  `database_query_executed=false`, `database_write_performed=false`,
  `requires_database_url=false`, `decision_support_only=true`,
  `planned_source=report-summary-v0 + markdown preview`,
  `planned_output_format=pdf`, `report_summary`, `markdown_excerpt`,
  `markdown_character_count=3621`, warnings, and `safety_boundary`. Observed
  warnings stated dry-run preview only, no PDF generated, no file written, no
  database read/write, no live EDS/DMI calls, and no control, dispatch, or
  activation. Safety interpretation: the endpoint works without
  `DATABASE_URL`, only plans a future PDF export, generated no PDF bytes,
  called no PDF renderer, returned no file path or download, wrote no file,
  executed no database query or write, executed no SQL, called no live EDS/DMI
  API, used no ML/LLM behavior, and performed no control, dispatch, or
  activation behavior. Human review remains required. This documentation-only
  step added no code, changed no backend or frontend behavior, added no
  endpoint, accessed no database, ran no SQL, called no live API, generated no
  PDF, wrote no files beyond the requested docs, and added no scheduler,
  Azure, auth, audit writes, control, dispatch, activation, or operational
  functionality.
- Added `POST /api/report/pdf/preview` as a backend-only read-only PDF
  dry-run preview API. The endpoint uses deterministic synthetic or
  caller-provided preview data, reuses the existing `report-summary-v0` plus
  Markdown preview foundation, and returns structured JSON with
  `pdf_preview_planned=true`, `pdf_generated=false`, `file_written=false`,
  `markdown_preview_generated=true`, no database read/write flags,
  `requires_database_url=false`, `planned_source`, `planned_output_format`,
  `report_summary`, a Markdown excerpt/count, explicit safety boundary, and
  warnings. It prepares future PDF export planning only; it does not generate
  PDF bytes, write files, access a database, require `DATABASE_URL`, run SQL,
  call live Energi Data Service or DMI/weather APIs, use ML/LLM behavior, add
  auth, scheduler/Azure infrastructure, audit writes, frontend behavior,
  control, dispatch, activation, or operational functionality.
- Documented observed manual frontend Report Markdown preview smoke results
  in `README.md`, `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke started the backend locally, started
  the frontend locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend, opened the local dashboard in a browser, and loaded Report Markdown
  preview by manual button click only. No auto-load or polling was observed.
  The Report Markdown preview card displayed Markdown preview only, and the
  manual button called `POST /api/report/markdown/preview`. Displayed flags
  were `markdown_preview_generated=true`, `pdf_generated=false`,
  `file_written=false`, `database_query_executed=false`,
  `database_write_performed=false`, `requires_database_url=false`, and
  `decision_support_only=true`. Displayed content included the report title,
  `price_area=DK1`, `generated_at_utc`, rendered Markdown text block, and
  `safety_boundary`. No download button or PDF export button was shown, and
  no file generation behavior was visible. This documentation-only step added
  no code, changed no frontend or backend behavior, added no API endpoint,
  did not access a database, executed no SQL, called no live APIs, generated
  no PDF, wrote no files beyond the requested docs, added no scheduler,
  Azure, auth, ML/LLM, audit write, control, dispatch, activation, or
  operational behavior, and preserved required human review.
- Added frontend Report Markdown preview support using the existing
  `POST /api/report/markdown/preview` backend endpoint. The new API helper
  posts JSON body `{}` through the existing `NEXT_PUBLIC_API_BASE_URL`
  pattern and handles non-200 responses with the shared frontend API error
  handling. The dashboard now includes a manual `Report Markdown preview`
  card with a `Load report Markdown preview` button, loading and error states,
  and no auto-load or polling. The card displays Markdown preview only after
  manual click, including `markdown_preview_generated`, `pdf_generated`,
  `file_written`, `database_query_executed`, `database_write_performed`,
  `requires_database_url`, `decision_support_only`, report title,
  `price_area`, `generated_at_utc`, rendered Markdown text, and
  `safety_boundary`. This frontend/docs change does not modify backend
  behavior, add endpoints, generate PDFs, write files, access a database from
  the frontend, run SQL, call live EDS/DMI APIs, add auth, migrations, Azure
  infrastructure, ML/LLM behavior, or audit writes. It prepares a future PDF
  export UI flow while preserving read-only decision support and human review.
- Documented observed manual API smoke results for
  `POST /api/report/markdown/preview` in `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke used `Content-Type:
  application/json` and body `{}` against
  `http://127.0.0.1:8000/api/report/markdown/preview`. The HTTP response
  returned valid JSON with `markdown_preview_generated=true`, non-empty
  Markdown, `pdf_generated=false`, `file_written=false`,
  `database_query_executed=false`, `database_write_performed=false`,
  `requires_database_url=false`, `decision_support_only=true`,
  `report_summary`, and `safety_boundary`. Observed Markdown content included
  the report title, report metadata, `price_area=DK1`,
  `generated_at_utc=2026-01-01T00:00:00Z`, current risk summary, forecast
  window summary, `0-24h`, `24-48h`, and `48-72h` forecast windows, key
  findings, recommended human actions, safety notes, limitations, source
  notes, and read-only / human-review wording. Safety interpretation: the
  endpoint works without `DATABASE_URL`, uses deterministic
  synthetic/caller-provided preview data, generated Markdown preview only,
  generated no PDF, wrote no file, executed no database query, performed no
  database write, executed no SQL, called no live EDS/DMI API, used no ML/LLM
  behavior, and performed no control, dispatch, or activation behavior. Human
  review remains required. This documentation-only step added no code,
  changed no backend or frontend behavior, added no endpoint, accessed no
  database, ran no SQL, called no live API, generated no PDF, wrote no files
  beyond the requested docs, and added no scheduler, Azure, auth, audit
  writes, control, dispatch, activation, or operational functionality.
- Added `POST /api/report/markdown/preview` as a backend-only read-only
  Markdown report preview API. The endpoint uses deterministic synthetic or
  caller-provided preview data, reuses the existing `report-summary-v0` and
  Markdown rendering foundation, and returns structured JSON with Markdown,
  `report_summary`, safety boundary fields, and explicit execution flags. It
  prepares a future PDF export flow but does not generate PDF output, write
  files, access a database, require `DATABASE_URL`, execute SQL, call live
  Energi Data Service or DMI/weather APIs, use ML/LLM behavior, add auth,
  scheduler/Azure infrastructure, audit writes, frontend behavior, control,
  dispatch, activation, or operational functionality.
- Documented observed manual frontend Report summary preview smoke results in
  `README.md`, `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke started the backend locally, started
  the frontend locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend, opened the local dashboard in a browser, and loaded Report summary
  preview by manual button click only. No auto-load or polling was observed.
  The Report summary preview card displayed JSON preview only, and the manual
  button called `POST /api/report/summary/preview`. Displayed flags were
  `report_preview_generated=true`, `pdf_generated=false`,
  `file_written=false`, `database_query_executed=false`,
  `database_write_performed=false`, `requires_database_url=false`, and
  `decision_support_only=true`. Displayed content included the report title,
  `price_area=DK1`, `generated_at_utc`, current risk summary, forecast window
  summary, `0-24h`, `24-48h`, and `48-72h` forecast windows,
  `key_findings`, `recommended_human_actions`, `safety_notes`,
  `limitations`, `explanation`, and `safety_boundary`. This documentation
  step added no code, changed no frontend or backend behavior, added no API
  endpoint, did not access a database, executed no SQL, called no live APIs,
  generated no PDF, wrote no files beyond the requested docs, added no
  scheduler, Azure, auth, ML/LLM, audit write, control, dispatch, activation,
  or operational behavior, and preserved required human review.
- Added frontend Report summary preview support using the existing
  `POST /api/report/summary/preview` backend endpoint. The new API helper
  posts JSON body `{}` through the existing `NEXT_PUBLIC_API_BASE_URL`
  pattern and handles non-200 responses with the shared frontend API error
  handling. The dashboard now includes a manual `Report summary preview` card
  with a `Load report summary preview` button, loading and error states, and
  no auto-load or polling. The card displays JSON preview only after manual
  click, including preview execution flags, report title, `price_area`,
  `generated_at_utc`, current risk summary, forecast window summary,
  `key_findings`, `recommended_human_actions`, `safety_notes`, `limitations`,
  `explanation`, and `safety_boundary`. This frontend/docs change does not
  modify backend behavior, add endpoints, generate PDFs, write files, access a
  database from the frontend, run SQL, call live EDS/DMI APIs, add auth,
  migrations, Azure infrastructure, ML/LLM behavior, audit writes, or add
  operational functionality. It prepares a future PDF export UI flow while
  preserving read-only decision support and human review.
- Documented observed manual API smoke results for
  `POST /api/report/summary/preview` in `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke used `Content-Type:
  application/json` and body `{}` against
  `http://127.0.0.1:8000/api/report/summary/preview`. The HTTP response
  returned valid JSON with `report_preview_generated=true`,
  `pdf_generated=false`, `file_written=false`,
  `database_query_executed=false`, `database_write_performed=false`,
  `requires_database_url=false`, `decision_support_only=true`,
  `report_summary`, recommendations, explanation, and `safety_boundary`.
  Observed `report_summary` fields included
  `report_version=report-summary-v0`, `price_area=DK1`,
  `generated_at_utc=2026-01-01T00:00:00Z`, available medium current risk,
  available forecast-window summary with
  `model_version=rule-engine-v0+forecast-window-v0`, and windows for
  `0-24h`, `24-48h`, and `48-72h`. This documentation step added no code,
  changed no backend or frontend behavior, added no endpoint, accessed no
  database, ran no SQL, called no live API, generated no PDF, wrote no files
  beyond the requested docs, used no ML/LLM behavior, and added no scheduler,
  Azure, auth, audit writes, control, dispatch, activation, or operational
  functionality. Human review remains required.
- Added `POST /api/report/summary/preview` as a backend-only read-only report
  summary preview API. The endpoint uses deterministic synthetic or
  caller-provided preview data with the existing `report-summary-v0`
  foundation, returns explicit safety and execution flags, and prepares a
  future UI report/PDF flow without generating PDFs yet. It does not modify
  frontend code, write files, access a database, require `DATABASE_URL`,
  execute SQL, call live Energi Data Service or DMI/weather APIs, use ML/LLM
  behavior, add scheduler/Azure/auth/audit writes, or add control, dispatch,
  activation, or operational functionality. Focused backend tests cover route
  existence, HTTP 200 response, import without `DATABASE_URL`, response
  flags, allowed POST-only preview behavior, and no file/PDF/DB/SQL/external
  API/action behavior.
- Documented observed manual frontend forecast window visual smoke results in
  `README.md`, `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke started the backend locally, started
  the frontend locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend, opened the local dashboard in a browser, and loaded forecast
  preview by manual button click only. No auto-load or polling was observed.
  The forecast window visual displayed `0-24h`, `24-48h`, and `48-72h`
  windows. Each window displayed `risk_level`, max risk score as a 0-100
  score, a visible horizontal risk bar, `top_reason_codes`, and
  `recommended_human_action`; raw/text forecast details remained visible
  below the visual. Observed values were `0-24h`: low, `30/100`; `24-48h`:
  high, `75/100`; `48-72h`: low, `10/100`;
  `model_version=rule-engine-v0+forecast-window-v0`;
  `decision_support_only=true`; and
  `generated_at_utc=2026-01-01T00:00:00Z`. The visual uses only the existing
  manual `Load forecast preview` response with synthetic/caller-provided
  preview data. This documentation step added no code, changed no frontend or
  backend behavior, added no backend endpoint, did not access a database,
  executed no SQL, wrote nothing to the database, called no live APIs, and
  added no scheduler, Azure, auth, ML/LLM, audit write, report/PDF wiring,
  automatic control, dispatch, activation, or operational functionality.
  Human review remains required.
- Added a simple frontend forecast-window visual inside the existing manual
  "Forecast preview" card. The visual appears only after the existing "Load
  forecast preview" action returns data, uses only that existing
  deterministic synthetic/caller-provided preview response, displays returned
  windows such as `0-24h`, `24-48h`, and `48-72h` with `risk_level`, max or
  average risk score, top reason codes, and `recommended_human_action`, and
  keeps the raw text/details visible below the visual. The risk bars use
  lightweight HTML/CSS only with no charting dependency. This adds no API
  endpoint, backend behavior, database code, SQL execution, database write,
  migration, live Energi Data Service call, DMI/weather call, auth, Azure
  infrastructure, ML/LLM behavior, audit write, report/PDF wiring,
  auto-loading, polling, automatic control, closed-loop workflow, or
  operational functionality. It prepares MVP 24-72h forecast readability as
  read-only decision support with human review required.
- Documented observed manual frontend risk score visual smoke results in
  `README.md`, `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke started the backend locally, started
  the frontend locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend, opened the local dashboard in a browser, and loaded current
  surplus risk by manual button click only. No auto-load or polling was
  observed. DK1 displayed `price_area=DK1`, `risk_score=35/100`,
  `risk_level=medium`, the visible `Decision-support risk score` box, a
  visible 0-100 horizontal bar, `Human review required`, raw/text risk
  details below the visual, and `decision_support_only=true`. DK2 displayed
  `price_area=DK2`, `risk_score=20/100`, `risk_level=low`, the same visual
  box, 0-100 bar, human-review wording, raw/text details, and
  `decision_support_only=true`. The visual uses only the existing manual
  `Load current risk` response. This documentation step added no code,
  changed no frontend or backend behavior, added no backend endpoint, did not
  access a database, executed no SQL, wrote nothing to the database, called no
  live APIs, and added no scheduler, Azure, auth, ML/LLM, audit write,
  report/PDF wiring, automatic control, dispatch, activation, or operational
  functionality. Human review remains required.
- Added a simple frontend visual surplus risk score inside the existing
  manual Current surplus risk card. The visual appears only after the
  existing `Load current risk` flow returns a result, uses only that existing
  current-risk backend response, displays `risk_score` as a 0-100
  decision-support score when valid, displays `risk_level`, keeps the raw
  text/details visible, and handles missing or invalid score/level fields
  without crashing. It uses lightweight HTML/CSS only with no charting
  dependency, no new API endpoint, no backend behavior change, no database
  code, no SQL, no database write, no live Energi Data Service or DMI/weather
  browser call, no auth, no Azure infrastructure, no ML/LLM, no audit write,
  no report/PDF wiring, and no automation/control behavior. UI wording
  preserves read-only decision support with `Decision-support risk score`,
  `Human review required`, and `Read-only recommendation context`.
- Documented frontend risk score visual validation results in `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. Observed validation recorded `npm run build`
  passing after `npm ci` installed frontend dependencies from the existing
  lockfile; `git diff --check` passed; `npm run lint` and
  `npm run typecheck` scripts did not exist. No backend server was started,
  no database was accessed, no SQL was executed, and no live Energi Data
  Service or DMI/weather APIs were called. `npm audit` reported 2 moderate
  findings, but dependency files were not changed in this scoped UI/docs task.
  This prepares MVP dashboard readability only and does not add a new
  endpoint, backend behavior, ML/LLM behavior, automation, control, dispatch,
  or activation. A future module may manually smoke-test the risk visual in
  the local frontend/backend dashboard, and another future module may improve
  dashboard layout and visual hierarchy, without adding ingestion, automation,
  database writes, backend changes, or ML/LLM behavior in this docs step.
- Documented observed manual frontend dashboard chart smoke results in
  `README.md`, `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The smoke started the backend locally, started
  the frontend locally with `NEXT_PUBLIC_API_BASE_URL` pointing to the
  backend, opened the local dashboard in a browser, and used manual button
  clicks only. No auto-load or polling was observed. DK1 spot prices loaded,
  the spot price table remained visible, the spot price trend chart displayed,
  DK1 power balance loaded, the power balance table remained visible, and the
  power balance trend chart displayed. After switching the price area to DK2,
  DK2 spot prices and power balance loaded with the same table and trend-chart
  behavior. Charts used only manually loaded backend rows. UI wording remains
  read-only: `Manual read-only spot price rows`, `Manual read-only power
  balance rows`, and `Trend from loaded backend rows`. This documentation step
  added no code, changed no frontend or backend behavior, added no backend
  endpoint or charting dependency, made no browser call to Energi Data
  Service, made no DMI/weather call, executed no SQL from the frontend,
  accessed no database, wrote nothing to the database, called no live APIs,
  executed no forecast logic from the chart itself, and added no scheduler,
  Azure, auth, ML/LLM, audit write, report/PDF wiring, polling, control,
  dispatch, activation, automation, energy-asset control, or operational
  functionality.
- Added a simple frontend power balance trend chart inside the existing manual
  Power balance card. The chart renders production MW over timestamp order
  from only the power balance rows already returned by the existing manual
  `Load power balance` backend request, keeps the table visible, supports the
  selected `DK1`/`DK2` result, handles empty, single-point, multi-point,
  missing, and invalid chart values safely, and uses lightweight inline
  SVG/HTML/CSS with no charting dependency. It does not auto-load, poll, add a
  backend endpoint, call live Energi Data Service or DMI/weather APIs from the
  browser, execute SQL, write to the database, add migrations, add auth, add
  Azure infrastructure, use ML/LLM behavior, write audit events, wire
  report/PDF flows, forecast, trade, control assets, or add control,
  dispatch, activation, automation, or operational functionality. This
  prepares MVP dashboard visualization only.
- Documented frontend power balance chart validation results in `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. Observed validation recorded `npm run build`
  passing and `git diff --check` passing; `npm run lint` and
  `npm run typecheck` scripts did not exist. No backend server was started,
  no database was accessed, no SQL was executed, and no live Energi Data
  Service or DMI/weather APIs were called. The documentation records that the
  chart renders in/near the existing Power balance card, uses only rows from
  the manual `Load power balance` action, keeps the existing table visible,
  renders only when rows exist, supports `DK1`/`DK2` through the selected
  price area, uses inline SVG/HTML/CSS without a charting dependency, plots
  `production_mw` over timestamp order, and safely handles empty, single-row,
  invalid timestamp, and invalid MW values. This documentation step did not
  add code, change frontend behavior, change backend behavior, add endpoints,
  access a database, execute SQL, write to a database, call live APIs, add
  auth, add Azure infrastructure, add ML/LLM behavior, write audit events,
  wire report/PDF flows, or add control, dispatch, activation, or operational
  functionality. Together with the spot price chart, this completes the first
  MVP pair of read-only dashboard visualizations. Future modules may improve
  dashboard layout and chart readability or add a manual local frontend smoke
  test for both charts without adding ingestion, automation, DB writes, or
  backend changes.
- Added a simple frontend spot price trend chart inside the existing manual
  Spot prices card. The chart renders EUR/MWh over timestamp order from only
  the spot price rows already returned by the existing manual
  `Load spot prices` backend request, keeps the table visible, supports the
  selected `DK1`/`DK2` result, handles empty, single-point, multi-point,
  missing, and invalid chart values safely, and uses lightweight inline
  SVG/HTML/CSS with no charting dependency. It does not auto-load, poll, add a
  backend endpoint, call live Energi Data Service or DMI/weather APIs from the
  browser, execute SQL, write to the database, add migrations, add auth, add
  Azure infrastructure, use ML/LLM behavior, write audit events, wire
  report/PDF flows, forecast, trade, control assets, or add control,
  dispatch, activation, automation, or operational functionality. This
  prepares MVP dashboard visualization only.
- Documented frontend spot price chart validation results in `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. Observed validation recorded `npm run build`
  passing and `git diff --check` passing; `npm run lint` and
  `npm run typecheck` scripts did not exist. No backend server was started,
  no database was accessed, no SQL was executed, and no live Energi Data
  Service or DMI/weather APIs were called. This documentation step did not add
  code, change frontend behavior, change backend behavior, add endpoints, add
  ingestion, add automation, add auth, add Azure infrastructure, add ML/LLM
  behavior, write audit events, wire report/PDF flows, or add control,
  dispatch, activation, or operational functionality. Future modules may
  improve dashboard layout without adding ingestion, automation, or backend
  changes in this docs step.
- Documented observed manual frontend plus backend energy freshness smoke
  results in `README.md`, `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`,
  and `docs/BACKTEST_RESULTS.md`. The smoke started the backend locally with
  `DATABASE_URL=postgresql://localhost/flexsignal_ai`, started the frontend
  locally with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`, opened the
  local dashboard in a browser, and used manual button clicks only. No
  auto-load or polling was observed. The dashboard loaded DK1/DK2 spot
  prices, power balance, current surplus risk, forecast preview,
  DB-backed energy freshness reads, and dry-run freshness query-plan
  previews. Observed DB-backed DK1 freshness returned `dry_run=false`,
  `database_query_executed=true`, `database_write_performed=false`,
  `requires_database_url=true`, spot price `row_count=53`, spot price latest
  timestamp `2026-06-11T21:45:00+02:00`, power balance `row_count=53`, power
  balance latest timestamp `2026-06-10T17:00:00+02:00`, and preserved the
  safety boundary. Observed DB-backed DK2 freshness returned the same
  execution flags, spot price `row_count=50`, spot price latest timestamp
  `2026-06-11T21:45:00+02:00`, power balance `row_count=50`, power balance
  latest timestamp `2026-06-10T17:00:00+02:00`, and preserved the safety
  boundary. Observed dry-run freshness preview returned `dry_run=true`,
  `database_query_executed=false`, `database_write_performed=false`,
  `requires_database_url=false`, spot price and power balance query plans,
  and no SQL execution. UI wording records DB-backed freshness read,
  SELECT-only read, no database write performed, freshness of stored
  local/configured database data, no new EDS/DMI fetch, and no implication
  that ingestion has run. This is documentation only: no code, frontend
  behavior, backend behavior, endpoint, database access, SQL, database write,
  live API call, scheduler, Azure, auth, ML/LLM, audit write, report/PDF
  wiring, control, dispatch, activation, or operational behavior was added.
- Documented frontend DB-backed energy freshness read wiring validation in
  `README.md`, `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. The documentation records that
  `fetchEnergyFreshnessRead(priceArea)` manually calls
  `GET /api/energy/freshness/read?price_area=DK1|DK2`, while the existing
  `fetchEnergyFreshness()` dry-run preview path remains preserved. The
  dashboard freshness card has controls for DB-backed reads and dry-run
  previews, displays SELECT-only stored/configured freshness fields, latest
  timestamps, row counts, `database_query_executed`,
  `database_write_performed`, `requires_database_url`, warnings, and the
  read-only human-review safety boundary, and maps missing backend
  `DATABASE_URL` HTTP 503 responses to
  `DB-backed freshness read requires backend DATABASE_URL.` Observed
  validation recorded `npm run build` passing, `git diff --check` passing,
  `npm run lint` and `npm run typecheck` scripts not existing, no backend
  server started, no frontend dev server started, no database access, no SQL
  execution, and no live EDS/DMI API calls. This change is documentation
  only: no backend behavior change, no new endpoint, no database code, no SQL
  execution from the frontend, no database write, no migration, no live EDS or
  DMI/weather call, no auth, no Azure infrastructure, no ML/LLM, no audit
  write, no report/PDF wiring, and no control, dispatch, activation, or
  operational functionality.
- Updated the frontend energy freshness card to support manual DB-backed
  freshness reads through the existing
  `GET /api/energy/freshness/read?price_area=DK1|DK2` endpoint while keeping
  the existing dry-run preview helper for
  `GET /api/energy/freshness?price_area=DK1|DK2`. The frontend now exposes a
  `fetchEnergyFreshnessRead()` API helper that uses the existing
  `NEXT_PUBLIC_API_BASE_URL` pattern, handles non-200 responses safely, maps
  the missing-`DATABASE_URL` HTTP 503 response to
  `DB-backed freshness read requires backend DATABASE_URL.`, and does not
  expose secrets or database URLs. The card displays `price_area`, `dry_run`,
  `database_query_executed`, `database_write_performed`,
  `requires_database_url`, `spot_price_freshness.latest_timestamp`,
  `spot_price_freshness.row_count`,
  `power_balance_freshness.latest_timestamp`,
  `power_balance_freshness.row_count`, warnings, and the read-only
  human-review safety boundary. UI wording labels the feature as a
  DB-backed freshness read, SELECT-only read, no database write performed,
  stored local/configured database data, and no new EDS/DMI fetch. The
  frontend does not execute SQL, access the database directly, write to the
  database, call live Energi Data Service or DMI/weather APIs, add backend
  endpoints, add migrations, add auth/Azure/ML/LLM behavior, write audit
  events, wire report/PDF flows, or add control, dispatch, activation, or
  operational functionality. This prepares dashboard data trust indicators
  only and does not imply ingestion has run or production monitoring exists.
- Documented observed local DB-backed energy freshness API smoke results for
  `GET /api/energy/freshness/read?price_area=DK1|DK2`. The backend was
  started locally with `DATABASE_URL=postgresql://localhost/flexsignal_ai`;
  the endpoint performed SELECT-only freshness reads, no database writes were
  performed, no live EDS/DMI calls were made, no ingestion was triggered, and
  no frontend changes were involved. Observed DK1: HTTP 200,
  `dry_run=false`, `database_query_executed=true`,
  `database_write_performed=false`, `requires_database_url=true`, spot price
  `row_count=53`, spot price latest timestamp
  `2026-06-11T21:45:00+02:00`, power balance `row_count=53`, power balance
  latest timestamp `2026-06-10T17:00:00+02:00`, and safety boundary
  preserved. Observed DK2: HTTP 200, `dry_run=false`,
  `database_query_executed=true`, `database_write_performed=false`,
  `requires_database_url=true`, spot price `row_count=50`, spot price latest
  timestamp `2026-06-11T21:45:00+02:00`, power balance `row_count=50`, power
  balance latest timestamp `2026-06-10T17:00:00+02:00`, and safety boundary
  preserved. Invalid `price_area=SE3` returned HTTP 400 with
  `Unsupported price_area`. This proves local DB-backed API freshness reads
  work against the observed local data, does not mean production monitoring or
  Azure deployment exists, and prepares manual frontend data trust display
  only. This change is documentation only.
- Documented observed validation for
  `GET /api/energy/freshness/read?price_area=DK1|DK2`, the first controlled
  DB-backed energy freshness read API. The endpoint supports `DK1` and `DK2`,
  returns HTTP 400 for invalid `price_area`, returns safe HTTP 503 when
  `DATABASE_URL` is missing at request time, still exposes the route when the
  app imports without `DATABASE_URL`, and does not return the raw database
  URL. Successful responses include `price_area`, `dry_run=false`,
  `database_query_executed=true`,
  `database_write_performed=false`, `requires_database_url=true`,
  `freshness_result`, `spot_price_freshness`, `power_balance_freshness`,
  warnings, and the read-only human-review safety boundary. The endpoint uses
  `backend/app/db/repositories/energy_freshness_reader.py` for SELECT-only
  freshness reads, does not write to the database, does not fetch new EDS/DMI
  data, does not trigger ingestion, does not modify frontend behavior, and
  does not add control, dispatch, activation, or operational functionality.
  Observed validation: focused API freshness read tests passed with
  `9 passed, 1 warning`; the full backend suite passed with
  `483 passed, 1 warning`; `py_compile` passed; forbidden-pattern grep matched
  only defensive/negative assertions in tests; `git diff --check` passed;
  tests used mocked DB only; and no live DB writes were performed. This
  improves MVP data trust readiness and does not verify production freshness.
  Frontend display remains separate from DB writes, ingestion, and automation.
  This change is documentation only.
- Added `GET /api/energy/freshness/read?price_area=DK1|DK2`, a read-only
  DB-backed energy freshness API endpoint, plus
  `backend/tests/test_api_energy_freshness_read.py`. The endpoint lazily
  requires `DATABASE_URL` at request time, returns a safe HTTP 503 warning if
  it is missing, rejects unsupported price areas with HTTP 400, opens a
  request-scoped database connection only for valid requests, and delegates to
  `backend/app/db/repositories/energy_freshness_reader.py` for SELECT-only
  spot price and power balance freshness reads. Successful responses include
  `dry_run=false`, `database_query_executed=true`,
  `database_write_performed=false`, `requires_database_url=true`,
  `freshness_result`, `spot_price_freshness`, `power_balance_freshness`,
  warnings, and the read-only human-review safety boundary. The endpoint does
  not write to the database, add migrations, modify frontend code, call live
  EDS/DMI APIs, trigger ingestion, add scheduler/Azure/auth behavior, use
  ML/LLMs, write audit events, wire report/PDF flows, or add control,
  dispatch, activation, or operational functionality. It prepares future
  dashboard live data trust indicators only.
- Documented observed manual local energy freshness DB smoke results for
  `scripts/energy_freshness_db_smoke.py`. The smoke used explicit
  `--execute` and a local `--database-url`, performed SELECT-only freshness
  reads, performed no database writes, made no live EDS/DMI calls, and started
  no backend or frontend server. Observed DK1 results:
  `database_query_executed=true`, `database_write_performed=false`, spot
  price `row_count=53`, spot price latest timestamp
  `2026-06-11T21:45:00+02:00`, power balance `row_count=53`, power balance
  latest timestamp `2026-06-10T17:00:00+02:00`, warnings `[]`. Observed DK2
  results: `database_query_executed=true`,
  `database_write_performed=false`, spot price `row_count=50`, spot price
  latest timestamp `2026-06-11T21:45:00+02:00`, power balance
  `row_count=50`, power balance latest timestamp
  `2026-06-10T17:00:00+02:00`, warnings `[]`. This proves local DB-backed
  freshness reads work against the observed local data, does not mean
  production freshness monitoring exists, and prepares future DB-backed
  API/dashboard freshness indicators. This change is documentation only.
- Added `scripts/energy_freshness_db_smoke.py`, a manual local-only smoke
  script for DB-executed energy freshness reads, plus focused unit tests in
  `backend/tests/test_energy_freshness_db_smoke.py`. The script reuses
  `backend/app/db/repositories/energy_freshness.py` for dry-run query-plan
  JSON and `backend/app/db/repositories/energy_freshness_reader.py` for
  explicit DB-executed SELECT reads. It supports `--price-area DK1|DK2`
  defaulting to `DK1`, `--pretty`, `--execute`, and `--database-url`. Dry-run
  is the default and does not connect to a database or execute SQL. Real reads
  require both `--execute` and an explicit local database URL; localhost,
  `127.0.0.1`, and local socket-style URLs are accepted, while obvious
  remote/cloud URLs are refused. Output is JSON with dry-run/execution flags,
  `database_query_executed`, `database_write_performed=false`,
  `requires_database_url`, `local_database_only`, freshness plan or result,
  warnings, and the read-only human-review safety boundary. The raw database
  URL is not printed. This does not add FastAPI endpoints, modify
  `backend/app/main.py`, modify frontend code, call live EDS/DMI APIs, write
  to the database, add migrations, add jobs, add Azure/auth behavior, use
  ML/LLMs, write audit events, wire report/PDF flows, or add control,
  dispatch, activation, or operational functionality.
- Added `backend/app/db/repositories/energy_freshness_reader.py`, a
  backend-only DB-executed read-only freshness reader, plus
  `backend/tests/test_energy_freshness_reader.py`. The reader reuses the
  existing `energy_freshness.py` query-plan builders, defensively validates
  parameterized SELECT-only SQL for `DK1`/`DK2`, requires an explicit
  caller-provided database connection, executes spot price and power balance
  freshness reads through common DB cursor patterns, and returns structured
  dictionaries only with `database_query_executed=true`,
  `database_write_performed=false`, source labels, earliest/latest timestamps,
  row counts, empty-row warnings, and the read-only human-review safety
  boundary. Implemented functions are `read_spot_price_freshness`,
  `read_power_balance_freshness`, and `read_energy_freshness_summary`; the
  combined summary includes `spot_price_freshness`,
  `power_balance_freshness`, `warnings`, and the safety boundary. Query plans
  must be parameterized and start with `SELECT`; unsafe SQL is rejected before
  cursor execution, and blocked mutating tokens include `INSERT`, `UPDATE`,
  `DELETE`, `UPSERT`, `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, and `MERGE`. It
  does not add FastAPI endpoints, modify `backend/app/main.py`, modify
  frontend code, create database connections, read `DATABASE_URL`, call live
  Energi Data Service or DMI/weather APIs, write to the database, add
  migrations, add scheduler/Azure/auth behavior, use ML/LLMs, write audit
  events, wire report/PDF flows, or add control, dispatch, activation, or
  operational functionality. It prepares future DB-backed API/dashboard
  freshness indicators only. Observed validation: focused reader tests passed
  with `24 passed`; the full backend suite passed with `466 passed, 1
  warning`; `py_compile` passed; forbidden-pattern grep matched only
  safety-boundary keys, defensive blocked-token validation, and negative
  assertions/unsafe-plan tests; `git diff --check` passed; tests used fake
  connection/cursor objects only; and no live DB writes were performed.
  Runtime integration remains deferred. A future module may add a controlled
  local DB freshness smoke script, and another future module may add a
  DB-backed read-only API endpoint that executes freshness SELECTs. This
  change is documentation only.
- Documented frontend energy freshness card validation results. The card uses
  the added `fetchEnergyFreshness()` helper to manually call the existing
  `GET /api/energy/freshness?price_area=DK1|DK2` endpoint through the
  existing `NEXT_PUBLIC_API_BASE_URL` pattern and displays dry-run query-plan
  previews only: `price_area`, `dry_run`,
  `database_query_executed`, `database_write_performed`,
  `requires_database_url`, spot price and power balance plan presence/status,
  warnings, and the read-only human-review safety boundary. It is explicitly
  labeled as a freshness query plan preview with no database query executed,
  no database write performed, and no new EDS/DMI fetch.
  The frontend does not call live EDS/DMI APIs, execute SQL, write to a
  database, add backend endpoints, add migrations, add auth/Azure/ML/LLM
  behavior, write audit events, wire report/PDF flows, or add control,
  dispatch, activation, or operational functionality. Updated docs to clarify
  that the card prepares future dashboard trust indicators and does not prove
  live data freshness. Observed validation: `npm run build` passed;
  `git diff --check` passed; the `npm run lint` script did not exist; the
  `npm run typecheck` script did not exist; no backend server was started; no
  frontend dev server was started; no database was accessed; no SQL was
  executed; and no live Energi Data Service or DMI/weather APIs were called.
  DB-backed SELECT execution now exists through the separate
  `GET /api/energy/freshness/read` endpoint. Future frontend wiring to that
  endpoint and future dashboard UI improvements remain separate reviewed
  modules. This change is documentation only.
- Documented observed validation for
  `GET /api/energy/freshness?price_area=DK1|DK2`, a read-only FastAPI energy
  freshness dry-run preview endpoint with focused coverage in
  `backend/tests/test_api_energy_freshness.py`. The endpoint delegates only to
  `backend/app/db/repositories/energy_freshness.py` query-plan builders and
  returns `price_area`, `dry_run=true`, `database_query_executed=false`,
  `database_write_performed=false`, `requires_database_url=false`,
  `freshness_plans`, `spot_price_freshness_plan`,
  `power_balance_freshness_plan`, warnings, and the read-only human-review
  safety boundary. It accepts only `DK1`/`DK2` and returns HTTP 400 for other
  price areas. It does not execute SQL, connect to a database, read
  `DATABASE_URL`, write data, call live EDS/DMI APIs, modify frontend code,
  add migrations, add scheduler/Azure/auth behavior, use ML/LLM logic, write
  audit events, or add control, dispatch, activation, or operational
  functionality. It prepares future dashboard data freshness indicators only.
  Observed validation: focused energy freshness API tests passed with
  `12 passed, 1 warning`; the full backend suite passed with `442 passed, 1
  warning`; `py_compile` passed; forbidden-pattern grep matched only required
  safety flags and negative/safety assertions in tests; `git diff --check`
  passed; and no live DB writes were performed. This change is documentation
  only.
- Added `backend/app/db/repositories/energy_freshness.py`, a read-only EDS
  data freshness read model, plus `backend/tests/test_energy_freshness.py`.
  The helper builds parameterized SELECT query plans for DK1/DK2
  `spot_prices`, `power_balance`, and combined energy freshness summaries
  with params, source labels, earliest/latest timestamp fields, row count
  fields, and empty-result warnings. Invalid `price_area` values outside
  `DK1`/`DK2` are rejected. It does not add FastAPI endpoints, modify
  `backend/app/main.py`, modify frontend code, connect to a database, read
  `DATABASE_URL`, execute SQL, write data, add migrations, call live EDS or
  DMI/weather APIs, add scheduler/Azure/auth behavior, use ML/LLM logic, write
  audit events, or add control, dispatch, activation, or operational
  functionality. This prepares future dashboard/API freshness indicators for
  MVP data trust and debugging only. Observed validation: focused energy
  freshness tests passed with `21 passed`; the full backend suite passed with
  `430 passed, 1 warning`; `py_compile` passed; forbidden-pattern grep
  matched only negative assertions in tests; `git diff --check` passed; and no
  live DB writes were performed. Runtime integration was deferred at that
  stage; the read-only API preview is now documented separately above, and the
  frontend freshness card was added later as a dry-run query-plan preview
  surface only. This change is documentation only.
- Documented read-only audit dry-run preview API validation results in
  `README.md`, `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`, and
  `docs/BACKTEST_RESULTS.md`. Recorded that `POST /api/audit/preview` is a
  reviewed read-only preview endpoint for `current_risk_viewed`,
  `forecast_preview_requested`, `report_summary_built`,
  `report_markdown_rendered`, and `report_pdf_exported`; accepts only
  `DK1`/`DK2`; defaults omitted actor fields to `actor_type=local_user` and
  `actor_id=unknown-local-user`; and returns dry-run audit persistence plans
  with `dry_run=true`, `database_write_performed=false`,
  `requires_database_url=false`, `event`, `persistence_plan`, `event_id`,
  `event_type`, `table=audit_events`, `conflict_behavior`,
  `safety_boundary`, and `warnings`. Documented HTTP 400 validation for
  unsupported event types and price areas outside `DK1`/`DK2`, response
  boundaries excluding raw `DATABASE_URL`, secrets, tokens, full headers, and
  full request bodies, and preservation of the read-only decision-support
  safety boundary. Recorded observed validation: route allowlist updated so
  `/api/audit/preview` is treated as an allowed read-only preview POST;
  focused mutating-route check passed with `1 passed, 1 warning`; focused
  audit preview API tests passed with `16 passed, 1 warning`; full backend
  suite passed with `409 passed, 1 warning`; `py_compile` passed;
  `git diff --check` passed; and no live DB writes were performed. Clarified
  that the endpoint uses `backend/app/audit/runtime_plan.py` dry-run planners
  only and does not execute SQL, write to the database, call the audit writer
  service, create database connections, read `DATABASE_URL`, call external
  APIs, write files, trigger report/PDF generation, modify frontend behavior,
  add automatic audit logging, enable production audit persistence, or connect
  audit persistence to forecast/risk/report/PDF runtime flows. Future runtime
  audit persistence remains deferred and requires explicit review. This
  change is documentation only.
- Added `POST /api/audit/preview`, a read-only FastAPI audit persistence
  dry-run endpoint, plus `backend/tests/test_api_audit_preview.py`. The
  endpoint delegates only to `backend/app/audit/runtime_plan.py` planner
  functions for `current_risk_viewed`, `forecast_preview_requested`,
  `report_summary_built`, `report_markdown_rendered`, and
  `report_pdf_exported`, validates `DK1`/`DK2` price areas, defaults omitted
  API actor fields to `actor_type=local_user` and
  `actor_id=unknown-local-user`, and returns the existing dry-run plan shape
  with `dry_run=true`, `database_write_performed=false`,
  `requires_database_url=false`, `event`, `persistence_plan`, `event_id`,
  `event_type`, `table=audit_events`, `ON CONFLICT (event_id) DO NOTHING`,
  safety-boundary details, and warnings. Added `local_user` to allowed audit
  actor types so the API default is valid. This endpoint does not write to the
  database, call the audit writer service, create database connections, read
  `DATABASE_URL`, execute SQL, add migrations, modify frontend behavior,
  trigger report/PDF generation, add automatic audit logging, wire audit
  persistence into report/PDF/forecast/risk runtime flows, add scheduler,
  Azure, auth, EDS/DMI, ML/LLM, control, dispatch, activation, or operational
  functionality. It is a preview endpoint for future reviewed audit
  integration only.
- Added `backend/app/audit/runtime_plan.py`, a pure backend runtime audit
  persistence dry-run planner, plus
  `backend/tests/test_audit_runtime_plan.py`. The planner delegates to
  `runtime_events.py` factory functions, uses the audit repository INSERT SQL
  builder, and returns dictionaries with `dry_run=true`,
  `database_write_performed=false`, `requires_database_url=false`, the
  `audit-event-v0` event, repository-built `audit_events` persistence plan,
  `event_id`, `event_type`, conflict behavior
  `ON CONFLICT (event_id) DO NOTHING`, safety-boundary details, and warnings.
  It does not write to the database, call the audit writer service, create
  database connections, read `DATABASE_URL`, execute SQL, expose an API,
  modify `backend/app/main.py`, modify routes, modify frontend behavior, add
  migrations, integrate with report/PDF/API/frontend flows, add scheduler,
  Azure, auth, EDS/DMI, ML/LLM, control, dispatch, activation, or operational
  functionality. Runtime integration remains deferred; this prepares a safe
  future API audit dry-run step only. Implemented planner functions are
  `build_current_risk_viewed_audit_plan`,
  `build_forecast_preview_requested_audit_plan`,
  `build_report_summary_built_audit_plan`,
  `build_report_markdown_rendered_audit_plan`, and
  `build_report_pdf_exported_audit_plan`. Each plan includes `dry_run=true`,
  `database_write_performed=false`, `requires_database_url=false`, `event`,
  `persistence_plan`, `event_id`, `event_type`, `table=audit_events`,
  `conflict_behavior`, `safety_boundary`, and `warnings`. The persistence plan
  previews the repository INSERT for `audit_events`; `event_id` is the
  idempotency key and conflict behavior is
  `ON CONFLICT (event_id) DO NOTHING`. SQL and parameters are previewed only,
  and no SQL is executed. Metadata remains safe and minimal: raw
  `DATABASE_URL`, secrets, tokens, full request headers, and full request
  bodies are not included. The full read-only human-review safety boundary is
  preserved. Observed validation: focused planner tests passed with
  `32 passed`; full backend suite passed with `393 passed, 1 warning`;
  `py_compile` passed for `runtime_plan` and tests; forbidden-pattern grep
  matched only safety/negative assertions in tests; `git diff --check`
  passed; tests were pure unit tests only; and no live DB writes were
  performed. Future work may add an API-side audit dry-run endpoint or wrapper
  after review, but automatic audit persistence remains deferred and
  production DB writes require explicit review.
- Documented runtime audit event factory validation results. Recorded that
  `backend/app/audit/runtime_events.py` now provides pure constructors
  `build_current_risk_viewed_event`,
  `build_forecast_preview_requested_event`,
  `build_report_summary_built_event`,
  `build_report_markdown_rendered_event`, and
  `build_report_pdf_exported_event` for standardized `audit-event-v0`
  dictionaries using existing `build_audit_event(...)`, explicit primitive
  inputs, standardized event/action/resource mappings, minimal safe metadata,
  and `runtime_factory_version=audit-runtime-event-factory-v0`. Documented
  mappings for `current_risk_viewed`/`view_current_risk`/`risk_snapshot`,
  `forecast_preview_requested`/`preview_forecast`/`forecast_preview`,
  `report_summary_built`/`build_report_summary`/`report_summary`,
  `report_markdown_rendered`/`render_report_markdown`/`report_markdown`, and
  `report_pdf_exported`/`preview_report_pdf_export`/`report_pdf`; resource ids
  include `price_area` plus `forecast-window-v0` or `report-summary-v0` where
  relevant. Documented metadata boundaries: allowed minimal fields include
  `price_area`, optional `request_id`, optional `source`,
  `forecast_window_version`, `report_version`, `output_format`, optional
  forecast `model_version`, and `runtime_factory_version`; forbidden metadata
  includes raw `DATABASE_URL`, secrets, tokens, raw user claims, full request
  headers, and full request bodies. Documented that every event preserves
  `event_version=audit-event-v0`, `decision_support_only=true`, and the full
  read-only human-review safety boundary. Recorded observed validation:
  focused runtime event tests passed with `30 passed`; the full backend suite
  passed with `361 passed, 1 warning`; `py_compile` passed for
  `runtime_events` and tests; forbidden-pattern grep returned no matches;
  `git diff --check` passed; tests were pure unit tests only; and no live DB
  writes were performed. Clarified that the factory is a backend foundation
  only and does not enable production audit persistence, automatic audit
  logging, audit writer calls, database connections, `DATABASE_URL` handling,
  migrations, FastAPI endpoints, API route changes, frontend behavior,
  report/PDF runtime wiring, scheduler, Azure infrastructure, auth/Entra
  integration, live EDS/DMI calls, ML/LLM behavior, control, dispatch,
  activation, or operational functionality. Future work may add an API audit
  dry-run wrapper/design after review, but automatic audit persistence remains
  deferred and production DB writes require explicit review. This change is
  documentation only.
- Added `backend/app/audit/runtime_events.py`, a pure backend runtime audit
  event factory for standardized `audit-event-v0` dictionaries, plus
  `backend/tests/test_audit_runtime_events.py`. The factory delegates to
  `build_audit_event(...)` and covers current-risk views, forecast-preview
  requests, report-summary builds, report Markdown rendering, and report PDF
  export previews. It uses explicit primitive inputs, safe defaults,
  deterministic timestamp injection when supplied, minimal metadata with
  `runtime_factory_version=audit-runtime-event-factory-v0`, and preserves the
  full read-only human-review safety boundary. It does not add FastAPI
  endpoints, modify routes or frontend code, write to a database, call the
  audit writer service, create database connections, read `DATABASE_URL`, add
  migrations, integrate with report/PDF/API/frontend flows, add scheduler,
  Azure, auth, EDS/DMI, ML/LLM, control, dispatch, activation, or operational
  functionality. Runtime integration remains deferred.
- Documented audit writer service foundation validation results. The writer
  exposes `write_audit_event(conn, event)` plus the
  `execute_audit_event_insert` alias, requires an explicit caller-provided
  database connection object, does not create connections, does not read
  `DATABASE_URL`, uses the existing audit repository insert SQL builder, and
  validates `audit-event-v0`, `decision_support_only=true`, and the full
  read-only human-review safety boundary before executing SQL. Invalid events
  raise `ValueError` and execute no SQL. Valid events return `event_id`,
  `event_type`, `table`, `database_write_performed`, `rowcount`,
  `conflict_behavior`, `safety_boundary_preserved`, and `warnings`.
  Documented observed validation: focused audit writer tests passed with
  `14 passed`; the full backend suite passed with `331 passed, 1 warning`;
  `py_compile` passed for `backend/app/audit/writer.py` and
  `backend/tests/test_audit_writer.py`; grep matched only safety-boundary
  strings and negative/static assertions; `git diff --check` passed; tests
  used fake connection/cursor objects only; and no live DB writes were
  performed. Clarified that the writer is a backend foundation only, does not
  enable production audit persistence, does not add automatic audit logging,
  does not expose API/frontend/report/PDF flows, and remains intentionally
  unwired from runtime flows. No code, backend behavior, frontend behavior,
  database writes, migrations, endpoints, scheduler, Azure infrastructure,
  auth, secrets, EDS/DMI calls, ML/LLM, control, dispatch, activation, or
  operational functionality was added by this documentation change.
- Added `backend/app/audit/writer.py`, an explicit audit writer service
  foundation for `audit-event-v0`, plus `backend/tests/test_audit_writer.py`.
  The writer requires a caller-provided database connection, validates
  `event_version=audit-event-v0`, `decision_support_only=true`, required event
  identity fields, and the full read-only human-review safety boundary before
  executing SQL. It uses the existing audit repository parameterized insert SQL
  builder and returns a structured result with event id, event type, table,
  row count, conflict behavior, write-performed flag,
  safety-boundary-preserved flag, and warnings. It does not create database
  connections, does not read `DATABASE_URL`, does not add FastAPI endpoints,
  and is not wired into API, frontend, report, PDF, scheduler, auth, external
  data, automatic audit logging, control, dispatch, activation, or operational
  flows. Unit tests use fake connection/cursor objects only and perform no live
  database writes.
- Documented the manually executed local audit DB write smoke result for the
  first actual local Postgres `audit_events` write. A human ran
  `DATABASE_URL="postgresql+psycopg://localhost/flexsignal_ai" alembic upgrade head`,
  then ran
  `python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://localhost/flexsignal_ai --verify-read --pretty`
  twice. Alembic used `PostgresqlImpl`, assumed transactional DDL, migrated
  `0001_initial_schema` to `0002_audit_events`, added the audit-event-v0
  persistence foundation, and succeeded. The first smoke reported
  `event_id=audit_evt_f8ea1513efa7fa0067b0ca04`,
  `event_type=report_pdf_exported`, `database_write_performed=true`,
  `dry_run=false`, `execute_requested=true`, `inserted_attempts=2`,
  `local_database_only=true`, `rowcount_first_insert=1`,
  `rowcount_second_insert=0`, `table=audit_events`,
  `verify_read_performed=true`, `warnings=[]`, and
  `conflict_behavior=ON CONFLICT (event_id) DO NOTHING`; `verified_row` was
  returned by `event_id`. The second smoke used the same event id and event
  type, returned `rowcount_first_insert=0` and `rowcount_second_insert=0`,
  and returned `verified_row`, confirming idempotency across repeated script
  executions. Documented that the verified row included
  `event_version=audit-event-v0`, `action=preview_report_pdf_export`,
  `actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
  `decision_support_only=true`, `resource_type=report_pdf`,
  `resource_id=report-summary-v0:DK1:synthetic-pdf`, and metadata
  `local_only=true`, `output_format=pdf`, `price_area=DK1`,
  `report_version=report-summary-v0`, and `synthetic_preview_only=true`.
  Documented the timezone note that the deterministic event read back
  `occurred_at_utc` as `2026-01-01T01:00:00+01:00`, interpreted as
  database/session timezone rendering of the stored `timestamptz` instant and
  not a smoke blocker. Documented that the raw `DATABASE_URL` was not printed
  and the safety boundary preserved read-only decision support, no automatic
  control, no dispatch, no activation, no operational energy-system
  integration, and human review required. Clarified that local audit DB write,
  idempotency, and verify-read are now manually verified, but production audit
  persistence is not enabled, automatic audit logging was not added, and API,
  frontend, report, and PDF flows remain unwired. No code, backend behavior,
  frontend behavior, database writes, migrations, endpoints, scheduler, Azure
  infrastructure, auth, secrets, EDS/DMI calls, ML/LLM, control, dispatch,
  activation, or operational functionality was added by this documentation
  change.
- Added `scripts/audit_db_write_smoke.py`, a manual local-only audit DB write
  smoke script for one deterministic synthetic `audit-event-v0`. The script
  imports `build_audit_event(...)` and the audit repository SQL builder, uses
  fixed `occurred_at_utc=2026-01-01T00:00:00Z`, supports `--pretty`,
  `--event-type`, `--database-url`, `--execute`, and `--verify-read`, and
  defaults to dry-run without connecting to a database. Real writes require
  both `--execute` and an explicit local `--database-url`; localhost,
  127.0.0.1, and local socket-style URLs are accepted, while obvious
  remote/cloud URLs are refused. Executed smoke writes only target
  `audit_events`, run the same parameterized
  `ON CONFLICT (event_id) DO NOTHING` insert twice, commit, and optionally
  verify-read by `event_id`. Added focused unit tests and updated README,
  scripts README, human oversight, model card, and backtest docs. This does
  not add FastAPI endpoints, frontend code, automatic audit logging,
  report/PDF/API/frontend integration, scheduler behavior, Azure
  infrastructure, auth, secrets, EDS/DMI calls, ML, LLMs, control, dispatch,
  activation, or operational functionality.
- Documented observed manual local audit DB write smoke script validation
  results. The documented commands/checks were
  `python3 -m py_compile scripts/audit_db_write_smoke.py backend/tests/test_audit_db_write_smoke.py`,
  `python -m pytest tests/test_audit_db_write_smoke.py -q`,
  `python -m pytest`, `python3 scripts/audit_db_write_smoke.py`,
  `python3 scripts/audit_db_write_smoke.py --pretty`,
  `python3 scripts/audit_db_write_smoke.py --event-type forecast_preview_requested --pretty`,
  `python3 scripts/audit_db_write_smoke.py --execute`,
  `python3 scripts/audit_db_write_smoke.py --execute --database-url postgresql://remote.example.com/flexsignal_ai`,
  forbidden-pattern grep on the script and test, and `git diff --check`.
  Observed results: `py_compile` passed; focused smoke tests passed with
  `7 passed`; the full backend suite passed with `317 passed, 1 warning`;
  default dry-run, `--pretty` dry-run, and
  `forecast_preview_requested` dry-run passed; `--execute` without
  `--database-url` failed safely with exit code `2`; the remote database URL
  command failed safely with exit code `2`; forbidden-pattern grep returned no
  matches; and `git diff --check` passed. Documented that no live DB writes
  were performed during those guardrail checks, the raw `DATABASE_URL` is not
  printed, `event_id` is deterministic, output includes `dry_run`,
  `execute_requested`, `database_write_performed`, `verify_read_performed`,
  `local_database_only`, `event_id`, `event_type`, `table: audit_events`,
  `inserted_attempts`, `conflict_behavior`, `safety_boundary`, and `warnings`,
  and the full read-only/human-review safety boundary is preserved. A later
  documentation-only entry records the first actual manual local Postgres
  write smoke. Production audit persistence is not enabled, no
  API/frontend/report/PDF flow is wired to audit persistence, and no automatic
  audit logging exists. Future production DB writes require explicit review.
  This change is documentation only.
- Added `scripts/audit_persistence_preview.py`, a manual local audit
  persistence dry-run preview. The script imports `build_audit_event(...)` and
  the audit repository SQL builder, uses fixed
  `occurred_at_utc=2026-01-01T00:00:00Z`, supports `--pretty`, supports
  `--event-type` values `forecast_preview_requested`,
  `current_risk_viewed`, `report_summary_built`,
  `report_markdown_rendered`, and `report_pdf_exported`, and defaults to
  `report_pdf_exported`. It prints JSON with `dry_run=true`,
  `database_write_performed=false`, `requires_database_url=false`, the event,
  and a repository-built `audit_events` persistence plan with idempotency key
  and `ON CONFLICT (event_id) DO NOTHING`. Updated README, scripts README,
  human oversight, model card, and backtest docs. This does not persist audit
  events, access a database, require `DATABASE_URL`, run SQL, expose an API,
  use frontend code, write files, generate PDFs, call EDS/DMI, use ML, use
  LLMs, add scheduling, add Azure infrastructure, add auth, add secrets, add
  automatic audit logging, or add control, dispatch, activation, or
  operational functionality.
- Documented observed manual audit persistence dry-run preview validation
  results. The documented commands/checks were
  `python3 -m py_compile scripts/audit_persistence_preview.py`,
  `python3 scripts/audit_persistence_preview.py`,
  `python3 scripts/audit_persistence_preview.py --pretty`,
  `python3 scripts/audit_persistence_preview.py --event-type forecast_preview_requested --pretty`,
  `python3 scripts/audit_persistence_preview.py --event-type report_pdf_exported --pretty`,
  `python3 scripts/audit_persistence_preview.py --event-type invalid-event`,
  forbidden-pattern grep on `scripts/audit_persistence_preview.py`, and
  `git diff --check`. Observed results: `py_compile` passed; the default
  command printed compact JSON; `--pretty` printed indented JSON; both valid
  single-event dry-runs passed; the invalid event type failed safely with exit
  code `2` and argparse invalid-choice output; forbidden-pattern grep returned
  no matches; and `git diff --check` passed. Documented output fields
  `dry_run=true`, `database_write_performed=false`,
  `requires_database_url=false`, `event`, and `persistence_plan`, including
  `event_version=audit-event-v0`, deterministic `audit_evt_...` event id,
  fixed `occurred_at_utc=2026-01-01T00:00:00Z`,
  `actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
  `decision_support_only=true`, safe metadata only,
  `synthetic_preview_only=true`, `local_only=true`, the full read-only
  human-review safety boundary, the `audit_events` target, SQL/SQL preview,
  parameter keys/params, `event_id` idempotency key, and
  `ON CONFLICT (event_id) DO NOTHING`. Clarified that this works locally with
  synthetic/caller-provided data and demonstrates persistence planning only;
  it does not prove live DB persistence, perform database writes, run SQL,
  connect to a database, expose API/frontend/report/PDF flows, generate PDFs,
  call EDS/DMI, use ML/LLMs, add automatic audit logging, or add operational
  functionality. Future controlled local audit persistence write testing must
  be separate and reviewed. This change is documentation only.
- Documented audit DB persistence foundation validation and CI resolution
  results for PR #87. Clarified that `audit-event-v0`, the manual audit-event
  preview script, and preview-result docs already existed before this step,
  and that PR #87 added schema/repository readiness only: Alembic migration
  `backend/alembic/versions/0002_audit_events.py` and
  `backend/app/audit/repository.py`. Documented the `audit_events` schema with
  `event_id` as the primary/idempotency key, event version/type, actor,
  occurrence time, resource, action, outcome, `decision_support_only`, JSONB
  `safety_boundary`, JSONB `metadata`, `created_at_utc`, and indexes for
  occurrence time, event type, resource lookup, and actor lookup. Documented
  repository validation before persistence planning, parameterized INSERT SQL,
  and `ON CONFLICT (event_id) DO NOTHING`, with no live database writes during
  validation.
- Documented initial PR validation for the audit DB persistence foundation:
  backend tests passed with `310 passed, 1 warning`, `py_compile` passed for
  `backend/app/audit/events.py` and `backend/app/audit/repository.py`,
  safety-boundary grep matched only `no_automatic_control`, `no_dispatch`, and
  `no_activation`, and `git diff --check` passed.
- Documented the GitHub backend-tests issue and resolution before merge. The
  initial CI failures were
  `tests/test_api_energy.py::test_app_exposes_no_mutating_write_methods` and
  `tests/test_api_risk.py::test_app_import_without_database_url_still_exposes_current_risk_route`;
  CI/import context was missing exposed routes `/api/risk/current`,
  `/api/risk/preview`, and `/api/forecast/preview`. The issue was interpreted
  as route exposure under newer FastAPI/Starlette test behavior, not live
  database writes or audit persistence execution. `backend/app/main.py` was
  updated with a small route-registration helper so `app.routes` exposes
  concrete paths in the test environment while keeping `DATABASE_URL`
  validation request-time only. Endpoint logic was not changed. No new API
  behavior, DB writes, scheduler, frontend, control, dispatch, activation, or
  operational behavior was added. The branch was not merged while
  backend-tests were red.
- Documented post-fix validation: focused route tests passed with
  `2 passed, 1 warning`, the full backend suite passed with
  `310 passed, 1 warning`, `git diff --check` passed, the PR diff was checked
  to exclude `.pyc`, virtualenv, cache, and generated files, GitHub
  backend-tests were re-run and green before merge, and PR #87 was merged only
  after backend-tests were green. Documented the final merged files:
  `backend/alembic/versions/0002_audit_events.py`,
  `backend/app/audit/repository.py`, `backend/app/main.py`,
  `backend/tests/test_audit_event_repository.py`, `README.md`,
  `docs/HUMAN_OVERSIGHT.md`, `docs/MODEL_CARD.md`,
  `docs/BACKTEST_RESULTS.md`, and `CHANGELOG.md`. Clarified that the audit DB
  persistence foundation does not prove production audit persistence, identify
  real users through Entra ID, or automatically write events. Future work may
  add a fake-executor/local-dry-run persistence preview, but automatic audit
  logging and frontend/report-download persistence wiring remain deferred
  until explicit review. This change is documentation only.
- Added audit-event database persistence foundation for `audit-event-v0`.
  New Alembic migration `0002_audit_events.py` defines an `audit_events`
  table with `event_id` as the primary/idempotency key, event version/type,
  actor, occurrence time, resource, action, outcome,
  `decision_support_only`, JSONB `safety_boundary`, JSONB `metadata`,
  `created_at_utc`, and indexes for occurrence time, event type, resource, and
  actor. New `backend/app/audit/repository.py` validates
  `build_audit_event(...)` dictionaries, preserves the required read-only
  safety boundary, serializes JSONB fields as parameters, and builds
  parameterized `ON CONFLICT (event_id) DO NOTHING` insert SQL. Added focused
  repository/migration tests and updated README, human oversight, model card,
  and backtest docs. This does not add FastAPI endpoints, frontend UI,
  automatic audit logging, report/PDF persistence wiring, scheduled logging,
  auth/Entra integration, Azure infrastructure, secrets, ML/LLM behavior,
  live API calls, live database writes, or control, dispatch, activation, or
  operational functionality. Future work can wire explicit read-only flows to
  audit persistence only after review.
- Documented observed manual audit-event preview validation results. The
  documented checks were
  `python3 -m py_compile scripts/audit_event_preview.py`,
  `python3 scripts/audit_event_preview.py`,
  `python3 scripts/audit_event_preview.py --pretty`,
  `python3 scripts/audit_event_preview.py --event-type report_pdf_exported --pretty`,
  `python3 scripts/audit_event_preview.py --event-type forecast_preview_requested --pretty`,
  `python3 scripts/audit_event_preview.py --event-type invalid-event`,
  forbidden-pattern grep on `scripts/audit_event_preview.py`, and
  `git diff --check`. Observed results: `py_compile` passed; the default
  command printed compact JSON with an `events` array; `--pretty` printed
  indented JSON; the two valid single-event commands each printed one event;
  the invalid event type failed safely with exit code `2` and a clear argparse
  invalid-choice validation error; forbidden-pattern grep returned no matches;
  and `git diff --check` passed. Documented that preview events covered
  `forecast_preview_requested`, `current_risk_viewed`,
  `report_summary_built`, `report_markdown_rendered`, and
  `report_pdf_exported`; included `event_version=audit-event-v0`,
  deterministic `audit_evt_...` ids, fixed
  `occurred_at_utc=2026-01-01T00:00:00Z`,
  `actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`,
  `decision_support_only=true`, safe metadata only,
  `synthetic_preview_only=true`, `local_only=true`, and the full
  read-only/human-review `safety_boundary`. Clarified that audit preview works
  locally with synthetic/caller-provided data and demonstrates future
  read-only decision-support audit-event shape, but does not persist events,
  prove database audit logging, connect auth or actor identity providers,
  create operational logs, or provide production audit persistence. Audit
  persistence can be considered next only as a separate reviewed module, with
  no automatic control, dispatch, activation, scheduler, or operational
  functionality. This change is documentation only.
- Added `scripts/audit_event_preview.py`, a manual synthetic local JSON
  preview for `audit-event-v0`. The script imports `build_audit_event(...)`
  from `backend/app/audit/events.py`, uses fixed
  `occurred_at_utc=2026-01-01T00:00:00Z`, supports compact JSON by default
  plus `--pretty`, supports `--event-type` values
  `forecast_preview_requested`, `current_risk_viewed`,
  `report_summary_built`, `report_markdown_rendered`,
  `report_pdf_exported`, and `all`, defaults to `all`, and uses
  `actor_type=local_developer`, `actor_id=local-dev`, `outcome=success`, and
  `decision_support_only=true`. The `all` mode prints an `events` array; a
  single event type prints one `event` object. Metadata is synthetic and safe
  only, including `price_area`, relevant `report_version`, relevant
  `output_format`, `synthetic_preview_only`, and `local_only`. Updated
  `scripts/README.md`, `README.md`, `docs/HUMAN_OVERSIGHT.md`,
  `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md` with usage examples,
  safety boundaries, and deferred persistence guidance. This does not persist
  audit logs yet, write files, access a database, run SQL, expose an API, use
  frontend code, call EDS or DMI/weather APIs, use ML, use LLMs, add a
  scheduler, add Azure infrastructure, add auth or secrets, or perform
  automatic control, dispatch, activation, closed-loop workflows, live control
  signals, autonomous decisions, or operational energy-system integration.
  Future audit work should document audit preview results first; database
  persistence remains a separate reviewed module.
- Added `audit-event-v0`, a pure backend Python in-memory audit event
  foundation for read-only decision-support actions. New
  `backend/app/audit/events.py` exposes `build_audit_event(...)`, validates
  explicit event types, actor types, outcomes, timezone-aware
  `occurred_at_utc`, non-empty resource/action fields, safe JSON-compatible
  metadata, and secret-like metadata keys, and returns deterministic
  `audit_evt_...` ids with an explicit safety boundary. Added focused tests and
  docs. This does not persist audit logs yet, write files, expose an API, read
  or write a database, call EDS or DMI/weather APIs, use ML, use LLMs, add
  scheduling, add Azure infrastructure, add auth or secrets, or perform
  automatic control, dispatch, activation, closed-loop workflows, live control
  signals, autonomous decisions, or operational energy-system integration.
  Manual/local audit preview is documented separately; database persistence
  should follow later only in a separate reviewed module.
- Documented observed manual/local PDF export v0 smoke-test results. The
  validation covered `standard`, `high-risk`, `missing-current-risk`, and
  `missing-forecast` synthetic/caller-provided scenarios through the
  `report-summary-v0` to Markdown to PDF path. Observed temporary outputs were
  `/tmp/flexsignal_report_preview.pdf` at `9697` bytes,
  `/tmp/flexsignal_report_high_risk.pdf` at `9930` bytes,
  `/tmp/flexsignal_report_missing_current.pdf` at `9263` bytes, and
  `/tmp/flexsignal_report_missing_forecast.pdf` at `6918` bytes. All started
  with `%PDF`, were larger than `1000` bytes, were removed after validation,
  and were not committed. Documented that backend tests passed with
  `257 passed, 1 warning`, `py_compile` passed, `git diff --check` passed,
  manual PDF preview runs passed, PDF byte/header checks passed, repository PDF
  checks passed, and grep found only required safety wording and no forbidden
  integration imports. Clarified that PDF export v0 remains manual/local
  read-only decision support only: no API endpoint, no frontend download, no
  live data, no database read/write, no EDS or DMI/weather API calls, no
  scheduler, no ML or LLM use, no automatic report jobs, and no automatic
  control, dispatch, activation, autonomous decisions, or operational
  energy-system integration. This change is documentation only.
- Added manual local PDF export v0 for `report-summary-v0`. New
  `backend/app/reporting/pdf.py` exposes
  `render_report_markdown_pdf_bytes(...)`, which accepts caller-provided
  Markdown and returns PDF bytes without writing files, fetching data, reading
  or writing a database, exposing an API, using frontend code, using ML, using
  LLMs, or adding operational behavior. New
  `scripts/report_pdf_preview.py` builds synthetic/caller-provided
  `report-summary-v0` data, renders Markdown, renders PDF bytes, requires
  explicit `--output PATH`, refuses overwrite without `--force`, and prints a
  compact JSON summary. Added focused PDF renderer and script tests, added
  `reportlab` to backend dependencies, exported the renderer from
  `app.reporting`, and updated README, scripts README, model card, and
  backtest notes. This remains manual/local read-only decision support only
  and must not be used for automatic control, dispatch, or activation.
- Added `scripts/report_markdown_preview.py`, a manual synthetic local
  Markdown preview for `report-summary-v0`. The script imports
  `build_report_summary(...)` from `backend/app/reporting/summary.py`, imports
  `render_report_summary_markdown(...)` from
  `backend/app/reporting/markdown.py`, uses fixed
  `generated_at_utc=2026-01-01T00:00:00Z`, supports
  `--price-area DK1|DK2`, and includes `standard`, `high-risk`,
  `missing-current-risk`, and `missing-forecast` scenarios over in-script
  synthetic/caller-provided sample data only. It prints Markdown to stdout,
  writes no files, generates no PDF files, fetches no data, accesses no
  database, runs no SQL, exposes no API, uses no frontend code, uses no ML or
  LLMs, and adds no scheduler, Azure, auth, secrets, control, dispatch,
  activation, or operational functionality. Updated `scripts/README.md`,
  `README.md`, `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md` with usage
  examples, safety boundaries, and observed local synthetic preview results.
- Documented observed local results from the manual synthetic
  `scripts/report_markdown_preview.py` commands only:
  `python3 scripts/report_markdown_preview.py`,
  `python3 scripts/report_markdown_preview.py --price-area DK2 --scenario high-risk`,
  `python3 scripts/report_markdown_preview.py --scenario missing-current-risk`,
  and
  `python3 scripts/report_markdown_preview.py --scenario missing-forecast`.
  All four runs printed the synthetic-only warning to stderr, rendered
  Markdown to stdout only, used
  `generated_at_utc=2026-01-01T00:00:00Z`,
  `report_version=report-summary-v0`, `decision_support_only=true`, and
  `human_review_required=true`, and included title, report metadata,
  current-risk summary, forecast-window summary, key findings, recommended
  human actions, safety notes, limitations, and source notes. The standard DK1
  run rendered available medium current risk with score `45` and three
  forecast windows. The high-risk DK2 run rendered available high current risk
  with score `75`, a high-risk `24-48h` forecast window with
  `max_risk_score=80`, human-review actions, and safety notes prohibiting
  automatic control, dispatch, and activation. The missing-current-risk run
  rendered current risk as unavailable, kept the forecast summary available,
  included `missing or incomplete current risk input`, and did not crash. The
  missing-forecast run rendered the forecast window summary as unavailable,
  kept current risk available, included `missing or incomplete forecast input`,
  and did not crash. Clarified that the Markdown preview works locally with
  synthetic/caller-provided data, renders `report-summary-v0` to readable
  Markdown, does not write files, does not generate PDF files, does not fetch
  data, does not read or write a database, does not expose an API, does not
  use frontend code, does not use ML or LLMs, remains read-only decision
  support only, and must not be used for automatic control, dispatch, or
  activation. Documented the next step as PDF export v0 using the stable
  report-summary and Markdown rendering path while remaining manual, local,
  and read-only first. This change is documentation only.
- Added `render_report_summary_markdown(...)`, a pure backend Python Markdown
  renderer for caller-provided `report-summary-v0` dictionaries. It returns a
  deterministic Markdown string with title, report metadata, current-risk
  summary, forecast-window summary, key findings, recommended human actions,
  safety notes, limitations, and source notes. Missing current-risk or forecast
  summaries render as clear unavailable sections, and optional missing fields
  use safe fallback text. Added tests covering title and metadata rendering,
  current-risk fields, all three forecast windows, high-risk window output,
  missing-summary handling, required safety wording, deterministic output, no
  file writing, and absence of external runtime or document-generation
  imports. Updated README, model card, and backtest notes to document that the
  renderer does not generate PDF files, write files, fetch data, access a
  database, expose an API, use frontend code, use ML, use LLMs, or add
  automatic control, dispatch, activation, or operational functionality.
- Documented observed local results from the manual synthetic
  `scripts/report_summary_preview.py` commands only:
  `python3 scripts/report_summary_preview.py --pretty`,
  `python3 scripts/report_summary_preview.py --price-area DK2 --scenario high-risk --pretty`,
  `python3 scripts/report_summary_preview.py --scenario missing-current-risk --pretty`,
  and
  `python3 scripts/report_summary_preview.py --scenario missing-forecast --pretty`.
  All runs printed the synthetic-only warning and reported
  `generated_at_utc=2026-01-01T00:00:00Z`,
  `report_version=report-summary-v0`, `decision_support_only=true`, and
  `human_review_required=true`. The standard DK1 run returned available
  medium current risk with score `45`, three forecast windows, no high-risk
  forecast window, and recommended actions requiring human review and
  prohibiting automatic control, dispatch, or activation. The high-risk DK2
  run returned available high current risk with score `75`, a high-risk
  `24-48h` forecast window with `max_risk_score=80`, high-risk key findings,
  and human-review escalation actions. The missing-current-risk run marked
  `current_risk_summary.status=unavailable`, added the limitation
  `missing or incomplete current risk input`, and kept the forecast summary
  available. The missing-forecast run marked
  `forecast_window_summary.status=unavailable`, added the limitation
  `missing or incomplete forecast input`, and kept the current-risk summary
  available. Clarified that the preview creates deterministic report payloads
  from synthetic/caller-provided data only; it does not generate PDF files,
  fetch data, read or write a database, expose an API, use frontend code, use
  ML, use LLMs, or perform automatic control, dispatch, activation, or
  operational functionality. Documented the next step as Markdown report
  rendering before later PDF export. This change is documentation only.
- Added `scripts/report_summary_preview.py`, a manual synthetic local JSON
  preview for `report-summary-v0`. The script imports
  `build_report_summary(...)` directly from `backend/app/reporting/summary.py`,
  uses fixed `generated_at_utc=2026-01-01T00:00:00Z`, supports compact JSON by
  default plus `--pretty`, supports `--price-area DK1|DK2`, and includes
  `standard`, `high-risk`, `missing-current-risk`, and `missing-forecast`
  scenarios over in-script caller-provided sample data only. The high-risk
  scenario demonstrates high-risk key findings and recommended human actions;
  the missing-input scenarios keep generation safe by marking the relevant
  summary unavailable. Documented usage in `scripts/README.md`, `README.md`,
  `docs/MODEL_CARD.md`, and `docs/BACKTEST_RESULTS.md`. This script does not
  generate PDF files, fetch data, access a database, run SQL, expose an API,
  run frontend code, call Energi Data Service, call DMI/weather APIs, add a
  scheduler, use Azure, add auth or secrets, train ML models, use LLMs, or add
  automatic control, dispatch, activation, or operational functionality.
- Added `report-summary-v0`, a pure backend Python deterministic
  data-structure builder for read-only decision-support reporting. It accepts
  caller-provided current-risk output and caller-provided `forecast-window-v0`
  output only, validates `DK1`/`DK2` and timezone-aware `generated_at_utc`,
  returns a deterministic report id based on price area, generated timestamp,
  and report version, and includes current-risk summary, forecast-window
  summary, model versions, key findings, deduplicated recommended human
  actions, safety notes, limitations, and source notes. Missing or incomplete
  current-risk or forecast input is handled as an unavailable summary with an
  explicit limitation instead of crashing. Added focused tests for valid
  reports, deterministic IDs, validation, unavailable summaries, high and
  unknown forecast findings, action deduplication, decision-support flags,
  safety notes, object inputs, and absence of DB/API/network/PDF dependencies.
  Updated README, model card, and backtest notes to document that this is a
  data structure only: it does not generate PDF files yet, fetch data, read or
  write a database, expose an API, use ML, use LLMs, add scheduler/auth/Azure
  behavior, or perform automatic control, dispatch, activation, or operational
  functionality. The next reporting step should be a Markdown/preview script,
  followed later by PDF rendering.
- Documented manual frontend Forecast preview card smoke-test results after
  the local CORS preflight fix was merged. The backend was started without
  `DATABASE_URL`, the frontend was started locally, and only the Forecast
  preview card was used; spot prices, power balance, and current surplus risk
  cards were not used. The card was visible with the read-only badge and
  synthetic/caller-provided preview warning, showed no forecast data before
  the manual "Load forecast preview" click, then displayed
  `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, `generated_at_utc=2026-01-01T00:00:00Z`, and
  `0-24h`, `24-48h`, and `48-72h` windows. DK1 returned `0-24h` low risk with
  `row_count=1`, `max_risk_score=30`, `average_risk_score=30`, and reason
  codes including `EXCHANGE_NET_NOT_USED_V0`, `MODERATE_PRICE`, and
  `MODERATE_RENEWABLE_SHARE`; `24-48h` high risk with `row_count=1`,
  `max_risk_score=75`, `average_risk_score=75`, reason codes including
  `EXCHANGE_NET_NOT_USED_V0`, `HIGH_RENEWABLE_SHARE`, and `NEGATIVE_PRICE`,
  and a recommended human action requiring human review; and `48-72h` low risk
  with `row_count=1`, `max_risk_score=10`, `average_risk_score=10`, and reason
  codes including `ELEVATED_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0`, and
  `NORMAL_PRICE`. Switching the selected price area to DK2 and clicking the
  manual button returned forecast-window data again with the same three
  windows and decision-support-only fields without frontend error, confirming
  that the selected price area can be used by the frontend helper for this
  flow. Clarified that the prior browser failure was caused by `OPTIONS`
  preflight returning `400`, and the successful frontend load from
  `POST /api/forecast/preview` practically confirms the local CORS preflight
  path for the Forecast preview card. This is local smoke-test documentation
  only: no ingestion, database access, SQL, database writes, live Energi Data
  Service calls, DMI/weather calls, scheduler, Azure infrastructure, auth,
  secrets, ML training, LLM use, automatic control, dispatch, activation, or
  operational functionality was run or added; it remains synthetic/caller-
  provided preview data only, read-only decision support for human review, and
  not production forecast validation.
- Added a manual read-only frontend "Forecast preview" dashboard card. The
  card uses the selected `DK1`/`DK2` price area, calls
  `POST /api/forecast/preview` only after the user clicks "Load forecast
  preview", posts deterministic synthetic/caller-provided demo rows with
  timezone-aware `generated_at_utc`, and displays the returned `0-24h`,
  `24-48h`, and `48-72h` windows with risk level, row count, max and average
  risk scores, top reason codes, recommended human action,
  `decision_support_only`, and `model_version`. The frontend helper uses only
  the backend API base URL helper. It does not auto-load, poll, call Energi
  Data Service or DMI/weather APIs from the browser, read or write a database,
  add backend endpoints, run SQL, schedule jobs, add Azure infrastructure,
  add auth or secrets, train ML, use LLMs, or add automatic control, dispatch,
  activation, closed-loop, or operational functionality. This remains
  synthetic/caller-provided preview data only, read-only decision support, and
  not production forecast validation.
- Documented manual smoke-test results for `POST /api/forecast/preview` only.
  The backend was started without `DATABASE_URL`, confirming that
  caller-provided forecast rows can be summarized without database access. The
  valid DK1 request returned HTTP 200 with `price_area=DK1`,
  `generated_at_utc=2026-01-01T00:00:00Z`,
  `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, and three windows: `0-24h` with
  `row_count=1`, `risk_level=low`, `max_risk_score=30`,
  `average_risk_score=30.0`, and reason codes including `MODERATE_PRICE` and
  `MODERATE_RENEWABLE_SHARE`; `24-48h` with `row_count=1`,
  `risk_level=high`, `max_risk_score=75`, `average_risk_score=75.0`, and
  reason codes including `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`; and
  `48-72h` with `row_count=0`, `risk_level=unknown`,
  `max_risk_score=null`, `average_risk_score=null`, and
  `average_confidence_score=0.0`. The high-risk DK2 request returned HTTP 200,
  `price_area=DK2`, `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, and a `24-48h` high-risk window with
  `row_count=1`, `max_risk_score=75`, `average_risk_score=75.0`, and reason
  codes including `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`; the `0-24h` and
  `48-72h` windows were `unknown` because `row_count=0`. Invalid
  `price_area=SE3` and timezone-naive `generated_at_utc` requests returned
  validation errors indicating that input should be `DK1` or `DK2` and that
  `generated_at_utc` must be timezone-aware. Clarified that this demonstrates
  deterministic caller-provided `0-24h`, `24-48h`, and `48-72h` window
  summaries, max-risk aggregation, empty-window `unknown` handling, and input
  validation only. No frontend was used; no ingestion, database access, SQL,
  database writes, live Energi Data Service calls, DMI/weather calls,
  scheduler, Azure infrastructure, auth, secrets, ML training, LLM use,
  automatic control, dispatch, activation, or operational functionality was
  used or added. This is read-only decision support, not production forecast
  validation.
- Added `POST /api/forecast/preview`, a read-only FastAPI wrapper around
  `forecast-window-v0` for caller-provided DK1/DK2 rows only. The endpoint
  returns deterministic `0-24h`, `24-48h`, and `48-72h` summaries from
  `build_forecast_window_forecast(...)`, validates supported price areas and
  timezone-aware request timestamps, allows empty caller-provided row lists to
  return three `unknown` windows, and preserves decision-support-only safety
  wording. Added API tests for valid previews, empty rows, invalid price areas,
  timezone-naive timestamps, absence of DB/API/network/job behavior, existing
  risk endpoint compatibility, and safety wording. Documented that the endpoint
  does not fetch EDS or DMI/weather data, read or write a database, persist
  payloads, start jobs, train ML, use LLMs, add frontend code, add auth, add
  Azure infrastructure, or perform automatic control, dispatch, activation, or
  operational workflows.
- Documented observed results from the synthetic local
  `scripts/forecast_window_preview.py` commands only:
  `python3 scripts/forecast_window_preview.py --pretty`,
  `python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty`,
  and
  `python3 scripts/forecast_window_preview.py --scenario empty-window --pretty`.
  All runs printed the synthetic-only warning and reported
  `generated_at_utc=2026-01-01T00:00:00Z`,
  `model_version=rule-engine-v0+forecast-window-v0`, and
  `decision_support_only=true`. The balanced DK1 run returned the three
  expected `0-24h`, `24-48h`, and `48-72h` windows with row counts `2/2/2`,
  risk levels `medium/low/medium`, and max risk scores `45/30/35`. The DK2
  high-risk run showed `24-48h` as `high` risk with `max_risk_score=75` and
  reason codes including `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`,
  demonstrating max-risk aggregation. The empty-window run showed DK1
  `24-48h` with `row_count=0`, `risk_level=unknown`,
  `average_risk_score=null`, `max_risk_score=null`, and no top reason codes,
  demonstrating insufficient caller-provided data handling. Clarified that
  this is synthetic/caller-provided local preview only, deterministic
  aggregation only, not ML, not DMI/weather based yet, not production forecast
  validation, and that no database access, SQL, live Energi Data Service
  polling, DMI/weather calls, backend/frontend servers, scheduler, Azure
  resources, secrets, auth, ML training, LLM use, automatic control, dispatch,
  activation, or operational functionality was added or used by this
  documentation update.
- Added a manual synthetic local `scripts/forecast_window_preview.py` for
  `forecast-window-v0`, with fixed `generated_at_utc`, DK1/DK2 selection,
  `balanced`, `high-risk`, and `empty-window` scenarios, compact or pretty JSON
  output, direct use of `build_forecast_window_forecast(...)`, and explicit
  synthetic-only safety warnings. Documented usage in the scripts README,
  README, model card, and backtest notes. This does not require `DATABASE_URL`,
  connect to a database, execute SQL, fetch live Energi Data Service data, call
  DMI/weather APIs, add FastAPI endpoints, modify backend startup, add frontend
  code, create ingestion jobs, use Azure, add secrets, add auth, train ML
  models, use LLMs, control, dispatch, activation, or operational
  functionality.
- Added `forecast-window-v0`, a pure backend Python deterministic aggregation
  layer for caller-provided DK1/DK2 surplus-risk rows. It returns three
  non-overlapping windows (`0-24h`, `24-48h`, `48-72h`), ignores rows before
  `generated_at_utc`, at or beyond +72h, or for another valid price area,
  rejects invalid DK areas and timezone-naive timestamps, reuses
  `calculate_surplus_risk` from `rule-engine-v0`, bases each non-empty window
  risk level on the maximum observed risk score, and includes deterministic
  averages, risk counts, top reason codes, human-review actions, and
  decision-support-only safety wording. Added forecast-window tests covering
  window assignment, ignored rows, empty windows, max-risk aggregation,
  deterministic reason-code ordering, timestamp validation, absence of DB/API
  and network dependencies in the forecast module, and required safety output.
  Updated README, model card, and backtest notes to document that this is not
  ML, not DMI/weather based yet, does not fetch data, does not write data, does
  not expose an API yet, is not production forecast validation, and must not be
  used for automatic control, dispatch, or activation. No FastAPI endpoint,
  frontend behavior, database access, SQL, live Energi Data Service calls,
  DMI/weather ingestion, scheduler, Azure infrastructure, secrets, auth, ML
  training, LLM use, control, dispatch, activation, or operational
  functionality was added.
- Added a concise MVP readiness summary across the README, local database
  runbook, model card, and backtest notes. Documented that FlexSignal AI is
  ready for a local technical MVP demo, not production ready, not a validated
  commercial forecasting product, and remains read-only decision support for
  human review only. Summarized the latest validated local dataset status
  (`spot_prices` DK1=53/DK2=50 and `power_balance` DK1=53/DK2=50), local DB
  backtest status (DK1 53 composed rows with low/medium/high 1/52/0 and
  average risk score `34.5283`; DK2 50 composed rows with low/medium/high
  42/8/0 and average risk score `21.8`), and read-only API/UI smoke-test
  status (DK1 current risk medium score 35, DK2 current risk low score 20,
  manual frontend loads for DK1/DK2 spot prices, power balance, and current
  risk, visible read-only badge/disclaimer, and no automatic loading, polling,
  control, dispatch, or activation observed). Clarified remaining gaps: no
  24-72 hour forecast, DMI/weather ingestion, full historical backtest, outcome
  labels, model performance metrics, Azure deployment, Microsoft Entra ID auth,
  audit-log implementation beyond documentation, PDF/report export, production
  database, scheduled ingestion, monitoring setup, or human approval workflow
  in product UI. Recommended the next MVP step as a simple deterministic
  24-72 hour forecast foundation using available local EDS data first, with no
  LLM forecast engine and no control, dispatch, or activation behavior. This
  change is documentation only; no code, backend behavior, frontend behavior,
  tests, servers, database writes, live API polling, scheduled jobs, Azure
  infrastructure, auth, secrets, ML training, LLM use, or operational
  functionality was added.
- Documented the read-only current-risk API and frontend smoke-test after the
  manual `limit 50` EDS confirmed local write had populated local PostgreSQL.
  API observations used
  `curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK1"` and
  `curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK2"`; DK1
  returned HTTP 200 with `timestamp_utc=2026-06-10T17:00:00+02:00`,
  `risk_level=medium`, `risk_score=35`, `confidence_score=1.0`, reason codes
  `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`,
  `model_version=rule-engine-v0`, `decision_support_only=true`, and source
  metadata showing `spot_prices` and `power_balance` rows found; DK2 returned
  HTTP 200 with the same timestamp, `risk_level=low`, `risk_score=20`,
  `confidence_score=1.0`, reason codes `NORMAL_PRICE`,
  `MODERATE_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`,
  `model_version=rule-engine-v0`, `decision_support_only=true`, and source
  metadata showing `spot_prices` and `power_balance` rows found. Frontend
  smoke-test observations at `http://localhost:3000` showed manual DK1 and DK2
  spot-price loads returning 5 `spot_prices` rows, manual DK1 and DK2
  power-balance loads returning 5 `power_balance` rows, manual current-risk
  loads matching the DK1 medium score 35 and DK2 low score 20 API results, and
  the read-only badge visible for both areas. Clarified that the dashboard
  still requires manual button clicks, no automatic loading or polling was
  observed, the current-risk endpoint still reads from local PostgreSQL and
  returns decision-support-only results, and this is local MVP smoke-test
  documentation only, not production validation. No code, backend behavior,
  frontend behavior, ingestion, database writes by this change, live Energi
  Data Service polling, tests, servers, scheduled jobs, Azure infrastructure,
  secrets, auth, ML training, LLM use, control, dispatch, activation, or
  operational functionality was added.
- Documented the manual EDS historical batch wrapper `limit 50` confirmed
  local write, repeated-run idempotency check, and DK1/DK2 local DB backtest
  results only. The confirmed command was
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --confirm-local-db-write --continue-on-error`;
  before the write, counts were `spot_prices` DK1=13 and DK2=10, and
  `power_balance` DK1=13 and DK2=12; the wrapper reported
  `child_exit_codes=[0, 0, 0, 0]`, 4 planned commands, 4 succeeded commands, 0
  failed commands, `confirmed_local_write=true`, `dry_run=false`, `limit=50`,
  `local_only=true`, `decision_support_only=true`, price areas `DK1`/`DK2`,
  and datasets `DayAheadPrices` and `ElectricityProdex5MinRealtime`; child
  confirmed writes all returned HTTP 200 with 50 raw records, 50 normalized
  records, 50 SQL commands, target tables `spot_prices` or `power_balance`,
  and `committed=true`; after the write, counts were `spot_prices` DK1=53 and
  DK2=50, and `power_balance` DK1=53 and DK2=50. Documented the repeated
  confirmed command idempotency check: the second run again reported
  `child_exit_codes=[0, 0, 0, 0]`, 4 planned commands, 4 succeeded commands, 0
  failed commands, `confirmed_local_write=true`, `dry_run=false`, `limit=50`,
  and `local_only=true`; counts remained unchanged, so no duplicate explosion
  was observed and the repeated import was idempotent for the same 50-record
  batch. Documented read-only local DB backtests after the batch: DK1 with 53
  spot-price rows read, 53 power-balance rows read, 53 composed and evaluated
  rows, 0 failed rows, low/medium/high counts of 1/52/0, average risk score
  `34.5283`, average confidence `1.0`, reason-code counts including
  `NORMAL_PRICE: 53`, `HIGH_RENEWABLE_SHARE: 52`,
  `EXCHANGE_NET_NOT_USED_V0: 53`, and `ELEVATED_RENEWABLE_SHARE: 1`; DK2 with
  50 spot-price rows read, 50 power-balance rows read, 50 composed and
  evaluated rows, 0 failed rows, low/medium/high counts of 42/8/0, average risk
  score `21.8`, average confidence `1.0`, reason-code counts including
  `NORMAL_PRICE: 50`, `MODERATE_RENEWABLE_SHARE: 39`,
  `HIGH_RENEWABLE_SHARE: 8`, `ELEVATED_RENEWABLE_SHARE: 3`, and
  `EXCHANGE_NET_NOT_USED_V0: 50`. Clarified that DK1 remained mostly medium
  risk on the expanded local sample, DK2 now includes both low and medium risk,
  and this is stronger technical validation than the 10-row sample but still
  not full model validation because the dataset is still small and has no
  outcome labels. No code, backend behavior, frontend behavior, database writes
  by this change, live API polling, scheduled jobs, Azure infrastructure,
  secrets, auth, ML training, LLM use, control, dispatch, activation, or
  operational functionality was added.
- Documented the manual EDS historical batch wrapper `limit 50` dry-run result
  only. The command was
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --continue-on-error`;
  wrapper output was `dry_run=true`, `confirmed_local_write=false`,
  `local_only=true`, `decision_support_only=true`, `limit=50`, price areas
  `DK1`/`DK2`, datasets `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`, 4 planned commands, 4 succeeded commands, 0
  failed commands, and child exit codes `[0, 0, 0, 0]`. Child dry-runs for
  `DayAheadPrices` DK1/DK2 and `ElectricityProdex5MinRealtime` DK1/DK2 all
  returned HTTP 200 with 50 raw records, 50 normalized records, 50 SQL
  commands, target tables `spot_prices` or `power_balance`, and
  `committed=false`. Clarified that limit 50 dry-run is validated for all
  supported DK1/DK2 dataset combinations, no database writes were committed,
  this validates command orchestration and normalization path only, confirmed
  writes still require explicit `--confirm-local-db-write`, and `100`/`500`
  still require future explicit enhancement. No code, backend behavior,
  frontend behavior, database writes, live API polling, scheduled jobs, Azure
  infrastructure, secrets, auth, ML training, LLM use, control, dispatch,
  activation, or operational functionality was added.
- Raised the explicit manual local Energi Data Service ingest safety cap from
  `limit 10` to `limit 50` in `scripts/manual_eds_local_db_ingest.py` and the
  `scripts/manual_eds_historical_batch_import.py` wrapper while preserving the
  conservative defaults (`2` for the child script, `10` for the wrapper),
  dry-run default, local `DATABASE_URL` safety gate, supported datasets,
  supported price areas, and required `--confirm-local-db-write` gate for
  writes. Added parser and wrapper orchestration tests for `limit 50`
  acceptance, `0`/`51` rejection, dry-run defaults, explicit confirmation
  passthrough, and non-local database URL rejection. Updated scripts and
  validation docs, the local database runbook, and backtest notes to state that
  `limit 50` is supported for manual local validation while `100` and `500`
  still require a future explicit enhancement. No scheduler, Azure
  infrastructure, backend startup ingestion, FastAPI endpoint, frontend code,
  production database support, secrets, auth, ML training, LLM use, control,
  dispatch, activation, closed-loop, or operational functionality was added.
- Documented the manual EDS historical batch confirmed local write,
  idempotency check, and DK1/DK2 local DB backtest results only. The confirmed
  command was
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 10 --confirm-local-db-write --continue-on-error`;
  before the write, counts were `spot_prices` DK1=3 and DK2=2, and
  `power_balance` DK1=3 and DK2=2; the wrapper reported
  `child_exit_codes=[0, 0, 0, 0]`, 4 planned commands, 4 succeeded commands, 0
  failed commands, `confirmed_local_write=true`, `dry_run=false`, `limit=10`,
  `local_only=true`, `decision_support_only=true`, price areas `DK1`/`DK2`,
  and datasets `DayAheadPrices` and `ElectricityProdex5MinRealtime`; child
  confirmed writes all returned HTTP 200 with 10 raw records, 10 normalized
  records, 10 SQL commands, target tables `spot_prices` or `power_balance`,
  and `committed=true`; after the write, counts were `spot_prices` DK1=13 and
  DK2=10, and `power_balance` DK1=13 and DK2=12. Documented the repeated
  confirmed command idempotency check: the second run again reported
  `child_exit_codes=[0, 0, 0, 0]`, 4 planned commands, 4 succeeded commands, 0
  failed commands, `confirmed_local_write=true`, `dry_run=false`, `limit=10`,
  and `local_only=true`; counts remained unchanged, so no duplicate explosion
  was observed. Documented read-only local DB backtests after the batch: DK1
  with 13 spot-price rows read, 13 power-balance rows read, 13 composed and
  evaluated rows, 0 failed rows, low/medium/high counts of 1/12/0, average
  risk score `33.0769`, average confidence `1.0`, reason-code counts including
  `NORMAL_PRICE: 13`, `HIGH_RENEWABLE_SHARE: 12`,
  `EXCHANGE_NET_NOT_USED_V0: 13`, and `ELEVATED_RENEWABLE_SHARE: 1`; DK2 with
  10 spot-price rows read, 12 power-balance rows read, 12 composed and
  evaluated rows, 0 failed rows, low/medium/high counts of 12/0/0, average
  risk score `20.0`, average confidence `1.0`, reason-code counts including
  `NORMAL_PRICE: 12`, `MODERATE_RENEWABLE_SHARE: 12`, and
  `EXCHANGE_NET_NOT_USED_V0: 12`. Clarified that DK1 shifted to mostly medium
  risk on the expanded local sample, DK2 remained low risk, and this is still
  technical validation only with a small dataset and no outcome labels. No
  code, backend behavior, frontend behavior, database writes by this change,
  live API polling, Azure infrastructure, secrets, auth, ML training, LLM use,
  control, dispatch, activation, or operational functionality was added.
- Documented the manual EDS historical batch wrapper dry-run result only:
  command
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 10 --continue-on-error`;
  wrapper output `dry_run=true`, `confirmed_local_write=false`,
  `local_only=true`, `decision_support_only=true`, `limit=10`, price areas
  `DK1`/`DK2`, datasets `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`, 4 planned commands, 4 succeeded commands, 0
  failed commands, and child exit codes `[0, 0, 0, 0]`; and child dry-run
  observations for all four dataset/price-area combinations showing HTTP 200,
  10 raw records, 10 normalized records, 10 SQL commands, target tables
  `spot_prices` or `power_balance`, and `committed=false`. Clarified that this
  validates command orchestration and normalization path only, did not write to
  the database, still requires explicit `--confirm-local-db-write` for
  confirmed writes, and used the wrapper default `limit 10`. No code, backend
  behavior, frontend behavior, database writes,
  live API polling, Azure infrastructure, secrets, auth, ML training, LLM use,
  control, dispatch, activation, or operational functionality was added.
- Added `scripts/manual_eds_historical_batch_import.py`, a manual local-only
  batch wrapper around `scripts/manual_eds_local_db_ingest.py` for explicit
  DK1/DK2 and `DayAheadPrices`/`ElectricityProdex5MinRealtime` validation
  batches. The wrapper requires a local DB-API `DATABASE_URL`, refuses
  non-local hosts, defaults to dry-run, passes `--confirm-local-db-write` to
  child commands only when explicitly received, prints the child command plan,
  stops on first child failure unless `--continue-on-error` is passed, defaults
  to `limit 10`, rejects limits above `50`, and emits a compact JSON summary.
  Updated scripts and validation docs, the local database runbook, and backtest
  notes to clarify that larger `100`/`500` staged imports require a future
  explicit enhancement and that the wrapper must not bypass the current child
  safety gate. No scheduler, Azure infrastructure, backend
  startup ingestion, FastAPI endpoint, frontend code, production database
  support, secrets, auth, ML training, LLM use, control, dispatch, activation,
  closed-loop, or operational functionality was added.
- Added a documentation-only historical local Energi Data Service import plan
  for expanding local DK1/DK2 samples of `DayAheadPrices` and
  `ElectricityProdex5MinRealtime` to support better read-only local backtesting.
  Documented the staged batch progression of `limit 50`, then `100`, then
  maximum `500` per dataset and price area, with `100` and `500` still
  requiring a future explicit enhancement plus row counts, distinct
  `source_record_id` counts, idempotency, and backtest outputs are checked.
  Documented required safety gates: local PostgreSQL only, `DATABASE_URL`
  targeting `localhost` or `127.0.0.1`, dry-run before confirmed write,
  explicit `--confirm-local-db-write` for confirmed writes, no production or
  Azure database, no scheduled jobs, no backend startup ingestion, no
  frontend-triggered ingestion, and no automatic polling loop. Documented
  post-batch validation expectations for row counts by `price_area`, distinct
  source IDs, repeated-import idempotency, DK1/DK2 local DB read-only backtests,
  `risk_level_counts`, and `average_risk_score`; stop conditions for duplicate
  explosion, non-local DB URLs, unconfirmed writes, failed normalization,
  unexpected field mapping, and any control/dispatch/activation behavior; and
  limitations that larger local samples are still not full model validation
  because outcome labels, DMI/weather data, and a 24-72 hour forecast are
  absent while `rule-engine-v0` remains deterministic and simple. No code,
  backend behavior, frontend behavior, database writes, live API polling, Azure
  infrastructure, secrets, auth, ML training, LLM use, control, dispatch,
  activation, or operational functionality was added.
- Added a concise MVP status documentation update covering the current
  read-only technical foundation: local PostgreSQL schema and Alembic baseline,
  manual local EDS ingestion for `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`, validated tiny DK1/DK2 local samples,
  read-only `spot_prices` and `power_balance` API paths, manual frontend loads
  for spot prices, power balance, and current risk, `rule-engine-v0`,
  `GET /api/risk/current` for DK1/DK2, synthetic and local DB read-only
  backtest previews, and `nearest_timestamp_v0_1` backtest row pairing.
  Documented validated local results only: DK1 has 3 spot-price rows, 3
  power-balance rows, current risk `medium` with score `35`, local DB backtest
  counts low/medium/high of 1/2/0, and average risk score `26.6667`; DK2 has 2
  spot-price rows, 2 power-balance rows, current risk `low` with score `20`,
  local DB backtest counts low/medium/high of 2/0/0, and average risk score
  `20.0`. Clarified that this remains preview/non-production work with a tiny
  dataset, no full historical backtest, no outcome labels, no 24-72 hour
  forecast, no DMI/weather ingestion, no production report export, no auth, no
  Azure deployment, no scheduled ingestion jobs, no production database, no
  human approval workflow beyond documentation/disclaimers, no automatic
  control, no dispatch, no activation, no operational energy system
  integration, no LLM as decision engine, and no autonomous decisions.
- Documented DK2 local Energi Data Service validation results only:
  `DayAheadPrices` DK2 and `ElectricityProdex5MinRealtime` DK2 both returned
  HTTP 200 in dry-run mode with 2 raw records, 2 normalized records, 2 SQL
  commands, and `committed=false`; both datasets were then manually confirmed
  with `committed=true` against local PostgreSQL only. Documented local row
  counts after ingest as `spot_prices` DK1=3 and DK2=2, and `power_balance`
  DK1=3 and DK2=2. This documentation preserves the local/manual boundary with
  no production database, Azure resources, startup migrations, automated
  ingestion job, live polling loop, ML training, LLM use, or automatic control,
  dispatch, activation, or operational functionality.
- Documented DK2 current-risk and local read-only DB backtest validation only:
  `GET /api/risk/current?price_area=DK2` returned HTTP 200 with
  `risk_level=low`, `risk_score=20`, `confidence_score=1.0`, reason codes
  including `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`, `model_version=rule-engine-v0`,
  `decision_support_only=true`, and source metadata showing `spot_prices` and
  `power_balance` rows found. Documented the command
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python
  scripts/risk_backtest_local_db.py --price-area DK2 --limit 10 --pretty` and
  observed read-only output with `pairing_strategy=nearest_timestamp_v0_1`, 2
  spot-price rows read, 2 power-balance rows read, 2 composed/evaluated rows, 0
  failed rows, low/medium/high risk counts of 2/0/0, average risk score `20.0`,
  average confidence score `1.0`, reason-code counts for `NORMAL_PRICE`,
  `MODERATE_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`, no missing price
  or generation data, and `model_version=rule-engine-v0`. Documented that this
  is technical validation on a tiny local sample, not full model validation or
  evidence for performance conclusions, with local PostgreSQL, manual
  validation, SELECT/read-only backtest behavior, no production database, no
  Azure resources, no startup migrations, no automated ingestion job, no live
  polling loop, no ML training, no LLM use, and no automatic control, dispatch,
  activation, or operational functionality.
- Added pure read-only nearest-timestamp risk backtest row pairing with
  `pair_rows_by_nearest_timestamp(...)`, deterministic DK1/DK2 validation,
  timezone-aware ISO timestamp parsing including trailing `Z`, power-balance
  rows as the primary timeline, deterministic tie-breaking by earlier
  spot-price timestamp then original order, unit tests, and local DB backtest
  metadata `pairing_strategy=nearest_timestamp_v0_1`. Updated the manual local
  DB backtest script and docs while preserving SELECT/read-only behavior only,
  no database writes, no live EDS polling, no API endpoint or startup changes,
  no frontend work, no ingestion jobs, no Azure resources, no secrets, no auth,
  no ML training, no LLM use, and no automatic control, dispatch, activation,
  or operational functionality.
- Documented the local read-only DB risk backtest rerun after
  `nearest_timestamp_v0_1` pairing was merged only: pre-backtest local table
  counts of 3 `spot_prices` rows and 3 `power_balance` rows, command
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python
  scripts/risk_backtest_local_db.py --price-area DK1 --limit 10 --pretty`,
  observed DK1 output with `read_only=true`, `decision_support_only=true`, 3
  `pairing_strategy=nearest_timestamp_v0_1`, 3 spot-price rows read, 3
  power-balance rows read, 3 composed rows, 3 total and evaluated rows, 0
  failed rows, low/medium/high risk counts of 1/2/0, average risk score
  `26.6667`, average confidence score `1.0`, reason-code counts for
  `NORMAL_PRICE`, `EXCHANGE_NET_NOT_USED_V0`, `HIGH_RENEWABLE_SHARE`, and
  `ELEVATED_RENEWABLE_SHARE`, 0 missing price rows, 0 missing generation-data
  rows, and `model_version=rule-engine-v0`. Documented that nearest-timestamp
  pairing is active, the tiny local DK1 risk distribution remained unchanged
  compared with the previous simple pairing run, the 3-row local sample is
  technical validation only, and a larger historical dataset is required before
  drawing performance conclusions. Confirmed documentation-only scope with
  local PostgreSQL SELECT/read-only behavior only, no database writes, no live
  EDS polling, no backend or frontend server, no startup migrations, no
  production database, no Azure resources, no ML training, no LLM use, and no
  automatic control, dispatch, activation, or operational functionality.
- Added a manual local PostgreSQL read-only `scripts/risk_backtest_local_db.py`
  backtest preview for `rule-engine-v0`, using existing SELECT query builders,
  local-only `postgresql://...` `DATABASE_URL` validation, DK1/DK2 filtering,
  latest-first list-order row pairing through `compose_surplus_risk_input`,
  compact or pretty JSON output, and documentation of the technical-validation
  limitation. This performs no database writes, live Energi Data Service
  fetches, API endpoint or startup changes, frontend work, ingestion jobs,
  Azure infrastructure, secrets, auth, ML training, LLM use, control, dispatch,
  activation, or operational functionality.
- Added a manual synthetic local `scripts/risk_backtest_preview.py` for the
  existing `rule-engine-v0` backtest evaluator, with hardcoded low-, medium-,
  high-like, missing-data, and invalid sample rows, compact or pretty JSON
  output, documentation, and explicit synthetic-only warnings. This does not
  require `DATABASE_URL`, connect to a database, execute SQL, fetch live Energi
  Data Service data, add API endpoints, modify backend startup, add frontend or
  ingestion code, use Azure, add secrets, train ML models, use LLMs, control,
  dispatch, activation, or operational functionality.
- Added pure Python `evaluate_risk_backtest` aggregation for local
  `rule-engine-v0` row dictionaries, including evaluated and failed row counts,
  low/medium/high counts, average risk and confidence scores, reason-code
  aggregation, missing price and generation-data counts, row-level error
  capture, unit tests, and documentation. This is synthetic/local
  decision-support evaluation only, with no database connections, SQL
  execution, API endpoints, FastAPI startup changes, frontend code, ingestion
  jobs, Azure infrastructure, secrets, ML training, LLM use, control, dispatch,
  activation, or operational functionality.
- Documented manual local frontend current-risk smoke-test results only:
  backend startup with `DATABASE_URL="postgresql://localhost/flexsignal_ai"
  python -m uvicorn app.main:app --reload`, frontend startup with
  `cd frontend`, `npm install`, and `npm run dev`, browser validation at
  `http://localhost:3000`, DK1 selection, manual Load spot prices, Load power
  balance, and Load current risk actions, 3 displayed spot price rows, 3
  displayed power balance rows, current surplus risk `risk_level=medium`,
  `risk_score=35`, `confidence_score=1`, `reason_codes` including
  `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`,
  `model_version=rule-engine-v0`, `decision_support_only=true`,
  `metadata.source_tables_used` showing `spot_prices` and `power_balance`,
  `metadata.spot_price_row_found=true`,
  `metadata.power_balance_row_found=true`, and no Failed to fetch error.
  Confirmed the frontend used only the backend API helper, with no direct
  Energi Data Service frontend call, polling or automatic refresh, database
  writes, live EDS polling, startup migrations, Azure resources, production
  database, LLM or ML model use, automatic control, dispatch, activation, or
  operational functionality.
- Added manual read-only frontend display for the existing current surplus risk
  API, including a third dashboard card, DK1/DK2-aware manual
  `GET /api/risk/current` fetch through the backend API base helper, loading
  and backend-unavailable error states, typed response fields for risk level,
  score, confidence, reason codes, explanation, recommended human action,
  model version, decision-support flag, and source metadata. No page-load fetch,
  polling, automatic refresh, direct Energi Data Service frontend call, backend
  code, database write, auth, Azure infrastructure, charts, forecasting/model
  logic, control, dispatch, activation, or operational functionality was added.
- Documented manual local current risk API smoke-test results for `GET
  /api/risk/current?price_area=DK1`: backend startup with
  `DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn
  app.main:app --reload`, observed `risk_level=medium`, `risk_score=35`,
  `confidence_score=1.0`, `reason_codes` including `NORMAL_PRICE`,
  `HIGH_RENEWABLE_SHARE`, and `EXCHANGE_NET_NOT_USED_V0`,
  `model_version=rule-engine-v0`, `decision_support_only=true`,
  `metadata.source_tables_used` including `spot_prices` and `power_balance`,
  and both `metadata.spot_price_row_found` and
  `metadata.power_balance_row_found` as `true`. Documented invalid
  `price_area=SE3` validation behavior and confirmed only DK1 and DK2 are
  accepted, with local PostgreSQL reads only through the existing read-only
  query path, no database writes, no live Energi Data Service polling, no
  startup migrations, no Azure resources, no production database, no LLM or ML
  model, and no automatic control, dispatch, activation, or operational
  functionality.
- Added read-only `GET /api/risk/current?price_area=DK1|DK2` surplus-risk API
  endpoint that lazily requires `DATABASE_URL` only when called, reads the
  latest existing local `spot_prices` and `power_balance` rows through existing
  SELECT-only query paths, composes input with `compose_surplus_risk_input`,
  scores with `rule-engine-v0`, returns source-table metadata, and includes
  mocked tests for DK1/DK2 validation, missing `DATABASE_URL`, empty rows,
  SELECT-only SQL, no live HTTP calls, unchanged preview behavior, and no
  control, dispatch, activation, ingestion, frontend, Azure, auth, ML, LLM, or
  database-write behavior.
- Added pure Python `compose_surplus_risk_input` mapping for existing
  `spot_prices` and `power_balance` row dictionaries into `rule-engine-v0`
  input, with DK1/DK2 and timestamp validation, focused unit tests, model-card
  documentation, no database connection, no SQL execution, no API/frontend/
  ingestion/Azure changes, no ML/LLM logic, and no control, dispatch,
  activation, or operational behavior.
- Documented manual local risk preview API smoke-test results for `POST
  /api/risk/preview`: backend startup with
  `python -m uvicorn app.main:app --reload`, valid caller-provided DK1 JSON
  payload at `2026-06-09T21:45:00+02:00` with negative price and high renewable
  share inputs, observed `risk_level=high`, `risk_score=75`,
  `confidence_score=1.0`, `reason_codes` including `NEGATIVE_PRICE` and
  `HIGH_RENEWABLE_SHARE`, `model_version=rule-engine-v0`, and
  `decision_support_only=true`. Documented invalid `price_area=SE3` validation
  behavior and confirmed only DK1 and DK2 are accepted, with caller-provided
  JSON only, no database connection, no database writes, no live Energi Data
  Service polling, no LLM or ML model, and no automatic control, dispatch,
  activation, or operational functionality.
- Added read-only `POST /api/risk/preview` FastAPI endpoint that validates
  caller-provided DK1/DK2 JSON payloads with Pydantic and delegates only to the
  existing pure `rule-engine-v0` surplus-risk scorer, returning the exact model
  output shape with `decision_support_only=true`, mocked API tests, no database
  dependency, no SQL execution, no live HTTP calls, no ingestion, no frontend,
  no Azure infrastructure, no LLM use, and no control, dispatch, activation, or
  operational behavior.
- Added deterministic pure Python `rule-engine-v0` surplus-risk scoring for
  DK1/DK2 read-only decision support, with validation, reason codes,
  confidence scoring, exchange-flow sign ambiguity documented as unused in v0,
  focused unit tests, and no database, API, frontend, ingestion, ML training,
  LLM, dispatch, activation, or control functionality.
- Documented manual local frontend-to-backend read-only smoke-test results:
  backend startup with `DATABASE_URL="postgresql://localhost/flexsignal_ai"
  python -m uvicorn app.main:app --reload`, frontend startup with
  `cd frontend`, `npm install`, and `npm run dev`, browser validation at
  `http://localhost:3000`, DK1 selection, manual Load spot prices and Load power
  balance actions, 3 displayed DK1 rows for both spot prices and power balance,
  no Failed to fetch error, HTTP 200 backend logs for both read-only API calls,
  and confirmed local-development CORS behavior. Confirmed the frontend only
  used the backend API helper, with no direct Energi Data Service frontend
  calls, polling, database writes, live EDS polling, startup migrations, Azure
  resources, production database, forecasting/model logic, control, dispatch,
  activation, or operational functionality.
- Added local-development-only CORS middleware for the read-only FastAPI API,
  allowing `http://localhost:3000` and `http://127.0.0.1:3000` with `GET` and
  `OPTIONS` only, no wildcard origins, no credentials, no startup migrations,
  no database writes, no live API polling, and no new write endpoints.
- Added manual read-only frontend integration for the existing backend energy
  API endpoints, including typed `limit=5` spot price and power balance fetch
  helpers, DK1/DK2 selection, manual load buttons, loading and backend
  unavailable error states, row counts, compact result tables, and visible copy
  confirming the browser uses only the backend API base URL helper and does not
  call Energi Data Service directly. No automatic page-load fetches, polling,
  charts, auth, Azure infrastructure, secrets, database writes,
  forecasting/model logic, dispatch, activation, control, backend code, or
  operational functionality were added.
- Documented manual local frontend dashboard shell smoke-test results: local
  startup via `npm install`, `npm run build`, and `npm run dev`; successful
  `next build` with TypeScript passing and static `/` route generation; browser
  validation at `http://127.0.0.1:3000` showing the FlexSignal AI title,
  read-only/no-automatic-control badge, DK1/DK2 selector, spot prices and power
  balance cards, placeholder/loading-ready/error-ready sections, backend API
  base URL helper `http://127.0.0.1:8000`, and no error screen. Confirmed the
  shell made no backend API requests, direct Energi Data Service calls, polling,
  database writes, auth, Azure resources, forecasting/model logic, control,
  dispatch, activation, or operational functionality, and noted the
  development-only `127.0.0.1` cross-origin warning with `localhost:3000` as
  the local development URL unless `allowedDevOrigins` is configured later.
- Added a minimal Next.js + TypeScript frontend dashboard shell with
  FlexSignal AI branding, the read-only/no-automatic-control scope badge, DK1
  and DK2 selector state, placeholder/loading/error-ready cards for spot prices
  and power balance, and a configurable future backend API base URL helper with
  no frontend data fetches, polling, forecasting, dispatch, activation, control,
  auth, database code, payments, Azure infrastructure, or backend ingestion
  changes.
- Documented manual local read-only FastAPI smoke-test results for `GET
  /health`, `GET /api/energy/spot-prices?price_area=DK1&limit=5`, and `GET
  /api/energy/power-balance?price_area=DK1&limit=5`, using local PostgreSQL
  only, with no database writes, live EDS polling, startup migrations, ingestion
  jobs, Azure resources, production database, forecasting, control, dispatch,
  activation, or operational functionality.
- Added read-only FastAPI energy endpoints for recent local `spot_prices` and
  `power_balance` rows, using existing SELECT query builders, lazy local-only
  `DATABASE_URL` validation, DK1/DK2 filtering, default limit `100`, hard
  maximum `1000`, mocked tests without PostgreSQL, and no writes, live EDS
  fetches, ingestion jobs, startup migrations, frontend, forecasting, control,
  dispatch, activation, or operational functionality.
- Added a manual local PostgreSQL read-preview script for existing
  `spot_prices` and `power_balance` tables using the existing read-only query
  builders, required local DB-API `DATABASE_URL`, local-host validation,
  DK1/DK2 filtering, default limit `10`, hard maximum `100`, compact JSON-line
  row output, and no writes, live EDS fetches, ingestion jobs, FastAPI imports,
  endpoints, forecasting, control, dispatch, activation, or operational
  functionality.
- Added pure read-only parameterized SELECT query builders for recent and
  time-window `spot_prices` and `power_balance` reads by DK1/DK2 `price_area`,
  with default limit `100`, hard maximum `1000`, no database connection, no SQL
  execution, no FastAPI endpoint, no ingestion job, and no operational control
  functionality.
- Documented confirmed manual live Energi Data Service to local PostgreSQL write
  validation results for `DayAheadPrices` DK1 to `spot_prices` and
  `ElectricityProdex5MinRealtime` DK1 to `power_balance`, both with `--limit 2`,
  explicit `--confirm-local-db-write`, local PostgreSQL only, and no Azure,
  production, startup, scheduled ingestion, automatic write, API endpoint,
  forecasting, control, dispatch, activation, or operational functionality.
- Added a manual local-only EDS-to-PostgreSQL ingest validation script for tiny
  live `DayAheadPrices` and `ElectricityProdex5MinRealtime` DK1/DK2 samples,
  with dry-run default, required local DB-API `DATABASE_URL`, local-host
  validation, limit maximum `10`, generated SQL preview counts, and explicit
  `--confirm-local-db-write` gating for local writes only.
- Documented manual local PostgreSQL migration and smoke-test validation
  results, including PostgreSQL 16.14 local readiness, Alembic upgrade to
  `0001_initial_schema`, verified tables, dry-run output, confirmed local write
  counts, idempotent upsert behavior, and the separate Alembic SQLAlchemy URL
  and smoke-test DB-API URL formats.
- Added psycopg v3 as a backend dev dependency for local/manual PostgreSQL
  Alembic and smoke-test validation, with docs using the explicit
  `postgresql+psycopg://localhost/flexsignal_ai` SQLAlchemy URL and preserving
  the no-startup-migrations/no-startup-writes boundary.
- Added an explicit manual local PostgreSQL smoke-test script for hardcoded DK1
  sample records through the existing write-plan, SQL builder, and transaction
  boundaries, guarded by `DATABASE_URL`, local-host validation, dry-run default,
  and `--confirm-local-db-write` for real local writes.
- Documented the future manual local PostgreSQL validation runbook, including
  local-only migration usage, explicit shell-only `DATABASE_URL`, safety
  boundaries, and the acceptance checklist required before real DB write code.
- Added a mocked database transaction boundary for generated SQL command
  dictionaries with caller-injected fake connections, pre-execution validation,
  commit-after-success, rollback-on-execute-failure, and no `DATABASE_URL`,
  database driver, PostgreSQL, startup, or ingestion side effects.
- Added a dry-run Energi Data Service persistence orchestration helper that
  chains normalized records through write-plan and SQL preview generation, with
  optional fake executor handoff and no database, HTTP, startup, or runtime
  ingestion side effects.
- Added a narrow Energi Data Service database write executor boundary that uses
  a caller-provided cursor, validates the full batch before execution, and does
  not create connections, commit transactions, schedule ingestion, or modify
  runtime startup.
- Added a pure parameterized SQL builder for Energi Data Service write-plan
  preview entries targeting `spot_prices` and `power_balance`, without database
  connections, execution, writes, ingestion jobs, or runtime startup changes.
- Documented manual read-only Energi Data Service write-plan preview validation
  for `DayAheadPrices` and `ElectricityProdex5MinRealtime` DK1/DK2 records,
  including the expected null `consumption_mw` value for the selected realtime
  production dataset.
- Added a manual read-only Energi Data Service write-plan preview script for
  `DayAheadPrices` and `ElectricityProdex5MinRealtime` DK1/DK2 records without
  database connections, SQL generation, or writes.
- Added a pure dry-run Energi Data Service database write-plan builder for
  `spot_prices` and `power_balance` preview entries without SQL generation or
  database writes.
- Added pure Energi Data Service record-to-database payload repository helpers
  for `spot_prices` and `power_balance` with mocked/unit tests and no database
  writes.
- Fixed backend package discovery so Alembic migrations are not installed as an application package.
- Added a controlled Energi Data Service dry-run ingestion module with mocked
  unit tests and no database writes.
- Added an Alembic initial migration baseline for the documented database schema.
- Initial project structure.
- Initial documentation baseline.
- Read-only decision-support scope defined.
- No frontend, database runtime, or infrastructure implementation yet.
