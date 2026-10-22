# Manual public EDS input archive v0

Use `scripts/archive_public_eds_input.py` for JSON response files already obtained
from the public Energi Data Service API. The script makes no network or database
calls. It validates one response, then copies its exact bytes to a local archive.
The default run only validates and prints a proposed manifest. Add `--write` to
create the archive.

```sh
python3 scripts/archive_public_eds_input.py /path/to/download.json \
  --dataset DayAheadPrices --price-area DK1 \
  --requested-start 2026-01-01T00:00 --requested-end 2026-02-01T00:00 \
  --request-timezone Europe/Copenhagen --archive-id prices-dk1-2026-01 \
  --retrieved-at 2026-02-02T12:00:00+01:00 \
  --source-url 'https://api.energidataservice.dk/dataset/DayAheadPrices?start=2026-01-01' \
  --write
```

Run once for each actual response file. Supported combinations are
`DayAheadPrices` and `ProductionConsumptionSettlement`, each for `DK1` and
`DK2`. For each response, choose a unique `--archive-id`; the script never
overwrites one. The example dates and URL are illustrative, not market
evidence. Use the **actual requested** start, end, IANA timezone and exact API
URL. Replace the illustrative URL in the command with the complete URL used
for that response. If the request used multiple chunks or pages, archive every response
separately and retain their request order outside this v0 archive. Resolve
dynamic ends such as `now` before recording them; the tool rejects `now`.

`--retrieved-at` and `--source-url` are optional only when genuinely unknown.
The manifest records `null` and an explicit limitation in that case. Keep any
original request log alongside the local archives if available. The tool does
not infer a retrieval time from the file clock or claim that a supplied URL
actually produced the file. A URL should point to the public EDS API and
include the real filter, time range, sort, limit, offset or cursor parameters
needed to identify the response. Do not put secrets or customer data in a URL.

Each archive directory contains `INPUT.json` and `MANIFEST.json`. The SHA-256
in the manifest is calculated from the original input bytes, without parsing
and reserializing them. Verify a saved copy with:

```sh
shasum -a 256 artifacts/public-eds-inputs/prices-dk1-2026-01/INPUT.json
```

Compare that output with `input_sha256` in the manifest. Matching hashes show
that the file bytes match the manifest's digest. They do not prove API origin,
completeness, or that EDS has not revised historical data. The `record_count`
is the length of the response's `records` array, not a unique-hour count.

A reproducible **new input set** needs all four dataset/area combinations for
the same resolved historical period, all response chunks/pages in request
order, exact request parameters and timezone, the archived bytes and hashes,
and the backtest code revision and effective configuration. A set made now
cannot establish the original inputs behind the published 129 DK1 / 72 DK2
risk-window counts. A verified backtest additionally requires replaying those
frozen records through a fixed code revision and configuration, checking the
output and documenting the comparison. This utility runs no backtest and
calculates no risk windows.

Archives live under `artifacts/public-eds-inputs/`, which `.gitignore`
excludes. Keep this directory local and access controlled. Before committing,
check `git status --short` and
`git check-ignore artifacts/public-eds-inputs/<archive-id>/INPUT.json`;
never force-add raw
datasets or customer information. The committed public snapshot at
`frontend/src/data/public-surplus-risk-backtest-snapshot.json` is a different,
derived artifact and is not modified by this workflow.

For the fixed four-archive April 2026 input set, see
[Frozen hourly EDS backtest input](HOURLY_EDS_BACKTEST_INPUT.md).
