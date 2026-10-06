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
    report(not good_res.errors and len(good_res.files) == 5 and "NY_SCH-tier2-pre-P1-pk-precheck.sql" in good_res.files,
           "good values render the P1 pre-step and the four files, no refusal", str(good_res.errors))
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
    report(bool(not res.errors and set(res.files) == {"NY_SCH-tier2-pre-P1-pk-precheck.sql"} and res.nothing_to_render),
           "steps 2-5 not ready: only the P1 pre-step is rendered")

    # === pre-steps (BOX Lead review, 2026-09-25) ====================================================
    f, _ = tmp_run(V, render=False, edit=lambda v: v.update(steps={}, identity={"_": "later"}))
    pre = render_sql.render(f, precheck_only=True)
    p1 = pre.files.get("NY_SCH-tier2-pre-P1-pk-precheck.sql", "")
    report(not pre.errors and list(pre.files) == ["NY_SCH-tier2-pre-P1-pk-precheck.sql"]
           and "BOX_FE.F___SEQUENCE(p_table, 'X')" in p1 and "PK PRECHECK OK - auth code" in p1,
           "--precheck renders P1 from the environment alone, before the rest of values.json exists", str(pre.errors))
    report(not plsql_lint(p1), "P1 passes the structural lint", "; ".join(plsql_lint(p1)))
    refuses("config built before P1 was run", "pk-precheck-missing", None,
            lambda f: (f / "01-evidence/Q-P1-pk-precheck.txt").unlink())
    refuses("config built while P1 reports a problem", "pk-precheck-not-ok", None,
            lambda f: (f / "01-evidence/Q-P1-pk-precheck.txt").write_text(
                (f / "01-evidence/Q-P1-pk-precheck.txt").read_text()
                + "PK PRECHECK PROBLEM - 3 existing PK(s) with fraction .99 sit at or ahead of the sequence\n"))
    refuses("P1 OK for another auth code", "pk-precheck-not-ok", None,
            lambda f: (f / "01-evidence/Q-P1-pk-precheck.txt").write_text("PK PRECHECK OK - auth code 21: ...\n"))

    # === FE step 11 reads skill set-up-book-labels (2026-09-30) =====================================
    refuses("step 11 with no book folder", "book-setup-missing", None,
            lambda f: shutil.rmtree(f / "books"))
    refuses("step 11 while the book folder is refused (a dummy no other branch uses - run 6)", "book-setup-invalid",
            None, lambda f: (f / "books/01-evidence/Q-10c-dummy-book-target.csv").write_text("FK_BRANCH,COUNT(*)\n20007.4,6\n"))
    refuses("step 11 while a book label is only proposed", "book-labels-pending", None,
            lambda f: bf.book_folder(f / "books", rows=(("XBR01", "BOOK_A", ""), ("XBR02", "BOOK B", "30001.44")),
                                     config=dict(bf.BOOK_CONFIG, pk_rule={"mode": "fixed", "source": "decision 1"},
                                                 model_columns=[{"name": "FK_OWNER_OBJ", "value": "17910.4",
                                                                 "source": "Q-10f"}])))
    refuses("step 11 books other than the register's", "book-labels-disagree",
            lambda v: v["steps"]["11"]["books"].append({"value": "23990.44", "name": "OTHER", "source": "decision 2"}))
    refuses("step 11 dummy other than the register's", "book-labels-disagree",
            lambda v: v["steps"]["11"]["dummy_book"].update(value="2742.44"),
            lambda f: (f / "00-inputs.md").write_text((f / "00-inputs.md").read_text().replace("2741.44", "2742.44")))
    refuses("the old P2/P3 proposals left in values.json", "values-moved",
            lambda v: v.update(prechecks={"dummy_label_proposal": {}}))

    # === skill set-up-book-labels: scripts/set_up_book_labels.py ====================================
    import set_up_book_labels as sbl

    def books_dir(**kw):
        d = Path(tempfile.mkdtemp()) / "books"
        bf.book_folder(d, **kw)
        return d
    with_rule = lambda **pk: dict(bf.BOOK_CONFIG, pk_rule=dict({"mode": "fixed", "source": "decision 1"}, **pk),
                                  model_columns=[{"name": "FK_OWNER_OBJ", "value": "17910.4", "source": "Q-10f"}])
    two = (("XBR01", "BOOK_A", ""), ("XBR02", "BOOK B desk", "30001.44"))

    r, st = sbl.evaluate(books_dir())
    report(not r.errors and st["complete"] and st["dummy"] == "2741.44" and st["books"] == {"XBR01": "23958.44"}
           and sbl.PROPOSAL not in r.files and "XBR01,BOOK_A,23958.44,exists" in r.files[sbl.REGISTER],
           "labels skill: every label exists, the dummy is shared - register complete, no proposal", str(r.errors))
    r, st = sbl.evaluate(books_dir(rows=two, config=with_rule()))
    prop = r.files.get(sbl.PROPOSAL, "")
    code_p = re.sub(r"--[^\n]*", "", prop)
    report(not r.errors and st["to_create"] == ["XBR02"] and "INSERT INTO PGT_SYS.PGT_DOMAINS" in prop
           and "30001.44, 'XBR02', 'BOOK B desk', 17910.4" in prop and "'XBR01'" not in code_p
           and "COMMIT" not in code_p and not st["complete"],
           "labels skill: a missing book label is proposed (fixed PK, exact description, no COMMIT)", str(r.errors))
    report(not plsql_lint(prop), "labels proposal passes the structural lint", "; ".join(plsql_lint(prop)))
    r, st = sbl.evaluate(books_dir(rows=two, config=with_rule(mode="expression",
                                                              value="PGT_SYS.F___SEQUENCE('PGT_DOMAINS','X')")))
    report(not r.errors and "VALUES (PGT_SYS.F___SEQUENCE('PGT_DOMAINS','X'), 'XBR02'" in r.files.get(sbl.PROPOSAL, ""),
           "labels skill: the allocation-expression PK rule renders the expression", str(r.errors))
    screen = dict(bf.BOOK_CONFIG, pk_rule={"mode": "screen", "source": "Q-10g (Label Config trace)"},
                  auth_code={"value": "44", "source": "Q-G3c"},
                  model_columns=[{"name": "FK_OWNER_OBJ", "value": "17910.4", "source": "Q-10f"}])
    r, st = sbl.evaluate(books_dir(rows=two, config=screen))
    prop = r.files.get(sbl.PROPOSAL, "")
    code_p = re.sub(r"--[^\n]*", "", prop)
    report(not r.errors and "v_pk(1) := PGT_SYS.F___SEQUENCE(TABLE_NAME => 'PGT_DOMAINS', SEQ_RANGE => '1') + v_frac" in prop
           and "FROM GOM_GLB_SYS.T__CORE_INFO_S" in prop and "IF v_auth <> 44 THEN" in prop
           and prop.index("T__CORE_INFO_S") < prop.index("v_pk(1) :=") and "WHERE PK = v_pk(1)" in prop
           and "MOD(v_pk(1), 1) <> 0.44" in prop and "VALUES (v_pk(1), 'XBR02', 'BOOK B desk', 17910.4)" in prop
           and "PGT_SYS.Pkg_SysPrecommit.p_DomainsPreCommit(PK => v_pk(1))" in prop
           and prop.index("<> 0.44") < prop.index("INSERT INTO") < prop.index("p_DomainsPreCommit(PK => v_pk(1))")
           and "COMMIT" not in code_p.replace("PreCommit", ""),
           "labels skill: 'screen' PK rule - sequence + the environment's auth code (read, checked), PK free, then insert + pre-commit",
           str(r.errors))
    report(not plsql_lint(prop), "labels proposal ('screen' rule) passes the structural lint", "; ".join(plsql_lint(prop)))
    r, _ = sbl.evaluate(books_dir(rows=two, config={k: v for k, v in screen.items() if k != "auth_code"}))
    report("book-label-auth-code" in {c for c, *_ in r.errors}, "labels skill refuses — 'screen' rule without the auth code",
           str(r.errors))
    r, _ = sbl.evaluate(books_dir(rows=(("XBR01", "BOOK_A", ""), ("XBR02", "BOOK B desk", "30001.21")),
                                  config=dict(with_rule(), auth_code={"value": "44", "source": "Q-G3c"})))
    report("book-label-pk-auth-code" in {c for c, *_ in r.errors},
           "labels skill refuses — a fixed PK without the auth code's fraction", str(r.errors))
    newdummy = dict(with_rule(), dummy={"mode": "create", "code": "BR99", "description": "BR DUMMY NEW", "pk": "30002.44",
                                        "source": "decision 3"})
    r, st = sbl.evaluate(books_dir(config=newdummy))
    report(not r.errors and st["to_create"] == ["BR99"] and "'BR99', 'BR DUMMY NEW'" in r.files.get(sbl.PROPOSAL, ""),
           "labels skill: a new dummy is proposed with the same rules", str(r.errors))
    r, st = sbl.evaluate(books_dir(config=newdummy, found=(("23958.44", "XBR01", "BOOK_A"),
                                                          ("30002.44", "BR99", "BR DUMMY NEW")), users="FK_BRANCH,COUNT(*)\n"))
    report(not r.errors and st["complete"] and st["dummy"] == "30002.44",
           "labels skill: a dummy it created is accepted once Q-10f finds it (no users yet)", str(r.errors))

    def sbl_refuses(label, code, **kw):
        d = books_dir(**{k: v for k, v in kw.items() if k != "after"})
        if kw.get("after"):
            kw["after"](d)
        r, _ = sbl.evaluate(d)
        report(code in r.codes() and sbl.PROPOSAL not in r.files, f"labels skill refuses — {label} [{code}]",
               f"got {sorted(r.codes())}")
    sbl_refuses("no book list", "book-list-missing", after=lambda d: (d / "00-books.csv").unlink())
    sbl_refuses("no configuration", "book-config-missing", after=lambda d: (d / "book-labels.json").unlink())
    sbl_refuses("no Q-10f", "evidence-missing", found=None)
    sbl_refuses("a code that breaks X<country><nn>", "book-label-code-bad", rows=(("NY001", "BOOK_A", ""),))
    sbl_refuses("a code of another country", "book-label-code-bad", rows=(("XES01", "BOOK_A", ""),))
    sbl_refuses("a code already used with another description", "book-label-conflict", rows=two, config=with_rule(),
                found=(("23958.44", "XBR01", "BOOK_A"), ("23960.44", "XBR02", "OTHER"), ("2741.44", "BR00", "BR DUMMY")))
    sbl_refuses("a description already used under another code", "book-label-conflict", rows=two, config=with_rule(),
                found=(("23958.44", "XBR01", "BOOK_A"), ("23960.44", "NY002", "BOOK B desk"), ("2741.44", "BR00", "BR DUMMY")))
    sbl_refuses("labels to create, no PK rule", "book-labels-rule-missing", rows=two)
    sbl_refuses("PK rule neither fixed nor an expression", "book-label-pk-rule", rows=two, config=with_rule(mode="auto"))
    sbl_refuses("fixed rule, a label without its PK", "book-label-pk-missing",
                rows=(("XBR01", "BOOK_A", ""), ("XBR02", "BOOK B desk", "")), config=with_rule())
    sbl_refuses("FK_OWNER_OBJ other than the Label Config object", "book-label-owner", rows=two,
                config=dict(with_rule(), model_columns=[{"name": "FK_OWNER_OBJ", "value": "35000999.65", "source": "Q-10f"}]))
    sbl_refuses("a NOT NULL column not set", "target-not-null-not-written", rows=two,
                config=dict(with_rule(), model_columns=[{"name": "FK_OWNER_OBJ", "value": "17910.4", "source": "Q-10f"}]),
                after=lambda d: (d / "01-evidence/Q-10e-domains-columns.csv").write_text(
                    (d / "01-evidence/Q-10e-domains-columns.csv").read_text() + "FK_LANG,NUMBER,22,N,N\n"))
    sbl_refuses("a dummy code longer than 5 characters", "dummy-code-too-long",
                config=dict(bf.BOOK_CONFIG, dummy={"mode": "create", "code": "BRDUMM", "description": "BR EMPTY",
                                                   "source": "decision 3"}))
    sbl_refuses("no dummy decided", "dummy-missing", config={k: v for k, v in bf.BOOK_CONFIG.items() if k != "dummy"})
    sbl_refuses("the dummy is one of the books", "dummy-is-a-book",
                config=dict(bf.BOOK_CONFIG, dummy={"mode": "existing", "code": "XBR01", "source": "decision 3"}))
    sbl_refuses("an existing dummy absent from the target", "dummy-label-not-in-target",
                found=(("23958.44", "XBR01", "BOOK_A"),))
    sbl_refuses("a dummy no other branch uses (run 6: the branch's own book)", "dummy-not-in-use",
                users="FK_BRANCH,COUNT(*)\n20007.4,6\n")
    out = subprocess.run([sys.executable, str(ROOT / "scripts/set_up_book_labels.py"), str(books_dir(rows=two, config=with_rule()))],
                         capture_output=True, text=True)
    report(out.returncode == 4 and "book-labels-PROPOSAL.sql" in out.stdout,
           "set_up_book_labels.py exits 4 and writes the proposal when labels are missing", out.stdout[-400:])

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

    # === parse_job_confs.py: db.conf + shell.conf -> jobs inventory (2026-10-01) =========================
    import csv as _csv
    env = Path(tempfile.mkdtemp()) / "env"
    env.mkdir()
    (env / "shell.conf").write_text(
        "# jobs : debug : chdir : shell script : params\n"
        "#GMM73M11:Y:data/x:ftpput.pl:FILE_$ODATE.txt\n"
        "GMGB0054D06:Y::ftpput.pl:AcctFileX.dat$ODATE AcctFileX.dat\n"
        "########## BOX - Conta General DEPOS BOOK_A ##########\n"
        "GMBX1ES45D07:Y:bin:mbjbox.sh GMBX1ES45D07 $ODATE 0000\n"
        "########## BOX - Conta General DEPOS BOOK_B ##########\n"
        "GMBOX0094D02:Y:bin:mbjbox.sh GMBOX0094D02 $ODATE 0000\n"
        "########## BOX - FE and ACC ##########\n###SLB - FRA###\n"
        "GMBX6LB03D09:Y:bin:mbjbox.sh GMBX6LB03D09 $ODATE 0000\n"
        "GMBX3ES02D07:Y:bin:mbjbox.sh GMBX3ES02D07 $ODATE 0000\n")
    (env / "db.conf").write_text(
        "########## BOX - FE and ACC ##########\n"
        "GMBX3ES02D07:T:F:PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup(2735.65, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_BRANC_MAD, "
        "to_date('$ODATE', 'YYYYMMDD'), PGT_ES.PKG_GMBATCHPROCESS.CST_PK_SWAP,\tPGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC,"
        "BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('XES02'));\n"
        "GMGB0054D01 : T : F : PGT_ES.Pkg_Locbatchdepend.f_GenMainDay(PGT_ES.PKG_GMBATCHPROCESS.CST_CIE_CFM_LON, "
        "to_char(to_date('$ODATE','YYYYMMDD'),'dd/mm/yyyy')) ;\n")
    out = subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(env)], capture_output=True, text=True)
    inv = {r["job"]: r for r in _csv.DictReader((env / "jobs-inventory.csv").open()) if r["file"] == "db.conf"
           or r["job"] != "GMBX3ES02D07"} if out.returncode == 0 else {}
    g = inv.get("GMBX3ES02D07", {})
    report(g.get("group") == "2735.65" and g.get("branch") == "CST_PK_BRANC_MAD" and g.get("instrument") == "CST_PK_SWAP"
           and g.get("mode") == "CST_PK_DINAMIC" and g.get("label") == "label:XES02" and g.get("step") == "D07"
           and g.get("token") == "ES" and g.get("instr_no") == "3" and g.get("family") == "BOX",
           "parse_job_confs: a db.conf f_ExecuteGroup line is decoded (group, branch, instrument, mode, label, name)", str(g))
    rows_all = list(_csv.DictReader((env / "jobs-inventory.csv").open())) if out.returncode == 0 else []
    both = [r for r in rows_all if r["job"] == "GMBX3ES02D07"]
    ex = {r["file"]: r["executed"] for r in both}
    report(len(both) == 2 and all(r["bound_in"] == "db.conf+shell.conf" for r in both)
           and ex == {"db.conf": "N-legacy", "shell.conf": "Y"} and "in BOTH files: 1" in out.stdout,
           "parse_job_confs: a job in both files is flagged; its shell.conf line runs, its db.conf line is legacy",
           str([r.get("bound_in") for r in both]) + out.stdout[-400:])
    s = inv.get("GMBX6LB03D09", {})
    report(s.get("entry") == "mbjbox.sh" and s.get("token") == "LB" and s.get("scope") == "product: FRA"
           and s.get("banner") == "BOX - FE and ACC / SLB - FRA" and s.get("chdir") == "bin",
           "parse_job_confs: a shell.conf mbjbox.sh line keeps its banner, token and product", str(s))
    o = inv.get("GMBOX0094D02", {})
    report(o.get("family") == "BOX" and o.get("naming") == "old-numbered" and "mbjbox.sh" in o.get("box_reason", ""),
           "parse_job_confs: an old-named BOX job (GMBOX....) is still classed BOX, and says why", str(o))
    report(inv.get("GMGB0054D01", {}).get("family") == "GBO" and inv.get("GMGB0054D06", {}).get("family") == "GBO"
           and inv.get("GMM73M11", {}).get("active") == "N",
           "parse_job_confs: GMGB jobs are GBO even under a BOX banner; a commented-out job is kept as inactive",
           str({k: inv.get(k, {}).get("family") for k in ("GMGB0054D01", "GMGB0054D06")}))

    # === find_jobs.py: list + Control-M order (2026-10-01) ===============================================
    env2 = Path(tempfile.mkdtemp()) / "env"
    env2.mkdir()
    call = ("PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup({g}, PGT_ES.PKG_GMBATCHPROCESS.{b}, to_date('$ODATE','YYYYMMDD'), "
            "PGT_ES.PKG_GMBATCHPROCESS.{i}, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC);")
    (env2 / "db.conf").write_text("\n".join([
        "GMBX1LB01D01:T:F:" + call.format(g="2628.65", b="CST_PK_BRANC_LND", i="CST_PK_DEP"),
        "GMBX1LB01D02:T:F:" + call.format(g="2629.65", b="CST_PK_BRANC_LND", i="CST_PK_DEP"),
        "GMBX1LB01D03:T:F:" + call.format(g="2630.65", b="CST_PK_BRANC_LND", i="CST_PK_DEP"),
        "GMBOX0099D01:T:F:" + call.format(g="2631.65", b="CST_PK_BRANC_LND", i="CST_PK_DEP"),
        "GMBX1ES01D01:T:F:" + call.format(g="2628.65", b="CST_PK_BRANC_MAD", i="CST_PK_DEP"),
        "GMBX1LB01D07:T:F:" + call.format(g="2407.65", b="CST_PK_BRANC_LND", i="CST_PK_DEP")]) + "\n")
    (env2 / "shell.conf").write_text("GMBX1LB01D07:Y:bin:mbjbox.sh GMBX1LB01D07 $ODATE 0000\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(env2)], capture_output=True, text=True)
    cmd = Path(tempfile.mkdtemp())
    def job(n, waits, adds):
        return {"Type": "Job:Script", "FileName": n, "FilePath": "/appl/gm/scripts", "Arguments": ["%%$ODATE"],
                "eventsToWaitFor": {"Type": "WaitForEvents", "Events": [{"Event": e} for e in waits]},
                "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": e} for e in adds]}}
    (cmd / "folder.json").write_text(json.dumps({"FOLDER_X": {"Type": "SimpleFolder",
        "GMBX0LB00D01": job("GMBX0LB00D01", ["EXT-OK"], ["GMBX0LB00D01-OK"]),
        "GMBX1LB01D01": job("GMBX1LB01D01", ["GMBX0LB00D01-OK"], ["GMBX1LB01D01-OK"]),
        "GMBX1LB01D03": job("GMBX1LB01D03", ["GMBX1LB01D02-OK"], ["GMBX1LB01D03-OK"]),
        "GMBX1LB01D02": job("GMBX1LB01D02", ["GMBX1LB01D01-OK"], ["GMBX1LB01D02-OK"])}}, indent=2))
    out = subprocess.run([sys.executable, str(ROOT / "scripts/find_jobs.py"), str(env2), "--side", "FE", "--product",
                          "deposits", "--branch", "SLB", "--controlm", str(cmd), "--out", str(env2 / "ans")],
                         capture_output=True, text=True)
    ans = list(_csv.DictReader((env2 / "ans.csv").open())) if out.returncode == 0 else []
    print(out.stdout) if "--show-find-jobs" in sys.argv else None
    order = {r["job"]: r["order"] for r in ans}
    report(order == {"GMBX1LB01D01": "1", "GMBX1LB01D02": "2", "GMBX1LB01D03": "3", "GMBOX0099D01": "-"},
           "find_jobs: FE deposits SLB = executed db.conf rows (old name found by its arguments; Madrid and the "
           "legacy ACC line left out), ordered by Control-M events", str(order) + out.stderr[-300:])
    d1 = next((r for r in ans if r["job"] == "GMBX1LB01D01"), {})
    report(d1.get("after_outside") == "GMBX0LB00D01" and d1.get("folder") == "FOLDER_X"
           and next((r for r in ans if r["job"] == "GMBOX0099D01"), {}).get("note") == "not found in the Control-M repos given",
           "find_jobs: names prerequisites outside the list, the folder, and jobs missing from Control-M", str(d1))

    # === build_fe_jobs.py: a new branch's FE jobs from a reference branch (2026-10-02) ===================
    def fe_fixture(wrapper_args=7, **over):
        root = Path(tempfile.mkdtemp())
        env, cmr, frun = root / "ref", root / "cm", root / "run/fe-jobs/depos"
        for d in (env, cmr, frun, root / "run/books"):
            d.mkdir(parents=True, exist_ok=True)
        call = ("PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup({g}, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_BRANC_LND, "
                "to_date('$ODATE','YYYYMMDD'), PGT_ES.PKG_GMBATCHPROCESS.{i}, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC{l});")
        lab = lambda b: f",BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('XLB{b}')"
        lines, jobs = ["########## BOX - FE ##########",
                       "GMBOX0114D01:T:F:" + call.format(g="2389.65", i="CST_PK_VACIO", l="")], {}
        def job(n, desc, waits=(), adds=None, frm=None):
            o = {"Type": "Job:Script", "SubApplication": "FINANCIAL_ENGINE", "FileName": n, "Host": "ref-host",
                 "FilePath": "/appl/gm/scripts", "CreatedBy": "devid0", "Description": desc, "RunAs": "gm",
                 "Application": "REF-APP", "Arguments": ["%%$ODATE"],
                 "When": dict({"WeekDays": ["NONE"], "MonthDays": ["ALL"], "MonthDaysCalendar": "REFCAL",
                               "DaysRelation": "OR"}, **({"FromTime": frm} if frm else {}))}
            if waits:
                o["eventsToWaitFor"] = {"Type": "WaitForEvents", "Events": [{"Event": w} for w in waits]}
            o["eventsToAdd"] = {"Type": "AddEvents", "Events": [{"Event": e} for e in (adds or [n + "-OK"])]}
            jobs[n] = o
        job("GMBOX0114D01", "Create Process Queues by Book BOX", frm="2200")
        for b, bd in (("14", "SLB BOOK_B"), ("15", "SLB BOOK_A")):
            for st, g, i, w in (("D01", "2628.65", "CST_PK_VACIO", ()), ("D02", "2629.65", "CST_PK_VACIO", (f"GMBX0LB{b}D01-OK",)),
                                ("D03", "2630.65", "CST_PK_VACIO", (f"GMBX0LB{b}D02-OK",))):
                lines.append(f"GMBX0LB{b}{st}:T:F:" + call.format(g=g, i=i, l=lab(b)))
                job(f"GMBX0LB{b}{st}", f"Step {st} - {bd}", w)
            lines.append(f"GMBX1LB{b}D04:T:F:" + call.format(g="2632.65", i="CST_PK_DEP", l=lab(b)))
            job(f"GMBX1LB{b}D04", f"MTM Data by book and product - {bd}", (), [f"GMBX1LB{b}D04-OK", f"G010014-GMBX1LB{b}D04-OK"])
            lines.append(f"GMBX1LB{b}D05:T:F:" + call.format(g="2631.65", i="CST_PK_DEP", l=lab(b)))
            job(f"GMBX1LB{b}D05", f"Insert BOX MM Deal Data - {bd}", (f"GMBX0LB{b}D03-OK",))
            lines.append(f"GMBX1LB{b}D06:T:F:" + call.format(g="2389.65", i="CST_PK_DEP", l=lab(b)))
            job(f"GMBX1LB{b}D06", f"Financiero - {bd}", ("GMBOX0114D01-OK", f"GMBX1LB{b}D05-OK"),
                [f"GMBX1LB{b}D06-OK", f"G010014-GMBX1LB{b}D06-OK"])
        lines.append("GMBX1LB00D08:T:F:" + call.format(g="2407.65", i="CST_PK_DEP", l=""))
        job("GMBX1LB00D08", "Branch step - SLB", ("GMBX0LB14D03-OK", "GMBX0LB15D03-OK", "GMGB4436D02-OK"))
        lines.append("GMBX1LB15D09:T:F:" + call.format(g="2407.65", i="CST_PK_DEP", l=lab("15")))
        job("GMBX1LB15D09", "Ended step - SLB BOOK_A")
        jobs["GMBX1LB15D09"]["When"]["EndDate"] = "20250512"
        (env / "db.conf").write_text("\n".join(lines) + "\n")
        subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(env)], capture_output=True, text=True)
        (cmr / "ref.json").write_text(json.dumps({"JACD-REF-BOXFE-1": dict({"Type": "SimpleFolder", "ControlmServer": "REF-SRV",
            "SiteStandard": "REF-SITE", "OrderMethod": "Manual"}, **jobs)}, indent=2))
        (root / "run/books/books-register.csv").write_text("kind,seq,code,description,pk,status,origin,evidence\n"
            "book,1,XNY01,NY BOOK ONE,1.44,exists,existing,Q-10f\nbook,2,XNY02,NY BOOK TWO,,to_create,,Q-10f\n"
            "dummy,,NYDUM,NY EMPTY,,to_create,created,x\n")
        (root / "ref-books.csv").write_text("CODE,DESCRIPTION\nXLB14,SLB BOOK_B\nXLB15,SLB BOOK_A\n")
        cfg = {"reference": {"env_folder": str(env), "controlm_json": str(cmr / "ref.json"), "token": "LB",
                             "branch_const": "CST_PK_BRANC_LND", "wrapper_owner": "PGT_ES", "display": "SLB",
                             "books_csv": str(root / "ref-books.csv"), "template_book": "15"},
               "instrument": "deposits",
               "target": {"branch_code": "NY_SCH", "token": "NY", "display": "NY", "wrapper_owner": "PGT_NY",
                          "wrapper_args": wrapper_args, "branch_const": "CST_PK_BRA_NYSCH",
                          "books_register": str(root / "run/books/books-register.csv"),
                          "constants": {"CST_PK_DEP": "CST_PK_DEP", "CST_PK_VACIO": "SAME", "CST_PK_DINAMIC": "CST_PK_DINAMIC"}},
               "controlm": {"folder_name": "JACD-NY-BOXFE-9", "ControlmServer": "T2-SRV", "SiteStandard": "T2-SITE",
                            "OrderMethod": "Manual", "Host": "t2-host", "FilePath": "/t2/scripts", "RunAs": "gm", "Application": "T2-APP",
                            "MonthDaysCalendar": "NYCAL", "CreatedBy": "omit"},
               "renames": {"GMBOX0114D01": "GMBX0NY00D01"},
               "external_events": {"GMGB4436D02-OK": "KEEP"}}
        for k, v in over.items():
            cfg[k] = v(cfg[k]) if callable(v) else v
        (frun / "fe-jobs-inputs.json").write_text(json.dumps(cfg, indent=2))
        return frun

    import build_fe_jobs as bfj
    ferun = fe_fixture()
    r = bfj.Result()
    rc = bfj.build(ferun, r)
    folder_json = json.loads((ferun / "out/JACD-NY-BOXFE-9.json").read_text()) if rc == 0 else {}
    fj = folder_json.get("JACD-NY-BOXFE-9", {})
    names = sorted(k for k, v in fj.items() if isinstance(v, dict))
    want = sorted([f"GMBX0NY{b}D0{s}" for b in ("01", "02") for s in "123"] + [f"GMBX1NY{b}D0{s}" for b in ("01", "02")
                  for s in "456"] + ["GMBX0NY00D01", "GMBX1NY00D08"])
    report(rc == 0 and names == want and fj.get("ControlmServer") == "T2-SRV",
           "build_fe_jobs: the reference chain (template book + its same-folder prerequisites) is copied once per target "
           "book, branch jobs once, old name renamed", f"rc={rc} {r.errors} {names}")
    ev = lambda j, k: [e["Event"] for e in fj.get(j, {}).get(k, {}).get("Events", [])]
    report(ev("GMBX1NY02D06", "eventsToWaitFor") == ["GMBX0NY00D01-OK", "GMBX1NY02D05-OK"]
           and ev("GMBX1NY01D04", "eventsToAdd") == ["GMBX1NY01D04-OK", "G010014-GMBX1NY01D04-OK"]
           and ev("GMBX1NY00D08", "eventsToWaitFor") == ["GMBX0NY01D03-OK", "GMBX0NY02D03-OK", "GMGB4436D02-OK"],
           "build_fe_jobs: events re-wired per book; a wait on every reference book becomes a wait on every target book; "
           "G010014- kept; a KEEP external event kept", str({j: ev(j, "eventsToWaitFor") for j in ("GMBX1NY02D06", "GMBX1NY00D08")}))
    j1 = fj.get("GMBX1NY01D04", {})
    report(j1.get("Host") == "t2-host" and j1.get("Application") == "T2-APP" and "CreatedBy" not in j1
           and j1.get("FilePath") == "/t2/scripts" and "GMBX1NY01D09" not in fj
           and j1.get("When", {}).get("MonthDaysCalendar") == "NYCAL"
           and j1.get("Description") == "MTM Data by book and product - NY BOOK ONE"
           and fj.get("GMBX1NY00D08", {}).get("Description") == "Branch step - NY",
           "build_fe_jobs: environment fields (host, path, run-as, application, calendar) from the inputs, developer ID "
           "not copied, descriptions re-booked, an ended reference job (EndDate past) not copied", str(j1))
    conf = (ferun / "out/db.conf.proposal").read_text() if rc == 0 else ""
    report("GMBX1NY02D05:T:F:PGT_NY.Pkg_GMBatchprocess.f_ExecuteGroup(2631.65, PGT_NY.PKG_GMBATCHPROCESS.CST_PK_BRA_NYSCH" in conf
           and "f_getPKByLabel('XNY02')" in conf and "PGT_ES" not in conf and "LND" not in conf and "# OPEN" not in conf,
           "build_fe_jobs: db.conf lines - job, wrapper owner, branch constant and label swapped", conf[:400])
    run5 = fe_fixture(wrapper_args=5)
    r5 = bfj.Result()
    rc5 = bfj.build(run5, r5)
    c5 = (run5 / "out/db.conf.proposal").read_text() if rc5 == 4 else ""
    report(rc5 == 4 and c5.count("# OPEN checkpoint 3") == 12 and "\nGMBX1NY00D08:" in c5,
           "build_fe_jobs: with a 5-argument target wrapper, label lines are written OPEN (exit 4), the others ready",
           f"rc={rc5} {r5.errors}")
    fb = fe_fixture()
    reg = Path(json.loads((fb / "fe-jobs-inputs.json").read_text())["target"]["books_register"])
    reg.with_name("00-books.csv").write_text("seq,label_code_proposed,label_description\n1,XNY01,NY BOOK ONE\n"
                                             "2,XNY02,NY BOOK TWO\n")
    reg.unlink()
    rb = bfj.Result()
    report(bfj.build(fb, rb) == 0 and "books-register-missing" in {c for c, *_ in rb.warns},
           "build_fe_jobs: without the books register it uses 00-books.csv, and says the labels are unchecked",
           str(rb.errors))
    for label, code, over in (
            ("an input still <...>", "input-missing", {"controlm": lambda c: dict(c, folder_name="<ask>")}),
            ("an old-named prerequisite without its new name", "rename-missing", {"renames": {}}),
            ("an external event not mapped", "external-event-unmapped", {"external_events": {}}),
            ("a wrapper constant not mapped", "constant-unmapped",
             {"target": lambda t: dict(t, constants={"CST_PK_DEP": "CST_PK_DEP"})})):
        rr = bfj.Result()
        rcx = bfj.build(fe_fixture(**over), rr)
        report(rcx == 1 and code in {c for c, *_ in rr.errors}, f"build_fe_jobs refuses — {label} [{code}]", str(rr.errors))

    # === explain_job.py + build_fe_jobs pending-questions.md (skill explain-box-job, 2026-10-06) ===========
    def dml_repo():
        d = Path(tempfile.mkdtemp()) / "cib-boxfin-dbboxfe"
        for rel, body in (
                ("r1.0.0", "Insert into PGT_PRC.T_PGT_BR_EVE_S (PK,GROUPDESCRIP,FK_OWNER_OBJ) values (2631.65,'OLD NAME',1);\n"),
                ("r1.1.0", "Insert into PGT_PRC.T_PGT_BR_EVE_S (PK,GROUPDESCRIP,FK_OWNER_OBJ) values (2631.65,'BOX MM DEAL DATA',1);\n"
                 "Insert into PGT_PRC.T_PGT_BR_EVE_EXT_S (PK,FK_PARENT,EVENTCODE,ORDERTOEXECUTE) values (1.65,2631.65,5001.65,2);\n"
                 "Insert into PGT_PRC.T_PGT_BR_EVE_EXT_S (PK,FK_PARENT,EVENTCODE,ORDERTOEXECUTE) values (2.65,2631.65,5000.65,1);\n"
                 "Insert into PGT_PRC.T_PGT_EVE_S (PK,NAME,FK_INSTRUMENT) values (5000.65,'LOAD MM DEALS',null);\n"
                 "Insert into PGT_PRC.T_PGT_EVE_S (PK,NAME,FK_INSTRUMENT) values (5001.65,'POST, MM DEALS',null);\n")):
            f = d / f"dml/03-PGT_PRC/{rel}/05_Static-Data/001-data_groupevents_263165.sql"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(body)
        return d

    pq = fe_fixture(renames={}, external_events={}, target=lambda t: dict(t, instruments=["deposits", "commodities"]))
    proot = pq.parents[2]
    pcfg = json.loads((pq / "fe-jobs-inputs.json").read_text())
    penv, pref = Path(pcfg["reference"]["env_folder"]), Path(pcfg["reference"]["controlm_json"])
    (penv / "shell.conf").write_text("GMBOX0028D01:Y:bin:mbjbox.sh GMBOX0028D01 $ODATE 0000\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(penv)], capture_output=True, text=True)
    fold = json.loads(pref.read_text())
    fj_ = fold["JACD-REF-BOXFE-1"]
    fj_["GMBX1LB00D08"]["eventsToWaitFor"]["Events"] += [{"Event": e} for e in (
        "GMBOX0028D01-OK", "GMBX3LB00D02-OK", "GMBX2LB00D02-OK", "GMBX4LB00D02-OK")]
    fj_["GMBX3LB00D02"] = {"Type": "Job:Script", "Description": "IRS branch step", "When": {"EndDate": "20240101"},
                           "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": "GMBX3LB00D02-OK"}]}}
    pref.write_text(json.dumps(fold, indent=2))
    other = proot / "cm-other"
    other.mkdir()
    def ojob(desc, sub, ev):
        return {"Type": "Job:Script", "SubApplication": sub, "Description": desc,
                "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": ev}]}}
    (other / "acc.json").write_text(json.dumps({"JACD-REF-BOXACC-1": {"Type": "SimpleFolder",
        "GMBOX0028D01": ojob("BOX Money Market Contratacion", "ACCOUNTING", "GMBOX0028D01-OK")}}, indent=2))
    (other / "fe2.json").write_text(json.dumps({"JACD-REF-BOXFE-2": {"Type": "SimpleFolder",
        "GMBX2LB00D02": ojob("Commodities branch step", "FINANCIAL_ENGINE", "GMBX2LB00D02-OK"),
        "GMBX4LB00D02": ojob("CCS branch step", "FINANCIAL_ENGINE", "GMBX4LB00D02-OK")}}, indent=2))
    pcfg = json.loads((pq / "fe-jobs-inputs.json").read_text())
    pcfg["reference"]["controlm_other"] = [str(other)]
    (pq / "fe-jobs-inputs.json").write_text(json.dumps(pcfg, indent=2))
    rp = bfj.Result()
    rcp = bfj.build(pq, rp)
    card = (pq / "pending-questions.md").read_text() if (pq / "pending-questions.md").exists() else ""
    rowp = lambda k: next((l for l in card.splitlines() if l.startswith(f"| `{k}`")), "")
    print(card) if "--show-pending" in sys.argv else None
    report(rcp == 1 and "`GMBX0NY00D01`" in rowp("GMBOX0114D01") and "Create Process Queues" in rowp("GMBOX0114D01")
           and "GMBX1LB15D06" in rowp("GMBOX0114D01"),
           "build_fe_jobs pending-questions: a missing rename shows what the job is, who waits for it and a "
           "new-convention suggestion", rowp("GMBOX0114D01") or card[:600])
    report("BOX Money Market Contratacion" in rowp("GMBOX0028D01-OK") and "ACC" in rowp("GMBOX0028D01-OK")
           and "JACD-REF-BOXACC-1" in rowp("GMBOX0028D01-OK") and "`DROP` for now" in rowp("GMBOX0028D01-OK")
           and "`GMBX2NY00D02-OK`" in rowp("GMBX2LB00D02-OK") and "`DROP` - CCS" in rowp("GMBX4LB00D02-OK")
           and "ended (EndDate 20240101)" in rowp("GMBX3LB00D02-OK") and "ask the BOX team" in rowp("GMGB4436D02-OK"),
           "build_fe_jobs pending-questions: each external event names its emitter, folder, side and a suggestion "
           "(ACC -> DROP for now; approved instrument -> target name; not approved / ended -> DROP; unknown -> ask)",
           card[-1500:])
    pcfg["renames"] = {"GMBOX0114D01": "GMBX0NY00D01"}
    pcfg["external_events"] = {e: "DROP" for e in ("GMBOX0028D01-OK", "GMBX3LB00D02-OK", "GMBX4LB00D02-OK")}
    pcfg["external_events"].update({"GMBX2LB00D02-OK": "GMBX2NY00D02-OK", "GMGB4436D02-OK": "KEEP"})
    (pq / "fe-jobs-inputs.json").write_text(json.dumps(pcfg, indent=2))
    rp2 = bfj.Result()
    rcp2 = bfj.build(pq, rp2)
    report(rcp2 == 0 and (pq / "pending-questions.md").read_text().startswith("# Pending questions\n\nNone"),
           "build_fe_jobs: once answered it builds, and pending-questions.md says none are pending", str(rp2.errors))

    dmlr = dml_repo()
    ex = subprocess.run([sys.executable, str(ROOT / "scripts/explain_job.py"), str(penv), "GMBX1LB15D05", "GMBOX0028D01",
                         "--controlm", str(pref.parent), str(other), "--dml", str(dmlr)], capture_output=True, text=True)
    print(ex.stdout) if "--show-explain" in sys.argv else None
    o = ex.stdout
    j5 = o.split("### `GMBX1LB15D05`", 1)[-1].split("### ", 1)[0]
    report(ex.returncode == 0 and "JACD-REF-BOXFE-1" in j5 and "Insert BOX MM Deal Data" in j5
           and "BOX MM DEAL DATA" in j5 and "OLD NAME" not in j5
           and j5.index("LOAD MM DEALS") < j5.index("POST, MM DEALS") and "db.conf:" in j5,
           "explain_job: an FE job - Control-M folder and waits, its executed db.conf binding, its group (newest "
           "release) and events in order from the repo DML", o[:1200] + ex.stderr[-300:])
    a28 = o.split("### `GMBOX0028D01`", 1)[-1]
    report("ACC" in a28 and "JACD-REF-BOXACC-1" in a28 and "shell.conf:" in a28 and "J-R2" in a28,
           "explain_job: an ACC job - found in the other folder repo, bound by shell.conf, group asked from J-R2",
           a28[:600])
    mbjc = proot / "mbj.csv"
    mbjc.write_text("PK,BRANCH,JOB_NAME,INSTRUMENT,GROUP_PK,GROUPDESCRIP,LABEL_CODE\n1.65,SLB,GMBOX0028D01,DEPOS,2631.65,"
                    "BOX MM DEAL DATA,XLB15\n")
    exm = subprocess.run([sys.executable, str(ROOT / "scripts/explain_job.py"), str(penv), "GMBOX0028D01", "--dml",
                          str(dmlr), "--mbj", str(mbjc)], capture_output=True, text=True)
    report(exm.returncode == 0 and "`2631.65` BOX MM DEAL DATA" in exm.stdout and "LOAD MM DEALS" in exm.stdout,
           "explain_job: with the J-R2 export, an ACC job's group and events are read", exm.stdout[:600])
    for label, code, argv_ in (("no inventory", "inventory-missing", [str(proot), "X"]),
                               ("a repo path that does not exist", "path-missing",
                                [str(penv), "X", "--controlm", str(proot / "nope")])):
        exr = subprocess.run([sys.executable, str(ROOT / "scripts/explain_job.py"), *argv_], capture_output=True, text=True)
        report(exr.returncode == 1 and code in exr.stderr, f"explain_job refuses — {label} [{code}]", exr.stderr)

    # === skills stay in sync with the code they call (2026-09-28) =======================================
    for sk in sorted((ROOT / "skills").glob("*/SKILL.md")):
        name = sk.parent.name
        if name.startswith("example-"):
            continue
        text = sk.read_text(encoding="utf-8")
        cases = list((ROOT / "evals/cases").glob(f"{name}*.md"))
        report(bool(cases), f"skill {name}: has an eval case in evals/cases/")
        links = re.findall(r"\]\((\.\./[^)#]+)", text)
        broken = [l for l in links if not (sk.parent / l).resolve().exists()]
        report(not broken, f"skill {name}: every relative link resolves", ", ".join(broken))
        scripts = sorted(set(re.findall(r"scripts/([a-z_]+\.py)", text)))
        missing = [s for s in scripts if not (ROOT / "scripts" / s).exists()]
        report(bool(scripts) and not missing, f"skill {name}: names its script(s), and they exist ({', '.join(scripts)})",
               ", ".join(missing))
        src = "".join((ROOT / "scripts" / s).read_text(encoding="utf-8") for s in scripts if s not in missing)
        codes = set(re.findall(r'res\.err\("([a-z0-9-]+)"', src))
        fm = text.split("## Failure modes", 1)[1].split("\n## ", 1)[0] if "## Failure modes" in text else ""
        named = {c for row in fm.splitlines() if row.startswith("|") and row.count("|") >= 4
                 for c in re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", row.split("|")[2])}
        unknown = sorted(named - codes)
        report(bool(named) and not unknown, f"skill {name}: every refusal code it names exists in its script(s) "
               f"({len(named)} codes)", ", ".join(unknown))
        flags = set(re.findall(r"[a-z_]+\.py [^\n`]*?(--[a-z-]+)", text))
        report(all(f"\"{f}\"" in src for f in flags), f"skill {name}: its script flags exist", ", ".join(flags))
        files = set(re.findall(r"-(P1-[A-Za-z-]+\.sql)", text)) | set(re.findall(r"(Q-P1-pk-precheck\.txt)", text)) | \
            set(re.findall(r"`(book-labels-PROPOSAL\.sql|books-register\.csv|book-labels\.json)`", text))
        report(all(f in src for f in files), f"skill {name}: the files it names are the ones its script uses",
               ", ".join(f for f in files if f not in src))

    # === run metrics (BOX Lead review, 2026-09-25) =====================================================
    out = subprocess.run([sys.executable, str(ROOT / "scripts/run_metrics.py"), str(good)], capture_output=True, text=True)
    mfile = good / "06-run-metrics.md"
    report(out.returncode == 0 and mfile.exists() and "## Effort" in mfile.read_text() and "**78**" in mfile.read_text()
           and "0 FAIL, 0 WARN" in mfile.read_text(), "run_metrics.py writes 06-run-metrics.md with effort and data counts",
           out.stdout[-800:] + out.stderr[-800:])

    print("\nall passed" if OK else "\nFAILURES")
    return 0 if OK else 1


if __name__ == "__main__":
    sys.exit(main())
