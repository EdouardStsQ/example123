#!/usr/bin/env python3
"""Tests of the box-report-migration-agent scripts (ADR 0028): fixed_width.py, check_fixed_width.py,
compare_fixed_width.py, check_report_run.py, and the report files of the first report (NY's GBUX). Synthetic records
only - no real trade. Run: python3 scripts/tests/test_report_migration.py"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import check_fixed_width as cfw  # noqa: E402
import check_report_run as crr  # noqa: E402
import compare_fixed_width as cmp  # noqa: E402
import fixed_width as fw  # noqa: E402

GBUX = ROOT / "runs/NY_SCH/branch/reports/gbux"
LAYOUT = GBUX / "layout.csv"
FAILS = []


def report(ok, what, detail=""):
    print(("✓ " if ok else "✗ ") + what)
    if not ok:
        FAILS.append(what)
        if detail:
            print("    " + str(detail)[:900])


FIELDS = fw.load_layout(LAYOUT)


def rec(**kv) -> str:
    """One record from field-name values (missing = blank), right-padded like RPAD."""
    base = {"registry": "1457069944", "gl_account": "940320-82", "instrument": "SWAP", "product": "SWAP",
            "product_type": "IR", "direction": "P", "report_product_code": "SWAPIRP", "event_marker": "E",
            "lifecycle_status": "0", "early_termination": "NO", "maturity": "301231"}
    base.update(kv)
    return "".join(base.get(f.name, "").ljust(f.width)[:f.width] for f in FIELDS)


def write(path, lines, nl="\n"):
    Path(path).write_text("".join(ln + nl for ln in lines), encoding="latin-1")
    return path


def main() -> int:
    tmp = Path(tempfile.mkdtemp())

    # === the GBUX layout and report files ============================================================
    report(len(FIELDS) == 22 and fw.record_length(FIELDS) == 164,
           "GBUX layout: 22 fields, 164 characters (spec 2 §1)", (len(FIELDS), fw.record_length(FIELDS)))
    report([f.n for f in FIELDS if f.sensitive] == [1, 2], "GBUX layout: trade id and GL account sensitive")
    seed = list(csv.DictReader((GBUX / "field-matrix.seed.csv").open(encoding="utf-8")))
    report({r["field"] for r in seed if r["field"]} == {str(n) for n in range(1, 23)},
           "GBUX seed matrix: a row for each of the 22 fields")
    dec = {r["id"] for r in csv.DictReader((GBUX / "decisions.csv").open(encoding="utf-8"))}
    dev = {r["id"] for r in csv.DictReader((GBUX / "deviations.csv").open(encoding="utf-8"))}
    named = {d for r in seed for d in r["decision"].split(";") if d.strip()}
    report(named <= dec | dev, "GBUX seed matrix: every decision / deviation it names exists", named - dec - dev)
    report(all(r["status"] == "default" for r in csv.DictReader((GBUX / "decisions.csv").open(encoding="utf-8"))),
           "GBUX decisions: all still defaults (only the BOX lead's answer makes one decided)")
    bad = tmp / "bad-layout.csv"
    bad.write_text(LAYOUT.read_text(encoding="utf-8").replace("2,gl_account,17,46,30", "2,gl_account,18,46,29"),
                   encoding="utf-8")
    try:
        fw.load_layout(bad)
        report(False, "layout loader refuses a gap between fields")
    except fw.LayoutError as exc:
        report("expected start 17" in str(exc), "layout loader refuses a gap between fields", exc)

    bad.write_text(LAYOUT.read_text(encoding="utf-8").replace(",text,[0-9]+,yes,", ",text,[0-9]{1,16},yes,"),
                   encoding="utf-8")
    try:
        fw.load_layout(bad)
        report(False, "layout loader refuses an unquoted comma in a value (a regex {m,n})")
    except fw.LayoutError as exc:
        report("wrong number of columns" in str(exc), "layout loader refuses an unquoted comma in a value (a regex {m,n})",
               exc)

    # === check_fixed_width ============================================================================
    good = write(tmp / "GBUX300101", [rec(), rec(), rec(instrument="DEPOSIT", product="STANDARD", product_type="DL",
                                                       direction="", report_product_code="", asset_liability="A",
                                                       deposit_subtype="STANDARD", overnight="O")])
    ok, out = cfw.check(good, FIELDS)
    txt = "\n".join(out)
    report(ok and "CHECK OK|3 record(s)|0 error(s)" in txt, "checker: a valid file is OK", txt[-400:])
    report("1 extra record(s) in 1 group(s)" in txt, "checker: byte-identical duplicates counted (DV6)")
    report("1457069944" not in txt and "940320-82" not in txt and "(sensitive - not listed)" in txt,
           "checker: trade id and GL account never printed")
    trimmed = write(tmp / "trimmed", [rec().rstrip(" ")])
    ok, out = cfw.check(trimmed, FIELDS)
    report(not ok and "trailing spaces removed" in "\n".join(out), "checker: a TRIMSPOOL-trimmed record named as such")
    short = write(tmp / "short", [rec(maturity="")[:153]])
    ok, out = cfw.check(short, FIELDS)
    report(not ok and "153 characters, layout 164" in "\n".join(out),
           "checker: a record cut before the maturity (no NVL, DV7) is short, not trimmed")
    badval = write(tmp / "badval", [rec(direction="X"), rec(maturity="301332"), rec(product_type=" IR")])
    ok, out = cfw.check(badval, FIELDS)
    t = "\n".join(out)
    report(not ok and "field 8 direction = 'X': value outside the allowed set" in t and "not a YYMMDD date" in t
           and "not left-aligned" in t, "checker: value outside the set, bad date, value not left-aligned", t[-700:])
    crlf = write(tmp / "crlf", [rec()], nl="\r\n")
    ok, out = cfw.check(crlf, FIELDS)
    report(ok and "| CRLF line endings | 1 |" in "\n".join(out), "checker: CRLF accepted and counted")
    r = subprocess.run([sys.executable, str(ROOT / "scripts/check_fixed_width.py"), str(badval), "--layout", str(LAYOUT)],
                       capture_output=True, text=True)
    report(r.returncode == 1 and "CHECK FAIL" in r.stdout, "check_fixed_width.py CLI: exit 1 on errors", r.stdout[-300:])

    # === compare_fixed_width ==========================================================================
    g = write(tmp / "g", [rec(), rec(), rec(registry="2", gl_account="A1")])
    b = write(tmp / "b", [rec(), rec(), rec(registry="2", gl_account="A1")])
    run = lambda *a: subprocess.run([sys.executable, str(ROOT / "scripts/compare_fixed_width.py"), *map(str, a),  # noqa
                                     "--layout", str(LAYOUT)], capture_output=True, text=True)
    r = run(g, b)
    report(r.returncode == 0 and "UNEXPLAINED|0" in r.stdout and "| Identical records | 3 | 3 |" in r.stdout,
           "comparer: identical files - exit 0, UNEXPLAINED|0", r.stdout[-500:])
    b2 = write(tmp / "b2", [rec(), rec(registry="2", gl_account="A1")])
    r = run(g, b2)
    report(r.returncode == 3 and "| Only on this side | 1 | 0 |" in r.stdout,
           "comparer: a duplicate missing on one side is a GBO-only record (multiset)", r.stdout[-600:])
    b3 = write(tmp / "b3", [rec(), rec(lifecycle_status="8"), rec(registry="2", gl_account="A2")])
    r = run(g, b3)
    t = r.stdout
    report(r.returncode == 3 and "| 20 | lifecycle_status | 1 |" in t and "| 2 | gl_account | 1 |" in t
           and "A1" not in t and "A2" not in t, "comparer: differences per field; GL account values hashed", t[-900:])
    exp = tmp / "expect.csv"
    exp.write_text("field,gbo_value,box_value,class\n20,0,8,D5\n2,*,*,D3\n", encoding="utf-8")
    r = run(g, b3, "--expect", exp)
    report(r.returncode == 0 and "D5: 1" in r.stdout and "UNEXPLAINED|0" in r.stdout,
           "comparer: expected differences classed by decision id", r.stdout[-700:])
    gi, bi = tmp / "gbo-ids.csv", tmp / "box-ids.csv"
    gi.write_text("id,key\n1457069944,FR1\n2,FR2\n", encoding="utf-8")
    bi.write_text("id,key\nMX1,FR1\nMX2,FR2\n", encoding="utf-8")
    b4 = write(tmp / "b4", [rec(registry="MX1"), rec(registry="MX1"), rec(registry="MX2", gl_account="A1")])
    r = run(g, b4, "--gbo-ids", gi, "--box-ids", bi)
    report(r.returncode == 0 and "| Identical records | 3 | 3 |" in r.stdout,
           "comparer: different trade ids matched through their common key (D1)", r.stdout[-600:])
    g5 = write(tmp / "g5", [rec(), rec(instrument="FX SPOT", product="FX", product_type="SPOT")])
    b5 = write(tmp / "b5", [rec()])
    r = run(g5, b5, "--only", "4=SWAP,DEPOSIT")
    report(r.returncode == 0 and "| Left out by the filter | 1 | 0 |" in r.stdout,
           "comparer: --only keeps the products in scope (D2)", r.stdout[-600:])
    r = run(g, b, "--detail", ROOT / "runs/x-detail.csv")
    report(r.returncode == 2 and "detail-in-repo" in r.stderr and not (ROOT / "runs/x-detail.csv").exists(),
           "comparer: --detail refused inside the repository", r.stderr)
    det = tmp / "out-detail.csv"
    r = run(g, b3, "--detail", det)
    report(det.exists() and "difference" in det.read_text(), "comparer: --detail written outside the repository")
    gs = write(tmp / "gs", [rec().rstrip(" ")])
    bs = write(tmp / "bs", [rec()])
    r = run(gs, bs)
    report(r.returncode == 0 and "| Short records padded | 1 | 0 |" in r.stdout,
           "comparer: a trimmed record padded before comparing (counted)", r.stdout[-500:])

    # === check_report_run =============================================================================
    root = tmp / "repo"
    shutil.copytree(GBUX, root / "runs/NY_SCH/branch/reports/gbux")
    rd = root / "runs/NY_SCH/branch/reports/gbux"
    runf = root / "runs/NY_SCH/tier2-preparalelo/reports/gbux_20261118_1"
    (runf / "01-evidence").mkdir(parents=True)
    (runf / "report-inputs.json").write_text(json.dumps({"branch": "NY_SCH", "report": "gbux"}), encoding="utf-8")
    shutil.copy(rd / "field-matrix.seed.csv", runf / "02-field-matrix.csv")
    tmpl = (ROOT / "agents/box-report-migration-agent/templates/gap-report.md.tmpl").read_text(encoding="utf-8")
    (runf / "03-gap-report.md").write_text(tmpl.replace("{{", "").replace("}}", ""), encoding="utf-8")
    codes = lambda go=False: [(k, m) for k, m in crr.check(runf, go, root)]  # noqa: E731
    res = codes()
    report(not any(k == "FAIL" for k, _ in res), "run checker: a gap run started from the seed passes",
           [m for k, m in res if k != "OK"])
    report(any(k == "WARN" and "GBO specification files: 0" in m for k, m in res),
           "run checker: warns while John's specification files are not in gbo-spec/")
    res = codes(True)
    fails = " | ".join(m for k, m in res if k == "FAIL")
    report("pending D1" in fails and "pending DV1" in fails and "F21" in fails and "none in 05-compare" in fails,
           "run checker --go-live: defaults, OPEN rows and no comparison all refused", fails)
    m = list(csv.DictReader((runf / "02-field-matrix.csv").open(encoding="utf-8")))
    m[2]["box_source"], m[3]["evidence"] = "", "01-evidence/R-B1-columns.csv"
    m[9]["decision"] = ""  # F1 is OPEN
    m[10]["decision"] = "D99"
    with (runf / "02-field-matrix.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=crr.MATRIX_COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(m)
    (runf / "GBUX250318").write_text("x", encoding="utf-8")
    (runf / "local").mkdir()
    (runf / "local" / "GBUX250319").write_text("x", encoding="utf-8")
    fails = " | ".join(mm for k, mm in codes() if k == "FAIL")
    report("P3: not OPEN but no BOX source" in fails and "R-B1-columns.csv not in the run" in fails
           and "F1: OPEN without the decision" in fails and "D99 not in decisions.csv" in fails
           and "GBUX250318" in fails and "GBUX250319" not in fails,
           "run checker: unsourced row, missing evidence, OPEN without decision, unknown id, a report file outside local/",
           fails)

    # === new_run.py: area reports ====================================================================
    nr = subprocess.run([sys.executable, str(ROOT / "scripts/new_run.py"), "--root", str(tmp / "nr"), "--branch",
                         "NY_SCH", "--tier", "tier2", "--env", "preparalelo", "--area", "reports", "--name", "gbux",
                         "--date", "20261118"], capture_output=True, text=True)
    report(nr.returncode == 0 and (tmp / "nr/runs/NY_SCH/tier2-preparalelo/reports/gbux_20261118_1/RUN.md").exists(),
           "new_run: area reports - runs/<BRANCH>/<tier>-<env>/reports/<report>_<date>_<n>/", nr.stdout + nr.stderr)

    shutil.rmtree(tmp, ignore_errors=True)
    print("\nFAILURES\n" + "\n".join(FAILS) if FAILS else "\nall passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
