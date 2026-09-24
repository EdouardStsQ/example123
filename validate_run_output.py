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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidence_to_sql  # noqa: E402  (same folder: one CSV reader for generator and checker)
import render_sql  # noqa: E402  (the SQL is rendered; the validator re-renders and compares)

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

# The walk, in INSERT order. Step 1 is a read; 13 and 14b are verify-only; 4b, 9, 10
# are not needed for NY (Question G, 2026-09-22) and verified absent. Anything here must appear in the findings table with a status.
WALK_STEPS = {
    "1": "T_BOX_ENGCONF_X (read — reuse or new?)",
    "2": "T_BOX_ENGCONF_S",
    "3": "T_BOX_ENGFCURVE_S",
    "4": "T_BOX_ENGLKFC_X",
    "4b": "T_BOX_ENGFIXDISC_S (not needed — verify absent)",
    "5": "T_BOX_ENGCONF_X (write)",
    "6": "T_BOX_ENGACCRCONF_S",
    "7": "T_BOX_CONFIG_ACCRUAL_S",
    "8": "T_BOX_FIXING_BY_INSTR_S",
    "9": "T_BOX_ENGZCCONF_S (not needed — verify absent)",
    "10": "T_BOX_ENGCURRENCYBASIS_S (not needed — verify absent)",
    "11": "T_BOX_CONF_BY_BOOK_S",
    "12": "T_BOX_ERRORS_FE_S",
    "13": "T_BOX_FIXING_ASSIGNMENT_S / T_BOX_BRPROCCAL_S (derived)",
    "14a": "T_BOX_ENGDAYS_MATURED_S (per instrument — insert only if missing)",
    "14b": "T_BOX_ENGSETUP_S (nothing to configure)",
}

# Steps that must NEVER produce an INSERT.
NO_INSERT_STEPS = {"1", "4b", "9", "10", "13", "14b"}

# INSERT order. A child appearing before its parent is a hard failure.
INSERT_ORDER = ["2", "3", "4", "5", "6", "7", "8", "11", "12", "14a"]

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
    "14a": "T_BOX_ENGDAYS_MATURED_S",
}

# Identity constants observed in Tier 1. Correct as values, wrong as literals —
# they must be derived per object (charter hard rule 9), not typed in.
TIER1_IDENTITY_CONSTANTS = [
    "35000126.65", "35000123.65", "35000289.65",
    "35001566.65", "35001114.65", "35001101.65",
    "35001120.65", "35000145.65",
]

# Procedures that COMMIT. Calling one inside a script framed as reversible is
# charter hard rule 11.
KNOWN_PRECOMMIT_PACKAGES = {"pkg_engprecommit"}

# Steps whose rows are keyed by instrument. Gate 0c fixes which instruments
# exist, so a PK outside the approved set in any of these is scope expansion.
INSTRUMENT_KEYED_STEPS = {"6", "7", "8", "11", "12", "14a"}

# Set per run from 00-inputs.md: "APPROVED_INSTRUMENTS: 20092.4, 2.4, …".
APPROVED_INSTRUMENTS: set[str] = set()

# Other per-run inputs, also read from 00-inputs.md ("NAME: value"). Empty = not stated.
RUN_INPUTS: dict[str, str] = {}
INPUT_NAMES = ("BRANCH_PK", "SOURCE_FRONT", "DUMMY_BOOK_LABEL", "TARGET_AUTH_CODE")
RUN_TEXT_INPUTS: dict[str, str] = {}      # QUOTE_REF_COLUMN (Q-04c's outcome)

# BOX is always the back source [stated: BOX FE expert via Edouard, 2026-09-23].
BOX_SOURCE_BACK = "586.4"

# Steps whose FK_BRANCH must be the branch itself. GBO's T_PGT_CONFIG_ACCRUAL_S
# keys on a branch CONFIG; copying it is the run-3 defect (hard rule 13, re-keyed).
BRANCH_KEYED_STEPS = {"7", "11", "12"}

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


def loop_iteration_count(body: str, whole: str) -> int | None:
    """How many rows a FOR … LOOP in `body` will emit, when countable.

    Two shapes occur: `FOR r IN (SELECT … UNION ALL …)` — count the SELECTs — and
    `FOR i IN 1 .. v_coll.COUNT` — find v_coll's ODCINUMBERLIST literal anywhere in
    the file and count its elements. Returns None when neither applies.
    """
    loops = re.findall(r"\bfor\s+\w+\s+in\b", body, re.I)
    if len(loops) > 1:
        return None                     # nested: the product is not countable here
    if re.search(r"for\s+\w+\s+in\s*\(\s*select[\s\S]*?\bfrom\s+deveng\.", body, re.I):
        return None                     # a runtime set read from GBO — the count guard owns it
    m = re.search(r"for\s+\w+\s+in\s*\(", body, re.I)
    if m:
        end = re.search(r"\bend\s+loop\b", body[m.end():], re.I)
        scope = body[m.end(): m.end() + (end.start() if end else len(body))]
        n = len(re.findall(r"\bselect\b", scope, re.I))
        return n or None
    m = re.search(r"for\s+\w+\s+in\s+\d+\s*\.\.\s*(\w+)\s*\.\s*count", body, re.I)
    if m:
        cm = re.search(re.escape(m.group(1)) + r"[\s\S]{0,120}?odcinumberlist\s*\(([\s\S]*?)\)",
                       whole, re.I)
        if cm:
            return len([x for x in cm.group(1).split(",") if x.strip()])
    return None


def insert_columns_and_values(stmt: str) -> tuple[list[str], list[str]]:
    """Column names and VALUES items of an INSERT … (cols) VALUES (vals).

    Positional, lowercased, best-effort: returns ([], []) for INSERT … SELECT or
    anything it cannot parse cleanly. Splits only on top-level commas so that
    F___SEQUENCE('T','X') survives as one item.
    """
    m = re.search(r"INSERT\s+INTO\s+[\w.\"]+\s*\(([^)]*)\)\s*VALUES\s*\(", stmt, re.I)
    if not m:
        return [], []
    cols = [c.strip().strip('"').lower() for c in m.group(1).split(",")]

    rest, depth, buf, vals = stmt[m.end():], 0, "", []
    for ch in rest:
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                break
            depth -= 1
        if ch == "," and depth == 0:
            vals.append(buf)
            buf = ""
            continue
        buf += ch
    vals.append(buf)
    return cols, [v.strip() for v in vals]


# --------------------------------------------------------------------------
# SQL checks
# --------------------------------------------------------------------------

def step_blocks(raw: str) -> list[tuple[str, str]]:
    """(step, block text) for every `-- STEP n` header, block running to the next header."""
    out = []
    heads = list(re.finditer(r"^[ \t]*--[ \t]*step[ \t]+(\d+[a-z]?)\b", raw, re.M | re.I))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(raw)
        out.append((m.group(1).lower(), raw[m.end():end]))
    return out


def resolve_value(v: str, sql_low: str) -> str | None:
    """A VALUES item as a numeric literal: itself, or the literal a CONSTANT was declared with."""
    v = v.strip().lower()
    if re.fullmatch(r"-?\d+(\.\d+)?", v):
        return v
    if re.fullmatch(r"[a-z_][\w$]*", v):
        m = re.search(rf"\b{re.escape(v)}\s+constant\s+\w+\s*:=\s*(-?\d+(?:\.\d+)?)\s*;", sql_low)
        if m:
            return m.group(1)
    return None


def same_number(a: str, b: str) -> bool:
    try:
        return float(a) == float(b)
    except ValueError:
        return False


def check_expert_review_rules(path: Path, name: str, raw: str, sql: str, low: str,
                              inserts: list[str], rpt: Report) -> None:
    """One check per point the BOX FE expert raised on run 3 (2026-09-23, ADR 0005)."""

    # --- BOX_FE only: the applying account sees nothing else ---------------
    other = sorted(set(re.findall(r"\b(deveng|pgt_stc|pgt_sys|pgt_mrk|gom_glb_sys)\s*\.", low)))
    if other:
        rpt.fail("config-reads-other-schema",
                 f"the config script references {', '.join(o.upper() for o in other)} — the account that "
                 "applies it sees BOX_FE only [assumed 2026-09-23]; the block would not compile. GBO sets "
                 "travel as generated literals (scripts/evidence_to_sql.py); GBO comparisons belong in "
                 "the verify script", name)

    # --- point 1: the auth code is visible and asserted --------------------
    n_alloc = len(re.findall(r"f___sequence\s*\(", low))
    n_chk = len(re.findall(r"\bchk_pk\s*\(", low)) - len(re.findall(r"procedure\s+chk_pk\b", low))
    m_frac = re.search(r"c_expected_fraction\s+constant\s+number\s*:=\s*(-?\d+(?:\.\d+)?)\s*;", low)
    if not m_frac:
        rpt.fail("auth-code-not-asserted",
                 "no c_expected_fraction constant — the auth-code fraction every PK must carry is "
                 "invisible and unchecked (Q-G3c, hard rule 3, templates/config.sql.tmpl)", name)
    elif n_chk < n_alloc:
        rpt.fail("pk-not-checked",
                 f"{n_alloc} F___SEQUENCE allocation(s) but {n_chk} chk_pk() call(s) — every "
                 "allocated PK is checked for the auth-code fraction (templates/config.sql.tmpl)", name)
    first_insert = re.search(r"\binsert\s+into\b", low)
    first_chk = re.search(r"(?<!procedure )\bchk_pk\s*\(", low)
    if m_frac and first_insert and (not first_chk or first_chk.start() > first_insert.start()):
        rpt.fail("auth-code-not-asserted",
                 "no chk_pk() before the first INSERT — the environment check must stop a script in "
                 "the wrong environment before it writes anything", name)
    want = RUN_INPUTS.get("TARGET_AUTH_CODE")
    if want and m_frac:
        expect = int(float(want)) / 10 ** len(str(int(float(want))))
        if not same_number(m_frac.group(1), str(expect)):
            rpt.fail("auth-code-mismatch",
                     f"00-inputs.md records TARGET_AUTH_CODE {want} (fraction {expect:g}) but the script "
                     f"expects {m_frac.group(1)}", name)

    # --- point 2: the header's source columns are BOX's, not GBO's ----------
    for stmt in inserts:
        if not re.search(r"insert\s+into\s+[\w.]*t_box_engconf_s\b", stmt, re.I):
            continue
        cols, vals = insert_columns_and_values(stmt)
        if len(cols) != len(vals):
            continue
        for col, want, label in (("fk_source_back", BOX_SOURCE_BACK, "586.4 (BOX is always the back source)"),
                                 ("fk_source_front", RUN_INPUTS.get("SOURCE_FRONT"), "SOURCE_FRONT from 00-inputs.md")):
            if col not in cols:
                rpt.fail("source-column-missing", f"step 2 INSERT has no {col.upper()}", name)
                continue
            got = resolve_value(vals[cols.index(col)], low)
            if not want:
                rpt.warn("no-source-front-input",
                         "00-inputs.md states no SOURCE_FRONT — the Murex instance is a stated "
                         "input, never mined from GBO (Q-02c)", name)
            elif got is None:
                rpt.warn("source-column-unresolved",
                         f"{col.upper()} is neither a literal nor a declared constant — cannot check "
                         f"it is {label}", name)
            elif not same_number(got, want):
                rpt.fail("source-column-wrong",
                         f"{col.upper()} = {got}, expected {label}. GBO's source systems are "
                         "re-keyed columns and are never copied (hard rule 13, Q-02)", name)

    # --- point 3 (and step 7): GBO sets equal their evidence -----------------
    try:
        check_sets_against_evidence(path, raw, rpt)
    except SystemExit as e:              # the shared CSV reader stops on a malformed file
        rpt.fail("evidence-unreadable", f"cannot read the evidence CSV: {e}", name)

    blocks = step_blocks(raw)
    for step, block in blocks:
        blow = strip_sql_comments(block).lower()
        # a set read from GBO inside the script must be count-guarded
        if re.search(r"for\s+\w+\s+in\s*\(\s*select[\s\S]*?\bfrom\s+deveng\.", blow) and \
                "raise_application_error" not in blow:
            rpt.fail("runtime-set-no-guard",
                     f"step {step} reads its rows from DEVENG at runtime with no count guard — the "
                     "set can shrink silently between the evidence and the apply (hard rule 8)", name)

        # --- point 4 (and 11, 12): FK_BRANCH is the branch --------------------
        if step in BRANCH_KEYED_STEPS:
            table = TARGET_TABLE_BY_STEP[step].lower()
            for stmt in insert_statements(strip_sql_comments(block)):
                if table not in stmt.lower():
                    continue
                cols, vals = insert_columns_and_values(stmt)
                if "fk_branch" not in cols or len(cols) != len(vals):
                    continue
                v = vals[cols.index("fk_branch")].strip().lower()
                if re.fullmatch(r"\w+\.fk_branch", v):
                    rpt.fail("branch-fk-copied",
                             f"step {step} writes FK_BRANCH = {v} — copied from the source row. In GBO "
                             "that column is a branch-CONFIG PK; BOX wants the branch (hard rule 13, "
                             "Q-06)", name)
                    continue
                got = resolve_value(v, low)
                bpk = RUN_INPUTS.get("BRANCH_PK")
                if got and bpk and not same_number(got, bpk):
                    rpt.fail("branch-fk-not-branch",
                             f"step {step} writes FK_BRANCH = {got}, but BRANCH_PK is {bpk}. Run 3 "
                             "wrote GBO's branch config 141.35 here (Q-06)", name)

        # --- point 5: every instrument also gets the dummy book ---------------
        if step == "11" and re.search(r"insert\s+into\s+[\w.]*t_box_conf_by_book_s", blow):
            dummy = RUN_INPUTS.get("DUMMY_BOOK_LABEL")
            if not dummy:
                rpt.warn("no-dummy-book-input",
                         "00-inputs.md states no DUMMY_BOOK_LABEL — step 11 needs a dummy-book row "
                         "per instrument (Q-10c)", name)
            else:
                idents = set(re.findall(r"\b[a-z_][\w$]*\b", blow))
                hit = dummy in blow or any(
                    (rv := resolve_value(i, low)) and same_number(rv, dummy) for i in idents)
                if not hit:
                    rpt.fail("conf-by-book-no-dummy",
                             f"step 11 never writes the dummy book {dummy} — every instrument gets a "
                             "(dummy book × instrument) row besides its real books (Q-10)", name)



def _evidence_csv(path: Path, pattern: str) -> Path | None:
    hits = sorted((path.parent.parent / "01-evidence").glob(pattern))
    return hits[0] if hits else None


def _sql_number(v: str) -> str | None:
    v = v.strip().lower()
    if re.fullmatch(r"cast\s*\(\s*null\s+as\s+number\s*\)|null", v):
        return None
    return evidence_to_sql.norm(v) if re.fullmatch(r"-?\d+(\.\d+)?", v) else v


def check_sets_against_evidence(path: Path, raw: str, rpt: Report) -> None:
    """The expert's point 3: *how are we sure the values are correct?* The literal sets in steps 4
    and 7 must be exactly what the evidence CSV holds — the validator reads the same CSV the
    generator did. (Verify V4/V10 then compare BOX with GBO in the database.)"""
    name, code = path.name, strip_sql_comments(raw)

    # step 4 — the quote-reference list
    if re.search(r"insert\s+into\s+[\w.]*t_box_englkfc_x", code, re.I):
        m = re.search(r"v_quote_refs\s+sys\.odcinumberlist\s*:=\s*sys\.odcinumberlist\s*\(([^)]*)\)", code, re.I)
        csv_p = _evidence_csv(path, "Q-04c*gbo*.csv")
        col = RUN_TEXT_INPUTS.get("QUOTE_REF_COLUMN", "FK_BS").upper()
        if not m:
            rpt.fail("quote-refs-not-generated",
                     "step 4 inserts quote references but has no v_quote_refs list — the set is "
                     "generated from Q-04c's CSV (scripts/evidence_to_sql.py), never read from DEVENG "
                     "or typed", name)
        elif not csv_p:
            rpt.fail("quote-refs-unchecked",
                     "no 01-evidence/Q-04c-…-gbo.csv — cannot prove step 4's list equals the evidence. Save the CSV the list was generated from", name)
        else:
            sql_set = {evidence_to_sql.norm(v) for v in m.group(1).split(",") if v.strip()}
            rows = evidence_to_sql.read_rows(csv_p)
            ev = {evidence_to_sql.norm(r.get(col, "")) for r in rows} - {None}
            if sql_set != ev:
                extra, miss = sorted(sql_set - ev, key=float), sorted(ev - sql_set, key=float)
                rpt.fail("quote-refs-not-evidence",
                         f"step 4's list differs from {csv_p.name} column {col}: "
                         f"{len(extra)} not in the evidence {extra[:5]}, {len(miss)} missing {miss[:5]}. "
                         "Regenerate it with scripts/evidence_to_sql.py", name)

    # step 7 — the exception rows
    if re.search(r"insert\s+into\s+[\w.]*t_box_config_accrual_s", code, re.I):
        cols = ["FK_INSTRUMENT", "FK_STRATEGY", "FK_INSTRTYPE", "CRITERIAL"]
        sql_rows = set()
        for sel in re.findall(r"select\s+((?:(?!\bselect\b).)*?)\s+from\s+dual\b(?!\s+where\s+1\s*=\s*0)", code, re.I | re.S):
            items = dict()
            for part in split_top_level(sel):
                am = re.match(r"(.*?)\s+as\s+(\w+)\s*$", part.strip(), re.I | re.S)
                if am:
                    items[am.group(2).upper()] = _sql_number(am.group(1))
            if set(cols) <= set(items):
                sql_rows.add(tuple(items[c] for c in cols))
        csv_p = _evidence_csv(path, "Q-06c*.csv")
        bpk = RUN_INPUTS.get("BRANCH_PK")
        if not csv_p or not bpk:
            rpt.fail("exceptions-unchecked",
                     "no 01-evidence/Q-06c-….csv or no BRANCH_PK — cannot prove step 7's rows equal "
                     "the evidence", name)
            return
        ev = set()
        for r in evidence_to_sql.read_rows(csv_p):
            if evidence_to_sql.norm(r.get("BRANCH_PK", "")) != evidence_to_sql.norm(bpk):
                continue
            if APPROVED_INSTRUMENTS and evidence_to_sql.norm(r.get("FK_INSTRUMENT", "")) not in \
                    {evidence_to_sql.norm(v) for v in APPROVED_INSTRUMENTS}:
                continue
            ev.add(tuple(evidence_to_sql.norm(r.get(c, "")) for c in cols))
        if sql_rows != ev:
            rpt.fail("exceptions-not-evidence",
                     f"step 7's rows differ from {csv_p.name} filtered to BRANCH_PK {bpk} and the approved "
                     f"instruments: {len(sql_rows - ev)} extra, {len(ev - sql_rows)} missing. Regenerate "
                     "with scripts/evidence_to_sql.py rows", name)


def split_top_level(s: str) -> list[str]:
    out, depth, buf = [], 0, ""
    for ch in s:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            out.append(buf); buf = ""
        else:
            buf += ch
    out.append(buf)
    return out



# --------------------------------------------------------------------------
# Run-4 checks (2026-09-24) — each one a defect run 4 produced
# --------------------------------------------------------------------------

STANDALONE_OBJECT_TABLES = {          # tables whose rows belong to their OWN SIGOM object
    "t_box_engfcurve_s", "t_box_englkfc_x", "t_box_errors_fe_s", "t_box_engdays_matured_s",
}
CONFIG_OWNER_TIER1 = "35000126.65"    # BOX_ENG_Config — right for 2, 5, 6, 7, 11; wrong for the above


def _matching_paren(s: str, open_idx: int) -> int:
    depth = 0
    for k in range(open_idx, len(s)):
        depth += s[k] == "("
        depth -= s[k] == ")"
        if depth == 0:
            return k
    return -1


def _select_list_names(cursor_sql: str) -> set[str]:
    m = re.search(r"\bselect\b(.*?)\bfrom\b", cursor_sql, re.I | re.S)
    if not m:
        return set()
    names = set()
    for item in split_top_level(m.group(1)):
        item = item.strip()
        am = re.match(r"(.*\S)\s+(?:as\s+)?([a-z_][\w$]*)$", item, re.I | re.S)
        if am and not re.fullmatch(r"(?:\w+\.)?\w+", item):
            names.add(am.group(2).lower())
        else:
            cm = re.fullmatch(r"(?:\w+\.)?([a-z_][\w$]*)", item, re.I)
            if cm:
                names.add(cm.group(1).lower())
            elif am:
                names.add(am.group(2).lower())
    return names


def check_run4_rules(name: str, code: str, inserts: list[str], raw: str, rpt: Report) -> None:
    low = code.lower()

    # --- a cursor's fields are the names its SELECT gives them --------------
    for m in re.finditer(r"\bfor\s+([a-z_]\w*)\s+in\s*\(", low):
        var, open_idx = m.group(1), m.end() - 1
        close = _matching_paren(low, open_idx)
        if close < 0 or not re.match(r"\s*loop\b", low[close + 1:]):
            continue
        names = _select_list_names(low[open_idx + 1: close])
        if not names:
            continue
        nxt = re.search(rf"\bfor\s+{re.escape(var)}\s+in\b", low[close:])
        body = low[close: close + (nxt.start() if nxt else len(low))]
        bad = sorted({f for f in re.findall(rf"\b{re.escape(var)}\.([a-z_][\w$]*)", body)} - names)
        if bad:
            rpt.fail("cursor-field-undeclared",
                     f"the loop over {var} reads {', '.join(var + '.' + b for b in bad)} but its SELECT names "
                     f"only {', '.join(sorted(names))} — PLS-00302, the block does not compile (run 4, step 7)",
                     name)

    # --- standalone objects carry their own owner, not the Config's ---------
    conf_owner = None
    for stmt in inserts:
        if re.search(r"insert\s+into\s+[\w.]*t_box_engconf_s\b", stmt, re.I):
            cols, vals = insert_columns_and_values(stmt)
            if "fk_owner_obj" in cols and len(cols) == len(vals):
                conf_owner = resolve_value(vals[cols.index("fk_owner_obj")], low)
    for stmt in inserts:
        tm = re.search(r"insert\s+into\s+[\w.]*?(t_box_\w+)", stmt, re.I)
        if not tm or tm.group(1).lower() not in STANDALONE_OBJECT_TABLES:
            continue
        cols, vals = insert_columns_and_values(stmt)
        if "fk_owner_obj" not in cols or len(cols) != len(vals):
            continue
        got = resolve_value(vals[cols.index("fk_owner_obj")], low)
        if got and ((conf_owner and same_number(got, conf_owner)) or same_number(got, CONFIG_OWNER_TIER1)):
            rpt.fail("identity-wrong-object",
                     f"{tm.group(1).upper()} is written with FK_OWNER_OBJ {got}, the MIS Config's owner — this "
                     "table belongs to its own SIGOM object (Q-G6: FixingCurve / Limit Error Assign / Days "
                     "Matured). It inserts cleanly and is edited through the wrong screen (run 4, step 14a)",
                     name)

    # --- step 11: the dummy is not a real book ------------------------------
    for step, block in step_blocks(raw):
        if step != "11":
            continue
        blow = strip_sql_comments(block).lower()
        if not re.search(r"insert\s+into\s+[\w.]*t_box_conf_by_book_s", blow):
            continue
        labels = set()
        for stmt in insert_statements(strip_sql_comments(block)):
            cols, vals = insert_columns_and_values(stmt)
            if "fk_label" in cols and len(cols) == len(vals):
                v = resolve_value(vals[cols.index("fk_label")], low)
                if v:
                    labels.add(evidence_to_sql.norm(v))
        for lm in re.finditer(r"odcinumberlist\s*\(([^)]*)\)", blow):
            if re.search(r"\blabel\b", blow[max(0, lm.start() - 80): lm.end() + 40]):
                for item in lm.group(1).split(","):
                    v = resolve_value(item, low)
                    if v:
                        labels.add(evidence_to_sql.norm(v))
        dummy = RUN_INPUTS.get("DUMMY_BOOK_LABEL")
        book_inputs = {evidence_to_sql.norm(v) for v in re.findall(r"\d+\.\d+", RUN_TEXT_INPUTS.get("BOOK_LABELS", ""))}
        if (labels and len(labels) == 1) or (dummy and evidence_to_sql.norm(dummy) in book_inputs):
            rpt.fail("dummy-is-a-book",
                     f"step 11 writes a single label ({', '.join(sorted(labels)) or dummy}) — the dummy book "
                     "and the real book are the same row. The dummy is a BOX FE rule and cannot be waived "
                     "or relabelled; find it with Q-10d and put it to the BOX FE team (run 4)", name)

    # --- every step that writes carries its provenance header -----------------
    for hm in re.finditer(r"^[ \t]*--[ \t]*step[ \t]+(\d+[a-z]?)\b[^\n]*\n((?:[ \t]*--[^\n]*\n)*)", raw, re.M | re.I):
        step, head = hm.group(1).lower(), hm.group(2).lower()
        table = TARGET_TABLE_BY_STEP.get(step)
        if not table:
            continue
        nxt = re.search(r"^[ \t]*--[ \t]*step[ \t]+\d", raw[hm.end():], re.M | re.I)
        body = strip_sql_comments(raw[hm.end(): hm.end() + (nxt.start() if nxt else len(raw))]).lower()
        if not re.search(r"insert\s+into\s+[\w.]*" + table.lower(), body):
            continue
        missing = [w for w in ("source", "findings", "if wrong") if w not in head]
        if missing:
            rpt.fail("step-header-incomplete",
                     f"step {step}'s header has no {', '.join(missing)} line — the template's header is how a "
                     "reviewer traces a value to its query and its sign-off (run 4 cut them to one line)", name)

    # --- the gates the template carries ------------------------------
    if re.search(r"insert\s+into\s+[\w.]*t_box_engfcurve_s", low) and "p_engfixingcurve_precommit" not in low:
        rpt.fail("curve-precommit-missing",
                 "a curve is created but P_ENGFixingCurve_PreCommit is never called — the one no-DML check "
                 "on the curve (hard rule 10)", name)
    # (existing-row guards: see check_run5_rules)



def check_verify_file(name: str, raw: str, config_code_low: str, rpt: Report) -> None:
    code = strip_sql_comments(raw)
    low = code.lower()
    if re.search(r"\bwhere\s+1\s*=\s*0\b", low) or re.search(r"(?<![\w.])(\d+(?:\.\d+)?)\s*<>\s*\1(?![\w.])", low):
        rpt.fail("verify-placebo",
                 "a verification query that cannot fail (WHERE 1=0, or a value compared with itself) — "
                 "run 4's auth-code 'check' was one. A check that cannot fail is not a check", name)
    missing = []
    if not re.search(r"\bfrom\s+gom_glb_sys\.t__core_info_s\b", low):
        missing.append("V1 auth code read from GOM_GLB_SYS.T__CORE_INFO_S")
    if "t_box_englkfc_x" in config_code_low and not ("deveng.t_pgt_englkfc_x" in low and "minus" in low):
        missing.append("V4 quote array compared with DEVENG.T_PGT_ENGLKFC_X (MINUS both ways)")
    if "t_box_config_accrual_s" in config_code_low and "deveng.t_pgt_config_accrual_s" not in low:
        missing.append("V10 exceptions compared with DEVENG.T_PGT_CONFIG_ACCRUAL_S")
    if "fk_owner_obj" not in low:
        missing.append("V9 identity per table")
    if missing:
        rpt.fail("verify-incomplete",
                 "the verification script is missing: " + "; ".join(missing) +
                 " — build it from templates/verify.sql.tmpl", name)




def check_run5_rules(name: str, code: str, inserts: list[str], raw: str, rpt: Report) -> None:
    """Defects run 5 produced (2026-09-24)."""
    low = code.lower()

    # --- a local procedure/function inside a SQL statement does not compile --
    local = set(re.findall(r"\b(?:procedure|function)\s+([a-z_]\w*)", low))
    for stmt in insert_statements(code):
        used = sorted(n for n in local if re.search(rf"\b{n}\s*\(", stmt, re.I))
        if used:
            rpt.fail("local-procedure-in-sql",
                     f"{', '.join(used)} is called inside an INSERT — a block-local procedure cannot be used "
                     "in a SQL statement (PLS-00222 / PLS-00231); the whole block is rejected. Assign the PK, "
                     "call chk_pk on its own line, then INSERT (run 5, steps 6/11/12/14a)", name)
            break

    # --- guards must read the table they guard, before its first INSERT --------
    if re.search(r"\bif\s+c_\w+\s*=\s*-1\b", low):
        rpt.fail("guard-placebo",
                 "a guard compares a constant with -1 — it can never fire. A guard reads the table: "
                 "SELECT COUNT(*) INTO v_n FROM <table> WHERE …; then tests v_n against 0 (run 5)", name)
    for step in ("11", "12", "14a"):
        table = TARGET_TABLE_BY_STEP[step].lower()
        ins = re.search(r"insert\s+into\s+[\w.]*" + table + r"\b", low)
        if not ins:
            continue
        before = low[:ins.start()]
        g = None
        for g in re.finditer(r"select\s+count\s*\(\s*\*\s*\)\s+into\s+(\w+)\s+from\s+[\w.]*" + table + r"\b[^;]*;", before):
            pass
        tested = g and re.search(rf"(\bif\s+{g.group(1)}\s*(<>|!=|>)\s*0\b|expect_rows\s*\([^;]*,\s*{g.group(1)}\s*,\s*0\s*\))",
                                 before[g.end(): g.end() + max(0, before.find(";", g.end()) - g.end())])
        if not tested:
            rpt.fail("no-existing-row-guard",
                     f"step {step} inserts into {table.upper()} without first counting the rows already there and "
                     "stopping on any — the rollback finds these rows by branch or instrument, so it may delete rows "
                     "this run did not create", name)

    # --- step 4 inserts from the generated list, not from typed literals ------
    lk = [s for s in inserts if re.search(r"insert\s+into\s+[\w.]*t_box_englkfc_x", s, re.I)]
    typed = []
    for stmt in lk:
        cols, vals = insert_columns_and_values(stmt)
        if "fk_bs" in cols and len(cols) == len(vals) and re.fullmatch(r"-?\d+(\.\d+)?", vals[cols.index("fk_bs")].strip()):
            typed.append(vals[cols.index("fk_bs")].strip())
    if typed:
        rpt.fail("quote-refs-typed",
                 f"{len(typed)} step-4 INSERT(s) carry a typed FK_BS literal — the generated v_quote_refs list is "
                 "what the validator checks against the evidence; typed values beside it are unchecked "
                 "(run 5: 38 typed INSERTs, the list declared and never used)", name)
    elif lk and "v_quote_refs" in low and not any("v_quote_refs" in s.lower() for s in lk):
        rpt.fail("quote-refs-list-unused",
                 "v_quote_refs is declared but no step-4 INSERT reads it", name)

    # --- every writing step has a header ---------------------------------------
    headed = {m.group(1).lower() for m in re.finditer(r"^[ \t]*--[ \t]*step[ \t]+(\d+[a-z]?)\b", raw, re.M | re.I)}
    unheaded = [st for st, t in TARGET_TABLE_BY_STEP.items()
                if st not in headed and re.search(r"insert\s+into\s+[\w.]*" + t.lower() + r"\b", low)]
    if unheaded:
        rpt.fail("step-without-header",
                 f"step(s) {', '.join(unheaded)} write rows with no `-- STEP n` header at all — nothing tells a "
                 "reviewer their source or sign-off (run 5: steps 2–5)", name)

    # --- step 11 rows belong to the configuration ------------------------------
    for stmt in inserts:
        if re.search(r"insert\s+into\s+[\w.]*t_box_conf_by_book_s", stmt, re.I):
            cols, _ = insert_columns_and_values(stmt)
            if cols and "fk_parent" not in cols:
                rpt.fail("conf-by-book-no-parent",
                         "a T_BOX_CONF_BY_BOOK_S row without FK_PARENT — it is the Config's amConfigByBook "
                         "extension; without the header's PK it belongs to no configuration, and verify and "
                         "rollback (keyed by FK_PARENT) never find it (run 5)", name)
                break

    # --- the two pre-commits, in the right place -------------------------------
    if re.search(r"insert\s+into\s+[\w.]*t_box_engconf_s\b", low) and "p_check_val_curves_precommit" not in low:
        rpt.fail("config-precommit-missing",
                 "the Config's pre-commit p_check_Val_Curves_precommit is never called (hard rule 10); a bare "
                 "COMMIT is not a substitute (run 5)", name)
    pc = low.find("p_engfixingcurve_precommit")
    first_lk = re.search(r"insert\s+into\s+[\w.]*t_box_englkfc_x", low)
    if pc >= 0 and first_lk and pc < first_lk.start():
        rpt.fail("curve-precommit-before-array",
                 "P_ENGFixingCurve_PreCommit is called before the quote-reference array is inserted — it "
                 "validates that array, so it checked nothing (run 5)", name)


def check_any_sql_file(name: str, raw: str, rpt: Report) -> None:
    """Checks for every file in 03-sql/, whatever its role."""
    code = strip_sql_comments(raw)
    if "&&" in code or "{{" in raw:
        rpt.fail("unresolved-substitution",
                 "the file still contains && or {{…}} placeholders — every value is resolved and "
                 "shown, with its source, before a reviewer sees it (run 3 hid its identity "
                 "constants behind &&QG6_*)", name)
    if re.search(r"\bif\s+1\s*=\s*0\b", code, re.I):
        rpt.fail("rollback-dead-code",
                 "IF 1 = 0 — unreachable code. The undo is a separate, runnable rollback file "
                 "(hard rule 11)", name)
    if "&" in raw and not re.search(r"^\s*set\s+define\s+off\b", raw, re.I | re.M):
        rpt.warn("define-not-off",
                 "an '&' appears (even in a comment: 'Deposit & Loan') and SET DEFINE OFF is absent — "
                 "SQL Developer will prompt for a substitution variable mid-script", name)



def role_of(file_name: str) -> str:
    n = file_name.lower()
    for role in ("rehearsal", "verify", "rollback"):
        if role in n:
            return role
    return "config"


def check_rendered(folder: Path, texts: dict[Path, str], rpt: Report) -> None:
    """Since 2026-09-24 the SQL is rendered from 03-sql/values.json by scripts/render_sql.py. Re-render and
    compare byte for byte: a hand edit, a stale file, or values changed without rendering again all FAIL.
    This is what makes the structure unbreakable: the validator no longer trusts a file it did not see made."""
    vfile = folder / render_sql.VALUES_FILE
    if not vfile.exists():
        if texts:
            rpt.fail("values-missing",
                     "SQL in 03-sql/ but no 03-sql/values.json — the SQL is rendered from it by "
                     "scripts/render_sql.py, never written by hand (runs 1–5 each broke the structure somewhere new)")
        return
    res = render_sql.render(folder)
    for code, where, msg in res.errors:
        rpt.fail("values-invalid", f"{code} — {where}: {msg}", "values.json")
    if res.errors:
        return
    for code, where, msg in res.warnings:
        rpt.warn("values-warning", f"{code} — {where}: {msg}", "values.json")
    on_disk = {p.name: t for p, t in texts.items()}
    for name, text in res.files.items():
        if name not in on_disk:
            rpt.fail("sql-not-rendered", f"{name} is missing — run python3 scripts/render_sql.py {folder}")
        elif on_disk[name].replace("\r\n", "\n") != text:
            a, b = on_disk[name].replace("\r\n", "\n").splitlines(), text.splitlines()
            line = next((i + 1 for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)) + 1)
            rpt.fail("sql-edited-by-hand",
                     f"{name} differs from what values.json renders to (first difference at line {line}). The SQL is "
                     "never edited: change values.json and run scripts/render_sql.py again", name)
    for name in sorted(set(on_disk) - set(res.files)):
        rpt.fail("sql-not-rendered",
                 f"{name} was not produced by scripts/render_sql.py from this values.json — archive or delete it", name)
    if res.nothing_to_render:
        rpt.info("nothing-to-render", res.nothing_to_render)


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

    # (identity constants are emitted as literals with provenance since
    #  2026-09-23 — run 3's substitution variables hid them from the reviewer)

    used_constants = {c for c in TIER1_IDENTITY_CONSTANTS[:3] if c in sql}
    if len(used_constants) == 1 and len(inserts) > 3:
        rpt.warn("identity-single-constant",
                 f"only one FK_OWNER_OBJ value ({used_constants.pop()}) across "
                 f"{len(inserts)} INSERTs — the walk spans three screens, so steps "
                 "3, 4 and 12 need different values", name)

    # --- hard rule 11: committing procedure vs rollback framing --------
    stmts_only = re.sub(r"'(?:[^']|'')*'", "''", low)     # a message that says ROLLBACK is not a ROLLBACK
    calls_committing = [p for p in COMMITTING_PROCEDURES if p in stmts_only]
    has_rollback = re.search(r"\browback\b|\brollback\b", stmts_only) is not None
    if calls_committing and has_rollback:
        rpt.fail("commit-vs-rollback",
                 f"script calls {calls_committing[0]} (which COMMITs) and also contains "
                 "ROLLBACK — the rollback is not an undo (hard rule 11)", name)
    if re.search(r"\bcommit\b", stmts_only) and "rollback" in stmts_only:
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
        "t_box_brproccal_s": "13", "t_box_engsetup_s": "14b",
    }
    for stmt in inserts:
        sl = stmt.lower()
        for table, step in parked_tables.items():
            if table in sl:
                rpt.fail("insert-for-no-insert-step",
                         f"INSERT into {table.upper()} — step {step} must never "
                         "produce a statement", name)

    # --- hard rule 13: intra-config FKs are variables, never literals ----
    # T_BOX_ENGCONF_S.FK_CURVEMAN/FK_CURVEACC point at the curve THIS script
    # creates. A literal there is a GBO PK carried into a BOX column.
    for stmt in inserts:
        if "t_box_engconf_s" not in stmt.lower():
            continue
        cols, vals = insert_columns_and_values(stmt)
        for col in ("fk_curveman", "fk_curveacc"):
            if col not in cols:
                continue
            v = vals[cols.index(col)] if len(vals) == len(cols) else ""
            if v.strip().lower() == "null":
                rpt.fail("curve-fk-null",
                         f"{col.upper()} = NULL in the INSERT into T_BOX_ENGCONF_S — the column is NOT "
                         "NULL (Q-02, DDL), so this raises ORA-01400. Allocate the curve's PK before "
                         "the header and insert it directly (fe-walk-notes.md, Steps 2–4)", name)
            elif re.fullmatch(r"-?\d+(\.\d+)?", v.strip()):
                rpt.fail("curve-fk-literal",
                         f"{col.upper()} = {v.strip()} is a literal in an INSERT into "
                         "T_BOX_ENGCONF_S — an intra-config FK must be the F___SEQUENCE "
                         "variable of the curve this script creates, never a mined PK "
                         "(hard rule 13)", name)

    # --- the curve must be referenced by something ----------------------
    if re.search(r"insert\s+into\s+[\w.]*t_box_engfcurve_s", low):
        m = re.search(r"(\w+)\s*:=\s*[\w.]*f___sequence\s*\(\s*'t_box_engfcurve_s'", low)
        var = m.group(1) if m else None
        linked = bool(var) and bool(
            re.search(r"update\s+[\w.]*t_box_engconf_s[\s\S]{0,400}?" + re.escape(var), low)
        )
        if var and not linked:           # allocate-first: the header INSERT carries the variable
            for stmt in inserts:
                if re.search(r"insert\s+into\s+[\w.]*t_box_engconf_s\b", stmt, re.I):
                    cols, vals = insert_columns_and_values(stmt)
                    if "fk_curveman" in cols and len(cols) == len(vals) and \
                            vals[cols.index("fk_curveman")].strip().lower() == var:
                        linked = True
        if not linked:
            rpt.fail("orphan-curve",
                     "a curve is INSERTed into T_BOX_ENGFCURVE_S but the header's FK_CURVEMAN "
                     "is never its variable — the configuration points at no curve this run "
                     "created (allocate the curve's PK first; fe-walk-notes.md, Steps 2–4)", name)

    # --- identity columns come from Q-G6, not sampled from the target ---
    # Any SELECT … INTO that reads FK_OWNER_OBJ/FK_EXTENSION out of a table is
    # sampling data. ROWNUM=1, MIN(PK), GROUP BY/HAVING — same defect, different
    # dress. The declared identity comes from the metamodel (Q-G6).
    for m in re.finditer(r"select\b[^;]{0,300}?\binto\b[^;]{0,300}?;", low):
        frag = m.group(0)
        if re.search(r"fk_owner_obj|fk_extension", frag) and re.search(r"\bfrom\b", frag):
            how = ("WHERE ROWNUM = 1" if "rownum" in frag else
                   "GROUP BY / HAVING" if "group by" in frag else
                   "MIN()/MAX()" if re.search(r"\b(min|max)\s*\(", frag) else
                   "a runtime SELECT")
            rpt.fail("identity-sampled-from-target",
                     f"FK_OWNER_OBJ / FK_EXTENSION sourced by {how} from a table — that "
                     "samples existing data instead of reading the declared identity. "
                     "Resolve them with Q-G6 and emit the constants (hard rule 9)", name)
            break

    # --- pre-commit procedures are called by their recorded name --------
    for m in re.finditer(r"([\w$]+)\s*\.\s*(p_check_val_curves_precommit|"
                         r"p_engfixingcurve_precommit)\s*\(", low):
        pkg = m.group(1)
        if pkg not in KNOWN_PRECOMMIT_PACKAGES:
            rpt.fail("precommit-wrong-package",
                     f"pre-commit called as {pkg.upper()}.{m.group(2).upper()} — the "
                     f"recorded package is {'/'.join(sorted(KNOWN_PRECOMMIT_PACKAGES)).upper()}. "
                     "An invented schema or package qualifier is a fabricated literal "
                     "(hard rule 1) and the call will fail", name)

    # --- the row count a step declares must be the count it emits -------
    # Run 2 declared a quote-reference array and emitted one row of 38. Run 3
    # emits N rows from ONE statement inside a loop, which is correct and must
    # not be flagged — so when a loop is present, count what the loop iterates.
    for m in re.finditer(r"^[ \t]*--[ \t]*step[ \t]+(\d+[a-z]?)\b", raw, re.M | re.I):
        step = m.group(1)
        table = TARGET_TABLE_BY_STEP.get(step.lower())
        if not table:
            continue
        nxt_h = re.search(r"^[ \t]*--[ \t]*step[ \t]+\d", raw[m.end():], re.M | re.I)
        block = raw[m.end(): m.end() + min(500, nxt_h.start() if nxt_h else 500)]
        cm = (re.search(r"runtime enumeration is\s+(\d+)", block, re.I)
              or re.search(r"(\d+)\s*rows?\b", block, re.I))
        if not cm:
            rpt.warn("step-no-row-count",
                     f"step {step}'s header states no row count — the count and why "
                     "that count is what a reviewer checks first", name)
            continue
        declared = int(cm.group(1))

        # Where does this step's INSERT live, and is it inside a loop?
        nxt = re.search(r"^[ \t]*--[ \t]*step[ \t]+\d", raw[m.end():], re.M | re.I)
        body = raw[m.end(): m.end() + (nxt.start() if nxt else len(raw))]
        if re.search(r"\bloop\b", body, re.I):
            actual = loop_iteration_count(body, raw)
            if actual is None:
                rpt.info("step-loop-count-unknown",
                         f"step {step} emits {declared} row(s) from a loop whose size "
                         "could not be counted mechanically — check it by eye", name)
                continue
        else:
            actual = sum(1 for s in inserts if table.lower() in s.lower())

        if actual != declared:
            rpt.fail("step-row-count-mismatch",
                     f"step {step} declares {declared} row(s) for {table} but the file "
                     f"produces {actual}. A set that shrinks between the finding and the "
                     "SQL is a silent enumeration loss (hard rule 8)", name)

    # --- every instrument written must be in the approved scope ---------
    # Run 3 emitted step-7 exception rows for six instruments gate 0c never
    # approved. Scope expansion is silent: the rows insert cleanly.
    if APPROVED_INSTRUMENTS:
        approved = {evidence_to_sql.norm(v) for v in APPROVED_INSTRUMENTS}
        for step, block in step_blocks(raw):
            if step not in INSTRUMENT_KEYED_STEPS:
                continue
            code_b = strip_sql_comments(block)
            seen = set()
            for stmt in insert_statements(code_b):          # FK_INSTRUMENT literals in INSERTs
                cols, vals = insert_columns_and_values(stmt)
                if "fk_instrument" in cols and len(cols) == len(vals):
                    seen.add(vals[cols.index("fk_instrument")].strip())
            seen.update(re.findall(r"(-?\d+(?:\.\d+)?)\s+as\s+fk_instrument\b", code_b, re.I))   # cursor rows
            for lm in re.finditer(r"fk_instrument\s+in\s*\(([^)]*)\)", code_b, re.I):             # IN lists
                seen.update(x.strip() for x in lm.group(1).split(","))
            for lm in re.finditer(r"odcinumberlist\s*\(([^)]*)\)", code_b, re.I):                   # 2026-09-23 shape
                if re.search(r"instrument", code_b[max(0, lm.start() - 80): lm.start()], re.I):
                    seen.update(x.strip() for x in lm.group(1).split(","))
            stray = sorted(x for x in seen if re.fullmatch(r"\d+\.\d+", x)
                           and evidence_to_sql.norm(x) not in approved)
            if stray:
                rpt.fail("instrument-out-of-scope",
                         f"step {step} writes instrument PK(s) {', '.join(stray)} which gate 0c did not approve — "
                         "silent scope expansion, the failure this gate exists to prevent", name)

    # --- every walk step opens with a header block ----------------------
    if inserts:
        headers = re.findall(r"^\s*--\s*step\s+\d+[a-z]?\b", raw_low, re.M)
        if not headers:
            rpt.fail("sql-no-step-headers",
                     f"{len(inserts)} INSERT(s) and no `-- STEP n` header block anywhere. "
                     "Every walk step opens with What / Source / Findings / Depends on / "
                     "If wrong — see the charter's Outputs", name)
        elif len(headers) < 2 and len(inserts) > 2:
            rpt.warn("sql-few-step-headers",
                     f"{len(inserts)} INSERT(s) but only {len(headers)} step header(s) — "
                     "one block per walk step, one for a repeated set", name)
        elif headers and not re.search(r"--\s*if wrong", raw_low):
            rpt.warn("sql-header-no-consequence",
                     "step headers present but no `If wrong` line — that is the line a "
                     "reviewer uses to decide where to look when a load fails", name)

    # --- 2026-09-23 BOX FE expert review: checks for each point ----------
    if inserts:
        check_expert_review_rules(path, name, raw, sql, low, inserts, rpt)
        check_run4_rules(name, sql, inserts, raw, rpt)
        check_run5_rules(name, sql, inserts, raw, rpt)


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

    for line in text.splitlines():
        if re.search(r"\[confirmed[^\]]*\][^|]*\b(approv|decid|decision|waiv|sme\b)", line, re.I):
            rpt.fail("decision-tagged-confirmed",
                     "a decision tagged [confirmed: …] — that tag is for query results; a person's decision is "
                     f"[stated: <name>, <role>, <date>] (run 4, step 6): {line.strip()[:90]!r}", name)
            break

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
    else:
        itext = inputs.read_text(encoding="utf-8", errors="replace")
        for key in INPUT_NAMES:
            im = re.search(rf"\b{key}\b[`*\s:|=]*(-?\d+(?:\.\d+)?)", itext)
            if im:
                RUN_INPUTS[key] = im.group(1)
        bm = re.search(r"^\s*BOOK_LABELS?\b[`*\s:|=]*([^\n]*)", itext, re.M)
        if bm:
            RUN_TEXT_INPUTS["BOOK_LABELS"] = bm.group(1)
        tm = re.search(r"\bQUOTE_REF_COLUMN\b[`*\s:|=]*([A-Za-z_]\w*)", itext)
        if tm:
            RUN_TEXT_INPUTS["QUOTE_REF_COLUMN"] = tm.group(1)
        m = re.search(r"APPROVED_INSTRUMENTS\b[`*\s:|=]*(\d[0-9., ]*)", itext, re.I)
        if m:
            APPROVED_INSTRUMENTS.update(
                v.strip() for v in m.group(1).split(",") if v.strip())
        else:
            rpt.warn("no-approved-instruments",
                     "00-inputs.md states no `APPROVED_INSTRUMENTS:` line, so the "
                     "instrument-scope check cannot run. Gate 0c's answer belongs in "
                     "the input contract as PKs, not only as instrument names")

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
        texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in sql_files}
        check_rendered(folder, texts, rpt)
        for p, t in texts.items():
            check_any_sql_file(p.name, t, rpt)
            if role_of(p.name) != "config":
                continue                  # verify, rollback, rehearsal: no INSERT-oriented checks
            check_sql(p, t, rpt)

        # three files, one job each (2026-09-23)
        config_files = [p for p, t in texts.items()
                        if insert_statements(strip_sql_comments(t)) and role_of(p.name) == "config"]
        if config_files:
            verify = [p for p in texts if role_of(p.name) == "verify"]
            rollback = [p for p in texts if role_of(p.name) == "rollback"]
            if not verify:
                rpt.fail("verify-script-missing",
                         "config SQL but no *-verify.sql — the expert asked for the auth code to be "
                         "part of the verification script; run 3 had none (fe-walk-notes.md)")
            else:
                vt = " ".join(strip_sql_comments(texts[p]).lower() for p in verify)
                if not re.search(r"\bfrom\s+gom_glb_sys\.t__core_info_s\b", vt):
                    rpt.fail("verify-no-auth-check",
                             "the verification script does not check the auth code of the rows "
                             "created (V1)")
                cfg_low = " ".join(strip_sql_comments(texts[p]).lower() for p in config_files)
                for p in verify:
                    check_verify_file(p.name, texts[p], cfg_low, rpt)
                if any("t_box_englkfc_x" in texts[p].lower() for p in config_files) and "minus" not in vt:
                    rpt.warn("verify-no-quote-set-check",
                             "no MINUS in the verification script — step 4's array is compared "
                             "with GBO's both ways (V4)")
            decided = [t for t in ("t_box_engaccrconf_s", "t_box_conf_by_book_s", "t_box_errors_fe_s",
                                   "t_box_engdays_matured_s")
                       if any(re.search(r"insert\s+into\s+[\w.]*" + t, strip_sql_comments(texts[p]), re.I)
                              for p in config_files)]
            if decided and not (folder / "00-decisions.md").exists():
                rpt.fail("decisions-log-missing",
                         f"SQL for decided steps ({', '.join(d.upper() for d in decided)}) but no "
                         "00-decisions.md — every decision card answered is a row: decision, value, "
                         "name, role, date, evidence")
            if not rollback or not any(re.search(r"\bdelete\s+from\b", texts[p], re.I)
                                       for p in rollback):
                rpt.fail("rollback-script-missing",
                         "config SQL but no runnable *-rollback.sql with DELETEs — the config's "
                         "last procedure COMMITs, so these DELETEs are the only undo (hard rule 11)")

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
            # Per step, not per file: a run with gate 0c open legitimately emits
            # steps 1–5 while 6+ wait. What is never legitimate is an INSERT for
            # the step that is waiting.
            sql_text = "\n".join(strip_sql_comments(p.read_text(encoding="utf-8", errors="replace"))
                                 for p in sql_files).upper()
            for line in ftext.splitlines():
                m = re.match(r"\s*\|\s*(\d+[A-Z]?)\s*\|", line)
                if not m:
                    continue
                step = m.group(1).lower()
                table = TARGET_TABLE_BY_STEP.get(step)
                if not table or not re.search(r"INSERT\s+INTO\s+[\w.]*" + table + r"\b", sql_text):
                    continue
                if "SME_DECISION_REQUIRED" in line:
                    rpt.fail("sql-with-open-sme-decision",
                             f"step {step} is SME_DECISION_REQUIRED but an INSERT into {table} "
                             "exists — no statement may be emitted for a decision nobody has made")
                elif "EVIDENCE_REQUIRED" in line:
                    if all_draft:
                        rpt.info("draft-sql-pending-evidence",
                                 f"step {step} EVIDENCE_REQUIRED with draft-marked SQL — the "
                                 "designed state of a deferred-verification run")
                    else:
                        rpt.fail("unmarked-sql-pending-evidence",
                                 f"step {step} is EVIDENCE_REQUIRED but an INSERT into {table} "
                                 "exists and the SQL is not marked as a draft")
            # The inverse, which run 2 produced: a step declared ready and then
            # not emitted. If the status says releasable, the SQL must exist; if
            # the SQL is absent, the status is overstating what the run did.
            all_sql = sql_text            # comment-stripped: a commented example is not SQL
            for line in ftext.splitlines():
                m = re.match(r"\s*\|\s*(\d+[A-Z]?)\s*\|", line)
                if not m:
                    continue
                step = m.group(1).lower()
                table = TARGET_TABLE_BY_STEP.get(step)
                if not table or step in NO_INSERT_STEPS:
                    continue
                ready = any(s in line for s in ("PROPOSED", "DERIVED"))
                if ready and not re.search(r"INSERT\s+INTO\s+[\w.]*" + table + r"\b", all_sql):
                    rpt.fail("ready-step-without-sql",
                             f"step {step} is statused ready but no INSERT into "
                             f"{table} exists. Either emit it, or say what still "
                             "blocks it — a status that overstates the run is worse "
                             "than a blocked step honestly reported")
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
