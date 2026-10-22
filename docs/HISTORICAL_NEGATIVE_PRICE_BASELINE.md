# Historical negative-price baseline (P0.9c)

Run the offline, price-only baseline against the frozen April 1–8, 2026
`DayAheadPrices` archives:

```sh
python3 scripts/historical_negative_price_baseline.py \
  --archive-root /path/to/public-eds-inputs \
  > /path/outside/archives/historical-negative-prices.json
```

The command reads the DK1 and DK2 price archives only. It makes no EDS API or
database calls. Standard output is deterministic JSON; errors go to standard
error with a nonzero exit status. Keep the output outside the read-only archive
directory. The archives themselves stay local and are excluded from Git.

The fixed data period is `[2026-04-01T00:00:00Z,
2026-04-08T00:00:00Z)`, with 672 required 15-minute observations per area.
The script reuses the archive verifier's SHA-256, byte-length, dataset, area,
UTC grid, duplicate, and missing-interval checks. A required archive, record,
timestamp, or native `DayAheadPriceDKK` value that is missing or invalid makes
the whole run fail. Settlement archives are not required. Existing archive
timestamps without an offset are interpreted as UTC by the verifier.

An interval is negative only when its observed `DayAheadPriceDKK` is strictly
less than zero DKK/MWh. Zero, including negative zero, is nonnegative. Within
each area, consecutive negative quarters form a window. Windows use a UTC
start-inclusive/end-exclusive boundary and end at any nonnegative or missing
quarter. The frozen archive run rejects missing quarters altogether; the
grouping rule also prevents gaps from being bridged if used with a sparse
validated sequence. DK1 and DK2 are never joined.

The JSON contains a schema version, data period, method and archive IDs, then
area summaries and their ordered windows. Counts cover all, negative, zero,
and positive intervals; negative windows and total negative duration are also
reported. Observed DKK/MWh statistics are minimum, maximum and mean for all
prices, negative prices, and each window. Minima and maxima retain source
decimal precision as strings. Means are decimal strings rounded to six places
using half-even rounding. A negative-only statistic is `null` when no negative
intervals exist. No hourly averaging, EUR conversion, or price threshold other
than zero is used.

This baseline **identifies historical negative prices** from archived observed
values. **Forecasting negative prices before delivery** requires an issuance
time, data available at that time, and a separate forecast method. **Forecasting
physical surplus risk** additionally needs a validated relationship to physical
system conditions; price alone does not establish surplus. **Identifying
customer-specific flexibility opportunities** requires the customer's load,
assets, tariffs, constraints, and operations. None of those three tasks is
performed here. The archived data does not establish publication-time vintages,
forecast lead time, or prediction accuracy. The output is a retrospective
benchmark, not a forecast, risk score, operational signal, or savings claim.
