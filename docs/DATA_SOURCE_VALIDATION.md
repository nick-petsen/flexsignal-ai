# Data Source Validation

This document records manually validated public API data sources for the v0.1 decision-support MVP. It documents observed responses only; it does not define ingestion, persistence, forecasting, dispatch, activation, or control behavior.

Validation date: 2026-06-08 local project validation session

## Validated Endpoints

### Energi Data Service - `DayAheadPrices`

Command:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --limit 5
```

Result:

- HTTP status: 200
- Top-level keys: `dataset`, `filters`, `limit`, `records`, `total`
- Record count: 5
- Sample fields observed: `DayAheadPriceDKK`, `DayAheadPriceEUR`, `PriceArea`, `TimeDK`, `TimeUTC`

Important note: the unfiltered sample returned `PriceArea = DE`. Future ingestion must filter to `DK1` and `DK2`.

Unit note: `DayAheadPriceDKK` and `DayAheadPriceEUR` are treated as
MWh-based internal spot price values for future schema mapping.

### Energi Data Service - `ElectricityProdex5MinRealtime`

Command:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --limit 5
```

Result:

- HTTP status: 200
- Top-level keys: `dataset`, `filters`, `limit`, `records`, `total`
- Record count: 5
- Sample fields observed: `Minutes5DK`, `Minutes5UTC`, `PriceArea`, `OnshoreWindPower`, `OffshoreWindPower`, `SolarPower`, `ProductionGe100MW`, `ProductionLt100MW`, `ExchangeGermany`, `ExchangeNorway`, `ExchangeSweden`, `ExchangeGreatBelt`, `ExchangeNetherlands`, `ExchangeGreatBritain`

Candidate use: primary candidate for near-real-time DK1/DK2 production, wind, solar, and exchange data.

### Energi Data Service - `ProductionConsumptionSettlement`

Command:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ProductionConsumptionSettlement --limit 5
```

Result:

- HTTP status: 200
- Top-level keys: `dataset`, `filters`, `limit`, `records`, `total`
- Record count: 5
- Sample fields observed: `HourDK`, `HourUTC`, `PriceArea`, `GrossConsumptionMWh`, `CentralPowerMWh`, `LocalPowerMWh`, `OffshoreWindGe100MW_MWh`, `OffshoreWindLt100MW_MWh`, `OnshoreWindGe50kW_MWh`, `OnshoreWindLt50kW_MWh`, `SolarPowerGe10Lt40kW_MWh`, `SolarPowerGe40kW_MWh`, `SolarPowerLt10kW_MWh`, `PowerToHeatMWh`, `ExchangeGE_MWh`, `ExchangeNO_MWh`, `ExchangeSE_MWh`

Candidate use: primary candidate for historical backtesting and settlement-level analysis.

### Energi Data Service - `ElectricityBalanceNonv`

Command:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityBalanceNonv --limit 5
```

Result:

- HTTP status: 200
- Top-level keys: `dataset`, `filters`, `limit`, `records`, `total`
- Record count: 5
- Sample fields observed: `HourDK`, `HourUTC`, `PriceArea`, `TotalLoad`, `OnshoreWindPower`, `OffshoreWindPower`, `SolarPower`, `Biomass`, `FossilGas`, `FossilHardCoal`, `FossilOil`, `HydroPower`, `Waste`, `OtherRenewable`

Candidate use: candidate for non-validated near-real-time electricity balance/load data.

### Elprisenligenu - `DK1`

Command:

```bash
python3 scripts/validate_data_sources.py --source elprisenligenu --date 2026-06-07 --price-area DK1
```

Result:

- HTTP status: 200
- Top-level JSON type: list
- Record count: 24
- Sample fields observed: `DKK_per_kWh`, `EUR_per_kWh`, `EXR`, `time_start`, `time_end`

Unit note: Elprisenligenu exposes kWh-based spot price fields. Any future
ingestion must explicitly convert them to MWh-based internal spot price values.

### Elprisenligenu - `DK2`

Command:

```bash
python3 scripts/validate_data_sources.py --source elprisenligenu --date 2026-06-07 --price-area DK2
```

Result:

- HTTP status: 200
- Top-level JSON type: list
- Record count: 24
- Sample fields observed: `DKK_per_kWh`, `EUR_per_kWh`, `EXR`, `time_start`, `time_end`

Unit note: Elprisenligenu exposes kWh-based spot price fields. Any future
ingestion must explicitly convert them to MWh-based internal spot price values.

## Energi Data Service PriceArea Filter Validation

Manual validation was performed for Energi Data Service `PriceArea` filtering
with both `DK1` and `DK2`.

Validated filter syntax:

```text
filter={"PriceArea":["DK1"]}
filter={"PriceArea":["DK2"]}
```

The following manual validation commands returned HTTP 200, record count 5, and
sample records with the expected `PriceArea`:

| Dataset | PriceArea | Command | Result |
| --- | --- | --- | --- |
| `DayAheadPrices` | `DK1` | `python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --price-area DK1 --limit 5` | HTTP 200; record count 5; sample record `PriceArea` was `DK1`. |
| `DayAheadPrices` | `DK2` | `python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --price-area DK2 --limit 5` | HTTP 200; record count 5; sample record `PriceArea` was `DK2`. |
| `ElectricityProdex5MinRealtime` | `DK1` | `python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 5` | HTTP 200; record count 5; sample record `PriceArea` was `DK1`. |
| `ElectricityProdex5MinRealtime` | `DK2` | `python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --price-area DK2 --limit 5` | HTTP 200; record count 5; sample record `PriceArea` was `DK2`. |

Any future ingestion for DK1/DK2 Energi Data Service datasets must use this
`PriceArea` filtering. This validation does not add ingestion, persistence,
forecasting, dispatch, activation, or control behavior.

## Energi Data Service Normalized Preview

The manual `scripts/preview_eds_normalized_records.py` helper can be used to
preview how `DayAheadPrices` and `ElectricityProdex5MinRealtime` records
normalize after applying the validated DK1/DK2 `PriceArea` filter. It performs a
single read-only HTTP `GET`, prints the final request URL, status, raw count,
normalized count, and compact normalized JSON lines.

This helper is not ingestion, persistence, scheduling, forecasting, dispatch,
activation, or control behavior. It does not expose an API and must remain a
manual validation aid only.

## Energi Data Service Write-Plan Preview

The manual `scripts/preview_eds_write_plan.py` helper can be used to preview how
`DayAheadPrices` and `ElectricityProdex5MinRealtime` records would map into
database write-plan entries after applying the validated DK1/DK2 `PriceArea`
filter. It performs a single read-only HTTP `GET`, prints the final request URL,
HTTP status, raw count, normalized count, write-plan entry count, and compact
write-plan JSON lines.

This helper is manual preview only. It does not connect to a database, execute
SQL, write records, create ingestion jobs, run automatically, expose an API
endpoint, schedule polling, forecast, dispatch, activate, or control energy
assets.

Manual read-only validation was performed for the current write-plan preview
mapping with both `DK1` and `DK2`.

| Dataset | PriceArea | Command | Result |
| --- | --- | --- | --- |
| `DayAheadPrices` | `DK1` | `python3 scripts/preview_eds_write_plan.py --dataset DayAheadPrices --price-area DK1 --limit 2` | HTTP 200; raw records 2; normalized records 2; write-plan entries 2; target table `spot_prices`; operations `upsert_preview`. |
| `DayAheadPrices` | `DK2` | `python3 scripts/preview_eds_write_plan.py --dataset DayAheadPrices --price-area DK2 --limit 2` | HTTP 200; raw records 2; normalized records 2; write-plan entries 2; target table `spot_prices`; operations `upsert_preview`. |
| `ElectricityProdex5MinRealtime` | `DK1` | `python3 scripts/preview_eds_write_plan.py --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 2` | HTTP 200; raw records 2; normalized records 2; write-plan entries 2; target table `power_balance`; operations `upsert_preview`. |
| `ElectricityProdex5MinRealtime` | `DK2` | `python3 scripts/preview_eds_write_plan.py --dataset ElectricityProdex5MinRealtime --price-area DK2 --limit 2` | HTTP 200; raw records 2; normalized records 2; write-plan entries 2; target table `power_balance`; operations `upsert_preview`. |

All four preview runs generated in-memory write-plan entries only. No SQL was
generated, no database connection was opened, and no database writes were
performed.

Important note: `ElectricityProdex5MinRealtime` write-plan entries currently
have `consumption_mw = null`. This is expected because the selected realtime
production dataset does not provide a clear consumption field. Consumption must
be sourced later from a separate validated dataset before surplus-risk scoring
depends on consumption.

## Proposed Historical Local EDS Import Plan

This plan is documentation only. It does not add code, change backend or
frontend behavior, write to a database, run live API polling, add scheduled
jobs, add Azure infrastructure, add secrets, add auth, add ML training, use
LLMs, or add control, dispatch, activation, or operational functionality.

Goal:

- Expand local EDS-derived sample data for `DK1` and `DK2`.
- Support better local read-only backtesting for `rule-engine-v0`.
- Keep the work as manual local technical validation only.

Planned datasets and price areas:

| Dataset | Price areas | Intended local target |
| --- | --- | --- |
| `DayAheadPrices` | `DK1`, `DK2` | `spot_prices` |
| `ElectricityProdex5MinRealtime` | `DK1`, `DK2` | `power_balance` |

Proposed batch sizes:

- Start with `limit 50` per dataset and price area.
- Increase to `limit 100` only after row counts, distinct
  `source_record_id` counts, idempotency, and backtest outputs are checked.
- Increase to a maximum of `limit 500` only after the same checks pass for the
  smaller batches.

Safety gates:

- Local PostgreSQL only.
- `DATABASE_URL` must target `localhost` or `127.0.0.1`.
- No production database.
- No Azure database.
- No scheduled jobs.
- No backend startup ingestion.
- No frontend-triggered ingestion.
- No automatic polling loop.
- Confirmed writes require explicit `--confirm-local-db-write`.
- Dry-run must be run before any confirmed write.

Validation after each import batch:

- Check row counts by `price_area`.
- Check distinct `source_record_id` counts.
- Re-run the same import to validate idempotency.
- Confirm counts do not duplicate unexpectedly.
- Run the local DB read-only backtest for `DK1` and `DK2`.
- Document `risk_level_counts` and `average_risk_score`.

Stop conditions:

- Any duplicate explosion.
- Any non-local `DATABASE_URL`.
- Any write without explicit confirmation.
- Any failed normalization.
- Any unexpected source field mapping.
- Any control, dispatch, activation, closed-loop, or operational behavior.

Limitations:

- A larger local sample is still not full model validation.
- No outcome labels are available yet.
- No DMI/weather data is included yet.
- No 24-72 hour forecast exists yet.
- `rule-engine-v0` remains deterministic and simple.

Recommended next implementation after this plan: add a safe manual historical
import script enhancement or batch wrapper. It should remain local-only,
dry-run-first, and confirmation-gated.

## Manual EDS Local DB Ingest Validation

The manual `scripts/manual_eds_local_db_ingest.py` helper can be used by a
developer to validate the end-to-end local write path for a tiny live Energi
Data Service sample. It fetches one supported dataset and one DK1/DK2 price
area, normalizes records, builds write-plan entries, builds parameterized SQL
commands, and defaults to dry-run. It writes only to a local PostgreSQL database
when `--confirm-local-db-write` is explicitly passed.

Safety gates:

- `DATABASE_URL` is required in dry-run and write mode.
- `DATABASE_URL` must use DB-API format such as
  `postgresql://localhost/flexsignal_ai`.
- The parsed database host must be `localhost` or `127.0.0.1`.
- Supported datasets are limited to `DayAheadPrices` and
  `ElectricityProdex5MinRealtime`.
- Supported price areas are limited to `DK1` and `DK2`.
- The default limit is `2`; the hard maximum is `10`.

The script prints a warning, final request URL, HTTP status, raw count,
normalized count, SQL command count, target tables, committed status, and
rolled-back status. It must not run automatically, read secrets from files,
import FastAPI, expose an endpoint, schedule polling, forecast, dispatch,
activate, or control energy assets.

### Confirmed Manual Local Write Results

Manual live Energi Data Service to local PostgreSQL write validation was
confirmed for `DK1` only with `--limit 2`. These writes required explicit
`--confirm-local-db-write` and used local PostgreSQL only. No Azure database,
production database, FastAPI startup integration, scheduled ingestion job,
automatic write path, API endpoint, control workflow, dispatch workflow,
activation workflow, or operational functionality was used or added.

| Dataset | PriceArea | Command | Result |
| --- | --- | --- | --- |
| `DayAheadPrices` | `DK1` | `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_local_db_ingest.py --dataset DayAheadPrices --price-area DK1 --limit 2 --confirm-local-db-write` | HTTP 200; raw records 2; normalized records 2; SQL commands 2; table `spot_prices`; `committed: true`; `rolled_back: false`; `spot_prices` count increased from 1 to 3. |
| `ElectricityProdex5MinRealtime` | `DK1` | `DATABASE_URL="postgresql://localhost/flexsignal_ai" backend/.venv/bin/python scripts/manual_eds_local_db_ingest.py --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 2 --confirm-local-db-write` | HTTP 200; raw records 2; normalized records 2; SQL commands 2; table `power_balance`; `committed: true`; `rolled_back: false`; `power_balance` count increased from 1 to 3. |

Observed rows included:

- `DayAheadPrices:DK1:2026-06-09T21:45:00`.
- `DayAheadPrices:DK1:2026-06-09T21:30:00`.
- `ElectricityProdex5MinRealtime:DK1:2026-06-08T23:25:00`.
- `ElectricityProdex5MinRealtime:DK1:2026-06-08T23:20:00`.

## Energi Data Service Dry-Run Ingestion Validation

The backend includes a controlled dry-run module at
`backend/app/ingestion/eds_dry_run.py` for validating `DayAheadPrices` and
`ElectricityProdex5MinRealtime` normalization before any persistence workflow is
implemented. It builds the validated Energi Data Service request URL, requires a
DK1 or DK2 `PriceArea`, accepts an injectable fetch function, extracts records,
normalizes supported records, and returns counts for raw, normalized, and
rejected records.

The dry-run module does not write to the database, run automatically, expose an
API endpoint, schedule polling, forecast, dispatch, activate, or control energy
assets. Current tests use mocked payloads only.

## Initial Source Selection for MVP

- Spot prices: `DayAheadPrices` as primary, Elprisenligenu as secondary/backup.
- Near-real-time production and exchange: `ElectricityProdex5MinRealtime`.
- Historical backtesting: `ProductionConsumptionSettlement`.
- Near-real-time load/balance candidate: `ElectricityBalanceNonv`.
- Weather data remains unresolved and must be validated separately.

## Open Implementation Notes

- Add `DK1`/`DK2` filtering before ingestion.
- Use the manually validated Energi Data Service `PriceArea` filter syntax for `DayAheadPrices` and `ElectricityProdex5MinRealtime` ingestion.
- Confirm timestamp normalization to UTC.
- Confirm unit conversions between MW, MWh, EUR/MWh, DKK/MWh, and kWh-based source spot price fields.
- Confirm source licensing and attribution requirements.
- Confirm polling/update frequency before scheduled ingestion.
- Avoid treating Elprisenligenu as the primary source until stability and license are reviewed.
- No source should be used for automatic control or dispatch in v0.1.
