# Backtest Results

## Status

FlexSignal AI now includes a pure Python backtest evaluator for
`rule-engine-v0`. It is a synthetic/local evaluator only: callers provide a
list of local row dictionaries, and each valid row is passed to
`calculate_surplus_risk`.

No real historical backtest has been run yet. This document does not claim
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
- composes rows through `compose_surplus_risk_input(...)`
- runs `evaluate_risk_backtest(rows)`
- prints compact JSON by default and indented JSON with `--pretty`
- reports `decision_support_only: true` and `read_only: true`

Row pairing is deliberately simple in v0. The script reads each table ordered by
latest `timestamp_utc` descending, then pairs rows by list order. If one table
returns more rows than the other, remaining rows are still composed with the
missing side omitted. This keeps the behavior deterministic but means results
should not be interpreted as fully time-aligned historical validation.

This is still a local technical validation helper, not full model validation,
not statistical calibration, and not evidence of production performance. It
does not fetch, clean, label, or audit a complete historical dataset.

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
  power-balance rows by list order after latest-first table reads.
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
