#!/usr/bin/env python3
"""
Reconciles the new engine's long-stock trades against the legacy "עסקאות
FIFO" tab (a partial, stale benchmark — no shorts/options, see
docs/TECHNICAL_DEBT.md "Matan bank-import mapping"). Read-only, offline,
does not touch the live Google Sheet.

Matches by (symbol, qty, buy_price, sell_price) rather than date, since the
legacy tab's own dates are suspected to carry a pre-existing off-by-one-day
bug independent of this migration (see report). Reports gross/net deltas
and any systematic date offset found.
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GS_FILE = REPO_ROOT / "AppScript_FULL.gs"
SNAPSHOT_CSV = REPO_ROOT / "test-data" / "matan_operations_snapshot.csv"
LEGACY_CSV = REPO_ROOT / "test-data" / "matan_legacy_fifo_tab.csv"

STUBS = """
'use strict';
function _stub(name) {
  return new Proxy(function(){}, { get: function(t,p){ return function(){ return undefined; }; },
                                    apply: function(){ return undefined; } });
}
var SpreadsheetApp = _stub('SpreadsheetApp');
var PropertiesService = _stub('PropertiesService');
var UrlFetchApp = _stub('UrlFetchApp');
var ScriptApp = _stub('ScriptApp');
var Logger = { log: function(){} };
var Session = { getScriptTimeZone: function(){ return 'America/New_York'; } };
var Utilities = {
  formatDate: function(date, timeZone, fmt) {
    var parts = new Intl.DateTimeFormat('en-US', { timeZone: timeZone, year: 'numeric', month: '2-digit' }).formatToParts(date);
    var y = parts.find(function(p){return p.type==='year';}).value;
    var m = parts.find(function(p){return p.type==='month';}).value;
    return y + '-' + m;
  }
};
"""

DRIVER_TEMPLATE = """
var FIXTURE = %s;
var normResult = normalizeOperations_(FIXTURE);
var fifoResult = applyFIFO_(normResult.ops);
var longStockTrades = fifoResult.trades.filter(function(t){ return t.side === 'long' && t.instrument === 'stock'; });
JSON.stringify(longStockTrades.map(function(t){
  return { symbol:t.symbol, buy_date:t.buy_date, sell_date:t.sell_date, qty:t.qty,
           buy_price:t.buy_price, sell_price:t.sell_price, gross:t.gross, net:t.net };
}));
"""


def coerce(cell):
    c = cell.strip()
    if c == "":
        return ""
    c_num = c.replace(",", "")
    try:
        return float(c_num) if "." in c_num else int(c_num)
    except ValueError:
        return cell


def load_fixture(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    data = []
    for r in rows:
        while len(r) < 7:
            r.append("")
        data.append([coerce(r[0]), r[1], r[2], coerce(r[3]), coerce(r[4]), coerce(r[5]), coerce(r[6])])
    return data


def get_engine_trades():
    fixture = load_fixture(SNAPSHOT_CSV)
    gs_code = GS_FILE.read_text(encoding="utf-8")
    driver = DRIVER_TEMPLATE % json.dumps(fixture, ensure_ascii=False)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as tmp:
        tmp.write(STUBS + "\n" + gs_code + "\n" + driver)
        tmp_path = tmp.name
    try:
        result = subprocess.run(["osascript", "-l", "JavaScript", tmp_path],
                                 capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        return json.loads(result.stdout)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def load_legacy():
    with open(LEGACY_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def main():
    engine_trades = get_engine_trades()
    legacy_rows = load_legacy()

    # Index engine trades by (symbol, qty, round(buy_price,2), round(sell_price,2))
    def key(sym, qty, bp, sp):
        return (sym, round(float(qty), 2), round(float(bp), 2), round(float(sp), 2))

    engine_by_key = {}
    for t in engine_trades:
        k = key(t["symbol"], t["qty"], t["buy_price"], t["sell_price"])
        engine_by_key.setdefault(k, []).append(t)

    matched = 0
    gross_mismatches = []
    date_offsets = []  # (legacy_date_dmy, engine_date_dmy) pairs for matched rows
    unmatched_legacy = []

    for row in legacy_rows:
        sym = row["סימבול"]
        try:
            qty = float(row["כמות"])
            bp = float(row["מחיר קנייה"])
            sp = float(row["מחיר מכירה"])
            legacy_gross = float(row["ברוטו ($)"])
        except (ValueError, KeyError):
            continue
        k = key(sym, qty, bp, sp)
        candidates = engine_by_key.get(k, [])
        if not candidates:
            unmatched_legacy.append(row)
            continue
        matched += 1
        t = candidates[0]
        if abs(t["gross"] - legacy_gross) > 0.05:
            gross_mismatches.append({"symbol": sym, "legacy_gross": legacy_gross, "engine_gross": t["gross"]})
        date_offsets.append({
            "symbol": sym,
            "legacy_buy_date": row["תאריך קנייה"], "engine_buy_date": t["buy_date"],
            "legacy_sell_date": row["תאריך מכירה"], "engine_sell_date": t["sell_date"],
        })

    print("=== Reconciliation: engine long-stock trades vs legacy 'עסקאות FIFO' tab ===")
    print(f"Legacy rows total: {len(legacy_rows)}")
    print(f"Matched by (symbol,qty,buy_price,sell_price): {matched}")
    print(f"Unmatched legacy rows (no engine trade found): {len(unmatched_legacy)}")
    print(f"Gross $ mismatches among matched rows (>$0.05 diff): {len(gross_mismatches)}")
    for m in gross_mismatches[:10]:
        print("  MISMATCH:", m)

    # Characterize date offset pattern on a sample of matches
    print("\n--- Date comparison sample (first 8 matches) ---")
    for d in date_offsets[:8]:
        print(f"  {d['symbol']}: legacy buy={d['legacy_buy_date']} engine buy={d['engine_buy_date']} | "
              f"legacy sell={d['legacy_sell_date']} engine sell={d['engine_sell_date']}")

    print(f"\n--- Unmatched legacy rows (sample, up to 10 of {len(unmatched_legacy)}) ---")
    for row in unmatched_legacy[:10]:
        print("  ", {k: row[k] for k in ["סימבול", "תאריך קנייה", "תאריך מכירה", "כמות", "מחיר קנייה", "מחיר מכירה", "ברוטו ($)"]})


if __name__ == "__main__":
    main()
