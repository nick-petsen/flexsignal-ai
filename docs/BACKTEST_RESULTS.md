# Backtest Results

## Status

FlexSignal AI now includes a pure Python backtest evaluator for
`rule-engine-v0`. It is a synthetic/local evaluator only: callers provide a
list of local row dictionaries, and each valid row is passed to
`calculate_surplus_risk`.

First local read-only database backtests have been run against tiny locally
stored DK1 and DK2 samples of EDS-derived rows. This document does not claim
validated production performance, predictive accuracy, or statistical
calibration.

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
