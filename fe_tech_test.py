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
  sql/10-PROD-raw-extract.sql    the RAW rows of the test trades (deal, flow, market data) as INSERTs - or, when they
                                 are already in DEV (raw_in_dev), sql/10-DEV-raw-check.sql: their presence
                                 (SQL Developer: run as script, F5 - the /*insert*/ hint)
  sql/20-PROD-quote-prices.sql   the QR prices of the test date as INSERTs (PGT_MRK.T_PGT_QUOTE_PRICES_S, by the
                                 date column given - PUBLISHDATE / SETTLEDATE counted side by side until it is)
  sql/30-DEV-static-check.sql    per trade and field: the RAW value, its alias for the source c_Deal uses, OK / MISSING
                                 (aliases by ALIASCODE + owner + extension + source - docs/reference/box-fe-static-aliases.csv),
                                 the folder's branch, the label's book, the filters p_Import_Deal_Data applies
  sql/40-DEV-bypass-join.sql     p_Import_Deal_Data: the join to BOX_TRD.T_BOX_DEAL_S inner -> left (bypass.join
                                 already-left: only the check; else from the package
  sql/49-DEV-bypass-rollback.sql   as exported from DEV); the rollback = the export unchanged; a check of which is live
  sql/50-DEV-accounting-attrs.sql  FK_PORTPROP / REFERENCE_ACCOUNTING on T_BOX_DEAL_DATA_S for the test trades (before
                                 the instrument's insert group). FK_PORTPROP is the PK of a portfolio property
                                 (BOX_ACC.T_BOX_ACCT_PORT_PROP_S, SIGOM Portfolio Properties), keyed by the branch
                                 GROUP (its FK_BRANCH), not the branch [operator, 2026-10-09]: the candidates of the
                                 target's group and the instrument (FK_INSTRUMENT = sub-product) are listed, and
                                 the value given is checked against both; the rows are the trades' FRONT_ID (one per
                                 leg); optional `bypass.extra_fields` for the other online-flow columns
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
# the portfolio property's FK_INSTRUMENT (PGT_SYS.T_PGT_SUB_PRODUCT_S) per instrument [operator's Tier 1 query,
# 2026-10-09: 2.4 Deposit & Loan; 20092.4 on the IRS portfolio properties]; another instrument: `sub_product_pk`
SUB_PRODUCT = {"depos": "2.4", "irs": "20092.4"}
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
    group_pk = need("branch_group_pk", "the target's branch GROUP PK - PGT_STC.T_PGT_BRANCH_S.FK_LOCALGROUP of the branch "
                    "(NY_SCH 21447.4); BOX_ACC.T_BOX_ACCT_PORT_PROP_S.FK_BRANCH holds it")
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

    # 10 / 20 - RAW rows (PROD extract, or already in DEV) and QR prices ----------------------------------------
    mkt = cfg.get("raw_market_data_filter")
    if undecided(mkt):          # the operator's own query: the market data rows of the trades [2026-10-09]
        mkt = f"FRONT_ID IN ({qlist(fids)})"
    raw_in_dev = cfg.get("raw_in_dev") is True
    if undecided(cfg.get("raw_in_dev")):
        opens.append("`raw_in_dev` - are the RAW rows of the test date already in the DEV environment (true: "
                     "sql/10-DEV-raw-check.sql) or extracted from PROD (false: sql/10-PROD-raw-extract.sql)?")
    w = f"FRONT_ID IN ({qlist(fids)}) AND TRUNC(PROCESSDATE) = {dlit}"
    status_note = ("-- DEAL_STATUS (e.g. '1s') is shown for the record: p_Import_Deal_Data does not filter on it (it computes\n"
                   "-- Live / Matured from the maturity); the BO status (FK_BO_STATUS 3.65) is only in the join the bypass\n"
                   "-- turns LEFT.\n")
    summary = (f"SELECT 'DEAL' TBL, FRONT_ID, SOURCESYSTEM, BOOK, DEAL_STATUS, INSTRUMENT, INSTRUMENT_TYPE, COUNT(*) N\n"
               f"FROM BOX_FE.T_BOX_RAW_DEAL_DATA_S WHERE {w}\n"
               "GROUP BY FRONT_ID, SOURCESYSTEM, BOOK, DEAL_STATUS, INSTRUMENT, INSTRUMENT_TYPE ORDER BY FRONT_ID;\n"
               f"SELECT 'FLOW' TBL, FRONT_ID, CASHFLOWTYPE, COUNT(*) N FROM BOX_FE.T_BOX_RAW_FLOW_DATA_S WHERE {w}\n"
               "GROUP BY FRONT_ID, CASHFLOWTYPE ORDER BY FRONT_ID, CASHFLOWTYPE;\n"
               f"SELECT 'MARKET' TBL, COUNT(*) N FROM BOX_FE.T_BOX_RAW_MARKET_DATA_S WHERE TRUNC(PROCESSDATE) = {dlit} "
               f"AND {mkt};\n")
    stale = sql / ("10-PROD-raw-extract.sql" if raw_in_dev else "10-DEV-raw-check.sql")
    if stale.exists():
        stale.unlink()
    if raw_in_dev:
        (sql / "10-DEV-raw-check.sql").write_text(
            f"-- DEV ({env}) - the RAW rows of {date} are already loaded here (raw_in_dev) [operator, 2026-10-09]:\n"
            "-- nothing to extract from PROD. Expected: 1 DEAL row per trade, its flows, its market data rows.\n"
            + status_note + summary, encoding="utf-8")
    else:
        (sql / "10-PROD-raw-extract.sql").write_text(
            f"-- PROD (the only environment where the RAW tables are loaded) - {date}, trades {', '.join(fids)}\n"
            "-- Run as script (F5) in SQL Developer: /*insert*/ prints INSERT statements - save the output as\n"
            "-- 01-evidence/10-raw-inserts.sql and run it in DEV (then the same summary in DEV must match).\n"
            + status_note + summary + "\n"
            f"SELECT /*insert*/ * FROM BOX_FE.T_BOX_RAW_DEAL_DATA_S WHERE {w};\n\n"
            f"SELECT /*insert*/ * FROM BOX_FE.T_BOX_RAW_FLOW_DATA_S WHERE {w};\n\n"
            f"SELECT /*insert*/ * FROM BOX_FE.T_BOX_RAW_MARKET_DATA_S WHERE TRUNC(PROCESSDATE) = {dlit} AND {mkt};\n",
            encoding="utf-8")
    qcol, qflt = cfg.get("quote_prices_date_column"), cfg.get("quote_prices_filter")
    qcols = "PK, FK_OWNER_OBJ, FK_PARENT, FK_EXTENSION, FK_QUOTETYPE, FK_QUOTESERIE, PUBLISHDATE, EXPIREDATE, SETTLEDATE, " \
            "MATURITYDATE, PUBLISHPRICE"
    extra = f" AND {qflt}" if not undecided(qflt) else ""
    if undecided(qcol):
        opens.append("`quote_prices_date_column` - which date of PGT_MRK.T_PGT_QUOTE_PRICES_S selects the prices of the "
                     "test date: PUBLISHDATE or SETTLEDATE (the first query of sql/20-PROD-quote-prices.sql counts both)")
        q20 = ("-- OPEN: the date column. Both candidates, counted for the test date:\n"
               f"SELECT 'PUBLISHDATE' COL, COUNT(*) FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC(PUBLISHDATE) = {dlit}{extra}\n"
               f"UNION ALL SELECT 'SETTLEDATE', COUNT(*) FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC(SETTLEDATE) = {dlit}{extra};\n"
               "-- Run the same two counts in DEV: DEV already has the prices of the date -> nothing to copy.\n"
               "-- then set quote_prices_date_column and run fe_tech_test.py again for the INSERT extract.\n")
    else:
        q20 = (f"SELECT COUNT(*) FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC({qcol}) = {dlit}{extra};\n"
               f"SELECT /*insert*/ * FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC({qcol}) = {dlit}{extra};\n\n"
               f"-- DEV ({env}), BEFORE running the inserts: rows already there for the date (0 expected; else they are\n"
               "-- DEV's own - keep them and skip the insert, or ask before deleting):\n"
               f"SELECT COUNT(*) FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC({qcol}) = {dlit}{extra};\n"
               f"-- DEV, AFTER: the count must match PROD's\n"
               f"SELECT {qcols} FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC({qcol}) = {dlit}{extra} ORDER BY FK_PARENT;\n")
    qr_in_dev = cfg.get("quote_prices_in_dev") is True and not undecided(qcol)
    for stale in ("20-DEV-quote-prices-check.sql", "20-PROD-quote-prices.sql"):
        if (sql / stale).exists():
            (sql / stale).unlink()
    if qr_in_dev:
        (sql / "20-DEV-quote-prices-check.sql").write_text(
            f"-- DEV ({env}) - the QR prices of {date} are already copied here (quote_prices_in_dev) [operator, 2026-10-09]:\n"
            f"-- nothing to extract from PROD. Expected: rows with {qcol} = the date (EXPIREDATE as copied).\n"
            f"SELECT COUNT(*) N, MIN(EXPIREDATE), MAX(EXPIREDATE) FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC({qcol}) = "
            f"{dlit}{extra};\n"
            f"SELECT FK_QUOTETYPE, COUNT(*) N FROM PGT_MRK.T_PGT_QUOTE_PRICES_S WHERE TRUNC({qcol}) = {dlit}{extra}\n"
            "GROUP BY FK_QUOTETYPE ORDER BY 1;\n", encoding="utf-8")
    else:
      (sql / "20-PROD-quote-prices.sql").write_text(
        f"-- PROD - the QR prices of {date}, as INSERTs for DEV (F5). Columns: {qcols}, DAILYMULTFACTOR,\n"
        "-- ACUMMULTFACTOR, GUID, REPLICIND, DIRTYPRICE [operator, 2026-10-09].\n"
        "-- An insert refused in DEV with ORA-00001 (PK / GUID already used there) or ORA-02291 (FK_PARENT / FK_QUOTESERIE\n"
        "-- not in DEV: the quote's static data is missing) is recorded in 03-results.md - never forced.\n"
        + (f"-- filter: {qflt}\n" if extra else "-- no filter (quote_prices_filter): every price of the date\n") + q20,
        encoding="utf-8")

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
        "-- p_Import_Deal_Data's filters [read, 2026-10-09]: TRUNC(PROCESSDATE) = the date; UPPER(BOOK) = UPPER(the label's\n"
        "-- book); UPPER(DATA_EXECUTION_TYPE) = 'BOOK'; TRUNC(MATURITYDATEREAL) + days matured (T_BOX_ENGDAYS_MATURED_S,\n"
        "-- 0 if none) + 5 >= the date. The INSTRUMENT text picks the days-matured row and the insert group.\n"
        + "\n".join(f"SELECT '{lab}' LABEL, BOX_SYS.PKG_BOXUTILITY.f_getBookByLabel('{lab}') BOOK FROM DUAL;" for lab in labels)
        + f"\nSELECT FRONT_ID, SOURCESYSTEM, DIRECTION, BOOK, DATA_EXECUTION_TYPE, INSTRUMENT, MATURITYDATEREAL, PROCESSDATE,\n"
        f"       CASE WHEN INSTRUMENT = '{raw_inst}' THEN 'OK' ELSE 'CHECK' END INSTR_OK,\n"
        "       CASE WHEN UPPER(DATA_EXECUTION_TYPE) = 'BOOK' THEN 'OK' ELSE 'FILTERED' END EXEC_TYPE_OK,\n"
        f"       CASE WHEN TRUNC(MATURITYDATEREAL) + 5 >= {dlit} THEN 'OK' ELSE 'CHECK (matured)' END MATURITY_OK,\n"
        "       CASE WHEN UPPER(BOOK) IN (" + ", ".join(f"UPPER(BOX_SYS.PKG_BOXUTILITY.f_getBookByLabel('{lab}'))"
                                               for lab in labels) + ") THEN 'OK' ELSE 'FILTERED' END BOOK_OK\n"
        f"FROM BOX_FE.T_BOX_RAW_DEAL_DATA_S WHERE FRONT_ID IN ({qlist(fids)}) AND TRUNC(PROCESSDATE) = {dlit};\n\n"
        "-- the branch process calendar (scheduling monitor, group 2935.65) has the test date [FK_BRANCH = the branch PK,\n"
        "-- DATETOPROCESS - operator, 2026-10-09]: MISSING -> run 2935.65 for the branch first (run card, step 0)\n"
        f"SELECT CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'MISSING' END STATUS FROM BOX_FE.T_BOX_BRPROCCAL_S\n"
        f"WHERE FK_BRANCH = {branch_pk} AND TRUNC(DATETOPROCESS) = {dlit};\n"
        f"SELECT FK_BRANCH, DATETOPROCESS FROM BOX_FE.T_BOX_BRPROCCAL_S\nWHERE FK_BRANCH = {branch_pk} "
        f"AND DATETOPROCESS >= TRUNC({dlit}, 'MM') AND DATETOPROCESS < ADD_MONTHS(TRUNC({dlit}, 'MM'), 1)\n"
        "ORDER BY DATETOPROCESS;\n",
        encoding="utf-8")

    # 40 / 49 - the bypass of the online flow (DEV only) -----------------------------------------------------------
    byp = cfg.get("bypass") if isinstance(cfg.get("bypass"), dict) else {}
    exp_, jmode = byp.get("package_export"), str(byp.get("join") or "").strip().lower()
    if jmode == "already-left":
        body40 = (f"-- DEV ({env}) - p_Import_Deal_Data's join to BOX_TRD.T_BOX_DEAL_S is already LEFT in this environment\n"
                  "-- [operator, 2026-10-09]: nothing to deploy. Check before 2629.65 (expected: 'left join'):\n")
        body49 = (f"-- DEV ({env}) - the LEFT join was in place before this test: this test restores nothing. Whether {env}\n"
                  "-- goes back to the inner join is for the environment's owner (the check below shows which is live).\n")
    elif undecided(exp_):
        opens.append("`bypass.join` - is p_Import_Deal_Data's join to BOX_TRD.T_BOX_DEAL_S already LEFT in DEV (check "
                     "query in sql/40)? yes -> `already-left` (nothing to deploy); no -> export the package body as "
                     "deployed in DEV into `bypass.package_export`: the agent writes the patch and its rollback for the "
                     "operator to run (no agent touches a database)")
        body40 = ("-- OPEN (bypass.join): first the check below. Still an inner join -> export the package body as deployed\n"
                  "-- in DEV, save it, set bypass.package_export and run fe_tech_test.py again:\n"
                  "SELECT text FROM all_source WHERE owner = 'BOX_FE' AND name = 'PKG_FE_DEAL_CALCULATION'\n"
                  "AND type = 'PACKAGE BODY' ORDER BY line;\n")
        body49 = "-- written once bypass.package_export is given (the export unchanged), or nothing with bypass.join already-left\n"
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
    byp_note = ("\n-- With the bypass the T_BOX_DEAL_S columns are NULL (sql/50 sets the ones the test needs). Also called with\n"
                "-- BO_CODE NULL: BOX_TRD.PKG_BOX_DEAL_LITE_DATA_API.f_GetAdditionalInfo(.., 'UTI') and\n"
                "-- BOX_SYS.PKG_BOXUTILITY.f_getCRDataByType('Notional Settle Type', ..) - if 2629.65 ends in ORA-20001\n"
                "-- 'Error in procedure p_Import_Deal_data', look there first.\n")
    check = ("\n-- which join is live now (DEV):\nSELECT line, text FROM all_source WHERE owner = 'BOX_FE' AND name = "
             "'PKG_FE_DEAL_CALCULATION' AND type = 'PACKAGE BODY'\nAND UPPER(text) LIKE '%BOX_TRD.T_BOX_DEAL_S%' "
             "ORDER BY line;\n")
    (sql / "40-DEV-bypass-join.sql").write_text(body40 + byp_note + check, encoding="utf-8")
    (sql / "49-DEV-bypass-rollback.sql").write_text(body49 + check, encoding="utf-8")

    pp, ra = byp.get("fk_portprop"), byp.get("reference_accounting")
    sub = cfg.get("sub_product_pk") or SUB_PRODUCT.get(inst)
    if undecided(sub):
        opens.append(f"`sub_product_pk` - the PGT_SYS.T_PGT_SUB_PRODUCT_S PK of {inst} (a portfolio property's "
                     "FK_INSTRUMENT; query 2 of sql/50 lists them when not given)")
        sub = None
    any_pp = str(byp.get("portprop_scope") or "").strip().lower() == "any"
    if undecided(pp) and any_pp:
        opens.append("`bypass.fk_portprop` - run sql/50 query 2d in DEV and return the CSV: the agent proposes the PK (any "
                     "Valid portfolio property of the instrument - FE only, portprop_scope any; the reference group's "
                     "first)")
    elif undecided(pp):
        opens.append("`bypass.fk_portprop` - run sql/50 queries 1, 2 (2b, 2c if 2 is empty) and return the CSV: the "
                     "agent proposes the PK (a Valid portfolio property of the target's branch GROUP and the instrument; "
                     "Trading / Hedging as the trade is booked). None -> create it in SIGOM Portfolio Properties in DEV "
                     "from the reference group's shape (2c), or say which to use")
    if not byp.get("extra_fields_decided"):
        opens.append("`bypass.extra_fields` - under the bypass p_Import_Deal_Data also leaves NULL FK_INSTRUMTYPE, "
                     "FK_TRDSUBTYPE, FK_MICROHEDGE, FK_STRATEGY, FK_DEALTREAT, FK_ACCTDOC, UTI, NOMINAL_SETTLEMENT, "
                     "COMPOUND_FREQ (from BOX_TRD.T_BOX_DEAL_S). Does the insert group (c_Deal) or a later step need any? "
                     "Give them as {column: value} (query 3 of sql/50 shows Tier 1's), then set extra_fields_decided: true")
    if undecided(ra):
        opens.append("`bypass.reference_accounting` - run sql/50 queries 3a-3d (in PROD, where the online flow fills it, "
                     "and in DEV) and return the CSVs: the agent proposes the value. Tier 1 evidence: the London (SLB) "
                     "trade carries its own DEAL_ID, the Madrid trades a contract reference. For FE any non-NULL value "
                     "passes; the choice matters for accounting. Answer `DEAL_ID` or a literal value")
    ins_grp, ins_name = INSERT_GROUPS.get(inst, ("<insert group>", f"Insert BOX {inst} Deal Data"))
    ppv = pp if not undecided(pp) else "<fk_portprop>"
    rav = ("TO_CHAR(DEAL_ID)" if str(ra).strip().upper() == "DEAL_ID" else "'" + str(ra).replace("'", "''") + "'") \
        if not undecided(ra) else "'<reference_accounting>'"
    fl = qlist(fids)
    xf = {k: v for k, v in (byp.get("extra_fields") or {}).items() if not undecided(v) and re.fullmatch(r"[A-Z_0-9]+", k)}
    ex_sql = "".join(f", {k} = {v}" for k, v in xf.items())
    subf = f" AND p.FK_INSTRUMENT = {sub}" if sub else ""
    ref_grp = cfg.get("reference_group_pk") if not undecided(cfg.get("reference_group_pk")) else None
    (sql / "50-DEV-accounting-attrs.sql").write_text(
        f"-- DEV ONLY ({env}) - after 2629.65 / 2630.65, BEFORE {ins_grp} ({ins_name}): the accounting attributes the\n"
        "-- online flow would fill; c_Deal skips a deal where either is NULL.\n"
        "-- FK_PORTPROP = BOX_ACC.T_BOX_ACCT_PORT_PROP_S.PK (SIGOM Portfolio Properties): FK_BRANCH = the branch GROUP\n"
        f"-- ({group_pk}, PGT_STC.T_PGT_BRANCH_GROUP_S), not the branch ({branch_pk}); FK_INSTRUMENT = the sub-product\n"
        "-- (PGT_SYS.T_PGT_SUB_PRODUCT_S); DESCRIPTION = Trading / Hedging + counterparty sector; STATUS Valid\n"
        "-- [operator's Tier 1 queries, 2026-10-09].\n"
        "-- p_Import_Deal_Data [read, 2026-10-09]: MERGE on FRONT_ID + SOURCESYSTEM + DIRECTION (one row per leg, the date\n"
        "-- in DATEPROCESS); DEAL_ID = FRONT_ID || '.' || the SOURCESYSTEM alias's FK_PARENT (Mx3EU -> .413; '.0' = the\n"
        "-- alias is missing); REFERENCE_ACCOUNTING, FK_PORTPROP, FK_INSTRUMTYPE, FK_TRDSUBTYPE, FK_MICROHEDGE,\n"
        "-- FK_STRATEGY, FK_DEALTREAT, FK_ACCTDOC, UTI, NOMINAL_SETTLEMENT, COMPOUND_FREQ come from BOX_TRD.T_BOX_DEAL_S -\n"
        "-- NULL under the bypass, AND RESET TO NULL by every re-run of 2629.65: run this file again after each one.\n\n"
        "-- 0. the test trades after 2629.65 / 2630.65 (DEAL_ID ending .0 -> SOURCESYSTEM alias missing: sql/30)\n"
        "SELECT DATEPROCESS, SOURCESYSTEM, FRONT_ID, DEAL_ID, DIRECTION, STATUS, BOOK, FOLDER, INSTRUMENT, FK_INSTRUMTYPE,\n"
        "       FK_STRATEGY, FK_PORTPROP, REFERENCE_ACCOUNTING\n"
        f"FROM BOX_FE.T_BOX_DEAL_DATA_S WHERE FRONT_ID IN ({fl}) AND DATEPROCESS = {dlit} ORDER BY FRONT_ID, DIRECTION;\n\n"
        f"-- 1. the group of the branch (expected {group_pk})\n"
        f"SELECT PK, FK_LOCALGROUP FROM PGT_STC.T_PGT_BRANCH_S WHERE PK = {branch_pk};\n\n"
        "-- 2. the candidates: Valid portfolio properties of the group and the instrument. Pick one: its DESCRIPTION\n"
        "--    starts Trading / Hedging - take the one matching how the trade is booked (for FE any Valid one works).\n"
        "SELECT p.PK, g.DESCRIPTION BRANCH_GROUP, p.FK_INSTRUMENT, sp.DESCRIPTION SUB_PRODUCT, p.DESCRIPTION, p.STATUS\n"
        "FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S p\nLEFT JOIN PGT_STC.T_PGT_BRANCH_GROUP_S g ON g.PK = p.FK_BRANCH\n"
        "LEFT JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = p.FK_INSTRUMENT\n"
        f"WHERE p.FK_BRANCH = {group_pk}{subf} AND p.STATUS = 'Valid' ORDER BY p.DESCRIPTION;\n\n"
        "-- 2b. 0 rows in 2: what the group has (any instrument / status) - a wrong sub-product or a non-Valid row?\n"
        "SELECT p.FK_INSTRUMENT, sp.DESCRIPTION SUB_PRODUCT, p.STATUS, SUBSTR(p.DESCRIPTION, 1, INSTR(p.DESCRIPTION || ' ', "
        "' ') - 1) KIND, COUNT(*) N\n"
        "FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S p LEFT JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = p.FK_INSTRUMENT\n"
        f"WHERE p.FK_BRANCH = {group_pk}\nGROUP BY p.FK_INSTRUMENT, sp.DESCRIPTION, p.STATUS, "
        "SUBSTR(p.DESCRIPTION, 1, INSTR(p.DESCRIPTION || ' ', ' ') - 1) ORDER BY 1, 3;\n\n"
        + (f"-- 2c. still none: the reference group's ({ref_grp}) for the instrument - the shape to create in SIGOM Portfolio\n"
           "--     Properties for the target's group in DEV (then 2 again)\n"
           "SELECT p.PK, p.FK_INSTRUMENT, p.DESCRIPTION, p.STATUS FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S p\n"
           f"WHERE p.FK_BRANCH = {ref_grp}{subf} AND p.STATUS = 'Valid' ORDER BY p.DESCRIPTION;\n\n" if ref_grp else "")
        + ("-- 2d. portprop_scope any (FE only: the portfolio property is not read by the FE test) [operator, 2026-10-09]:\n"
           "--     any Valid one of the instrument in DEV, the reference group's first. The accounting test needs the\n"
           "--     target's own (created by sigom-box-acc-configs from GBO's PGT_ACT portfolio properties).\n"
           "SELECT p.PK, p.FK_BRANCH, g.DESCRIPTION BRANCH_GROUP, p.FK_INSTRUMENT, sp.DESCRIPTION SUB_PRODUCT, "
           "p.DESCRIPTION, p.STATUS\nFROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S p\n"
           "LEFT JOIN PGT_STC.T_PGT_BRANCH_GROUP_S g ON g.PK = p.FK_BRANCH\n"
           "LEFT JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = p.FK_INSTRUMENT\n"
           f"WHERE p.STATUS = 'Valid'{subf}\n"
           f"ORDER BY CASE WHEN p.FK_BRANCH = {ref_grp or group_pk} THEN 0 ELSE 1 END, p.FK_BRANCH, p.DESCRIPTION;\n\n"
           if any_pp else "")
        + "-- 3a. REFERENCE_ACCOUNTING as filled by the online flow (run in PROD and in DEV): its kind per portfolio-property\n"
        "--     group, source system and instrument, with an example\n"
        "SELECT p.FK_BRANCH PP_GROUP, d.SOURCESYSTEM, d.INSTRUMENT,\n"
        "       CASE WHEN d.REFERENCE_ACCOUNTING IS NULL THEN 'NULL' WHEN d.REFERENCE_ACCOUNTING = TO_CHAR(d.DEAL_ID) THEN "
        "'DEAL_ID'\n            WHEN d.REFERENCE_ACCOUNTING = TO_CHAR(d.FRONT_ID) THEN 'FRONT_ID' ELSE 'OTHER, length ' || "
        "LENGTH(d.REFERENCE_ACCOUNTING) END KIND,\n"
        "       COUNT(*) N, MIN(d.REFERENCE_ACCOUNTING) EXAMPLE\n"
        "FROM BOX_FE.T_BOX_DEAL_DATA_S d LEFT JOIN BOX_ACC.T_BOX_ACCT_PORT_PROP_S p ON p.PK = d.FK_PORTPROP\n"
        "WHERE d.DATEPROCESS = (SELECT MAX(DATEPROCESS) FROM BOX_FE.T_BOX_DEAL_DATA_S)\n"
        "GROUP BY p.FK_BRANCH, d.SOURCESYSTEM, d.INSTRUMENT, CASE WHEN d.REFERENCE_ACCOUNTING IS NULL THEN 'NULL' WHEN "
        "d.REFERENCE_ACCOUNTING = TO_CHAR(d.DEAL_ID) THEN 'DEAL_ID'\n         WHEN d.REFERENCE_ACCOUNTING = "
        "TO_CHAR(d.FRONT_ID) THEN 'FRONT_ID' ELSE 'OTHER, length ' || LENGTH(d.REFERENCE_ACCOUNTING) END\n"
        "ORDER BY 1, 2, 3, 4;\n\n"
        "-- 3b. its origin, BOX_TRD.T_BOX_DEAL_S.ACCOUNTING_REF (the column p_Import_Deal_Data copies), against BO_CODE\n"
        "SELECT CASE WHEN ACCOUNTING_REF IS NULL THEN 'NULL' WHEN ACCOUNTING_REF = BO_CODE THEN 'BO_CODE' ELSE "
        "'OTHER, length ' || LENGTH(ACCOUNTING_REF) END KIND,\n       COUNT(*) N, MIN(ACCOUNTING_REF) EXAMPLE, MIN(BO_CODE) "
        "BO_CODE_EXAMPLE\nFROM BOX_TRD.T_BOX_DEAL_S WHERE FK_PARENT IS NULL AND FK_BO_STATUS = 3.65\n"
        "GROUP BY CASE WHEN ACCOUNTING_REF IS NULL THEN 'NULL' WHEN ACCOUNTING_REF = BO_CODE THEN 'BO_CODE' ELSE "
        "'OTHER, length ' || LENGTH(ACCOUNTING_REF) END ORDER BY 2 DESC;\n\n"
        "-- 3c. the column's type and length (a literal must fit)\n"
        "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE FROM ALL_TAB_COLUMNS\n"
        "WHERE OWNER IN ('BOX_FE', 'BOX_TRD') AND COLUMN_NAME IN ('REFERENCE_ACCOUNTING', 'ACCOUNTING_REF');\n\n"
        "-- 3d. who reads it after the import (a lookup or a format check would constrain the value)\n"
        "SELECT OWNER, NAME, TYPE, LINE, TRIM(TEXT) TEXT FROM ALL_SOURCE\n"
        "WHERE OWNER IN ('BOX_FE', 'BOX_ACC', 'BOX_TRD') AND UPPER(TEXT) LIKE '%REFERENCE_ACCOUNTING%'\n"
        "ORDER BY OWNER, NAME, LINE;\n\n"
        "-- 3. how deals already in BOX carry them (shape only: group, sub-product, the other online-flow fields, reference)\n"
        "SELECT d.DEAL_ID, d.INSTRUMENT, d.FK_INSTRUMTYPE, d.FK_TRDSUBTYPE, d.FK_MICROHEDGE, d.FK_STRATEGY, d.FK_DEALTREAT,\n"
        "       d.FK_ACCTDOC, d.FK_PORTPROP, p.FK_BRANCH PP_GROUP, p.FK_INSTRUMENT PP_SUBPRODUCT,\n"
        "       CASE WHEN d.REFERENCE_ACCOUNTING = TO_CHAR(d.DEAL_ID) THEN 'DEAL_ID' ELSE 'OTHER' END REFERENCE_KIND\n"
        "FROM BOX_FE.T_BOX_DEAL_DATA_S d JOIN BOX_ACC.T_BOX_ACCT_PORT_PROP_S p ON p.PK = d.FK_PORTPROP\n"
        f"WHERE d.DATEPROCESS = (SELECT MAX(DATEPROCESS) FROM BOX_FE.T_BOX_DEAL_DATA_S) AND ROWNUM <= 20;\n\n"
        f"-- 4. the update{' (+ extra_fields)' if xf else ''}\n"
        f"UPDATE BOX_FE.T_BOX_DEAL_DATA_S SET FK_PORTPROP = {ppv}, REFERENCE_ACCOUNTING = {rav}{ex_sql}\n"
        f"WHERE FRONT_ID IN ({fl}) AND DATEPROCESS = {dlit};\n"
        "-- rows updated = the rows of query 0 (one per leg), then COMMIT\n\n"
        + ("-- 5. check: each row's portfolio property exists, is Valid and of the instrument (any group: portprop_scope "
         "any)\n" if any_pp else
         "-- 5. check: each row's portfolio property exists, is Valid, of the target's group and the instrument\n")
        + "SELECT d.FRONT_ID, d.DIRECTION, d.DEAL_ID, d.FK_PORTPROP, d.REFERENCE_ACCOUNTING, p.FK_BRANCH, p.FK_INSTRUMENT,\n"
        "       CASE WHEN p.PK IS NULL THEN 'NO PORTPROP'"
        + ("" if any_pp else f" WHEN p.FK_BRANCH <> {group_pk} THEN 'OTHER GROUP'") + "\n"
        + (f"            WHEN p.FK_INSTRUMENT <> {sub} THEN 'OTHER INSTRUMENT'\n" if sub else "")
        + "            WHEN p.STATUS <> 'Valid' THEN 'NOT VALID' WHEN d.REFERENCE_ACCOUNTING IS NULL THEN 'NO REFERENCE'\n"
        "            ELSE 'OK' END STATUS\n"
        "FROM BOX_FE.T_BOX_DEAL_DATA_S d LEFT JOIN BOX_ACC.T_BOX_ACCT_PORT_PROP_S p ON p.PK = d.FK_PORTPROP\n"
        f"WHERE d.FRONT_ID IN ({fl}) AND d.DATEPROCESS = {dlit};\n",
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
            "(`sql/30-DEV-static-check.sql`, last two queries: `FK_BRANCH` = the branch, `DATETOPROCESS`) - `MISSING` -> run 2935.65 first.", ""]
    card += ["| # | Event group | Branch | Process date | Instrument | Label | From the jobs |", "|---|---|---|---|---|---|---|"]
    k = 0
    for g, n, lv in seq:
        k += 1
        js = [j for j in jobs if j[0] == g]
        if g == "2629.65":
            card.append(f"| {k}a | **bypass:** `sql/40-DEV-bypass-join.sql` "
                        f"({'check the join is LEFT' if jmode == 'already-left' else 'inner -> left join'}) | | | | | DEV only |")
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
    card += ["", "A re-run of 2629.65 resets `FK_PORTPROP` / `REFERENCE_ACCOUNTING` to NULL (its MERGE takes them from "
             "`BOX_TRD.T_BOX_DEAL_S`): run `sql/50` again before the insert group.", "", ("After the last step: nothing to restore - the LEFT join was in place before the test (`sql/49` shows which "
              "join is live)." if jmode == "already-left" else "After the last step: **`sql/49-DEV-bypass-rollback.sql`** - "
              "DEV back to the inner join (check query at its end).")]
    (run / "02-run-card.md").write_text("\n".join(card) + "\n", encoding="utf-8")

    # 60 - checks ---------------------------------------------------------------------------------------------------
    (sql / "60-DEV-checks.sql").write_text(
        f"-- DEV ({env}) - after each step (INFERRED table / column names - confirm; OPEN: the batch error log)\n"
        f"-- after 2629.65 Import Deal Data And Flow Data: one row per leg (also sql/50 query 0)\n"
        f"SELECT FRONT_ID, DIRECTION, DEAL_ID, STATUS, BOOK, FOLDER, INSTRUMENT, FK_STRATEGY, FK_PORTPROP, REFERENCE_ACCOUNTING "
        f"FROM BOX_FE.T_BOX_DEAL_DATA_S\nWHERE FRONT_ID IN ({fl}) AND DATEPROCESS = {dlit};\n"
        f"-- before {ins_grp}: sql/50-DEV-accounting-attrs.sql query 5 -> OK for each trade\n"
        f"SELECT FRONT_ID, SOURCESYSTEM, DIRECTION, COUNT(*) FROM BOX_FE.T_BOX_FLOW_DATA_S\n"
        f"WHERE FRONT_ID IN ({fl}) AND PROCESSDATE = {dlit} GROUP BY FRONT_ID, SOURCESYSTEM, DIRECTION;\n\n"
        f"-- after {ins_grp} {ins_name}\nSELECT * FROM BOX_FE.T_BOX_DATADEAL_S WHERE ROWNUM <= 50;   "
        "-- OPEN: its trade / date columns\n", encoding="utf-8")
    opens.append("the tables each event group feeds and the batch error log - to complete sql/60-DEV-checks.sql")

    # 01 plan + 03 results ---------------------------------------------------------------------------------------------
    plan = [f"# Technical test - {cfg.get('branch', '')} - {inst} - {env} - {date}", "",
            "| # | Step | Where | File |", "|---|---|---|---|",
            f"| 1 | Environment and test date: **{env}**, **{date}** | - | `{INPUTS}` |",
            *(["| 2 | RAW rows of the test trades already in DEV: check them (deal, flow, market data) | DEV | "
               "`sql/10-DEV-raw-check.sql` |", "| 3 | - (nothing to insert) | - | - |"] if raw_in_dev else
              ["| 2 | RAW tables for the test trades (deal, flow, market data) | PROD | `sql/10-PROD-raw-extract.sql` |",
               "| 3 | Insert the RAW rows in DEV | DEV | `01-evidence/10-raw-inserts.sql` (the output of 2) |"]),
            ("| 4 | QR prices of the test date already in DEV: check them | DEV | `sql/20-DEV-quote-prices-check.sql` |"
             if qr_in_dev else "| 4 | QR prices of the test date | PROD -> DEV | `sql/20-PROD-quote-prices.sql` |"),
            "| 5 | Static data: every alias MISSING created first; folder branch; label book; filters | DEV | "
            "`sql/30-DEV-static-check.sql` |",
            "| 6 | Bypass of the online flow: the join LEFT (before 2629.65 - check, or deploy), the accounting attributes "
            "(before the insert group) | DEV | `sql/40-…`, `sql/50-…` |",
            "| 7 | Run the event groups in order | SIGOM DEV | `02-run-card.md` |",
            "| 8 | Each step ends OK and its tables are fed; then the rollback | DEV | `sql/60-DEV-checks.sql`, "
            "`sql/49-…` |", "",
            "Return each query's output as a CSV in `01-evidence/` (named after the file: `30-static-check.csv` …); "
            "the agent records it in `03-results.md`.", "",
            "**Deal status:** not a filter of `p_Import_Deal_Data` (Live / Matured computed from the maturity; the BO "
            "status only in the join the bypass turns LEFT) - see OPEN below for the insert group.", "", "## OPEN - to answer before or during the test", ""]
    opens.append("deal status: not filtered by p_Import_Deal_Data (read) - does the insert group (c_Deal) filter on a "
                 "status? If not, nothing to do")
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
