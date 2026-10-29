#!/usr/bin/env python3
"""Tests of scripts/render_acc_sql.py - sigom-box-acc-configs-agent phase 2 (ADR 0022). No database needed.
Run: python3 scripts/tests/test_render_acc_sql.py"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import render_acc_sql as ra

sys.path.insert(0, str(ROOT / "scripts/tests"))
from test_validate_run_output import plsql_lint  # the repo's one PL/SQL structure lint

FAILS = []


def report(ok, what, detail=""):
    print(("✓ " if ok else "✗ ") + what)
    if not ok:
        FAILS.append(what)
        if detail:
            print("    " + str(detail)[:900])


VALUES = {
    "branch": "NY_SCH", "env": "tier2-dev", "auth_code": 44, "group_pk": 21447.4, "branch_pk": 20007.4,
    "owners": {},
    "global_pk": {"T_BOX_ACCT_TOPICS_S": {"start": "next-free", "source": "operator 2026-10-28, DEV test"}},
    "global_topics": [{"row": {"CODE": "FXNEWTOPIC", "DESCRIPTION": "FX new topic"}, "key_columns": ["CODE"],
                       "source": "A-06 l.12"}],
    "accounts": [{"row": {"CODE": "9970201-939617", "DESCRIPTION": "acc O'Brien"}, "source": "A-10a l.3",
                  "date_rule": {"row": {"INIDATE": {"date": "1900-01-01"}}}}],
    "local_properties": [{"key": "lo-otc", "instrument_pk": 20111.4, "inivalpcdate": "1900-01-01",
                          "global_topics": ["FXNEWTOPIC", "CASH"], "local_topics": ["FXCONTROL"],
                          "internal_topics": ["INTTOPIC"], "conditions": [1515.21, 1514.21], "source": "ADR 0020"}],
    "portfolio_properties": [
        {"key": "gbo-2485.35", "instrument_pk": 20111.4, "inivalpcdate": "1900-01-01", "description": "OTC prop 1",
         "conditions": [{"cond_pk": 1515.21, "column": "VALUE_FUNC", "value": "Swaption"},
                        {"cond_pk": 1514.21, "column": "FK_STRATEGY", "value": 3.4}],
         "accounts": {"global": {"FXNEWTOPIC": "9970201-939617", "CASH": "817904-840"},
                      "local": {"FXCONTROL": "TCPV"}, "internal": {"INTTOPIC": "INTERNAL"}},
         "source": "A-04d l.4"},
        {"key": "gbo-2487.35", "instrument_pk": 20111.4, "inivalpcdate": "1900-01-01", "description": "OTC prop 2",
         "conditions": [{"cond_pk": 1515.21, "column": "VALUE_FUNC", "value": "Swaption"},
                        {"cond_pk": 1514.21, "column": "FK_STRATEGY", "value": 4.4}],
         "accounts": {"global": {"FXNEWTOPIC": "9970201-939617", "CASH": "817904-840"},
                      "local": {"FXCONTROL": "TCPA"}, "internal": {"INTTOPIC": "INTERNAL"}},
         "source": "A-04d l.5"}],
    "rows": [{"table": "T_BOX_CROSS_ACCTCONF_S", "row": {"FK_BRANCH": {"ref": "branch"}, "FK_CURRENCY": 840.4,
                                                          "ACC_TYPE": 1, "FK_GLTA": {"ref": "glta:817904-840"}},
              "key_columns": ["FK_BRANCH", "FK_CURRENCY", "ACC_TYPE"], "source": "A-03a l.7"}],
}


def run_dir(values) -> Path:
    d = Path(tempfile.mkdtemp())
    (d / "03-sql").mkdir()
    (d / "03-sql/acc-values.json").write_text(json.dumps(values, indent=1))
    return d


def cli(d, *a):
    return subprocess.run([sys.executable, str(ROOT / "scripts/render_acc_sql.py"), str(d), *a],
                          capture_output=True, text=True, check=False)


def errors(values):
    res = ra.Result()
    ra.validate(values, res)
    return {c for c, *_ in res.errors}, res.errors


def main() -> int:
    # the template is not renderable as it is (open values)
    tpl = json.loads((ROOT / "agents/sigom-box-acc-configs-agent/templates/acc-values.example.json").read_text())
    codes, _ = errors(tpl)
    report("value-open" in codes, "the values template is refused as it is (its <...> values are open)", codes)
    codes, errs = errors(VALUES)
    report(not codes, "a complete values file passes every check", errs)
    nc = copy.deepcopy(VALUES)
    nc["_not_carried"] = [{"what": "GBO 2214.35", "why": "OPEN: account no source has", "source": "<matrix q6>"}]
    codes, errs = errors(nc)
    report(not codes, "the agent's _not_carried list (a comment key, ADR 0023) is ignored by the checks", errs)

    # 1. precheck, then the refusals of the render, then the files
    d = run_dir(VALUES)
    p = cli(d, "--precheck")
    pre = next((d / "03-sql").glob("*-precheck.sql"), None)
    pt = pre.read_text() if pre else ""
    report(p.returncode == 0 and not plsql_lint(pt) and "routine('PKG_ACCTPROP', 'F_GENTOPICCOND', 2, 1, TRUE);" in pt
           and "seq_ahead('T_BOX_ACCT_PORT_PROP_S', 'BOX_ACC', 'SPK_T_BOX_ACCT_PORT_PROP_S');" in pt
           and "has_cols('T_BOX_ACCT_PORT_PROP_S'," in pt and "topic CASH" in pt and "account 817904-840" in pt
           and "condition 1515.21" in pt and "ACC PRECHECK OK" in pt and "INSERT" not in pt.upper().replace("INSTR", "")
           and "FK_LOCALGROUP = c_group" in pt and "T_PGT_BRANCH_GROUP_S" not in pt,
           "precheck: read-only - auth code, the branch in its group (no read of T_PGT_BRANCH_GROUP_S: BOX_ACC cannot, "
           "DGBOUS), routine signatures (ALL_ARGUMENTS), each sequence ahead of its fraction, NOT NULL columns supplied, "
           "codes and conditions present, global range; lint clean",
           (p.stderr, plsql_lint(pt)))
    # every look-up of the block is prechecked - also a row's {ref: glta:} (DGBOUS 2026-10-29: a Cross Account Config
    # row's account missing in BOX passed the precheck and stopped the rehearsal with ORA-20003)
    vr = copy.deepcopy(VALUES)
    vr["rows"][0]["row"]["FK_GLTA"] = {"ref": "glta:9999999-ONLYINROW"}
    vr["rows"][0]["row"]["FK_TOPIC"] = {"ref": "topic:ONLYINROW"}
    res_r = ra.Result()
    m_r = ra.validate(vr, res_r)
    pr = ra.render_precheck(vr, m_r, "x") if m_r else ""
    report("CODE = '9999999-ONLYINROW'" in pr and "account 9999999-ONLYINROW: ' || v_n" in pr
           and "CODE = 'ONLYINROW'" in pr,
           "precheck: the accounts and topics a row looks up (Cross Account Config, Net CCS…) are checked too",
           res_r.errors)
    r0 = cli(d)
    sha = re.search(r"values sha256 (\w+)", pt).group(1) if pt else ""
    (d / "03-sql/NY_SCH-tier2-dev-acc-precheck-output.txt").write_text("values sha256 0000\nACC PRECHECK OK\n")
    r1 = cli(d)
    # what SQL Developer (F5) saves: the DBMS_OUTPUT lines only - the script's -- comments are not echoed
    printed = "\n".join(re.findall(r"DBMS_OUTPUT\.PUT_LINE\('(values sha256 \w+)'\)", pt))
    report(printed == f"values sha256 {sha}", "the precheck PRINTS the values' sha256 (its -- header is not in the saved "
           "output - DGBOUS, 2026-10-29)", printed)
    (d / "03-sql/NY_SCH-tier2-dev-acc-precheck-output.txt").write_text(
        f"Session altered.\n\n{printed}\nok      auth code 44\nACC PRECHECK OK - the config can be rendered.\n")
    r2 = cli(d)
    report(r0.returncode == 1 and "precheck-not-ok" in r0.stderr and r1.returncode == 1 and "precheck-stale" in r1.stderr
           and r2.returncode == 0, "render refuses without the precheck's OK output, and with an output made for other "
           "values", (r0.stderr, r1.stderr, r2.stderr))
    rd = lambda n: (d / "03-sql" / n).read_text() if (d / "03-sql" / n).exists() else ""
    reh, cfg, ver = rd("NY_SCH-tier2-dev-acc-rehearsal.sql"), rd("NY_SCH-tier2-dev-acc-config.sql"), \
        rd("NY_SCH-tier2-dev-acc-verify.sql")
    lint = {n: plsql_lint(t) for n, t in (("rehearsal", reh), ("config", cfg), ("verify", ver))}
    report(not any(lint.values()) and reh.rstrip().endswith("ROLLBACK;") and "COMMIT;" in cfg
           and "COMMIT;" not in reh and "RAISE_APPLICATION_ERROR(-20009" in cfg,
           "rehearsal ends with ROLLBACK (problems reported), config commits only with no problem; lint clean", lint)
    report("SELECT NVL(MAX(TRUNC(PK)), 0) + 1 INTO v_g0 FROM BOX_ACC.T_BOX_ACCT_TOPICS_S WHERE PK - TRUNC(PK) = c_global;"
           in cfg and "v_pk := global_pk('T_BOX_ACCT_TOPICS_S', v_g0);" in cfg
           and "BOX_ACC.PKG_ACCTPRECOMMIT.p_TopicsPreCommit(v_pk);" in cfg
           and "created('T_BOX_ACCT_TOPICS_S', v_pk, 'FXNEWTOPIC', TRUE);" in cfg,
           "global topic: .65 PK (next free, DEV), p_TopicsPreCommit, logged CREATED-GLOBAL")
    report("v_pk := next_pk('T_BOX_ACCT_GLTA_S', 'BOX_ACC.SPK_T_BOX_ACCT_GLTA_S');" in cfg and "'acc O''Brien'" in cfg
           and cfg.index("INSERT INTO BOX_ACC.T_BOX_ACCT_PARENT_DATE_S") < cfg.index("p_AccountPrecommit(v_pk)")
           and "(PK, FK_OWNER_OBJ, FK_EXTENSION, FK_PARENT, INIDATE)\n    VALUES (v_ref, 35000169.65, 35001497.65, v_pk, "
           "TO_DATE('1900-01-01','YYYY-MM-DD'));" in cfg and "VALUES (v_pk, 35000179.65, 'FXNEWTOPIC'" in cfg,
           "account: sequence + fraction, quotes escaped; its date rule an extension of the account (owner 35000169.65, "
           "amDateDep 35001497.65, FK_PARENT = the account) inserted before p_AccountPrecommit; topics' owner built in")
    report("    v_h1 := topic_pk('CASH');\n    INSERT INTO BOX_ACC.T_BOX_LINK_ARRAY_X (PK, FK_OWNER_OBJ, FK_EXTENSION, "
           "FK_PARENT, FK_BS)\n    VALUES (v_pk, 35000194.65, 35003724.65, v_lo, v_h1);" in cfg
           and "VALUES (v_pk, 35000194.65, 35001818.65, v_lo, 1515.21);" in cfg
           and "problem('local property lo-otc: the group already has one" in cfg,
           "local property: its row, then one array row per topic (by CODE) and per condition (its PK); an existing one "
           "is a problem, not a second row")
    i_pp = cfg.index("created('T_BOX_ACCT_PORT_PROP_S', v_pp, 'gbo-2485.35');")
    seq = [cfg.find(x, i_pp) for x in ("BOX_ACC.PKG_ACCTPROP.f_GenTopicCond(v_pp, v_msg);",
                                       "v_h1 := glta_pk('TCPV')", "SET VALUE_FUNC = 'Swaption'",
                                       "SET FK_STRATEGY = 3.4", "FK_GLTA IS NULL",
                                       "BOX_ACC.PKG_ACCTPRECOMMIT.p_StatusPortFolio(v_pp);", "IF NVL(v_status, '?') <> 'Valid'")]
    report(all(x > 0 for x in seq) and seq == sorted(seq) and "v_h2 := topic_pk('FXCONTROL');\n  UPDATE BOX_ACC.T_BOX_ACCT_LIST_TOPIC_S SET FK_GLTA = v_h1"
           in cfg and "FK_EXTENSION = 35001513.65 AND FK_TOPIC = v_h2;" in cfg and "FK_EXTENSION = 35001514.65 AND FK_CONDITION = 1515.21" in cfg and "c_group, 20111.4" in cfg,
           "portfolio property: inserted on the group, f_GenTopicCond, each list row's account, each condition's value, "
           "no row without an account, p_StatusPortFolio, STATUS must be Valid", seq)
    # a function of the block cannot be called inside a SQL statement (PLS-00231, DGBOUS 2026-10-29): every
    # topic_pk / glta_pk call is a PL/SQL assignment to v_h<n>, never inside INSERT / UPDATE / SELECT
    calls = [ln for ln in (reh + cfg).splitlines() if re.search(r"\b(?:topic|glta)_pk\('", ln)]
    report(calls and all(re.fullmatch(r"\s*v_h\d+ := (?:topic|glta)_pk\('(?:[^']|'')*'\);", ln) for ln in calls)
           and "v_h1      NUMBER;" in cfg,
           "no topic / account look-up inside a SQL statement: each one assigned to v_h<n> first (PLS-00231 in DGBOUS)",
           [ln for ln in calls if not re.fullmatch(r"\s*v_h\d+ := (?:topic|glta)_pk\('(?:[^']|'')*'\);", ln)][:3])
    report("v_pk := next_pk('T_BOX_CROSS_ACCTCONF_S'" in cfg and "c_branch" in cfg and "PRESENT|T_BOX_CROSS_ACCTCONF_S" in cfg,
           "other rows: natural key checked first (present -> skipped), then inserted with the table's sequence")

    # 2. refusals
    def ref(mut, want, what):
        vv = copy.deepcopy(VALUES)
        mut(vv)
        c, e = errors(vv)
        report(want in c, f"refused: {what} [{want}]", e)

    ref(lambda v: v.update(env="tier2-pre"), "global-pk-range", "\"next-free\" .65 outside DEV")
    ref(lambda v: v["portfolio_properties"][0]["conditions"].append({"cond_pk": 9.21, "value": "x"}),
        "pp-condition-not-in-local", "a condition the local property does not have")
    ref(lambda v: v["portfolio_properties"][0]["conditions"].pop(), "pp-condition-missing",
        "a condition of the local property with no value")
    ref(lambda v: v["portfolio_properties"][0]["accounts"]["global"].pop("CASH"), "pp-account-missing",
        "a topic of the list with no account")
    ref(lambda v: v["portfolio_properties"][0]["accounts"]["global"].update(OTHER="X"), "pp-topic-not-in-local",
        "an account for a topic the local property does not have")
    ref(lambda v: v["portfolio_properties"][1]["conditions"].__setitem__(1, {"cond_pk": 1514.21, "column": "FK_STRATEGY",
                                                                             "value": 3.4}),
        "pp-clash", "two properties with the same condition values (clash mode a)")
    ref(lambda v: v["portfolio_properties"][0]["conditions"][0].update(value="H123456"), "value-masked",
        "a hashed (masked) value")
    ref(lambda v: v["portfolio_properties"][0]["accounts"]["local"].update(FXCONTROL="<OPEN - which>"), "value-open",
        "an open account")
    ref(lambda v: v["accounts"][0]["row"].update(PK=1), "column-reserved", "a PK given by hand")
    ref(lambda v: v["accounts"][0]["row"].update(VALIDDATE={"date": "2026-01-01"}), "column-computed",
        "a column BOX computes")
    ref(lambda v: v["rows"][0].pop("source"), "source-missing", "a value without its source")
    ref(lambda v: v["rows"].append({"table": "T_PGT_OBJ_SOURCE_S", "row": {}, "source": "x"}), "table-not-supported",
        "a table outside BOX_ACC's generic rows")
    ref(lambda v: v["portfolio_properties"][0]["conditions"][0].update(column="FK_COUNTERPARTY"), "cond-column",
        "a counterparty condition column")
    vb = copy.deepcopy(VALUES)
    vb["portfolio_properties"][1]["conditions"][1]["value"] = 3.4
    vb["portfolio_properties"][1]["expect_invalid"] = True
    cb, eb = errors(vb)
    report(not cb, "clash mode (b): the clashing property marked expect_invalid is rendered, its STATUS not required "
           "Valid", eb)

    # 3. rollback from the config's output
    out = ("CREATED-GLOBAL|T_BOX_ACCT_TOPICS_S|901.65|FXNEWTOPIC\nCREATED|T_BOX_ACCT_GLTA_S|501.44|9970201-939617\n"
           "CREATED|T_BOX_ACCT_PARENT_DATE_S|3.44|9970201-939617\nCREATED|T_BOX_CONF_LO_PROP_S|11.44|lo-otc\n"
           "CREATED|T_BOX_LINK_ARRAY_X|71.44|lo-otc|global|CASH\nCREATED|T_BOX_ACCT_PORT_PROP_S|300.44|gbo-2485.35\n"
           "CREATED|T_BOX_ACCT_PORT_PROP_S|301.44|gbo-2487.35\nSTATUS|gbo-2485.35|300.44|Valid|\n"
           "ACC CONFIG COMMITTED - save this output\n")
    (d / "03-sql/NY_SCH-tier2-dev-acc-config-output.txt").write_text(out)
    rb = cli(d, "--rollback")
    rbt, gbt = rd("NY_SCH-tier2-dev-acc-rollback.sql"), rd("global_pk_rollback.sql")
    order = [rbt.find(x) for x in ("T_BOX_ACCT_LIST_COND_S WHERE FK_PARENT IN (300.44, 301.44)",
                                   "T_BOX_ACCT_LIST_TOPIC_S WHERE FK_PARENT IN (300.44, 301.44)",
                                   "T_BOX_ACCT_PORT_PROP_S WHERE PK IN (300.44, 301.44)", "T_BOX_LINK_ARRAY_X WHERE PK IN (71.44)",
                                   "T_BOX_CONF_LO_PROP_S WHERE PK IN (11.44)", "T_BOX_ACCT_PARENT_DATE_S WHERE PK IN (3.44)",
                                   "T_BOX_ACCT_GLTA_S WHERE PK IN (501.44)", "T_BOX_ACCT_TOPICS_S WHERE PK IN (901.65)")]
    report(rb.returncode == 0 and all(o > 0 for o in order) and order == sorted(order) and not plsql_lint(rbt)
           and "T_BOX_ACCT_TOPICS_S WHERE PK IN (901.65)" in gbt and "GLTA" not in gbt and not plsql_lint(gbt),
           "rollback: exactly the config's CREATED rows, children first (generated lists by parent); "
           "global_pk_rollback.sql only the .65 objects", (rb.stderr, order))
    (d / "03-sql/NY_SCH-tier2-dev-acc-config-output.txt").write_text(out.replace("ACC CONFIG COMMITTED", "x"))
    report(cli(d, "--rollback").returncode == 1, "rollback refused from an output that does not say the config committed")

    print("\nFAILURES\n" + "\n".join(FAILS) if FAILS else "\nall passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
