# Backtest Results

## Status

FlexSignal AI now includes a pure Python backtest evaluator for
`rule-engine-v0`. It is a synthetic/local evaluator only: callers provide a
list of local row dictionaries, and each valid row is passed to
`calculate_surplus_risk`.

Local read-only database backtests have been run against DK1 and DK2
EDS-derived rows after the manual `limit 50` import. This supports a local
technical MVP demo only. It does not claim production readiness, validated
commercial forecasting performance, predictive accuracy, or statistical
calibration.

## Current MVP Backtest Status

The current backtest work is a read-only technical validation layer for
`rule-engine-v0`. It confirms that the local sample data can be read, composed,
paired with `nearest_timestamp_v0_1`, scored, and summarized. It does not
validate commercial performance or operational readiness.

Latest documented local DB backtest results after the confirmed manual EDS
historical batch write:

| Area | Spot prices read | Power balance read | Composed rows | Backtest risk counts | Average risk score |
| --- | ---: | ---: | ---: | --- | ---: |
| DK1 | 53 | 53 | 53 | low=1, medium=52, high=0 | 34.5283 |
| DK2 | 50 | 50 | 50 | low=42, medium=8, high=0 | 21.8 |

Current read-only foundation:

- Synthetic backtest preview exists for local smoke validation.
- Local PostgreSQL read-only backtest exists for existing local rows.
- Backtest row pairing uses `nearest_timestamp_v0_1`.
- `forecast-window-v0` exists as deterministic pure Python aggregation over
  caller-provided rows for `0-24h`, `24-48h`, and `48-72h` windows.
- `POST /api/forecast/preview` exposes that aggregation for caller-provided
  rows only.
- The frontend dashboard has a manual read-only forecast preview card that
  calls `POST /api/forecast/preview` with deterministic
  synthetic/caller-provided demo rows only.
- DK1 and DK2 local DB backtests complete with no failed rows on the expanded
  local samples documented below.
- Results are descriptive summaries of deterministic rule-engine outputs.
- Latest local dataset status is `spot_prices` DK1 `53`, `spot_prices` DK2
  `50`, `power_balance` DK1 `53`, and `power_balance` DK2 `50`.

Still preview / not production:

- Dataset is still small.
- No full historical backtest has been run.
- No outcome labels are available.
- No production 24-72 hour forecast has been validated.
- `forecast-window-v0` and `POST /api/forecast/preview` are not ML, not LLM
  based, not DMI/weather based yet, do not fetch EDS or DMI data, do not read
  or write a database, and are not production forecast validation. The
  frontend card does not change that validation status.
- No DMI/weather data is included.
- No statistical calibration or predictive accuracy claim is made.
- No PDF/report export exists yet.
- No scheduled ingestion jobs, production database, Azure deployment, auth, ML
  training, LLM decisioning, automatic control, dispatch, activation, or
  operational workflow exists.

Recommended next MVP step: keep the deterministic forecast-window foundation
read-only while adding explicit validation and caller-provided/local data
composition before any production data path. Do not use an LLM as the forecast
engine, and do not add control, dispatch, or activation behavior.

## Forecast Preview API Boundary

`POST /api/forecast/preview` accepts caller-provided DK1/DK2 rows and returns
the deterministic `forecast-window-v0` `0-24h`, `24-48h`, and `48-72h`
summaries. It is read-only decision support only.

The frontend dashboard now includes a manual "Forecast preview" card for this
endpoint. It uses deterministic synthetic/caller-provided rows only, includes a
timezone-aware `generated_at_utc`, uses only the backend API base URL helper,
does not auto-load or poll, does not fetch EDS/DMI data from the browser, and
does not read or write a database.

The endpoint does not fetch Energi Data Service data, call DMI/weather APIs,
read or write a database, persist rows, start jobs, train ML models, use LLMs,
or perform automatic control, dispatch, activation, closed-loop workflows,
asset connections, plant/device commands, or live control signals.

### Forecast Preview API Smoke Test Results

`POST /api/forecast/preview` was smoke-tested manually with the backend started
without `DATABASE_URL`. This confirms that the endpoint does not require
database access for caller-provided forecast rows. No frontend was used, and no
ingestion, database writes, SQL, live Energi Data Service calls, DMI/weather
calls, scheduler, Azure infrastructure, auth, secrets, ML training, LLM use,
control, dispatch, activation, or operational functionality was used.

Valid DK1 request:

| Field | Observed value |
| --- | --- |
| HTTP | `200` |
| `price_area` | `DK1` |
| `generated_at_utc` | `2026-01-01T00:00:00Z` |
| `model_version` | `rule-engine-v0+forecast-window-v0` |
| `decision_support_only` | `true` |
| Windows returned | `3` |

Valid DK1 window results:

| Window | Row count | Risk level | Max risk score | Average risk score | Notes |
| --- | ---: | --- | ---: | ---: | --- |
| `0-24h` | 1 | low | 30 | 30.0 | top reason codes included `MODERATE_PRICE` and `MODERATE_RENEWABLE_SHARE` |
| `24-48h` | 1 | high | 75 | 75.0 | top reason codes included `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE` |
| `48-72h` | 0 | unknown | null | null | `average_confidence_score=0.0` |

High-risk DK2 request:

- HTTP `200`
- `price_area`: `DK2`
- `model_version`: `rule-engine-v0+forecast-window-v0`
- `decision_support_only`: `true`
- `24-48h` returned `row_count=1`, `risk_level=high`,
  `max_risk_score=75`, `average_risk_score=75.0`, and top reason codes
  including `HIGH_RENEWABLE_SHARE` and `NEGATIVE_PRICE`.
- `0-24h` and `48-72h` were `unknown` because `row_count=0`.

Validation requests:

- `price_area=SE3` returned a validation error indicating that input should be
  `DK1` or `DK2`.
- Timezone-naive `generated_at_utc` returned a validation error indicating that
  `generated_at_utc` must be timezone-aware.

Interpretation:

- `POST /api/forecast/preview` works for caller-provided rows.
- It returns deterministic `0-24h`, `24-48h`, and `48-72h` forecast windows.
- It demonstrates max-risk aggregation.
- It handles empty windows as `unknown`.
- It validates DK1/DK2 and timezone-aware `generated_at_utc`.
- It is read-only decision support and requires human review.
- It is not production forecast validation.

### Frontend Forecast Preview Smoke Test After CORS Fix

The frontend Forecast preview card was smoke-tested manually from `main` after
the local CORS preflight fix was merged. The backend was started without
`DATABASE_URL`, and the frontend was started locally. The smoke test used only
the Forecast preview card; spot prices, power balance, and current surplus risk
cards were not used. No ingestion, database access, SQL, database writes, live
Energi Data Service calls, DMI/weather calls, scheduler, Azure infrastructure,
auth, secrets, ML training, LLM use, automatic control, dispatch, activation,
or operational functionality was run or added.

Frontend behavior observed:

- Forecast preview card was visible.
- Read-only badge was visible.
- Synthetic/caller-provided preview warning was visible.
- No forecast data appeared before clicking the manual button.
- Manual "Load forecast preview" button triggered the preview.
- The card displayed `model_version=rule-engine-v0+forecast-window-v0`,
  `decision_support_only=true`, `generated_at_utc=2026-01-01T00:00:00Z`, and
  three windows: `0-24h`, `24-48h`, and `48-72h`.

DK1 frontend result:

| Window | Row count | Risk level | Max risk score | Average risk score | Top reason codes observed |
| --- | ---: | --- | ---: | ---: | --- |
| `0-24h` | 1 | low | 30 | 30 | `EXCHANGE_NET_NOT_USED_V0`, `MODERATE_PRICE`, `MODERATE_RENEWABLE_SHARE` |
| `24-48h` | 1 | high | 75 | 75 | `EXCHANGE_NET_NOT_USED_V0`, `HIGH_RENEWABLE_SHARE`, `NEGATIVE_PRICE`; recommended human action required human review |
| `48-72h` | 1 | low | 10 | 10 | `ELEVATED_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0`, `NORMAL_PRICE` |

DK2 frontend result:

- The selected price area was switched to `DK2`.
- Manual "Load forecast preview" returned forecast-window data again.
- The card displayed the same three forecast windows and decision-support-only
  fields without frontend error.
- This confirmed the selected price area can be used by the frontend helper
  for the forecast preview flow.

CORS interpretation: the previous browser error was caused by `OPTIONS`
preflight returning `400`. After the CORS fix, the frontend successfully loaded
forecast preview data from `POST /api/forecast/preview`, practically
confirming the local CORS preflight path for the Forecast preview card.

Interpretation:

- The frontend forecast preview card works locally.
- It manually calls `POST /api/forecast/preview`.
- It displays deterministic `0-24h`, `24-48h`, and `48-72h` windows.
- It uses synthetic/caller-provided demo rows only.
- It is not production forecast validation, not ML, not LLM based, and not
  DMI/weather based yet.
- It does not fetch EDS/DMI data from the browser.
- It does not read or write a database.
- It does not auto-load or poll.
- It remains local frontend/backend smoke-test documentation only, read-only
  decision support only, and requires human review.

## Planned Historical Local Sample Backtest Validation

This is a documentation-only plan for using larger local EDS-derived samples to
improve read-only technical backtest coverage. The current manual batch wrapper
defaults to `limit 10` and now supports explicit `limit 50` for manual local
validation. It does not add backend or frontend behavior, run database writes,
run live API polling, add scheduled jobs, add Azure infrastructure, add
secrets, add auth, add ML training, use LLMs, or add control, dispatch,
activation, closed-loop, or operational functionality.

The proposed local import source remains limited to:

- `DayAheadPrices` for `DK1` and `DK2`.
- `ElectricityProdex5MinRealtime` for `DK1` and `DK2`.

The larger batch progression is:

| Stage | Limit per dataset and price area | Required action before next stage |
| --- | ---: | --- |
| 1 | 50 | Confirmed local write, repeated-import idempotency, and DK1/DK2 local DB backtest results are documented below. |
| 2 | 100 | Repeat the same checks and confirm counts do not duplicate unexpectedly. |
| 3 | 500 maximum | Run only after smaller batches pass without mapping, normalization, or idempotency issues. |

The `100` and `500` stages still require a future explicit enhancement before
the manual wrapper can run them. The wrapper must not bypass the child script
safety gate.

After each batch, rerun the local DB read-only backtest for both `DK1` and
`DK2` and document:

- `spot_price_rows_read`
- `power_balance_rows_read`
- `composed_rows`
- `backtest_summary.risk_level_counts`
- `backtest_summary.average_risk_score`
- `backtest_summary.failed_rows`
- `backtest_summary.missing_price_count`
- `backtest_summary.missing_generation_data_count`

Any future larger local sample imported through the manual batch wrapper should
be followed by DK1 and DK2 local DB backtest reruns before drawing conclusions
from the expanded data.

Stop the local validation flow if any import produces duplicate explosion,
uses a non-local database URL, writes without explicit confirmation, fails
normalization, reveals unexpected source field mapping, or introduces control,
dispatch, activation, closed-loop, or operational behavior.

Even after these larger local samples are imported, the results remain
technical validation only. They are not full model validation because there are
no outcome labels, no DMI/weather data, no production-validated 24-72 hour
forecast, no statistical calibration, and `rule-engine-v0` remains
deterministic and simple.

## Confirmed Local Batch Backtest Results

The following local DB backtests were run after the manual EDS historical batch
wrapper performed confirmed local writes for `DayAheadPrices` and
`ElectricityProdex5MinRealtime` across `DK1` and `DK2`.

Counts before the confirmed batch write:

| Table | DK1 | DK2 |
| --- | ---: | ---: |
| `spot_prices` | 13 | 10 |
| `power_balance` | 13 | 12 |

Confirmed batch write command:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_historical_batch_import.py --limit 50 --confirm-local-db-write --continue-on-error
```

Confirmed batch summary:

- `child_exit_codes`: `[0, 0, 0, 0]`
- `commands_planned`: `4`
- `commands_succeeded`: `4`
- `commands_failed`: `0`
- `confirmed_local_write`: `true`
- `dry_run`: `false`
- `limit`: `50`
- `local_only`: `true`
- `decision_support_only`: `true`
- `price_areas`: `DK1`, `DK2`
- `datasets`: `DayAheadPrices`, `ElectricityProdex5MinRealtime`

Child confirmed write observations:

| Dataset | PriceArea | HTTP | Raw | Normalized | SQL commands | Table | Committed |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `DayAheadPrices` | `DK1` | 200 | 50 | 50 | 50 | `spot_prices` | `true` |
| `DayAheadPrices` | `DK2` | 200 | 50 | 50 | 50 | `spot_prices` | `true` |
| `ElectricityProdex5MinRealtime` | `DK1` | 200 | 50 | 50 | 50 | `power_balance` | `true` |
| `ElectricityProdex5MinRealtime` | `DK2` | 200 | 50 | 50 | 50 | `power_balance` | `true` |

Counts after the confirmed batch write:

| Table | DK1 | DK2 |
| --- | ---: | ---: |
| `spot_prices` | 53 | 50 |
| `power_balance` | 53 | 50 |

The same confirmed batch command was run a second time as an idempotency
check. The second run reported `child_exit_codes: [0, 0, 0, 0]`,
`commands_planned: 4`, `commands_succeeded: 4`, `commands_failed: 0`,
`confirmed_local_write: true`, `dry_run: false`, `limit: 50`, and
`local_only: true`. Counts remained unchanged after the second run:
`spot_prices` DK1 `53`, `spot_prices` DK2 `50`, `power_balance` DK1 `53`, and
`power_balance` DK2 `50`. No duplicate explosion was observed, and the
repeated import was idempotent for the same 50-record batch.

### DK1 Result After Confirmed Batch Write

Command:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK1 --limit 100 --pretty
```

Observed output:

- `price_area`: `DK1`
- `read_only`: `true`
- `decision_support_only`: `true`
- `pairing_strategy`: `nearest_timestamp_v0_1`
- `spot_price_rows_read`: `53`
- `power_balance_rows_read`: `53`
- `composed_rows`: `53`
- `backtest_summary.total_rows`: `53`
- `backtest_summary.evaluated_rows`: `53`
- `backtest_summary.failed_rows`: `0`
- `backtest_summary.risk_level_counts.low`: `1`
- `backtest_summary.risk_level_counts.medium`: `52`
- `backtest_summary.risk_level_counts.high`: `0`
- `backtest_summary.average_risk_score`: `34.5283`
- `backtest_summary.average_confidence_score`: `1.0`
- `backtest_summary.reason_code_counts.NORMAL_PRICE`: `53`
- `backtest_summary.reason_code_counts.HIGH_RENEWABLE_SHARE`: `52`
- `backtest_summary.reason_code_counts.EXCHANGE_NET_NOT_USED_V0`: `53`
- `backtest_summary.reason_code_counts.ELEVATED_RENEWABLE_SHARE`: `1`
- `backtest_summary.missing_price_count`: `0`
- `backtest_summary.missing_generation_data_count`: `0`
- `backtest_summary.model_version`: `rule-engine-v0`

### DK2 Result After Confirmed Batch Write

Command:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK2 --limit 100 --pretty
```

Observed output:

- `price_area`: `DK2`
- `read_only`: `true`
- `decision_support_only`: `true`
- `pairing_strategy`: `nearest_timestamp_v0_1`
- `spot_price_rows_read`: `50`
- `power_balance_rows_read`: `50`
- `composed_rows`: `50`
- `backtest_summary.total_rows`: `50`
- `backtest_summary.evaluated_rows`: `50`
- `backtest_summary.failed_rows`: `0`
- `backtest_summary.risk_level_counts.low`: `42`
- `backtest_summary.risk_level_counts.medium`: `8`
- `backtest_summary.risk_level_counts.high`: `0`
- `backtest_summary.average_risk_score`: `21.8`
- `backtest_summary.average_confidence_score`: `1.0`
- `backtest_summary.reason_code_counts.NORMAL_PRICE`: `50`
- `backtest_summary.reason_code_counts.MODERATE_RENEWABLE_SHARE`: `39`
- `backtest_summary.reason_code_counts.HIGH_RENEWABLE_SHARE`: `8`
- `backtest_summary.reason_code_counts.ELEVATED_RENEWABLE_SHARE`: `3`
- `backtest_summary.reason_code_counts.EXCHANGE_NET_NOT_USED_V0`: `50`
- `backtest_summary.missing_price_count`: `0`
- `backtest_summary.missing_generation_data_count`: `0`
- `backtest_summary.model_version`: `rule-engine-v0`

Interpretation:

- The batch wrapper successfully performed confirmed local writes for all
  supported DK1/DK2 dataset combinations.
- The import was idempotent for the repeated 50-record batch.
- DK1 remained mostly medium risk on the expanded local sample.
- DK2 now includes both low and medium risk on the expanded local sample.
- This is stronger technical validation than the 10-row sample.
- This is still technical validation and not full model validation.
- Dataset size is still small and has no outcome labels.

Safety notes:

- Local PostgreSQL only.
- Manual confirmed write only.
- Explicit `--confirm-local-db-write` was required.
- Backtests were read-only.
- No production database.
- No Azure resources.
- No scheduler.
- No live API polling.
- No backend startup ingestion.
- No frontend-triggered ingestion.
- No automatic polling loop.
- No ML training.
- No LLM use.
- No automatic control, dispatch, activation, or operational functionality.

## Read-Only API And Frontend Smoke Test After Limit 50 Local Import

After local PostgreSQL had been populated by the manual `limit 50` EDS
confirmed local write documented above, the read-only current-risk API and
frontend dashboard were smoke-tested against the larger local sample. No
ingestion or writes were run during this smoke-test. This was a local MVP
smoke-test only, not production validation or model-performance validation.

API commands:

```bash
curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK1"
curl -s "http://127.0.0.1:8000/api/risk/current?price_area=DK2"
```

Observed API results:

| Area | HTTP | Timestamp | Risk level | Risk score | Confidence | Reason codes | Model | Decision support only |
| --- | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| DK1 | 200 | `2026-06-10T17:00:00+02:00` | medium | 35 | 1.0 | `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | `rule-engine-v0` | true |
| DK2 | 200 | `2026-06-10T17:00:00+02:00` | low | 20 | 1.0 | `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | `rule-engine-v0` | true |

Both API responses reported `metadata.source_tables_used` as `spot_prices` and
`power_balance`, with `metadata.spot_price_row_found=true` and
`metadata.power_balance_row_found=true`.

Frontend smoke-test URL:

```text
http://localhost:3000
```

Observed frontend results:

| Area | Spot prices manual load | Power balance manual load | Current risk manual load | Read-only badge |
| --- | --- | --- | --- | --- |
| DK1 | 5 `spot_prices` rows | 5 `power_balance` rows | `risk_level=medium`, `risk_score=35`, `confidence_score=1`; reason codes included `NORMAL_PRICE`, `HIGH_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | visible |
| DK2 | 5 `spot_prices` rows | 5 `power_balance` rows | `risk_level=low`, `risk_score=20`, `confidence_score=1`; reason codes included `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, `EXCHANGE_NET_NOT_USED_V0` | visible |

Interpretation:

- The read-only dashboard works for DK1 and DK2 after the `limit 50` local
  import.
- The frontend still requires manual button clicks.
- No automatic loading, polling, dispatch, activation, or control behavior was
  observed.
- The current-risk endpoint still reads from local PostgreSQL and returns
  decision-support-only results.
- These observations are compatible with the local DB backtest summaries, but
  they do not add outcome labels, statistical calibration, DMI/weather data, or
  a validated 24-72 hour forecast.

Safety notes:

- Local PostgreSQL only.
- Read-only API/UI smoke-test only.
- No ingestion was run.
- No database writes were run.
- No live Energi Data Service polling was run.
- No Azure resources.
- No scheduler.
- No backend startup ingestion.
- No frontend-triggered ingestion.
- No automatic polling loop.
- No ML training.
- No LLM use.
- No automatic control, dispatch, activation, or operational functionality.

## Synthetic Preview Script

`scripts/risk_backtest_preview.py` provides a manual local preview of
`evaluate_risk_backtest(rows)` using a tiny hardcoded synthetic dataset. The
sample rows are included only to exercise low-, medium-, and high-like
rule-engine outputs, missing-data counters, and one invalid row captured in
`failed_rows`.

Run it manually:

```bash
python3 scripts/risk_backtest_preview.py
python3 scripts/risk_backtest_preview.py --pretty
```

The script prints a JSON summary of the evaluator output. It does not read a
historical dataset and does not establish model validity.

This preview is not a real historical backtest, not model validation, not
statistical calibration, and not evidence of production performance. It is only
a local smoke preview of existing deterministic aggregation behavior.

## Forecast Window Synthetic Preview Script

`scripts/forecast_window_preview.py` provides a manual synthetic local preview
of `forecast-window-v0` using fixed `generated_at_utc` output and in-script
caller-provided rows only. It calls `build_forecast_window_forecast(...)` and
prints compact JSON by default.

Run it manually:

```bash
python3 scripts/forecast_window_preview.py
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

The `balanced` scenario covers all three windows with mixed low/medium-like
scores. The `high-risk` scenario includes a negative-price and
high-renewable-share row to demonstrate max-risk window aggregation. The
`empty-window` scenario leaves a matching-price-area window empty, returning
`risk_level` `unknown`.

This preview is not a historical backtest, not model validation, not statistical
calibration, and not evidence of production performance. It does not require
`DATABASE_URL`, read or write a database, run SQL, fetch Energi Data Service
data, call DMI/weather APIs, expose an API endpoint, run frontend code, create
ingestion jobs, use Azure, add secrets, add auth, train ML models, use LLMs,
control assets, dispatch, activate, or perform operational functionality.

### Observed Forecast Window Synthetic Preview Results

The following local synthetic commands were run:

```bash
python3 scripts/forecast_window_preview.py --pretty
python3 scripts/forecast_window_preview.py --price-area DK2 --scenario high-risk --pretty
python3 scripts/forecast_window_preview.py --scenario empty-window --pretty
```

All three outputs printed the synthetic-only warning and reported
`generated_at_utc=2026-01-01T00:00:00Z`,
`model_version=rule-engine-v0+forecast-window-v0`, and
`decision_support_only=true`.

Balanced scenario, `price_area=DK1`:

| Window | Row count | Risk level | Max risk score | Top reason codes |
| --- | ---: | --- | ---: | --- |
| `0-24h` | 2 | medium | 45 | `EXCHANGE_NET_NOT_USED_V0:2`, `LOW_PRICE:1`, `LOW_RENEWABLE_SHARE:1`, `MODERATE_RENEWABLE_SHARE:1`, `NORMAL_PRICE:1` |
| `24-48h` | 2 | low | 30 | `EXCHANGE_NET_NOT_USED_V0:2`, `ELEVATED_RENEWABLE_SHARE:1`, `MODERATE_PRICE:1`, `MODERATE_RENEWABLE_SHARE:1`, `NORMAL_PRICE:1` |
| `48-72h` | 2 | medium | 35 | `EXCHANGE_NET_NOT_USED_V0:2`, `ELEVATED_RENEWABLE_SHARE:1`, `LOW_PRICE:1`, `LOW_RENEWABLE_SHARE:1`, `NORMAL_PRICE:1` |

High-risk scenario, `price_area=DK2`: the `24-48h` window became `high` risk
with `row_count=2` and `max_risk_score=75`. The top reason codes showed the
intended high-risk inputs, including `NEGATIVE_PRICE:1` and
`HIGH_RENEWABLE_SHARE:1`, and demonstrated that the window risk level is based
on the maximum observed row risk score.

Empty-window scenario, `price_area=DK1`: the `24-48h` window had
`row_count=0`, `risk_level=unknown`, `average_risk_score=null`,
`max_risk_score=null`, and `top_reason_codes=[]`. This demonstrates the
insufficient caller-provided data path for an empty forecast window.

Interpretation:

- `forecast-window-v0` preview works locally with synthetic rows.
- It returns `0-24h`, `24-48h`, and `48-72h` windows.
- It is deterministic aggregation over caller-provided rows.
- It is not ML.
- It is not DMI/weather based yet.
- It does not fetch data.
- It does not read or write a database.
- `POST /api/forecast/preview` exposes the same caller-provided aggregation
  boundary for JSON requests only.
- It is not production forecast validation.

Safety notes:

- Synthetic local preview only.
- Read-only decision support only.
- Human review required.
- No database access.
- No live Energi Data Service polling.
- No DMI/weather calls.
- No backend or frontend servers.
- No scheduler.
- No Azure resources.
- No ML or LLM use.
- Must not be used for automatic control, dispatch, or activation.

## Local DB Read-Only Backtest Script

`scripts/risk_backtest_local_db.py` provides a manual local PostgreSQL
read-only backtest preview for `rule-engine-v0` using existing local
`spot_prices` and `power_balance` rows.

Run it manually against a local DB-API PostgreSQL URL:

```bash
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/risk_backtest_local_db.py --price-area DK1
DATABASE_URL='postgresql://localhost/flexsignal_ai' python3 scripts/risk_backtest_local_db.py --price-area DK2 --limit 100 --pretty
```

The script:

- requires `DATABASE_URL`
- accepts only `postgresql://...` DB-API URLs
- refuses non-local hosts and allows only `localhost` or `127.0.0.1`
- reads latest rows from `spot_prices` and `power_balance` through existing
  SELECT-only query builders
- composes rows with `nearest_timestamp_v0_1` pairing through
  `compose_surplus_risk_input(...)`
- runs `evaluate_risk_backtest(rows)`
- prints compact JSON by default and indented JSON with `--pretty`
- reports `pairing_strategy: nearest_timestamp_v0_1`
- reports `decision_support_only: true` and `read_only: true`

Row pairing now uses deterministic `nearest_timestamp_v0_1` behavior. The
power-balance rows are the primary timeline, and each power-balance row is
paired with the nearest spot-price row by `timestamp_utc`. Ties are resolved by
the earlier spot-price timestamp, then original row order. If one table is
empty, remaining rows from the other table are still composed with the missing
side omitted. This improves on list-order pairing but remains a simple timestamp
pairing strategy, not audited historical alignment.

This is still a local technical validation helper, not full model validation,
not statistical calibration, and not evidence of production performance. It
does not fetch, clean, label, or audit a complete historical dataset.

### Observed Local DK1 Result After Nearest-Timestamp Pairing

The local read-only DB backtest was rerun against actual locally stored
EDS-derived rows for DK1 after `nearest_timestamp_v0_1` pairing was merged.

Local table counts before the backtest:

- `spot_prices`: `3`
- `power_balance`: `3`

Command run:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK1 --limit 10 --pretty
```

Observed output:

- `price_area`: `DK1`
- `limit`: `10`
- `read_only`: `true`
- `decision_support_only`: `true`
- `spot_price_rows_read`: `3`
- `power_balance_rows_read`: `3`
- `composed_rows`: `3`
- `pairing_strategy`: `nearest_timestamp_v0_1`
- `backtest_summary.total_rows`: `3`
- `backtest_summary.evaluated_rows`: `3`
- `backtest_summary.failed_rows`: `0`
- `backtest_summary.risk_level_counts.low`: `1`
- `backtest_summary.risk_level_counts.medium`: `2`
- `backtest_summary.risk_level_counts.high`: `0`
- `backtest_summary.average_risk_score`: `26.6667`
- `backtest_summary.average_confidence_score`: `1.0`
- `backtest_summary.reason_code_counts.NORMAL_PRICE`: `3`
- `backtest_summary.reason_code_counts.EXCHANGE_NET_NOT_USED_V0`: `3`
- `backtest_summary.reason_code_counts.HIGH_RENEWABLE_SHARE`: `2`
- `backtest_summary.reason_code_counts.ELEVATED_RENEWABLE_SHARE`: `1`
- `backtest_summary.missing_price_count`: `0`
- `backtest_summary.missing_generation_data_count`: `0`
- `backtest_summary.model_version`: `rule-engine-v0`

Interpretation:

- `nearest_timestamp_v0_1` pairing is active.
- On the tiny local DK1 sample, the risk distribution remained unchanged
  compared with the previous simple pairing run.
- This is expected because the local dataset only contains 3 composed rows.
- This is still technical validation, not full model validation.
- A larger historical dataset is required before drawing performance
  conclusions.

Safety notes:

- Local PostgreSQL only.
- SELECT/read-only only.
- No database writes.
- No live EDS polling.
- No backend or frontend server.
- No startup migrations.
- No production database.
- No Azure resources.
- No ML training.
- No LLM use.
- No automatic control, dispatch, activation, or operational functionality.

### Observed Local DK2 Result After Manual Local Ingest

DK2 was manually validated with tiny local Energi Data Service samples before
running the current-risk smoke test and local read-only DB backtest.

Local EDS dry-run validation:

- `DayAheadPrices` DK2 returned HTTP `200`.
- `DayAheadPrices` raw record count: `2`.
- `DayAheadPrices` normalized record count: `2`.
- `DayAheadPrices` SQL command count: `2`.
- `DayAheadPrices` committed: `false`.
- `ElectricityProdex5MinRealtime` DK2 returned HTTP `200`.
- `ElectricityProdex5MinRealtime` raw record count: `2`.
- `ElectricityProdex5MinRealtime` normalized record count: `2`.
- `ElectricityProdex5MinRealtime` SQL command count: `2`.
- `ElectricityProdex5MinRealtime` committed: `false`.

Confirmed local write validation:

- `DayAheadPrices` DK2 committed: `true`.
- `ElectricityProdex5MinRealtime` DK2 committed: `true`.
- Local PostgreSQL only.
- Manual confirmed local write only.

Local row counts after DK2 ingest:

- `spot_prices`:
  - `DK1`: `3`
  - `DK2`: `2`
- `power_balance`:
  - `DK1`: `3`
  - `DK2`: `2`

Current risk API smoke test:

```text
GET /api/risk/current?price_area=DK2
```

Observed result:

- backend returned HTTP `200`
- `price_area`: `DK2`
- `risk_level`: `low`
- `risk_score`: `20`
- `confidence_score`: `1.0`
- `reason_codes` included `NORMAL_PRICE`, `MODERATE_RENEWABLE_SHARE`, and
  `EXCHANGE_NET_NOT_USED_V0`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`
- `metadata.source_tables_used` included `spot_prices` and `power_balance`
- `metadata.spot_price_row_found`: `true`
- `metadata.power_balance_row_found`: `true`

Command run:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/risk_backtest_local_db.py --price-area DK2 --limit 10 --pretty
```

Observed output:

- `price_area`: `DK2`
- `limit`: `10`
- `read_only`: `true`
- `decision_support_only`: `true`
- `pairing_strategy`: `nearest_timestamp_v0_1`
- `spot_price_rows_read`: `2`
- `power_balance_rows_read`: `2`
- `composed_rows`: `2`
- `backtest_summary.total_rows`: `2`
- `backtest_summary.evaluated_rows`: `2`
- `backtest_summary.failed_rows`: `0`
- `backtest_summary.risk_level_counts.low`: `2`
- `backtest_summary.risk_level_counts.medium`: `0`
- `backtest_summary.risk_level_counts.high`: `0`
- `backtest_summary.average_risk_score`: `20.0`
- `backtest_summary.average_confidence_score`: `1.0`
- `backtest_summary.reason_code_counts.NORMAL_PRICE`: `2`
- `backtest_summary.reason_code_counts.MODERATE_RENEWABLE_SHARE`: `2`
- `backtest_summary.reason_code_counts.EXCHANGE_NET_NOT_USED_V0`: `2`
- `backtest_summary.missing_price_count`: `0`
- `backtest_summary.missing_generation_data_count`: `0`
- `backtest_summary.model_version`: `rule-engine-v0`

Interpretation:

- DK2 local read-only path is now validated.
- The DK2 current risk endpoint returned low risk on the tiny local sample.
- The DK2 local DB backtest returned low risk for both composed rows.
- This is still technical validation, not full model validation.
- The dataset is tiny and not enough for performance conclusions.

Safety notes:

- Local PostgreSQL only.
- Manual validation only.
- SELECT/read-only backtest only.
- No production database.
- No Azure resources.
- No startup migrations.
- No automated ingestion job.
- No live polling loop.
- No ML training.
- No LLM use.
- No automatic control, dispatch, activation, or operational functionality.

## Reported Metrics

`evaluate_risk_backtest(rows)` reports:

- `total_rows`: number of supplied rows
- `evaluated_rows`: rows successfully evaluated by `rule-engine-v0`
- `failed_rows`: rows rejected by validation or other row-level errors
- `risk_level_counts`: counts for `low`, `medium`, and `high`
- `average_risk_score`: average score across evaluated rows
- `average_confidence_score`: average confidence across evaluated rows
- `reason_code_counts`: aggregate reason-code frequencies
- `missing_price_count`: evaluated rows with missing price data
- `missing_generation_data_count`: evaluated rows with missing production or
  renewable generation data
- `failed_row_errors`: row index, error type, and error message for failed rows
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`

Invalid rows do not stop the whole evaluation. The evaluator captures row-level
errors and continues with remaining rows.

## Limitations

- The evaluator only summarizes deterministic `rule-engine-v0` outputs.
- It does not fetch, clean, or validate a historical dataset.
- The local DB backtest script reads local rows only and pairs spot-price and
  power-balance rows with simple nearest-timestamp matching.
- No outcome labels are used, so the backtest cannot measure predictive
  correctness.
- Tiny local samples can be useful for smoke validation but are too small for
  statistical conclusions.
- It does not train a model or tune thresholds.
- It does not calculate precision, recall, false positives, false negatives,
  MAE, RMSE, or calibrated probabilities because no labeled historical
  evaluation dataset has been run.
- Results depend entirely on the caller-provided local rows and the current
  rule-engine behavior.
- Average scores are descriptive summaries of evaluated rows, not forecasts.

## Safety Boundary

The evaluator is read-only decision-support tooling. It does not connect to a
database, execute SQL, call live APIs, poll external services, create ingestion
jobs, or use LLMs.

It does not perform or trigger automatic control, dispatch, activation,
closed-loop workflows, asset connections, plant/device commands, or live
control signals.

The synthetic preview script follows the same boundary: it uses hardcoded local
rows only and does not require `DATABASE_URL`, fetch live Energi Data Service
data, call HTTP APIs, run backend or frontend servers, use Azure, train ML
models, or add operational behavior.

The local DB backtest script narrows the database exception to manual local
PostgreSQL reads only. It executes generated `SELECT` queries only, refuses
non-local database hosts, performs no writes, does not call live Energi Data
Service APIs, does not poll external services, does not add FastAPI endpoints,
does not modify backend startup, does not add frontend code, does not create
ingestion jobs, and does not perform control, dispatch, activation, or
operational workflows.
