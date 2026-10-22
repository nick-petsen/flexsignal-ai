# Historical Backtest Impact Verification v0

## Objective and status

Determine whether the P0.4 timestamp normalization correction changes the
published public DK1/DK2 surplus-risk backtest when both code versions process
the **same original source records**.

**Status: NOT VERIFIED (2026-10-22).** The original hourly input was not found
in this workspace or the inspected repository history. No historical
before/after backtest was run. The published figures remain historical claims,
but their numerical validity after the correction is unknown.

## Input provenance audit

The first published figures were added in commit `a908e1d` (2026-07-05) to
`docs/BACKTEST_RESULTS.md` as an observed dry run. The documentation names
Energi Data Service `DayAheadPrices` and
`ProductionConsumptionSettlement`, price areas DK1/DK2, and a period of
`2026-01-01` to `now`. It records `dry_run=true`, `file_written=false`, and
`database_write_performed=false`. The backtest scripts fetch the four
dataset/area combinations, normalize their EDS `TimeUTC` or `HourUTC` fields,
pair price and settlement rows by UTC hour, score them, and group risk windows.
The default scoring thresholds documented for the engine are 25 EUR/MWh,
0.65 medium renewable share, and 0.80 high renewable share.

The **exact source records cannot be identified** from the publication. The
resolved Danish-local end timestamp behind `now`, request URLs, source
response bytes or hashes, response order, dataset revision state, raw row
counts, and effective runtime environment were not archived with the result.
An EDS fetch today could return revised settlement values or a different
period, so it would not reproduce the original input.

The canonical
`frontend/src/data/public-surplus-risk-backtest-snapshot.json` was introduced
in commit `a0ee6be` and later given price context in `eb3ecdf`. Its exporter,
`scripts/public_surplus_risk_snapshot_export.py`, embeds the published summary
metrics and selected top-window values as constants. The JSON contains
aggregates and ten selected windows, not the underlying hourly price and
settlement records or their raw timestamp text. It cannot reconstruct all
joins, skipped rows, or risk-window boundaries. The corresponding tests use
small synthetic EDS payloads and assert the fixed artifact; they do not contain
the historical input.

Audit performed: inspected the public input/backtest/export scripts,
`docs/BACKTEST_RESULTS.md`, the canonical JSON, relevant test fixtures, the
workspace files including ignored `.context` files, tracked files, and the
available `origin/main` history. No archived raw or normalized hourly input
for this run was found. This finding is limited to those locations; an
external archive may exist.

## Code revisions and reproducibility

| Role | Revision | Relevant behavior |
| --- | --- | --- |
| First published results | `a908e1d` | Records the observed DK1/DK2 figures with an unresolved `now` end. |
| Last pre-correction revision | `0550a3c` | `public_surplus_risk_backtest_input.py` retains source timestamp text; `public_surplus_risk_backtest.py` strips any offset while truncating to an hour. |
| Corrected revision | `94c6ead` | Converts EDS `TimeUTC` and `HourUTC` values to UTC before deduplication, hourly matching, and window grouping. |

The correction also changes input deduplication from `source_record_id` to
dataset/area/normalized UTC instant. These changes can alter matches, skipped
rows, scores, or window boundaries when source timestamps carry nonzero
offsets or duplicate instants. Code inspection establishes this possibility;
it does not establish whether such records occurred in the original run.

A fair comparison would replay identical frozen **raw EDS response records**
for all four dataset/area combinations, in the same order and with the same
request chunks, through the old and corrected code. It would fix the original
resolved end, all thresholds and other configuration, and use isolated
temporary outputs. Comparing the current EDS feed with the old published
aggregates would not meet that standard. Neither a database read nor snapshot
regeneration is needed for this verification.

## Historical comparison

| Measure | Published pre-correction DK1 | Published pre-correction DK2 | Corrected run on identical input |
| --- | ---: | ---: | --- |
| Joined hours | 4,208 | 4,208 | Unknown |
| Skipped rows | 233 | 233 | Unknown |
| Risk windows | 129 | 72 | Unknown |
| Highest risk score | 100 | 85 | Unknown |

**Exact differences: undetermined.** No comparable before/after results exist
for joined hours, skipped rows, risk-window counts, start/end timestamps,
levels, scores, top windows, or price/production matches. The snapshot's ten
top windows are only a partial output and cannot establish that the other
windows or joined hours remain the same.

## Required follow-up

First, locate the original read-only EDS response archive, if one exists,
including raw `TimeUTC`/`HourUTC` strings and values for DK1/DK2 prices and
settlement, its request metadata and ordering, the resolved end timestamp,
and the effective backtest configuration. Record hashes and provenance before
using it. If that archive cannot be recovered, the historical impact remains
unverifiable; a newly fetched period may support a **new** backtest but cannot
validate these published counts.

If the archive is recovered, the next small task is a read-only comparison
runner that loads the same frozen responses into `0550a3c` and `94c6ead`,
captures outputs only in isolated temporary locations, and reports every
metric and per-window/per-hour difference listed above. Review that result
before considering any separate snapshot or published-metric update.
