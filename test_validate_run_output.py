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
import copy, csv, json, re, shutil, subprocess, sys, tempfile
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

    with (env2 / "db.conf").open("a") as f:
        f.write("GMBOX0310D01:T:F:" + call.format(g="3001.65", b="CST_PK_BRANC_MAD", i="CST_PK_CDS") + "\n"
                "GMGB0093D01:T:F:" + call.format(g="3002.65", b="CST_PK_BRANC_MAD", i="CST_PK_CDS") + "\n"
                "GMGB1420D01:T:F:PGT_PRG.pkg_BatchDepend.F_VERIFYCURRPAIRINDEX(PGT_ES.PKG_GMBATCHPROCESS.CST_CURR_PAIR,"
                "to_date('$ODATE','YYYYMMDD'));\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(env2)], capture_output=True, text=True)
    rf = subprocess.run([sys.executable, str(ROOT / "scripts/find_jobs.py"), str(env2), "--product", "credit derivatives",
                         "--references"], capture_output=True, text=True)
    rrow = lambda b: next((x for x in rf.stdout.splitlines() if x.startswith(f"| {b} |")), "")
    report(rf.returncode == 0 and rrow("MADRID").startswith("| MADRID | ES | 1 | 0 | 1") and rrow("SLB").startswith("| SLB | LB | 0 | 0 | 0"),
           "find_jobs --references: which onboarded branch runs a product (CDS found by its db.conf constant: Madrid "
           "yes, SLB no) - the reference to use for it", rf.stdout[-500:] + rf.stderr)
    ex2 = subprocess.run([sys.executable, str(ROOT / "scripts/explain_job.py"), str(env2), "GMGB1420D01"],
                         capture_output=True, text=True)
    report("**Runs:** `PGT_PRG.pkg_BatchDepend.F_VERIFYCURRPAIRINDEX(CST_CURR_PAIR" in ex2.stdout,
           "explain_job: a job that runs no group shows its conf call (what it does, from the function name)",
           ex2.stdout[:400])

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
            ("an instrument no reference job runs (to skip)", "nothing-to-copy", {"instrument": "cds"}),
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
           and "ended (EndDate 20240101)" in rowp("GMBX3LB00D02-OK") and "ask the GBO team" in rowp("GMGB4436D02-OK"),
           "build_fe_jobs pending-questions: each external event names its emitter, folder, side and a suggestion "
           "(ACC -> DROP for now; approved instrument -> target name; not approved / ended -> DROP; GBO -> ask the GBO team)",
           card[-1500:])
    pcfg["renames"] = {"GMBOX0114D01": "GMBX0NY00D01"}
    pcfg["external_events"] = {e: "DROP" for e in ("GMBOX0028D01-OK", "GMBX3LB00D02-OK", "GMBX4LB00D02-OK")}
    pcfg["external_events"].update({"GMBX2LB00D02-OK": "GMBX2NY00D02-OK", "GMGB4436D02-OK": "KEEP"})
    (pq / "fe-jobs-inputs.json").write_text(json.dumps(pcfg, indent=2))
    rp2 = bfj.Result()
    rcp2 = bfj.build(pq, rp2)
    report(rcp2 == 0 and (pq / "pending-questions.md").read_text().startswith("# Pending questions\n\nNone"),
           "build_fe_jobs: once answered it builds, and pending-questions.md says none are pending", str(rp2.errors))

    # === build_fe_jobs: prerequisite folder (load prices) + environment descriptor (pro.json) - 2026-10-06 =====
    lp = fe_fixture(target=lambda t: dict(t, constants=dict(t["constants"], CST_PK_VACIO="SAME")))
    lroot = lp.parents[2]
    lcfg = json.loads((lp / "fe-jobs-inputs.json").read_text())
    lenv = Path(lcfg["reference"]["env_folder"])
    lcall = ("PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup({g}, PGT_ES.PKG_GMBATCHPROCESS.{b}, to_date('$ODATE','YYYYMMDD'), "
             "PGT_ES.PKG_GMBATCHPROCESS.CST_PK_VACIO, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC);")
    with (lenv / "db.conf").open("a") as f:
        f.write("#MAD LOAD PRICES\n" + "".join(f"GMBOX0026D0{k}:T:F:" + lcall.format(g=g, b="CST_PK_BRANC_MAD") + "\n"
                                              for k, g in (("1", "2385.65"), ("2", "2386.65"))) +
                "#REF LOAD PRICES\n" + "".join(f"GMBOX0026D0{k}:T:F:" + lcall.format(g=g, b="CST_PK_BRANC_LND") + "\n"
                                              for k, g in (("3", "2387.65"), ("4", "2388.65"))) +
                "GMGB1420D01:T:F:PGT_PRG.pkg_BatchDepend.F_VERIFYCURRPAIRINDEX(PGT_ES.PKG_GMBATCHPROCESS.CST_CURR_PAIR,"
                "to_date('$ODATE','YYYYMMDD'));\n")
    tenv = lroot / "tgt-env"
    tenv.mkdir()
    (tenv / "db.conf").write_text("GMNY0011D01_PR:T:F:PGT_NY.Pkg_Locbatchdepend.f_returnverificurrindex(0, "
                                  "to_date('$ODATE','YYYYMMDD'), 20007.4);\nGMNY0020D01_PR:T:F:PGT_NY.Pkg_Locbatch."
                                  "f_loadbookpositions(0, to_date('$ODATE','YYYYMMDD'));\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(tenv)], capture_output=True, text=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(lenv)], capture_output=True, text=True)
    lrepo = lroot / "cib-loadprices" / "projects"
    lrepo.mkdir(parents=True)
    def lpjob(n, desc, waits=()):
        o = {"Type": "Job:Script", "SubApplication": "FINANCIAL_ENGINE", "FileName": n, "Host": "ref-host",
             "FilePath": "/appl/gm/scripts", "CreatedBy": "devid0", "Description": desc, "RunAs": "gm",
             "Application": "REF-APP", "When": {"MonthDaysCalendar": "REFCAL"},
             "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": n + "-OK"}]}}
        if waits:
            o["eventsToWaitFor"] = {"Type": "WaitForEvents", "Events": [{"Event": w} for w in waits]}
        return o
    (lrepo / "loadprices.json").write_text(json.dumps({"JACD-REF-LOADPRICES-1": {
        "Type": "SimpleFolder", "ControlmServer": "REF-SRV", "SiteStandard": "REF-SITE", "OrderMethod": "Manual",
        "GMBOX0026D01": lpjob("GMBOX0026D01", "Captura curvas fixing - Madrid"),
        "GMBOX0026D02": lpjob("GMBOX0026D02", "Captura datos mercado - Madrid", ["GMBOX0026D01-OK"]),
        "GMBOX0026D03": lpjob("GMBOX0026D03", "Captura curvas fixing - SLB"),
        "GMBOX0026D04": lpjob("GMBOX0026D04", "Captura datos mercado - SLB", ["GMBOX0026D03-OK"])}}, indent=2))
    ddir = lroot / "cnfgsrvc" / "ref-fe"
    ddir.mkdir(parents=True)
    def dadd(job, events):
        return {"Comment": "Add PRO prerequisitos", "Add": {"Path": f"$.JACD-REF-BOXFE-1.{job}",
                "propertyName": "eventsToWaitFor", "propertyValue": {"Type": "WaitForEvents",
                "Events": [{"Event": e} for e in events]}}}
    (ddir / "pro.json").write_text(json.dumps({"DeployDescriptor": [
        {"Comment": "site standard per env", "Property": "SiteStandard", "Replace": [{"(.*)_D_(.*)": "$1_P_$2"}]},
        dadd("GMBOX0114D01", ["GMGB1420D01-OK", "GMBOX0026D04-OK"]),
        dadd("GMBX3LB00D01", ["GMGB1420D01-OK", "GMBOX0026D04-OK"]),
        dadd("GMBX1LB14D05", ["G010012-PAUKIREFBOOK-OK"]),
        dadd("GMBX0LB15D01", ["G010012-PAUKISCIBDDSLBBOOKA001D-OK"]),
        dadd("GMBX0LB14D01", ["G010012-PAUKISCIBDDSLBBOOKB001D-OK"]),
        {"Comment": "host", "Property": "Host", "Replace": [{"ref-host": "ref-host-pro"}]}]}, indent=2))
    def dljob(name, book, ctry):
        arg = '{\\"country_code_vr\\":\\"' + ctry + '\\", \\"book_vr\\":\\"' + book + '\\", \\"book_aux\\":\\"BOOK\\"}'
        return {"Type": "Job:Script", "CreatedBy": "devid9", "Arguments": ["auki_bo_sql_generic", "AUKI_DEAL_DATA", arg],
                "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": name + "-OK"}, {"Event": "G010012-" + name + "-OK"}]}}
    dlr, dlt = lroot / "dl" / "ref.json", lroot / "dl" / "ny.json"
    dlr.parent.mkdir()
    dlr.write_text(json.dumps({"DL-REF": {"Type": "SimpleFolder",
        "PAUKISCIBDDSLBBOOKA001D": dljob("PAUKISCIBDDSLBBOOKA001D", "SLB BOOK_A", "LB"),
        "PAUKISCIBDDSLBBOOKAOTC001D": dljob("PAUKISCIBDDSLBBOOKAOTC001D", "SLB BOOK_A", "LB"),
        "PAUKISCIBDDSLBBOOKB001D": dljob("PAUKISCIBDDSLBBOOKB001D", "SLB BOOK_B", "LB")}}, indent=2))
    dlt.write_text(json.dumps({"DL-NY": {"Type": "SimpleFolder",
        "PAUKISCIBDDNYBOOKONE001D": dljob("PAUKISCIBDDNYBOOKONE001D", "NY BOOK ONE", "NY"),
        "PAUKISCIBDDNYBOOKONEOTC001D": dljob("PAUKISCIBDDNYBOOKONEOTC001D", "NY BOOK ONE", "NY"),
        "PAUKISCIBFDNYBOOK2001D": dljob("PAUKISCIBFDNYBOOK2001D", "NY BOOK 2", "NY"),
        "PAUKISCIBDDNYBOOK2001D": dljob("PAUKISCIBDDNYBOOK2001D", "NY BOOK 2", "NY")}}, indent=2))
    lcfg["datalake"] = {"reference_json": [str(dlr)], "target_json": [str(dlt)]}
    lcfg["target"]["env_folder"] = str(tenv)
    lcfg["reference"]["descriptor_dir"] = str(ddir)
    lcfg["prerequisites"] = [{"controlm_json": str(lrepo / "loadprices.json"), "folder_name": "JACD-NY-LOADPRICES-9"}]
    (lp / "fe-jobs-inputs.json").write_text(json.dumps(lcfg, indent=2))
    rl = bfj.Result()
    rcl = bfj.build(lp, rl)
    lcard = (lp / "pending-questions.md").read_text() if (lp / "pending-questions.md").exists() else ""
    print(lcard) if "--show-pending" in sys.argv else None
    report(rcl == 1 and "target-name-duplicate" in {c for c, *_ in rl.errors} and "external-event-unmapped" in
           {c for c, *_ in rl.errors} and "`GMBOX0114D01` → `GMBX0NY00D03`" in lcard and "GMGB1420D01-OK" in lcard
           and "GMBX1LB14D05" not in lcard and "PAUKISCIBDDSLBBOOKA" not in lcard.split("## Data Lake")[0],
           "build_fe_jobs prerequisites: load-price jobs take GMBX0<TT>00D01/D02; a rename on the same name is refused "
           "with the next free name; a descriptor (PRO) wait on a GBO event is asked", str(rl.errors) + lcard[:800])
    rowl = lambda k: next((x for x in lcard.splitlines() if x.startswith(f"| `{k}`")), "")
    report("datalake-book-unmapped" in {c for c, *_ in rl.errors} and "`XNY01`" not in lcard
           and "`NY BOOK 2`" in rowl("XNY02") and "F_VERIFYCURRPAIRINDEX" in rowl("GMGB1420D01-OK")
           and "GMNY0011D01_PR" in rowl("GMGB1420D01-OK") and "GMNY0020D01_PR" not in rowl("GMGB1420D01-OK"),
           "build_fe_jobs pending: a target book with no Data Lake job under its description is asked with the closest "
           "Data Lake books; a GBO wait shows what the job runs and the target's look-alike job (INFERRED)",
           rowl("XNY02") + " || " + rowl("GMGB1420D01-OK"))
    lcfg["datalake"]["book_map"] = {"XNY02": "NY BOOK 2"}
    lcfg["renames"] = {"GMBOX0114D01": "GMBX0NY00D03"}
    lcfg["external_events"] = {"GMGB4436D02-OK": "KEEP", "GMGB1420D01-OK": "KEEP"}
    (lp / "fe-jobs-inputs.json").write_text(json.dumps(lcfg, indent=2))
    rl2 = bfj.Result()
    rcl2 = bfj.build(lp, rl2)
    lo = lp / "out"
    lpf = json.loads((lo / "JACD-NY-LOADPRICES-9.json").read_text()).get("JACD-NY-LOADPRICES-9", {}) if rcl2 == 0 else {}
    lfe = json.loads((lo / "JACD-NY-BOXFE-9.json").read_text()).get("JACD-NY-BOXFE-9", {}) if rcl2 == 0 else {}
    report(rcl2 == 0 and sorted(k for k, v in lpf.items() if isinstance(v, dict)) == ["GMBX0NY00D01", "GMBX0NY00D02"]
           and lpf["GMBX0NY00D01"]["Description"] == "Captura curvas fixing - NY"
           and [e["Event"] for e in lpf["GMBX0NY00D02"]["eventsToWaitFor"]["Events"]] == ["GMBX0NY00D01-OK"]
           and lpf["GMBX0NY00D02"]["Host"] == "t2-host" and "CreatedBy" not in lpf["GMBX0NY00D02"]
           and lpf.get("ControlmServer") == "T2-SRV" and "GMBX0NY00D03" in lfe
           and "eventsToWaitFor" not in lfe["GMBX0NY00D03"],
           "build_fe_jobs prerequisites: a second folder with only the reference branch's load-price jobs (the other "
           "branch's left out), renamed, re-hosted, re-described; the FE folder file keeps no PRO-only wait",
           f"rc={rcl2} {rl2.errors} {sorted(lpf)}")
    lconf = (lo / "db.conf.proposal").read_text() if rcl2 == 0 else ""
    report(lconf.index("JACD-NY-LOADPRICES-9") < lconf.index("GMBX0NY00D01:") < lconf.index("- FE - depos")
           and "GMBX0NY00D02:T:F:PGT_NY.Pkg_GMBatchprocess.f_ExecuteGroup(2388.65, PGT_NY.PKG_GMBATCHPROCESS.CST_PK_BRA_NYSCH"
           in lconf and "2385.65" not in lconf if rcl2 == 0 else False,
           "build_fe_jobs prerequisites: their db.conf lines first, under their own banner, swapped like the FE lines",
           lconf[:500])
    dpro = json.loads((lo / "descriptors/JACD-NY-BOXFE-9/pro.json").read_text())["DeployDescriptor"] \
        if (lo / "descriptors/JACD-NY-BOXFE-9/pro.json").exists() else []
    lrep = (lo / "report.md").read_text() if rcl2 == 0 else ""
    paths_ = [d.get("Add", {}).get("Path") for d in dpro]
    q114 = next((d for d in dpro if d.get("Add", {}).get("Path") == "$.JACD-NY-BOXFE-9.GMBX0NY00D03"), {})
    report(dpro and dpro[0].get("Property") == "SiteStandard" and "$.JACD-NY-BOXFE-9.GMBX0NY00D03" in paths_
           and [e["Event"] for e in q114["Add"]["propertyValue"]["Events"]] == ["GMGB1420D01-OK", "GMBX0NY00D02-OK"]
           and not any("GMBX3" in str(x) for x in paths_) and not any(d.get("Property") == "Host" for d in dpro)
           and "GMBX3LB00D01" in lrep and "only reference book 14 gets it" in lrep and "carries the reference value `ref-host`" in lrep,
           "build_fe_jobs descriptors: the reference pro.json re-pointed to the target folder and jobs (load-price wait "
           "renamed); other instruments' entries listed, a one-book entry and a host value sent to review",
           json.dumps(dpro)[:600] + lrep[-700:])
    w01 = lambda b: next((d for d in dpro if d.get("Add", {}).get("Path") == f"$.JACD-NY-BOXFE-9.GMBX0NY{b}D01"), {})
    evs = lambda d: [e["Event"] for e in d.get("Add", {}).get("propertyValue", {}).get("Events", [])]
    report(evs(w01("01")) == ["G010012-PAUKISCIBDDNYBOOKONE001D-OK"] and evs(w01("02")) == ["G010012-PAUKISCIBDDNYBOOK2001D-OK"]
           and "GMBX0LB14D01 (book 14: as the template book's)" in lrep and "Data Lake waits" in lrep,
           "build_fe_jobs Data Lake: each target book's step waits for its own Data Lake job (same type, book label = "
           "book_vr, book_map override); the other reference books' entries are covered by the template book's",
           json.dumps([w01("01"), w01("02")])[:500] + lrep[-600:])
    with (tenv / "db.conf").open("a") as f:
        f.write("GMBX0NY00D02:T:F:PGT_NY.Pkg_X.f_Y(0);\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(tenv)], capture_output=True, text=True)
    rl4 = bfj.Result()
    report(bfj.build(lp, rl4) == 1 and any(c == "target-name-exists" and "target environment" in m for c, _, m in rl4.errors),
           "build_fe_jobs refuses — a generated name already used in the target environment's job confs "
           "[target-name-exists]", str(rl4.errors))
    lcfg["reference"].pop("descriptor_dir")
    (lp / "fe-jobs-inputs.json").write_text(json.dumps(lcfg, indent=2))
    rl3 = bfj.Result()
    report(bfj.build(lp, rl3) == 1 and "prerequisite-not-linked" in {c for c, *_ in rl3.errors},
           "build_fe_jobs refuses — a prerequisite folder no copied job waits for [prerequisite-not-linked]",
           str(rl3.errors))

    # === build_fe_jobs: BOX expert review fixes (2026-10-07) ====================================================
    # instrument scope: another instrument's job is not copied, its waits are inherited; OR-groups merged; -NOK renamed
    sx = fe_fixture(target=lambda t: dict(t, wrapper_args=5, dbconf_format="pgt_prg", branch_pk="20007.4",
                                          constant_values={"CST_PK_DINAMIC": "0", "CST_PK_VACIO": "0"}))
    sxc = json.loads((sx / "fe-jobs-inputs.json").read_text())
    sxf = Path(sxc["reference"]["controlm_json"])
    fold = json.loads(sxf.read_text())
    fx = fold["JACD-REF-BOXFE-1"]
    for n, desc in (("6", "FRA merge - SLB BOOK_A"), ("7", "Merge Deal Data and Flow data for OTC BOX - SLB BOOK_A")):
        fx[f"GMBX{n}LB15D11"] = {"Type": "Job:Script", "FileName": f"GMBX{n}LB15D11", "Description": desc,
            "IfBase:Folder:CompletionStatus_0": {"Type": "If:CompletionStatus", "CompletionStatus": "NOTOK",
                "Event:Add_0": {"Type": "Event:Add", "Event": f"GMBX{n}LB15D11-NOK"}},
            "eventsToWaitFor": {"Type": "WaitForEvents", "Events": [{"Event": "GMBX0LB15D02-OK"}]},
            "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": f"GMBX{n}LB15D11-OK"}]}}
    or_waits = []
    for a, b in (("OK", "OK"), ("OK", "NOK"), ("NOK", "OK"), ("NOK", "NOK")):
        or_waits += (["OR"] if or_waits else []) + [{"Event": f"GMBX6LB15D11-{a}"}, {"Event": f"GMBX7LB15D11-{b}"}]
    fx["GMBX0LB15D03"]["eventsToWaitFor"]["Events"] = or_waits
    fx["GMBX1LB15D05"]["IfBase:Folder:CompletionStatus_0"] = {"Type": "If:CompletionStatus", "CompletionStatus": "NOTOK",
        "Event:Add_0": {"Type": "Event:Add", "Event": "GMBX1LB15D05-NOK"}}
    sxf.write_text(json.dumps(fold, indent=2))
    rx = bfj.Result()
    rcx = bfj.build(sx, rx)
    xf = json.loads((sx / "out/JACD-NY-BOXFE-9.json").read_text()).get("JACD-NY-BOXFE-9", {}) if rcx == 0 else {}
    xrep = (sx / "out/report.md").read_text() if rcx == 0 else ""
    report(rcx == 0 and not any(k.startswith(("GMBX6", "GMBX7")) for k in xf)
           and xf["GMBX0NY01D03"]["eventsToWaitFor"]["Events"] == [{"Event": "GMBX0NY01D02-OK"}]
           and xf["GMBX0NY02D03"]["eventsToWaitFor"]["Events"] == [{"Event": "GMBX0NY02D02-OK"}]
           and "`GMBX7LB15D11` (OTC option)" in xrep and "GMBX0LB15D03" in xrep,
           "build_fe_jobs scope: another instrument's jobs (GMBX6/7 D11) are not copied; a wait on them is replaced by "
           "their own waits and the four OR-groups collapse to one wait (D03 -> D02)",
           f"rc={rcx} {rx.errors} " + json.dumps(xf.get("GMBX0NY01D03", {}).get("eventsToWaitFor")))
    nok = xf.get("GMBX1NY02D05", {}).get("IfBase:Folder:CompletionStatus_0", {}).get("Event:Add_0", {}).get("Event")
    report(nok == "GMBX1NY02D05-NOK" and "LB" not in json.dumps(xf),
           "build_fe_jobs: events in If:CompletionStatus -> Event:Add blocks are renamed too (-NOK), nothing of the "
           "reference token left in the folder", str(nok))
    xconf = (sx / "out/db.conf.proposal").read_text() if rcx == 0 else ""
    tm = "to_char(sysdate,'RRRR-mm-DD HH24:MI:SS')"
    core = lambda rest: "T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(" + rest + ");"
    report(rcx == 0 and "GMBX1NY02D05:" + core(f"2631.65, 20007.4, to_date('$ODATE','YYYYMMDD'), PGT_NY.PKG_GMBATCHPROCESS."
           f"CST_PK_DEP, {tm}, 0, BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('XNY02'), NULL") in xconf
           and "GMBX0NY01D01:" + core(f"2628.65, 20007.4, to_date('$ODATE','YYYYMMDD'), NULL, {tm}, 0, "
                                       "BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('XNY01'), NULL") in xconf
           and "GMBX1NY00D08:" + core(f"2407.65, 20007.4, to_date('$ODATE','YYYYMMDD'), PGT_NY.PKG_GMBATCHPROCESS."
                                       f"CST_PK_DEP, {tm}, 0, NULL, NULL") in xconf
           and "# OPEN" not in xconf and ":T:F:" not in xconf and "f_ExecuteGroup" not in xconf
           and "CST_PK_VACIO" not in xconf and "branch PK `20007.4` on every line" in xrep,
           "build_fe_jobs dbconf_format pgt_prg: every line is the core call as Mexico's with the BOX job expert's "
           "corrections - branch PK on every line (per-book too), CST_PK_VACIO -> NULL, time = to_char(sysdate, ...), "
           "vstatic by value, label in place (NULL at branch level); no OPEN line with a 5-argument wrapper",
           xconf[:700])
    rbp_ = bfj.Result()
    report(bfj.build(fe_fixture(target=lambda t: dict(t, dbconf_format="pgt_prg")), rbp_) == 1
           and any(w.endswith("target.branch_pk") for c, w, _ in rbp_.errors),
           "build_fe_jobs refuses — core call without the target branch PK [input-missing target.branch_pk]",
           str(rbp_.errors))
    (sx.parent / "instrument-plan.csv").write_text("instrument,status,reference,reason,source\ndepos,in progress,SLB,,t\n"
                                                    "otc,built,SLB,,t\nfra,to build,,,t\n")
    rx2 = bfj.Result()
    rcx2 = bfj.build(sx, rx2)
    xf2 = json.loads((sx / "out/JACD-NY-BOXFE-9.json").read_text()).get("JACD-NY-BOXFE-9", {}) if rcx2 == 0 else {}
    w2 = [e if isinstance(e, str) else e["Event"] for e in xf2.get("GMBX0NY01D03", {}).get("eventsToWaitFor", {})
          .get("Events", [])]
    report(rcx2 == 0 and w2 == ["GMBX0NY01D02-OK", "GMBX7NY01D11-OK", "OR", "GMBX0NY01D02-OK", "GMBX7NY01D11-NOK"]
           and "GMBX7NY01D11" not in xf2,
           "build_fe_jobs scope: an instrument already built (instrument-plan.csv) keeps its wait, renamed to the "
           "target's job; the one not built is inherited; duplicate OR-groups merged", f"rc={rcx2} {rx2.errors} {w2}")
    # several instruments in one run + Initial Accounting jobs + hand-off + job_unix.sh (2026-10-08)
    mx = fe_fixture(instrument=["depos", "otc"],
                    target=lambda t: dict(t, dbconf_format="pgt_prg", branch_pk="20007.4",
                                          constant_values={"CST_PK_DINAMIC": "0", "CST_PK_VACIO": "0"},
                                          constants=dict(t["constants"], CST_PK_OTC="CST_PK_OTC", CST_PK_SWAP="SAME")),
                    controlm=lambda c: dict(c, FilePath="/gmny/scripts"))
    mcfg = json.loads((mx / "fe-jobs-inputs.json").read_text())
    menv, mref = Path(mcfg["reference"]["env_folder"]), Path(mcfg["reference"]["controlm_json"])
    ia_call = ("PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup(2409.65, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_BRANC_LND, "
               "to_date('$ODATE','YYYYMMDD'), PGT_ES.PKG_GMBATCHPROCESS.{i}, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC);")
    with (menv / "db.conf").open("a") as f:
        f.write("GMBX7LB15D11:T:F:PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup(2700.65, PGT_ES.PKG_GMBATCHPROCESS."
                "CST_PK_BRANC_LND, to_date('$ODATE','YYYYMMDD'), PGT_ES.PKG_GMBATCHPROCESS.CST_PK_OTC, "
                "PGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC,BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('XLB15'));\n"
                + "".join(f"{j}:T:F:" + ia_call.format(i=i) + "\n" for j, i in (
                    ("GMBOX0028D01", "CST_PK_DEP"), ("GMBX3LB00D02", "CST_PK_SWAP"), ("GMBX7LB00D02", "CST_PK_OTC"))))
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(menv)], capture_output=True, text=True)
    fold = json.loads(mref.read_text())
    fm = fold["JACD-REF-BOXFE-1"]
    for n, desc in (("6", "FRA merge - SLB BOOK_A"), ("7", "Merge Deal Data and Flow data for OTC BOX - SLB BOOK_A")):
        fm[f"GMBX{n}LB15D11"] = {"Type": "Job:Script", "FileName": f"GMBX{n}LB15D11", "Description": desc,
            "eventsToWaitFor": {"Type": "WaitForEvents", "Events": [{"Event": "GMBX0LB15D02-OK"}]},
            "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": f"GMBX{n}LB15D11-OK"}]}}
    fm["GMBX0LB15D03"]["eventsToWaitFor"]["Events"] = [{"Event": "GMBX6LB15D11-OK"}, {"Event": "GMBX7LB15D11-OK"}]
    fm["GMBX0LB15D02"]["eventsToWaitFor"]["Events"] += [{"Event": e} for e in (
        "GMBOX0028D01-OK", "GMBX3LB00D02-OK", "GMBX7LB00D02-OK")]
    mref.write_text(json.dumps(fold, indent=2))
    macc = mx.parents[2] / "acc-repo"
    macc.mkdir()
    def iajob(n, d):
        return {"Type": "Job:Script", "SubApplication": "ACCOUNTING", "FileName": n, "Host": "ref-host", "RunAs": "gm",
                "FilePath": "/appl/gm/scripts", "CreatedBy": "devid0", "Application": "REF-ACC-APP",
                "Description": f"BOX - Initial accounting (PP, Recla, Reval) - {d}",
                "When": {"MonthDaysCalendar": "REFCAL", "FromTime": "2330"},
                "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": f"{n}-OK"}, {"Event": f"G010014-{n}-OK"},
                                                                {"Event": f"G010012-{n}-OK"}]}}
    (macc / "acc.json").write_text(json.dumps({"JACD-REF-BOXACC-1": {"Type": "SimpleFolder",
        "GMBOX0028D01": iajob("GMBOX0028D01", "MM"), "GMBX7LB00D02": iajob("GMBX7LB00D02", "OTC")}}, indent=2))
    mcfg = json.loads((mx / "fe-jobs-inputs.json").read_text())
    mcfg["reference"]["controlm_other"] = [str(macc)]
    mcfg["initial_accounting"] = {"group": "2409.65", "name": "BOX - Initial accounting (PP, Recla, Reval)"}
    mcfg["acc"] = {"folder_name": "JACD-NY-BOXACC-9", "Application": "T2-ACC-APP"}
    mcfg["unix"] = {"etc_dir": "/gmny/etc"}
    (menv / "unix").mkdir()
    (menv / "unix/delete_jobsBX.ksh").write_text("#!/bin/ksh\n\n#by SOMEONE x000000\n\ncd /appl/gm/etc\n\n"
                                                  "CONF_FILE=`echo $1`\necho done >> evidencias.log\nexit 0\n")
    (mx / "fe-jobs-inputs.json").write_text(json.dumps(mcfg, indent=2))
    rm = bfj.Result()
    rcm = bfj.build(mx, rm)
    mo = mx / "out"
    mf = json.loads((mo / "JACD-NY-BOXFE-9.json").read_text())["JACD-NY-BOXFE-9"] if rcm == 0 else {}
    mw = lambda j: [e["Event"] for e in mf.get(j, {}).get("eventsToWaitFor", {}).get("Events", [])]
    report(rcm == 0 and "GMBX7NY01D11" in mf and "GMBX7NY02D11" in mf and "GMBX1NY01D05" in mf
           and not any(k.startswith("GMBX6") for k in mf)
           and mw("GMBX0NY01D03") == ["GMBX0NY01D02-OK", "GMBX7NY01D11-OK"]
           and mw("GMBX0NY02D02") == ["GMBX0NY02D01-OK", "GMBX1NY00D02-OK", "GMBX7NY00D02-OK"],
           "build_fe_jobs several instruments: one FE folder with both chains, shared jobs once, waits between the "
           "run's instruments kept (OTC D11), FRA inherited; D02 waits for the run's Initial Accounting jobs (IRS's, "
           "not built, dropped)", f"rc={rcm} {rm.errors} {mw('GMBX0NY02D02')} {mw('GMBX0NY01D03')}")
    mconf = (mo / "db.conf.proposal").read_text() if rcm == 0 else ""
    tm_ = "to_char(sysdate,'RRRR-mm-DD HH24:MI:SS')"
    report(rcm == 0 and f"GMBX1NY00D02:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(2409.65, 20007.4, to_date('$ODATE',"
           f"'YYYYMMDD'), PGT_NY.PKG_GMBATCHPROCESS.CST_PK_DEP, {tm_}, 0, NULL, NULL);" in mconf
           and "GMBX7NY00D02:T:P:" in mconf and "GMBX3NY00D02" not in mconf
           and mconf.index("Initial accounting") < mconf.index("- FE - depos") < mconf.index("- FE - otc")
           and mconf.count("\nGMBX0NY01D02:") == 1,
           "build_fe_jobs Initial Accounting: one db.conf core line per instrument built (group 2409.65), under its own "
           "banner before the FE lines; a shared line written once", mconf[:900])
    mh = json.loads((mo / "acc-handoff.json").read_text())["initial_accounting"] if rcm == 0 else []
    h1 = next((h for h in mh if h["target_job"] == "GMBX1NY00D02"), {})
    report(rcm == 0 and sorted(h["target_job"] for h in mh) == ["GMBX1NY00D02", "GMBX7NY00D02"]
           and h1.get("emits") == ["GMBX1NY00D02-OK", "G010014-GMBX1NY00D02-OK", "G010012-GMBX1NY00D02-OK"]
           and h1.get("waited_by") == ["GMBX0NY01D02", "GMBX0NY02D02"] and h1["acc_folder"] == "JACD-NY-BOXACC-9"
           and h1["draft_job"]["Application"] == "T2-ACC-APP" and h1["draft_job"]["Host"] == "t2-host"
           and "CreatedBy" not in h1["draft_job"] and h1["draft_job"]["When"]["FromTime"] == "2330"
           and "GMBOX0028D01" not in json.dumps(h1["draft_job"]),
           "build_fe_jobs hand-off: acc-handoff.json - per Initial Accounting job its db.conf line, who waits, the "
           "events it emits (prefixes kept) and a draft ACC job (target values, no developer ID)", json.dumps(h1)[:900])
    mu = (mo / "unix/job_unix.sh").read_text() if (mo / "unix/job_unix.sh").exists() else ""
    mdel = (mo / "unix/db_delete.txt").read_text().splitlines() if (mo / "unix/db_delete.txt").exists() else []
    mks = (mo / "unix/delete_jobsBX.ksh").read_text() if (mo / "unix/delete_jobsBX.ksh").exists() else ""
    report(mu.startswith("sh -x /gmny/etc/delete_jobsBX.ksh  db.conf /gmny/etc/db_delete.txt\n"
                         "sh -x /gmny/etc/add_new_jobs.ksh db.conf /gmny/etc/db_nuevo.conf\n")
           and "cp /gmny/scripts/templates/db_job /gmny/scripts/GMBX1NY00D02" in mu
           and "chmod 755 /gmny/scripts/GMBX7NY02D11" in mu and "shell_job" not in mu and "#!" not in mu
           and mu.count("cp /gmny/scripts/templates/db_job") == mu.count("chmod 755") == mconf.count(":T:P:")
           and (mo / "unix/db_nuevo.conf").read_text() == mconf
           and "GMBX1NY00D02" in mdel and any(x.startswith("##########") for x in mdel)
           and len([x for x in mdel if x.startswith("GMBX")]) == mconf.count(":T:P:")
           and "cd /gmny/etc" in mks and "/appl/gm/etc" not in mks and "#by" not in mks
           and "unix-script-missing" in {c for c, *_ in rm.warns},
           "unix_package: out/unix/ as the Tier 1 CDS package - job_unix.sh (delete_jobsBX + add_new_jobs on db.conf, "
           "then cp db_job + chmod 755 per job), db_nuevo.conf = the proposal, db_delete.txt = its jobs and banners, "
           "the target's delete_jobsBX.ksh (etc folder replaced, author line out); a reference script missing is said",
           mu[:400] + " || " + mks[:200])
    mcfg2 = json.loads((mx / "fe-jobs-inputs.json").read_text())
    mcfg2["controlm"]["target_repo"] = "cib-boxfin-t2xxfe"
    (mx / "fe-jobs-inputs.json").write_text(json.dumps(mcfg2, indent=2))
    clone = mx.parents[2] / "clone-t2xxfe"
    (clone / "projects").mkdir(parents=True)
    (clone / "projects/cib-boxfin-t2xxfe.json").write_text(json.dumps({"JACD-NY-BOXFE-9": {
        "Type": "SimpleFolder", "GMBX0NY01D01": mf.get("GMBX0NY01D01", {}), "GMBXOLD": {"Type": "Job:Script"}}}))
    sp = subprocess.run([sys.executable, str(ROOT / "scripts/stage_target_pr.py"), str(mx), "--checkout",
                         f"cib-boxfin-t2xxfe={clone}"], capture_output=True, text=True)
    staged = mo / "pr/cib-boxfin-t2xxfe/projects/cib-boxfin-t2xxfe.json"
    report(sp.returncode == 0 and staged.exists() and staged.read_text() == (mo / "JACD-NY-BOXFE-9.json").read_text()
           and "1 removed" in sp.stdout and "yes / no" in sp.stdout and (mo / "JACD-NY-BOXFE-9.json").exists(),
           "stage_target_pr: out/pr/<repo>/projects/<repo>.json = the folder JSON renamed (out/ untouched) and a "
           "summary vs the repo's current file for the operator's yes / no", sp.stdout[-500:] + sp.stderr[-300:])
    mcfg2["controlm"].pop("target_repo")
    (mx / "fe-jobs-inputs.json").write_text(json.dumps(mcfg2, indent=2))
    with (menv / "db.conf").open("a") as f:
        f.write("GMBX1LB15D99:T:F:PGT_ES.X.f_y(1);\n")
    mcfg["unix"] = {}
    (mx / "fe-jobs-inputs.json").write_text(json.dumps(mcfg, indent=2))
    rm2 = bfj.Result()
    bfj.build(mx, rm2)
    mu2 = (mo / "unix/job_unix.sh").read_text()
    report("# OPEN - the etc folder is not given: sh -x <etc>/delete_jobsBX.ksh" in mu2
           and "unix-etc-missing" in {c for c, *_ in rm2.warns},
           "unix_package: without the etc folder the add_new_jobs line is written commented OPEN (warning)", mu2[:300])

    # excluded books, old-named per-book jobs of other reference books, DROP-REVIEW, template book per instrument
    ex = fe_fixture(external_events={"GMGB4436D02-OK": "DROP-REVIEW"},
                    reference=lambda r: dict(r, template_book={"depos": "15"}))
    exc = json.loads((ex / "fe-jobs-inputs.json").read_text())
    eenv, eref = Path(exc["reference"]["env_folder"]), Path(exc["reference"]["controlm_json"])
    with (eenv / "db.conf").open("a") as f:
        f.write("GMBOX0031D03:T:F:PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup(2630.65, PGT_ES.PKG_GMBATCHPROCESS."
                "CST_PK_BRANC_LND, to_date('$ODATE','YYYYMMDD'), PGT_ES.PKG_GMBATCHPROCESS.CST_PK_VACIO, "
                "PGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC,BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('XLB03'));\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(eenv)], capture_output=True, text=True)
    fold = json.loads(eref.read_text())
    fe_ = fold["JACD-REF-BOXFE-1"]
    fe_["GMBOX0031D03"] = {"Type": "Job:Script", "FileName": "GMBOX0031D03", "Description": "Update current values - SLB X",
                           "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": "GMBOX0031D03-OK"}]}}
    fe_["GMBX1LB00D08"]["eventsToWaitFor"]["Events"].insert(0, {"Event": "GMBOX0031D03-OK"})
    eref.write_text(json.dumps(fold, indent=2))
    reg_ = Path(exc["target"]["books_register"])
    (reg_.parent / "books-excluded.csv").write_text("code,description,scope,reason,source,date\n"
                                                     "XNY02,NY BOOK TWO,jobs,no Data Lake book,operator,2026-10-08\n")
    rx_ = bfj.Result()
    rcx_ = bfj.build(ex, rx_)
    xf_ = json.loads((ex / "out/JACD-NY-BOXFE-9.json").read_text())["JACD-NY-BOXFE-9"] if rcx_ == 0 else {}
    xr_ = (ex / "out/report.md").read_text() if rcx_ == 0 else ""
    w8 = [e["Event"] for e in xf_.get("GMBX1NY00D08", {}).get("eventsToWaitFor", {}).get("Events", [])]
    report(rcx_ == 0 and not any("NY02" in k for k in xf_) and w8 == ["GMBX0NY01D03-OK"]
           and "books excluded" in xr_ and "XNY02 (NY BOOK TWO)" in xr_
           and "Decisions to review" in xr_ and "`GMGB4436D02-OK`" in xr_.split("Decisions to review")[1][:200]
           and "GMBOX0031D03" not in json.dumps(xf_)
           and "XNY02" not in (ex / "out/db.conf.proposal").read_text(),
           "build_fe_jobs: an excluded book (books-excluded.csv) gets no job and no db.conf line; an old-named job of "
           "another reference book (label XLB03, same group as the template book's D03) is that step of each target "
           "book - not renamed, not copied; DROP-REVIEW drops and lists the decision; template_book per instrument",
           f"rc={rcx_} {rx_.errors} {w8}")
    (reg_.parent / "books-excluded.csv").write_text("code\nXNY99\n")
    rbx = bfj.Result()
    report(bfj.build(ex, rbx) == 1 and "excluded-book-unknown" in {c for c, *_ in rbx.errors},
           "build_fe_jobs refuses — an excluded book that is not in the register [excluded-book-unknown]", str(rbx.errors))
    # look-alikes: same group once the target's constants are resolved (J-E4b)
    import explain_job as ej
    cdir = Path(tempfile.mkdtemp())
    (cdir / "J-E4b-PGT_NY-constants.csv").write_text("OWNER,LINE,TEXT\nPGT_NY,40,  cst_pk_finac CONSTANT NUMBER := 3557.65;\n"
                                                      "PGT_NY,41,  cst_pk_ccs CONSTANT NUMBER := 4.65;\n")
    tc = ej.load_constants([cdir])
    rr_ = {"file": "db.conf", "entry": "PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup", "group": "3557.65",
           "instrument": "CST_PK_CCS"}
    tinv_ = [{"job": "GMNY0026D02_PR", "file": "db.conf", "entry": "PGT_NY.Pkg_GMBatchprocess.f_ExecuteGroup",
              "group": "CST_PK_FINAC", "instrument": "CST_PK_CCS", "family": "OTHER", "line": "9"},
             {"job": "GMNY0099D01_PR", "file": "db.conf", "entry": "PGT_NY.Pkg_GMBatchprocess.f_ExecuteGroup",
              "group": "CST_PK_OTHER", "instrument": "CST_PK_CCS", "family": "OTHER", "line": "10"},
             {"job": "GMNY0016D03_PR", "file": "shell.conf", "entry": "mover.sh", "params": "x", "family": "OTHER"}]
    top_, sure_ = ej.lookalikes(rr_, tinv_, {"CST_PK_CCS": "4.65"}, tc)
    sh_top, sh_sure = ej.lookalikes({"file": "shell.conf", "entry": "CargaSTM.sh", "params": "/miscarga SWA $ODATE 91"},
                                    tinv_, {}, tc)
    report(tc.get("CST_PK_FINAC") == "3557.65" and top_ and top_[0][1]["job"] == "GMNY0026D02_PR" and sure_
           and "same group 3557.65" in top_[0][2] and not sh_sure,
           "explain_job look-alikes: the target job of the same group (its CST_ constant resolved from J-E4b) is the "
           "confident match; another script (CargaSTM.sh vs mover.sh) is never a confident one", str(top_)[:400])

    # scheduling monitor: a prerequisite folder selected by instrument, group 39073.21 -> 2935.65 (2026-10-09)
    sm = fe_fixture(target=lambda t: dict(t, dbconf_format="pgt_prg", branch_pk="20007.4", local_group_suffix=".21",
                                          constant_values={"CST_PK_DINAMIC": "0", "CST_PK_VACIO": "0"},
                                          constants=dict(t["constants"], CST_PK_SWAP="SAME")))
    smc = json.loads((sm / "fe-jobs-inputs.json").read_text())
    smenv = Path(smc["reference"]["env_folder"])
    smcall = ("PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup(39073.21, PGT_ES.PKG_GMBATCHPROCESS.{b}, to_date('$ODATE',"
              "'YYYYMMDD'), PGT_ES.PKG_GMBATCHPROCESS.{i}, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC);")
    with (smenv / "db.conf").open("a") as f:
        for j, b, i in (("GMBX1LB00D06", "CST_PK_BRANC_LND", "CST_PK_DEP"), ("GMBX3LB00D06", "CST_PK_BRANC_LND", "CST_PK_SWAP"),
                        ("GMBX1ES00D06", "CST_PK_BRANC_MAD", "CST_PK_DEP")):
            f.write(f"{j}:T:F:" + smcall.format(b=b, i=i) + "\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(smenv)], capture_output=True, text=True)
    def smjob(n, d, waits=()):
        o = {"Type": "Job:Script", "FileName": n, "Host": "ref-host", "CreatedBy": "devid0", "RunAs": "gm",
             "Application": "REF-APP", "FilePath": "/appl/gm/scripts", "Description": f"BOX Scheduling monitor process - {d}",
             "When": {"WeekDays": ["NONE"], "MonthDays": ["D1"], "FromTime": "1300", "MonthDaysCalendar": "REFCAL"},
             "eventsToAdd": {"Type": "AddEvents", "Events": [{"Event": f"{n}-OK"}]}}
        if waits:
            o["eventsToWaitFor"] = {"Type": "WaitForEvents", "Events": [{"Event": w} for w in waits]}
        return o
    smrepo = sm.parents[2] / "schedmon"
    smrepo.mkdir()
    (smrepo / "schedmon.json").write_text(json.dumps({"JACD-T1-SCHEDMON-1": {"Type": "SimpleFolder",
        "GMBX1ES00D06": smjob("GMBX1ES00D06", "Madrid depo"), "GMBX3LB00D06": smjob("GMBX3LB00D06", "SLB IRS"),
        "GMBX1LB00D06": smjob("GMBX1LB00D06", "SLB depo", ["GMBX3LB00D06-OK"])}}, indent=2))
    smc["prerequisites"] = [{"controlm_json": str(smrepo / "schedmon.json"), "folder_name": "JACD-NY-SCHEDMON-9",
                             "select": "instruments"}]
    (sm / "fe-jobs-inputs.json").write_text(json.dumps(smc, indent=2))
    rsm = bfj.Result()
    report(bfj.build(sm, rsm) == 1 and "local-group-unmapped" in {c for c, *_ in rsm.errors},
           "build_fe_jobs refuses — a reference group local to its installation (.21) not mapped to the target's "
           "[local-group-unmapped]", str(rsm.errors))
    smc["prerequisites"][0]["group_map"] = {"39073.21": "2935.65"}
    (sm / "fe-jobs-inputs.json").write_text(json.dumps(smc, indent=2))
    rsm2 = bfj.Result()
    rcsm = bfj.build(sm, rsm2)
    smf = json.loads((sm / "out/JACD-NY-SCHEDMON-9.json").read_text())["JACD-NY-SCHEDMON-9"] if rcsm == 0 else {}
    smconf = (sm / "out/db.conf.proposal").read_text() if rcsm == 0 else ""
    report(rcsm == 0 and sorted(k for k, v in smf.items() if isinstance(v, dict)) == ["GMBX1NY00D06"]
           and "eventsToWaitFor" not in smf["GMBX1NY00D06"] and smf["GMBX1NY00D06"]["When"]["MonthDays"] == ["D1"]
           and smf["GMBX1NY00D06"]["Description"] == "BOX Scheduling monitor process - NY depo"
           and "GMBX1NY00D06:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(2935.65, 20007.4," in smconf
           and "39073.21" not in smconf and smconf.index("JACD-NY-SCHEDMON-9") < smconf.index("- FE - depos"),
           "build_fe_jobs scheduling monitor: a prerequisite folder selected by instrument (select: instruments) - only "
           "the reference branch's job of the instruments built, its wait on another instrument's job inherited, monthly "
           "When kept, db.conf line with the global group (39073.21 -> 2935.65)", f"rc={rcsm} {rsm2.errors} {sorted(smf)}")

    # versioned runs (new_run.py) + frozen run refused + the technical test pack (fe_tech_test.py) - 2026-10-09
    vr = Path(tempfile.mkdtemp())
    nr = lambda *a: subprocess.run([sys.executable, str(ROOT / "scripts/new_run.py"), "--root", str(vr), *a],
                                   capture_output=True, text=True)
    n1 = nr("--branch", "NY_SCH", "--tier", "tier2", "--env", "dev", "--area", "fe-jobs", "--name", "depos", "--date", "20261009")
    n2 = nr("--branch", "NY_SCH", "--tier", "tier2", "--env", "dev", "--area", "fe-jobs", "--name", "depos", "--date", "20261009")
    r1, r2 = Path(n1.stdout.splitlines()[0]) if n1.stdout else None, Path(n2.stdout.splitlines()[0]) if n2.stdout else None
    nr("--freeze", str(r1)) if r1 else None
    idx = (vr / "runs/NY_SCH/tier2-dev/fe-jobs/RUNS.md").read_text() if (vr / "runs/NY_SCH/tier2-dev/fe-jobs/RUNS.md").exists() else ""
    nb = nr("--branch", "XX", "--tier", "tier2", "--env", "dev", "--area", "fe-jobs", "--name", "depos")
    report(r1 and r1.name == "depos_20261009_1" and r2.name == "depos_20261009_2" and "NEW ENVIRONMENT" in n1.stdout
           and "books-register.csv" in n1.stdout and "NEW ENVIRONMENT" not in n2.stdout and (r1 / ".frozen").exists()
           and "`depos_20261009_1` | 20261009 | - | frozen" in idx and "`depos_20261009_2` | 20261009 | - | open" in idx
           and nb.returncode == 1 and (r1 / "RUN.md").exists(),
           "new_run: runs/<BRANCH>/<tier>-<env>/<area>/<name>_<date>_<n> - next free version, a new environment created "
           "empty with what it lacks listed, RUN.md + RUNS.md, --freeze; an unknown branch refused",
           n1.stdout + n2.stdout + idx)
    fz = fe_fixture()
    (fz / ".frozen").write_text("x")
    rfz = bfj.Result()
    report(bfj.build(fz, rfz) == 1 and "run-frozen" in {c for c, *_ in rfz.errors},
           "build_fe_jobs refuses — a frozen run is never written again [run-frozen]", str(rfz.errors))
    tt = Path(tempfile.mkdtemp())
    (tt / "pkg.sql").write_text("package body PKG_FE_DEAL_CALCULATION as\n procedure p_Import_Deal_Data(P_ProcessDate in date, "
                                "P_Label in varchar2) as\n begin\n merge into X using (select 1 from BOX_FE.T_BOX_RAW_DEAL_DATA_S r\n"
                                "  left join PGT_STC.T_PGT_OBJSRC_INPUT_S o on 1=1\n  inner join BOX_TRD.T_BOX_DEAL_S P on 1=1);\n end;\n"
                                " procedure p_Other as begin select 1 from dual join BOX_TRD.T_BOX_DEAL_S z on 1=1; end;\nend;\n")
    (tt / "jobs/out").mkdir(parents=True)
    (tt / "jobs/out/db.conf.proposal").write_text(
        "GMBX0NY01D02:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(2629.65, 20007.4, to_date('$ODATE','YYYYMMDD'), NULL, "
        "to_char(sysdate,'RRRR-mm-DD HH24:MI:SS'), 0, BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('XNY01'), NULL);\n"
        "GMBX0NY02D02:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(2629.65, 20007.4, to_date('$ODATE','YYYYMMDD'), NULL, "
        "to_char(sysdate,'RRRR-mm-DD HH24:MI:SS'), 0, BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('XNY02'), NULL);\n"
        "GMBX1NY01D05:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(2631.65, 20007.4, to_date('$ODATE','YYYYMMDD'), "
        "PGT_NY.PKG_GMBATCHPROCESS.CST_PK_DEP, to_char(sysdate,'RRRR-mm-DD HH24:MI:SS'), 0, "
        "BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('XNY01'), NULL);\n")
    run_t = tt / "run"
    run_t.mkdir()
    (run_t / "tech-test-inputs.json").write_text(json.dumps({
        "branch": "NY_SCH", "environment": "<ask>", "test_date": "2026-10-08", "branch_pk": "20007.4", "instrument": "depos",
        "branch_group_pk": "21447.4",
        "trades": [{"front_id": "123", "label": "XNY01"}, {"front_id": "456", "label": "XNY01"}],
        "fe_jobs_run": str(tt / "jobs"), "bypass": {"package_export": str(tt / "pkg.sql"), "reference_accounting": "DEAL_ID",
                                                    "extra_fields": {"FK_INSTRUMTYPE": "10053.4"}}}))
    ft = subprocess.run([sys.executable, str(ROOT / "scripts/fe_tech_test.py"), str(run_t)], capture_output=True, text=True)
    s40 = (run_t / "sql/40-DEV-bypass-join.sql").read_text() if (run_t / "sql/40-DEV-bypass-join.sql").exists() else ""
    s49 = (run_t / "sql/49-DEV-bypass-rollback.sql").read_text() if (run_t / "sql/49-DEV-bypass-rollback.sql").exists() else ""
    s30 = (run_t / "sql/30-DEV-static-check.sql").read_text() if (run_t / "sql/30-DEV-static-check.sql").exists() else ""
    s20 = (run_t / "sql/20-PROD-quote-prices.sql").read_text() if (run_t / "sql/20-PROD-quote-prices.sql").exists() else ""
    s50 = (run_t / "sql/50-DEV-accounting-attrs.sql").read_text() if (run_t / "sql/50-DEV-accounting-attrs.sql").exists() else ""
    rc_ = (run_t / "02-run-card.md").read_text() if (run_t / "02-run-card.md").exists() else ""
    plan_ = (run_t / "01-plan.md").read_text() if (run_t / "01-plan.md").exists() else ""
    report(ft.returncode == 0 and "left join BOX_TRD.T_BOX_DEAL_S P" in s40 and s40.count("left join") == 2
           and "dual join BOX_TRD.T_BOX_DEAL_S z" in s40 and "inner join BOX_TRD.T_BOX_DEAL_S P" in s49
           and s40.startswith("-- DEV ONLY") and "create or replace package body" in s40
           and "s.FK_OWNER_OBJ = 1453.4 AND s.FK_EXTENSION = 10513.4 AND s.FK_SOURCE = 279.4" in s30
           and "f_getBookByLabel('XNY01')" in s30 and "'Loan / Depos'" in s30
           and "`GMBX0NY01D02`" in rc_ and "`GMBX0NY02D02`" not in rc_ and "`GMBX1NY01D05`" in rc_
           and rc_.index("4a | **bypass:** `sql/40") < rc_.index("2629.65") and rc_.index("sql/50") < rc_.index("2631.65")
           and "`environment`" in plan_ and "OPEN" in plan_ and (run_t / "03-results.md").exists()
           and "FK_BRANCH = 20007.4 AND TRUNC(DATETOPROCESS) = DATE '2026-10-08'" in s30 and "BRPROCCAL" not in plan_
           and "WHERE p.FK_BRANCH = 21447.4 AND p.FK_INSTRUMENT = 2.4 AND p.STATUS = 'Valid'" in s50
           and "'OTHER GROUP'" in s50 and "'OTHER INSTRUMENT'" in s50 and "REFERENCE_ACCOUNTING = TO_CHAR(DEAL_ID)" in s50
           and "TO_CHAR(DEAL_ID), FK_INSTRUMTYPE = 10053.4\nWHERE FRONT_ID IN ('123', '456') AND DATEPROCESS" in s50
           and "RESET TO NULL by every re-run of 2629.65" in s50 and "`bypass.extra_fields`" in plan_
           and "UPPER(DATA_EXECUTION_TYPE) = 'BOOK'" in s30 and "TRUNC(MATURITYDATEREAL) + 5 >=" in s30
           and "resets `FK_PORTPROP`" in rc_ and "BoValidated" not in plan_
           and "FK_LOCALGROUP FROM PGT_STC.T_PGT_BRANCH_S WHERE PK = 20007.4" in s50
           and "TRUNC(PUBLISHDATE)" in s20 and "TRUNC(SETTLEDATE)" in s20 and "/*insert*/" not in s20
           and "`bypass.fk_portprop`" in plan_ and "`quote_prices_date_column`" in plan_,
           "fe_tech_test: the DEV-only bypass made from the DEV export (only p_Import_Deal_Data's join turned LEFT; the "
           "rollback = the export), the static check by alias + source, the label's book and instrument filters, the run "
           "card from the jobs run (the test's labels only) with the bypass steps in place, OPEN points in the plan; the "
           "portfolio property candidates by branch GROUP + sub-product (Valid), the update by FRONT_ID (one row per leg) "
           "with REFERENCE_ACCOUNTING = the deal's DEAL_ID when answered so and the extra online-flow fields given, "
           "p_Import_Deal_Data's filters as read, the reset of 2629.65 re-runs on the run card, the process calendar by FK_BRANCH / DATETOPROCESS, QR prices "
           "date column asked (both counted)",
           ft.stdout + ft.stderr + rc_[:800])
    # the NY inputs of DGBOUS: RAW already in DEV, the join already LEFT [operator, 2026-10-09]
    run_n = tt / "run_ny"
    run_n.mkdir()
    shutil.copyfile(ROOT / "runs/NY_SCH/tier2-dev/tests/technical/tech-test-inputs.NY_SCH.json", run_n / "tech-test-inputs.json")
    fn = subprocess.run([sys.executable, str(ROOT / "scripts/fe_tech_test.py"), str(run_n)], capture_output=True, text=True)
    rd = lambda f: (run_n / f).read_text() if (run_n / f).exists() else ""
    report(fn.returncode == 0 and (run_n / "sql/10-DEV-raw-check.sql").exists()
           and not (run_n / "sql/10-PROD-raw-extract.sql").exists() and "/*insert*/" not in rd("sql/10-DEV-raw-check.sql")
           and "FRONT_ID IN ('72376416', '73542359')" in rd("sql/10-DEV-raw-check.sql")
           and "already LEFT in this environment" in rd("sql/40-DEV-bypass-join.sql")
           and "create or replace" not in rd("sql/40-DEV-bypass-join.sql") and "nothing to restore" in rd("02-run-card.md")
           and "check the join is LEFT" in rd("02-run-card.md") and "`bypass.package_export`" not in rd("01-plan.md")
           and "`bypass.join`" not in rd("01-plan.md") and "`raw_market_data_filter`" not in rd("01-plan.md")
           and "WHERE p.FK_BRANCH = 21462.4 AND p.FK_INSTRUMENT = 2.4" in rd("sql/50-DEV-accounting-attrs.sql")
           and "2b. 0 rows in 2" in rd("sql/50-DEV-accounting-attrs.sql")
           and "f_getBookByLabel('XNY02')" in rd("sql/30-DEV-static-check.sql") and "| 2 | RAW rows of the test trades already in DEV" in rd("01-plan.md"),
           "fe_tech_test with NY's DGBOUS inputs: RAW already in DEV -> a DEV presence check, no PROD extract; the join "
           "already LEFT -> only its check, nothing to deploy or restore; the portfolio property found by queries "
           "(group + sub-product, what the group has, the reference group's shape)", fn.stdout + fn.stderr)
    (run_t / ".frozen").write_text("x")
    ft2 = subprocess.run([sys.executable, str(ROOT / "scripts/fe_tech_test.py"), str(run_t)], capture_output=True, text=True)
    report(ft2.returncode == 1 and "run-frozen" in ft2.stderr, "fe_tech_test refuses — a frozen run [run-frozen]",
           ft2.stderr)

    # old-named job: the rename suggestion follows its new-named siblings (same group)
    sb = fe_fixture(renames={})
    sbe = Path(json.loads((sb / "fe-jobs-inputs.json").read_text())["reference"]["env_folder"])
    with (sbe / "db.conf").open("a") as f:
        f.write("GMBX3LB00D01:T:F:PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup(2389.65, PGT_ES.PKG_GMBATCHPROCESS."
                "CST_PK_BRANC_LND, to_date('$ODATE','YYYYMMDD'), PGT_ES.PKG_GMBATCHPROCESS.CST_PK_SWAP, "
                "PGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC);\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(sbe)], capture_output=True, text=True)
    rsb = bfj.Result()
    bfj.build(sb, rsb)
    sbc = (sb / "pending-questions.md").read_text() if (sb / "pending-questions.md").exists() else ""
    sbr = next((x for x in sbc.splitlines() if x.startswith("| `GMBOX0114D01`")), "")
    report("`GMBX1NY00D01` - same group `2389.65`" in sbr and "`GMBX3LB00D01`" in sbr,
           "build_fe_jobs pending: an old-named job's suggested name follows the reference's new-named siblings of the "
           "same group (GMBOX0114D01 ~ GMBX3LB00D01 -> GMBX1NY00D01)", sbr or sbc[:500])
    rk = bfj.Result()
    report(bfj.build(fe_fixture(external_events={"GMGB4436D02-OK": "KEEP", "GMBX4LB00D02-OK": "KEEP"}), rk) == 1
           and "keep-reference-event" in {c for c, *_ in rk.errors} or False,
           "build_fe_jobs refuses — KEEP of the reference branch's own job's event [keep-reference-event]", str(rk.errors))
    # descriptors: every entry type, per-environment values, EndDate deletes, Data Lake in its PRE spelling (IAUKI)
    (tenv / "db.conf").write_text("".join(x for x in (tenv / "db.conf").read_text().splitlines(True)
                                          if not x.startswith("GMBX0NY00D02")))
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(tenv)], capture_output=True, text=True)
    lcfg["reference"]["descriptor_dir"] = str(ddir)
    lcfg["controlm"]["env"] = {"pre.json": {"Host": "t2-host-pre", "StartDate": "20261101", "OrderMethod": "ON DEMAND"}}
    (lp / "fe-jobs-inputs.json").write_text(json.dumps(lcfg, indent=2))
    (ddir / "pre.json").write_text(json.dumps({"DeployDescriptor": [
        {"Comment": "server", "Property": "ControlmServer", "Assign": "REF-SRV-PRE"},
        {"Comment": "host", "Property": "Host", "Assign": "ref-host-pre"},
        {"Comment": "order", "Property": "OrderMethod", "Assign": "JAC0500"},
        {"Comment": "folder", "Property": "@", "ApplyOn": {"Type": ".*Folder"}, "Replace": [{"JACD-(.*)": "JACI-$1"}]},
        {"Comment": "critico", "Add": {"Path": "$.DocumentationFile", "propertyName": "Path", "propertyValue": "CRITICO"}},
        {"Comment": "end", "Delete": "$.JACD-REF-BOXFE-1.GMBX1LB15D09.When.EndDate"},
        {"Comment": "start", "Add": {"Path": "$.JACD-REF-BOXFE-1.GMBX1LB15D06.When", "propertyName": "StartDate",
                                     "propertyValue": "20241120"}},
        dadd("GMBX0LB15D01", ["G010014-IAUKISCIBDDSLBBOOKA001D-OK"])]}, indent=2))
    rl5 = bfj.Result()
    rcl5 = bfj.build(lp, rl5)
    dpre = json.loads((lo / "descriptors/JACD-NY-BOXFE-9/pre.json").read_text())["DeployDescriptor"] \
        if (lo / "descriptors/JACD-NY-BOXFE-9/pre.json").exists() else []
    lfe5 = json.loads((lo / "JACD-NY-BOXFE-9.json").read_text()).get("JACD-NY-BOXFE-9", {}) if rcl5 == 0 else {}
    lrep5 = (lo / "report.md").read_text() if rcl5 == 0 else ""
    byc = {d.get("Comment"): d for d in dpre}
    sdates = [d["Add"]["propertyValue"] for d in dpre if d.get("Add", {}).get("propertyName") == "StartDate"]
    dlw = [d for d in dpre if d.get("Add", {}).get("Path") == "$.JACD-NY-BOXFE-9.GMBX0NY01D01"]
    report(rcl5 == 0 and byc.get("host", {}).get("Assign") == "t2-host-pre"
           and byc.get("order", {}).get("Assign") == "ON DEMAND"
           and byc.get("server", {}).get("Assign") == "REF-SRV-PRE" and "folder" in byc and "critico" in byc
           and "end" not in byc and sdates == ["20261101", "20261101"]
           and [e["Event"] for e in dlw[0]["Add"]["propertyValue"]["Events"]] == ["G010014-IAUKISCIBDDNYBOOKONE001D-OK"]
           and "GMBX1NY01D09" in lfe5 and "EndDate" not in json.dumps(lfe5.get("GMBX1NY01D09", {}))
           and "re-enabled by a descriptor" in lrep5 and "`REF-SRV-PRE` copied from the reference - confirm" in lrep5,
           "build_fe_jobs descriptors: Assign from the target's per-environment values (Host never guessed, others "
           "copied to confirm), regex Replace and $.DocumentationFile copied, StartDate from the inputs, an EndDate "
           "delete re-enables the job (copied, no EndDate) and is not copied, a PRE Data Lake wait keeps its I spelling",
           f"rc={rcl5} {rl5.errors} " + json.dumps(dpre)[:900])
    lcfg["controlm"].pop("env")
    (lp / "fe-jobs-inputs.json").write_text(json.dumps(lcfg, indent=2))
    rl6 = bfj.Result()
    bfj.build(lp, rl6)
    lrep6 = (lo / "report.md").read_text() if (lo / "report.md").exists() else ""
    report("target's Host for pre.json: controlm.env.pre.json.Host" in lrep6 and "StartDate (activation date)" in lrep6
           and "target's OrderMethod for pre.json: controlm.env.pre.json.OrderMethod" in lrep6,
           "build_fe_jobs descriptors: without the target's per-environment values, Host, OrderMethod (time zone: never "
           "SLB's) and StartDate go to review",
           lrep6[-900:])
    (ddir / "pre.json").unlink()

    # parse_job_confs: the core call p_ExecuteGroup (8 arguments)
    cenv = Path(tempfile.mkdtemp())
    (cenv / "db.conf").write_text("GMBX0MX01D01:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(2628.65, NULL, "
                                  "to_date('$ODATE','YYYYMMDD'),NULL,to_date('$ODATE','YYYYMMDD'), 0, "
                                  "BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('MX01'),NULL);\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/parse_job_confs.py"), str(cenv)], capture_output=True, text=True)
    crow = next(csv.DictReader((cenv / "jobs-inventory.csv").open()), {})
    report(crow.get("group") == "2628.65" and crow.get("label") == "label:MX01" and crow.get("mode") == "0"
           and crow.get("instrument") == "NULL" and crow.get("family") == "BOX" and crow.get("flags") == "T:P",
           "parse_job_confs: a core p_ExecuteGroup line is decoded (group, branch, date, instrument, time, vstatic, "
           "label, sub-label)", str(crow))

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
