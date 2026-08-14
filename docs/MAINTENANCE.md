# fifo-matan — Maintenance Schedule

Short, periodic checklist. Not a substitute for `DEVELOPMENT_RULES.md`'s
per-fix verification checklist — this is standing upkeep, done on a
schedule regardless of whether anything was just changed.

## Monthly

- `git status` / `git log` — working tree clean, nothing unpushed.
- `python3 tools/smoke_check.py` — syntax, duplicate functions, auth
  consistency, manifest/sw asset consistency all pass.
- Production reachable: `curl -sL -o /dev/null -w "%{http_code}\n" https://idansorojon-cell.github.io/fifo-matan/` → expect `200`.
- Apps Script backend reachable and auth enforced: an unauthenticated
  `curl` to the web app `exec` URL with any `action=` param should return
  `{"ok":false,"error":"Unauthorized","code":401}`, not a 500 or a silent
  data leak.
- Finnhub / Anthropic API calls not erroring in Apps Script executions
  (check the Apps Script editor's Executions log — not remotely
  verifiable from git alone).

## Quarterly

- Chart.js CDN pin (`index.html`) still current — check
  `https://data.jsdelivr.com/v1/packages/npm/chart.js/resolved?specifier=latest`
  against the pinned version in `index.html`.
- `claude-sonnet-4-6` model ID in `AppScript_FULL.gs`
  (`handleAiChat_`) still valid — confirm AI Chat returns real replies,
  not a silently-swallowed API error.
- Re-skim `docs/` for accuracy — several files were inherited verbatim
  from Idan's original project at fork time (commit `9108e54`) and are
  marked stale; if anyone does the work to bring one fully up to date,
  remove its banner.
- Confirm the deployed Apps Script backend still matches
  `AppScript_FULL.gs` in git — deploy is a manual paste-and-redeploy
  step, not automatic on `git push` (see `docs/PROJECT_OVERVIEW.md` —
  Deployment).

## After any release where FIFO/tax logic changed

- `python3 tools/dry_run.py test-data/matan_operations_snapshot.csv` —
  `accountingMatches: true`, `fifoErrors: []`.
- `python3 tools/reconcile_legacy.py` — mismatch pattern unchanged from
  the known synthetic-fixture baseline (see `test-data/README.md`): 4
  legacy rows, 2 matched (1 clean, 1 with the deliberate rounding
  mismatch), 2 unmatched (option + short, by design — the legacy tab is
  long-stock-only). A *different* pattern is a signal to investigate.
- Service worker cache version (`CACHE_NAME` in `sw.js`) bumped if any
  `index.html`/`css/*`/`js/*` file changed — otherwise returning users
  stay on stale cached code indefinitely.
- Manual smoke test of the live site after the GitHub Pages deploy
  settles (~30–90s after push).

## Data privacy (standing rule)

Real trading/financial data must never be committed to this repository
— it's public. This applies to any production or user financial data,
not just `test-data/`.

- **Test fixtures must be synthetic.** `test-data/matan_operations_snapshot.csv`
  and `test-data/matan_legacy_fifo_tab.csv` are 100% invented (see
  `test-data/README.md`) — this was not always true; real trading data
  lived at those exact paths from 2026-07-06 until it was removed and
  purged from git history via `git filter-repo` + force-push on
  2026-08-14. Never reintroduce real records at these paths.
- **Real exports stay local and ignored.** `.gitignore` denies every
  `test-data/*.csv` by default, explicitly allow-listing only the two
  synthetic filenames above. A real bank/broker export or live-sheet
  snapshot dropped into `test-data/` for local debugging is
  automatically ignored — leave it that way, don't force-add it.
- **Privacy review before committing anything under `test-data/`.**
  Before `git add`-ing a new or changed file there, confirm by hand
  that it contains no real symbol/date/price/quantity/P&L data, no
  account or tax identifiers, and no names/contact info. If in doubt,
  don't commit it — ask first.
