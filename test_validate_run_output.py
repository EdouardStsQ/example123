#!/usr/bin/env python3
"""
Regression tests for scripts/validate_run_output.py.

    python3 scripts/tests/test_validate_run_output.py

A check that fires on good output is more expensive than no check (run-3 review), so both
directions are tested: the filled templates must be clean, and each mutation must trip exactly
the check written for it.
"""
from __future__ import annotations
import re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VALIDATOR = ROOT / "scripts/validate_run_output.py"
sys.path.insert(0, str(HERE))
import build_fixtures  # noqa: E402


def run(folder: Path) -> tuple[set[str], set[str], str]:
    out = subprocess.run([sys.executable, str(VALIDATOR), str(folder)],
                         capture_output=True, text=True).stdout
    fails = set(re.findall(r"^\s+FAIL\s+(\S+)", out, re.M))
    warns = set(re.findall(r"^\s+WARN\s+(\S+)", out, re.M))
    return fails, warns, out


def mutated(src: Path, file_glob: str, old: str, new: str, count: int = 1) -> Path:
    tmp = Path(tempfile.mkdtemp()) / "run"
    shutil.copytree(src, tmp)
    [p] = list((tmp / "03-sql").glob(file_glob))
    text = p.read_text()
    assert old in text, f"mutation anchor not found: {old!r}"
    p.write_text(text.replace(old, new, count))
    return tmp


def main() -> int:
    build_fixtures.good()
    build_fixtures.run3_like()
    good = build_fixtures.OUT / "good"
    ok = True

    def expect(label, folder, must_fail=(), clean=False):
        nonlocal ok
        fails, warns, out = run(folder)
        missing = set(must_fail) - fails
        if clean and (fails or warns):
            ok = False; print(f"✗ {label}: expected clean, got FAIL {sorted(fails)} WARN {sorted(warns)}")
        elif missing:
            ok = False; print(f"✗ {label}: expected FAIL {sorted(missing)}\n{out}")
        else:
            print(f"✓ {label}")

    expect("filled templates are clean", good, clean=True)
    expect("run-3-like output trips every expert-review check", build_fixtures.OUT / "run3-like",
           must_fail={"auth-code-not-asserted", "source-column-wrong", "quote-refs-typed",
                      "branch-fk-not-branch", "conf-by-book-no-dummy", "rollback-dead-code",
                      "unresolved-substitution", "verify-script-missing", "rollback-script-missing"})
    expect("step-4 set with no count guard", mutated(good, "*config.sql",
           "RAISE_APPLICATION_ERROR(-20004", "DBMS_OUTPUT.PUT_LINE(-20004"),
           must_fail={"runtime-set-no-guard"})
    expect("an allocation without chk_pk", mutated(good, "*config.sql",
           "chk_pk(v_curve_pk, 'T_BOX_ENGFCURVE_S');", ""), must_fail={"pk-not-checked"})
    expect("step 7 copies GBO FK_BRANCH", mutated(good, "*config.sql",
           "r.CRITERIAL, c_branch_pk,", "r.CRITERIAL, r.FK_BRANCH,"), must_fail={"branch-fk-copied"})
    expect("verify script without the auth check", mutated(good, "*verify.sql",
           "gom_glb_sys.t__CORE_INFO_S", "dual"), must_fail={"verify-no-auth-check"})
    expect("script built for another auth code", mutated(good, "*config.sql",
           "CONSTANT NUMBER := 99;", "CONSTANT NUMBER := 21;"), must_fail={"auth-code-mismatch"})
    expect("source front copied from GBO", mutated(good, "*config.sql",
           "c_source_front        CONSTANT NUMBER := 513.4;", "c_source_front        CONSTANT NUMBER := 9.4;"),
           must_fail={"source-column-wrong"})
    expect("dummy book dropped from step 11", mutated(good, "*config.sql",
           "sys.odcinumberlist(23958.44, c_dummy_book)", "sys.odcinumberlist(23958.44)"),
           must_fail={"conf-by-book-no-dummy"})

    expect("header curve columns NULL (the 2026-09-22 design, ORA-01400)", mutated(good, "*config.sql",
           "v_curve_pk, v_curve_pk, c_source_front", "NULL, NULL, c_source_front"),
           must_fail={"curve-fk-null"})
    late = mutated(good, "*config.sql",
                   "SELECT auth_code INTO v_auth_code FROM gom_glb_sys.t__CORE_INFO_S;", "")
    [cf] = list((late / "03-sql").glob("*config.sql"))
    cf.write_text(cf.read_text().replace("c_source_front, c_source_back);",
        "c_source_front, c_source_back);\n  SELECT auth_code INTO v_auth_code FROM gom_glb_sys.t__CORE_INFO_S;", 1))
    expect("auth code read only after the first INSERT", late, must_fail={"auth-code-not-asserted"})

    # per-step unsigned-SQL logic, both directions
    def with_findings(src, step, status):
        tmp = Path(tempfile.mkdtemp()) / "run"
        shutil.copytree(src, tmp)
        f = tmp / "02-findings.md"
        f.write_text(re.sub(rf"^\| {re.escape(step)} \| object \| \w+ \|",
                            f"| {step} | object | {status} |", f.read_text(), flags=re.M))
        return tmp
    expect("SQL for a step still awaiting its SME", with_findings(good, "6", "SME_DECISION_REQUIRED"),
           must_fail={"sql-with-open-sme-decision"})
    fails, _, out = run(with_findings(good, "8", "SME_DECISION_REQUIRED"))
    if "sql-with-open-sme-decision" in fails:
        ok = False; print("✗ an open decision on a step with no SQL must not fail the run\n" + out)
    else:
        print("✓ an open decision on a step with no SQL does not fail the run")

    # a step header without an 'N rows' phrase must not borrow the next step's count
    fails, _, out = run(mutated(good, "*config.sql", "STEP 8 — Fixing exceptions → T_BOX_FIXING_BY_INSTR_S. 0 rows —",
                                "STEP 8 — Fixing exceptions → T_BOX_FIXING_BY_INSTR_S. none —"))
    if "step-row-count-mismatch" in fails:
        ok = False; print("✗ step 8 header borrowed a later step's row count\n" + out)
    else:
        print("✓ a header's row count is read from its own block only")

    print("\nall passed" if ok else "\nFAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
