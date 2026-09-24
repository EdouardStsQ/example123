#!/usr/bin/env python3
"""
evidence_to_sql.py — turn a query-result CSV into SQL literals, so nobody types them.

The config script may only touch BOX_FE (the applying account cannot read DEVENG — stated
2026-09-23), so sets mined from GBO have to travel inside the script as literals. This is how
they get there without transcription: straight from the CSV in 01-evidence/, and the validator
compares the SQL against the same CSV afterwards.

    # step 4 — the quote-reference array
    python3 scripts/evidence_to_sql.py list \
        runs/NY_SCH/tier2-pre/01-evidence/Q-04c-quote-ref-column-gbo.csv FK_BS

    # step 7 — this branch's accrual exceptions, approved instruments only
    python3 scripts/evidence_to_sql.py rows \
        runs/NY_SCH/tier2-pre/01-evidence/Q-06c-accrual-exceptions-emit.csv \
        FK_INSTRUMENT,FK_STRATEGY,FK_INSTRTYPE,CRITERIAL \
        --where BRANCH_PK=20007.4 --in FK_INSTRUMENT=20092.4,2.4,20.4,20111.4,20213.4,20313.4

`list` prints `sys.odcinumberlist(...)` of the column's DISTINCT values; `rows` prints a
`SELECT … FROM dual UNION ALL …` cursor body. Both print the count on stderr, for the step header.
Values must be numeric; an empty cell or `(null)` becomes NULL. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from decimal import Decimal
from pathlib import Path

NUM = re.compile(r"-?\d+(\.\d+)?")
NULLS = {"", "(null)", "null"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = [h.strip().strip('"').upper() for h in next(reader)]
        dup = {h for h in header if header.count(h) > 1}
        if dup:
            sys.exit(f"{path.name}: duplicate column(s) {sorted(dup)} — alias them in the query "
                     "(e.g. T6.PK AS BRANCH_PK) and export again")
        return [dict(zip(header, (c.strip() for c in row))) for row in reader if any(row)]


def norm(v: str) -> str | None:
    """Canonical numeric literal: '20007,40' → '20007.4', '100' → '100'. None for NULL."""
    v = (v or "").strip().strip('"')
    if v.lower() in NULLS:
        return None
    if v.count(",") == 1 and "." not in v:          # Spanish-locale export: 1,35 → 1.35
        v = v.replace(",", ".")
    if not NUM.fullmatch(v):
        sys.exit(f"non-numeric value {v!r} — this script only emits numeric literals")
    return format(Decimal(v).normalize(), "f")


def norm_safe(v: str) -> str | None:
    """norm() for callers that report problems themselves: None for NULL *and* for non-numeric."""
    try:
        return norm(v)
    except SystemExit:
        return None


def select(rows, args) -> list[dict[str, str]]:
    for cond in args.where or []:
        col, val = cond.split("=", 1)
        rows = [r for r in rows if norm(r.get(col.upper(), "")) == norm(val)]
    for cond in args.in_ or []:
        col, vals = cond.split("=", 1)
        allowed = {norm(v) for v in vals.split(",")}
        rows = [r for r in rows if norm(r.get(col.upper(), "")) in allowed]
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["list", "rows"])
    ap.add_argument("csv", type=Path)
    ap.add_argument("columns", help="one column for list; comma-separated for rows")
    ap.add_argument("--where", action="append", metavar="COL=VAL")
    ap.add_argument("--in", dest="in_", action="append", metavar="COL=V1,V2")
    a = ap.parse_args(argv)

    rows = select(read_rows(a.csv), a)
    cols = [c.strip().upper() for c in a.columns.split(",")]
    missing = [c for c in cols if rows and c not in rows[0]]
    if missing:
        sys.exit(f"{a.csv.name}: no column(s) {missing}")

    if a.mode == "list":
        vals = sorted({norm(r[cols[0]]) for r in rows} - {None}, key=float)
        print("sys.odcinumberlist(" + ", ".join(vals) + ")")
        print(f"-- {len(vals)} distinct {cols[0]} from {a.csv.name}", file=sys.stderr)
    else:
        seen, out = set(), []
        for r in rows:
            t = tuple(norm(r[c]) for c in cols)
            if t in seen:
                continue
            seen.add(t)
            items = [f"{v if v is not None else 'CAST(NULL AS NUMBER)'} AS {c}" for v, c in zip(t, cols)]
            out.append("SELECT " + ", ".join(items) + " FROM dual")
        if not out:   # an empty cursor that still compiles and names its columns
            out = ["SELECT " + ", ".join(f"CAST(NULL AS NUMBER) AS {c}" for c in cols) + " FROM dual WHERE 1 = 0"]
            print(out[0])
        else:
            print("\n    UNION ALL ".join(out))
        print(f"-- {len(seen)} row(s) from {a.csv.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
