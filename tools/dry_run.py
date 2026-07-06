#!/usr/bin/env python3
"""
Dry-run test harness for the extended FIFO engine in AppScript_FULL.gs.

Runs the ACTUAL normalizeOperations_/applyFIFO_/closeLots_/detectInstrument_/
parseBankDate_ functions verbatim (no reimplementation, zero drift risk) by
loading the real .gs file into macOS's built-in JavaScriptCore engine via
`osascript -l JavaScript` (no Node.js required/available on this machine).

Never touches the live Google Sheet or the Apps Script deployment — purely
a local, offline replay against a static CSV snapshot in test-data/.

Usage: python3 tools/dry_run.py [path/to/snapshot.csv]
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GS_FILE = REPO_ROOT / "AppScript_FULL.gs"
DEFAULT_CSV = REPO_ROOT / "test-data" / "matan_operations_snapshot.csv"

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
// ── Dry-run driver ──────────────────────────────────────────────────
var FIXTURE = %s;

var normResult = normalizeOperations_(FIXTURE);
var fifoResult = applyFIFO_(normResult.ops);

var actionCounts = {};
normResult.ops.forEach(function(op){ actionCounts[op.action] = (actionCounts[op.action]||0)+1; });

var instrumentCounts = {};
normResult.ops.forEach(function(op){ instrumentCounts[op.instrument] = (instrumentCounts[op.instrument]||0)+1; });

var totalDataRows = FIXTURE.length - 1;
var accountedFor = normResult.ops.length + normResult.errors.length + normResult.skipped.length;

var shortTrades = fifoResult.trades.filter(function(t){ return t.side === 'short'; });
var optionTrades = fifoResult.trades.filter(function(t){ return t.instrument === 'option'; });

var summary = {
  totalDataRowsProcessed: totalDataRows,
  opsParsed: normResult.ops.length,
  normalizeErrors: normResult.errors,
  skipped: normResult.skipped,
  accountedFor: accountedFor,
  accountingMatches: accountedFor === totalDataRows,
  actionCounts: actionCounts,
  instrumentCounts: instrumentCounts,
  tradesProduced: fifoResult.trades.length,
  openPositions: fifoResult.positions,
  fifoErrors: fifoResult.errors,
  shortTradeCount: shortTrades.length,
  optionTradeCount: optionTrades.length,
  optionTradesSample: optionTrades.map(function(t){ return {symbol:t.symbol, qty:t.qty, buy_price:t.buy_price, sell_price:t.sell_price, gross:t.gross, net:t.net, multiplier:t.multiplier}; })
};

JSON.stringify(summary, null, 2);
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


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    fixture = load_fixture(csv_path)
    gs_code = GS_FILE.read_text(encoding="utf-8")
    driver = DRIVER_TEMPLATE % json.dumps(fixture, ensure_ascii=False)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as tmp:
        tmp.write(STUBS + "\n" + gs_code + "\n" + driver)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", tmp_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print("HARNESS FAILED (non-zero exit):", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        print(result.stdout)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
