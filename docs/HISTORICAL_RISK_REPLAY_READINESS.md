# Historical risk replay readiness (P0.9b.4)

Run the read-only audit against the same four local archives as P0.9a:

```sh
python3 scripts/audit_historical_risk_replay.py \
  --archive-root /path/to/public-eds-inputs
```

The command calls the P0.9a builder, including the P0.8 archive integrity and
UTC alignment checks. It prints deterministic JSON with `PASS` or `BLOCKED`
for each area, each compatibility check, and overall. Exit `0` means PASS,
exit `1` means the audit completed and readiness is BLOCKED, and exit `2`
means archive verification/build or audit execution failed (or the CLI
arguments were invalid). Execution errors produce a fail-closed JSON report
with overall `BLOCKED` and an `execution_error`; argument errors follow
standard argparse stderr output.
It reads archive bytes only; it does not save the generated rows, score them,
calculate risk windows, fetch EDS, or use a database. A build failure blocks
both areas. `source_field_coverage` counts absent and explicit `null` values
separately in each area's 168 settlement rows.

## Actual input contracts and mapping

| Consumer input | P0.9a field | Audit result |
| --- | --- | --- |
| Historical public engine: area and UTC hour | `price_area`, `hour_utc` | Direct, after frozen period and unique-hour checks. |
| Historical public engine: EUR/MWh price | `price_eur_per_mwh` | Direct hourly mean of four observed day-ahead quarters. |
| Current `rule-engine-v0`: DKK/MWh price | `price_dkk_per_mwh` | Native hourly mean of four observed `DayAheadPriceDKK` quarters, with no FX conversion. The audit requires a finite decimal string representable by the rule engine's numeric price input. Observed price mapping passes for both areas. Issuance-time vintage remains unproven. |
| Historical public engine: gross consumption | `settlement_observed.GrossConsumptionMWh` | Direct; must be present, numeric, finite, and positive. |
| Historical public engine: renewable generation | Wind and solar component fields plus one hydro/other-renewable field in `settlement_observed` | Existing `normalize_production_consumption_record` sums these fields. The audit requires every wind and solar component and at least one hydro/other-renewable alternative, avoiding an unmarked partial sum. Values must be finite and nonnegative. |
| Current `rule-engine-v0`: production MW | No direct validated P0.9a total | Settlement has hourly MWh components; the historical normalizer can derive a different `production_total_mwh`, but that is neither a verified current-engine denominator nor an issuance-time forecast. |
| Current `rule-engine-v0`: onshore wind, offshore wind, solar MW | Corresponding hourly MWh settlement components | An hourly energy total could represent average MW for that hour, but these values are observed after the hour, so they cannot be used as forecast inputs without a separately archived issuance-time forecast. |
| Current `rule-engine-v0`: consumption and net exchange MW | Gross consumption and exchange MWh settlement fields | Context only in v0 scoring; observed and unavailable as issuance-time forecasts. Exchange sign conventions remain unvalidated. |
| Forecast-window contract: `generated_at_utc` and future rows | No issuance timestamp or archived forecast rows | Blocked. A historical observation timestamp is not a forecast issuance timestamp. |

The audit checks the current engine's actual `VALID_PRICE_AREAS`,
`NUMERIC_FIELDS`, `RENEWABLE_FIELDS`, and `_validate_input` contract from
`backend/app/risk/rule_engine.py`; changed or incompatible contracts fail
closed. The validator technically permits omitted numerical
fields and then returns a low-information score with missing-data reason codes.
The audit treats DKK price and production/renewables as **required for a
meaningful compatibility claim**, so it fails closed instead of calling the
engine with missing values. The `price_input` finding checks the observed DKK
field independently; it does not establish when that price was published.
The historical public engine is a separate scoring implementation with EUR/MWh
price and gross-consumption-based renewable share; this audit checks its input
mapping only.

In `rule-engine-v0`, `production_mw` is the denominator for the sum of
`wind_onshore_mw`, `wind_offshore_mw`, and `solar_mw`. The historical public
engine instead divides renewable generation MWh by gross consumption MWh.
Those denominators have different meanings. The audit does not infer
`production_mw` from unrelated settlement generation values.

## Four-archive finding

The local frozen April 2026 archives yield 168 rows each for DK1 and DK2.
Both areas pass **observed historical input** mapping, with no absent or null
required gross-consumption or wind/solar fields and a present hydro field.
The native observed DKK/MWh price passes the current rule engine's price input
check in both areas. Both remain **BLOCKED** for current `rule-engine-v0`
compatibility because the production MW denominator has not been validated.
Both are **BLOCKED** for forecast issuance because issuance-time inputs and vintages
are unproven. Overall readiness is **BLOCKED**. The complete JSON report stays
local and is not committed.

## Observed data and look-ahead boundary

P0.9a rows are observed historical data. `settlement_observed` consumption,
wind, solar, and hydro generation are realized values. Feeding those values to
any risk forecast issued before their publication introduces look-ahead bias.
The day-ahead price may have been available before delivery, but the archive
does not establish the publication time or vintage of the particular value;
assuming it was known at issuance may also introduce look-ahead bias. Neither
P0.9a nor these archives include `generated_at_utc`, source publication or
revision timestamps, or the exact forecast inputs visible at issuance.

An `observed_historical_input=PASS` means only that the frozen rows can be
mapped to the older historical public engine's input fields without filling
required values, with a valid native DKK price also present. It is **not** a
forecast replay pass, a risk score, a risk window result, or an accuracy claim.
Overall readiness remains `BLOCKED` while
production semantics and issuance-time provenance are unresolved. The April
2026 archive period also cannot verify the old 129/72 window counts from a
different input period whose original records have not been found locally.
