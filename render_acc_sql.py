#!/usr/bin/env python3
"""
render_acc_sql.py - sigom-box-acc-configs-agent phase 2: a branch's BOX ACC configuration as SQL, rendered from ONE
values file [operator, 2026-10-28 - ADR 0022]. The agent decides the VALUES (each with its source, from the gap run's
evidence and the operator's answers); this script writes the PL/SQL, so its structure cannot drift.

    python3 scripts/render_acc_sql.py <run folder> --precheck     # 1. <base>-precheck.sql (read-only)
    python3 scripts/render_acc_sql.py <run folder>                # 2. rehearsal / config / verify (needs 1's output OK)
    python3 scripts/render_acc_sql.py <run folder> --rollback     # 3. rollback + global_pk_rollback (from 2's output)

Reads <run>/03-sql/acc-values.json (template: agents/sigom-box-acc-configs-agent/templates/acc-values.example.json).
Writes <run>/03-sql/<BRANCH>-<env>-acc-*.sql and render-report.md, nothing else. The operator runs the files in SQL
Developer (F5) with the BOX_ACC account and saves each Script Output beside them:
    <base>-precheck-output.txt   the precheck's output - it must end with ACC PRECHECK OK for the same values
    <base>-config-output.txt     the config's output - its CREATED| lines are what the rollback deletes

How rows are made - the way SIGOM does, in one transaction (nothing in the packages commits):
  PKs        the table's own sequence (BOX_ACC.SPK_<table> unless pk.sequences says otherwise) + the installation's
             fraction (auth code), each checked: fraction, not already used. GLOBAL objects (topics and standard
             historics missing in BOX, ADR 0018) take .65 PKs: the number part from global_pk.<table>.start (a
             range agreed with the BOX team) or, in a DEV environment only, "next-free" (the highest .65 + 1, read
             when the block runs). No sequence or SIGOM function hands out a .65 PK in a Tier 2 installation: they
             append the installation's own code (.44).
  routines   PKG_ACCTPRECOMMIT.p_TopicsPreCommit / p_AccountPrecommit after a topic / an account (+ its date rule);
             PKG_ACCTPROP.f_GenTopicCond after each portfolio property (it builds the lists from the local property),
             then each list row's account (FK_GLTA) and each condition's value, then p_StatusPortFolio and its STATUS
             read back. The precheck checks the routines' signatures (ALL_ARGUMENTS) before anything runs.
  references topics and accounts by CODE, looked up when the block runs (exactly one row, else stop); conditions by
             the PK of the target environment (the condition map); group / branch / instrument PKs from the values.
  guard      every insert checks its natural key first; the config stops (and Oracle undoes it all) at the first
             problem it cannot recover from, and at the end if any problem was counted.
Refusals name the field to fix (codes in the render report). Exit: 0 rendered · 1 refused · 2 bad invocation.
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

VALUES = "03-sql/acc-values.json"
OWN = {"T_BOX_ACCT_PORT_PROP_S": "35000170.65", "T_BOX_CONF_LO_PROP_S": "35000194.65",
       "T_BOX_LINK_ARRAY_X": "35000194.65", "T_BOX_ACCT_GLTA_S": "35000169.65",
       "T_BOX_CROSS_ACCTCONF_S": "35000189.65", "T_BOX_CONF_INSTRUM_TYPE_S": "35000292.65",
       "T_BOX_NETCCS_BSPLAN_S": "35000348.65", "T_BOX_ACCT_TOPICS_S": "35000179.65",
       "T_BOX_ACCT_HISTSTD": "35000180.65"}                         # box-acc-model.md section 2 (A-P2)
PDATE_EXT = "35001497.65"   # amDateDep: the date rule is an EXTENSION of the account object (owner 35000169.65,
                            # FK_PARENT = the account) - box-acc-model.md section 2
LIST_EXT = {"global": "35001510.65", "local": "35001513.65", "internal": "35001518.65"}
COND_EXT = "35001514.65"
ARRAY_EXT = {"global": "35003724.65", "local": "35001814.65", "internal": "35003725.65", "conditions": "35001818.65"}
TOPICS, HISTSTD, GLTA, PDATE = "T_BOX_ACCT_TOPICS_S", "T_BOX_ACCT_HISTSTD", "T_BOX_ACCT_GLTA_S", "T_BOX_ACCT_PARENT_DATE_S"
LOPROP, LINK, PPROP = "T_BOX_CONF_LO_PROP_S", "T_BOX_LINK_ARRAY_X", "T_BOX_ACCT_PORT_PROP_S"
LTOPIC, LCOND = "T_BOX_ACCT_LIST_TOPIC_S", "T_BOX_ACCT_LIST_COND_S"
GENERIC_OK = {"T_BOX_CROSS_ACCTCONF_S", "T_BOX_CONF_INSTRUM_TYPE_S", "T_BOX_NETCCS_BSPLAN_S"}
RESERVED = {"PK", "FK_OWNER_OBJ", "FK_EXTENSION", "FK_PARENT"}
COMPUTED = {"STATUS", "MESSAGE", "VALIDDATE", "LOC_CODE", "HOSTINTERFIND", "PARENT_ACCOUNT", "LSTMNTDATE",
            "LSTMNTUSER", "LSTMNTSOURCE"}                           # set by triggers / pre-commits - never supplied
COND_COLS = {"VALUE_FUNC", "FK_INSTRUMTYPE", "FK_STRATEGY", "FK_DEALTREAT", "FK_COLLATERALIND", "STRUCTIND",
             "FK_STRUCTYPE", "FK_MICROTYPE", "FK_TRDSUBTYPE"}       # FK_PORTFOLIO / FK_COUNTERPARTY: never (masked)
ROUTINES = [  # (package, routine, arguments, of which IN, is a function) - as the config calls them (code read
    # 2026-09-21 / 2026-10-14: f_GenTopicCond(PK, MSG), p_StatusPortFolio(PK)); the precheck verifies each one
    ("PKG_ACCTPROP", "F_GENTOPICCOND", 2, 1, True),
    ("PKG_ACCTPRECOMMIT", "P_STATUSPORTFOLIO", 1, 1, False),
    ("PKG_ACCTPRECOMMIT", "P_ACCOUNTPRECOMMIT", 1, 1, False),
    ("PKG_ACCTPRECOMMIT", "P_TOPICSPRECOMMIT", 1, 1, False),
]
NUM = re.compile(r"-?\d+(\.\d+)?")
IDENT = re.compile(r"[A-Z][A-Z0-9_]{0,29}")
OPEN = re.compile(r"^\s*<")


class Result:
    def __init__(self):
        self.errors, self.warns = [], []

    def err(self, code, where, msg):
        self.errors.append((code, where, msg))

    def warn(self, code, where, msg):
        self.warns.append((code, where, msg))


# --- values ---------------------------------------------------------------------------------------------------------
def lit(v, where: str, res: Result) -> str:
    """A JSON value as an SQL literal: number, 'string', {"date": "YYYY-MM-DD"}, {"num": "20007.4"}, null, refs."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        res.err("value-type", where, "true / false is not a column value")
        return "NULL"
    if isinstance(v, (int, float)):
        if "e" in repr(v).lower() or repr(v) in ("nan", "inf", "-inf"):
            res.err("value-number", where, f"{v!r} - write it as {{\"num\": \"...\"}}")
            return "NULL"
        return repr(v)
    if isinstance(v, str):
        if OPEN.match(v):
            res.err("value-open", where, f"{v[:80]!r} - an open answer: settle it in the values first")
        if re.fullmatch(r"H-?\d+", v):
            res.err("value-masked", where, "a hashed (masked) value cannot be written - charter open question 10")
        return "'" + v.replace("'", "''") + "'"
    if isinstance(v, dict):
        if "date" in v and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(v["date"])):
            return f"TO_DATE('{v['date']}','YYYY-MM-DD')"
        if "num" in v and NUM.fullmatch(str(v["num"])):
            return str(v["num"])
        if "ref" in v:
            r = str(v["ref"])
            if r in ("group", "branch"):
                return f"c_{r}"
            m = re.fullmatch(r"(topic|glta):(.+)", r)
            if m:
                return f"{m.group(1)}_pk('{m.group(2).replace(chr(39), chr(39) * 2)}')"
        res.err("value-type", where, f"{json.dumps(v)[:80]} - expected {{date}}, {{num}} or {{ref: group | branch | "
                "topic:CODE | glta:CODE}}")
        return "NULL"
    res.err("value-type", where, f"{type(v).__name__} is not a column value")
    return "NULL"


def num(v, where: str, res: Result) -> str:
    s = str(v).strip() if v is not None else ""
    if not NUM.fullmatch(s):
        res.err("value-number", where, f"{v!r} - a PK / number expected")
        return "NULL"
    return s


def cols(row: dict, where: str, res: Result, reserved=RESERVED) -> list[tuple[str, str]]:
    out = []
    for c, v in (row or {}).items():
        if str(c).startswith("_"):
            continue
        cu = str(c).upper()
        if not IDENT.fullmatch(cu):
            res.err("column-name", where, f"{c!r}")
        elif cu in reserved:
            res.err("column-reserved", where, f"{cu} is set by the script")
        elif cu in COMPUTED:
            res.err("column-computed", where, f"{cu} is computed by BOX (trigger / pre-commit) - never supplied")
        else:
            out.append((cu, lit(v, f"{where}.{cu}", res)))
    return out


def need_source(e: dict, where: str, res: Result):
    if not str(e.get("source") or "").strip():
        res.err("source-missing", where, "every value names its source (evidence file:line, decision, date)")


def validate(v: dict, res: Result) -> dict:
    """Every check that does not need the database. Returns the normalised model the renderers use."""
    m: dict = {"tables": {}}
    for k in ("branch", "env", "auth_code", "group_pk", "branch_pk"):
        if v.get(k) in (None, "") or (isinstance(v.get(k), str) and OPEN.match(v[k])):
            res.err("value-missing", k, "required")
    auth = str(v.get("auth_code", "")).strip()
    if auth and not re.fullmatch(r"\d+", auth):
        res.err("value-number", "auth_code", f"{auth!r}")
    m["auth"] = auth
    m["fraction"] = f"0.{auth}" if auth.isdigit() else "NULL"
    m["dev"] = "dev" in str(v.get("env", "")).lower()
    m["group"], m["branch"] = num(v.get("group_pk"), "group_pk", res), num(v.get("branch_pk"), "branch_pk", res)
    owners = {**OWN, **{k.upper(): str(x) for k, x in (v.get("owners") or {}).items() if not k.startswith("_")}}
    m["owners"] = owners
    seqs = {k.upper(): str(x) for k, x in (v.get("pk", {}).get("sequences") or {}).items() if not k.startswith("_")}
    m["seq"] = lambda t: seqs.get(t, f"BOX_ACC.SPK_{t}")
    for t, s in seqs.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*", s):
            res.err("pk-sequence", f"pk.sequences.{t}", f"{s!r} - OWNER.SEQUENCE_NAME")

    def used(t, kind="sequence"):
        m["tables"].setdefault(t, set()).add(kind)

    # global objects (.65): topics, standard historics
    gpk = {k.upper(): x for k, x in (v.get("global_pk") or {}).items() if not k.startswith("_")}
    m["globals"] = []
    for sec, table in (("global_topics", TOPICS), ("standard_historics", HISTSTD)):
        items = v.get(sec) or []
        if not items:
            continue
        g = gpk.get(table) or {}
        start = str(g.get("start", "")).strip()
        if start == "next-free" and not m["dev"]:
            res.err("global-pk-range", f"global_pk.{table}", "\"next-free\" only in a DEV environment - elsewhere the "
                    "range the BOX team agreed (ADR 0018)")
        elif start != "next-free" and not re.fullmatch(r"\d+", start):
            res.err("global-pk-range", f"global_pk.{table}", "start: the first number of the agreed .65 range, or "
                    "\"next-free\" (DEV only)")
        if table not in owners:
            res.err("owner-missing", f"owners.{table}", "the table's FK_OWNER_OBJ (A-P2 / A-G2)")
        need_source(g, f"global_pk.{table}", res)
        rows = []
        for i, it in enumerate(items):
            w = f"{sec}[{i}]"
            need_source(it, w, res)
            key = [str(k).upper() for k in (it.get("key_columns") or (["CODE"] if table == TOPICS else []))]
            row = cols(it.get("row"), w + ".row", res)
            if not key or any(k not in dict(row) for k in key):
                res.err("key-missing", w, "key_columns (natural key) must be columns of the row")
            rows.append({"row": row, "key": key, "label": str((it.get("row") or {}).get("CODE", f"#{i}"))})
        m["globals"].append({"table": table, "start": start, "rows": rows, "precommit": table == TOPICS})
        used(table, "global")
    # accounts (+ date rule)
    m["accounts"] = []
    for i, a in enumerate(v.get("accounts") or []):
        w = f"accounts[{i}]"
        need_source(a, w, res)
        row = cols(a.get("row"), w + ".row", res)
        if "CODE" not in dict(row):
            res.err("key-missing", w, "row.CODE")
        dr = None
        if a.get("date_rule"):
            dr = cols(a["date_rule"].get("row"), w + ".date_rule.row", res)
            used(PDATE)
        m["accounts"].append({"code": str((a.get("row") or {}).get("CODE", "")), "row": row, "date_rule": dr})
        used(GLTA)
    # local properties
    m["locals"], lp_by_instr = [], {}
    for i, lp in enumerate(v.get("local_properties") or []):
        w = f"local_properties[{i}]"
        need_source(lp, w, res)
        ins = num(lp.get("instrument_pk"), w + ".instrument_pk", res)
        d = lp.get("inivalpcdate") or "1900-01-01"
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d)):
            res.err("value-date", w + ".inivalpcdate", f"{d!r}")
        arrays = {}
        for arr in ("global", "local", "internal"):
            arrays[arr] = [str(c) for c in lp.get(f"{arr}_topics") or []]
        arrays["conditions"] = [num(c, w + ".conditions", res) for c in lp.get("conditions") or []]
        for arr, xs in arrays.items():
            if len(set(xs)) != len(xs):
                res.err("array-duplicate", f"{w}.{arr}", "an entry twice")
        if ins in lp_by_instr:
            res.err("local-twice", w, f"instrument {ins} has two local properties in the values")
        rec = {"key": lp.get("key") or f"lo-{ins}", "instrument": ins, "date": str(d), "arrays": arrays,
               "row": cols(lp.get("row"), w + ".row", res, RESERVED | {"FK_BRANCH", "FK_INSTRUMENT", "INIVALPCDATE"})}
        lp_by_instr[ins] = rec
        m["locals"].append(rec)
        used(LOPROP)
        used(LINK)
    existing_lp = {num(x, "existing_local_properties", res): {
        "global": [str(c) for c in (e.get("global_topics") or [])], "local": [str(c) for c in (e.get("local_topics") or [])],
        "internal": [str(c) for c in (e.get("internal_topics") or [])],
        "conditions": [num(c, "existing_local_properties", res) for c in (e.get("conditions") or [])]}
        for x, e in (v.get("existing_local_properties") or {}).items() if not str(x).startswith("_")}
    # portfolio properties
    m["pps"], seen_keys, sig = [], set(), {}
    for i, pp in enumerate(v.get("portfolio_properties") or []):
        w = f"portfolio_properties[{i}]"
        need_source(pp, w, res)
        key = str(pp.get("key") or "")
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", key) or key in seen_keys:
            res.err("pp-key", w, "a unique key per property (e.g. gbo-<GBO PK>)")
        seen_keys.add(key)
        ins = num(pp.get("instrument_pk"), w + ".instrument_pk", res)
        d = pp.get("inivalpcdate")
        if not d or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d)):
            res.err("value-date", w + ".inivalpcdate", f"{d!r} - the decided start date (YYYY-MM-DD)")
        lp = lp_by_instr.get(ins) or existing_lp.get(ins)
        if not lp:
            res.err("pp-no-local", w, f"instrument {ins}: no local property in the values (local_properties) nor "
                    "declared existing (existing_local_properties)")
            lp = {"arrays": {"global": [], "local": [], "internal": [], "conditions": []}}
        arrays = lp.get("arrays", lp)
        conds = []
        for j, c in enumerate(pp.get("conditions") or []):
            cw = f"{w}.conditions[{j}]"
            cpk = num(c.get("cond_pk"), cw + ".cond_pk", res)
            col = str(c.get("column", "VALUE_FUNC")).upper()
            if col not in COND_COLS:
                res.err("cond-column", cw, f"{col} - one of {', '.join(sorted(COND_COLS))}")
            if cpk not in arrays["conditions"]:
                res.err("pp-condition-not-in-local", cw, f"condition {cpk} is not in the local property's conditions - "
                        "f_GenTopicCond would not create it (ADR 0020)")
            conds.append((cpk, col, lit(c.get("value"), cw + ".value", res)))
        missing_c = sorted(set(arrays["conditions"]) - {c[0] for c in conds})
        if missing_c:
            res.err("pp-condition-missing", w, f"no value for condition(s) {', '.join(missing_c)} of the local property "
                    "- BOX would mark it InValid")
        acc = {}
        for lst in ("global", "local", "internal"):
            given = {str(t): str(a) for t, a in ((pp.get("accounts") or {}).get(lst) or {}).items()}
            for t, a in given.items():
                if OPEN.match(a):
                    res.err("value-open", f"{w}.accounts.{lst}.{t}", "an open account - settle it first (the "
                            "property would be InValid)")
            extra = sorted(set(given) - set(arrays[lst]))
            if extra:
                res.err("pp-topic-not-in-local", f"{w}.accounts.{lst}", f"{', '.join(extra)} not in the local "
                        "property's list - f_GenTopicCond would not create the row")
            miss = sorted(set(arrays[lst]) - set(given))
            if miss:
                res.err("pp-account-missing", f"{w}.accounts.{lst}", f"no account for {', '.join(miss[:8])}"
                        f"{' …' if len(miss) > 8 else ''} ({len(miss)}) - every topic of the list needs one")
            acc[lst] = given
        expect_invalid = bool(pp.get("expect_invalid"))
        s = (ins, str(d), tuple(sorted((c[0], c[1], c[2]) for c in conds)))
        if s in sig and not expect_invalid and not sig[s][1]:
            res.err("pp-clash", w, f"same instrument, start date and condition values as {sig[s][0]} - BOX keeps one "
                    "Valid: the operator's choice (decisions.pp_clash_choices), or expect_invalid (clash mode b)")
        sig.setdefault(s, (key, expect_invalid))
        m["pps"].append({"key": key, "instrument": ins, "date": str(d), "description": pp.get("description") or "",
                         "conds": conds, "accounts": acc, "expect_invalid": expect_invalid})
        used(PPROP)
    # generic rows (cross account config, conf instrument type, net CCS plan)
    m["rows"] = []
    for i, r in enumerate(v.get("rows") or []):
        w = f"rows[{i}]"
        need_source(r, w, res)
        t = str(r.get("table", "")).upper().removeprefix("BOX_ACC.")
        if t not in GENERIC_OK:
            res.err("table-not-supported", w, f"{t or '?'} - generic rows: {', '.join(sorted(GENERIC_OK))}")
            continue
        row = cols(r.get("row"), w + ".row", res)
        key = [str(k).upper() for k in r.get("key_columns") or []]
        if not key or any(k not in dict(row) for k in key):
            res.err("key-missing", w, "key_columns (natural key) must be columns of the row")
        m["rows"].append({"table": t, "row": row, "key": key, "label": f"{t}#{i}"})
        used(t)
    # two rows of one table with the same natural key: the second would be skipped as PRESENT (the first was just
    # created) - NY's two Conf Instru Type rows, DGBOUS rehearsal 2026-10-29. The key must tell every row apart.
    seen: dict = {}
    for r in m["rows"]:
        d = dict(r["row"])
        k = (r["table"], tuple((c, d.get(c)) for c in r["key"]))
        if k in seen:
            res.err("key-duplicate", r["label"], f"same key_columns values ({', '.join(r['key'])}) as {seen[k]} - "
                    "add the column that tells them apart (charter natural keys), or drop the duplicate row")
        seen.setdefault(k, r["label"])
    for t in m["tables"]:
        if t not in owners and t != PDATE:
            res.err("owner-missing", f"owners.{t}", "the table's FK_OWNER_OBJ")
    if not (m["globals"] or m["accounts"] or m["locals"] or m["pps"] or m["rows"]):
        res.err("nothing-to-render", "values", "no section has rows")
    return m


# --- rendering ------------------------------------------------------------------------------------------------------
def esc(s: str) -> str:
    return str(s).replace("'", "''")


def header(v: dict, sha: str, what: str, run_order: bool = True) -> list[str]:
    return ["SET DEFINE OFF",
            "-- ============================================================================",
            f"-- {v['branch']} - BOX ACC configuration - {v['env']} - {what}",
            "-- Rendered by scripts/render_acc_sql.py (sigom-box-acc-configs-agent phase 2, ADR 0022). Never edit:",
            "-- change 03-sql/acc-values.json and render again.",
            f"-- values sha256 {sha}",
            *(["-- Run order (BOX_ACC account, SQL Developer F5): 1 precheck (read-only) -> save its output as",
               "-- <base>-precheck-output.txt; 2 rehearsal (ROLLBACK); 3 config (COMMIT) -> save its output as",
               "-- <base>-config-output.txt; 4 verify (read-only); rollback files rendered from 3's output, ONLY to undo",
               "-- it. Any error stops a block and Oracle undoes everything it did."] if run_order else []),
            "-- ============================================================================"]


def ins_values(table, owner_sql, pkexpr, row, extra=()) -> str:
    names = ["PK", "FK_OWNER_OBJ", *[c for c, _ in extra], *[c for c, _ in row]]
    vals = [pkexpr, owner_sql, *[x for _, x in extra], *[x for _, x in row]]
    return (f"    INSERT INTO BOX_ACC.{table} ({', '.join(names)})\n"
            f"    VALUES ({', '.join(vals)});")


CALL = re.compile(r"\b(?:topic|glta)_pk\('(?:[^']|'')*'\)")
N_HOIST = 20      # v_h1..v_h20 declared in the block


def hoist(sql: str) -> str:
    """A function declared in the block cannot be called inside a SQL statement (PLS-00231 - DGBOUS, 2026-10-29):
    each topic_pk / glta_pk call of the statement is assigned to v_h<n> just before it, and the statement uses v_h<n>."""
    calls: list[str] = []

    def sub(mo):
        calls.append(mo.group(0))
        return f"v_h{len(calls)}"
    out = CALL.sub(sub, sql)
    if len(calls) > N_HOIST:
        raise ValueError(f"{len(calls)} topic / account look-ups in one statement (max {N_HOIST})")
    indent = re.match(r"\s*", sql).group(0)
    return "\n".join([f"{indent}v_h{i} := {c};" for i, c in enumerate(calls, 1)] + [out])


def key_where(row, key) -> str:
    d = dict(row)
    return " AND ".join(f"{k} = {d[k]}" if d[k] != "NULL" else f"{k} IS NULL" for k in key)


def render_block(v: dict, m: dict, sha: str, mode: str) -> str:
    """mode: 'rehearsal' (ends ROLLBACK, problems reported) or 'config' (COMMIT only with no problem)."""
    L = header(v, sha, "REHEARSAL (ends with ROLLBACK)" if mode == "rehearsal" else "CONFIG (COMMIT)")
    globals_ = m["globals"]
    L += ["SET AUTOCOMMIT OFF", "SET SERVEROUTPUT ON SIZE UNLIMITED",
          "WHENEVER SQLERROR EXIT FAILURE ROLLBACK",
          "ALTER SESSION SET NLS_NUMERIC_CHARACTERS = '.,';",
          "DECLARE",
          f"  c_expected_auth_code CONSTANT NUMBER := {m['auth']};   -- auth_code",
          f"  c_group    CONSTANT NUMBER := {m['group']};   -- group_pk (FK_BRANCH of local and portfolio properties)",
          f"  c_branch   CONSTANT NUMBER := {m['branch']};   -- branch_pk",
          "  c_global   CONSTANT NUMBER := 0.65;   -- global objects (ADR 0018)",
          "  v_fraction NUMBER;",
          "  v_auth     NUMBER;",
          "  v_problems PLS_INTEGER := 0;",
          "  v_pk       NUMBER;",
          "  v_ref      NUMBER;",
          "  v_lo       NUMBER;",
          "  v_pp       NUMBER;",
          "  v_n        PLS_INTEGER;",
          "  v_msg      VARCHAR2(4000);",
          "  v_ret      VARCHAR2(4000);",
          "  v_status   VARCHAR2(100);",
          "  v_message  VARCHAR2(4000);",
          *[f"  v_h{i}      NUMBER;   -- a topic / account PK looked up before a SQL statement" for i in range(1, N_HOIST + 1)],
          *[f"  v_g{i}      NUMBER;   -- next .65 number, {g['table']}" for i, g in enumerate(globals_)],
          "  PROCEDURE problem (p_what VARCHAR2) IS",
          "  BEGIN",
          "    v_problems := v_problems + 1;",
          "    DBMS_OUTPUT.PUT_LINE('PROBLEM|' || p_what);",
          "  END problem;",
          "  PROCEDURE created (p_table VARCHAR2, p_pk NUMBER, p_key VARCHAR2, p_global BOOLEAN DEFAULT FALSE) IS",
          "  BEGIN",
          "    DBMS_OUTPUT.PUT_LINE(CASE WHEN p_global THEN 'CREATED-GLOBAL|' ELSE 'CREATED|' END || p_table || '|'",
          "      || TO_CHAR(p_pk) || '|' || p_key);",
          "  END created;",
          "  FUNCTION pk_taken (p_table VARCHAR2, p_pk NUMBER) RETURN BOOLEAN IS",
          "    v_c PLS_INTEGER;",
          "  BEGIN",
          "    EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM BOX_ACC.' || p_table || ' WHERE PK = :p' INTO v_c USING p_pk;",
          "    RETURN v_c > 0;",
          "  END pk_taken;",
          "  FUNCTION next_pk (p_table VARCHAR2, p_seq VARCHAR2) RETURN NUMBER IS",
          "    v_s NUMBER;",
          "  BEGIN",
          "    EXECUTE IMMEDIATE 'SELECT ' || p_seq || '.NEXTVAL FROM DUAL' INTO v_s;",
          "    v_s := v_s + v_fraction;",
          "    IF pk_taken(p_table, v_s) THEN",
          "      RAISE_APPLICATION_ERROR(-20001, p_table || ': PK ' || v_s || ' already used - the sequence ' || p_seq",
          "        || ' is behind the table: run the precheck again, give its proposal to the BOX team. Nothing kept.');",
          "    END IF;",
          "    RETURN v_s;",
          "  END next_pk;",
          "  FUNCTION global_pk (p_table VARCHAR2, p_next IN OUT NUMBER) RETURN NUMBER IS",
          "    v_s NUMBER;",
          "  BEGIN",
          "    v_s := p_next + c_global;",
          "    p_next := p_next + 1;",
          "    IF pk_taken(p_table, v_s) THEN",
          "      RAISE_APPLICATION_ERROR(-20004, p_table || ': global PK ' || v_s || ' already used - the agreed .65 '",
          "        || 'range is not free (precheck). Nothing kept.');",
          "    END IF;",
          "    RETURN v_s;",
          "  END global_pk;",
          "  FUNCTION topic_pk (p_code VARCHAR2) RETURN NUMBER IS",
          "    v_c PLS_INTEGER;",
          "    v_p NUMBER;",
          "  BEGIN",
          f"    SELECT COUNT(*), MIN(PK) INTO v_c, v_p FROM BOX_ACC.{TOPICS} WHERE CODE = p_code AND FK_OWNER_OBJ > 0;",
          "    IF v_c <> 1 THEN",
          "      RAISE_APPLICATION_ERROR(-20002, 'Topic ' || p_code || ': ' || v_c || ' row(s) in BOX, expected 1. '",
          "        || 'Nothing kept.');",
          "    END IF;",
          "    RETURN v_p;",
          "  END topic_pk;",
          "  FUNCTION glta_pk (p_code VARCHAR2) RETURN NUMBER IS",
          "    v_c PLS_INTEGER;",
          "    v_p NUMBER;",
          "  BEGIN",
          f"    SELECT COUNT(*), MIN(PK) INTO v_c, v_p FROM BOX_ACC.{GLTA} WHERE CODE = p_code AND FK_OWNER_OBJ > 0;",
          "    IF v_c <> 1 THEN",
          "      RAISE_APPLICATION_ERROR(-20003, 'Account ' || p_code || ': ' || v_c || ' row(s) in BOX, expected 1 '",
          "        || '(charter open question 6). Nothing kept.');",
          "    END IF;",
          "    RETURN v_p;",
          "  END glta_pk;",
          "BEGIN",
          "  IF DBMS_TRANSACTION.LOCAL_TRANSACTION_ID IS NOT NULL THEN",
          "    RAISE_APPLICATION_ERROR(-20097, 'This session has an open transaction. Type ROLLBACK; and run this file '",
          "      || 'again. Nothing has been done.');",
          "  END IF;",
          "  SELECT AUTH_CODE INTO v_auth FROM GOM_GLB_SYS.T__CORE_INFO_S;",
          "  IF v_auth <> c_expected_auth_code THEN",
          "    RAISE_APPLICATION_ERROR(-20005, 'Built for auth code ' || c_expected_auth_code || ', this installation is '",
          "      || v_auth || '. Wrong environment? Nothing has been done.');",
          "  END IF;",
          "  v_fraction := v_auth / POWER(10, LENGTH(TO_CHAR(v_auth)));"]
    # 1. global objects
    for i, g in enumerate(globals_):
        t = g["table"]
        L.append(f"  -- 1. global objects, {t}: .65 PKs ({'next free' if g['start'] == 'next-free' else 'from ' + g['start']})")
        if g["start"] == "next-free":
            L.append(f"  SELECT NVL(MAX(TRUNC(PK)), 0) + 1 INTO v_g{i} FROM BOX_ACC.{t} WHERE PK - TRUNC(PK) = c_global;")
        else:
            L.append(f"  v_g{i} := {g['start']};")
        for r in g["rows"]:
            L += [hoist(f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{t} WHERE {key_where(r['row'], r['key'])};"),
                  "  IF v_n > 0 THEN",
                  f"    DBMS_OUTPUT.PUT_LINE('PRESENT|{t}|{esc(r['label'])}');",
                  "  ELSE",
                  f"    v_pk := global_pk('{t}', v_g{i});",
                  hoist(ins_values(t, m["owners"][t], "v_pk", r["row"])),
                  *(["    BOX_ACC.PKG_ACCTPRECOMMIT.p_TopicsPreCommit(v_pk);"] if g["precommit"] else []),
                  f"    created('{t}', v_pk, '{esc(r['label'])}', TRUE);",
                  "  END IF;"]
    # 2. accounts
    if m["accounts"]:
        L.append(f"  -- 2. global accounts ({len(m['accounts'])}), each with its date rule if any, then p_AccountPrecommit")
    for a in m["accounts"]:
        code = esc(a["code"])
        L += [f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{GLTA} WHERE CODE = '{code}' AND FK_OWNER_OBJ > 0;",
              "  IF v_n > 0 THEN",
              f"    DBMS_OUTPUT.PUT_LINE('PRESENT|{GLTA}|{code}');",
              "  ELSE",
              f"    v_pk := next_pk('{GLTA}', '{m['seq'](GLTA)}');",
              hoist(ins_values(GLTA, m["owners"][GLTA], "v_pk", a["row"])),
              f"    created('{GLTA}', v_pk, '{code}');"]
        if a["date_rule"] is not None:      # an extension of the account object: its owner, amDateDep, the account
            L += [f"    v_ref := next_pk('{PDATE}', '{m['seq'](PDATE)}');",
                  hoist(ins_values(PDATE, m["owners"][GLTA], "v_ref", a["date_rule"],
                                   extra=[("FK_EXTENSION", PDATE_EXT), ("FK_PARENT", "v_pk")])),
                  f"    created('{PDATE}', v_ref, '{code}');"]
        L += ["    BOX_ACC.PKG_ACCTPRECOMMIT.p_AccountPrecommit(v_pk);", "  END IF;"]
    # 3. local properties and their arrays
    for lp in m["locals"]:
        k = esc(lp["key"])
        L += [f"  -- 3. local property {k}: instrument {lp['instrument']}, start {lp['date']}",
              (f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{LOPROP} WHERE FK_BRANCH = c_group AND FK_INSTRUMENT = "
              f"{lp['instrument']}"),
              f"    AND INIVALPCDATE = TO_DATE('{lp['date']}','YYYY-MM-DD') AND FK_OWNER_OBJ > 0;",
              "  IF v_n > 0 THEN",
              f"    problem('local property {k}: the group already has one for this instrument and date - not created');",
              "  ELSE",
              f"    v_lo := next_pk('{LOPROP}', '{m['seq'](LOPROP)}');",
              hoist(ins_values(LOPROP, m["owners"][LOPROP], "v_lo", lp["row"],
                               extra=[("FK_BRANCH", "c_group"), ("FK_INSTRUMENT", lp["instrument"]),
                                      ("INIVALPCDATE", f"TO_DATE('{lp['date']}','YYYY-MM-DD')")])),
              f"    created('{LOPROP}', v_lo, '{k}');"]
        for arr in ("global", "local", "internal", "conditions"):
            for x in lp["arrays"][arr]:
                bs = x if arr == "conditions" else f"topic_pk('{esc(x)}')"
                L += [f"    v_pk := next_pk('{LINK}', '{m['seq'](LINK)}');",
                      hoist(f"    INSERT INTO BOX_ACC.{LINK} (PK, FK_OWNER_OBJ, FK_EXTENSION, FK_PARENT, FK_BS)\n"
                            f"    VALUES (v_pk, {m['owners'][LOPROP]}, {ARRAY_EXT[arr]}, v_lo, {bs});"),
                      f"    created('{LINK}', v_pk, '{k}|{arr}|{esc(x)}');"]
        L.append("  END IF;")
    # 4. portfolio properties
    for pp in m["pps"]:
        k = esc(pp["key"])
        L += [(f"  -- 4. portfolio property {k}: instrument {pp['instrument']}, start {pp['date']}"
              f"{' - EXPECTED InValid (clash mode b)' if pp['expect_invalid'] else ''}"),
              f"  v_pp := next_pk('{PPROP}', '{m['seq'](PPROP)}');",
              f"  INSERT INTO BOX_ACC.{PPROP} (PK, FK_OWNER_OBJ, FK_BRANCH, FK_INSTRUMENT, INIVALPCDATE, DESCRIPTION)",
              f"  VALUES (v_pp, {m['owners'][PPROP]}, c_group, {pp['instrument']}, TO_DATE('{pp['date']}','YYYY-MM-DD'),",
              f"    '{esc(pp['description'])}');",
              f"  created('{PPROP}', v_pp, '{k}');",
              "  v_ret := BOX_ACC.PKG_ACCTPROP.f_GenTopicCond(v_pp, v_msg);"]
        for lst in ("global", "local", "internal"):
            for t, a in sorted(pp["accounts"][lst].items()):
                L += [hoist(f"  UPDATE BOX_ACC.{LTOPIC} SET FK_GLTA = glta_pk('{esc(a)}')\n"
                            f"  WHERE  FK_PARENT = v_pp AND FK_OWNER_OBJ = {m['owners'][PPROP]} AND FK_EXTENSION = "
                            f"{LIST_EXT[lst]} AND FK_TOPIC = topic_pk('{esc(t)}');"),
                      "  IF SQL%ROWCOUNT <> 1 THEN",
                      f"    problem('{k}: {lst} topic {esc(t)} - ' || SQL%ROWCOUNT || ' list row(s) generated, expected 1');",
                      "  END IF;"]
        for cpk, col, val in pp["conds"]:
            L += [f"  UPDATE BOX_ACC.{LCOND} SET {col} = {val}",
                  (f"  WHERE  FK_PARENT = v_pp AND FK_OWNER_OBJ = {m['owners'][PPROP]} AND FK_EXTENSION = {COND_EXT} "
                  f"AND FK_CONDITION = {cpk};"),
                  "  IF SQL%ROWCOUNT <> 1 THEN",
                  f"    problem('{k}: condition {cpk} - ' || SQL%ROWCOUNT || ' list row(s) generated, expected 1');",
                  "  END IF;"]
        L += [(f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{LTOPIC} WHERE FK_PARENT = v_pp AND FK_OWNER_OBJ = "
              f"{m['owners'][PPROP]} AND FK_GLTA IS NULL;"),
              "  IF v_n > 0 THEN",
              f"    problem('{k}: ' || v_n || ' list row(s) without an account');",
              "  END IF;",
              "  BOX_ACC.PKG_ACCTPRECOMMIT.p_StatusPortFolio(v_pp);",
              f"  SELECT STATUS, MESSAGE INTO v_status, v_message FROM BOX_ACC.{PPROP} WHERE PK = v_pp;",
              f"  DBMS_OUTPUT.PUT_LINE('STATUS|{k}|' || TO_CHAR(v_pp) || '|' || v_status || '|' || v_message);"]
        if not pp["expect_invalid"]:
            L += ["  IF NVL(v_status, '?') <> 'Valid' THEN",
                  f"    problem('{k}: STATUS ' || v_status || ' - ' || v_message);",
                  "  END IF;"]
    # 5. other branch rows
    for r in m["rows"]:
        t = r["table"]
        L += [f"  -- 5. {t}",
              hoist(f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{t} WHERE {key_where(r['row'], r['key'])} "
                    "AND FK_OWNER_OBJ > 0;"),
              "  IF v_n > 0 THEN",
              f"    DBMS_OUTPUT.PUT_LINE('PRESENT|{t}|{esc(r['label'])}');",
              "  ELSE",
              f"    v_pk := next_pk('{t}', '{m['seq'](t)}');",
              hoist(ins_values(t, m["owners"][t], "v_pk", r["row"])),
              f"    created('{t}', v_pk, '{esc(r['label'])}');",
              "  END IF;"]
    L += ["  DBMS_OUTPUT.PUT_LINE('SUMMARY|problems|' || v_problems);"]
    if mode == "config":
        L += ["  IF v_problems > 0 THEN",
              "    RAISE_APPLICATION_ERROR(-20009, v_problems || ' problem(s) above (PROBLEM| lines). Nothing has been kept.');",
              "  END IF;",
              "  COMMIT;",
              "  DBMS_OUTPUT.PUT_LINE('ACC CONFIG COMMITTED - save this output as <base>-config-output.txt');"]
    else:
        L += ["  DBMS_OUTPUT.PUT_LINE('REHEARSAL DONE - rolled back below. 0 problems = the config can run.');"]
    L += ["END;", "/"]
    if mode == "rehearsal":
        L.append("ROLLBACK;")
    return "\n".join(L) + "\n"


def render_precheck(v: dict, m: dict, sha: str) -> str:
    L = header(v, sha, "PRECHECK (read-only)")
    tables = sorted(m["tables"])
    supplied = {}
    for g in m["globals"]:
        supplied.setdefault(g["table"], set()).update({"PK", "FK_OWNER_OBJ"} | {c for r in g["rows"] for c, _ in r["row"]})
    for a in m["accounts"]:
        supplied.setdefault(GLTA, set()).update({"PK", "FK_OWNER_OBJ"} | {c for c, _ in a["row"]})
        if a["date_rule"] is not None:
            supplied.setdefault(PDATE, set()).update({"PK", "FK_OWNER_OBJ", "FK_EXTENSION", "FK_PARENT"}
                                                     | {c for c, _ in a["date_rule"]})
    for lp in m["locals"]:
        supplied.setdefault(LOPROP, set()).update({"PK", "FK_OWNER_OBJ", "FK_BRANCH", "FK_INSTRUMENT", "INIVALPCDATE"}
                                                  | {c for c, _ in lp["row"]})
        supplied.setdefault(LINK, set()).update({"PK", "FK_OWNER_OBJ", "FK_EXTENSION", "FK_PARENT", "FK_BS"})
    if m["pps"]:
        supplied.setdefault(PPROP, set()).update({"PK", "FK_OWNER_OBJ", "FK_BRANCH", "FK_INSTRUMENT", "INIVALPCDATE",
                                                  "DESCRIPTION"})
    for r in m["rows"]:
        supplied.setdefault(r["table"], set()).update({"PK", "FK_OWNER_OBJ"} | {c for c, _ in r["row"]})
    L += ["SET SERVEROUTPUT ON SIZE UNLIMITED",
          "ALTER SESSION SET NLS_NUMERIC_CHARACTERS = '.,';",
          "DECLARE",
          f"  c_expected_auth_code CONSTANT NUMBER := {m['auth']};",
          f"  c_group    CONSTANT NUMBER := {m['group']};",
          f"  c_branch   CONSTANT NUMBER := {m['branch']};",
          "  v_auth     NUMBER;",
          "  v_fraction NUMBER;",
          "  v_bad      PLS_INTEGER := 0;",
          "  v_n        PLS_INTEGER;",
          "  v_max      NUMBER;",
          "  v_last     NUMBER;",
          "  v_cache    NUMBER;",
          "  v_incr     NUMBER;",
          "  PROCEDURE bad (p_what VARCHAR2) IS",
          "  BEGIN",
          "    v_bad := v_bad + 1;",
          "    DBMS_OUTPUT.PUT_LINE('PROBLEM ' || p_what);",
          "  END bad;",
          "  PROCEDURE ok (p_what VARCHAR2) IS",
          "  BEGIN",
          "    DBMS_OUTPUT.PUT_LINE('ok      ' || p_what);",
          "  END ok;",
          "  PROCEDURE seq_ahead (p_table VARCHAR2, p_owner VARCHAR2, p_seq VARCHAR2) IS",
          "  BEGIN",
          "    SELECT MAX(LAST_NUMBER), MAX(CACHE_SIZE), MAX(INCREMENT_BY), COUNT(*) INTO v_last, v_cache, v_incr, v_n",
          "    FROM   ALL_SEQUENCES WHERE SEQUENCE_OWNER = p_owner AND SEQUENCE_NAME = p_seq;",
          "    IF v_n = 0 THEN",
          "      bad(p_table || ': sequence ' || p_owner || '.' || p_seq || ' not found (or not granted) - the BOX dev '",
          "        || 'says which sequence SIGOM uses (pk.sequences in the values)');",
          "      RETURN;",
          "    END IF;",
          "    EXECUTE IMMEDIATE 'SELECT MAX(TRUNC(PK)) FROM BOX_ACC.' || p_table || ' WHERE PK - TRUNC(PK) = :f'",
          "      INTO v_max USING v_fraction;",
          "    IF v_max IS NOT NULL AND v_last - NVL(v_cache, 0) * v_incr <= v_max THEN",
          "      bad(p_table || ': sequence at ' || v_last || ' (cache ' || NVL(v_cache, 0) || '), highest PK of fraction '",
          "        || v_fraction || ' is ' || v_max || '. PROPOSAL for the BOX team: move ' || p_owner || '.' || p_seq",
          "        || ' above ' || (v_max + 1000) || '.');",
          "    ELSE",
          "      ok(p_table || ': sequence ' || p_seq || ' at ' || v_last || ', highest PK of the fraction '",
          "        || NVL(TO_CHAR(v_max), 'none'));",
          "    END IF;",
          "  END seq_ahead;",
          "  PROCEDURE has_cols (p_table VARCHAR2, p_cols VARCHAR2) IS",
          "    v_def VARCHAR2(32000);",
          "  BEGIN",
          "    FOR c IN (SELECT COLUMN_NAME, NULLABLE, DATA_DEFAULT FROM ALL_TAB_COLUMNS",
          "              WHERE OWNER = 'BOX_ACC' AND TABLE_NAME = p_table) LOOP",
          "      v_def := c.DATA_DEFAULT;",
          "      IF c.NULLABLE = 'N' AND v_def IS NULL AND INSTR(',' || p_cols || ',', ',' || c.COLUMN_NAME || ',') = 0 THEN",
          "        bad(p_table || '.' || c.COLUMN_NAME || ' is NOT NULL with no default and the values do not give it');",
          "      END IF;",
          "    END LOOP;",
          "  END has_cols;",
          "  PROCEDURE col_exists (p_table VARCHAR2, p_col VARCHAR2) IS",
          "  BEGIN",
          "    SELECT COUNT(*) INTO v_n FROM ALL_TAB_COLUMNS WHERE OWNER = 'BOX_ACC' AND TABLE_NAME = p_table",
          "    AND COLUMN_NAME = p_col;",
          "    IF v_n = 0 THEN",
          "      bad(p_table || '.' || p_col || ': no such column (A-P8)');",
          "    END IF;",
          "  END col_exists;",
          "  PROCEDURE routine (p_pkg VARCHAR2, p_name VARCHAR2, p_args PLS_INTEGER, p_in PLS_INTEGER, p_function BOOLEAN) IS",
          "    v_args PLS_INTEGER;",
          "    v_in   PLS_INTEGER;",
          "    v_ret  PLS_INTEGER;",
          "    v_rett VARCHAR2(30);",
          "  BEGIN",
          "    SELECT COUNT(DISTINCT OVERLOAD || '#'), SUM(CASE WHEN POSITION > 0 AND ARGUMENT_NAME IS NOT NULL THEN 1 ELSE 0 END),",
          "           SUM(CASE WHEN POSITION > 0 AND IN_OUT = 'IN' THEN 1 ELSE 0 END),",
          "           SUM(CASE WHEN POSITION = 0 THEN 1 ELSE 0 END), MAX(CASE WHEN POSITION = 0 THEN DATA_TYPE END)",
          "    INTO   v_n, v_args, v_in, v_ret, v_rett",
          "    FROM   ALL_ARGUMENTS WHERE OWNER = 'BOX_ACC' AND PACKAGE_NAME = p_pkg AND OBJECT_NAME = p_name;",
          "    IF v_n = 0 THEN",
          "      bad('BOX_ACC.' || p_pkg || '.' || p_name || ': not found (or not granted)');",
          "    ELSIF v_n > 1 OR NVL(v_args, 0) <> p_args OR NVL(v_in, 0) <> p_in",
          "          OR (p_function AND (v_ret = 0 OR v_rett NOT IN ('NUMBER', 'VARCHAR2')))",
          "          OR (NOT p_function AND v_ret > 0) THEN",
          "      bad('BOX_ACC.' || p_pkg || '.' || p_name || ': signature not the one the config calls (' || p_args",
          "        || ' argument(s), ' || p_in || ' IN' || CASE WHEN p_function THEN ', returns NUMBER / VARCHAR2' END",
          "        || ') - list ALL_ARGUMENTS for it and tell the agent');",
          "    ELSE",
          "      ok('BOX_ACC.' || p_pkg || '.' || p_name || ' signature');",
          "    END IF;",
          "  END routine;",
          "BEGIN",
          # the script's -- comments are not echoed by SQL Developer (F5): the values' sha256 must be PRINTED for the
          # saved output to prove it was made for these values (render refuses otherwise - DGBOUS, 2026-10-29)
          f"  DBMS_OUTPUT.PUT_LINE('values sha256 {sha}');",
          "  SELECT AUTH_CODE INTO v_auth FROM GOM_GLB_SYS.T__CORE_INFO_S;",
          "  IF v_auth <> c_expected_auth_code THEN",
          "    bad('auth code ' || v_auth || ', the values say ' || c_expected_auth_code || ' - wrong environment?');",
          "  ELSE",
          "    ok('auth code ' || v_auth);",
          "  END IF;",
          "  v_fraction := v_auth / POWER(10, LENGTH(TO_CHAR(v_auth)));",
          # the group is proved by its branch (FK_LOCALGROUP): BOX_ACC cannot read PGT_STC.T_PGT_BRANCH_GROUP_S
          # in Tier 2 DEV (ORA-00942, DGBOUS 2026-10-29) - only T_PGT_BRANCH_S
          "  SELECT COUNT(*) INTO v_n FROM PGT_STC.T_PGT_BRANCH_S WHERE PK = c_branch AND FK_LOCALGROUP = c_group;",
          "  IF v_n = 1 THEN ok('branch ' || c_branch || ' in the group'); ELSE bad('branch ' || c_branch",
          "    || ' not found in group ' || c_group); END IF;"]
    for pkg, name, n_args, n_in, fn in ROUTINES:
        L.append(f"  routine('{pkg}', '{name}', {n_args}, {n_in}, {'TRUE' if fn else 'FALSE'});")
    for t in tables:
        if "sequence" in m["tables"][t]:
            owner, seq = m["seq"](t).split(".")
            L.append(f"  seq_ahead('{t}', '{owner}', '{seq}');")
        for c in sorted(supplied.get(t, set())):
            L.append(f"  col_exists('{t}', '{c}');")
        L.append(f"  has_cols('{t}', '{','.join(sorted(supplied.get(t, set())))}');")
    for g in m["globals"]:
        t, n = g["table"], len(g["rows"])
        if g["start"] == "next-free":
            L += [f"  SELECT NVL(MAX(TRUNC(PK)), 0) INTO v_max FROM BOX_ACC.{t} WHERE PK - TRUNC(PK) = 0.65;",
                  f"  ok('{t}: {n} global .65 PK(s) from ' || (v_max + 1) || ' (next free - DEV only)');"]
        else:
            L += [f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{t} WHERE PK - TRUNC(PK) = 0.65",
                  f"  AND TRUNC(PK) BETWEEN {g['start']} AND {int(g['start']) + n - 1};",
                  (f"  IF v_n = 0 THEN ok('{t}: .65 range {g['start']}-{int(g['start']) + n - 1} free'); "
                  f"ELSE bad('{t}: ' || v_n || ' PK(s) already in the .65 range {g['start']}-{int(g['start']) + n - 1}'); "
                   "END IF;")]
        for r in g["rows"]:
            L += [f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{t} WHERE {key_where(r['row'], r['key'])};",
                  f"  IF v_n > 0 THEN ok('{t} {esc(r['label'])}: already present - will be skipped'); END IF;"]
    # every topic / account the block looks up - also the {ref: topic: / glta:} values of the other rows, the
    # accounts' and global objects' rows (DGBOUS 2026-10-29: a Cross Account Config row's account missing in BOX
    # passed the precheck and stopped the rehearsal)
    refs = {"topic": set(), "glta": set()}
    for row in ([r["row"] for r in m["rows"]] + [r["row"] for g in m["globals"] for r in g["rows"]]
                + [a["row"] for a in m["accounts"]] + [a["date_rule"] for a in m["accounts"] if a["date_rule"]]):
        for _, val in row:
            for mo in re.finditer(r"\b(topic|glta)_pk\('((?:[^']|'')*)'\)", str(val)):
                refs[mo.group(1)].add(mo.group(2).replace("''", "'"))
    codes_t = sorted({t for pp in m["pps"] for lst in pp["accounts"].values() for t in lst}
                     | {x for lp in m["locals"] for a in ("global", "local", "internal") for x in lp["arrays"][a]}
                     | refs["topic"])
    new_t = {r["label"] for g in m["globals"] if g["table"] == TOPICS for r in g["rows"]}
    for c in codes_t:
        if c not in new_t:
            L += [f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{TOPICS} WHERE CODE = '{esc(c)}' AND FK_OWNER_OBJ > 0;",
                  f"  IF v_n <> 1 THEN bad('topic {esc(c)}: ' || v_n || ' row(s), expected 1'); END IF;"]
    codes_a = sorted({a for pp in m["pps"] for lst in pp["accounts"].values() for a in lst.values()} | refs["glta"])
    new_a = {a["code"] for a in m["accounts"]}
    for c in codes_a:
        if c not in new_a:
            L += [f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{GLTA} WHERE CODE = '{esc(c)}' AND FK_OWNER_OBJ > 0;",
                  f"  IF v_n <> 1 THEN bad('account {esc(c)}: ' || v_n || ' row(s), expected 1'); END IF;"]
    for c in sorted(new_a):
        L += [f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{GLTA} WHERE CODE = '{esc(c)}' AND FK_OWNER_OBJ > 0;",
              f"  IF v_n > 0 THEN ok('account {esc(c)}: already present - will be skipped'); END IF;"]
    conds = sorted({c for lp in m["locals"] for c in lp["arrays"]["conditions"]})
    for c in conds:
        L += [f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.T_BOX_CONDPAR_PROP_S WHERE PK = {c} AND FK_OWNER_OBJ > 0;",
              f"  IF v_n <> 1 THEN bad('condition {c}: not in this environment (condition map, A-01-TGT)'); END IF;"]
    for lp in m["locals"]:
        L += [(f"  SELECT COUNT(*) INTO v_n FROM BOX_ACC.{LOPROP} WHERE FK_BRANCH = c_group AND FK_INSTRUMENT = "
              f"{lp['instrument']} AND INIVALPCDATE = TO_DATE('{lp['date']}','YYYY-MM-DD') AND FK_OWNER_OBJ > 0;"),
              (f"  IF v_n > 0 THEN bad('local property {esc(lp['key'])}: the group already has one (A-G4) - declare it in "
              "existing_local_properties'); END IF;")]
    L += ["  IF v_bad = 0 THEN",
          "    DBMS_OUTPUT.PUT_LINE('ACC PRECHECK OK - the config can be rendered. Save this output as '",
          "      || '<base>-precheck-output.txt');",
          "  ELSE",
          "    DBMS_OUTPUT.PUT_LINE('ACC PRECHECK PROBLEM - ' || v_bad || ' problem(s) above. Nothing can be rendered '",
          "      || 'until this file prints OK.');",
          "  END IF;",
          "END;", "/"]
    return "\n".join(L) + "\n"


def render_verify(v: dict, m: dict, sha: str) -> str:
    L = header(v, sha, "VERIFY (read-only) - each query says its expected result", run_order=False)
    L += [f"-- 1. the portfolio properties of group {m['group']}: STATUS (expected Valid, except expect_invalid)",
          f"SELECT FK_INSTRUMENT, STATUS, COUNT(*) AS n FROM BOX_ACC.{PPROP}",
          f"WHERE  FK_BRANCH = {m['group']} AND FK_OWNER_OBJ > 0 GROUP BY FK_INSTRUMENT, STATUS ORDER BY 1, 2;",
          (f"-- expected: {len(m['pps'])} new properties "
          f"({sum(1 for p in m['pps'] if p['expect_invalid'])} expected InValid)"),
          "-- 2. list rows without an account (expected: none)",
          f"SELECT l.FK_EXTENSION, COUNT(*) AS n FROM BOX_ACC.{LTOPIC} l JOIN BOX_ACC.{PPROP} p ON p.PK = l.FK_PARENT",
          f"WHERE  p.FK_BRANCH = {m['group']} AND l.FK_OWNER_OBJ = {OWN[PPROP]} AND l.FK_GLTA IS NULL GROUP BY l.FK_EXTENSION;",
          "-- 3. conditions without a value (expected: none)",
          f"SELECT c.FK_CONDITION, COUNT(*) AS n FROM BOX_ACC.{LCOND} c JOIN BOX_ACC.{PPROP} p ON p.PK = c.FK_PARENT",
          f"WHERE  p.FK_BRANCH = {m['group']} AND c.FK_OWNER_OBJ = {OWN[PPROP]} AND c.FK_EXTENSION = {COND_EXT}",
          "AND    c.VALUE_FUNC IS NULL AND c.FK_INSTRUMTYPE IS NULL AND c.FK_STRATEGY IS NULL AND c.FK_DEALTREAT IS NULL",
          "AND    c.FK_COLLATERALIND IS NULL AND c.STRUCTIND IS NULL GROUP BY c.FK_CONDITION;",
          f"-- 4. local properties of group {m['group']} (expected: one per instrument)",
          f"SELECT FK_INSTRUMENT, INIVALPCDATE, COUNT(*) AS n FROM BOX_ACC.{LOPROP}",
          f"WHERE  FK_BRANCH = {m['group']} AND FK_OWNER_OBJ > 0 GROUP BY FK_INSTRUMENT, INIVALPCDATE ORDER BY 1;"]
    codes = sorted({r["label"] for g in m["globals"] if g["table"] == TOPICS for r in g["rows"]})
    if codes:
        L += ["-- 5. the global topics created (expected: one row each, PK ending .65)",
              f"SELECT CODE, PK FROM BOX_ACC.{TOPICS} WHERE CODE IN (" + ", ".join(f"'{esc(c)}'" for c in codes) + ") ORDER BY 1;"]
    acc = sorted(a["code"] for a in m["accounts"])
    if acc:
        L += ["-- 6. the accounts created (expected: one row each)",
              f"SELECT CODE, COUNT(*) AS n FROM BOX_ACC.{GLTA} WHERE CODE IN ("
              + ", ".join(f"'{esc(c)}'" for c in acc[:900]) + ") GROUP BY CODE HAVING COUNT(*) <> 1;",
              "-- expected: no row"]
    return "\n".join(L) + "\n"


DELETE_ORDER = [LCOND, LTOPIC, PPROP, LINK, LOPROP, PDATE, GLTA, "T_BOX_CROSS_ACCTCONF_S", "T_BOX_CONF_INSTRUM_TYPE_S",
                "T_BOX_NETCCS_BSPLAN_S", HISTSTD, TOPICS]


def render_rollback(v: dict, sha: str, output: str):
    made: dict = {}
    glob: dict = {}
    for ln in output.splitlines():
        p = ln.strip().split("|")
        if len(p) >= 3 and p[0] in ("CREATED", "CREATED-GLOBAL") and NUM.fullmatch(p[2]) and IDENT.fullmatch(p[1]):
            made.setdefault(p[1], []).append(p[2])
            if p[0] == "CREATED-GLOBAL":
                glob.setdefault(p[1], []).append(p[2])
    if "ACC CONFIG COMMITTED" not in output:
        return None, None, "the config output does not say ACC CONFIG COMMITTED - nothing to undo, or not the whole output"

    def deletes(d, include_lists):
        L = []
        order = [t for t in DELETE_ORDER if t in d or (include_lists and t in (LCOND, LTOPIC) and PPROP in d)]
        for t in order:
            if t in (LCOND, LTOPIC):
                pks = d.get(PPROP, [])
                col, extra = "FK_PARENT", f" AND FK_OWNER_OBJ = {OWN[PPROP]}"
            else:
                pks, col, extra = d[t], "PK", ""
            for i in range(0, len(pks), 500):
                L += [f"  DELETE FROM BOX_ACC.{t} WHERE {col} IN ({', '.join(pks[i:i + 500])}){extra};",
                      f"  DBMS_OUTPUT.PUT_LINE(RPAD('{t}', 32) || SQL%ROWCOUNT || ' row(s) deleted');"]
        return L

    def wrap(what, body):
        return "\n".join(header(v, sha, what, run_order=False) + [
            "SET AUTOCOMMIT OFF", "SET SERVEROUTPUT ON SIZE UNLIMITED", "WHENEVER SQLERROR EXIT FAILURE ROLLBACK",
            "BEGIN", *body, "  COMMIT;", "  DBMS_OUTPUT.PUT_LINE('ROLLBACK DONE');", "END;", "/"]) + "\n"

    main_ = wrap("ROLLBACK - deletes exactly the rows the config created (its CREATED| lines)", deletes(made, True))
    g = wrap("GLOBAL PK ROLLBACK - deletes only the global .65 objects the config created (ADR 0018)",
             deletes(glob, False)) if glob else None
    return main_, g, None


# --- main -----------------------------------------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("run", help="the run folder (its 03-sql/acc-values.json)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--precheck", action="store_true", help="render the precheck only")
    g.add_argument("--rollback", action="store_true", help="render the rollback files from the config output")
    a = ap.parse_args(argv)
    run = Path(a.run)
    vp = run / VALUES
    if not vp.exists():
        print(f"REFUSED values-missing: {vp} (template: agents/sigom-box-acc-configs-agent/templates/"
              "acc-values.example.json)", file=sys.stderr)
        return 1
    raw = vp.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()[:16]
    try:
        v = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"REFUSED values-json: {e}", file=sys.stderr)
        return 1
    res = Result()
    m = validate(v, res)
    base = f"{v.get('branch', 'BRANCH')}-{v.get('env', 'env')}-acc"
    sql = run / "03-sql"
    if res.errors:
        for c, w, msg in res.errors:
            print(f"REFUSED {c}: {w}: {msg}", file=sys.stderr)
        return 1
    if a.precheck:
        (sql / f"{base}-precheck.sql").write_text(render_precheck(v, m, sha), encoding="utf-8")
        print(f"{sql / (base + '-precheck.sql')} - run it (BOX_ACC), save the output as {base}-precheck-output.txt")
        return 0
    if a.rollback:
        op = sql / f"{base}-config-output.txt"
        if not op.exists():
            print(f"REFUSED config-output-missing: {op}", file=sys.stderr)
            return 1
        r, gr, err = render_rollback(v, sha, op.read_text(encoding="utf-8", errors="replace"))
        if err:
            print(f"REFUSED config-output: {err}", file=sys.stderr)
            return 1
        (sql / f"{base}-rollback.sql").write_text(r, encoding="utf-8")
        if gr:
            (sql / "global_pk_rollback.sql").write_text(gr, encoding="utf-8")
        print(f"{sql / (base + '-rollback.sql')}" + (f" and {sql / 'global_pk_rollback.sql'}" if gr else ""))
        return 0
    po = sql / f"{base}-precheck-output.txt"
    out = po.read_text(encoding="utf-8", errors="replace") if po.exists() else ""
    if "ACC PRECHECK OK" not in out:
        print(f"REFUSED precheck-not-ok: {po} {'missing' if not po.exists() else 'does not end with ACC PRECHECK OK'} - "
              "render --precheck, run it, save its output", file=sys.stderr)
        return 1
    if f"values sha256 {sha}" not in out:
        print("REFUSED precheck-stale: the precheck output was made for other values - render --precheck and run it "
              "again", file=sys.stderr)
        return 1
    files = {f"{base}-rehearsal.sql": render_block(v, m, sha, "rehearsal"),
             f"{base}-config.sql": render_block(v, m, sha, "config"),
             f"{base}-verify.sql": render_verify(v, m, sha)}
    for n, t in files.items():
        (sql / n).write_text(t, encoding="utf-8")
    rep = [f"# Render report - {v['branch']} {v['env']} BOX ACC configuration", "",
           f"Rendered {datetime.datetime.now().isoformat(timespec='minutes')} from `{VALUES}` (sha256 {sha}).", "",
           "| What | Count |", "|---|---|",
           *[f"| global {g['table']} (.65, {'next free - DEV' if g['start'] == 'next-free' else 'from ' + g['start']}) "
             f"| {len(g['rows'])} |" for g in m["globals"]],
           (f"| accounts | {len(m['accounts'])} ({sum(1 for x in m['accounts'] if x['date_rule'] is not None)} with a date "
           "rule) |"),
           f"| local properties | {len(m['locals'])} |",
           (f"| portfolio properties | {len(m['pps'])} ({sum(1 for p in m['pps'] if p['expect_invalid'])} expected "
           "InValid) |"),
           f"| other rows | {len(m['rows'])} |", "",
           ("Run: rehearsal (ROLLBACK) → config (COMMIT, save the output as "
           f"`{base}-config-output.txt`) → verify → `render_acc_sql.py <run> --rollback` renders the undo.")]
    (sql / "render-report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    for n in files:
        print(sql / n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
