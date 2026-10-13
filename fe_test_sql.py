"""
fe_test_sql.py - SQL shared by the BOX FE tests (technical test, Y test, parallel test) [lessons of the NY_SCH
technical test, operator 2026-10-13]. Imported by fe_tech_test.py and fe_reconcile.py; no agent runs SQL.

  stage_checks(...)   after each key step, the rows the step must have written for the test trades - 0 rows with
                      the step ended OK is a failure ("the process didn't fail but there was no data")
  diagnose(...)       for an event group: its events, the procedures of their Update / Calculate entries
                      (T_PGT_UPDATE_S.TXFUNCNAME), and the lines of those packages that filter (INSTRUMENT, BOOK,
                      SOURCESYSTEM, dates...) - to find WHY nothing was written (e.g. p_Import_Mtm_Data filters
                      mtm.INSTRUMENT = 'Loan / Depos' while the RAW market data rows carry 'Deposit')
  instrument_check()  the INSTRUMENT text of each RAW table for the trades against the text the procedures expect
  static_tables()     where each aliased static object lives (GOM_GLB_SYS.T__OBJ_DEF_S.BASIC_STORAGE of the alias's
                      FK_OWNER_OBJ - e.g. counterparty 1448.4 -> PGT_STC.T_PGT_ENTITY_S), so no test has to search
  financial_pair()    GBO (PROD) vs BOX (DEV) product financial data of the trades, both keyed by FRONT_ID through the
                      product's deal table (GBO DEVENG.T_PGT_<GBO code>DATAMIS_S, BOX BOX_FE.T_BOX_DEAL_DATA_S); the
                      GBO / BOX codes from docs/reference/gbo-box-product-tables.csv - they differ (CCS = SW, ...)

Table and column names marked INFERRED in docs/reference/box-fe-test-lookups.md are written with a comment; a query
that fails on a column (ORA-00904) is answered with the table's columns (the query listing them is written too).
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

# the GBO / BOX product tables of the SIGOM Financial Status menus [operator screenshots, 2026-10-13]: the codes
# DIFFER between the two systems (BOX CCS = GBO SW "CS (Currency Swap)", CFM = IF, CDS = CD, FRA = FR, OTC = OB / OE /
# OF / OI / OS, FX = SP / NDS / FP / FM; MM, IR, CF the same)
PRODUCT_TABLES = Path(__file__).resolve().parent.parent / "docs/reference/gbo-box-product-tables.csv"
PRODUCT_CODE = {"depos": "MM", "irs": "IR", "ccs": "CCS", "otc": "OTC", "cap": "CF", "cfm": "CFM", "fra": "FRA",
                "fx": "FX", "commodities": "CES", "cds": "CDS", "brs": "BRS"}     # BOX code (fallback)


def product_tables() -> list:
    return list(csv.DictReader(PRODUCT_TABLES.open(encoding="utf-8"))) if PRODUCT_TABLES.exists() else []


def box_code(product: str) -> str:
    r = next((r for r in product_tables() if r["side"] == "BOX" and r["box_product"] == product), None)
    return r["code"] if r else PRODUCT_CODE.get(product, "<CODE>")


def gbo_products(product: str) -> list:
    """The GBO product rows of a BOX product (one, or several: OTC -> 5, FX -> 4); [] = no GBO counterpart known."""
    return [r for r in product_tables() if r["side"] == "GBO" and r["box_product"] == product]


def gbo_code_of(table: str) -> str:
    m = re.search(r"T_PGT_([A-Z0-9]+?)(DATAMIS|FINANCST|RISK)_S", str(table).upper())
    return m.group(1) if m else ""


# the product's insert event group (step 7 of the FE process) and the RAW INSTRUMENT text the import procedures
# filter on (p_Import_Deal_Data's decode, operator screenshot 2026-10-09; cap 3922.65 from SLB's chain)
INSERT_GROUPS = {"depos": ("2631.65", "Insert BOX MM Deal Data"), "commodities": ("2490.65", "Insert BOX CES Deal Data"),
                 "irs": ("2835.65", "Insert BOX IRS Deal Data"), "ccs": ("3255.65", "Insert BOX CCS Deal Data"),
                 "cfm": ("3479.65", "Insert BOX CFM Deal Data"), "fra": ("3661.65", "Insert BOX FRA Deal Data"),
                 "fx": ("3155.65", "Insert BOX FX Deal Data"), "otc": ("3803.65", "Insert BOX OTC Deal Data"),
                 "cap": ("3922.65", "Insert BOX CF Deal Data")}
RAW_INSTRUMENT = {"depos": "Loan / Depos", "irs": "IRS", "commodities": "Commodity Swap", "ccs": "Currency Swap",
                  "cds": "CDS", "cfm": "CFM", "fra": "FRA", "otc": "OTC", "cap": "Cap and Floor", "brs": "Bond Return Swap"}
FILTER_WORDS = "INSTRUMENT|BOOK|SOURCESYSTEM|PROCESSDATE|DATEPROCESS|DATA_EXECUTION_TYPE|STATUS|DIRECTION|FK_BRANCH"


def q(xs) -> str:
    return ", ".join("'" + str(x).replace("'", "''") + "'" for x in xs)


def columns(owner: str, table: str) -> str:
    return (f"SELECT COLUMN_NAME, DATA_TYPE FROM ALL_TAB_COLUMNS WHERE OWNER = '{owner}' AND TABLE_NAME = '{table}' "
            "ORDER BY COLUMN_ID;\n")


def deal_ids(fids, dlit) -> str:
    return (f"SELECT DISTINCT DEAL_ID FROM BOX_FE.T_BOX_DEAL_DATA_S WHERE FRONT_ID IN ({q(fids)}) "
            f"AND DATEPROCESS = {dlit}")


def stage_checks(fids, dlit, product: str, ins_grp: str, ins_name: str) -> dict:
    """{step: sql} - the rows each key step must have written for the trades (expected: > 0 per trade)."""
    code = box_code(product)
    return {
        "2629.65": (
            "-- after 2629.65 Import Deal Data And Flow Data - expected: one row per trade and leg, and its flows\n"
            "SELECT FRONT_ID, SOURCESYSTEM, DIRECTION, DEAL_ID, STATUS, BOOK, FOLDER, INSTRUMENT, FK_PORTPROP, "
            "REFERENCE_ACCOUNTING\n"
            f"FROM BOX_FE.T_BOX_DEAL_DATA_S WHERE FRONT_ID IN ({q(fids)}) AND DATEPROCESS = {dlit};\n"
            "SELECT FRONT_ID, SOURCESYSTEM, DIRECTION, COUNT(*) N FROM BOX_FE.T_BOX_FLOW_DATA_S\n"
            f"WHERE FRONT_ID IN ({q(fids)}) AND PROCESSDATE = {dlit} GROUP BY FRONT_ID, SOURCESYSTEM, DIRECTION;\n"),
        "2632.65": (
            "-- after 2632.65 Import Mtm Data - expected: the trades' MtM rows [table: operator 2026-10-13; key columns\n"
            "-- INFERRED - on ORA-00904 use the column list below]. 0 rows with the step ended OK -> sql/70 (2632.65)\n"
            f"SELECT * FROM BOX_FE.T_BOX_MTM_DATA_S WHERE FRONT_ID IN ({q(fids)});\n"
            + columns("BOX_FE", "T_BOX_MTM_DATA_S")),
        ins_grp: (
            f"-- after {ins_grp} {ins_name} - expected: the trades in the product tables (DEAL_ID from the deal data)\n"
            f"SELECT * FROM BOX_FE.T_BOX_DATADEAL_S WHERE DEAL_ID IN ({deal_ids(fids, dlit)});   -- key INFERRED\n"
            f"SELECT * FROM BOX_FE.T_BOX_{code}FINANCST_S WHERE DEAL_ID IN ({deal_ids(fids, dlit)}) AND DDATE = {dlit};\n"
            + columns("BOX_FE", "T_BOX_DATADEAL_S")),
    }


def diagnose(groups, catalog: str = "PGT_PRC") -> str:
    """Why an event group wrote nothing: its events, their procedures, the filtering lines of those packages."""
    g = ", ".join(groups)
    fx = (f"SELECT DISTINCT x.FK_PARENT GRP, x.ORDERTOEXECUTE, x.EVENTCODE, u.TXFUNCNAME,\n"
          "       UPPER(REGEXP_SUBSTR(u.TXFUNCNAME, '[^.]+', 1, 1)) OWN, UPPER(REGEXP_SUBSTR(u.TXFUNCNAME, '[^.]+', 1, 2)) "
          "PKG,\n       UPPER(REGEXP_SUBSTR(u.TXFUNCNAME, '[^.]+', 1, 3)) PRC\n"
          f"FROM {catalog}.T_PGT_BR_EVE_EXT_S x JOIN {catalog}.T_PGT_UPDATE_S u ON u.FK_PARENT = x.EVENTCODE\n"
          f"WHERE x.FK_PARENT IN ({g})")
    return (
        f"-- Diagnose an event group that ended OK but wrote nothing for the test trades [lesson, 2026-10-13]. Run in\n"
        "-- the test environment, return each output as a CSV: the agent reads the procedure's filters and compares\n"
        "-- them with the RAW rows (sql/30, INSTRUMENT check) - the first mismatch is the root cause.\n\n"
        f"-- D1. the group's events, in order (J-C2)\nSELECT x.FK_PARENT GRP, x.ORDERTOEXECUTE, x.EVENTCODE, e.NAME, "
        "e.FK_INSTRUMENT\n"
        f"FROM {catalog}.T_PGT_BR_EVE_EXT_S x JOIN {catalog}.T_PGT_EVE_S e ON e.PK = x.EVENTCODE\n"
        f"WHERE x.FK_PARENT IN ({g}) ORDER BY 1, 2;\n\n"
        "-- D2. the procedure of each event (SIGOM event config, Update / Calculate tab = T_PGT_UPDATE_S.TXFUNCNAME)\n"
        f"{fx}\nORDER BY 1, 2;\n\n"
        "-- D3. the event's own selection (SIGOM query tabs: FROM / WHERE / SELECT)\n"
        f"SELECT x.FK_PARENT GRP, x.ORDERTOEXECUTE, c.* FROM {catalog}.T_PGT_BR_EVE_EXT_S x\n"
        f"JOIN {catalog}.T_PGT_COND_S c ON c.FK_PARENT = x.EVENTCODE WHERE x.FK_PARENT IN ({g}) ORDER BY 1, 2;\n\n"
        f"-- D4. the lines of those packages that filter ({FILTER_WORDS.replace('|', ', ')}) - the cursor's WHERE\n"
        f"WITH p AS ({fx})\n"
        "SELECT p.GRP, p.TXFUNCNAME, s.LINE, TRIM(s.TEXT) TEXT FROM p\n"
        "JOIN ALL_SOURCE s ON s.OWNER = p.OWN AND s.NAME = p.PKG AND s.TYPE = 'PACKAGE BODY'\n"
        f"WHERE REGEXP_LIKE(UPPER(s.TEXT), '{FILTER_WORDS}') ORDER BY 1, 2, 3;\n\n"
        "-- D5. the whole package body of one procedure, when D4 is not enough (set &&OWN / &&PKG from D2)\n"
        "-- SELECT LINE, TEXT FROM ALL_SOURCE WHERE OWNER = '&&OWN' AND NAME = '&&PKG' AND TYPE = 'PACKAGE BODY' "
        "ORDER BY LINE;\n")


def instrument_check(fids, dlit, expected: str) -> str:
    """The INSTRUMENT text of each RAW table for the trades vs the text the import procedures filter on."""
    out = [f"-- INSTRUMENT text per RAW table for the trades - expected '{expected}' (the text the import procedures\n"
           "-- filter on: p_Import_Deal_Data / p_Import_Mtm_Data). A MISMATCH imports nothing and does not fail\n"
           "-- [lesson, 2026-10-13: the RAW market data carried 'Deposit', p_Import_Mtm_Data expects 'Loan / Depos'].\n"]
    for t in ("T_BOX_RAW_DEAL_DATA_S", "T_BOX_RAW_MARKET_DATA_S", "T_BOX_RAW_FLOW_DATA_S"):
        out.append(f"SELECT '{t}' TBL, INSTRUMENT, COUNT(*) N, CASE WHEN INSTRUMENT = '{expected}' THEN 'OK' ELSE "
                   f"'MISMATCH' END STATUS\nFROM BOX_FE.{t} WHERE FRONT_ID IN ({q(fids)}) AND TRUNC(PROCESSDATE) = "
                   f"{dlit}\nGROUP BY INSTRUMENT;" + ("   -- ORA-00904: this table has no INSTRUMENT column, skip"
                                                     if "FLOW" in t else "") + "\n")
    return "\n".join(out)


def static_tables(owner_objs) -> str:
    """Where each aliased static object is stored - no test searches for the counterparty table again."""
    return ("-- where each aliased static object lives (its SIGOM object's BASIC_STORAGE): e.g. 1448.4 counterparty ->\n"
            "-- PGT_STC.T_PGT_ENTITY_S [operator, 2026-10-13]\n"
            "SELECT PK, PK_NAME, BASIC_STORAGE, EXT_STORAGE FROM GOM_GLB_SYS.T__OBJ_DEF_S\n"
            f"WHERE PK IN ({', '.join(sorted(set(owner_objs)))}) ORDER BY PK;\n")


def financial_pair(fids, dlit, product: str, gbo_env: str = "PROD", box_env: str = "DEV") -> tuple[str, str]:
    """GBO and BOX product financial data of the trades, FRONT_ID added through each side's deal table. A BOX
    product with several GBO products (OTC, FX) gets one GBO statement per GBO table, each exported to its own CSV."""
    code = box_code(product)
    gps = gbo_products(product)
    if not gps:
        gbo = (f"-- GBO ({gbo_env}) - {product}: no GBO product known for it in docs/reference/gbo-box-product-tables.csv "
               "- OPEN (which GBO Financial Status menu holds these trades?)\n")
    else:
        gbo = (f"-- GBO ({gbo_env}) - {product} financial data of the trades: {', '.join(r['menu'] for r in gps)} "
               f"[{gps[0]['status']}; tables: operator screenshots 2026-10-13].\n-- By DEAL_ID and DDATE; FRONT_ID from "
               "the product's GBO deal table. Export each statement as CSV with header.\n")
        for r in gps:
            c = r["code"]
            gbo += (f"\n-- {r['menu']} -> 01-evidence/80-gbo-financial{'-' + c if len(gps) > 1 else ''}.csv\n"
                    f"SELECT d.FRONT_ID, f.*\nFROM {r['financial_table']} f\n"
                    f"JOIN (SELECT DISTINCT DEAL_ID, FRONT_ID FROM {r['deal_table']} WHERE FRONT_ID IN ({q(fids)})) d\n"
                    f"  ON d.DEAL_ID = f.DEAL_ID\nWHERE f.DDATE = {dlit}\nORDER BY 1;\n")
    box = (f"-- BOX ({box_env}) - {product} financial data of the trades [BOX_FE.T_BOX_{code}FINANCST_S by DEAL_ID and\n"
           "-- DDATE; FRONT_ID from BOX_FE.T_BOX_DEAL_DATA_S]. Export as CSV with header -> 01-evidence/81-box-financial.csv\n"
           f"SELECT d.FRONT_ID, f.*\nFROM BOX_FE.T_BOX_{code}FINANCST_S f\n"
           f"JOIN (SELECT DISTINCT DEAL_ID, FRONT_ID FROM BOX_FE.T_BOX_DEAL_DATA_S WHERE FRONT_ID IN ({q(fids)})\n"
           f"      AND DATEPROCESS = {dlit}) d ON d.DEAL_ID = f.DEAL_ID\nWHERE f.DDATE = {dlit}\nORDER BY 1;\n")
    return gbo, box
