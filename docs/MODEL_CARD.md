# Model Card: rule-engine-v0

## Overview

`rule-engine-v0` is a deterministic, rule-based surplus-risk scorer for DK1 and
DK2 electricity areas. It is not a machine-learning model and does not use LLM
reasoning. The implementation is pure Python decision-support logic.

## Intended Use

The model estimates low, medium, or high surplus electricity production risk for
human review. It is read-only decision support for `v0.1`; it must not be used
as an autonomous decision-maker or critical operational system.

`POST /api/risk/preview` wraps `rule-engine-v0` for caller-provided JSON data
only. The preview API does not fetch live data, read from a database, write to a
database, or connect to assets or operational systems in this step.

`POST /api/forecast/preview` wraps `forecast-window-v0` for caller-provided
DK1/DK2 rows only. It returns deterministic `0-24h`, `24-48h`, and `48-72h`
window summaries and does not fetch EDS or DMI/weather data, read or write a
database, start jobs, use ML, use LLMs, or perform operational actions.

`GET /api/risk/current?price_area=DK1|DK2` wraps the same rule engine for the
latest existing local database rows. It lazily requires `DATABASE_URL` only when
the endpoint is called, reads the most recent `spot_prices` and `power_balance`
rows for the requested price area through existing read-only query paths,
returns source-table metadata, and does not write to the database, fetch live
Energi Data Service data, schedule ingestion, or connect to operational
systems.

## Current MVP Status

`rule-engine-v0` is the current read-only scoring baseline for the technical
MVP foundation. It is simple, deterministic, testable, and explainable. It is
not a trained forecasting model, not an LLM decision engine, and not validated
for production operations.

Working read-only paths around the model:

- `POST /api/risk/preview` scores caller-provided DK1/DK2 JSON.
- `POST /api/forecast/preview` summarizes caller-provided DK1/DK2 rows into
  three forecast windows.
- `GET /api/risk/current` scores the latest existing local DK1/DK2 rows.
- The frontend can manually request current risk through the backend API.
- Synthetic and local DB read-only backtest previews exist.
- Local DB backtest row pairing uses `nearest_timestamp_v0_1`.

Validated local sample results:

| Area | Current risk API smoke-test | Local DB rows | Local DB backtest | Average risk score |
| --- | --- | --- | --- | ---: |
| DK1 | medium, score 35 | 53 spot prices, 53 power-balance rows | low=1, medium=52, high=0 | 34.5283 |
| DK2 | low, score 20 | 50 spot prices, 50 power-balance rows | low=42, medium=8, high=0 | 21.8 |

The latest local validation confirms that the read-only API, frontend manual
loads, local DB backtest, and deterministic scoring path work for DK1 and DK2
after the `limit 50` local import. It supports a local technical MVP demo only.
It does not establish predictive accuracy, statistical calibration, commercial
validity, production readiness, or operational fitness.

## Inputs

- `price_area`: `DK1` or `DK2`
- `timestamp_utc`: required string
- `price_dkk_per_mwh`: optional spot price
- `production_mw`: optional total production
- `consumption_mw`: optional consumption context
- `wind_onshore_mw`, `wind_offshore_mw`, `solar_mw`: optional renewable
  production fields
- `exchange_net_mw`: optional exchange context

## Method

The score starts at `0` and is capped at `100`.

- Negative prices add high risk.
- Low positive prices add medium risk.
- Moderately low prices add low risk.
- Higher renewable share, calculated from wind and solar over total production,
  increases risk.
- Missing price, production, or renewable fields reduce confidence.

Risk levels are:

- `low`: 0-34
- `medium`: 35-69
- `high`: 70-100

Confidence starts at `1.0`, is reduced for missing key data, has a floor of
`0.2`, and is rounded to two decimals.

## Risk Input Composer

`compose_surplus_risk_input` is a deterministic mapper from existing
`spot_prices` and `power_balance` row dictionaries into the `rule-engine-v0`
input shape. It does not score risk by itself, connect to a database, execute
SQL, call live APIs, perform ML or LLM logic, or perform control, dispatch, or
activation.

## Backtest Evaluator

`evaluate_risk_backtest` is a pure Python local evaluator for
`rule-engine-v0` outputs. It passes each supplied row dictionary to
`calculate_surplus_risk`, aggregates risk-level counts, average scores,
confidence, reason codes, missing-data counts, and row-level validation errors.

The evaluator is not ML training, threshold tuning, forecasting, or autonomous
decision-making. It does not connect to a database, execute SQL, call live APIs,
poll services, ingest data, use LLMs, or perform control, dispatch, activation,
or operational workflows.

## Forecast Window Aggregation

`forecast-window-v0` is a pure Python deterministic aggregation layer over
caller-provided surplus-risk input rows. It groups matching DK1/DK2 rows into
three non-overlapping windows: `0-24h`, `24-48h`, and `48-72h`, then reuses
`calculate_surplus_risk` from `rule-engine-v0` for row-level scoring.

The window risk level is based on the maximum observed row risk score in the
window, not the average alone. Empty windows return `unknown` with no risk
score and an explanation that there is not enough caller-provided data.

`forecast-window-v0` is not a machine-learning model, not DMI/weather based
yet, not production forecast validation, and not an LLM forecast engine. The
`POST /api/forecast/preview` API exposes this aggregation for caller-provided
rows only. It does not fetch data, write data, call live Energi Data Service,
call DMI/weather APIs, connect to a database, schedule jobs, train models, or
use secrets, auth, Azure infrastructure, or operational integrations.

All outputs are read-only decision support only and must not be used for
automatic control, dispatch, activation, closed-loop workflows, asset
connections, plant/device commands, or live control signals.

`scripts/forecast_window_preview.py` is a manual synthetic local preview for
`forecast-window-v0`. It uses fixed `generated_at_utc` output and only
in-script caller-provided rows for `balanced`, `high-risk`, and `empty-window`
scenarios. It calls `build_forecast_window_forecast(...)` and prints compact
JSON by default or indented JSON with `--pretty`.

The preview script does not require `DATABASE_URL`, read or write a database,
run SQL, fetch Energi Data Service data, call DMI/weather APIs, expose a FastAPI
endpoint, run frontend code, create a scheduler, use Azure, add secrets, add
auth, train ML models, use LLMs, or perform control, dispatch, activation, or
operational functionality.

### Forecast Window Preview Results

The synthetic preview script was run with:

```bash
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

All observed outputs used `generated_at_utc=2026-01-01T00:00:00Z`,
`model_version=rule-engine-v0+forecast-window-v0`, and
`decision_support_only=true`.

Balanced synthetic rows for `price_area=DK1` returned the three expected
windows: `0-24h` had `row_count=2`, `risk_level=medium`, and
`max_risk_score=45`; `24-48h` had `row_count=2`, `risk_level=low`, and
`max_risk_score=30`; `48-72h` had `row_count=2`, `risk_level=medium`, and
`max_risk_score=35`. Top reason codes were deterministic and included
`EXCHANGE_NET_NOT_USED_V0` in all three windows, with price and renewable-share
codes reflecting the in-script rows.

The high-risk synthetic DK2 run demonstrated max-risk aggregation: the
`24-48h` window became `high` risk with `max_risk_score=75`. Its top reason
codes included `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`.

The empty-window synthetic run demonstrated insufficient caller-provided data
handling: the `24-48h` window had `row_count=0`, `risk_level=unknown`,
`average_risk_score=null`, `max_risk_score=null`, and no top reason codes.

These results are local synthetic preview results only. They are deterministic
aggregation over caller-provided rows, not ML, not DMI/weather based yet, not
production forecast validation, and not evidence of predictive accuracy. The
script does not fetch data, read or write a database, expose an API, run
backend or frontend servers, schedule jobs, use Azure, use ML or LLMs, or
perform control, dispatch, activation, closed-loop, or operational behavior.

### Forecast Preview API Smoke Test Results

Manual smoke testing of `POST /api/forecast/preview` was documented with the
backend started without `DATABASE_URL`. This confirms that caller-provided
forecast rows can be summarized without database access. No frontend,
ingestion, database writes, SQL, live Energi Data Service calls, DMI/weather
calls, scheduler, Azure infrastructure, auth, secrets, ML training, LLM use,
control, dispatch, activation, or operational functionality was used.

Valid DK1 request observations:

- HTTP `200`
- `price_area`: `DK1`
- `generated_at_utc`: `2026-01-01T00:00:00Z`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- windows returned: `3`
- `0-24h`: `row_count=1`, `risk_level=low`, `max_risk_score=30`,
  `average_risk_score=30.0`; top reason codes included `MODERATE_PRICE` and
  `MODERATE_RENEWABLE_SHARE`
- `24-48h`: `row_count=1`, `risk_level=high`, `max_risk_score=75`,
  `average_risk_score=75.0`; top reason codes included
  `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`
- `48-72h`: `row_count=0`, `risk_level=unknown`, `max_risk_score=null`,
  `average_risk_score=null`, and `average_confidence_score=0.0`

High-risk DK2 request observations:

- HTTP `200`
- `price_area`: `DK2`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- `24-48h`: `row_count=1`, `risk_level=high`, `max_risk_score=75`,
  `average_risk_score=75.0`; top reason codes included
  `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`
- `0-24h` and `48-72h` were `unknown` because `row_count=0`

Validation observations:

- `price_area=SE3` returned a validation error indicating that input should be
  `DK1` or `DK2`.
- Timezone-naive `generated_at_utc` returned a validation error indicating that
  `generated_at_utc` must be timezone-aware.

Interpretation: the API returns deterministic forecast-window summaries for
caller-provided rows, demonstrates max-risk aggregation, handles empty windows
as `unknown`, and validates supported price areas plus timezone-aware
`generated_at_utc`. These observations do not establish predictive accuracy,
statistical calibration, production readiness, or operational fitness.

## Limitations

- This is a simple baseline for traceable decision support, not a validated
  forecasting system.
- Missing consumption data limits interpretation of actual surplus conditions;
  `consumption_mw` is recorded as context but does not drive v0 scoring.
- `exchange_net_mw` is validated but does not drive v0 scoring because exchange
  sign conventions can be ambiguous across source systems and require explicit
  validation before use.
- The model does not account for weather forecasts, outages, grid constraints,
  curtailment, balancing markets, or operational conditions.
- Confidence scores are deterministic data-completeness indicators, not
  statistically calibrated probabilities.
- The current validated local dataset is tiny and no full historical backtest
  with outcome labels has been run.
- A deterministic 24-72 hour caller-provided forecast-window aggregation
  foundation exists, but it is not production forecast validation and does not
  fetch, persist, or ingest forecast data.
- No DMI/weather ingestion, PDF report export, auth, Azure deployment,
  scheduled ingestion job, or production database exists yet.
- No monitoring or observability setup exists yet.
- No human approval workflow exists beyond documentation and disclaimers.

Recommended next MVP step: keep `rule-engine-v0` and `forecast-window-v0` as
explainable read-only baselines while adding explicit validation and
caller-provided/local data composition before any UI surface or production data
path. Do not use an LLM as the forecast engine.

## Human Oversight and Safety

Outputs require human review. `rule-engine-v0` must not perform or trigger
automatic control, dispatch, activation, closed-loop workflows, asset
connections, plant/device commands, or live control signals.

The preview API is not autonomous and cannot trigger control actions. It returns
the same read-only decision-support output shape as the pure rule engine.

The current-risk API is also not autonomous. It reads existing local data only
and returns read-only decision support plus metadata indicating whether the
latest `spot_prices` and `power_balance` rows were found.

## Local API Smoke Test Results

Manual local API smoke testing was documented for `POST /api/risk/preview` with
the backend started manually:

```bash
python -m uvicorn app.main:app --reload
```

A valid caller-provided JSON payload used `price_area` `DK1`,
`timestamp_utc` `2026-06-09T21:45:00+02:00`, `price_dkk_per_mwh` `-10`,
`production_mw` `1000`, `wind_onshore_mw` `500`, `wind_offshore_mw` `350`,
`solar_mw` `50`, and `consumption_mw` `900`.

Observed output:

- `risk_level`: `high`
- `risk_score`: `75`
- `confidence_score`: `1.0`
- `reason_codes` included `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`

An invalid input smoke test using `price_area` `SE3` returned a validation
error. Only `DK1` and `DK2` are accepted.

The smoke test used caller-provided JSON only. No database connection was used,
no database writes were performed, no live Energi Data Service polling was
performed, no LLM or ML model was used, and no automatic control, dispatch,
activation, or operational functionality exists.

Manual local API smoke testing was also documented for
`GET /api/risk/current?price_area=DK1` with the backend started manually:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

Observed output:

- `risk_level`: `medium`
- `risk_score`: `35`
- `confidence_score`: `1.0`
- `reason_codes` included `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`
- `metadata.source_tables_used` included `spot_prices` and `power_balance`
- `metadata.spot_price_row_found`: `true`
- `metadata.power_balance_row_found`: `true`

An invalid input smoke test using
`GET /api/risk/current?price_area=SE3` returned a validation error. Only `DK1`
and `DK2` are accepted.

The current-risk smoke test read from local PostgreSQL only through the existing
read-only query path. No database writes were performed, no live Energi Data
Service polling was performed, no startup migrations were run, no Azure
resources were used, no production database was used, no LLM or ML model was
used, and no automatic control, dispatch, activation, or operational
functionality exists.

## Local Frontend Current-Risk Smoke Test Results

Manual local frontend current-risk smoke testing was documented with the backend
started manually:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

The frontend was started manually:

```bash
cd frontend
npm install
npm run dev
```

The browser opened `http://localhost:3000`. The manual read-only UI actions
were selecting DK1, clicking Load spot prices, clicking Load power balance, and
clicking Load current risk.

Observed frontend output:

- Spot prices displayed 3 rows.
- Power balance displayed 3 rows.
- Current surplus risk displayed `risk_level` `medium`.
- `risk_score` was `35`.
- `confidence_score` was `1`.
- `reason_codes` included `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`.
- `model_version` was `rule-engine-v0`.
- `decision_support_only` was `true`.
- `metadata.source_tables_used` showed `spot_prices` and `power_balance`.
- `metadata.spot_price_row_found` was `true`.
- `metadata.power_balance_row_found` was `true`.
- No Failed to fetch error appeared.

The frontend used only the backend API helper and did not call Energi Data
Service directly. No polling or automatic refresh was used, no database writes
were performed, no live EDS polling was performed, no startup migrations were
run, no Azure resources were used, no production database was used, no LLM or
ML model was used, and no automatic control, dispatch, activation, or
operational functionality exists.
