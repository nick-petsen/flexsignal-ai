# Changelog

## v0.1.0 - TODO

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
