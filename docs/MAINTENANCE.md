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
  the known baseline (rounding + the documented pre-existing 1-day
  legacy-tab date offset + the legacy tab's lack of an options
  multiplier). A *new* kind of mismatch is a signal to investigate.
- Service worker cache version (`CACHE_NAME` in `sw.js`) bumped if any
  `index.html`/`css/*`/`js/*` file changed — otherwise returning users
  stay on stale cached code indefinitely.
- Manual smoke test of the live site after the GitHub Pages deploy
  settles (~30–90s after push).
