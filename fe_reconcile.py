#!/usr/bin/env python3
"""
fe_reconcile.py - GBO vs BOX FE reconciliation: the "Y" test and the parallel test [operator, 2026-10-09; basics].

    python3 scripts/fe_reconcile.py pack    runs/<BRANCH>/<tier>-<env>/tests/<y|parallel>/<name>_<YYYYMMDD>_<n>/
    python3 scripts/fe_reconcile.py compare runs/<BRANCH>/<tier>-<env>/tests/<y|parallel>/<run>/ [--date YYYY-MM-DD]
    python3 scripts/fe_reconcile.py files <gbo.csv>[,<gbo2.csv>...] <box.csv> --key FRONT_ID[,COL...] --out <result.csv>

Skills `box-fe-y-test` (a few trades, one or a few dates, field by field) and `box-fe-parallel-test` (the whole
branch, every day of a period, breaks followed day to day). Reads <run>/y-test-inputs.json or
parallel-test-inputs.json and the field map docs/reference/gbo-box-fe-field-map.csv (per product and area - deal,
financial, mtm: the GBO and BOX tables, the key, the date column, the fields, their kind and tolerance). No agent
touches a database: `pack` writes the extraction queries, the operator runs them and returns each output as a CSV,
`compare` reconciles the CSVs.

  pack     01-plan.md (steps + OPEN points), sql/10-GBO-<product>-<area>.sql, sql/20-BOX-<product>-<area>.sql for
           every product the operator chose (`products`: one, several, all; trades per product)
           (evidence expected at 01-evidence/<date>/gbo-<product>-<area>.csv and box-<product>-<area>.csv)
  pack also writes sql/30-BOX-trace.sql (per product: where each trade stops in BOX: RAW -> deal data -> MtM -> product tables,
           with the INSTRUMENT text check) and sql/70-BOX-diagnose.sql (the procedures of the groups and their filters)
           - the lessons of the technical test [operator, 2026-10-13]
  files    two CSVs compared directly (the technical test's optional GBO vs BOX financial data): the columns common
           to both, except ids and audit columns, numbers within 0.01
  compare  03-recon/<date>-<product>-<area>.csv (key, field, GBO, BOX, difference, status) and 03-results.md;
           parallel: 04-breaks.csv - every break with first / last date seen, days open, NEW / OPEN / RESOLVED

An area with no `field` row compares every column common to both CSVs (auto, as `files`). A `link` row gives the
deal table that carries the key when the area's table does not.

The GBO / BOX trade key [operator, 2026-11-24 - ADR 0029]: GBO's DEAL_ID and BOX's DEAL_ID differ, and so do the two
FRONT_IDs (GBO 40603.35 / front 26420182 is BOX 1680634.513 / front 1680634). The link between them is the AUKI
migration crosswalk BOX_MIG.T_BOX_AUKI_MIG_DEALS_S: REGISTRY = GBO DEAL_ID, FK_AUKI_ID = BOX DEAL_ID (PROCESS_DATE,
FK_BRANCH_ORIGIN = the GBO branch). An area with an `xwalk` row is keyed on GBO_DEAL_ID on both sides: GBO's own
DEAL_ID, BOX's DEAL_ID translated through the crosswalk (the latest row per BOX deal up to the last date, for the
input `gbo_branch`), both as text with a '.' decimal (TO_CHAR ... 'TM9'); GBO's rows restricted to the branch through
the area's GBO deal table (the `link` row) or its own FK_BRANCH. pack then also writes sql/05-crosswalk-checks.sql
(one GBO id per BOX deal and back; per product and date: BOX deals mapped to the branch, GBO deals with a crosswalk
row; with trades, the BOX DEAL_ID / FRONT_ID of each - the trace (30) takes BOX FRONT_IDs, input `box_front_ids`).
FRONT_ID, BACK_ID, REFERENCE_ACCOUNTING and FK_BRANCH are never compared (they differ by design). A key value found
twice in one CSV is counted (`Duplicate keys` in 03-results.md) - only its first row is compared.
Keys may be composite (`FRONT_ID,CURRENCY`). The GBO and BOX product codes differ (docs/reference/gbo-box-product-
tables.csv): a BOX product made of several GBO products (OTC = OB / OE / OF / OI / OS, FX = SP / NDS / FP / FM) gets
one GBO query per GBO table (`…-<area>-<GBO code>`), read together by compare. Status per key and field: OK, DIFF (beyond the tolerance), ONLY_GBO, ONLY_BOX (the trade on one side only),
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
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fe_test_sql as T  # noqa: E402
MAP = ROOT / "docs/reference/gbo-box-fe-field-map.csv"
INPUTS = {"y": "y-test-inputs.json", "parallel": "parallel-test-inputs.json"}
AREAS = ("deal", "financial", "mtm")
SKIP_AUTO = re.compile(r"^(PK|FK_OWNER_OBJ|FK_PARENT|FK_EXTENSION|DEAL_ID|GUID|REPLICIND|LSTMNT.*|RECON_DATE|"
                       r"CREATED.*|MODIFIED.*|USER.*|TIMESTAMP.*|FRONT_ID|BACK_ID|REFERENCE_ACCOUNTING|FK_BRANCH|"
                       r"GBO_DEAL_ID)$", re.I)
# the AUKI migration crosswalk, GBO DEAL_ID <-> BOX DEAL_ID [operator, 2026-11-24 - ADR 0029]
XW = {"table": "BOX_MIG.T_BOX_AUKI_MIG_DEALS_S", "box_id": "FK_AUKI_ID", "gbo_id": "REGISTRY",
      "date": "PROCESS_DATE", "branch": "FK_BRANCH_ORIGIN"}
DOT = "'TM9', 'NLS_NUMERIC_CHARACTERS=''.,'''"          # a number as text with a '.' decimal, whatever the session


def as_text(expr: str) -> str:
    return f"TO_CHAR({expr}, {DOT})"


def xw_subquery(branch: str, last: str) -> str:
    """The crosswalk rows of the branch: the latest per BOX deal up to the last date compared (x.FK_INSTRUMENT, the
    GBO instrument, can filter a product in BOX's shared deal table)."""
    return (f"SELECT {XW['box_id']}, {XW['gbo_id']}, FK_INSTRUMENT FROM (SELECT {XW['box_id']}, {XW['gbo_id']}, "
            f"FK_INSTRUMENT, ROW_NUMBER() OVER "
            f"(PARTITION BY {XW['box_id']} ORDER BY {XW['date']} DESC) RN FROM {XW['table']} WHERE {XW['branch']} = "
            f"{branch} AND {XW['date']} < {last} + 1) WHERE RN = 1")


def kind_of(values) -> str:
    vals = [v for v in values if str(v or "").strip()]
    if vals and all(num(v) is not None for v in vals):
        return "amount"
    if vals and all(re.match(r"(\d{4}-\d{2}-\d{2}|\d{1,2}[/.-](\d{1,2}|[A-Za-z]{3})[/.-]\d{2,4})", str(v).strip())
                    for v in vals):
        return "date"
    return "text"


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
    """{area: {table: row, key: row, date: row, filter: row, link: row, fields: [rows], tables: [rows], links: [rows]}}
    for the product. A BOX product with several GBO products (OTC -> OB / OE / OF / OI / OS) has one `table` (and
    `link`) row per GBO table: `tables` / `links` keep them in order, `table` / `link` are the first."""
    out = {a: {"fields": [], "tables": [], "links": []} for a in areas}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if r["product"].strip().lower() != product or r["area"].strip() not in out:
            continue
        a, role = r["area"].strip(), r["role"].strip()
        if role == "field":
            out[a]["fields"].append(r)
        elif role in ("table", "link"):
            out[a][role + "s"].append(r)
            out[a].setdefault(role, r)
        else:
            out[a][role] = r
    return out


def gbo_suffix(m: dict, i: int) -> str:
    """'' with one GBO table, else '-<GBO code>' (T_PGT_OBFINANCST_S -> -OB)."""
    if len(m["tables"]) <= 1:
        return ""
    return "-" + (T.gbo_code_of(m["tables"][i].get("gbo_table", "")) or str(i + 1))


def read_inputs(run: Path, res: Result):
    found = [(m, run / f) for m, f in INPUTS.items() if (run / f).exists()]
    if not found:
        res.err("inputs-missing", str(run), f"{' or '.join(INPUTS.values())} - copy the skill's template there")
        return None, None
    mode, p = found[0]
    cfg = json.loads(p.read_text(encoding="utf-8-sig"))
    return mode, cfg


def products_of(cfg) -> list:
    """The products of the run, as the operator chose them (one, several, all) - `products` (list) or `product`."""
    v = cfg.get("products") or cfg.get("product") or []
    return [str(x).lower() for x in (v if isinstance(v, list) else [v]) if not undecided(x)]


def per(cfg, key, prod, default=None):
    """A value given per product ({product: value}) or once for all."""
    v = cfg.get(key)
    if isinstance(v, dict):
        v = v.get(prod)
    return default if undecided(v) else v


def trades_of(cfg, prod, n_products: int) -> list:
    v = cfg.get("trades")
    if isinstance(v, dict):
        v = v.get(prod) or []
    elif n_products > 1:
        v = []                                     # a flat list is ambiguous with several products
    return [t for t in (v or []) if not undecided(t)]


def pack(run: Path, res: Result) -> int:
    mode, cfg = read_inputs(run, res)
    if cfg is None:
        return 1
    opens = []
    prods = products_of(cfg)
    if not prods:
        opens.append("`products` - the products to compare, as the operator chooses (one, several, all): "
                     + ", ".join(T.PRODUCT_CODE))
    areas = [a for a in (cfg.get("areas") or AREAS) if a in AREAS]
    mp = Path(cfg.get("field_map") or MAP)
    mp = mp if mp.is_absolute() else ROOT / mp
    if not mp.exists():
        res.err("map-missing", str(mp), "the field map (docs/reference/gbo-box-fe-field-map.csv)")
        return 1
    for k, what in (("gbo_environment", "the GBO environment holding the target's data for the same dates"),
                    ("box_environment", "the BOX environment (NY_SCH: DGBOUS DEV, IGBOUSIB PRE Paralelo)")):
        if undecided(cfg.get(k)):
            opens.append(f"`{k}` - {what}")
    dates = [d for d in (cfg.get("dates") or []) if not undecided(d)]
    if not dates:
        opens.append("`dates` - the date(s) to compare, YYYY-MM-DD")
    dl = ", ".join(f"DATE '{d}'" for d in dates) or "DATE '<date>'"
    last = f"DATE '{max(dates)}'" if dates else "DATE '<date>'"
    branch = cfg.get("gbo_branch")
    branch = "<gbo_branch>" if undecided(branch) else str(branch)
    sql = run / "sql"
    sql.mkdir(exist_ok=True)
    nfiles = 0
    xchecks = []                                   # sql/05-crosswalk-checks.sql, per product
    for prod in prods:
        fmap = load_map(mp, prod, areas)
        trades = trades_of(cfg, prod, len(prods))
        xw_used = any(fmap[a].get("xwalk") for a in areas)
        if xw_used and branch.startswith("<"):
            opens.append("`gbo_branch` - the GBO branch PK of the target (NY_SCH: 20007.4): the crosswalk's "
                         "FK_BRANCH_ORIGIN and GBO's FK_BRANCH")
        if mode == "y" and not trades:
            opens.append(f"`trades.{prod}` - the {prod} trades to compare (FRONT_ID)"
                         + (" - with several products give them per product: {\"depos\": [...], \"irs\": [...]}"
                            if len(prods) > 1 else ""))
        for a in areas:
            m = fmap[a]
            t, k, dt = m.get("table") or {}, m.get("key") or {}, m.get("date") or {}
            flt = m.get("filter") or {}
            if not t:
                opens.append(f"field map - {prod} `{a}`: no table row")
                continue
            sides = [("gbo", "10-GBO", i) for i in range(max(1, len(m["tables"])))] + [("box", "20-BOX", 0)]
            for side, tag, gi_ in sides:
                t = m["tables"][gi_] if m["tables"] else {}
                sfx = gbo_suffix(m, gi_) if side == "gbo" else ""
                tab, kc, dc = t.get(f"{side}_table", ""), k.get(f"{side}_column", ""), dt.get(f"{side}_column", "")
                for v, what in ((tab, "table"), (kc, "key column"), (dc, "date column")):
                    if undecided(v):
                        opens.append(f"field map - {prod} `{a}` {side.upper()} {what}")
                if "<" in kc:
                    opens.append(f"field map - {prod} `{a}` {side.upper()} key column(s) {kc}")
                cols = [f[f"{side}_column"] for f in m["fields"] if not undecided(f[f"{side}_column"])]
                lk = (m["links"][gi_] if gi_ < len(m["links"]) else m.get("link")) or {}
                ltab, lcol = lk.get(f"{side}_table", ""), lk.get(f"{side}_column", "")
                xw = m.get("xwalk") or {}
                if not cols and not ltab:
                    opens.append(f"field map - {prod} `{a}` {side.upper()}: no field rows - every common column is "
                                 "compared (auto); add `field` rows to name pairs with different names or tolerances")
                cond = [f"TRUNC({dc or '<date column>'}) IN ({dl})"]
                if trades:
                    cond.append(f"{kc or '<key column>'} IN ({qlist(trades)})")
                extra = per(cfg, f"{side}_filter", prod) or flt.get(f"{side}_column")
                if not undecided(extra):
                    cond.append(f"({extra})")
                env = cfg.get(f"{side}_environment") or f"<{side} environment>"
                fn = sql / f"{tag}-{prod}-{a}{sfx}.sql"
                head = (f"-- {side.upper()} ({env}) - {prod} {a}{' ' + sfx[1:] if sfx else ''}: export as CSV (with header) "
                        f"to 01-evidence/<date>/{side}-{prod}-{a}{sfx}.csv\n-- (one file per date, or one with all dates: "
                        "compare splits it by RECON_DATE)" + ("; compare reads every gbo-" + f"{prod}-{a}-*.csv together"
                                                            if sfx else "") + ".\n")
                if xw:
                    # GBO DEAL_ID <-> BOX DEAL_ID through the AUKI migration crosswalk (ADR 0029)
                    k1 = kc.split(",")[0].strip() or "GBO_DEAL_ID"
                    idc = xw.get(f"{side}_column") or "DEAL_ID"
                    if xw.get("box_table", "").strip().upper() != XW["table"]:
                        opens.append(f"field map - {prod} `{a}` xwalk: box_table {xw.get('box_table')!r}, expected "
                                     f"{XW['table']}")
                    if side == "gbo":
                        gid = f"f.{idc}"
                        own = (f"f.{idc} IN (SELECT {lcol or 'DEAL_ID'} FROM {ltab} WHERE FK_BRANCH = {branch} AND "
                               f"TRUNC({dc}) IN ({dl}))" if ltab and not undecided(ltab) else f"f.FK_BRANCH = {branch}")
                        body = (f"SELECT TRUNC(f.{dc}) RECON_DATE, {as_text(gid)} {k1}, f.*\nFROM {tab} f\n"
                                f"WHERE TRUNC(f.{dc}) IN ({dl})\nAND {own}")
                        note = (f"-- Keyed on {k1} = GBO's own {idc}; the branch's rows through "
                                f"{ltab if ltab and not undecided(ltab) else 'FK_BRANCH'} [ADR 0029].\n")
                    else:
                        gid = f"x.{XW['gbo_id']}"
                        body = (f"SELECT TRUNC(f.{dc}) RECON_DATE, {as_text(gid)} {k1}, f.*\nFROM {tab} f\n"
                                f"JOIN ({xw_subquery(branch, last)}) x\n  ON x.{XW['box_id']} = f.{idc}\n"
                                f"WHERE TRUNC(f.{dc}) IN ({dl})")
                        note = (f"-- Keyed on {k1} = the GBO DEAL_ID of each BOX {idc}, through {XW['table']} "
                                f"({XW['box_id']} -> {XW['gbo_id']}) [operator, 2026-11-24 - ADR 0029].\n")
                    if trades:
                        body += f"\nAND {as_text(gid)} IN ({qlist(trades)})"
                    if not undecided(extra):
                        body += f"\nAND ({extra})"
                    fn.write_text(head + note + body + "\nORDER BY 1, 2;\n", encoding="utf-8")
                    if side == "box":
                        gdeal = ((m.get("link") or {}).get("gbo_table") if a == "financial"
                                 else (m.get("table") or {}).get("gbo_table"))
                        xchecks.append((prod, a, tab, idc, dc, gdeal or "", trades))
                elif ltab and not undecided(ltab):
                    # the key lives in the deal table: f.* joined to it on the link column (e.g. DEAL_ID)
                    lw = f" WHERE {kc} IN ({qlist(trades)})" if trades else ""
                    fn.write_text(
                        head + f"-- {kc} through {ltab} on {lcol} [field map, role link, {lk.get('status', '')}]; every "
                        f"column of {tab}\n-- (auto compare when the map has no field rows).\n"
                        f"SELECT TRUNC(f.{dc}) RECON_DATE, l.{kc}, f.*\nFROM {tab} f\n"
                        f"JOIN (SELECT DISTINCT {lcol}, {kc} FROM {ltab}{lw}) l ON l.{lcol} = f.{lcol}\n"
                        f"WHERE TRUNC(f.{dc}) IN ({dl})" + (f" AND ({extra})" if not undecided(extra) else "")
                        + "\nORDER BY 1, 2;\n", encoding="utf-8")
                else:
                    sel = ", ".join(dict.fromkeys([f"TRUNC({dc or '<date column>'}) RECON_DATE", kc or "<key column>",
                                                   *cols]))
                    fn.write_text(head + f"-- Table / columns from the field map (status: {t.get('status', '')}).\n"
                                  f"SELECT {sel}\nFROM {tab or '<table>'}\nWHERE {' AND '.join(cond)}\nORDER BY 1, 2;\n",
                                  encoding="utf-8")
                nfiles += 1
        trace_ids = trades
        if trades and xw_used:
            trace_ids = [x for x in (per(cfg, "box_front_ids", prod) or []) if not undecided(x)]
            if not trace_ids:
                opens.append(f"`box_front_ids.{prod}` - the trades' BOX FRONT_IDs for the trace (30): "
                             "sql/05-crosswalk-checks.sql part 4 lists them")
        if trace_ids and dates:
            trades = trace_ids
            dlt = f"DATE '{dates[0]}'"
            ig = per(cfg, "insert_group", prod, T.INSERT_GROUPS.get(prod, ("<insert group>",))[0])
            ri = per(cfg, "raw_instrument", prod, T.RAW_INSTRUMENT.get(prod, "<the RAW INSTRUMENT text>"))
            if str(ig).startswith("<") or str(ri).startswith("<"):
                opens.append(f"`insert_group.{prod}` / `raw_instrument.{prod}` - the product's insert event group and "
                             "the RAW INSTRUMENT text the import procedures expect")
            chk = T.stage_checks(trades, dlt, prod, ig, "the product's insert group")
            (sql / f"30-BOX-trace-{prod}.sql").write_text(
                f"-- BOX ({cfg.get('box_environment')}) - {prod}: where each trade stops, {dates[0]} [lesson of the "
                "technical test,\n-- 2026-10-13]: run when a trade is ONLY_GBO or a BOX CSV is empty. RAW first, then "
                "each step's rows.\n"
                f"SELECT 'RAW DEAL' STAGE, FRONT_ID, COUNT(*) N FROM BOX_FE.T_BOX_RAW_DEAL_DATA_S WHERE FRONT_ID IN "
                f"({qlist(trades)}) AND TRUNC(PROCESSDATE) = {dlt} GROUP BY FRONT_ID;\n"
                f"SELECT 'RAW MARKET' STAGE, FRONT_ID, COUNT(*) N FROM BOX_FE.T_BOX_RAW_MARKET_DATA_S WHERE FRONT_ID IN "
                f"({qlist(trades)}) AND TRUNC(PROCESSDATE) = {dlt} GROUP BY FRONT_ID;\n\n"
                + "\n".join(f"-- ===== step {g} =====\n{chk[g]}" for g in chk)
                + "\n" + T.instrument_check(trades, dlt, ri), encoding="utf-8")
            (sql / f"70-BOX-diagnose-{prod}.sql").write_text(T.diagnose(["2629.65", "2632.65", str(ig), "2608.65", "2389.65"]),
                                                             encoding="utf-8")
    if xchecks:
        xs = [f"-- The AUKI migration crosswalk {XW['table']} ({XW['box_id']} = BOX DEAL_ID, {XW['gbo_id']} = GBO "
              f"DEAL_ID) for branch {branch} [ADR 0029].\n-- Run in the BOX environment ({cfg.get('box_environment')}); "
              "part 3 also reads GBO's tables - only where GBO and BOX are the same\n-- database (PRE Paralelo). "
              "Save each result as 01-evidence/05-crosswalk-<part>.csv (counts only, except part 4).\n",
              "-- 1. one GBO id per BOX deal, one BOX deal per GBO id (expected 0 and 0)",
              f"SELECT 'BOX deal -> several GBO ids' CHECK_NAME, COUNT(*) N FROM (SELECT {XW['box_id']} FROM {XW['table']} "
              f"WHERE {XW['branch']} = {branch} AND {XW['date']} < {last} + 1 GROUP BY {XW['box_id']} HAVING "
              f"COUNT(DISTINCT {XW['gbo_id']}) > 1)\nUNION ALL\nSELECT 'GBO deal -> several BOX deals', COUNT(*) FROM "
              f"(SELECT {XW['gbo_id']} FROM {XW['table']} WHERE {XW['branch']} = {branch} AND {XW['date']} < {last} + 1 "
              f"GROUP BY {XW['gbo_id']} HAVING COUNT(DISTINCT {XW['box_id']}) > 1);", "",
              "-- 2. BOX: per product and date, the deals of the table and those the crosswalk maps to the branch"]
        for prod, a, tab, idc, dc, gdeal, trades in xchecks:
            xs.append(f"SELECT '{prod} {a}' PRODUCT, TRUNC(f.{dc}) RECON_DATE, COUNT(DISTINCT f.{idc}) BOX_DEALS_ALL_BRANCHES, "
                      f"COUNT(DISTINCT x.{XW['box_id']}) MAPPED_TO_BRANCH\nFROM {tab} f LEFT JOIN "
                      f"({xw_subquery(branch, last)}) x ON x.{XW['box_id']} = f.{idc}\nWHERE TRUNC(f.{dc}) IN ({dl}) "
                      "GROUP BY TRUNC(f.{dc});".replace("{dc}", dc))
        xs += ["", "-- 3. GBO: per product and date, the branch's deals and those with a crosswalk row (the rest can only "
               "be ONLY_GBO)"]
        for prod, a, tab, idc, dc, gdeal, trades in xchecks:
            if gdeal and not undecided(gdeal):
                xs.append(f"SELECT '{prod}' PRODUCT, TRUNC(g.DDATE) RECON_DATE, COUNT(DISTINCT g.DEAL_ID) GBO_DEALS, "
                          f"COUNT(DISTINCT x.{XW['gbo_id']}) WITH_CROSSWALK_ROW\nFROM {gdeal} g LEFT JOIN {XW['table']} x "
                          f"ON x.{XW['gbo_id']} = g.DEAL_ID AND x.{XW['branch']} = {branch} AND x.{XW['date']} < {last} + 1\n"
                          f"WHERE g.FK_BRANCH = {branch} AND TRUNC(g.DDATE) IN ({dl}) GROUP BY TRUNC(g.DDATE);")
        tr = [(p_, t_) for p_, _a, _t, _i, _d, _g, t_ in xchecks if t_]
        if tr:
            xs += ["", "-- 4. the trades: GBO DEAL_ID -> BOX DEAL_ID and BOX FRONT_ID (the trace's input box_front_ids)"]
            for p_, t_ in tr:
                xs.append(f"SELECT '{p_}' PRODUCT, {as_text('x.' + XW['gbo_id'])} GBO_DEAL_ID, x.{XW['box_id']} BOX_DEAL_ID, "
                          f"d.FRONT_ID BOX_FRONT_ID\nFROM ({xw_subquery(branch, last)}) x LEFT JOIN (SELECT DISTINCT DEAL_ID, "
                          f"FRONT_ID FROM BOX_FE.T_BOX_DATADEAL_S WHERE TRUNC(DDATE) IN ({dl})) d ON d.DEAL_ID = "
                          f"x.{XW['box_id']}\nWHERE {as_text('x.' + XW['gbo_id'])} IN ({qlist(t_)});")
        seen_, body_ = set(), []
        for ln in xs:                               # the same query for two areas once; blank lines kept
            if ln and ln in seen_:
                continue
            seen_.add(ln)
            body_.append(ln)
        (sql / "05-crosswalk-checks.sql").write_text("\n".join(body_) + "\n", encoding="utf-8")
        nfiles += 1
    plan = [f"# {'Y test (GBO vs BOX)' if mode == 'y' else 'Parallel test'} - {cfg.get('branch', '')} - "
            f"{', '.join(prods) or '<products>'} - {', '.join(dates) or '<dates>'}", "",
            "| # | Step | Where | File |", "|---|---|---|---|",
            f"| 1 | Products, environments, dates: GBO **{cfg.get('gbo_environment')}**, BOX "
            f"**{cfg.get('box_environment')}** | - | `{INPUTS[mode]}` |",
            "| 2 | The BOX side of each product checked step by step first (technical-test flow: RAW, event groups, the "
            "checks after the key steps) - a BOX side not checked is not compared | BOX | skill `box-fe-technical-test` |",
            *(["| 2b | The GBO / BOX trade key: the crosswalk checks (one id each way; how many deals map) - before "
               "reading any ONLY_GBO / ONLY_BOX | BOX | `sql/05-crosswalk-checks.sql` |"] if xchecks else []),
            "| 3 | Extract GBO (per product and area) | GBO | `sql/10-GBO-<product>-<area>.sql` -> "
            "`01-evidence/<date>/gbo-<product>-<area>.csv` |",
            "| 4 | Extract BOX (per product and area) | BOX | `sql/20-BOX-<product>-<area>.sql` -> "
            "`01-evidence/<date>/box-<product>-<area>.csv` |",
            "| 4b | A trade missing or empty on the BOX side: where it stops and why | BOX | `sql/30-BOX-trace-<product>.sql`, "
            "`sql/70-BOX-diagnose-<product>.sql` |",
            "| 5 | Reconcile | agent | `fe_reconcile.py compare` -> `03-recon/`, `03-results.md`"
            + (", `04-breaks.csv`" if mode == "parallel" else "") + " |",
            "| 6 | Explain every DIFF / ONLY_*: a map fix (tolerance, column), a known difference, or a defect | operator + "
            "agent | `03-results.md` |", "", "## OPEN - to answer before the extraction", ""]
    plan += [f"- {o}" for o in dict.fromkeys(opens)] or ["- none"]
    (run / "01-plan.md").write_text("\n".join(plan) + "\n", encoding="utf-8")
    print(f"wrote {run}: 01-plan.md, sql/ ({nfiles} extraction files) - {len(set(opens))} OPEN point(s)")
    for o in dict.fromkeys(opens):
        print(f"  OPEN {o}")
    return 0


def rows_of(path: Path, d: str):
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    if rows and "RECON_DATE" in {c.upper() for c in rows[0]}:
        col = next(c for c in rows[0] if c.upper() == "RECON_DATE")
        rows = [r for r in rows if day(r[col]) == d]
    return rows


class Index(dict):
    dups = 0


def key_part(v) -> str:
    """A key value as text; a plain number in either decimal style the same ('40603,35' = '40603.35')."""
    s = str(v or "").strip()
    if re.fullmatch(r"-?\d+([.,]\d+)?", s):
        try:
            return format(Decimal(s.replace(",", ".")).normalize(), "f")
        except InvalidOperation:
            return s
    return s


def index(rows, kc):
    """{key: row}; a composite key (A,B) joins the values with '|'. A key seen again is counted (.dups), the first
    row kept."""
    cols = [next((c for c in (rows[0] if rows else {}) if c.upper() == x.strip().upper()), x.strip())
            for x in kc.split(",")]
    ix = Index()
    for r in rows:
        k = "|".join(key_part(r.get(c, "")) for c in cols)
        if k in ix:
            ix.dups += 1
        else:
            ix[k] = r
    return ix


def auto_fields(G, B, kg, kb):
    """The columns common to both CSVs (same name), except keys, ids and audit columns; kind from the values."""
    keys = {x.strip().upper() for x in (kg + "," + kb).split(",")}
    gc = {c.upper(): c for c in (G[0] if G else {})}
    bc = {c.upper(): c for c in (B[0] if B else {})}
    out = []
    for u in [c for c in gc if c in bc and c not in keys and not SKIP_AUTO.match(c)]:
        kind = kind_of([r.get(gc[u]) for r in G] + [r.get(bc[u]) for r in B])
        out.append({"gbo_column": gc[u], "box_column": bc[u], "kind": kind, "tol_abs": "0.01" if kind == "amount" else "",
                    "tol_rel": ""})
    return out


def files(gpaths, bpath: Path, key: str, out: Path, res: Result) -> int:
    """gpaths: one GBO CSV or several (a BOX product made of several GBO products: OTC, FX) read together."""
    gpaths = [Path(x) for x in (gpaths if isinstance(gpaths, list) else str(gpaths).split(","))]
    for pth in (*gpaths, bpath):
        if not pth.exists():
            res.err("evidence-missing", str(pth), "the CSV to compare")
            return 1
    G = [r for g in gpaths for r in csv.DictReader(g.open(encoding="utf-8-sig"))]
    B = list(csv.DictReader(bpath.open(encoding="utf-8-sig")))
    for side, rows in (("GBO", G), ("BOX", B)):
        if rows and any(x.strip().upper() not in {c.upper() for c in rows[0]} for x in key.split(",")):
            res.err("key-missing", f"{side} {rows and list(rows[0])[:5]}", f"key {key!r} not in the CSV")
            return 1
    gi, bi = index(G, key), index(B, key)
    cnt, lines = defaultdict(int), []
    fields = auto_fields(G, B, key, key)                  # once, not per key (a 10k-row CSV took minutes)
    for k_ in sorted(set(gi) | set(bi)):
        if k_ not in gi or k_ not in bi:
            st = "ONLY_GBO" if k_ not in bi else "ONLY_BOX"
            lines.append([k_, "-", "", "", "", st])
            cnt[st] += 1
            continue
        for f in fields:
            gv, bv = gi[k_].get(f["gbo_column"], ""), bi[k_].get(f["box_column"], "")
            st, diff = same(f["kind"], gv, bv, f["tol_abs"], "")
            lines.append([k_, f["gbo_column"], gv, bv, diff, st])
            cnt[st] += 1
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "column", "GBO", "BOX", "difference", "status"])
        w.writerows(lines)
    only = sorted({c.upper() for c in (G[0] if G else {})} ^ {c.upper() for c in (B[0] if B else {})})
    print(f"compared {len(set(gi) | set(bi))} key(s): " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items()))
          + f" -> {out}" + (f"\n  columns on one side only (not compared): {', '.join(only)}" if only else "")
          + (f"\n  duplicate keys (first row kept): GBO {gi.dups}, BOX {bi.dups}" if gi.dups or bi.dups else ""))
    return 0


def compare(run: Path, res: Result, only=None) -> int:
    mode, cfg = read_inputs(run, res)
    if cfg is None:
        return 1
    prods = products_of(cfg)
    areas = [a for a in (cfg.get("areas") or AREAS) if a in AREAS]
    mp = Path(cfg.get("field_map") or MAP)
    mp = mp if mp.is_absolute() else ROOT / mp
    if not mp.exists():
        res.err("map-missing", str(mp), "the field map")
        return 1
    fmaps = {p_: load_map(mp, p_, areas) for p_ in prods}
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
      for prod in prods:
        for a in areas:
            m = fmaps[prod][a]
            k = m.get("key") or {}
            gs = sorted((ev / d).glob(f"gbo-{prod}-{a}.csv")) + sorted((ev / d).glob(f"gbo-{prod}-{a}-*.csv"))
            b = ev / d / f"box-{prod}-{a}.csv"
            if not gs or not b.exists():
                summary.append((d, prod, a, "missing CSV", {}))
                continue
            kg, kb = k.get("gbo_column", ""), k.get("box_column", "")
            G, B = [r for g in gs for r in rows_of(g, d)], rows_of(b, d)
            for side, rows, kc in (("GBO", G, kg), ("BOX", B, kb)):
                if undecided(kc) or (rows and any(x.strip().upper() not in {c.upper() for c in rows[0]}
                                                  for x in kc.split(","))):
                    res.err("key-missing", f"{d}/{side.lower()}-{prod}-{a}.csv", f"key column {kc!r} not in the CSV (field map "
                            f"{prod} {a} role key)")
            if res.errors:
                return 1

            gi, bi = index(G, kg), index(B, kb)
            fields = m["fields"] or auto_fields(G, B, kg, kb)
            lines, cnt = [], defaultdict(int)
            for key in sorted(set(gi) | set(bi)):
                if key not in bi or key not in gi:
                    st = "ONLY_GBO" if key not in bi else "ONLY_BOX"
                    lines.append([key, "-", "", "", "", st])
                    cnt[st] += 1
                    breaks.append((key, prod, a, "-", d, st))
                    continue
                for f in fields:
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
                        breaks.append((key, prod, a, f"{gc} / {bc}", d, st))
            with (out / f"{d}-{prod}-{a}.csv").open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["key", "field (GBO / BOX)", "GBO", "BOX", "difference", "status"])
                w.writerows(lines)
            summary.append((d, prod, a, f"{len(set(gi) | set(bi))} keys", dict(cnt, DUPS=f"{gi.dups} / {bi.dups}")))
    rep = [f"# Results - {'Y test' if mode == 'y' else 'parallel test'} {cfg.get('branch', '')} {', '.join(prods)} "
           f"({datetime.date.today().isoformat()})", "",
           "| Date | Product | Area | Keys | OK | DIFF | ONLY_GBO | ONLY_BOX | NO_COLUMN | Duplicate keys GBO / BOX | File |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for d, pr_, a, n, c in summary:
        rep.append(f"| {d} | {pr_} | {a} | {n} | {c.get('OK', 0)} | {c.get('DIFF', 0)} | {c.get('ONLY_GBO', 0)} | "
                   f"{c.get('ONLY_BOX', 0)} | {c.get('NO_COLUMN', 0)} | {c.get('DUPS', '-')} | `03-recon/{d}-{pr_}-{a}.csv` |")
    rep += ["", "Every DIFF / ONLY_* / NO_COLUMN gets an explanation below (map fix, known difference, defect) before "
            "sign-off.", "", "## Explanations", ""]
    old = run / "03-results.md"
    keep = old.read_text(encoding="utf-8").split("## Explanations", 1)[1].lstrip("\n") if old.exists() and \
        "## Explanations" in old.read_text(encoding="utf-8") else ""
    old.write_text("\n".join(rep) + "\n" + keep, encoding="utf-8")
    if mode == "parallel":
        seen = defaultdict(list)
        for key, pr_, a, f, d, st in breaks:
            seen[(key, pr_, a, f)].append((d, st))
        last = dates[-1]
        with (run / "04-breaks.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["key", "product", "area", "field", "first_seen", "last_seen", "days", "last_status", "state"])
            for (key, pr_, a, f), ds in sorted(seen.items()):
                first, lst = ds[0][0], ds[-1][0]
                state = "RESOLVED" if lst != last else ("NEW" if first == last else "OPEN")
                w.writerow([key, pr_, a, f, first, lst, len(ds), ds[-1][1], state])
    print(f"compared {len(dates)} date(s) x {len(prods)} product(s) x {len(areas)} area(s): {run / '03-results.md'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("action", choices=["pack", "compare", "files"])
    ap.add_argument("run", help="the run folder (pack / compare) or the GBO CSV(s), comma-separated (files)")
    ap.add_argument("box_csv", nargs="?", help="files: the BOX CSV")
    ap.add_argument("--date", help="compare one date only (YYYY-MM-DD)")
    ap.add_argument("--key", default="FRONT_ID", help="files: the key column(s), comma-separated")
    ap.add_argument("--out", help="files: the result CSV")
    a = ap.parse_args(argv)
    res = Result()
    if a.action == "files":
        if not a.box_csv or not a.out:
            print("files <gbo.csv> <box.csv> --key <col[,col]> --out <result.csv>", file=sys.stderr)
            return 2
        return files(a.run.split(","), Path(a.box_csv), a.key, Path(a.out), res)
    run = Path(a.run)
    if not run.is_dir():
        print(f"not a folder: {run}", file=sys.stderr)
        return 2
    if (run / ".frozen").exists():
        res.err("run-frozen", str(run), "start a new version (scripts/new_run.py)")
        return 1
    return pack(run, res) if a.action == "pack" else compare(run, res, a.date)


if __name__ == "__main__":
    sys.exit(main())
