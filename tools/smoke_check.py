#!/usr/bin/env python3
"""
Dependency-free smoke check for fifo-matan.

Not a test framework — just fast, offline sanity checks that catch the
most common ways this repo breaks itself: JS/GS syntax errors, duplicate
top-level function names (Apps Script silently lets the last one win),
missing critical entry points, an auth flag that's out of sync between
frontend and backend, a manifest/service-worker pointing at files that
don't exist, and leftover git conflict markers.

Never touches the live Google Sheet or the Apps Script deployment.
Exit code 0 = all checks passed, 1 = at least one failed.

Usage: python3 tools/smoke_check.py
"""
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
failures = []
warnings = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"WARN: {msg}")


def ok(msg):
    print(f"OK:   {msg}")


def node_check(path):
    """Syntax-check a JS-like file via `node --check` if node is available."""
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        warn(f"node not available — skipped syntax check for {path.name}")
        return
    result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"syntax error in {path.name}: {result.stderr.strip().splitlines()[-1] if result.stderr else 'unknown'}")
    else:
        ok(f"syntax valid: {path.name}")


def check_js_syntax():
    for f in sorted((REPO_ROOT / "js").glob("*.js")):
        node_check(f)
    # .gs files are JS-compatible; node --check requires a .js extension
    import tempfile
    for gs in ["AppScript_FULL.gs", "AppScript_PATCH.gs"]:
        src = REPO_ROOT / gs
        if not src.exists():
            continue
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as tmp:
            tmp.write(src.read_bytes())
            tmp_path = Path(tmp.name)
        node_check_named(tmp_path, gs)
        tmp_path.unlink(missing_ok=True)


def node_check_named(tmp_path, display_name):
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        warn(f"node not available — skipped syntax check for {display_name}")
        return
    result = subprocess.run(["node", "--check", str(tmp_path)], capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"syntax error in {display_name}: {result.stderr.strip().splitlines()[-1] if result.stderr else 'unknown'}")
    else:
        ok(f"syntax valid: {display_name}")


def check_duplicate_top_level_functions():
    for gs in ["AppScript_FULL.gs", "AppScript_PATCH.gs"]:
        src = REPO_ROOT / gs
        if not src.exists():
            continue
        names = re.findall(r"^function\s+(\w+)\s*\(", src.read_text(encoding="utf-8"), re.MULTILINE)
        seen = {}
        for n in names:
            seen[n] = seen.get(n, 0) + 1
        dups = [n for n, c in seen.items() if c > 1]
        if dups:
            warn(f"{gs}: duplicate top-level function name(s) (last definition wins): {', '.join(sorted(dups))}")
        else:
            ok(f"{gs}: no duplicate top-level function names")


def check_critical_functions_exist():
    src = (REPO_ROOT / "AppScript_FULL.gs").read_text(encoding="utf-8")
    required = ["doGet", "doPost", "onOpen", "handleGetTrades_", "handleAddTrade_", "validateToken_"]
    for fn in required:
        pattern = rf"^function\s+{re.escape(fn)}\s*\("
        if re.search(pattern, src, re.MULTILINE):
            ok(f"critical function present: {fn}")
        else:
            fail(f"critical function missing from AppScript_FULL.gs: {fn}")


def check_auth_flag_consistency():
    files = {
        "AppScript_FULL.gs": r"var\s+AUTH_DISABLED\s*=\s*(true|false)",
        "js/api.js": r"const\s+AUTH_DISABLED\s*=\s*(true|false)",
        "js/auth.js": r"const\s+AUTH_DISABLED\s*=\s*(true|false)",
    }
    values = {}
    for rel, pattern in files.items():
        path = REPO_ROOT / rel
        if not path.exists():
            fail(f"{rel} not found — cannot check AUTH_DISABLED")
            continue
        m = re.search(pattern, path.read_text(encoding="utf-8"))
        if not m:
            fail(f"AUTH_DISABLED not found in {rel}")
            continue
        values[rel] = m.group(1)
    if len(set(values.values())) > 1:
        fail(f"AUTH_DISABLED mismatch across files: {values}")
    elif values:
        ok(f"AUTH_DISABLED consistent across {len(values)} files: {list(values.values())[0]}")


def check_manifest_and_sw_assets():
    import json
    manifest_path = REPO_ROOT / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for icon in manifest.get("icons", []):
            icon_path = REPO_ROOT / icon["src"]
            if icon_path.exists():
                ok(f"manifest icon exists: {icon['src']}")
            else:
                fail(f"manifest.json references missing icon: {icon['src']}")
    sw_path = REPO_ROOT / "sw.js"
    if sw_path.exists():
        sw_src = sw_path.read_text(encoding="utf-8")
        m = re.search(r"STATIC_ASSETS\s*=\s*\[(.*?)\]", sw_src, re.DOTALL)
        if m:
            entries = re.findall(r"['\"]([^'\"]+)['\"]", m.group(1))
            missing = []
            for e in entries:
                if e.startswith("http") or e == "./":
                    continue
                if not (REPO_ROOT / e).exists():
                    missing.append(e)
            if missing:
                fail(f"sw.js STATIC_ASSETS references missing file(s): {', '.join(missing)}")
            else:
                ok(f"sw.js STATIC_ASSETS: all {len(entries)} local entries exist")


def check_conflict_markers():
    result = subprocess.run(
        ["git", "grep", "-lE", r"^(<<<<<<< |=======$|>>>>>>> )"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        fail(f"conflict markers found in: {result.stdout.strip().splitlines()}")
    else:
        ok("no git conflict markers in tracked files")


def main():
    print(f"fifo-matan smoke check — {REPO_ROOT}\n")
    check_js_syntax()
    print()
    check_duplicate_top_level_functions()
    print()
    check_critical_functions_exist()
    print()
    check_auth_flag_consistency()
    print()
    check_manifest_and_sw_assets()
    print()
    check_conflict_markers()
    print()
    print(f"Summary: {len(failures)} failure(s), {len(warnings)} warning(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
