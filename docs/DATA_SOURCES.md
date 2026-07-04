# Public Surplus-Risk Data Source Mapping v0

This document maps public data sources for the next surplus-risk backtest step.
It is source mapping only. It does not implement a full surplus-production
backtest, customer-specific savings, forecasting logic, database schema,
backend API behavior, frontend UI, dispatch, activation, automatic control, or
asset integration.

The current public market backtest uses Energi Data Service `DayAheadPrices`
only for market price opportunity. The next historical public surplus-risk v1
backtest should add settlement-based production, consumption, and renewable
generation context before it makes a more complete system-level surplus-risk
estimate. Near-live datasets remain later work.

## Validation Boundary

- Public Energi Data Service data only.
- DK1 and DK2 are the only target Danish price areas.
- Source fields marked "to be verified" must be validated before ingestion or
  scoring logic uses them.
- Dataset classifications are `required_for_historical_surplus_risk_v1`,
  `optional_later`, and `near_live_later`.
- DMI/weather data is later work and is not part of this mapping.
- No listed source may be used for control signals, dispatch instructions,
  asset activation, or operational automation in v0.1.

Manual EDS source checks can be run with:

```bash
python3 scripts/public_surplus_data_source_check.py
```

The checker is dry-run/read-only. It performs small sequential Energi Data
Service `GET` requests, writes no files, writes no database records, calls no
non-EDS external APIs, and does not print environment variables or secrets. The
request delay defaults to `SURPLUS_SOURCE_CHECK_REQUEST_DELAY_SECONDS` when set,
otherwise `1.0` second.

The first public surplus-risk input foundation can be prepared with:

```bash
BACKTEST_START_DATE=2026-01-01 BACKTEST_DRY_RUN=true python3 scripts/public_surplus_risk_backtest_input.py
```

This script fetches only the required historical v1 sources,
`DayAheadPrices` and `ProductionConsumptionSettlement`, for DK1/DK2. It
normalizes public market/system-level rows for later scoring, reports missing
optional fields as warnings, writes no files or database records by default,
and does not calculate final surplus-risk scores or customer-specific savings.
Full scoring comes in the next step.

## Candidate Sources

| Source | Purpose | Expected key fields | DK1/DK2 or bidding-zone support | Timestamp field | Area field | Classification | Known limitation / validation needed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DayAheadPrices` | Market price opportunity context already used by public market v0. | `DayAheadPriceEUR`, `DayAheadPriceDKK`, `PriceArea`, `TimeUTC`, `TimeDK`. | DK1/DK2 `PriceArea` filter already used and manually validated in existing code paths. | `TimeUTC`. | `PriceArea`. | `required_for_historical_surplus_risk_v1`. | This is price context only. It does not prove physical surplus production, demand, customer savings, dispatch value, or asset behavior. |
| `ProductionConsumptionSettlement` | Historical production and consumption context for system-level backtesting. | `GrossConsumptionMWh`, wind MWh fields, solar MWh fields, exchange MWh fields, production-category MWh fields, `PriceArea`, `HourUTC`, `HourDK`. | DK1 and DK2 `PriceArea` samples returned HTTP 200 during manual checks. | `HourUTC`. | `PriceArea`. | `required_for_historical_surplus_risk_v1`. | Settlement data is MWh by hour, not MW. Final unit handling, late updates, and exchange sign convention are to be verified before scoring. |
| `ElectricityProdex5MinRealtime` | Near-live production, wind, solar, and exchange context for later current/recent-state checks. | `ProductionGe100MW`, `ProductionLt100MW`, `OnshoreWindPower`, `OffshoreWindPower`, `SolarPower`, exchange MW fields, `PriceArea`, `Minutes5UTC`, `Minutes5DK`. | DK1/DK2 `PriceArea` filter already validated in existing code paths. | `Minutes5UTC`. | `PriceArea`. | `near_live_later`. | Not required for the next historical surplus-risk v1 backtest. Existing normalizer does not infer consumption. Exchange sign convention and whether all production categories should be summed for risk scoring remain to be verified. |
| `ElectricityBalanceNonv` | Optional near-live non-validated balance/load context. | `TotalLoad`, generation mix fields, `OnshoreWindPower`, `OffshoreWindPower`, `SolarPower`, `PriceArea`, `HourUTC`, `HourDK`. | DK1 sample has returned HTTP 200 in manual checks. Optional DK1/DK2 checks can hit EDS HTTP 429 and should be retried later if this dataset is promoted. | `HourUTC`. | `PriceArea`. | `optional_later`. | Non-validated data may change. DK1/DK2 sample validation, update cadence, units, and reliability are to be verified before use. EDS HTTP 429 on this optional dataset is a warning, not a required-source failure. |
| Exchange/import/export fields inside `ElectricityProdex5MinRealtime` and `ProductionConsumptionSettlement` | Optional interconnector context for later risk interpretation. | `ExchangeGermany`, `ExchangeNorway`, `ExchangeSweden`, `ExchangeGreatBelt`, `ExchangeNetherlands`, `ExchangeGreatBritain`; settlement fields such as `ExchangeGE_MWh`, `ExchangeNO_MWh`, `ExchangeSE_MWh`, `ExchangeGB_MWh`, `ExchangeNL_MWh`, `ExchangeGreatBelt_MWh`. | Present in DK1/DK2 samples where applicable; some links are `null` when not relevant for an area. | Same as parent dataset: `Minutes5UTC` or `HourUTC`. | `PriceArea`. | `optional_later`. | Direction/sign conventions, null handling, and whether a standalone EDS exchange dataset is needed are to be verified. |
| DMI/weather | Later weather feature context for forecasting. | To be verified later. | To be verified later. | To be verified later. | To be verified later. | Out of scope for this PR. | Do not add weather/DMI integration in this step. Existing weather strategy docs track later validation. |

## Minimum v1 Public Surplus-Risk Inputs

A first public surplus-risk v1 backtest should require:

- `DayAheadPrices` for DK1/DK2 price opportunity context.
- `ProductionConsumptionSettlement` for historical demand, production, wind,
  solar, and hourly settlement context.
- The input foundation script normalizes these sources into `timestamp_utc`,
  `price_area`, `day_ahead_price_eur_per_mwh`, `gross_consumption_mwh`,
  `renewable_generation_mwh`, `wind_generation_mwh`, `solar_generation_mwh`,
  `production_total_mwh` where safely derivable, and optional exchange fields
  when available.

Optional later inputs:

- `ElectricityProdex5MinRealtime` for near-live renewable/oversupply and
  recent-state context.
- `ElectricityBalanceNonv` after DK2, unit, update cadence, and non-validated
  data caveats are checked.
- Exchange/import/export fields after sign conventions are documented.
- DMI/weather after separate source validation.

## Field Notes

`ProductionConsumptionSettlement` values are energy values in MWh. Do not force
them into MW fields without an explicit interval conversion and tests.

`ElectricityProdex5MinRealtime` values are candidate power values for near-live
generation and exchange context. Existing code maps wind, solar, total
production, and net exchange candidates, but consumption is not clearly present
in that dataset. It is not required for the next historical surplus-risk v1
backtest.

Exchange fields may be useful later, but they are not required for the first
public surplus-risk v1 pass. Direction and sign convention must be documented
before using exchange values in a risk score.

## Validation Checklist Before Future Backtest Logic

- Confirm exact dataset names and sample fields with
  `scripts/public_surplus_data_source_check.py`.
- Confirm DK1 and DK2 filters for every required dataset.
- Treat optional-later and near-live-later HTTP 429 responses as warnings unless
  those datasets are promoted to required status in a later scope.
- Confirm units for MW, MWh, EUR/MWh, and DKK/MWh fields.
- Confirm timestamp timezone handling and alignment between hourly and
  5-minute sources.
- Confirm renewable aggregation formulas before scoring oversupply.
- Confirm whether exchange/import/export fields are included in v1 or deferred.
- Keep the backtest system-level and public-data-only; do not calculate
  customer-specific savings without customer load, asset, tariff, and
  operational data.
