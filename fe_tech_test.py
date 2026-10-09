#!/usr/bin/env python3
"""
fe_tech_test.py - the BOX FE technical test pack for one instrument in a DEV environment [operator, 2026-10-09].

    python3 scripts/fe_tech_test.py runs/<BRANCH>/<tier>-<env>/tests/technical/<name>_<YYYYMMDD>_<n>/

Skill `box-fe-technical-test`. Reads <run>/tech-test-inputs.json (template: skills/box-fe-technical-test/
tech-test-inputs.example.json), docs/reference/box-fe-static-aliases.csv and, when given, the box-fe-jobs-agent run
whose db.conf.proposal gives the event groups, instruments and labels of the run card. Writes, for the operator
(no agent touches a database):

  01-plan.md                     the steps of the technical test, in order, with what to run where and the OPEN points
  02-run-card.md                 the event groups to run from SIGOM (GBO > SYS > Process > Batch > Run Batch), in the
                                 order of the Financial Process, with Branch / Event Group / Process Date / Instrument /
                                 Label per line, and the bypass steps where they go
  sql/10-PROD-raw-extract.sql    the RAW rows of the test trades (deal, flow, market data) as INSERTs
                                 (SQL Developer: run as script, F5 - the /*insert*/ hint)
  sql/20-PROD-quote-prices.sql   the QR prices of the test date as INSERTs
  sql/30-DEV-static-check.sql    per trade and field: the RAW value, its alias for the source c_Deal uses, OK / MISSING
                                 (aliases by ALIASCODE + owner + extension + source - docs/reference/box-fe-static-aliases.csv),
                                 the folder's branch, the label's book, the filters p_Import_Deal_Data applies
  sql/40-DEV-bypass-join.sql     p_Import_Deal_Data: the join to BOX_TRD.T_BOX_DEAL_S inner -> left (from the package
  sql/49-DEV-bypass-rollback.sql   as exported from DEV); the rollback = the export unchanged; a check of which is live
  sql/50-DEV-accounting-attrs.sql  FK_PORTPROP / REFERENCE_ACCOUNTING on T_BOX_DEAL_DATA_S for the test trades (before
                                 the instrument's insert group), with a query listing values that exist in DEV
  sql/60-DEV-checks.sql          after each step: the rows in the tables it feeds (INFERRED column names - confirm)
  03-results.md                  one row per step: expected, result, evidence file - filled from the operator's CSVs

The online flow (Murex / Camunda -> BOX API -> BOX_TRD.T_BOX_DEAL_S) is bypassed in DEV only [operator, 2026-10-09]: the
package change and the update are DEV scripts with their rollback, never a change to cib-boxfin-dbboxfe (read-only).
A value still '<...>' in the inputs is written as an OPEN point, never guessed. Standard library only.
Exit 0 written · 1 refused · 2 bad invocation.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUTS = "tech-test-inputs.json"
ALIASES = ROOT / "docs/reference/box-fe-static-aliases.csv"
# the Financial Process (FE) order [operator, 2026-10-09]; the instrument's insert group is step 7
SEQUENCE = [("2387.65", "ENG GN - Main Captura de las curvas de fixing BOX", "branch"),
            ("2388.65", "ENG GN - Main Captura datos mercado for config BOX", "branch"),
            ("2628.65", "Calc Raw Flow StartDate And EndDate BOX", "book"),
            ("2629.65", "Import Deal Data And Flow Data BOX", "book"),
            ("2630.65", "Update current values and amountlocal BOX", "book"),
            ("2632.65", "Import Mtm Data BOX", "book"),
            ("<insert>", "Insert BOX <instrument> Deal Data", "book"),
            ("2608.65", "Create Process Queues by Book BOX", "branch"),
            ("2389.65", "ENG GN Main Dia Queue By Book BOX", "book")]
INSERT_GROUPS = {"depos": ("2631.65", "Insert BOX MM Deal Data"), "commodities": ("2490.65", "Insert BOX CES Deal Data"),
                 "irs": ("2835.65", "Insert BOX IRS Deal Data"), "ccs": ("3255.65", "Insert BOX CCS Deal Data"),
                 "cfm": ("3479.65", "Insert BOX CFM Deal Data"), "fra": ("3661.65", "Insert BOX FRA Deal Data"),
                 "fx": ("3155.65", "Insert BOX FX Deal Data"), "otc": ("3803.65", "Insert BOX OTC Deal Data")}
# the RAW INSTRUMENT text p_Import_Deal_Data / c_Deal map [read: PKG_FE_DEAL_CALCULATION, operator 2026-10-09]
RAW_INSTRUMENT = {"depos": "Loan / Depos", "irs": "IRS", "commodities": "Commodity Swap", "ccs": "Currency Swap",
                  "cds": "CDS", "cfm": "CFM", "fra": "FRA", "otc": "OTC", "cap": "Cap and Floor"}
GROUP_RE = re.compile(r"^([A-Z][A-Z0-9_]+):T:P:\S*p_ExecuteGroup\(([^,]+),\s*([^,]+),[^,]+,\s*([^,]+),[^,]+,[^,]+,\s*(.+?),\s*([^,]+)\);",
                      re.I)


class Result:
    def __init__(self):
        self.errors = []

    def err(self, code, where, msg):
        self.errors.append((code, where, msg))
        print(f"REFUSED {code}: {where}: {msg}", file=sys.stderr)


def undecided(v) -> bool:
    return v is None or (isinstance(v, str) and (not v.strip() or v.strip().startswith("<")))


def resolve(base: Path, p: str) -> Path:
    q = Path(p)
    if q.is_absolute() or q.exists():
        return q
    for r in (base, *base.parents):
        if (r / p).exists():
            return r / p
    return q


def qlist(xs) -> str:
    return ", ".join("'" + str(x).replace("'", "''") + "'" for x in xs)


def card_from_jobs(dbconf: Path, groups: set) -> list:
    """(group, job, instrument, label) of the jobs run's db.conf.proposal lines."""
    out = []
    for line in dbconf.read_text(encoding="utf-8", errors="replace").splitlines():
        m = GROUP_RE.match(line.strip())
        if m and m.group(2).strip() in groups:
            lab = re.search(r"f_getPKByLabel\('([^']+)'\)", m.group(5))
            out.append((m.group(2).strip(), m.group(1), m.group(4).strip(), lab.group(1) if lab else ""))
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or not Path(argv[0]).is_dir():
        print("usage: fe_tech_test.py <runs/<BRANCH>/<tier>-<env>/tests/technical/<run>/>", file=sys.stderr)
        return 2
    run = Path(argv[0])
    res = Result()
    if (run / ".frozen").exists():
        res.err("run-frozen", str(run), "start a new version (scripts/new_run.py --area tests/technical)")
        return 1
    ip = run / INPUTS
    if not ip.exists():
        res.err("inputs-missing", str(ip), "copy skills/box-fe-technical-test/tech-test-inputs.example.json there")
        return 1
    cfg = json.loads(ip.read_text(encoding="utf-8-sig"))
    opens = []

    def need(key, what):
        v = cfg.get(key)
        if undecided(v):
            opens.append(f"`{key}` - {what}")
            return f"<{key}>"
        return v
    env = need("environment", "the DEV environment where the test runs (e.g. a Tier 2 DEV database)")
    date = need("test_date", "the test date YYYY-MM-DD - every query and the Run Batch use it")
    branch_pk = need("branch_pk", "the target branch PK (NY_SCH 20007.4)")
    inst = str(cfg.get("instrument") or "depos").lower()
    raw_inst = cfg.get("raw_instrument") or RAW_INSTRUMENT.get(inst, "<raw instrument text>")
    trades = [t for t in (cfg.get("trades") or []) if isinstance(t, dict) and not undecided(t.get("front_id"))]
    if not trades:
        opens.append("`trades` - the 2 test trades (FRONT_ID, label; e.g. one loan and one deposit, different currencies)")
    if len(trades) == 1:
        opens.append("`trades` - only 1 trade: the test asks for 2 with different characteristics")
    fids = [t["front_id"] for t in trades] or ["<FRONT_ID 1>", "<FRONT_ID 2>"]
    labels = sorted({t.get("label") for t in trades if not undecided(t.get("label"))}) or ["<label>"]
    dlit = f"DATE '{date}'" if not str(date).startswith("<") else "DATE '<test date>'"
    sql = run / "sql"
    sql.mkdir(exist_ok=True)

    # 10 / 20 - PROD extracts ------------------------------------------------------------------------------------
    mkt = cfg.get("raw_market_data_filter")
    if undecided(mkt):
        opens.append("`raw_market_data_filter` - which rows of BOX_FE.T_BOX_RAW_MARKET_DATA_S the test needs (column / "
                     "condition: e.g. the curves of the trades' currencies) - written as a commented query until given")
    (sql / "10-PROD-raw-extract.sql").write_text(
        f"-- PROD (the only environment where the RAW tables are loaded) - {date}, trades {', '.join(fids)}\n"
        "-- Run as script (F5) in SQL Developer: /*insert*/ prints INSERT statements - save the output as\n"
        "-- 01-evidence/10-raw-inserts.sql and run it in DEV.\n"
        "-- Check the deal status first: a trade not in AUKI / BOX comes as '1s'; BOX expects 'BoValidated' (see 01-plan.md)\n"
        f"SELECT FRONT_ID, SOURCESYSTEM, BOOK, INSTRUMENT, STATUS FROM BOX_FE.T_BOX_RAW_DEAL_DATA_S\n"
        f"WHERE  FRONT_ID IN ({qlist(fids)}) AND TRUNC(PROCESSDATE) = {dlit};\n\n"
        f"SELECT /*insert*/ * FROM BOX_FE.T_BOX_RAW_DEAL_DATA_S\nWHERE  FRONT_ID IN ({qlist(fids)}) AND TRUNC(PROCESSDATE) = {dlit};\n\n"
        f"SELECT /*insert*/ * FROM BOX_FE.T_BOX_RAW_FLOW_DATA_S\nWHERE  FRONT_ID IN ({qlist(fids)}) AND TRUNC(PROCESSDATE) = {dlit};"
        "   -- INFERRED columns: confirm\n\n"
        + (f"SELECT /*insert*/ * FROM BOX_FE.T_BOX_RAW_MARKET_DATA_S\nWHERE  TRUNC(PROCESSDATE) = {dlit} AND {mkt};\n"
           if not undecided(mkt) else
           f"-- OPEN: the market data rows the test needs\n-- SELECT /*insert*/ * FROM BOX_FE.T_BOX_RAW_MARKET_DATA_S "
           f"WHERE TRUNC(PROCESSDATE) = {dlit} AND <filter>;\n"), encoding="utf-8")
    qcol = cfg.get("quote_prices_date_column")
    if undecided(qcol):
        opens.append("`quote_prices_date_column` - the date column of PGT_MRK.T_PGT_QUOTE_PRICES_S (and any filter: the "
                     "trades' curves only)")
        qcol = "<date column>"
    (sql / "20-PROD-quote-prices.sql").write_text(
        f"-- PROD - the QR prices of {date}, as INSERTs for DEV (F5). Then in DEV: the count must match.\n"
        f"SELECT COUNT(*) FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC({qcol}) = {dlit};\n"
        f"SELECT /*insert*/ * FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC({qcol}) = {dlit};\n", encoding="utf-8")

    # 30 - DEV static data -------------------------------------------------------------------------------------------
    rows = list(csv.DictReader(ALIASES.open(encoding="utf-8")))
    parts = []
    for r in rows:
        rt = "BOX_FE.T_BOX_RAW_DEAL_DATA_S" if r["raw_table"] == "deal" else "BOX_FE.T_BOX_RAW_FLOW_DATA_S"
        src = f" AND s.FK_SOURCE = {r['source']}" if r["source"] else ""
        if r["alias_table"].endswith("T_PGT_OBJSRC_INPUT_S"):
            parts.append(f"SELECT '{r['field']}' FIELD, r.FRONT_ID, TO_CHAR(r.{r['raw_column']}) RAW_VALUE, "
                         f"TO_CHAR(s.FK_PARENT) STATIC_PK, TO_CHAR(s.FK_SOURCE) SOURCE, "
                         f"CASE WHEN s.ALIASCODE IS NULL THEN 'MISSING' ELSE 'OK' END STATUS\n"
                         f"FROM {rt} r LEFT JOIN {r['alias_table']} s ON s.ALIASCODE = r.{r['raw_column']}\n"
                         f"  AND s.FK_OWNER_OBJ = {r['owner_obj']} AND s.FK_EXTENSION = {r['extension']}{src}\n"
                         f"WHERE r.FRONT_ID IN ({qlist(fids)}) AND TRUNC(r.PROCESSDATE) = {dlit}")
        else:
            parts.append(f"SELECT '{r['field']}' FIELD, r.FRONT_ID, TO_CHAR(r.{r['raw_column']}) RAW_VALUE, "
                         f"TO_CHAR(s.FK_PARENT) STATIC_PK, TO_CHAR(s.FK_SOURCE) SOURCE, "
                         f"CASE WHEN r.{r['raw_column']} IS NULL THEN 'EMPTY' WHEN s.PK IS NULL THEN 'MISSING' ELSE 'OK' END STATUS\n"
                         f"FROM {rt} r LEFT JOIN {r['alias_table']} s ON s.ALIASCODE = r.{r['raw_column']}\n"
                         f"  AND s.FK_OWNER_OBJ = {r['owner_obj']} AND s.FK_EXTENSION = {r['extension']}{src}\n"
                         f"WHERE r.FRONT_ID IN ({qlist(fids)}) AND TRUNC(r.PROCESSDATE) = {dlit}")
    (sql / "30-DEV-static-check.sql").write_text(
        f"-- DEV ({env}) - after the RAW inserts. Static data is matched by ALIASCODE for the source c_Deal / "
        "p_Import_Deal_Data use\n-- (docs/reference/box-fe-static-aliases.csv; a field without a source lists every "
        "source found). Any MISSING row: create\n-- the static (or its alias for that source) in DEV before running.\n"
        "-- RAW column names are those of the deal / flow data (INFERRED for RAW: confirm).\n"
        + "\nUNION ALL\n".join(parts) + "\nORDER BY 2, 1;\n\n"
        "-- the folder of each trade belongs to the target branch (INFERRED table PGT_TRD.T_PGT_FOLDER_S: confirm)\n"
        f"SELECT r.FRONT_ID, r.FOLDER, f.PK FOLDER_PK, f.FK_BRANCH, CASE WHEN f.FK_BRANCH = {branch_pk} THEN 'OK' "
        "ELSE 'CHECK' END STATUS\nFROM BOX_FE.T_BOX_RAW_DEAL_DATA_S r\n"
        "LEFT JOIN PGT_TRD.T_PGT_OBJ_SOURCE_S s ON s.ALIASCODE = r.FOLDER AND s.FK_OWNER_OBJ = 1453.4 AND "
        "s.FK_EXTENSION = 10513.4 AND s.FK_SOURCE = 279.4\nLEFT JOIN PGT_TRD.T_PGT_FOLDER_S f ON f.PK = s.FK_PARENT\n"
        f"WHERE r.FRONT_ID IN ({qlist(fids)}) AND TRUNC(r.PROCESSDATE) = {dlit};\n\n"
        "-- p_Import_Deal_Data's filters: the RAW BOOK is the label's book, the instrument text, maturity\n"
        + "\n".join(f"SELECT '{lab}' LABEL, BOX_SYS.PKG_BOXUTILITY.f_getBookByLabel('{lab}') BOOK FROM DUAL;" for lab in labels)
        + f"\nSELECT FRONT_ID, BOOK, INSTRUMENT, CASE WHEN INSTRUMENT = '{raw_inst}' THEN 'OK' ELSE 'CHECK' END INSTR_OK, "
        f"MATURITYDATEREAL, PROCESSDATE\nFROM BOX_FE.T_BOX_RAW_DEAL_DATA_S WHERE FRONT_ID IN ({qlist(fids)}) "
        f"AND TRUNC(PROCESSDATE) = {dlit};\n\n"
        "-- the branch process calendar (scheduling monitor, group 2935.65) has the test date\n"
        f"SELECT * FROM BOX_FE.T_BOX_BRPROCCAL_S WHERE ROWNUM <= 50;   -- OPEN: its branch / date columns\n",
        encoding="utf-8")
    opens.append("`T_BOX_BRPROCCAL_S` - its branch and date columns, to check the scheduling monitor filled the test month")

    # 40 / 49 - the bypass of the online flow (DEV only) -----------------------------------------------------------
    byp = cfg.get("bypass") if isinstance(cfg.get("bypass"), dict) else {}
    exp_ = byp.get("package_export")
    if undecided(exp_):
        opens.append("`bypass.package_export` - BOX_FE.PKG_FE_DEAL_CALCULATION body AS DEPLOYED IN DEV (query in "
                     "sql/40-DEV-bypass-join.sql), saved as a .sql file - the patch is made from it")
        body40 = ("-- OPEN: export the package body as deployed in DEV, save it, set bypass.package_export and run again:\n"
                  "SELECT text FROM all_source WHERE owner = 'BOX_FE' AND name = 'PKG_FE_DEAL_CALCULATION'\n"
                  "AND type = 'PACKAGE BODY' ORDER BY line;\n")
        body49 = "-- written once bypass.package_export is given (the export unchanged)\n"
    else:
        src = resolve(run, exp_).read_text(encoding="utf-8", errors="replace")
        proc = re.search(r"procedure\s+p_Import_Deal_Data\b.*?(?=\n\s*(?:procedure|function)\s+\w|\Z)", src, re.I | re.S)
        joins = list(re.finditer(r"\b(left\s+(?:outer\s+)?|inner\s+)?join(\s+BOX_TRD\.T_BOX_DEAL_S\b)", proc.group(0),
                                 re.I)) if proc else []
        hdr = "" if re.match(r"\s*create\s", src, re.I) else "create or replace "
        if len(joins) != 1:
            res.err("join-not-found", str(exp_), f"{len(joins)} join(s) to BOX_TRD.T_BOX_DEAL_S in p_Import_Deal_Data "
                    "(expected 1) - check the export")
            return 1
        m = joins[0]
        if (m.group(1) or "").lower().startswith("left"):
            body40 = "-- already a LEFT join in this export - nothing to patch\n"
        else:
            a, b = proc.start() + m.start(), proc.start() + m.end()
            patched = src[:a] + "left join" + m.group(2) + src[b:]
            body40 = (f"-- DEV ONLY ({env}) - p_Import_Deal_Data: the join to BOX_TRD.T_BOX_DEAL_S inner -> left, so the "
                      "trades\n-- import without the online flow (Deal Lite). Made from the DEV export "
                      f"{Path(exp_).name}. Rollback: 49-DEV-bypass-rollback.sql\n" + hdr + patched.rstrip() + "\n/\n")
        body49 = (f"-- DEV ONLY - restores PKG_FE_DEAL_CALCULATION as exported ({Path(exp_).name})\n" + hdr
                  + src.rstrip() + "\n/\n")
    check = ("\n-- which join is live now (DEV):\nSELECT line, text FROM all_source WHERE owner = 'BOX_FE' AND name = "
             "'PKG_FE_DEAL_CALCULATION' AND type = 'PACKAGE BODY'\nAND UPPER(text) LIKE '%BOX_TRD.T_BOX_DEAL_S%' "
             "ORDER BY line;\n")
    (sql / "40-DEV-bypass-join.sql").write_text(body40 + check, encoding="utf-8")
    (sql / "49-DEV-bypass-rollback.sql").write_text(body49 + check, encoding="utf-8")

    pp, ra = byp.get("fk_portprop"), byp.get("reference_accounting")
    if undecided(pp) or undecided(ra):
        opens.append("`bypass.fk_portprop` / `bypass.reference_accounting` - values that exist in DEV (the first query "
                     "of sql/50-DEV-accounting-attrs.sql lists some); for FE any existing value works")
    ins_grp, ins_name = INSERT_GROUPS.get(inst, ("<insert group>", f"Insert BOX {inst} Deal Data"))
    (sql / "50-DEV-accounting-attrs.sql").write_text(
        f"-- DEV ONLY ({env}) - after 2629.65 / 2630.65, BEFORE {ins_grp} ({ins_name}): the accounting attributes the\n"
        "-- online flow would fill; c_Deal skips a deal where either is NULL.\n"
        "SELECT DISTINCT FK_PORTPROP, REFERENCE_ACCOUNTING FROM BOX_FE.T_BOX_DEAL_DATA_S\n"
        "WHERE FK_PORTPROP IS NOT NULL AND REFERENCE_ACCOUNTING IS NOT NULL AND ROWNUM <= 20;\n\n"
        f"UPDATE BOX_FE.T_BOX_DEAL_DATA_S SET FK_PORTPROP = {pp if not undecided(pp) else '<fk_portprop>'}, "
        f"REFERENCE_ACCOUNTING = '{ra if not undecided(ra) else '<reference_accounting>'}'\n"
        f"WHERE FRONT_ID IN ({qlist(fids)}) AND DATEPROCESS = {dlit};\n-- check: 1 row per trade, then COMMIT\n",
        encoding="utf-8")

    # 02 - run card -----------------------------------------------------------------------------------------------
    seq = [(ins_grp if g == "<insert>" else g, ins_name if g == "<insert>" else n, lv) for g, n, lv in SEQUENCE]
    jobs = []
    jr = cfg.get("fe_jobs_run")
    if not undecided(jr):
        dbp = resolve(run, jr) / "out" / "db.conf.proposal"
        if dbp.exists():
            jobs = card_from_jobs(dbp, {g for g, _, _ in seq})
        else:
            opens.append(f"`fe_jobs_run` - {dbp} not found")
    card = [f"# Run card - {inst} - {date} - {env}", "",
            "SIGOM: **GBO > SYS > Process > Batch > Run Batch** - one line at a time, in this order; check each with "
            "`sql/60-DEV-checks.sql` before the next.", "",
            "0. **Scheduling monitor** (2935.65) has filled the branch process calendar for the test month "
            "(`sql/30-DEV-static-check.sql`, last query) - else run 2935.65 first.", ""]
    card += ["| # | Event group | Branch | Process date | Instrument | Label | From the jobs |", "|---|---|---|---|---|---|---|"]
    k = 0
    for g, n, lv in seq:
        k += 1
        js = [j for j in jobs if j[0] == g]
        if g == "2629.65":
            card.append(f"| {k}a | **bypass:** `sql/40-DEV-bypass-join.sql` (inner -> left join) | | | | | DEV only |")
        if g == ins_grp:
            card.append(f"| {k}a | **bypass:** `sql/50-DEV-accounting-attrs.sql` (FK_PORTPROP, REFERENCE_ACCOUNTING) | | | "
                        "| | DEV only |")
        if js:
            for _, jn, ins, lab in js:
                if lab and lab not in labels and labels != ["<label>"]:
                    continue                                   # the test's labels only
                card.append(f"| {k} | {g} {n} | {branch_pk} | {date} | {ins} | {lab or '-'} | `{jn}` |")
        else:
            lab = ", ".join(labels) if lv == "book" else "-"
            ins = "-" if g in ("2387.65", "2388.65", "2628.65", "2629.65", "2630.65") else inst
            card.append(f"| {k} | {g} {n} | {branch_pk} | {date} | {ins} | {lab} | (no jobs run given) |")
    card += ["", "After the last step: **`sql/49-DEV-bypass-rollback.sql`** - DEV back to the inner join (check query at "
             "its end)."]
    (run / "02-run-card.md").write_text("\n".join(card) + "\n", encoding="utf-8")

    # 60 - checks ---------------------------------------------------------------------------------------------------
    (sql / "60-DEV-checks.sql").write_text(
        f"-- DEV ({env}) - after each step (INFERRED table / column names - confirm; OPEN: the batch error log)\n"
        f"-- after 2629.65 Import Deal Data And Flow Data\nSELECT FRONT_ID, BOOK, INSTRUMENT, FK_PORTPROP, REFERENCE_ACCOUNTING "
        f"FROM BOX_FE.T_BOX_DEAL_DATA_S\nWHERE FRONT_ID IN ({qlist(fids)}) AND DATEPROCESS = {dlit};\n"
        f"SELECT FRONT_ID, COUNT(*) FROM BOX_FE.T_BOX_FLOW_DATA_S WHERE FRONT_ID IN ({qlist(fids)}) GROUP BY FRONT_ID;\n\n"
        f"-- after {ins_grp} {ins_name}\nSELECT * FROM BOX_FE.T_BOX_DATADEAL_S WHERE ROWNUM <= 50;   "
        "-- OPEN: its trade / date columns\n", encoding="utf-8")
    opens.append("the tables each event group feeds and the batch error log - to complete sql/60-DEV-checks.sql")

    # 01 plan + 03 results ---------------------------------------------------------------------------------------------
    plan = [f"# Technical test - {cfg.get('branch', '')} - {inst} - {env} - {date}", "",
            "| # | Step | Where | File |", "|---|---|---|---|",
            f"| 1 | Environment and test date: **{env}**, **{date}** | - | `{INPUTS}` |",
            "| 2 | RAW tables for the test trades (deal, flow, market data); check the deal status | PROD | "
            "`sql/10-PROD-raw-extract.sql` |",
            "| 3 | Insert the RAW rows in DEV | DEV | `01-evidence/10-raw-inserts.sql` (the output of 2) |",
            "| 4 | QR prices of the test date | PROD -> DEV | `sql/20-PROD-quote-prices.sql` |",
            "| 5 | Static data: every alias MISSING created first; folder branch; label book; filters | DEV | "
            "`sql/30-DEV-static-check.sql` |",
            "| 6 | Bypass of the online flow: the join (before 2629.65), the accounting attributes (before the insert "
            "group) | DEV | `sql/40-…`, `sql/50-…` |",
            "| 7 | Run the event groups in order | SIGOM DEV | `02-run-card.md` |",
            "| 8 | Each step ends OK and its tables are fed; then the rollback | DEV | `sql/60-DEV-checks.sql`, "
            "`sql/49-…` |", "",
            "Return each query's output as a CSV in `01-evidence/` (named after the file: `30-static-check.csv` …); "
            "the agent records it in `03-results.md`.", "",
            "**Deal status:** a trade not in AUKI / BOX comes from PROD as `1s`; BOX expects `BoValidated` - see OPEN "
            "below before step 3.", "", "## OPEN - to answer before or during the test", ""]
    opens.append("deal status: set the test deals to `BoValidated` in DEV after the insert, or keep them as in PROD?")
    plan += [f"- {o}" for o in opens]
    (run / "01-plan.md").write_text("\n".join(plan) + "\n", encoding="utf-8")
    res = run / "03-results.md"
    if not res.exists():
        res.write_text(f"# Results - technical test {inst} {date} {env}\n\n| # | Step | Expected | Result | Evidence |\n"
                       "|---|---|---|---|---|\n" + "".join(f"| {i} | {s} | {e} | | |\n" for i, s, e in (
                           (2, "RAW extract", "2 trades, deal + flow rows"), (3, "RAW in DEV", "same rows"),
                           (4, "QR prices", "same count PROD / DEV"), (5, "static data", "no MISSING"),
                           (6, "bypass", "left join live; attributes set"), (7, "event groups", "each ends OK"),
                           (8, "tables fed / rollback", "rows per table; inner join back"))), encoding="utf-8")
    print(f"wrote {run}: 01-plan.md, 02-run-card.md, sql/ (6 files), 03-results.md - {len(opens)} OPEN point(s)")
    for o in opens:
        print(f"  OPEN {o}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
