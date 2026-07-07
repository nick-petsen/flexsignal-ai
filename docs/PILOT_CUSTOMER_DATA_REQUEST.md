# Pilot Customer Data Request

## Purpose

This pilot checks whether public DK1/DK2 surplus-risk and price-signal
windows match a customer's operational reality.

The pilot uses public price signal only. It is not a customer value claim.
Customer-specific assessment requires tariff, constraints, operating costs,
and human validation.

FlexSignal AI v0.1 remains read-only decision support. Human review is
required before any customer-facing interpretation is shared.

## What The Customer Gets Back

- PDF pilot preview report.
- Matched public risk windows for DK1 or DK2.
- Indicative gross opportunity signal.
- Human review next steps.

## What The Pilot Does Not Provide

- No verified customer savings.
- No profit or revenue claim.
- No guaranteed value.
- No financial advice.
- No automatic control.
- No dispatch.
- No activation.
- No live control signals.
- No asset integration.

## Required Minimum Data

Please provide the following minimum data where available:

- Price area: `DK1` or `DK2`.
- Timestamp.
- Timezone.
- Load and/or production time series.
- Flexible energy or capacity, if available.
- Availability flag, if available.
- Operational note, if available.
- Operational contact for human review.

Preferred history:

- Minimum 3 months.
- Preferred 6-12 months.
- Hourly or sub-hourly granularity.

## Customer Type Sections

### Producer / Developer

For wind, solar, battery, PtX, hybrid sites, renewable developers, and energy
park operators, include the minimum data plus any available:

- Asset type.
- Installed capacity MW.
- Production or generation time series.
- Flexible capacity MW or flexible energy MWh.
- Curtailment periods.
- Maintenance or outage periods.
- Export, grid, or site constraints.
- Notes on negative-price handling or operating policy.

### Energy Consumer / Flexible Load

For industrial sites, data centers, cold storage, heat pumps, electric boilers,
district heating, PtX consumption, buildings, or campuses, include the minimum
data plus any available:

- Load or consumption time series.
- Flexible load capacity MW.
- Flexible energy MWh.
- Minimum and maximum runtime.
- Ramp limits.
- Lead time.
- Process, comfort, storage, or production constraints.
- Operating schedule or availability windows.

### Grid / Distribution / System Operator

For grid, distribution, system, planning, or local flexibility teams, include
the minimum data plus any available:

- Aggregated load or generation per area.
- Anonymized grid area, feeder, or transformer area id.
- Local generation/load balance.
- Area capacity if shareable.
- Known congestion or bottleneck events.
- Flexible customer categories.
- Planned outages or network constraints.
- Operational notes for interpreting public signal windows.

### Hybrid Site

For sites combining production, storage, PtX, and/or flexible consumption,
include the minimum data plus any available:

- Separate production, consumption, storage, and flexibility time series.
- Site-level net import/export time series.
- Battery state-of-charge if relevant and shareable.
- PtX, storage, or load operating windows.
- Site constraints that affect whether flexibility is technically possible.
- Operational notes explaining site mode during relevant timestamps.

## Data Quality Checklist

Before sending data, please check:

- Timestamps are parseable and consistently ordered.
- Timezone is explicit.
- Price area is consistently `DK1` or `DK2`.
- Units are explicit, for example MWh, kWh, MW, or kW.
- Missing values are blank or consistently encoded.
- Duplicate timestamps are removed or explained.
- Availability flags are documented.
- Operational notes avoid personal data unless approved.
- No passwords, API keys, secrets, control credentials, or personal access
  tokens are included.

## File Format Expectations

Preferred format for v0:

- CSV.
- One row per timestamp.
- UTF-8 encoding where possible.
- Header row with stable column names.
- Use ISO timestamps where possible.

Excel or Parquet can be discussed for later handling, but the local v0
validator accepts CSV only.

## CSV Column Reference

Recommended columns:

| Column | Required | Notes |
| --- | --- | --- |
| `site_id` | Optional | Use an anonymized site id where possible. |
| `price_area` | Yes | `DK1` or `DK2`. |
| `timestamp` | Yes | One row per timestamp. |
| `timezone` | Yes | For example `Europe/Copenhagen` or `UTC`. |
| `load_mwh` | If relevant | Consumption per interval. |
| `generation_mwh` | If relevant | Production per interval. |
| `flexible_capacity_mw` | If available | Available capacity estimate. |
| `flexible_energy_mwh` | If available | Available energy estimate. |
| `availability_flag` | If available | True/false, 1/0, or documented status. |
| `operational_note` | If available | Short context for human review. |

If field names differ, include a short mapping note with the file.

## Questions For Operational Review

- Which contact can validate operational interpretation?
- Are timestamps local time, UTC, or timezone-aware?
- Are values measured, estimated, nominated, or planned?
- Which columns represent load, production, or flexible volume?
- Are there known outages, maintenance periods, or abnormal operations?
- Are there site constraints that make flexibility unavailable at some times?
- Are there tariff, contract, or operating-cost details needed for later
  customer-specific assessment?
- Can the pilot output be discussed externally after human review, and with
  whom?

## Handling Boundary

Do not send raw files through public channels. Do not include secrets,
credentials, or control-system details. Raw customer CSV files must not be
committed to git.

Generated artifacts are ignored by git. A PDF pilot preview report can be
shared only after human review.
