#!/usr/bin/env python3
"""
Build the regression fixtures.

    python3 scripts/tests/build_fixtures.py        # writes scripts/tests/fixtures/{good,run3-like}/

`good`      — a complete run folder (inputs, decisions, findings, evidence, 03-sql/values.json) whose SQL is
              RENDERED by scripts/render_sql.py, exactly as a run does it. Must pass the validator with 0 FAIL.
`run3-like` — the defects the BOX FE expert found in run 3 (2026-09-23), hand-written. Must FAIL on each.

⚠ Every number here is a fixture value for testing. The auth code 99 is invented on purpose so it can never
be mistaken for a real environment's. Never copy a value from this file into a run.
"""
from __future__ import annotations
import copy, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))
import render_sql  # noqa: E402

INSTR = ["20092.4", "2.4", "20.4", "20111.4", "20213.4", "20313.4"]
NAMES = ["Swap", "Deposit & Loan", "Cross Currency Swap", "OTC Option", "Caps And Floors", "Credit Derivatives"]

# FIXTURE evidence: 38 quote refs on the GBO curve (plus one duplicate row, as a real export may have),
# and accrual exceptions for the branch plus another branch and an unapproved instrument, to exercise the filters.
QUOTE_CSV = ('"BRIDGE_PK","FK_BS","QUOTE_REF_PK","QUOTE_TYPE","QUOTE_SOURCE","CURRENCY_PAIR"\n'
             + "".join(f"{900+i}.35,{6400+i}.4,{6400+i}.4,FX,REUTERS,USD/X{i}\n" for i in range(38))
             + "999.35,6400.4,6400.4,FX,REUTERS,USD/X0\n")
COUNTS_CSV = "N_ROWS,N_FK_BS,N_RESOLVED\n39,38,39\n"
EXC_CSV = ("FK_INSTRUMENT,FK_STRATEGY,FK_INSTRTYPE,CRITERIAL,BRANCH_PK,BRANCH,GBO_ROW_PK\n"
           + "".join(f"{i},142.4,,1,20007.4,NEW YORK,{n}1.35\n{i},143.4,5.4,1,20007.4,NEW YORK,{n}2.35\n"
                     for n, i in enumerate(INSTR))
           + "8.4,142.4,,1,20007.4,NEW YORK,991.35\n"          # unapproved instrument — filtered out
           + "20092.4,144.4,,1,1651.44,OTHER BRANCH,992.35\n")  # another branch — filtered out


NOT_NULL = {"PK", "FK_OWNER_OBJ", "DESCRIPTION", "FK_CURRENCY", "FK_CURVEMAN", "FK_CURVEACC",
            "FK_FEEFIRSTDAYSEL", "FK_INTFIRSTDAYSEL", "INTCOMMONBASIS", "BYTRIGGER"}


def columns_csv() -> str:
    """FIXTURE Q-G3d (e): every column the templates use, plus one NOT NULL column WITH a default per table
    (must not be demanded) and one nullable extra (must be ignored)."""
    out = ["TABLE_NAME,COLUMN_NAME,DATA_TYPE,DATA_LENGTH,NULLABLE,HAS_DEFAULT"]
    for table, (_, cols) in render_sql.WRITES.items():
        for c in (["PK"] if table == "T_BOX_FIXING_BY_INSTR_S" else []) + cols:
            typ, n = ("VARCHAR2", 100) if c == "DESCRIPTION" else ("DATE", 7) if c == "DDATE" else ("NUMBER", 22)
            out.append(f"{table},{c},{typ},{n},{'N' if c in NOT_NULL else 'Y'},N")
        out.append(f"{table},AUDIT_TS,DATE,7,N,Y")
        out.append(f"{table},REMARKS,VARCHAR2,200,Y,N")
    return "\n".join(out) + "\n"


def v(value, source):
    return {"value": value, "source": source}


VALUES = {
    "_readme": "FIXTURE values for the validator's tests - never a source for a run",
    "run": {"run_no": "fixture", "run_date": "2026-09-24", "branch_code": "NY_SCH",
            "target_env": "Tier 2 PRE (FIXTURE)", "env_slug": "tier2-pre"},
    "environment": {"target_auth_code": v("99", "Q-G3c (a)"),
                    "sequence_function_owner": v("BOX_FE", "Q-G3b (b)"),
                    "precommit_package_owner": v("BOX_FE", "Q-G3b (d)")},
    "identity": {k: v(val, "Q-G7 / Q-G6") for k, val in (
        ("owner_engconf", "35000126.65"), ("ext_engconf_x", "35001566.65"), ("ext_engaccrconf", "35001114.65"),
        ("ext_config_accrual", "35001120.65"), ("ext_conf_by_book", "35006145.65"),
        ("owner_engfcurve", "35000123.65"), ("ext_englkfc", "35001101.65"),
        ("owner_errors_fe", "35000289.65"), ("owner_days_matured", "35000145.65"))},
    "branch": {"branch_pk": v("20007.4", "Q-G1; 00-inputs.md BRANCH_PK"),
               "source_front": v("513.4", "00-inputs.md SOURCE_FRONT; Q-02c"),
               "approved_instruments": [{"value": i, "name": n, "source": "00-inputs.md APPROVED_INSTRUMENTS"}
                                        for i, n in zip(INSTR, NAMES)]},
    "gbo": {"config_pk": v("64408.35", "Q-G2 level 1"), "curve_pk": v("1.35", "Q-02 FK_CURVEMAN; Q-03")},
    "steps": {
        "1": {"status": "CONFIRMED_ABSENT", "source": "Q-01"},
        "2": {"status": "PROPOSED", "source": "Q-02", "description": v("Configuracion -NY", "Q-02"),
              "fk_calendar": v("83.4", "Q-02"), "fk_currency": v("159.4", "Q-02")},
        "3": {"status": "PROPOSED", "source": "Q-03", "description": v("NY Configuration Suc", "Q-03"),
              "fk_currency": v("159.4", "Q-03")},
        "4": {"status": "PROPOSED", "source": "Q-04c", "expected_count": v(38, "Q-04c (b)")},
        "4b": {"status": "CONFIRMED_ABSENT", "source": "Q-G7"},
        "5": {"status": "PROPOSED", "source": "Q-01c"},
        "6": {"status": "PROPOSED", "source": "Q-05, Q-05d", "decisions": [1],
              "rows": [{"FK_INSTRUMENT": i, "FK_FEEFIRSTDAYSEL": "3.4", "FK_INTFIRSTDAYSEL": "3.4",
                        "INTCOMMONBASIS": 1, "BYTRIGGER": 1, "BYRESIDUAL": 0, "INTERVAL": 377,
                        "FK_BASIS": "2.4", "FK_MDRBASIS": None, "source": "decision 1; Q-05"} for i in INSTR]},
        "7": {"status": "PROPOSED", "source": "Q-06, Q-06c", "expected_count": v(12, "Q-06c")},
        "8": {"status": "CONFIRMED_ABSENT", "source": "Q-07"},
        "9": {"status": "CONFIRMED_ABSENT", "source": "Q-08"},
        "10": {"status": "CONFIRMED_ABSENT", "source": "Q-09"},
        "11": {"status": "PROPOSED", "source": "Q-10, Q-10d", "decisions": [2, 3],
               "books": [{"value": "23958.44", "name": "NY001", "source": "decision 2; Q-10"}],
               "dummy_book": {"value": "2741.44", "name": "BR00 - BR DUMMY", "source": "decision 3; Q-10d"}},
        "12": {"status": "PROPOSED", "source": "Q-13 (b), ADR 0004", "decisions": [4],
               "rows": [{"FK_INSTRUMENT": i, "LIMIT_ERRORS": 115 if i == "20.4" else 100,
                         "source": "decision 4; Q-13 (b)"} for i in INSTR]},
        "13": {"status": "CONFIRMED_PRESENT", "source": "Q-11"},
        "14a": {"status": "PROPOSED", "source": "Q-12 (a), Q-12 (b)", "decisions": [5],
                "already_present": [{"value": i, "source": "Q-12 (a)"} for i in INSTR if i != "20213.4"],
                "ddate": v("SYSDATE", "decision 5"),
                "rows": [{"FK_INSTRUMENT": "20213.4", "NUM_DAYS": 30, "source": "decision 5; Q-12 (b)"}]},
        "14b": {"status": "NOT_BRANCH_SCOPED", "source": "Q-12"},
    },
}

DECISIONS = ("| # | Decision | Value | Name | Role | Date | Evidence |\n|---|---|---|---|---|---|---|\n"
             "| 1 | Step 6 accrual values | NY GBO | fixture SME | product SME | 2026-09-24 | Q-05, Q-05d |\n"
             "| 2 | Step 11 books | 23958.44 | fixture SME | product SME | 2026-09-24 | Q-10 |\n"
             "| 3 | Step 11 dummy label | 2741.44 | fixture BOX FE | BOX FE team | 2026-09-24 | Q-10d |\n"
             "| 4 | Step 12 limits | SLB's | fixture SME | product SME | 2026-09-24 | Q-13 (b) |\n"
             "| 5 | Step 14a days | 30 | fixture SME | product SME | 2026-09-24 | Q-12 (b) |\n")


def findings_md(values) -> str:
    rows = "\n".join(f"| {s} | object | {st['status']} | [stated: fixture, 2026-09-24] {st['source']} |"
                     for s, st in values["steps"].items())
    return "| Step | Object | Status | Evidence |\n|---|---|---|---|\n" + rows + "\n"


def inputs_md() -> str:
    return ("# Inputs (FIXTURE)\n\n"
            f"APPROVED_INSTRUMENTS: {', '.join(INSTR)}\n"
            "BRANCH_PK: 20007.4\nREFERENCE_BRANCH_PK: 20087.4\nSOURCE_FRONT: 513.4\nDUMMY_BOOK_LABEL: 2741.44\n"
            "TARGET_AUTH_CODE: 99\nTARGET_PK_FRACTION: 0.99\nQUOTE_REF_COLUMN: FK_BS\n")


def base(folder: Path):
    if folder.exists():
        shutil.rmtree(folder)
    (folder / "01-evidence").mkdir(parents=True)
    (folder / "03-sql").mkdir()
    (folder / "01-evidence/Q-04c-quote-ref-column-gbo.csv").write_text(QUOTE_CSV)
    (folder / "01-evidence/Q-04c-quote-ref-column-counts.csv").write_text(COUNTS_CSV)
    (folder / "01-evidence/Q-06c-accrual-exceptions-emit.csv").write_text(EXC_CSV)
    (folder / "01-evidence/Q-G3d-columns.csv").write_text(columns_csv())
    (folder / "01-evidence/Q-G4-preflight.csv").write_text("USER,DB,BOXFE_VISIBLE,DEVENG_VISIBLE\nX,Y,62,525\n")
    (folder / "01-evidence/Q-02-generic-gbo.csv").write_text("PK\n64408.35\n")
    (folder / "00-inputs.md").write_text(inputs_md())


def write_run(folder: Path, values: dict, render: bool = True) -> render_sql.Result | None:
    """A full run folder from `values`; renders the SQL like a run does. Returns the render result."""
    base(folder)
    (folder / "02-findings.md").write_text(findings_md(values))
    for q in sorted(set(re.findall(r"\bQ-[\w]+\b", findings_md(values)))):   # one stub CSV per query cited
        stub = folder / "01-evidence" / f"{q}-fixture.csv"
        if not any((folder / "01-evidence").glob(f"{q}-*")):
            stub.write_text("FIXTURE\n1\n")
    (folder / "00-decisions.md").write_text(DECISIONS)
    (folder / "03-sql/values.json").write_text(json.dumps(values, indent=2))
    if not render:
        return None
    res = render_sql.render(folder)
    for name, text in res.files.items():
        (folder / "03-sql" / name).write_text(text, encoding="ascii", newline="\n")
    return res


def good() -> render_sql.Result:
    res = write_run(OUT / "good", copy.deepcopy(VALUES))
    assert not res.errors, res.errors
    return res


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
    f = OUT / "run3-like"
    base(f)
    vals = copy.deepcopy(VALUES)
    for st in vals["steps"].values():
        st["status"] = "PROPOSED"
    (f / "02-findings.md").write_text(findings_md(vals))
    (f / "03-sql/NY_SCH-tier2-pre-steps-1-to-11.sql").write_text(RUN3)


if __name__ == "__main__":
    good()
    run3_like()
    print(f"fixtures written to {OUT}")
