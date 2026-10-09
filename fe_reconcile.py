#!/usr/bin/env python3
"""
fe_reconcile.py - GBO vs BOX FE reconciliation: the "Y" test and the parallel test [operator, 2026-10-09; basics].

    python3 scripts/fe_reconcile.py pack    runs/<BRANCH>/<tier>-<env>/tests/<y|parallel>/<name>_<YYYYMMDD>_<n>/
    python3 scripts/fe_reconcile.py compare runs/<BRANCH>/<tier>-<env>/tests/<y|parallel>/<run>/ [--date YYYY-MM-DD]

Skills `box-fe-y-test` (a few trades, one or a few dates, field by field) and `box-fe-parallel-test` (the whole
branch, every day of a period, breaks followed day to day). Reads <run>/y-test-inputs.json or
parallel-test-inputs.json and the field map docs/reference/gbo-box-fe-field-map.csv (per product and area - deal,
financial, mtm: the GBO and BOX tables, the key, the date column, the fields, their kind and tolerance). No agent
touches a database: `pack` writes the extraction queries, the operator runs them and returns each output as a CSV,
`compare` reconciles the CSVs.

  pack     01-plan.md (steps + OPEN points), sql/10-GBO-<area>.sql, sql/20-BOX-<area>.sql
           (evidence expected at 01-evidence/<date>/gbo-<area>.csv and box-<area>.csv)
  compare  03-recon/<date>-<area>.csv (key, field, GBO, BOX, difference, status) and 03-results.md;
           parallel: 04-breaks.csv - every break with first / last date seen, days open, NEW / OPEN / RESOLVED

Status per key and field: OK, DIFF (beyond the tolerance), ONLY_GBO, ONLY_BOX (the trade on one side only),
NO_COLUMN (the field missing from a CSV). Amounts compare with tol_abs / tol_rel (either passes); dates as
YYYY-MM-DD whatever the CSV format; text trimmed, upper case. A map value still '<...>' is an OPEN point, never
guessed. Standard library only. Exit 0 written · 1 refused · 2 bad invocation.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "docs/reference/gbo-box-fe-field-map.csv"
INPUTS = {"y": "y-test-inputs.json", "parallel": "parallel-test-inputs.json"}
AREAS = ("deal", "financial", "mtm")


class Result:
    def __init__(self):
        self.errors = []

    def err(self, code, where, msg):
        self.errors.append((code, where, msg))
        print(f"REFUSED {code}: {where}: {msg}", file=sys.stderr)


def undecided(v) -> bool:
    return v is None or (isinstance(v, str) and (not v.strip() or v.strip().startswith("<")))


def qlist(xs) -> str:
    return ", ".join("'" + str(x).replace("'", "''") + "'" for x in xs)


def num(v):
    s = str(v or "").strip().replace(" ", "")
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})*,\d+", s) or re.fullmatch(r"-?\d+,\d+", s):
        s = s.replace(".", "").replace(",", ".")          # 1.234,56 (Spanish locale export)
    try:
        return float(s)
    except ValueError:
        return None


MONTHS = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
MONTHS.update({"ENE": 1, "ABR": 4, "AGO": 8, "DIC": 12})


def day(v) -> str:
    s = str(v or "").strip().upper()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "-".join(m.groups())
    m = re.match(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", s)
    if m:
        d, mo, y = m.groups()
        return f"{int(y) + 2000 if len(y) == 2 else int(y):04d}-{int(mo):02d}-{int(d):02d}"
    m = re.match(r"(\d{1,2})-([A-Z]{3})-(\d{2,4})", s)
    if m and m.group(2) in MONTHS:
        d, mo, y = m.groups()
        return f"{int(y) + 2000 if len(y) == 2 else int(y):04d}-{MONTHS[mo]:02d}-{int(d):02d}"
    return s


def same(kind, a, b, tabs, trel):
    """(status, difference) of one field."""
    if kind == "amount":
        x, y = num(a), num(b)
        if x is None and y is None:
            return ("OK" if str(a or "").strip() == str(b or "").strip() else "DIFF"), ""
        if x is None or y is None:
            return "DIFF", ""
        d = y - x
        ok = abs(d) <= (num(tabs) or 0.0) or (num(trel) is not None and abs(d) <= abs(x) * num(trel))
        return ("OK" if ok else "DIFF"), f"{d:.6f}".rstrip("0").rstrip(".")
    if kind == "date":
        return ("OK" if day(a) == day(b) else "DIFF"), ""
    return ("OK" if str(a or "").strip().upper() == str(b or "").strip().upper() else "DIFF"), ""


def load_map(path: Path, product: str, areas) -> dict:
    """{area: {table: row, key: row, date: row, filter: row, fields: [rows]}} for the product."""
    out = {a: {"fields": []} for a in areas}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if r["product"].strip().lower() != product or r["area"].strip() not in out:
            continue
        a, role = r["area"].strip(), r["role"].strip()
        if role == "field":
            out[a]["fields"].append(r)
        else:
            out[a][role] = r
    return out


def read_inputs(run: Path, res: Result):
    found = [(m, run / f) for m, f in INPUTS.items() if (run / f).exists()]
    if not found:
        res.err("inputs-missing", str(run), f"{' or '.join(INPUTS.values())} - copy the skill's template there")
        return None, None
    mode, p = found[0]
    cfg = json.loads(p.read_text(encoding="utf-8-sig"))
    return mode, cfg


def pack(run: Path, res: Result) -> int:
    mode, cfg = read_inputs(run, res)
    if cfg is None:
        return 1
    opens = []
    prod = str(cfg.get("product") or "").lower()
    areas = [a for a in (cfg.get("areas") or AREAS) if a in AREAS]
    mp = Path(cfg.get("field_map") or MAP)
    mp = mp if mp.is_absolute() else ROOT / mp
    if not mp.exists():
        res.err("map-missing", str(mp), "the field map (docs/reference/gbo-box-fe-field-map.csv)")
        return 1
    fmap = load_map(mp, prod, areas)
    for k, what in (("gbo_environment", "the GBO environment holding the target's data for the same dates"),
                    ("box_environment", "the BOX environment (NY_SCH: DGBOUS for the Y test? IGBOUSIB = PRE Paralelo)")):
        if undecided(cfg.get(k)):
            opens.append(f"`{k}` - {what}")
    dates = [d for d in (cfg.get("dates") or []) if not undecided(d)]
    if not dates:
        opens.append("`dates` - the date(s) to compare, YYYY-MM-DD")
    trades = [t for t in (cfg.get("trades") or []) if not undecided(t)]
    if mode == "y" and not trades:
        opens.append("`trades` - the trades to compare (their values in the key column, the same on both sides)")
    dl = ", ".join(f"DATE '{d}'" for d in dates) or "DATE '<date>'"
    sql = run / "sql"
    sql.mkdir(exist_ok=True)
    for a in areas:
        m = fmap[a]
        t, k, dt = m.get("table") or {}, m.get("key") or {}, m.get("date") or {}
        flt = m.get("filter") or {}
        if not t:
            opens.append(f"field map - {prod} `{a}`: no table row")
            continue
        for side, tag in (("gbo", "10-GBO"), ("box", "20-BOX")):
            tab, kc, dc = t.get(f"{side}_table", ""), k.get(f"{side}_column", ""), dt.get(f"{side}_column", "")
            for v, what in ((tab, "table"), (kc, "key column"), (dc, "date column")):
                if undecided(v):
                    opens.append(f"field map - {prod} `{a}` {side.upper()} {what}")
            cols = [f[f"{side}_column"] for f in m["fields"] if not undecided(f[f"{side}_column"])]
            if not cols:
                opens.append(f"field map - {prod} `{a}` {side.upper()}: no field to compare yet (role `field` rows)")
            cond = [f"TRUNC({dc or '<date column>'}) IN ({dl})"]
            if trades:
                cond.append(f"{kc or '<key column>'} IN ({qlist(trades)})")
            extra = cfg.get(f"{side}_filter") or flt.get(f"{side}_column")
            if not undecided(extra):
                cond.append(f"({extra})")
            sel = ", ".join(dict.fromkeys([f"TRUNC({dc or '<date column>'}) RECON_DATE", kc or "<key column>", *cols]))
            env = cfg.get(f"{side}_environment") or f"<{side} environment>"
            (sql / f"{tag}-{a}.sql").write_text(
                f"-- {side.upper()} ({env}) - {prod} {a}: export as CSV (with header) to 01-evidence/<date>/{side}-{a}.csv,\n"
                "-- one file per date (or one file with all dates: compare splits it by RECON_DATE).\n"
                f"-- Table / columns from {mp.relative_to(ROOT) if mp.is_relative_to(ROOT) else mp} (status: {t.get('status', '')}).\n"
                f"SELECT {sel}\nFROM {tab or '<table>'}\nWHERE {' AND '.join(cond)}\nORDER BY 1, 2;\n", encoding="utf-8")
    plan = [f"# {'Y test (GBO vs BOX)' if mode == 'y' else 'Parallel test'} - {cfg.get('branch', '')} - {prod} - "
            f"{', '.join(dates) or '<dates>'}", "",
            "| # | Step | Where | File |", "|---|---|---|---|",
            f"| 1 | Environments and dates: GBO **{cfg.get('gbo_environment')}**, BOX **{cfg.get('box_environment')}** | - | "
            f"`{INPUTS[mode]}` |",
            "| 2 | Extract GBO (per area) | GBO | `sql/10-GBO-<area>.sql` -> `01-evidence/<date>/gbo-<area>.csv` |",
            "| 3 | Extract BOX (per area) | BOX | `sql/20-BOX-<area>.sql` -> `01-evidence/<date>/box-<area>.csv` |",
            "| 4 | Reconcile | agent | `fe_reconcile.py compare` -> `03-recon/`, `03-results.md`"
            + (", `04-breaks.csv`" if mode == "parallel" else "") + " |",
            "| 5 | Explain every DIFF / ONLY_*: a map fix (tolerance, column), a known difference, or a defect | operator + "
            "agent | `03-results.md` |", "", "## OPEN - to answer before the extraction", ""]
    plan += [f"- {o}" for o in dict.fromkeys(opens)] or ["- none"]
    (run / "01-plan.md").write_text("\n".join(plan) + "\n", encoding="utf-8")
    print(f"wrote {run}: 01-plan.md, sql/ ({len(areas) * 2} files) - {len(set(opens))} OPEN point(s)")
    for o in dict.fromkeys(opens):
        print(f"  OPEN {o}")
    return 0


def rows_of(path: Path, d: str):
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    if rows and "RECON_DATE" in {c.upper() for c in rows[0]}:
        col = next(c for c in rows[0] if c.upper() == "RECON_DATE")
        rows = [r for r in rows if day(r[col]) == d]
    return rows


def compare(run: Path, res: Result, only=None) -> int:
    mode, cfg = read_inputs(run, res)
    if cfg is None:
        return 1
    prod = str(cfg.get("product") or "").lower()
    areas = [a for a in (cfg.get("areas") or AREAS) if a in AREAS]
    mp = Path(cfg.get("field_map") or MAP)
    mp = mp if mp.is_absolute() else ROOT / mp
    if not mp.exists():
        res.err("map-missing", str(mp), "the field map")
        return 1
    fmap = load_map(mp, prod, areas)
    ev = run / "01-evidence"
    dates = sorted(p.name for p in ev.iterdir() if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name)) \
        if ev.exists() else []
    if only:
        dates = [d for d in dates if d == only]
    if not dates:
        res.err("evidence-missing", str(ev), "no 01-evidence/<YYYY-MM-DD>/ folder with the CSVs - run pack's queries first")
        return 1
    out = run / "03-recon"
    out.mkdir(exist_ok=True)
    summary, breaks = [], []
    for d in dates:
        for a in areas:
            m = fmap[a]
            k = m.get("key") or {}
            g, b = ev / d / f"gbo-{a}.csv", ev / d / f"box-{a}.csv"
            if not g.exists() or not b.exists():
                summary.append((d, a, "missing CSV", {}))
                continue
            kg, kb = k.get("gbo_column", ""), k.get("box_column", "")
            G, B = rows_of(g, d), rows_of(b, d)
            for side, rows, kc in (("GBO", G, kg), ("BOX", B, kb)):
                if undecided(kc) or (rows and kc.upper() not in {c.upper() for c in rows[0]}):
                    res.err("key-missing", f"{d}/{side.lower()}-{a}.csv", f"key column {kc!r} not in the CSV (field map "
                            f"{prod} {a} role key)")
            if res.errors:
                return 1

            def index(rows, kc):
                col = next((c for c in (rows[0] if rows else {}) if c.upper() == kc.upper()), kc)
                ix = {}
                for r in rows:
                    ix.setdefault(str(r.get(col, "")).strip(), r)
                return ix
            gi, bi = index(G, kg), index(B, kb)
            lines, cnt = [], defaultdict(int)
            for key in sorted(set(gi) | set(bi)):
                if key not in bi or key not in gi:
                    st = "ONLY_GBO" if key not in bi else "ONLY_BOX"
                    lines.append([key, "-", "", "", "", st])
                    cnt[st] += 1
                    breaks.append((key, a, "-", d, st))
                    continue
                for f in m["fields"]:
                    gc, bc = f["gbo_column"], f["box_column"]
                    if undecided(gc) or undecided(bc):
                        continue
                    gr, br = gi[key], bi[key]
                    gcol = next((c for c in gr if c.upper() == gc.upper()), None)
                    bcol = next((c for c in br if c.upper() == bc.upper()), None)
                    if gcol is None or bcol is None:
                        st, diff, gv, bv = "NO_COLUMN", "", gr.get(gcol, ""), br.get(bcol, "")
                    else:
                        gv, bv = gr[gcol], br[bcol]
                        st, diff = same(f.get("kind", "text").strip() or "text", gv, bv, f.get("tol_abs"), f.get("tol_rel"))
                    lines.append([key, f"{gc} / {bc}", gv, bv, diff, st])
                    cnt[st] += 1
                    if st != "OK":
                        breaks.append((key, a, f"{gc} / {bc}", d, st))
            with (out / f"{d}-{a}.csv").open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["key", "field (GBO / BOX)", "GBO", "BOX", "difference", "status"])
                w.writerows(lines)
            summary.append((d, a, f"{len(set(gi) | set(bi))} keys", dict(cnt)))
    rep = [f"# Results - {'Y test' if mode == 'y' else 'parallel test'} {cfg.get('branch', '')} {prod} "
           f"({datetime.date.today().isoformat()})", "",
           "| Date | Area | Keys | OK | DIFF | ONLY_GBO | ONLY_BOX | NO_COLUMN | File |", "|---|---|---|---|---|---|---|---|---|"]
    for d, a, n, c in summary:
        rep.append(f"| {d} | {a} | {n} | {c.get('OK', 0)} | {c.get('DIFF', 0)} | {c.get('ONLY_GBO', 0)} | "
                   f"{c.get('ONLY_BOX', 0)} | {c.get('NO_COLUMN', 0)} | `03-recon/{d}-{a}.csv` |")
    rep += ["", "Every DIFF / ONLY_* / NO_COLUMN gets an explanation below (map fix, known difference, defect) before "
            "sign-off.", "", "## Explanations", ""]
    old = run / "03-results.md"
    keep = old.read_text(encoding="utf-8").split("## Explanations", 1)[1].lstrip("\n") if old.exists() and \
        "## Explanations" in old.read_text(encoding="utf-8") else ""
    old.write_text("\n".join(rep) + "\n" + keep, encoding="utf-8")
    if mode == "parallel":
        seen = defaultdict(list)
        for key, a, f, d, st in breaks:
            seen[(key, a, f)].append((d, st))
        last = dates[-1]
        with (run / "04-breaks.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["key", "area", "field", "first_seen", "last_seen", "days", "last_status", "state"])
            for (key, a, f), ds in sorted(seen.items()):
                first, lst = ds[0][0], ds[-1][0]
                state = "RESOLVED" if lst != last else ("NEW" if first == last else "OPEN")
                w.writerow([key, a, f, first, lst, len(ds), ds[-1][1], state])
    print(f"compared {len(dates)} date(s) x {len(areas)} area(s): {run / '03-results.md'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("action", choices=["pack", "compare"])
    ap.add_argument("run")
    ap.add_argument("--date", help="compare one date only (YYYY-MM-DD)")
    a = ap.parse_args(argv)
    run = Path(a.run)
    if not run.is_dir():
        print(f"not a folder: {run}", file=sys.stderr)
        return 2
    res = Result()
    if (run / ".frozen").exists():
        res.err("run-frozen", str(run), "start a new version (scripts/new_run.py)")
        return 1
    return pack(run, res) if a.action == "pack" else compare(run, res, a.date)


if __name__ == "__main__":
    sys.exit(main())
