#!/usr/bin/env python3
"""
validate_run_output.py — mechanical checks on a BOX FE config run folder.

Every check here encodes a defect this project actually produced. None of them
needs judgement, which is the point: the charter's hard rules are prose that a
model evaluates about its own output, and a model that misread a rule once will
misread it again. These run the same way every time.

    python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/
    python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/ --strict

Exit codes:  0 = no FAILs   1 = one or more FAILs   2 = bad invocation

--strict promotes WARN to FAIL. Use it in CI once a run is expected to be clean.

Checks are deliberately high-signal and low-false-positive: each one either
matches a known-bad pattern exactly, or counts something whose expected value is
known. Where a check cannot be made reliable it is a WARN with its reason stated,
never a silent pass.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Facts the checks rely on. Update these when the walk or the corpus changes.
# --------------------------------------------------------------------------

CANONICAL_STATUSES = {
    "CONFIRMED_PRESENT",
    "CONFIRMED_ABSENT",
    "PROPOSED",
    "DERIVED",
    "SME_DECISION_REQUIRED",
    "EXTERNAL_CHECK_REQUIRED",
    "EVIDENCE_REQUIRED",
    "NOT_BRANCH_SCOPED",
}

# Status-shaped tokens that have appeared in the corpus and are NOT canonical.
KNOWN_BAD_STATUSES = {"CROSS_TIER_VERIFIED", "REQUIRES_SME_VALUE"}

# The walk, in INSERT order. Step 1 is a read; 13/14 are verify-only; 4b, 9, 10
# are parked. Anything here must appear in the findings table with a status.
WALK_STEPS = {
    "1": "T_BOX_ENGCONF_X (read — reuse or new?)",
    "2": "T_BOX_ENGCONF_S",
    "3": "T_BOX_ENGFCURVE_S",
    "4": "T_BOX_ENGLKFC_X",
    "4b": "T_BOX_ENGFIXDISC_S (parked)",
    "5": "T_BOX_ENGCONF_X (write)",
    "6": "T_BOX_ENGACCRCONF_S",
    "7": "T_BOX_CONFIG_ACCRUAL_S",
    "8": "T_BOX_FIXING_BY_INSTR_S",
    "9": "T_BOX_ENGZCCONF_S (parked)",
    "10": "T_BOX_ENGCURRENCYBASIS_S (parked)",
    "11": "T_BOX_CONF_BY_BOOK_S",
    "12": "T_BOX_ERRORS_FE_S",
    "13": "T_BOX_FIXING_ASSIGNMENT_S / T_BOX_BRPROCCAL_S (derived)",
    "14": "T_BOX_ENGDAYS_MATURED_S / T_BOX_ENGSETUP_S (not branch-scoped)",
}

# Steps that must NEVER produce an INSERT.
NO_INSERT_STEPS = {"1", "4b", "9", "10", "13", "14"}

# INSERT order. A child appearing before its parent is a hard failure.
INSERT_ORDER = ["2", "3", "4", "5", "6", "7", "8", "11", "12"]

TARGET_TABLE_BY_STEP = {
    "2": "T_BOX_ENGCONF_S",
    "3": "T_BOX_ENGFCURVE_S",
    "4": "T_BOX_ENGLKFC_X",
    "5": "T_BOX_ENGCONF_X",
    "6": "T_BOX_ENGACCRCONF_S",
    "7": "T_BOX_CONFIG_ACCRUAL_S",
    "8": "T_BOX_FIXING_BY_INSTR_S",
    "11": "T_BOX_CONF_BY_BOOK_S",
    "12": "T_BOX_ERRORS_FE_S",
}

# Identity constants observed in Tier 1. Correct as values, wrong as literals —
# they must be derived per object (charter hard rule 9), not typed in.
TIER1_IDENTITY_CONSTANTS = [
    "35000126.65", "35000123.65", "35000289.65",
    "35001566.65", "35001114.65", "35001101.65",
]

# Procedures that COMMIT. Calling one inside a script framed as reversible is
# charter hard rule 11.
COMMITTING_PROCEDURES = ["p_check_val_curves_precommit"]

# Procedures that perform no DML and are safe to call as validation gates.
SAFE_PROCEDURES = ["p_engfixingcurve_precommit"]

DRAFT_HEADER_MARKER = "draft"

SEVERITY_ORDER = {"FAIL": 0, "WARN": 1, "INFO": 2}


@dataclass
class Finding:
    severity: str          # FAIL | WARN | INFO
    check: str
    message: str
    where: str = ""

    def __str__(self) -> str:
        loc = f"  [{self.where}]" if self.where else ""
        return f"{self.severity:<5} {self.check:<28} {self.message}{loc}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: str, check: str, message: str, where: str = "") -> None:
        self.findings.append(Finding(severity, check, message, where))

    def fail(self, check: str, message: str, where: str = "") -> None:
        self.add("FAIL", check, message, where)

    def warn(self, check: str, message: str, where: str = "") -> None:
        self.add("WARN", check, message, where)

    def info(self, check: str, message: str, where: str = "") -> None:
        self.add("INFO", check, message, where)

    def counts(self) -> dict[str, int]:
        out = {"FAIL": 0, "WARN": 0, "INFO": 0}
        for f in self.findings:
            out[f.severity] += 1
        return out


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def strip_sql_comments(sql: str) -> str:
    """Remove -- line comments and /* */ blocks, so annotations don't trip checks."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def split_statements(sql: str) -> list[str]:
    """Crude statement split on ';'. Good enough: every check is per-statement
    pattern matching, not parsing."""
    return [s.strip() for s in sql.split(";") if s.strip()]


def insert_statements(sql_nocomments: str) -> list[str]:
    return [s for s in split_statements(sql_nocomments)
            if re.match(r"^\s*INSERT\s+INTO", s, re.I)]


# --------------------------------------------------------------------------
# SQL checks
# --------------------------------------------------------------------------

def check_sql(path: Path, raw: str, rpt: Report) -> None:
    name = path.name
    sql = strip_sql_comments(raw)
    low = sql.lower()
    raw_low = raw.lower()

    # --- hard rule 4: no DDL, ever -------------------------------------
    for kw in ("create table", "alter table", "drop table", "create index",
               "truncate table"):
        if kw in low:
            rpt.fail("no-ddl", f"DDL found ({kw!r}) — charter hard rule 4", name)

    # --- hard rule 3: PKs come from F___SEQUENCE -----------------------
    bare_nextval = re.findall(r"sq_box_finaneng\d\s*\.\s*nextval", low)
    if bare_nextval and "f___sequence" not in low:
        rpt.fail("pk-bare-nextval",
                 "bare SQ_BOX_FINANENG*.NEXTVAL with no F___SEQUENCE — drops the "
                 "auth-code fraction (hard rule 3)", name)

    inserts = insert_statements(sql)
    if inserts and "f___sequence" not in low:
        rpt.fail("pk-no-sequence-call",
                 f"{len(inserts)} INSERT(s) but no F___SEQUENCE call anywhere — "
                 "a literal PK is a hard failure (hard rule 3)", name)

    # --- hard rule 9 + 'three kinds of column' -------------------------
    for stmt in inserts:
        head = stmt[:200].replace("\n", " ")
        if re.search(r"\bfrom\s+deveng\b", stmt, re.I) and re.search(r"\bselect\b", stmt, re.I):
            rpt.fail("insert-select-from-gbo",
                     "INSERT … SELECT … FROM DEVENG — collapses mined, allocated and "
                     f"structural columns (hard rule 9): {head!r}", name)
        # Column list present before VALUES/SELECT?
        m = re.match(r"^\s*INSERT\s+INTO\s+[\w.\"]+\s*(\()?", stmt, re.I)
        if m and not m.group(1):
            rpt.fail("insert-no-column-list",
                     f"INSERT without an explicit column list (hard rule 9): {head!r}", name)

    # --- identity constants must be bound, not typed -------------------
    for const in TIER1_IDENTITY_CONSTANTS:
        if const in sql:
            rpt.warn("identity-constant-literal",
                     f"hard-coded identity constant {const} — derive it per object "
                     "from Q-G6/Q-G7 and bind it (hard rule 9)", name)

    used_constants = {c for c in TIER1_IDENTITY_CONSTANTS[:3] if c in sql}
    if len(used_constants) == 1 and len(inserts) > 3:
        rpt.warn("identity-single-constant",
                 f"only one FK_OWNER_OBJ value ({used_constants.pop()}) across "
                 f"{len(inserts)} INSERTs — the walk spans three screens, so steps "
                 "3, 4 and 12 need different values", name)

    # --- hard rule 11: committing procedure vs rollback framing --------
    calls_committing = [p for p in COMMITTING_PROCEDURES if p in low]
    has_rollback = re.search(r"\browback\b|\brollback\b", low) is not None
    if calls_committing and has_rollback:
        rpt.fail("commit-vs-rollback",
                 f"script calls {calls_committing[0]} (which COMMITs) and also contains "
                 "ROLLBACK — the rollback is not an undo (hard rule 11)", name)
    if "commit" in low and "rollback" in low:
        rpt.warn("commit-and-rollback",
                 "script contains both COMMIT and ROLLBACK — state which statements "
                 "are actually reversible", name)

    # --- step 8 must carry its curve values ----------------------------
    for stmt in inserts:
        if "t_box_fixing_by_instr_s" in stmt.lower():
            if not re.search(r"fk_fixingcurve_(acc|man)", stmt, re.I):
                rpt.fail("step8-null-curves",
                         "step 8 INSERT does not set FK_FIXINGCURVE_ACC/MAN — the "
                         "step-2 pre-commit will back-fill them and COMMIT while "
                         "doing so (hard rules 10/11)", name)

    # --- draft marking --------------------------------------------------
    if inserts and DRAFT_HEADER_MARKER not in raw_low[:1200]:
        rpt.warn("draft-header",
                 "no 'draft' marker in the file header — required while gate 0e "
                 "and the deferred C2 reads are outstanding", name)

    # --- ordering -------------------------------------------------------
    seen: list[str] = []
    for stmt in inserts:
        for step, table in TARGET_TABLE_BY_STEP.items():
            if table.lower() in stmt.lower():
                seen.append(step)
                break
    ordered = [s for s in seen if s in INSERT_ORDER]
    expected_rank = {s: i for i, s in enumerate(INSERT_ORDER)}
    for a, b in zip(ordered, ordered[1:]):
        if expected_rank[b] < expected_rank[a]:
            rpt.fail("insert-order",
                     f"step {b} INSERT appears after step {a} — FK-dependency order "
                     f"is {' → '.join(INSERT_ORDER)}", name)
            break

    # --- steps that must never produce SQL ------------------------------
    parked_tables = {
        "t_box_engfixdisc_s": "4b", "t_box_engzcconf_s": "9",
        "t_box_engcurrencybasis_s": "10", "t_box_fixing_assignment_s": "13",
        "t_box_brproccal_s": "13", "t_box_engdays_matured_s": "14",
        "t_box_engsetup_s": "14",
    }
    for stmt in inserts:
        sl = stmt.lower()
        for table, step in parked_tables.items():
            if table in sl:
                rpt.fail("insert-for-no-insert-step",
                         f"INSERT into {table.upper()} — step {step} must never "
                         "produce a statement", name)

    # --- verification + rollback pairing --------------------------------
    if inserts:
        if not re.search(r"\bselect\b", low):
            rpt.warn("no-verification-select",
                     "no verification SELECT in the file (procedure step E3)", name)
        if not re.search(r"\bdelete\s+from\b", low):
            rpt.warn("no-rollback-delete",
                     "no rollback DELETE in the file — with a committing procedure "
                     "in the walk these are the only undo (E3, hard rule 11)", name)


# --------------------------------------------------------------------------
# Findings-table checks
# --------------------------------------------------------------------------

def check_findings(path: Path, text: str, rpt: Report) -> None:
    name = path.name
    upper = text.upper()

    # Non-canonical status tokens
    for token in sorted(KNOWN_BAD_STATUSES):
        if token in upper:
            rpt.fail("status-vocabulary",
                     f"{token} is not one of the canonical eight statuses", name)
    for token in set(re.findall(r"\b[A-Z][A-Z_]{6,}\b", upper)):
        if token.endswith("_REQUIRED") or token.startswith("CONFIRMED_"):
            if token not in CANONICAL_STATUSES:
                rpt.fail("status-vocabulary",
                         f"{token} looks like a status but is not canonical", name)

    # Every walk step present
    for step in WALK_STEPS:
        pattern = rf"(^|\|)\s*{re.escape(step)}\s*\|"
        if not re.search(pattern, text, re.M):
            rpt.fail("missing-walk-step",
                     f"step {step} ({WALK_STEPS[step]}) has no row in the findings "
                     "table — an unstatused object is the failure this agent exists "
                     "to prevent", name)

    # Every row carries a status
    rows = [ln for ln in text.splitlines()
            if ln.strip().startswith("|") and ln.count("|") >= 3]
    body = [r for r in rows if not re.match(r"^\s*\|[\s:|-]+\|\s*$", r)]
    unstatused = [r for r in body[1:]
                  if not any(s in r.upper() for s in CANONICAL_STATUSES)]
    if unstatused:
        rpt.warn("unstatused-row",
                 f"{len(unstatused)} findings row(s) carry no canonical status", name)

    if "[stated:" not in text and "[confirmed" not in text:
        rpt.warn("no-evidence-tags",
                 "no [stated:…] or [confirmed:…] tags — every status must trace to "
                 "a named query result or a named SME", name)


# --------------------------------------------------------------------------
# Cross-artifact checks
# --------------------------------------------------------------------------

def check_run_folder(folder: Path, rpt: Report) -> None:
    if not folder.is_dir():
        rpt.fail("run-folder", f"not a directory: {folder}")
        return

    evidence = folder / "01-evidence"
    findings = folder / "02-findings.md"
    sql_dir = folder / "03-sql"
    inputs = folder / "00-inputs.md"

    if not inputs.exists():
        rpt.warn("missing-inputs", "00-inputs.md absent — the input contract is "
                                   "written before any query runs")

    # --- hard rule 8: the visibility preflight ---------------------------
    if evidence.is_dir():
        csvs = sorted(p.name for p in evidence.glob("*.csv"))
        if not csvs:
            rpt.warn("no-evidence", "01-evidence/ contains no CSVs")
        elif not any("preflight" in c.lower() for c in csvs):
            rpt.fail("no-preflight",
                     "no preflight CSV in 01-evidence/ — a result set whose "
                     "visibility preflight was not run is not evidence (hard rule 8)")
    else:
        rpt.warn("no-evidence-dir", "01-evidence/ does not exist")

    # --- findings ---------------------------------------------------------
    if findings.exists():
        text = findings.read_text(encoding="utf-8", errors="replace")
        check_findings(findings, text, rpt)
        cited = set(re.findall(r"\bQ-[\w]+\b", text))
        if evidence.is_dir() and cited:
            have = " ".join(p.name for p in evidence.glob("*"))
            missing = sorted(q for q in cited if q not in have)
            if missing:
                rpt.warn("evidence-missing",
                         f"queries cited with no CSV in 01-evidence/: "
                         f"{', '.join(missing[:8])}"
                         f"{' …' if len(missing) > 8 else ''}")
    else:
        rpt.warn("missing-findings", "02-findings.md absent")

    # --- SQL --------------------------------------------------------------
    if sql_dir.is_dir():
        sql_files = sorted(sql_dir.glob("*.sql"))
        if not sql_files:
            rpt.info("no-sql", "03-sql/ contains no .sql files (expected before "
                               "the findings table is signed off)")
        for p in sql_files:
            check_sql(p, p.read_text(encoding="utf-8", errors="replace"), rpt)

        # Statements must not exist for unsigned rows.
        #
        # EVIDENCE_REQUIRED is treated differently from SME_DECISION_REQUIRED on
        # purpose. In a *deferred-verification* run — the preferred shape when the
        # target is read-blocked — every BOX-side finding is EVIDENCE_REQUIRED by
        # design and the SQL is a marked draft. Warning on that would cry wolf on
        # every legitimate run of the mode the charter recommends. An unresolved
        # SME decision is never legitimate.
        if findings.exists() and sql_files:
            ftext = findings.read_text(encoding="utf-8", errors="replace").upper()
            all_draft = all(
                DRAFT_HEADER_MARKER in p.read_text(
                    encoding="utf-8", errors="replace").lower()[:1200]
                for p in sql_files)
            if "SME_DECISION_REQUIRED" in ftext:
                rpt.fail("sql-with-open-sme-decision",
                         "SQL exists while the findings table still carries "
                         "SME_DECISION_REQUIRED rows — no statement may be emitted "
                         "for a decision nobody has made")
            if "EVIDENCE_REQUIRED" in ftext:
                if all_draft:
                    rpt.info("draft-sql-pending-evidence",
                             "EVIDENCE_REQUIRED rows with draft-marked SQL — the "
                             "designed state of a deferred-verification run")
                else:
                    rpt.fail("unmarked-sql-pending-evidence",
                             "EVIDENCE_REQUIRED rows but the SQL is not marked as a "
                             "draft — either mark it or resolve the evidence")
    else:
        rpt.info("no-sql-dir", "03-sql/ does not exist yet")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Mechanical checks on a BOX FE config run folder.")
    ap.add_argument("run_folder", type=Path,
                    help="e.g. runs/NY_SCH/tier2-pre/")
    ap.add_argument("--strict", action="store_true",
                    help="treat WARN as FAIL")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress INFO lines")
    args = ap.parse_args(argv)

    rpt = Report()
    check_run_folder(args.run_folder, rpt)

    rpt.findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.check))

    print(f"\nvalidate_run_output — {args.run_folder}")
    print("=" * 72)
    shown = [f for f in rpt.findings
             if not (args.quiet and f.severity == "INFO")]
    if not shown:
        print("  no findings")
    for f in shown:
        print(f"  {f}")

    c = rpt.counts()
    print("=" * 72)
    print(f"  {c['FAIL']} FAIL   {c['WARN']} WARN   {c['INFO']} INFO")
    if args.strict and c["WARN"]:
        print("  (--strict: WARNs count as failures)")
    print()

    failed = c["FAIL"] or (args.strict and c["WARN"])
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
