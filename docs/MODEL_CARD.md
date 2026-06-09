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

`GET /api/risk/current?price_area=DK1|DK2` wraps the same rule engine for the
latest existing local database rows. It lazily requires `DATABASE_URL` only when
the endpoint is called, reads the most recent `spot_prices` and `power_balance`
rows for the requested price area through existing read-only query paths,
returns source-table metadata, and does not write to the database, fetch live
Energi Data Service data, schedule ingestion, or connect to operational
systems.

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
