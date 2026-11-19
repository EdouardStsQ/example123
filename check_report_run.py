#!/usr/bin/env python3
"""
check_report_run.py - is a box-report-migration-agent run finished? (ADR 0028)

    python3 scripts/check_report_run.py <run folder>              # the gap run / build / parallel run as it stands
    python3 scripts/check_report_run.py <run folder> --go-live     # ... and ready for go-live

The run's `report-inputs.json` names the branch and the report; the report's own files live once per branch in
`runs/<BRANCH>/branch/reports/<report>/` (layout, decodes, the field-matrix seed, decisions, deviations, the GBO
specification). Checks:
- the report folder: every file there and a layout that loads (contiguous, widths add up);
- `02-field-matrix.csv`: every seed row and every layout field present; a class from the set; a row not OPEN has a
  BOX source and its evidence; an OPEN row names the decision it waits for; every decision / deviation id named
  exists; every `01-evidence/<file>.csv` named is in the run;
- `03-gap-report.md`: every section, no `{{...}}` left;
- no trade-level file in the run folder (the report files themselves, spools, id files, detail differences): they
  stay in the run's `local/` folder, which git ignores;
- `--go-live`: every decision and deviation `decided` (with its answer and date), no OPEN row, and a comparison in
  `05-compare/` ending `UNEXPLAINED|0`.
Standard library only. Exit 0 OK · 1 FAIL · 2 bad invocation.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixed_width as fw  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REPORT_FILES = ["layout.csv", "decodes.csv", "field-matrix.seed.csv", "decisions.csv", "deviations.csv",
                "gbo-spec/README.md"]
MATRIX_COLS = ["id", "field", "name", "gbo_source", "box_source", "class", "confidence", "evidence", "decision",
               "status"]
CLASSES = {"same", "equivalent", "constant", "derived", "n/a", "OPEN"}
STATUSES = {"proposed", "confirmed", "OPEN"}
GAP_SECTIONS = ["## Summary", "## Field matrix", "## OPEN", "## Decisions", "## Next"]


def rows(path):
    return list(csv.DictReader(Path(path).open(encoding="utf-8")))


def check(run: Path, go_live: bool, root: Path) -> list[tuple[str, str]]:
    res = []
    ok = lambda m: res.append(("OK", m))  # noqa: E731
    fail = lambda m: res.append(("FAIL", m))  # noqa: E731
    warn = lambda m: res.append(("WARN", m))  # noqa: E731

    inp = run / "report-inputs.json"
    if not inp.exists():
        fail("report-inputs.json missing in the run")
        return res
    try:
        cfg = json.loads(inp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"report-inputs.json: {exc}")
        return res
    branch, report = cfg.get("branch", ""), cfg.get("report", "")
    if not branch or not report:
        fail("report-inputs.json: branch and report are required")
        return res
    rdir = root / (cfg.get("report_dir") or f"runs/{branch}/branch/reports/{report}")

    # the report's own files
    missing = [f for f in REPORT_FILES if not (rdir / f).exists()]
    if missing:
        fail(f"report folder {rdir.relative_to(root) if rdir.is_relative_to(root) else rdir}: missing {', '.join(missing)}")
        return res
    try:
        fields = fw.load_layout(rdir / "layout.csv")
        ok(f"layout: {len(fields)} fields, record length {fw.record_length(fields)}")
    except fw.LayoutError as exc:
        fail(f"layout: {exc}")
        return res
    spec = [p.name for p in (rdir / "gbo-spec").glob("*.md") if p.name != "README.md"]
    (ok if spec else warn)(f"GBO specification files: {len(spec)}" + ("" if spec else
                           " - add them (gbo-spec/README.md says which and how)"))
    decisions = {r["id"]: r for r in rows(rdir / "decisions.csv")}
    deviations = {r["id"]: r for r in rows(rdir / "deviations.csv")}
    seed = rows(rdir / "field-matrix.seed.csv")

    # the field matrix
    mpath = run / "02-field-matrix.csv"
    matrix = []
    if not mpath.exists():
        fail("02-field-matrix.csv missing (start from the seed in the report folder)")
    else:
        matrix = rows(mpath)
        cols = list(matrix[0].keys()) if matrix else []
        if cols != MATRIX_COLS:
            fail(f"02-field-matrix.csv columns {cols} - expected {MATRIX_COLS}")
            matrix = []
    if matrix:
        ids = {r["id"] for r in matrix}
        lost = [r["id"] for r in seed if r["id"] not in ids]
        (fail if lost else ok)(f"matrix: every seed row present" + (f" - missing {', '.join(lost)}" if lost else ""))
        nums = {r["field"] for r in matrix if r["field"]}
        nofield = [str(f.n) for f in fields if str(f.n) not in nums]
        (fail if nofield else ok)("matrix: every layout field has a row" +
                                  (f" - missing field(s) {', '.join(nofield)}" if nofield else ""))
        bad = []
        for r in matrix:
            rid = r["id"]
            if r["class"] not in CLASSES:
                bad.append(f"{rid}: class {r['class']!r}")
            if r["status"] not in STATUSES:
                bad.append(f"{rid}: status {r['status']!r}")
            if r["class"] != "OPEN" and (not r["box_source"].strip() or not r["evidence"].strip()):
                bad.append(f"{rid}: not OPEN but no BOX source or evidence")
            if r["class"] == "OPEN" and not r["decision"].strip():
                bad.append(f"{rid}: OPEN without the decision it waits for")
            for dec in filter(None, re.split(r"[;, ]+", r["decision"])):
                if dec not in decisions and dec not in deviations:
                    bad.append(f"{rid}: decision {dec} not in decisions.csv / deviations.csv")
            for ev in re.findall(r"01-evidence/[\w.\-]+\.csv", r["evidence"]):
                if not (run / ev).exists():
                    bad.append(f"{rid}: {ev} not in the run")
        for b in bad:
            fail(f"matrix {b}")
        if not bad:
            n_open = sum(1 for r in matrix if r["class"] == "OPEN")
            ok(f"matrix: {len(matrix)} rows, {n_open} OPEN, every source evidenced")

    # the gap report
    gp = run / "03-gap-report.md"
    if not gp.exists():
        fail("03-gap-report.md missing")
    else:
        txt = gp.read_text(encoding="utf-8")
        gone = [s for s in GAP_SECTIONS if s not in txt]
        (fail if gone else ok)("03-gap-report.md: every section" + (f" - missing {', '.join(gone)}" if gone else ""))
        if "{{" in txt:
            fail("03-gap-report.md: a {{...}} placeholder left")

    # no trade-level data outside local/
    pat = re.compile(rf"^{re.escape(report.upper())}\d{{6}}|\.lst$|\.spool$|-detail\.csv$|-ids\.csv$", re.I)
    leaked = [str(p.relative_to(run)) for p in run.rglob("*") if p.is_file() and "local" not in p.relative_to(run).parts
              and pat.search(p.name)]
    (fail if leaked else ok)("no trade-level file outside local/" + (f" - {', '.join(leaked)}" if leaked else ""))

    if go_live:
        pend = [k for k, r in decisions.items() if r["status"] != "decided" or not r["answer"] or not r["date"]]
        (fail if pend else ok)("go-live: every decision decided" + (f" - pending {', '.join(pend)}" if pend else ""))
        pend = [k for k, r in deviations.items() if r["status"] != "decided"]
        (fail if pend else ok)("go-live: every deviation decided" + (f" - pending {', '.join(pend)}" if pend else ""))
        opn = [r["id"] for r in matrix if r["class"] == "OPEN"]
        (fail if opn or not matrix else ok)("go-live: no OPEN row" + (f" - {', '.join(opn)}" if opn else ""))
        cmp_ok = [p.name for p in (run / "05-compare").glob("*.md")
                  if "UNEXPLAINED|0" in p.read_text(encoding="utf-8")] if (run / "05-compare").is_dir() else []
        (fail if not cmp_ok else ok)("go-live: a comparison with no unexplained difference" +
                                     (f" ({', '.join(sorted(cmp_ok))})" if cmp_ok else " - none in 05-compare/"))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("run")
    ap.add_argument("--go-live", action="store_true")
    ap.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    run = Path(a.run)
    if not run.is_dir():
        print(f"REFUSED run-missing: {run}", file=sys.stderr)
        return 2
    res = check(run, a.go_live, Path(a.root))
    for kind, msg in res:
        print(f"{kind} {msg}")
    failed = any(k == "FAIL" for k, _ in res)
    print(f"REPORT RUN {'FAIL' if failed else 'OK'}" + (" (go-live)" if a.go_live else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
