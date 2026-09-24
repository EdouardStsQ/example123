#!/usr/bin/env python3
"""
Regression tests for scripts/render_sql.py and scripts/validate_run_output.py.

    python3 scripts/tests/test_validate_run_output.py

Three groups, both directions each (a check that fires on good output is worse than no check):
  1. the renderer: a good values file renders four clean files; each bad values file is REFUSED with the
     code written for it, and nothing is written;
  2. the rendered SQL: structural PL/SQL lint (blocks, IF, LOOP, parentheses, quotes, declaration order);
  3. the validator: the rendered run is clean; each hand edit trips `sql-edited-by-hand` AND the specific
     check for the defect it introduces (defence in depth: the checks still hold if a file is edited).
"""
from __future__ import annotations
import copy, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VALIDATOR = ROOT / "scripts/validate_run_output.py"
EXAMPLE = ROOT / "agents/sigom-box-fe-configs-agent/templates/values.example.json"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))
import build_fixtures as bf  # noqa: E402
import render_sql  # noqa: E402

OK = True


def report(passed: bool, label: str, detail: str = "") -> None:
    global OK
    OK &= passed
    print(("✓ " if passed else "✗ ") + label + ("" if passed or not detail else "\n" + detail))


def run(folder: Path) -> tuple[set[str], set[str], str]:
    out = subprocess.run([sys.executable, str(VALIDATOR), str(folder)], capture_output=True, text=True).stdout
    return (set(re.findall(r"^\s+FAIL\s+(\S+)", out, re.M)), set(re.findall(r"^\s+WARN\s+(\S+)", out, re.M)), out)


def tmp_run(values: dict, render: bool = True, edit=None):
    """A fresh run folder from `values` (after edit(values)); rendered unless render=False."""
    vals = copy.deepcopy(values)
    if edit:
        edit(vals)
    folder = Path(tempfile.mkdtemp()) / "run"
    res = bf.write_run(folder, vals, render=render)
    return folder, res


# ------------------------------------------------------------------------------------------------
# PL/SQL structural lint — no Oracle here, so check what a parser would reject first
# ------------------------------------------------------------------------------------------------

def plsql_lint(sql: str) -> list[str]:
    problems = []
    code = re.sub(r"--[^\n]*", " ", sql)                         # comments (no '--' inside our strings)
    if code.count("'") % 2:
        problems.append("odd number of single quotes")
    code = re.sub(r"'(?:[^']|'')*'", "''", code)                  # string contents
    blocks = [b for b in re.split(r"^\s*/\s*$", code, flags=re.M) if b.strip()]
    for b in blocks:
        body = re.sub(r"^\s*SET\s+[^\n]*$", " ", b, flags=re.M | re.I)
        if not re.search(r"\bDECLARE\b|\bBEGIN\b", body, re.I):
            continue
        up = body.upper()
        n_end_if, n_end_loop = len(re.findall(r"\bEND\s+IF\b", up)), len(re.findall(r"\bEND\s+LOOP\b", up))
        n_if = len(re.findall(r"\bIF\b", up)) - n_end_if
        n_loop = len(re.findall(r"\bLOOP\b", up)) - n_end_loop
        n_begin = len(re.findall(r"\bBEGIN\b", up))
        n_end = len(re.findall(r"\bEND\b(?!\s+(IF|LOOP)\b)", up)) - len(re.findall(r"\bCASE\b", up))
        if n_if != n_end_if:
            problems.append(f"IF {n_if} vs END IF {n_end_if}")
        if n_loop != n_end_loop:
            problems.append(f"LOOP {n_loop} vs END LOOP {n_end_loop}")
        if n_begin != n_end:
            problems.append(f"BEGIN {n_begin} vs END {n_end}")
        if body.count("(") != body.count(")"):
            problems.append(f"parentheses ( {body.count('(')} vs ) {body.count(')')}")
        dm = re.search(r"\bDECLARE\b", up)
        if dm:
            rest = up[dm.end():]
            n_sub = len(re.findall(r"\b(?:PROCEDURE|FUNCTION)\s+\w+", rest.split("\nBEGIN\n")[0]))
            stripped = re.sub(r"\b(?:PROCEDURE|FUNCTION)\s+(\w+)[\s\S]*?\bEND\s+\1\s*;", "@SUB@", rest)
            decl = stripped.split("BEGIN", 1)[0]
            if decl.count("@SUB@") != n_sub:
                problems.append("a subprogram is not closed by END <its name>;")
            if "@SUB@" in decl and re.search(r"\b[A-Z_]\w*\s+(CONSTANT\s+)?[A-Z_][\w.%]*[^;]*;",
                                             decl[decl.index("@SUB@"):].replace("@SUB@", " ")):
                problems.append("a variable is declared after a subprogram (PLS-00103)")
        if not re.search(r"\bEND\s*;\s*$", body.strip(), re.I):
            problems.append("block does not end with END;")
        for stmt in re.findall(r"INSERT\s+INTO[^;]*;", body, re.I):
            if re.search(r"\bchk_pk\s*\(|\bexpect_rows\s*\(", stmt, re.I):
                problems.append("a local procedure inside an INSERT")
    for s in re.split(r";", re.sub(r"^\s*/\s*$", ";", code, flags=re.M)):
        if s.count("(") != s.count(")"):
            problems.append(f"unbalanced parentheses in statement: {s.strip()[:60]!r}")
            break
    return problems


LINT_BROKEN = {
    "IF without END IF": "DECLARE v NUMBER; BEGIN IF v = 1 THEN v := 2; END; END;\n/\n",
    "variable after a subprogram": ("DECLARE\n  PROCEDURE p IS BEGIN NULL; END p;\n  v NUMBER;\nBEGIN\n  p;\nEND;\n/\n"),
    "procedure inside VALUES": ("DECLARE v_pk NUMBER;\n  PROCEDURE chk_pk (x NUMBER) IS BEGIN NULL; END chk_pk;\nBEGIN\n"
                                "  INSERT INTO T (A) VALUES (chk_pk(v_pk));\nEND;\n/\n"),
    "unbalanced parentheses": "BEGIN\n  INSERT INTO T (A VALUES (1);\nEND;\n/\n",
}


def check_rendered_files(label: str, res) -> None:
    for name, text in res.files.items():
        bad = [c for c in text if ord(c) > 126]
        report(not bad and "{{" not in text and "@@" not in text and "--#" not in text,
               f"{label}: {name} is ASCII, no placeholder or template note left", str(bad[:3]))
        probs = plsql_lint(text)      # the verify file too: its statements' parentheses and quotes
        report(not probs, f"{label}: {name} passes the SQL/PL-SQL structural lint", "; ".join(probs))


# ------------------------------------------------------------------------------------------------

def shape(o):
    if isinstance(o, dict):
        return {k: shape(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, list):
        return [shape(o[0])] if o else []
    return "leaf"


def main() -> int:
    good_res = bf.good()
    bf.run3_like()
    good = bf.OUT / "good"
    V = bf.VALUES

    # === 0. the lint itself must catch what it claims to ========================================
    for what, sql in LINT_BROKEN.items():
        report(bool(plsql_lint(sql)), f"the PL/SQL lint catches: {what}")

    # === 1. renderer ============================================================================
    report(not good_res.errors and len(good_res.files) == 4, "good values render four files, no refusal",
           str(good_res.errors))
    check_rendered_files("good", good_res)
    again = render_sql.render(good)
    report(again.files == good_res.files, "rendering is deterministic (same inputs, same bytes)")
    cfg = good_res.files["NY_SCH-tier2-pre-config.sql"]
    reh = good_res.files["NY_SCH-tier2-pre-rehearsal.sql"]
    code_only = lambda s: re.sub(r"'(?:[^']|'')*'", "''", re.sub(r"--[^\n]*", "", s))
    call = "BOX_FE.PKG_ENGPRECOMMIT.p_check_Val_Curves_precommit(:pk)"
    c_code, r_code = code_only(cfg), code_only(reh)
    report(call in cfg and call in reh and "COMMIT;" in c_code and "ROLLBACK;" not in c_code
           and "ROLLBACK;" in r_code and "COMMIT;" not in r_code,
           "both files run both pre-commits; config ends in COMMIT, rehearsal in ROLLBACK")
    import difflib
    changed = [l for l in difflib.unified_diff(reh.splitlines(), cfg.splitlines(), n=0, lineterm="")
               if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    report(len(changed) <= 20, f"rehearsal and config differ only at the head and the tail ({len(changed)} lines)",
           "\n".join(changed))
    report(shape(json.loads(EXAMPLE.read_text())) == shape(V), "values.example.json has exactly the fixture's shape",
           f"{shape(json.loads(EXAMPLE.read_text()))}\n!=\n{shape(V)}")
    ex_folder, _ = tmp_run(V, render=False)
    shutil.copy(EXAMPLE, ex_folder / "03-sql/values.json")
    ex = render_sql.render(ex_folder)
    report("values-placeholder" in ex.codes() and not ex.files, "the untouched example is refused (placeholders)")

    def refuses(label, code, edit, evidence=None):
        folder, _ = tmp_run(V, render=False, edit=edit)
        if evidence:
            evidence(folder)
        res = render_sql.render(folder)
        report(code in res.codes() and not res.files, f"refused — {label} [{code}]",
               f"got {sorted(res.codes())}")

    def at(path):
        def get(v):
            for k in path:
                v = v[k]
            return v
        return get

    refuses("a <placeholder> left", "values-placeholder",
            lambda v: v["steps"]["2"]["description"].update(value="<DESCRIPTION exactly as mined>"))
    refuses("a value without a source", "values-no-source",
            lambda v: v["steps"]["2"]["fk_calendar"].update(source=""))
    refuses("a source that names nothing", "values-no-source",
            lambda v: v["steps"]["2"]["fk_calendar"].update(source="as agreed"))
    refuses("a decision cited but not logged", "decision-missing", lambda v: v["steps"]["6"].update(decisions=[9]))
    refuses("a decided step with no decision", "decision-missing", lambda v: v["steps"]["12"].pop("decisions"))
    refuses("step 6 row without FK_BASIS (run 5)", "step6-missing-column", lambda v: v["steps"]["6"]["rows"][1].pop("FK_BASIS"))
    refuses("step 6 NULL in a NOT NULL column", "step6-null-in-not-null",
            lambda v: v["steps"]["6"]["rows"][0].update(BYTRIGGER=None))
    refuses("step 6 misspelt column", "step6-unknown-column", lambda v: v["steps"]["6"]["rows"][0].update(FK_BASE="2.4"))
    refuses("step 6 missing an instrument", "step6-rows-not-approved-set", lambda v: v["steps"]["6"]["rows"].pop())
    refuses("step 12 unapproved instrument", "instrument-not-approved",
            lambda v: v["steps"]["12"]["rows"][0].update(FK_INSTRUMENT="8.4"))
    refuses("LIMIT_ERRORS 0 (run 3)", "step12-limit", lambda v: v["steps"]["12"]["rows"][0].update(LIMIT_ERRORS=0))
    refuses("dummy book = the real book (run 4)", "dummy-is-a-book",
            lambda v: v["steps"]["11"]["dummy_book"].update(value="23958.44"))
    refuses("dummy label without its BOX FE decision", "decision-missing",
            lambda v: v["steps"]["11"]["dummy_book"].update(source="Q-10d"))
    refuses("Days Matured with the Config owner (run 4)", "identity-not-distinct",
            lambda v: v["identity"]["owner_days_matured"].update(value="35000126.65"))
    refuses("auth code differs from 00-inputs.md", "values-disagree-with-inputs",
            lambda v: v["environment"]["target_auth_code"].update(value="21"))
    refuses("an instrument not in APPROVED_INSTRUMENTS", "values-disagree-with-inputs",
            lambda v: v["branch"]["approved_instruments"].pop())
    refuses("step 1: a configuration already exists", "step-unsupported-status",
            lambda v: v["steps"]["1"].update(status="CONFIRMED_PRESENT"))
    refuses("steps 9/10 reopened without repo support", "step-unsupported-status",
            lambda v: v["steps"]["10"].update(status="PROPOSED"))
    refuses("step 4 count differs from the CSV", "count-disagrees",
            lambda v: v["steps"]["4"]["expected_count"].update(value=37))
    refuses("step 7 count differs from the filtered CSV", "count-disagrees",
            lambda v: v["steps"]["7"]["expected_count"].update(value=14))
    refuses("step 7 CONFIRMED_ABSENT but the CSV has the branch's rows", "count-disagrees",
            lambda v: (v["steps"]["7"].update(status="CONFIRMED_ABSENT"), v["steps"]["7"].pop("expected_count")))
    refuses("14a creates a row that already exists", "step14a-coverage",
            lambda v: v["steps"]["14a"]["rows"].append({"FK_INSTRUMENT": "20092.4", "NUM_DAYS": 30, "source": "decision 5"}))
    refuses("14a leaves an instrument unaccounted", "step14a-coverage",
            lambda v: v["steps"]["14a"]["already_present"].pop())
    refuses("a held step that names no one", "values-missing-field",
            lambda v: v["steps"]["12"].update(status="SME_DECISION_REQUIRED"))
    refuses("a non-canonical status", "values-bad-status", lambda v: v["steps"]["6"].update(status="REQUIRES_SME_VALUE"))
    refuses("a number that is not a number", "values-not-a-number",
            lambda v: v["steps"]["2"]["fk_calendar"].update(value="83,4x"))
    refuses("a schema owner that is not a name", "values-bad-owner",
            lambda v: v["environment"]["sequence_function_owner"].update(value="BOX FE"))
    refuses("a quote reference that does not resolve", "evidence-unresolved", None,
            lambda f: (f / "01-evidence/Q-04c-quote-ref-column-counts.csv").write_text("N_ROWS,N_FK_BS,N_RESOLVED\n39,38,38\n"))
    refuses("the Q-06c CSV missing", "evidence-missing", None,
            lambda f: (f / "01-evidence/Q-06c-accrual-exceptions-emit.csv").unlink())
    refuses("the status disagrees with 02-findings.md", "findings-disagree", None,
            lambda f: (f / "02-findings.md").write_text((f / "02-findings.md").read_text()
                                                        .replace("| 12 | object | PROPOSED", "| 12 | object | SME_DECISION_REQUIRED")))
    refuses("the target has no such column (Q-G3d)", "target-column-missing", None,
            lambda f: (f / "01-evidence/Q-G3d-columns.csv").write_text((f / "01-evidence/Q-G3d-columns.csv").read_text()
                                                                     .replace("T_BOX_ENGACCRCONF_S,FK_MDRBASIS,", "T_BOX_ENGACCRCONF_S,FK_MDR_BASIS,")))
    refuses("a NOT NULL column the template does not write (Q-G3d)", "target-not-null-not-written", None,
            lambda f: (f / "01-evidence/Q-G3d-columns.csv").write_text((f / "01-evidence/Q-G3d-columns.csv").read_text()
                                                                     + "T_BOX_ERRORS_FE_S,FK_SCOPE,NUMBER,22,N,N\n"))
    refuses("a NULL into a NOT NULL target column (Q-G3d)", "target-null-in-not-null",
            lambda v: v["steps"]["6"]["rows"][0].update(FK_BASIS=None), lambda f: (f / "01-evidence/Q-G3d-columns.csv").write_text(
                (f / "01-evidence/Q-G3d-columns.csv").read_text().replace("T_BOX_ENGACCRCONF_S,FK_BASIS,NUMBER,22,Y", "T_BOX_ENGACCRCONF_S,FK_BASIS,NUMBER,22,N")))
    refuses("a DESCRIPTION longer than its column (Q-G3d)", "target-text-too-long",
            lambda v: v["steps"]["3"]["description"].update(value="X" * 101))
    refuses("the Q-G3d columns CSV missing", "evidence-missing", None,
            lambda f: (f / "01-evidence/Q-G3d-columns.csv").unlink())
    refuses("a DDATE expression that is not supported", "step14a-ddate",
            lambda v: v["steps"]["14a"]["ddate"].update(value="DATE '2026-01-01'"))
    refuses("a decision signed by 'user'", "decision-incomplete", None,
            lambda f: (f / "00-decisions.md").write_text((f / "00-decisions.md").read_text()
                                                         .replace("| fixture SME | product SME | 2026-09-24 | Q-13 (b)",
                                                                  "| user | user | 2026-09-24 | Q-13 (b)")))

    # text literals: apostrophe doubled; non-ASCII carried by UNISTR, the file stays ASCII
    f, res = tmp_run(V, edit=lambda v: (v["steps"]["2"]["description"].update(value="Configuración -NY's"),))
    c = res.files.get("NY_SCH-tier2-pre-config.sql", "")
    report("UNISTR('Configuraci\\00F3n -NY''s')" in c and all(ord(ch) < 127 for ch in c),
           "non-ASCII text is rendered as UNISTR(...), apostrophes doubled, the file stays ASCII",
           str(res.errors) + c[:0])

    f, res = tmp_run(V, edit=lambda v: v["steps"]["14a"]["ddate"].update(value="TRUNC(SYSDATE)"))
    report("TRUNC(SYSDATE), 20213.4, 30);" in res.files.get("NY_SCH-tier2-pre-config.sql", "") and run(f)[0] == set(),
           "DDATE = TRUNC(SYSDATE) renders and validates", str(res.errors))

    # a held decided step: DRAFT, config stops at once, rehearsal still runs; validator clean
    def hold12(v):
        v["steps"]["12"] = {"status": "SME_DECISION_REQUIRED", "source": "Q-13 (b)", "waits_on": "product SME"}
    f, res = tmp_run(V, edit=hold12)
    cfg, reh = res.files.get("NY_SCH-tier2-pre-config.sql", ""), res.files.get("NY_SCH-tier2-pre-rehearsal.sql", "")
    report(not res.errors and "-20099" in cfg and "-20099" not in reh and "T_BOX_ERRORS_FE_S (PK" not in cfg,
           "a held step renders a DRAFT: the config stops on its first statement, the rehearsal runs", str(res.errors))
    check_rendered_files("draft", res)
    fails, warns, out = run(f)
    report(not fails, "the DRAFT run folder validates with 0 FAIL", out)

    # 14a all present: no step-14a SQL, V8 still checks every instrument has a row
    def all_present(v):
        v["steps"]["14a"] = {"status": "CONFIRMED_PRESENT", "source": "Q-12 (a)",
                             "already_present": [{"value": i, "source": "Q-12 (a)"} for i in bf.INSTR]}
    f, res = tmp_run(V, edit=all_present)
    ver = res.files.get("NY_SCH-tier2-pre-verify.sql", "")
    report(not res.errors and "T_BOX_ENGDAYS_MATURED_S (PK" not in res.files.get("NY_SCH-tier2-pre-config.sql", "x")
           and "V8" in ver and run(f)[0] == set(),
           "14a CONFIRMED_PRESENT: no 14a insert, V8 kept, validator clean", str(res.errors))

    # core held: nothing to render
    f, res = tmp_run(V, edit=lambda v: v["steps"]["4"].update(status="EVIDENCE_REQUIRED", waits_on="operator: Q-04c"))
    report(bool(not res.errors and not res.files and res.nothing_to_render), "steps 2-5 not ready: nothing is rendered")

    # === 3. validator on the rendered run, and on hand edits ======================================
    fails, warns, out = run(good)
    report(not fails and not warns, "the rendered run validates clean", out)
    fails, _, out = run(bf.OUT / "run3-like")
    need = {"auth-code-not-asserted", "source-column-wrong", "quote-refs-not-evidence", "curve-fk-null",
            "branch-fk-not-branch", "conf-by-book-no-dummy", "rollback-dead-code", "unresolved-substitution",
            "verify-script-missing", "rollback-script-missing", "values-missing"}
    report(need <= fails, "run-3-like hand-written output trips every expert-review check", str(need - fails))

    def edited(file_glob, old, new, count=1):
        tmp = Path(tempfile.mkdtemp()) / "run"
        shutil.copytree(good, tmp)
        [p] = list((tmp / "03-sql").glob(file_glob))
        text = p.read_text()
        assert old in text, f"mutation anchor not found in {p.name}: {old!r}"
        p.write_text(text.replace(old, new, count))
        return tmp

    def expect(label, folder, must_fail):
        fails, _, out = run(folder)
        missing = set(must_fail) - fails
        report(not missing, f"hand edit caught — {label} {sorted(must_fail)}", out)

    E = "sql-edited-by-hand"
    C = "*-config.sql"
    expect("config reads DEVENG", edited(C, "IF v_quote_refs.COUNT <> c_expected_quote_refs THEN",
           "SELECT COUNT(*) INTO v_n FROM DEVENG.T_PGT_ENGLKFC_X;\n  IF v_quote_refs.COUNT <> c_expected_quote_refs THEN"),
           {E, "config-reads-other-schema"})
    expect("a quote ref not in the evidence", edited(C, "6400.4, 6401.4,", "6399.4, 6401.4,"), {E, "quote-refs-not-evidence"})
    expect("an exception row for another strategy", edited(C, "SELECT 2.4 AS FK_INSTRUMENT, 142.4 AS FK_STRATEGY",
           "SELECT 2.4 AS FK_INSTRUMENT, 144.4 AS FK_STRATEGY"), {E, "exceptions-not-evidence"})
    expect("an allocation without chk_pk", edited(C, "chk_pk(v_curve_pk, 'T_BOX_ENGFCURVE_S');", ""), {E, "pk-not-checked"})
    expect("step 7 copies GBO FK_BRANCH", edited(C, "r.CRITERIAL, c_branch_pk,", "r.CRITERIAL, r.FK_BRANCH,"),
           {E, "branch-fk-copied"})
    expect("verify without the auth check", edited("*-verify.sql", "gom_glb_sys.t__CORE_INFO_S", "dual", 2),
           {E, "verify-no-auth-check"})
    expect("built for another auth code", edited(C, "c_expected_fraction   CONSTANT NUMBER := 0.99;",
           "c_expected_fraction   CONSTANT NUMBER := 0.21;"), {E, "auth-code-mismatch"})
    expect("source front copied from GBO", edited(C, "c_source_front        CONSTANT NUMBER := 513.4;",
           "c_source_front        CONSTANT NUMBER := 9.4;"), {E, "source-column-wrong"})
    expect("dummy rows replaced by the book", edited(C, "20092.4, c_dummy_book);", "20092.4, 23958.44);", 1),
           {E})
    expect("header curve columns NULL (ORA-01400)", edited(C, "v_curve_pk, v_curve_pk, c_source_front",
           "NULL, NULL, c_source_front"), {E, "curve-fk-null"})
    expect("cursor field not named by its SELECT (run 4)", edited(C, "r.FK_INSTRUMENT, r.FK_STRATEGY, r.FK_INSTRTYPE",
           "r.instrument, r.strategy, r.instrtype"), {E, "cursor-field-undeclared"})
    expect("Days Matured with the Config owner (run 4)", edited(C, "c_owner_days_matured  CONSTANT NUMBER := 35000145.65;",
           "c_owner_days_matured  CONSTANT NUMBER := 35000126.65;"), {E, "identity-wrong-object"})
    expect("dummy set to the real book (run 4)", edited(C, "c_dummy_book          CONSTANT NUMBER := 2741.44;",
           "c_dummy_book          CONSTANT NUMBER := 23958.44;"), {E, "dummy-is-a-book"})
    expect("verify check that cannot fail (run 4)", edited("*-verify.sql", "-- V2 - ROW COUNTS",
           "SELECT COUNT(*) FROM BOX_FE.T_BOX_ENGCONF_S WHERE 1=0 AND 0.44 <> 0.44;\n-- V2 - ROW COUNTS"),
           {E, "verify-placebo"})
    expect("verify without the GBO comparison for step 4", edited("*-verify.sql", "DEVENG.T_PGT_ENGLKFC_X",
           "BOX_FE.T_BOX_ENGLKFC_X", 2), {E, "verify-incomplete"})
    expect("step header without its Source line (run 4)", edited(C, "  -- Source      : FK_BS = c_branch_pk (Q-01c)\n", ""),
           {E, "step-header-incomplete"})
    expect("no curve pre-commit (run 4)", edited(C,
           "EXECUTE IMMEDIATE 'BEGIN BOX_FE.PKG_ENGPRECOMMIT.P_ENGFixingCurve_PreCommit(:pk); END;' USING v_curve_pk;", "NULL;"),
           {E, "curve-precommit-missing"})
    expect("chk_pk inside VALUES (run 5)", edited(C, "VALUES (v_pk, c_owner_errors, c_branch_pk,",
           "VALUES (chk_pk(v_pk, 'X'), c_owner_errors, c_branch_pk,"), {E, "local-procedure-in-sql"})
    expect("a guard that cannot fire (run 5)", edited(C,
           "SELECT COUNT(*) INTO v_n FROM BOX_FE.T_BOX_ERRORS_FE_S WHERE FK_BRANCH = c_branch_pk;\n  expect_rows('pre-flight: T_BOX_ERRORS_FE_S rows for the branch', v_n, 0);",
           "IF c_expected_auth_code = -1 THEN RAISE_APPLICATION_ERROR(-20012, 'x'); END IF;"),
           {E, "guard-placebo", "no-existing-row-guard"})
    expect("a count that is never tested", edited(C,
           "expect_rows('pre-flight: T_BOX_CONF_BY_BOOK_S rows for the branch', v_n, 0);", "NULL;"),
           {E, "no-existing-row-guard"})
    expect("typed quote refs beside the list (run 5)", edited(C, "v_curve_pk, v_quote_refs(i));", "v_curve_pk, 22.35);"),
           {E, "quote-refs-typed"})
    expect("a step with no header (run 5)", edited(C, "  -- STEP 5 - Branch association", "  -- Branch association"),
           {E, "step-without-header"})
    expect("step 11 rows without FK_PARENT (run 5)", edited(C,
           "(PK, FK_OWNER_OBJ, FK_PARENT, FK_EXTENSION, FK_BRANCH, FK_INSTRUMENT, FK_LABEL)\n  VALUES (v_pk, c_owner_conf, v_conf_pk, c_ext_conf_by_book,",
           "(PK, FK_OWNER_OBJ, FK_EXTENSION, FK_BRANCH, FK_INSTRUMENT, FK_LABEL)\n  VALUES (v_pk, c_owner_conf, c_ext_conf_by_book,"),
           {E, "conf-by-book-no-parent"})
    expect("Config pre-commit replaced by COMMIT (run 5)", edited(C,
           "EXECUTE IMMEDIATE 'BEGIN BOX_FE.PKG_ENGPRECOMMIT.p_check_Val_Curves_precommit(:pk); END;' USING v_conf_pk;",
           "COMMIT;"), {E, "config-precommit-missing"})
    early = edited(C, "EXECUTE IMMEDIATE 'BEGIN BOX_FE.PKG_ENGPRECOMMIT.P_ENGFixingCurve_PreCommit(:pk); END;' USING v_curve_pk;",
                   "NULL;")
    [cf] = list((early / "03-sql").glob(C))
    cf.write_text(cf.read_text().replace("  INSERT INTO BOX_FE.T_BOX_ENGFCURVE_S",
                                         "  BOX_FE.PKG_ENGPRECOMMIT.P_ENGFixingCurve_PreCommit(v_curve_pk);\n  INSERT INTO BOX_FE.T_BOX_ENGFCURVE_S", 1))
    expect("curve pre-commit before the array (run 5)", early, {E, "curve-precommit-before-array"})
    expect("an unapproved instrument typed into step 12", edited(C, "c_branch_pk, 20111.4, 100);", "c_branch_pk, 8.4, 100);"),
           {E, "instrument-out-of-scope"})
    expect("the rehearsal edited", edited("*-rehearsal.sql", "ROLLBACK;", "COMMIT;"), {E})
    extra = edited(C, "SET DEFINE OFF", "SET DEFINE OFF")
    (extra / "03-sql/NY_SCH-tier2-pre-steps-1-to-11.sql").write_text("-- hand-written\nSELECT 1 FROM dual;\n")
    expect("a hand-written file beside the rendered ones", extra, {"sql-not-rendered"})
    novals = edited(C, "SET DEFINE OFF", "SET DEFINE OFF")
    (novals / "03-sql/values.json").unlink()
    expect("SQL with no values.json", novals, {"values-missing"})
    stale = edited(C, "SET DEFINE OFF", "SET DEFINE OFF")
    vj = stale / "03-sql/values.json"
    vd = json.loads(vj.read_text())
    vd["steps"]["12"]["rows"][0]["LIMIT_ERRORS"] = 90
    vj.write_text(json.dumps(vd))
    expect("values.json changed, SQL not rendered again", stale, {E})
    tagged = edited(C, "SET DEFINE OFF", "SET DEFINE OFF")
    fnd = tagged / "02-findings.md"
    fnd.write_text(fnd.read_text() + "\nStep 6: [confirmed: Q-05d] SME approved SLB BOX values\n")
    expect("a decision tagged [confirmed] (run 4)", tagged, {"decision-tagged-confirmed"})
    nodec = edited(C, "SET DEFINE OFF", "SET DEFINE OFF")
    (nodec / "00-decisions.md").unlink()
    expect("decided steps with no decisions log", nodec, {"decisions-log-missing", "values-invalid"})
    sme = edited(C, "SET DEFINE OFF", "SET DEFINE OFF")
    fnd = sme / "02-findings.md"
    fnd.write_text(fnd.read_text().replace("| 6 | object | PROPOSED", "| 6 | object | SME_DECISION_REQUIRED"))
    expect("SQL for a step still awaiting its SME", sme, {"sql-with-open-sme-decision", "values-invalid"})

    print("\nall passed" if OK else "\nFAILURES")
    return 0 if OK else 1


if __name__ == "__main__":
    sys.exit(main())
