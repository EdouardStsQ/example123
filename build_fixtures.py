#!/usr/bin/env python3
"""
Build the validator's two regression fixtures from the SQL templates.

    python3 scripts/tests/build_fixtures.py        # writes scripts/tests/fixtures/{good,run3-like}/

`good`      — the templates filled with FIXTURE values. Must pass with 0 FAIL.
`run3-like` — the defects the BOX FE expert found in run 3 (2026-09-23). Must FAIL on each.

⚠ Every number here is a fixture value for testing the validator. The auth code 99 is invented on
purpose so it can never be mistaken for a real environment's. Never copy a value from this file
into a run.
"""
from __future__ import annotations
import re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "agents/sigom-box-fe-configs-agent/templates"
OUT = Path(__file__).resolve().parent / "fixtures"

INSTR = ["20092.4", "2.4", "20.4", "20111.4", "20213.4", "20313.4"]
GENERATOR = ROOT / "scripts/evidence_to_sql.py"

# FIXTURE evidence: 38 quote refs on the GBO curve (with one duplicate row, as a real export may have),
# and accrual exceptions for NY plus another branch and an unapproved instrument, to exercise the filters.
QUOTE_CSV = '"PK","FK_OWNER_OBJ","FK_PARENT","FK_BS"\n' + "".join(
    f"{900+i}.35,1.35,1.35,{6400+i}.4\n" for i in range(38)) + "999.35,1.35,1.35,6400.4\n"
EXC_CSV = ("FK_INSTRUMENT,FK_STRATEGY,FK_INSTRTYPE,CRITERIAL,BRANCH_PK\n"
           + "".join(f"{i},142.4,,1,20007.4\n{i},143.4,5.4,1,20007.4\n" for i in INSTR)
           + "8.4,142.4,,1,20007.4\n"            # unapproved instrument — filtered out
           + "20092.4,144.4,,1,1651.44\n")       # another branch — filtered out

def generate(*args) -> str:
    return subprocess.run([sys.executable, str(GENERATOR), *args], capture_output=True,
                          text=True, check=True).stdout.strip()

def block(table, cols, vals):
    return (f"v_pk := F___SEQUENCE('{table}','X');  chk_pk(v_pk, '{table}');\n"
            f"  INSERT INTO BOX_FE.{table} ({', '.join(cols)})\n"
            f"  VALUES ({', '.join(vals)});")

step6 = "\n  ".join(block("T_BOX_ENGACCRCONF_S",
    ["PK","FK_OWNER_OBJ","FK_PARENT","FK_EXTENSION","FK_INSTRUMENT","FK_FEEFIRSTDAYSEL",
     "FK_INTFIRSTDAYSEL","INTCOMMONBASIS","BYTRIGGER","BYRESIDUAL","INTERVAL","FK_BASIS","FK_MDRBASIS"],
    ["v_pk","c_owner_conf","v_conf_pk","c_ext_accrconf",i,"3.4","3.4","1","1","0","377","2.4","NULL"])
    for i in INSTR)
step12 = "\n  ".join(block("T_BOX_ERRORS_FE_S",
    ["PK","FK_OWNER_OBJ","FK_BRANCH","FK_INSTRUMENT","LIMIT_ERRORS"],
    ["v_pk","c_owner_errors","c_branch_pk",i,"100"]) for i in INSTR)
step14a = block("T_BOX_ENGDAYS_MATURED_S",
    ["PK","FK_OWNER_OBJ","DDATE","FK_INSTRUMENT","NUM_DAYS"],
    ["v_pk","c_owner_days_matured","SYSDATE","20313.4","30"])

VALUES = {
    "BRANCH_CODE": "NY_SCH", "TARGET_ENV": "Tier 2 PRE (FIXTURE)", "ENV": "tier2-pre",
    "RUN_NO": "fixture", "RUN_DATE": "2026-09-23",
    "TARGET_AUTH_CODE": "99", "TARGET_PK_FRACTION": "0.99",
    "OWNER_ENGCONF": "35000126.65", "EXT_ENGCONF_X": "35001566.65", "EXT_ENGACCRCONF": "35001114.65",
    "EXT_CONFIG_ACCRUAL": "35001120.65", "EXT_CONF_BY_BOOK": "35006145.65",
    "OWNER_ENGFCURVE": "35000123.65", "EXT_ENGLKFC": "35001101.65",
    "OWNER_ERRORS_FE": "35000289.65", "OWNER_DAYS_MATURED": "35000145.65",
    "BRANCH_PK": "20007.4", "SOURCE_FRONT": "513.4", "DUMMY_BOOK_LABEL": "26391.4",
    "GBO_CONFIG_PK": "64408.35", "GBO_CURVE_PK": "1.35",
    "EXPECTED_QUOTE_REFS": "38", "EXPECTED_EXCEPTIONS": "12",
    "CONF_DESCRIPTION": "Configuracion -NY", "CURVE_DESCRIPTION": "NY Configuration Suc",
    "FK_CALENDAR": "83.4", "FK_CURRENCY": "159.4", "CURVE_FK_CURRENCY": "159.4",
    "QUOTE_REF_COLUMN": "FK_BS", "Q04C_OUTCOME": "A",
    "N_INSTRUMENTS": "6", "N_BOOK_ROWS": "12", "N_DAYS_MATURED": "1", "N_STEP8": "0",
    "BOOKS": "NY001", "BOOK_LABELS": "23958.44",
    "APPROVED_INSTRUMENTS": ", ".join(INSTR), "DAYS_MATURED_INSTRUMENTS": "20313.4",
    "SIGNER_6": "fixture SME", "SIGNER_11": "fixture SME", "SIGNER_12": "fixture SME",
    "SIGNER_14A": "fixture SME",
    "STEP_6_ROWS": step6, "STEP_12_ROWS": step12, "STEP_14A_ROWS": step14a,
    "STEP_8_LINE": "NY's GBO has none (Q-07)",
}
for k in ("2","3","4","5","6","7","11","12","14A"):
    VALUES[f"STATUS_{k}"] = "PROPOSED"

def fill(text: str) -> str:
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: VALUES[m.group(1)], text)
    assert "{{" not in out, "unfilled placeholder"
    return out

STEPS = ["1","2","3","4","4b","5","6","7","8","9","10","11","12","13","14a","14b"]

def findings(status_for):
    rows = "\n".join(f"| {s} | object | {status_for(s)} | [stated: fixture, 2026-09-23] Q-02 |" for s in STEPS)
    return "| Step | Object | Status | Evidence |\n|---|---|---|---|\n" + rows + "\n"

def inputs():
    return ("# Inputs (FIXTURE)\n\n"
            f"APPROVED_INSTRUMENTS: {', '.join(INSTR)}\n"
            "BRANCH_PK: 20007.4\nSOURCE_FRONT: 513.4\nDUMMY_BOOK_LABEL: 26391.4\n"
            "TARGET_AUTH_CODE: 99\nQUOTE_REF_COLUMN: FK_BS\n")

def base(folder: Path):
    if folder.exists():
        shutil.rmtree(folder)
    (folder / "01-evidence").mkdir(parents=True)
    (folder / "03-sql").mkdir()
    (folder / "01-evidence/Q-04c-quote-ref-column-gbo.csv").write_text(QUOTE_CSV)
    (folder / "01-evidence/Q-06c-accrual-exceptions-emit.csv").write_text(EXC_CSV)
    (folder / "01-evidence/Q-G4-preflight.csv").write_text("USER,DB,BOXFE_VISIBLE,DEVENG_VISIBLE\nX,Y,62,525\n")
    (folder / "01-evidence/Q-02-generic-gbo.csv").write_text("PK\n64408.35\n")
    (folder / "00-inputs.md").write_text(inputs())

def good():
    f = OUT / "good"; base(f)
    VALUES["QUOTE_REFS_LIST"] = generate("list", str(f / "01-evidence/Q-04c-quote-ref-column-gbo.csv"), "FK_BS")
    VALUES["EXCEPTION_ROWS"] = generate("rows", str(f / "01-evidence/Q-06c-accrual-exceptions-emit.csv"),
                                        "FK_INSTRUMENT,FK_STRATEGY,FK_INSTRTYPE,CRITERIAL",
                                        "--where", "BRANCH_PK=20007.4", "--in", "FK_INSTRUMENT=" + ",".join(INSTR))
    no_sql = {"1": "CONFIRMED_ABSENT", "4b": "CONFIRMED_ABSENT", "8": "CONFIRMED_ABSENT",
              "9": "CONFIRMED_ABSENT", "10": "CONFIRMED_ABSENT", "13": "CONFIRMED_PRESENT",
              "14b": "NOT_BRANCH_SCOPED"}
    (f / "02-findings.md").write_text(findings(lambda s: no_sql.get(s, "PROPOSED")))
    (f / "00-decisions.md").write_text(
        "| # | Decision | Value | Name | Role | Date | Evidence |\n|---|---|---|---|---|---|---|\n"
        "| 1 | Step 6 accrual values | NY GBO | fixture SME | product SME | 2026-09-24 | Q-05, Q-05d |\n"
        "| 2 | Step 11 books | 23958.44 | fixture SME | product SME | 2026-09-24 | Q-10 |\n"
        "| 3 | Step 11 dummy label | 26391.4 | fixture BOX FE | BOX FE team | 2026-09-24 | Q-10d |\n")
    for name in ("config", "verify", "rollback"):
        (f / f"03-sql/NY_SCH-tier2-pre-{name}.sql").write_text(fill((TPL / f"{name}.sql.tmpl").read_text()))

RUN3 = """-- NY_SCH Tier 2 PRE steps 1 to 11 (run-3-like FIXTURE)
DECLARE
  v_conf_pk NUMBER; v_curve_pk NUMBER; v_pk NUMBER;
  v_quote_refs sys.odcinumberlist := sys.odcinumberlist(6401.4, 6402.4, 6403.4);
BEGIN
  -- STEP 2 — header. 1 row.
  -- If wrong: wrong config
  v_conf_pk := F___SEQUENCE('T_BOX_ENGCONF_S','X');
  INSERT INTO BOX_FE.T_BOX_ENGCONF_S (PK, FK_OWNER_OBJ, DESCRIPTION, FK_CALENDAR, FK_CURRENCY,
    FK_CURVEMAN, FK_CURVEACC, FK_SOURCE_FRONT, FK_SOURCE_BACK)
  VALUES (v_conf_pk, &&QG6_OWNER_ENGCONF, 'Configuracion -NY', 83.4, 159.4, NULL, NULL, 9.4, 11.4);
  -- STEP 3 — curve. 1 row.
  v_curve_pk := F___SEQUENCE('T_BOX_ENGFCURVE_S','X');
  INSERT INTO BOX_FE.T_BOX_ENGFCURVE_S (PK, FK_OWNER_OBJ, DESCRIPTION, FK_CURRENCY)
  VALUES (v_curve_pk, &&QG6_OWNER_ENGFCURVE, 'NY Configuration Suc', 159.4);
  -- STEP 4 — quote refs. 3 rows.
  FOR i IN 1 .. v_quote_refs.COUNT LOOP
    v_pk := F___SEQUENCE('T_BOX_ENGLKFC_X','X');
    INSERT INTO BOX_FE.T_BOX_ENGLKFC_X (PK, FK_OWNER_OBJ, FK_EXTENSION, FK_PARENT, FK_BS)
    VALUES (v_pk, &&QG6_OWNER_ENGFCURVE, &&QG6_EXTENSION_ENGLKFC_X, v_curve_pk, v_quote_refs(i));
  END LOOP;
  UPDATE BOX_FE.T_BOX_ENGCONF_S SET FK_CURVEMAN = v_curve_pk, FK_CURVEACC = v_curve_pk WHERE PK = v_conf_pk;
  -- STEP 7 — exceptions. 1 row.
  v_pk := F___SEQUENCE('T_BOX_CONFIG_ACCRUAL_S','X');
  INSERT INTO BOX_FE.T_BOX_CONFIG_ACCRUAL_S (PK, FK_OWNER_OBJ, FK_PARENT, FK_EXTENSION, CRITERIAL,
    FK_BRANCH, FK_INSTRUMENT, FK_STRATEGY)
  VALUES (v_pk, 35000126.65, v_conf_pk, 35001120.65, 1, 141.35, 20092.4, 142.4);
  -- STEP 11 — book. 1 row.
  v_pk := F___SEQUENCE('T_BOX_CONF_BY_BOOK_S','X');
  INSERT INTO BOX_FE.T_BOX_CONF_BY_BOOK_S (PK, FK_OWNER_OBJ, FK_PARENT, FK_EXTENSION, FK_BRANCH,
    FK_INSTRUMENT, FK_LABEL)
  VALUES (v_pk, 35000126.65, v_conf_pk, 35006145.65, 20007.4, 20092.4, 23958.44);
  IF 1 = 0 THEN
    DELETE FROM BOX_FE.T_BOX_ENGCONF_S WHERE PK = v_conf_pk;
  END IF;
END;
/
"""

def run3_like():
    f = OUT / "run3-like"; base(f)
    (f / "02-findings.md").write_text(findings(lambda s: "PROPOSED"))
    (f / "03-sql/NY_SCH-tier2-pre-steps-1-to-11.sql").write_text(RUN3)

if __name__ == "__main__":
    good(); run3_like()
    print(f"fixtures written to {OUT}")
