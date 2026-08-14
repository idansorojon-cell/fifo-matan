# test-data/

**SYNTHETIC TEST DATA — contains no real user trading records.**

Every file in this directory is 100% invented. Dates, symbols, quantities,
and prices are fabricated to exercise specific code paths in
`tools/dry_run.py` and `tools/reconcile_legacy.py` — none of it was
derived from, or scaled/masked from, anyone's real trade history.

Symbols are prefixed `ZZ` to make that obvious at a glance and avoid any
resemblance to real market tickers.

## `matan_operations_snapshot.csv`

Input to `tools/dry_run.py`. Covers:
- comma-formatted quantity parsing (`"1,000"`)
- the sheet's stray "secondary header" row and a blank row (both must be
  skipped, not treated as data or errors)
- a genuinely invalid row (non-numeric qty) to exercise the error path
- LONG: simple full close (ZZLONG)
- multiple buys before a sell, FIFO lot ordering across two lots, and a
  partial close leaving an open position (ZZMULTI)
- a single-lot partial close leaving an open position (ZZPART)
- SHORT open/close (ZZSHORT)
- an option symbol with the 100x multiplier (ZZOPT — full OCC-style
  symbol, e.g. `ZZOPT 300101C00010000`)

## `matan_legacy_fifo_tab.csv`

Input to `tools/reconcile_legacy.py`. Covers:
- a matched row with a deliberate gross-$ rounding mismatch (mirrors the
  real legacy tab's known rounding quirk)
- a matched row with a deliberate 1-day date offset (mirrors the real
  legacy tab's known, pre-existing off-by-one-day bug — see
  `docs/TECHNICAL_DEBT.md`)
- a clean matched row with no mismatch
- two unmatched rows (an option and a short trade) — the legacy tab is
  documented as long-stock-only, so these are expected to never match,
  same as in the real data

## Provenance

Prior to 2026-08-14, this directory held two real, tracked files derived
from Matan's actual trading history (`matan_operations_snapshot.csv`,
`matan_legacy_fifo_tab.csv`, 332 and 198 rows respectively) that had been
public on GitHub for 38 days. They were replaced with the synthetic
fixtures above, and removed from git history entirely (`git filter-repo`
+ force-push), as part of a data-privacy remediation. See git log for the
remediation commit and `docs/MAINTENANCE.md` for the standing rule this
established.

Real exports (bank/broker CSV downloads, sheet snapshots) must never be
committed here — see `.gitignore` and `docs/MAINTENANCE.md`.
