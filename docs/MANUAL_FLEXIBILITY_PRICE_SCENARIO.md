# Manual flexibility price scenario (P1.0a)

This offline CLI makes an **illustrative historical price comparison** for a
manually selected load shift. It reads the frozen April 1–8, 2026 DK1/DK2
`DayAheadPrices` archives and never changes them. For example, with **hypothetical**
energy and power inputs:

```sh
python3 scripts/manual_flexibility_price_scenario.py \
  --archive-root /path/to/public-eds-inputs \
  --price-area DK1 \
  --original-utc 2026-04-01T00:00:00Z \
  --alternative-utc 2026-04-01T00:15:00Z \
  --energy-mwh 0.125 \
  --max-flexible-power-mw 0.5
```

Both UTC timestamps must be distinct 15-minute starts in the same area. The
caller chooses both intervals; the CLI does not search for a better one. An
optional `--alternative-price-area` can explicitly check that a separately
declared destination area matches `--price-area`. Each input price comes from
native `DayAheadPriceDKK`, with no currency conversion or hourly averaging.
The script verifies both complete frozen price archives, including manifest
hashes, before using any observation. An invalid price anywhere in either
archive fails the run.

The signed indicative spot-price-only gross difference in DKK is
`energy_mwh × (original_price_dkk_per_mwh - alternative_price_dkk_per_mwh)`.
It can be positive, zero, or negative. The required average destination power
is `energy_mwh / 0.25 hours`, then compared with the customer-declared maximum
flexible power. The power check is one limited constraint. Passing it does not
establish that the alternative schedule is operationally feasible.

Successful output is deterministic JSON with decimal strings, both prices and
UTC timestamps, the input energy and power, required average power, power-check
result, signed gross difference, archive IDs, assumptions and limitations.
Errors go to standard error with a nonzero exit status. No API or database
calls, customer integrations, scheduling, dispatch, control, or writes occur.

The archives contain observed historical prices; this calculation does not
assume those observations were known before delivery. It is not a forecast,
optimization, validated customer saving, or operational recommendation.
Actual flexibility, alternative operating schedule, power limitations, market
arrangements and financial outcome require customer validation. Tariffs, taxes,
operational costs and realized savings are outside this calculation.
