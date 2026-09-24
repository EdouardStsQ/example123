#!/usr/bin/env python3
"""
render_sql.py - build a run's four SQL files from the templates and ONE values file.

    python3 scripts/render_sql.py runs/NY_SCH/tier2-pre/

Why this exists. Five runs hand-wrote the SQL from the templates, and each one broke its structure
somewhere new: a cursor field that did not exist, a procedure inside VALUES, guards that could not
fire, a list declared and never used. The agent's judgement is needed for the VALUES and the
DECISIONS, not for PL/SQL syntax. So the agent writes `03-sql/values.json` (every value with its
source) and this script writes the SQL. The structure lives in the templates and cannot drift.

Reads (all inside RUN_FOLDER):
    03-sql/values.json                               every value, each with its source
    00-inputs.md                                     the run inputs (cross-checked, must agree)
    00-decisions.md                                  every decision a value cites (name, role, date)
    02-findings.md                                   each step's status (must agree with values.json)
    01-evidence/Q-04c-quote-ref-column-gbo.csv       step 4's set (column FK_BS)
    01-evidence/Q-04c-quote-ref-column-counts.csv    step 4's counts (N_ROWS, N_FK_BS, N_RESOLVED)
    01-evidence/Q-06c-accrual-exceptions-emit.csv    step 7's rows, all branches

Writes (03-sql/), and nothing else:
    <BRANCH>-<env>-rehearsal.sql   the config block ending in ROLLBACK - run it first
    <BRANCH>-<env>-config.sql      the same block ending in the committing Config pre-commit
    <BRANCH>-<env>-verify.sql      read-only checks, each with its expected result
    <BRANCH>-<env>-rollback.sql    the only undo
    render-report.md               what was rendered, from what, and what was filtered out

Then it runs scripts/validate_run_output.py on the run folder and exits with its code.
Any problem with the values stops it BEFORE anything is written: exit 1, each problem listed with
the JSON path it is about. Nothing here is judgement - every refusal names the fix.

Exit codes: 0 rendered and validator clean · 1 values refused, or validator FAIL · 2 bad invocation
            3 nothing to render (steps 2-5 not all ready - the report says which)
Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TPL = ROOT / "agents/sigom-box-fe-configs-agent/templates"
sys.path.insert(0, str(HERE))
import evidence_to_sql  # noqa: E402  (the one CSV reader the validator also uses)

VALUES_FILE = "03-sql/values.json"
Q04C = "01-evidence/Q-04c-quote-ref-column-gbo.csv"
Q04C_COUNTS = "01-evidence/Q-04c-quote-ref-column-counts.csv"
Q06C = "01-evidence/Q-06c-accrual-exceptions-emit.csv"

STATUSES = {"CONFIRMED_PRESENT", "CONFIRMED_ABSENT", "PROPOSED", "DERIVED", "SME_DECISION_REQUIRED",
            "EXTERNAL_CHECK_REQUIRED", "EVIDENCE_REQUIRED", "NOT_BRANCH_SCOPED"}
EMIT = {"PROPOSED", "DERIVED"}
HELD = {"SME_DECISION_REQUIRED", "EXTERNAL_CHECK_REQUIRED", "EVIDENCE_REQUIRED"}
WALK = ["1", "2", "3", "4", "4b", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14a", "14b"]
CORE = ["2", "3", "4", "5"]                  # all emitted, or no SQL at all
OPTIONAL = ["6", "7", "11", "12", "14a"]     # each emitted when ready; held -> DRAFT
DECIDED = {"6", "11", "12", "14a"}           # values a person signs: need a decision
FIXED_STATUS = {                             # steps this renderer supports in one state only
    "1": ({"CONFIRMED_ABSENT"}, "a configuration already exists for the branch: adapting it is a human "
                                "decision this renderer does not support (charter, step 1)"),
    "4b": ({"CONFIRMED_ABSENT"}, "Question G closed 2026-09-22; reopening it needs repo support first"),
    "8": ({"CONFIRMED_ABSENT"}, "step-8 rows are not supported by the templates; ask for repo support"),
    "9": ({"CONFIRMED_ABSENT"}, "Question G closed 2026-09-22; reopening it needs repo support first"),
    "10": ({"CONFIRMED_ABSENT"}, "Question G closed 2026-09-22; reopening it needs repo support first"),
    "14b": ({"NOT_BRANCH_SCOPED"}, "T_BOX_ENGSETUP_S has nothing to configure (BOX FE expert, point 7)"),
}

IDENTITY = [  # key, placeholder, object, kind
    ("owner_engconf", "OWNER_ENGCONF", "BOX_ENG_Config", "owner"),
    ("ext_engconf_x", "EXT_ENGCONF_X", "apBranch", "ext"),
    ("ext_engaccrconf", "EXT_ENGACCRCONF", "amAccrualConfig", "ext"),
    ("ext_config_accrual", "EXT_CONFIG_ACCRUAL", "BOX_ENG_Config_Accrual", "ext"),
    ("ext_conf_by_book", "EXT_CONF_BY_BOOK", "amConfigByBook", "ext"),
    ("owner_engfcurve", "OWNER_ENGFCURVE", "BOX_ENG_FixingCurve", "owner"),
    ("ext_englkfc", "EXT_ENGLKFC", "apQuoteReference", "ext"),
    ("owner_errors_fe", "OWNER_ERRORS_FE", "BOX - Limit Error Assign", "owner"),
    ("owner_days_matured", "OWNER_DAYS_MATURED", "BOX_ENG_Days_Matured", "owner"),
]

STEP6_COLS = ["FK_FEEFIRSTDAYSEL", "FK_INTFIRSTDAYSEL", "INTCOMMONBASIS", "BYTRIGGER",
              "BYRESIDUAL", "INTERVAL", "FK_BASIS", "FK_MDRBASIS"]
STEP6_NOT_NULL = {"FK_FEEFIRSTDAYSEL", "FK_INTFIRSTDAYSEL", "INTCOMMONBASIS", "BYTRIGGER"}
STEP7_COLS = ["FK_INSTRUMENT", "FK_STRATEGY", "FK_INSTRTYPE", "CRITERIAL"]

Q_G3D_COLUMNS = "01-evidence/Q-G3d-columns.csv"
# Every column the four files write or read, per table - checked against Q-G3d (e) before rendering, so a
# missing column (ORA-00904) or an unwritten NOT NULL column (ORA-01400) is a refusal here, not a surprise
# at apply time.
WRITES = {
    "T_BOX_ENGCONF_S": ("2", ["PK", "FK_OWNER_OBJ", "DESCRIPTION", "FK_CALENDAR", "FK_CURRENCY", "FK_CURVEMAN",
                              "FK_CURVEACC", "FK_SOURCE_FRONT", "FK_SOURCE_BACK"]),
    "T_BOX_ENGFCURVE_S": ("3", ["PK", "FK_OWNER_OBJ", "DESCRIPTION", "FK_CURRENCY"]),
    "T_BOX_ENGLKFC_X": ("4", ["PK", "FK_OWNER_OBJ", "FK_EXTENSION", "FK_PARENT", "FK_BS"]),
    "T_BOX_ENGCONF_X": ("5", ["PK", "FK_OWNER_OBJ", "FK_EXTENSION", "FK_PARENT", "FK_BS"]),
    "T_BOX_ENGACCRCONF_S": ("6", ["PK", "FK_OWNER_OBJ", "FK_PARENT", "FK_EXTENSION", "FK_INSTRUMENT",
                                  "FK_FEEFIRSTDAYSEL", "FK_INTFIRSTDAYSEL", "INTCOMMONBASIS", "BYTRIGGER",
                                  "BYRESIDUAL", "INTERVAL", "FK_BASIS", "FK_MDRBASIS"]),
    "T_BOX_CONFIG_ACCRUAL_S": ("7", ["PK", "FK_OWNER_OBJ", "FK_PARENT", "FK_EXTENSION", "CRITERIAL", "FK_BRANCH",
                                     "FK_INSTRUMENT", "FK_STRATEGY", "FK_INSTRTYPE"]),
    "T_BOX_FIXING_BY_INSTR_S": ("8", ["FK_PARENT"]),
    "T_BOX_CONF_BY_BOOK_S": ("11", ["PK", "FK_OWNER_OBJ", "FK_PARENT", "FK_EXTENSION", "FK_BRANCH", "FK_INSTRUMENT",
                                    "FK_LABEL"]),
    "T_BOX_ERRORS_FE_S": ("12", ["PK", "FK_OWNER_OBJ", "FK_BRANCH", "FK_INSTRUMENT", "LIMIT_ERRORS"]),
    "T_BOX_ENGDAYS_MATURED_S": ("14a", ["PK", "FK_OWNER_OBJ", "DDATE", "FK_INSTRUMENT", "NUM_DAYS"]),
}
ALWAYS_READ = {"T_BOX_ENGACCRCONF_S": ["FK_PARENT", "FK_INSTRUMENT"], "T_BOX_CONFIG_ACCRUAL_S": ["FK_PARENT"],
               "T_BOX_FIXING_BY_INSTR_S": ["FK_PARENT"], "T_BOX_CONF_BY_BOOK_S": ["FK_PARENT", "FK_BRANCH"],
               "T_BOX_ERRORS_FE_S": ["FK_BRANCH"]}
DDATE_EXPRESSIONS = {"SYSDATE": "SYSDATE", "TRUNC(SYSDATE)": "TRUNC(SYSDATE)"}

NUM_RE = re.compile(r"-?\d+(\.\d+)?")
SOURCE_RE = re.compile(r"Q-[A-Za-z0-9]|00-inputs|decision\s+\d+|\[stated|\[confirmed|constant", re.I)
PLACEHOLDER_RE = re.compile(r"^\s*<|<[A-Za-z_][^>]*>|\bTODO\b|\bTBD\b|\?\?\?|\bFILL\b", re.I)
IDENT_RE = re.compile(r"[A-Za-z][A-Za-z0-9_$#]{0,29}")
BAD_DECIDERS = {"", "user", "the user", "operator", "the operator", "me", "tbd", "n/a", "na", "-", "unknown",
                "devin", "agent", "claude"}

OUTPUT_ROLES = ["rehearsal", "config", "verify", "rollback"]


# ------------------------------------------------------------------------------------------------
@dataclass
class Result:
    files: dict[str, str] = field(default_factory=dict)     # file name -> content
    errors: list[tuple[str, str, str]] = field(default_factory=list)   # (code, path, message)
    warnings: list[tuple[str, str, str]] = field(default_factory=list)
    report: list[str] = field(default_factory=list)
    base: str = ""
    nothing_to_render: str = ""

    def err(self, code: str, path: str, msg: str) -> None:
        self.errors.append((code, path, msg))

    def warn(self, code: str, path: str, msg: str) -> None:
        self.warnings.append((code, path, msg))

    def codes(self) -> set[str]:
        return {c for c, _, _ in self.errors}


def canon(v) -> str | None:
    """Canonical numeric literal, or None when v is not a plain number (bool, text, NaN...)."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, Decimal):
        v = str(v)
    if isinstance(v, (int, float)):
        v = repr(v) if isinstance(v, float) else str(v)
    if not isinstance(v, str):
        return None
    v = v.strip()
    if not NUM_RE.fullmatch(v):
        return None
    try:
        return format(Decimal(v).normalize(), "f")
    except InvalidOperation:
        return None


def ascii_comment(s) -> str:
    """Text safe inside a -- comment: one line, ASCII, no template braces."""
    s = str(s)
    for a, b in (("—", "-"), ("–", "-"), ("→", "->"), ("×", "x"), ("’", "'"),
                 ("“", '"'), ("”", '"'), ("≤", "<="), ("≥", ">=")):
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace("{{", "{ {").replace("}}", "} }").replace("@@", "@ @")


def sql_text(s: str) -> str:
    """A string literal. ASCII -> '...'. Anything else -> UNISTR('...') so the file itself stays ASCII
    and no editor's encoding guess can change what is written."""
    if all(32 <= ord(c) < 127 for c in s):
        return "'" + s.replace("'", "''") + "'"
    out = []
    for c in s:
        o = ord(c)
        if c == "\\":
            out.append("\\005C")
        elif c == "'":
            out.append("''")
        elif 32 <= o < 127:
            out.append(c)
        else:
            b = c.encode("utf-16-be")
            out.extend("\\%02X%02X" % (b[i], b[i + 1]) for i in range(0, len(b), 2))
    return "UNISTR('" + "".join(out) + "')"


# ------------------------------------------------------------------------------------------------
# Reading the run folder
# ------------------------------------------------------------------------------------------------

def read_inputs(path: Path) -> dict[str, str]:
    """00-inputs.md, tolerant of `NAME: value`, **NAME**: value and | `NAME` | value | shapes."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    t = path.read_text(encoding="utf-8", errors="replace")
    for key in ("BRANCH_PK", "REFERENCE_BRANCH_PK", "SOURCE_FRONT", "DUMMY_BOOK_LABEL", "TARGET_AUTH_CODE",
                "TARGET_PK_FRACTION"):
        m = re.search(rf"(?<![A-Z_]){key}\b[`*\s:|=]*(-?\d+(?:\.\d+)?)", t)
        if m:
            out[key] = m.group(1)
    m = re.search(r"(?<![A-Z_])APPROVED_INSTRUMENTS\b[`*\s:|=]*(\d[0-9., ]*)", t)
    if m:
        out["APPROVED_INSTRUMENTS"] = m.group(1)
    m = re.search(r"(?<![A-Z_])QUOTE_REF_COLUMN\b[`*\s:|=]*([A-Za-z_]\w*)", t)
    if m:
        out["QUOTE_REF_COLUMN"] = m.group(1)
    m = re.search(r"^\s*\W*BOOK_LABELS?\b[`*\s:|=]*([^\n]*)", t, re.M)
    if m:
        out["BOOK_LABELS"] = m.group(1)
    return out


def read_table(path: Path) -> list[dict[str, str]]:
    """A markdown table as dicts keyed by lower-cased header. First table with a header row wins."""
    if not path.exists():
        return []
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    rows, header = [], None
    for ln in lines:
        if not ln.startswith("|"):
            if header and rows:
                break
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if header is None:
            header = [re.sub(r"[`*]", "", c).strip().lower() for c in cells]
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def read_decisions(path: Path) -> dict[int, dict[str, str]]:
    """Rows of the decisions table by number (first column). Column names are matched loosely:
    name / decided by / who, role / authority, date."""
    out = {}
    for r in read_table(path):
        cells = list(r.values())
        m = re.search(r"\d+", cells[0] if cells else "")
        if not m:
            continue
        pick = lambda *keys: next((r[k] for k in r for want in keys if k.startswith(want)), "")
        out[int(m.group())] = {**r, "name": pick("name", "decided by", "who", "person"),
                               "role": pick("role", "authority"), "date": pick("date")}
    return out


def read_findings_statuses(path: Path) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    if not path.exists():
        return out
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*\|\s*`?(\d+[a-zA-Z]?)`?\s*\|", ln)
        if not m:
            continue
        step = m.group(1).lower()
        found = {s for s in STATUSES if re.search(rf"\b{s}\b", ln.upper())}
        out.setdefault(step, set()).update(found)
    return out


# ------------------------------------------------------------------------------------------------
# Validating values.json - every refusal names its JSON path and its fix
# ------------------------------------------------------------------------------------------------

class V:
    """Accessors that record a problem instead of raising, so one pass reports everything."""

    def __init__(self, res: Result, decisions: dict[int, dict[str, str]]):
        self.res, self.decisions, self.cited = res, decisions, set()

    def node(self, parent, key, path, kind=dict, required=True):
        if not isinstance(parent, dict) or key not in parent:
            if required:
                self.res.err("values-missing-field", f"{path}.{key}" if path else key, "required field is missing")
            return None
        v = parent[key]
        if kind and not isinstance(v, kind):
            self.res.err("values-wrong-type", f"{path}.{key}", f"expected {kind.__name__}, got {type(v).__name__}")
            return None
        return v

    def source(self, src, path) -> str:
        if not isinstance(src, str) or not src.strip():
            self.res.err("values-no-source", path, "every value carries a non-empty `source`")
            return ""
        if not SOURCE_RE.search(src):
            self.res.err("values-no-source", path, f"source {src!r} names no query (Q-...), no 00-inputs.md "
                                                   "input and no decision (decision N) - say where the value came from")
        for m in re.finditer(r"decision\s+(\d+)", src, re.I):
            self.decision(int(m.group(1)), path)
        return src.strip()

    def decision(self, n: int, path: str) -> None:
        self.cited.add(n)
        d = self.decisions.get(n)
        if d is None:
            self.res.err("decision-missing", path, f"decision {n} is cited but has no row in 00-decisions.md")
            return
        name, role, date = (d.get("name", ""), d.get("role", ""), d.get("date", ""))
        if name.strip().lower() in BAD_DECIDERS or name.strip().startswith("<") or \
                role.strip().lower() in BAD_DECIDERS or role.strip().startswith("<"):
            self.res.err("decision-incomplete", path, f"decision {n} in 00-decisions.md names no person and role "
                                                      f"(name {name!r}, role {role!r}) - [stated: <name>, <role>, <date>]")
        if not re.search(r"\d{4}-\d{2}-\d{2}", date):
            self.res.err("decision-incomplete", path, f"decision {n} has no date (YYYY-MM-DD): {date!r}")

    def leaf_num(self, parent, key, path, *, positive=True, integer=False) -> tuple[str | None, str]:
        n = self.node(parent, key, path)
        if n is None:
            return None, ""
        p = f"{path}.{key}"
        src = self.source(n.get("source"), p + ".source")
        c = canon(n.get("value"))
        if c is None:
            self.res.err("values-not-a-number", p + ".value", f"{n.get('value')!r} is not a number")
            return None, src
        if positive and Decimal(c) <= 0:
            self.res.err("values-not-positive", p + ".value", f"{c} must be > 0")
        if integer and "." in c:
            self.res.err("values-not-integer", p + ".value", f"{c} must be a whole number")
        return c, src

    def leaf_text(self, parent, key, path) -> tuple[str | None, str]:
        n = self.node(parent, key, path)
        if n is None:
            return None, ""
        p = f"{path}.{key}"
        src = self.source(n.get("source"), p + ".source")
        v = n.get("value")
        if not isinstance(v, str) or not v.strip():
            self.res.err("values-empty-text", p + ".value", "a non-empty text value is required")
            return None, src
        if v != v.strip() or any(ord(c) < 32 for c in v):
            self.res.err("values-bad-text", p + ".value", "no leading/trailing spaces or control characters - "
                                                          "copy the mined text exactly")
        if len(v) > 255:
            self.res.err("values-bad-text", p + ".value", f"{len(v)} characters; over 255")
        return v, src


def walk_placeholders(obj, path, res: Result) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not str(k).startswith("_"):
                walk_placeholders(v, f"{path}.{k}" if path else k, res)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk_placeholders(v, f"{path}[{i}]", res)
    elif isinstance(obj, str) and PLACEHOLDER_RE.search(obj):
        res.err("values-placeholder", path, f"{obj!r} is a placeholder, not a value")


def instrument_list(v: V, parent, key, path, approved_names) -> list[str]:
    lst = v.node(parent, key, path, kind=list)
    out = []
    for i, item in enumerate(lst or []):
        p = f"{path}.{key}[{i}]"
        if not isinstance(item, dict):
            v.res.err("values-wrong-type", p, "expected {value, source}")
            continue
        v.source(item.get("source"), p + ".source")
        c = canon(item.get("value"))
        if c is None:
            v.res.err("values-not-a-number", p + ".value", f"{item.get('value')!r} is not a number")
            continue
        if approved_names is not None and c not in approved_names:
            v.res.err("instrument-not-approved", p + ".value", f"{c} is not an approved instrument")
        out.append(c)
    return out


# ------------------------------------------------------------------------------------------------
# Rendering
# ------------------------------------------------------------------------------------------------

def apply_sections(text: str, keys: set[str], res: Result, tpl_name: str) -> str:
    def on(expr: str) -> bool:
        return any(all((k[1:] not in keys) if k.startswith("!") else (k in keys) for k in alt.split("&"))
                   for alt in expr.split("|"))
    out, stack = [], []
    for ln in text.splitlines(keepends=True):
        if ln.startswith("--#"):
            continue
        m = re.match(r"\s*--\s*@@(BEGIN|END)\s+(\S+)\s*$", ln)
        if m:
            if m.group(1) == "BEGIN":
                stack.append(m.group(2))
            else:
                if not stack or stack[-1] != m.group(2):
                    res.err("template-broken", tpl_name, f"@@END {m.group(2)} does not close {stack[-1:] or 'anything'}")
                    return ""
                stack.pop()
            continue
        if all(on(s) for s in stack):
            out.append(ln)
    if stack:
        res.err("template-broken", tpl_name, f"unclosed @@BEGIN {stack}")
    return "".join(out)


def fill(text: str, subs: dict[str, str], res: Result, name: str) -> str:
    missing = set()

    def rep(m):
        k = m.group(1)
        if k not in subs:
            missing.add(k)
            return m.group(0)
        return subs[k]
    out = re.sub(r"\{\{(\w+)\}\}", rep, text)
    if missing:
        res.err("template-broken", name, f"no value for placeholder(s) {sorted(missing)}")
    return out


def sql_ident(col: str) -> str:
    """INTERVAL is an Oracle keyword (not reserved): quoted, in upper case, it is the same column and cannot
    be read as the start of an interval literal."""
    return f'"{col}"' if col in {"INTERVAL"} else col


def pk_block(seq: str, table: str, indent: str = "  ") -> str:
    return f"{indent}v_pk := {seq}('{table}','X');  chk_pk(v_pk, '{table}');\n"


def render(folder: Path) -> Result:
    res = Result()
    folder = Path(folder)
    vpath = folder / VALUES_FILE
    if not vpath.exists():
        res.err("values-file-missing", VALUES_FILE, "no values file - write it from "
                "agents/sigom-box-fe-configs-agent/templates/values.example.json")
        return res
    raw_bytes = vpath.read_bytes()
    try:
        data = json.loads(raw_bytes.decode("utf-8-sig"), parse_float=Decimal)   # 35000126.65 stays exact
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        res.err("values-not-json", VALUES_FILE, f"not valid JSON: {e}")
        return res
    if not isinstance(data, dict):
        res.err("values-not-json", VALUES_FILE, "the top level must be an object")
        return res
    walk_placeholders(data, "", res)

    inputs = read_inputs(folder / "00-inputs.md")
    decisions = read_decisions(folder / "00-decisions.md")
    findings = read_findings_statuses(folder / "02-findings.md")
    v = V(res, decisions)
    if not (folder / "00-inputs.md").exists():
        res.err("inputs-missing", "00-inputs.md", "the input contract is written first; the renderer checks values against it")
    if not (folder / "02-findings.md").exists():
        res.err("findings-missing", "02-findings.md", "every step's status must be in the findings table too")

    # --- run ------------------------------------------------------------------------------
    run = v.node(data, "run", "") or {}
    run_no = str(run.get("run_no", "")).strip()
    run_date = str(run.get("run_date", "")).strip()
    branch_code = str(run.get("branch_code", "")).strip()
    target_env = str(run.get("target_env", "")).strip()
    env_slug = str(run.get("env_slug", "")).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", run_date):
        res.err("values-bad-run", "run.run_date", "YYYY-MM-DD")
    if not re.fullmatch(r"[A-Z0-9_]{2,20}", branch_code):
        res.err("values-bad-run", "run.branch_code", "e.g. NY_SCH")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", env_slug):
        res.err("values-bad-run", "run.env_slug", "lower-case with dashes, e.g. tier2-pre")
    if not target_env or not run_no:
        res.err("values-bad-run", "run", "run_no and target_env are required")
    base = f"{branch_code}-{env_slug}"
    res.base = base

    # --- environment ----------------------------------------------------------------------
    env = v.node(data, "environment", "") or {}
    auth, src_auth = v.leaf_num(env, "target_auth_code", "environment", integer=True)
    fraction = None
    if auth:
        fraction = format((Decimal(auth) / (Decimal(10) ** len(auth))).normalize(), "f")
        if inputs.get("TARGET_AUTH_CODE") and canon(inputs["TARGET_AUTH_CODE"]) != auth:
            res.err("values-disagree-with-inputs", "environment.target_auth_code",
                    f"{auth} here, {inputs['TARGET_AUTH_CODE']} in 00-inputs.md")
        if not inputs.get("TARGET_AUTH_CODE"):
            res.err("values-disagree-with-inputs", "environment.target_auth_code",
                    "00-inputs.md has no TARGET_AUTH_CODE line (Q-G3c)")
        if inputs.get("TARGET_PK_FRACTION") and canon(inputs["TARGET_PK_FRACTION"]) != fraction:
            res.err("values-disagree-with-inputs", "environment.target_auth_code",
                    f"auth code {auth} gives fraction {fraction}; 00-inputs.md says {inputs['TARGET_PK_FRACTION']}")
    owners = {}
    for key in ("sequence_function_owner", "precommit_package_owner"):
        val, _ = v.leaf_text(env, key, "environment")
        if val and not IDENT_RE.fullmatch(val):
            res.err("values-bad-owner", f"environment.{key}.value", f"{val!r} is not a schema name (Q-G3b (b)/(d))")
        owners[key] = (val or "").upper()
    seq = f"{owners['sequence_function_owner']}.F___SEQUENCE"
    pkg = f"{owners['precommit_package_owner']}.PKG_ENGPRECOMMIT"

    # --- identity -------------------------------------------------------------------------
    ident = v.node(data, "identity", "") or {}
    idv, idsrc = {}, {}
    for key, ph, obj, kind in IDENTITY:
        c, s = v.leaf_num(ident, key, "identity")
        idv[key], idsrc[key] = c, s
    own = [idv[k] for k, _, _, kind in IDENTITY if kind == "owner" and idv[k]]
    ext = [idv[k] for k, _, _, kind in IDENTITY if kind == "ext" and idv[k]]
    if len(own) == 4 and len(set(own)) != 4:
        res.err("identity-not-distinct", "identity", "the four owners (Config, FixingCurve, Limit Error Assign, "
                "Days Matured) must be four different objects - run 4 wrote the Config owner on Days Matured")
    if len(ext) == 5 and (len(set(ext)) != 5 or set(ext) & set(own)):
        res.err("identity-not-distinct", "identity", "the five extensions must differ from each other and from every owner")

    # --- branch ---------------------------------------------------------------------------
    br = v.node(data, "branch", "") or {}
    branch_pk, src_branch = v.leaf_num(br, "branch_pk", "branch")
    source_front, src_front = v.leaf_num(br, "source_front", "branch")
    for key, val in (("BRANCH_PK", branch_pk), ("SOURCE_FRONT", source_front)):
        if val and inputs.get(key) is None:
            res.err("values-disagree-with-inputs", f"branch.{key.lower()}", f"00-inputs.md has no {key} line")
        elif val and canon(inputs[key]) != val:
            res.err("values-disagree-with-inputs", f"branch.{key.lower()}", f"{val} here, {inputs[key]} in 00-inputs.md")
    approved: list[str] = []
    names: dict[str, str] = {}
    for i, item in enumerate(v.node(br, "approved_instruments", "branch", kind=list) or []):
        p = f"branch.approved_instruments[{i}]"
        if not isinstance(item, dict):
            res.err("values-wrong-type", p, "expected {value, name, source}")
            continue
        v.source(item.get("source"), p + ".source")
        c = canon(item.get("value"))
        if c is None:
            res.err("values-not-a-number", p + ".value", f"{item.get('value')!r} is not a number")
            continue
        if c in names:
            res.err("values-duplicate", p, f"{c} listed twice")
        approved.append(c)
        names[c] = ascii_comment(item.get("name") or c)
    if not approved:
        res.err("values-missing-field", "branch.approved_instruments", "gate 0c's answer: at least one instrument")
    if "APPROVED_INSTRUMENTS" not in inputs:
        res.err("values-disagree-with-inputs", "branch.approved_instruments", "00-inputs.md has no APPROVED_INSTRUMENTS line")
    else:
        inp = {canon(x) for x in inputs["APPROVED_INSTRUMENTS"].split(",") if x.strip()}
        if inp != set(approved):
            res.err("values-disagree-with-inputs", "branch.approved_instruments",
                    f"{sorted(set(approved))} here, {sorted(x for x in inp if x)} in 00-inputs.md")
    if inputs.get("QUOTE_REF_COLUMN") and inputs["QUOTE_REF_COLUMN"].upper() != "FK_BS":
        res.err("values-disagree-with-inputs", "00-inputs.md QUOTE_REF_COLUMN",
                "settled 2026-09-24: the quote reference is FK_BS")

    # --- gbo ------------------------------------------------------------------------------
    gbo = v.node(data, "gbo", "") or {}
    gbo_conf, src_gbo_conf = v.leaf_num(gbo, "config_pk", "gbo")
    gbo_curve, src_gbo_curve = v.leaf_num(gbo, "curve_pk", "gbo")

    # --- steps: status, and agreement with the findings table -----------------------------
    steps = v.node(data, "steps", "") or {}
    status: dict[str, str] = {}
    for s in WALK:
        st = steps.get(s)
        p = f"steps.{s}"
        if not isinstance(st, dict):
            res.err("values-missing-field", p, "every walk step has an entry with its status and source")
            continue
        stt = str(st.get("status", "")).strip()
        if stt not in STATUSES:
            res.err("values-bad-status", p + ".status", f"{stt!r} is not one of the eight canonical statuses")
            continue
        status[s] = stt
        v.source(st.get("source"), p + ".source")
        if stt in HELD and not str(st.get("waits_on", "")).strip():
            res.err("values-missing-field", p + ".waits_on", f"{stt}: name who or what it waits on")
        if s in FIXED_STATUS and stt not in FIXED_STATUS[s][0]:
            res.err("step-unsupported-status", p + ".status", f"{stt}: {FIXED_STATUS[s][1]}")
        if (folder / "02-findings.md").exists():
            got = findings.get(s, set())
            if not got:
                res.err("findings-disagree", p + ".status", f"02-findings.md has no row for step {s} with a status")
            elif got != {stt}:
                res.err("findings-disagree", p + ".status",
                        f"{stt} here, {', '.join(sorted(got))} in 02-findings.md row {s} - one status per row, the same in both")
    emitted = {s for s in CORE + OPTIONAL if status.get(s) in EMIT}
    held = [s for s in CORE + OPTIONAL if status.get(s) in HELD]
    for s in CORE:
        if s in status and status[s] not in EMIT | HELD:
            res.err("step-unsupported-status", f"steps.{s}.status",
                    f"{status[s]}: steps 2-5 are either built (PROPOSED/DERIVED) or held")
    core_ready = all(s in emitted for s in CORE)
    if status.get("14a") == "CONFIRMED_ABSENT":
        res.err("step-unsupported-status", "steps.14a.status", "use CONFIRMED_PRESENT when every approved "
                "instrument already has a Days Matured row, PROPOSED when some are missing")
    for s in ("6", "12"):
        if status.get(s) in {"CONFIRMED_ABSENT", "CONFIRMED_PRESENT", "NOT_BRANCH_SCOPED"}:
            res.err("step-unsupported-status", f"steps.{s}.status", f"{status[s]}: every approved instrument "
                    "needs a step-%s row; build it or hold it" % s)
    if status.get("11") in {"CONFIRMED_ABSENT", "CONFIRMED_PRESENT", "NOT_BRANCH_SCOPED"}:
        res.err("step-unsupported-status", "steps.11.status", f"{status['11']}: the branch needs its book rows")

    for s in sorted(DECIDED & emitted, key=WALK.index):
        ds = steps[s].get("decisions")
        if not isinstance(ds, list) or not ds or not all(isinstance(x, int) for x in ds):
            res.err("decision-missing", f"steps.{s}.decisions", "a decided step lists the decision number(s) it "
                    "rests on, e.g. [1] - each a row in 00-decisions.md")
        else:
            for n in ds:
                v.decision(n, f"steps.{s}.decisions")
    if emitted & DECIDED and not (folder / "00-decisions.md").exists():
        res.err("decision-missing", "00-decisions.md", "decided steps are emitted but there is no decisions log")

    subs: dict[str, str] = {}
    report = res.report

    # --- step 2, 3 ------------------------------------------------------------------------
    s2 = steps.get("2") if isinstance(steps.get("2"), dict) else {}
    s3 = steps.get("3") if isinstance(steps.get("3"), dict) else {}
    conf_desc = curve_desc = None
    cal = cur = ccur = None
    src_cd = src_cal = src_cur = src_vd = src_ccur = ""
    if "2" in emitted:
        conf_desc, src_cd = v.leaf_text(s2, "description", "steps.2")
        cal, src_cal = v.leaf_num(s2, "fk_calendar", "steps.2")
        cur, src_cur = v.leaf_num(s2, "fk_currency", "steps.2")
    if "3" in emitted:
        curve_desc, src_vd = v.leaf_text(s3, "description", "steps.3")
        ccur, src_ccur = v.leaf_num(s3, "fk_currency", "steps.3")
    if conf_desc and curve_desc and conf_desc == curve_desc:
        res.warn("same-description", "steps.3.description", "header and curve share a DESCRIPTION")
    subs.update(FK_CALENDAR=cal or "", FK_CURRENCY=cur or "", CURVE_FK_CURRENCY=ccur or "",
                SRC_CONF_DESCRIPTION=ascii_comment(src_cd), SRC_FK_CALENDAR=ascii_comment(src_cal),
                SRC_FK_CURRENCY=ascii_comment(src_cur), SRC_CURVE_DESCRIPTION=ascii_comment(src_vd),
                SRC_CURVE_FK_CURRENCY=ascii_comment(src_ccur))

    # --- step 4 ---------------------------------------------------------------------------
    quote_refs: list[str] = []
    src_exp4 = ""
    if "4" in emitted:
        s4 = steps.get("4") or {}
        exp4, src_exp4 = v.leaf_num(s4, "expected_count", "steps.4", integer=True)
        csvp = folder / Q04C
        if not csvp.exists():
            res.err("evidence-missing", Q04C, "step 4's set is generated from this CSV (Q-04c (a))")
        else:
            rows = _read_csv(csvp, res)
            if rows is not None:
                if rows and "FK_BS" not in rows[0]:
                    res.err("evidence-bad-shape", Q04C, f"no FK_BS column; columns are {sorted(rows[0])}")
                else:
                    vals, bad = set(), []
                    for r in rows:
                        c = canon(evidence_to_sql.norm_safe(r.get("FK_BS", "")) or "")
                        if c is None:
                            bad.append(r.get("FK_BS", ""))
                        else:
                            vals.add(c)
                    if bad:
                        res.err("evidence-bad-value", Q04C, f"FK_BS not numeric or empty in {len(bad)} row(s): {bad[:5]}")
                    quote_refs = sorted(vals, key=Decimal)
                    unresolved = [r.get("FK_BS") for r in rows if "QUOTE_REF_PK" in r
                                  and r.get("QUOTE_REF_PK", "").strip().lower() in evidence_to_sql.NULLS]
                    if unresolved:
                        res.err("evidence-unresolved", Q04C, f"{len(unresolved)} quote reference(s) do not resolve in "
                                f"PGT_MRK.T_PGT_QUOTE_REFERENCE_S: {unresolved[:5]} - a source question, not a row to drop")
                    report.append(f"- Step 4: {len(rows)} CSV row(s), {len(quote_refs)} distinct FK_BS.")
        cp = folder / Q04C_COUNTS
        if not cp.exists():
            res.err("evidence-missing", Q04C_COUNTS, "Q-04c (b), the counts - hard rule 8")
        else:
            crow = _read_csv(cp, res)
            if crow:
                c0 = crow[0]
                nfk = canon(c0.get("N_FK_BS", ""))
                nrows, nres = canon(c0.get("N_ROWS", "")), canon(c0.get("N_RESOLVED", ""))
                if nfk is None or nrows is None or nres is None:
                    res.err("evidence-bad-shape", Q04C_COUNTS, "expected columns N_ROWS, N_FK_BS, N_RESOLVED")
                else:
                    if quote_refs and int(nfk) != len(quote_refs):
                        res.err("evidence-disagree", Q04C_COUNTS, f"N_FK_BS {nfk}, but the set CSV has {len(quote_refs)} distinct FK_BS")
                    if nres != nrows:
                        res.err("evidence-unresolved", Q04C_COUNTS, f"N_RESOLVED {nres} <> N_ROWS {nrows}: a quote "
                                "reference does not resolve - a source question, not a row to drop")
        if exp4 and quote_refs and int(exp4) != len(quote_refs):
            res.err("count-disagrees", "steps.4.expected_count.value", f"{exp4}, but the CSV has {len(quote_refs)} distinct FK_BS")
        if not quote_refs and csvp.exists():
            res.err("evidence-empty", Q04C, "no quote references - the curve needs its array (hard rule 8: is the query right?)")
        lines, per = [], 8
        for i in range(0, len(quote_refs), per):
            lines.append(", ".join(quote_refs[i:i + per]))
        subs["QUOTE_REFS_LIST"] = "sys.odcinumberlist(\n    " + ",\n    ".join(lines) + ")" if quote_refs else "sys.odcinumberlist()"
        subs["EXPECTED_QUOTE_REFS"] = str(len(quote_refs))
        subs["STATED_QUOTE_REFS"] = exp4 or ""
        subs["SRC_EXPECTED_QUOTE_REFS"] = ascii_comment(src_exp4)

    # --- step 6 ---------------------------------------------------------------------------
    n6 = 0
    if "6" in emitted:
        s6 = steps["6"]
        rows6 = v.node(s6, "rows", "steps.6", kind=list) or []
        seen, blocks = [], []
        for i, r in enumerate(rows6):
            p = f"steps.6.rows[{i}]"
            if not isinstance(r, dict):
                res.err("values-wrong-type", p, "expected an object")
                continue
            extra = set(r) - set(STEP6_COLS) - {"FK_INSTRUMENT", "source"}
            miss = (set(STEP6_COLS) | {"FK_INSTRUMENT"}) - set(r)
            if extra:
                res.err("step6-unknown-column", p, f"unknown column(s) {sorted(extra)} - the columns are FK_INSTRUMENT, "
                        + ", ".join(STEP6_COLS))
            if miss:
                res.err("step6-missing-column", p, f"missing {sorted(miss)} - write null explicitly for an empty column "
                        "(run 5 dropped FK_BASIS silently)")
            v.source(r.get("source"), p + ".source")
            ins = canon(r.get("FK_INSTRUMENT"))
            if ins is None or ins not in names:
                res.err("instrument-not-approved", p + ".FK_INSTRUMENT", f"{r.get('FK_INSTRUMENT')!r} is not an approved instrument")
                continue
            seen.append(ins)
            vals = []
            for col in STEP6_COLS:
                x = r.get(col)
                if x is None:
                    if col in STEP6_NOT_NULL:
                        res.err("step6-null-in-not-null", f"{p}.{col}", f"{col} is NOT NULL")
                    vals.append("NULL")
                else:
                    c = canon(x)
                    if c is None:
                        res.err("values-not-a-number", f"{p}.{col}", f"{x!r} is not a number")
                    vals.append(c or "NULL")
            blocks.append((ins, vals, r.get("source", "")))
        if sorted(seen) != sorted(approved):
            res.err("step6-rows-not-approved-set", "steps.6.rows",
                    f"one row per approved instrument: have {sorted(seen)}, approved {sorted(approved)}")
        order = {x: i for i, x in enumerate(approved)}
        blocks.sort(key=lambda b: order.get(b[0], 999))
        out = []
        for ins, vals, src in blocks:
            out.append(f"  -- {names[ins]} ({ins}): {ascii_comment(src)}\n" + pk_block(seq, "T_BOX_ENGACCRCONF_S")
                       + "  INSERT INTO BOX_FE.T_BOX_ENGACCRCONF_S\n"
                       "    (PK, FK_OWNER_OBJ, FK_PARENT, FK_EXTENSION, FK_INSTRUMENT,\n"
                       "     " + ", ".join(sql_ident(c) for c in STEP6_COLS) + ")\n"
                       "  VALUES\n"
                       f"    (v_pk, c_owner_conf, v_conf_pk, c_ext_accrconf, {ins},\n"
                       "     " + ", ".join(vals) + ");\n")
        n6 = len(blocks)
        subs["STEP_6_ROWS"] = "\n".join(out).rstrip("\n")
        subs["SRC_6"] = ascii_comment(s6.get("source", "")) + f"; decision(s) {', '.join(map(str, s6.get('decisions') or []))}"
        subs["V11_6"] = [(ins, vals) for ins, vals, _ in blocks]

    # --- step 7 ---------------------------------------------------------------------------
    exc_rows: list[tuple] = []
    exp7 = None
    csv7 = folder / Q06C
    if status.get("7") in EMIT | {"CONFIRMED_ABSENT"}:
        if not csv7.exists():
            res.err("evidence-missing", Q06C, "step 7's rows (or their absence) are proved by this CSV (Q-06c)")
        else:
            rows = _read_csv(csv7, res)
            if rows is not None and branch_pk:
                need = set(STEP7_COLS) | {"BRANCH_PK"}
                if rows and not need <= set(rows[0]):
                    res.err("evidence-bad-shape", Q06C, f"expected columns {sorted(need)}; have {sorted(rows[0])}")
                else:
                    seen7, dropped, dups = set(), [], 0
                    for r in rows:
                        b = canon(evidence_to_sql.norm_safe(r.get("BRANCH_PK", "")) or "")
                        ins = canon(evidence_to_sql.norm_safe(r.get("FK_INSTRUMENT", "")) or "")
                        label = r.get("BRANCH", "") or ""
                        gpk = r.get("GBO_ROW_PK", "") or ""
                        if b != branch_pk:
                            dropped.append(f"GBO row {gpk or '?'}: branch {b or 'unresolved'} {ascii_comment(label)}".rstrip())
                            continue
                        if ins not in names:
                            dropped.append(f"GBO row {gpk or '?'}: instrument {ins} not approved")
                            continue
                        t = []
                        for c in STEP7_COLS:
                            raw = (r.get(c) or "").strip()
                            if raw.lower() in evidence_to_sql.NULLS:
                                t.append(None)
                            else:
                                cc = canon(evidence_to_sql.norm_safe(raw) or "")
                                if cc is None:
                                    res.err("evidence-bad-value", Q06C, f"{c} {raw!r} is not numeric (GBO row {gpk})")
                                t.append(cc)
                        t = tuple(t)
                        if t in seen7:
                            dups += 1
                            continue
                        seen7.add(t)
                        exc_rows.append(t)
                    report.append(f"- Step 7: {len(rows)} CSV row(s); kept {len(exc_rows)}; filtered out {len(dropped)}"
                                  + (f"; {dups} exact duplicate(s) merged" if dups else "") + ".")
                    report.extend(f"    - filtered out - {d}" for d in dropped)
        s7 = steps.get("7") or {}
        if status.get("7") in EMIT:
            exp7, src_exp7 = v.leaf_num(s7, "expected_count", "steps.7", integer=True)
            if exp7 and csv7.exists() and int(exp7) != len(exc_rows):
                res.err("count-disagrees", "steps.7.expected_count.value",
                        f"{exp7}, but Q-06c filtered to branch {branch_pk} and the approved instruments has {len(exc_rows)}")
            if csv7.exists() and not exc_rows:
                res.err("count-disagrees", "steps.7.status", "PROPOSED with no rows - if the branch has no exceptions "
                        "the status is CONFIRMED_ABSENT")
            subs["SRC_EXPECTED_EXCEPTIONS"] = ascii_comment(src_exp7)
            subs["STATED_EXCEPTIONS"] = exp7 or ""
        elif csv7.exists() and exc_rows:
            res.err("count-disagrees", "steps.7.status", f"CONFIRMED_ABSENT, but Q-06c has {len(exc_rows)} row(s) for "
                    "the branch and the approved instruments")
    if "7" in emitted:
        sel = []
        for t in exc_rows:
            items = [f"{x if x is not None else 'CAST(NULL AS NUMBER)'} AS {c}" for x, c in zip(t, STEP7_COLS)]
            sel.append("SELECT " + ", ".join(items) + " FROM dual")
        subs["EXCEPTION_ROWS"] = "\n              UNION ALL ".join(sel)
    subs["EXPECTED_EXCEPTIONS"] = str(len(exc_rows)) if "7" in emitted else "0"

    # --- step 11 --------------------------------------------------------------------------
    n11, books, dummy = 0, [], None
    if "11" in emitted:
        s11 = steps["11"]
        blist = v.node(s11, "books", "steps.11", kind=list) or []
        bnames = {}
        for i, b in enumerate(blist):
            p = f"steps.11.books[{i}]"
            if not isinstance(b, dict):
                res.err("values-wrong-type", p, "expected {value, name, source}")
                continue
            v.source(b.get("source"), p + ".source")
            c = canon(b.get("value"))
            if c is None:
                res.err("values-not-a-number", p + ".value", f"{b.get('value')!r} is not a label PK")
                continue
            if c in bnames:
                res.err("values-duplicate", p, f"book {c} listed twice")
            books.append(c)
            bnames[c] = ascii_comment(b.get("name") or c)
        if not books:
            res.err("values-missing-field", "steps.11.books", "the branch's real books (a decision card)")
        dn = v.node(s11, "dummy_book", "steps.11") or {}
        dummy = canon(dn.get("value")) if dn else None
        dsrc = v.source(dn.get("source"), "steps.11.dummy_book.source") if dn else ""
        if dn and dummy is None:
            res.err("values-not-a-number", "steps.11.dummy_book.value", f"{dn.get('value')!r} is not a label PK")
        if dummy and dummy in books:
            res.err("dummy-is-a-book", "steps.11.dummy_book.value", f"{dummy} is also a real book - the dummy row is a "
                    "BOX FE rule and never a real book's label (run 4)")
        if dummy and not re.search(r"decision\s+\d+", dsrc, re.I):
            res.err("decision-missing", "steps.11.dummy_book.source", "the Tier 2 dummy label is a BOX FE team "
                    "decision: cite it (decision N)")
        if dummy and inputs.get("DUMMY_BOOK_LABEL") is None:
            res.err("values-disagree-with-inputs", "steps.11.dummy_book", "00-inputs.md has no DUMMY_BOOK_LABEL line")
        elif dummy and canon(inputs["DUMMY_BOOK_LABEL"]) != dummy:
            res.err("values-disagree-with-inputs", "steps.11.dummy_book", f"{dummy} here, {inputs['DUMMY_BOOK_LABEL']} in 00-inputs.md")
        if inputs.get("BOOK_LABELS"):
            ib = {canon(x) for x in re.findall(r"\d+(?:\.\d+)?", inputs["BOOK_LABELS"])}
            if ib and ib != set(books):
                res.err("values-disagree-with-inputs", "steps.11.books", f"{sorted(books)} here, {sorted(ib)} in 00-inputs.md")
        out, pairs = [], []
        for ins in approved:
            for b in books + ["DUMMY"]:
                lab = "c_dummy_book" if b == "DUMMY" else b
                what = "dummy book" if b == "DUMMY" else f"{bnames.get(b, b)} ({b})"
                out.append(f"  -- {names[ins]} ({ins}) x {what}\n" + pk_block(seq, "T_BOX_CONF_BY_BOOK_S")
                           + "  INSERT INTO BOX_FE.T_BOX_CONF_BY_BOOK_S\n"
                           "    (PK, FK_OWNER_OBJ, FK_PARENT, FK_EXTENSION, FK_BRANCH, FK_INSTRUMENT, FK_LABEL)\n"
                           f"  VALUES (v_pk, c_owner_conf, v_conf_pk, c_ext_conf_by_book, c_branch_pk, {ins}, {lab});\n")
                pairs.append((ins, dummy if b == "DUMMY" else b))
        n11 = len(out)
        subs.update(STEP_11_ROWS="\n".join(out).rstrip("\n"), DUMMY_BOOK_LABEL=dummy or "",
                    DUMMY_BOOK_NAME=ascii_comment(dn.get("name") or "dummy book"), SRC_DUMMY_BOOK=ascii_comment(dsrc),
                    BOOKS_TEXT=", ".join(f"{bnames[b]} ({b})" for b in books if b in bnames),
                    BOOK_LABELS=", ".join(books),
                    SRC_11=ascii_comment(s11.get("source", "")) + f"; decision(s) {', '.join(map(str, s11.get('decisions') or []))}")
        subs["V11_11"] = pairs

    # --- step 12 --------------------------------------------------------------------------
    n12 = 0
    if "12" in emitted:
        s12 = steps["12"]
        rows12 = v.node(s12, "rows", "steps.12", kind=list) or []
        got, out, v11 = [], [], []
        for i, r in enumerate(rows12):
            p = f"steps.12.rows[{i}]"
            if not isinstance(r, dict):
                res.err("values-wrong-type", p, "expected an object")
                continue
            if set(r) - {"FK_INSTRUMENT", "LIMIT_ERRORS", "source"}:
                res.err("step12-unknown-column", p, f"unknown {sorted(set(r) - {'FK_INSTRUMENT', 'LIMIT_ERRORS', 'source'})}")
            v.source(r.get("source"), p + ".source")
            ins, lim = canon(r.get("FK_INSTRUMENT")), canon(r.get("LIMIT_ERRORS"))
            if ins not in names:
                res.err("instrument-not-approved", p + ".FK_INSTRUMENT", f"{r.get('FK_INSTRUMENT')!r} is not approved")
                continue
            if lim is None or "." in lim or int(lim) <= 0:
                res.err("step12-limit", p + ".LIMIT_ERRORS", f"{r.get('LIMIT_ERRORS')!r}: a whole number > 0 - 0 aborts the "
                        "load on the first failed deal (ADR 0004)")
                continue
            got.append((ins, lim, r.get("source", "")))
        if sorted(g[0] for g in got) != sorted(approved):
            res.err("step12-rows-not-approved-set", "steps.12.rows",
                    f"one row per approved instrument: have {sorted(g[0] for g in got)}, approved {sorted(approved)}")
        order = {x: i for i, x in enumerate(approved)}
        for ins, lim, src in sorted(got, key=lambda g: order.get(g[0], 999)):
            out.append(f"  -- {names[ins]} ({ins}): {ascii_comment(src)}\n" + pk_block(seq, "T_BOX_ERRORS_FE_S")
                       + "  INSERT INTO BOX_FE.T_BOX_ERRORS_FE_S (PK, FK_OWNER_OBJ, FK_BRANCH, FK_INSTRUMENT, LIMIT_ERRORS)\n"
                       f"  VALUES (v_pk, c_owner_errors, c_branch_pk, {ins}, {lim});\n")
            v11.append((ins, lim))
        n12 = len(out)
        subs["STEP_12_ROWS"] = "\n".join(out).rstrip("\n")
        subs["SRC_12"] = ascii_comment(s12.get("source", "")) + f"; decision(s) {', '.join(map(str, s12.get('decisions') or []))}"
        subs["V11_12"] = v11

    # --- step 14a -------------------------------------------------------------------------
    n14, dm_instruments = 0, []
    s14 = steps.get("14a") if isinstance(steps.get("14a"), dict) else {}
    present = []
    if status.get("14a") in EMIT | {"CONFIRMED_PRESENT"}:
        present = instrument_list(v, s14, "already_present", "steps.14a", names)
    if status.get("14a") == "CONFIRMED_PRESENT":
        if sorted(present) != sorted(approved):
            res.err("step14a-coverage", "steps.14a.already_present", "CONFIRMED_PRESENT means every approved instrument "
                    f"has a row (Q-12 (a)): listed {sorted(present)}, approved {sorted(approved)}")
        if s14.get("rows"):
            res.err("step14a-coverage", "steps.14a.rows", "CONFIRMED_PRESENT with rows to insert")
    if "14a" in emitted:
        dd, _ = v.leaf_text(s14, "ddate", "steps.14a")
        ddate_sql = DDATE_EXPRESSIONS.get(re.sub(r"\s+", "", dd or "").upper())
        if dd and not ddate_sql:
            res.err("step14a-ddate", "steps.14a.ddate.value", "SYSDATE or TRUNC(SYSDATE) (DateToProcess, decision "
                    "card 5 - Q-12 (a)/(b) show whether existing rows carry a time of day)")
            ddate_sql = "SYSDATE"
        rows14 = v.node(s14, "rows", "steps.14a", kind=list) or []
        got, out, v11 = [], [], []
        for i, r in enumerate(rows14):
            p = f"steps.14a.rows[{i}]"
            if not isinstance(r, dict):
                res.err("values-wrong-type", p, "expected an object")
                continue
            if set(r) - {"FK_INSTRUMENT", "NUM_DAYS", "source"}:
                res.err("step14a-unknown-column", p, f"unknown {sorted(set(r) - {'FK_INSTRUMENT', 'NUM_DAYS', 'source'})}")
            v.source(r.get("source"), p + ".source")
            ins, nd = canon(r.get("FK_INSTRUMENT")), canon(r.get("NUM_DAYS"))
            if ins not in names:
                res.err("instrument-not-approved", p + ".FK_INSTRUMENT", f"{r.get('FK_INSTRUMENT')!r} is not approved")
                continue
            if nd is None or "." in nd or int(nd) <= 0:
                res.err("step14a-days", p + ".NUM_DAYS", f"{r.get('NUM_DAYS')!r}: a whole number of days > 0")
                continue
            got.append((ins, nd, r.get("source", "")))
        created = [g[0] for g in got]
        if set(created) & set(present):
            res.err("step14a-coverage", "steps.14a.rows", f"{sorted(set(created) & set(present))} already have a row (Q-12 (a))")
        if sorted(created + present) != sorted(approved) or len(set(created)) != len(created):
            res.err("step14a-coverage", "steps.14a", "every approved instrument is either already_present (Q-12 (a)) "
                    f"or created here, once: present {sorted(present)}, created {sorted(created)}, approved {sorted(approved)}")
        if not got:
            res.err("step14a-coverage", "steps.14a.rows", "PROPOSED with nothing to create - use CONFIRMED_PRESENT")
        order = {x: i for i, x in enumerate(approved)}
        for ins, nd, src in sorted(got, key=lambda g: order.get(g[0], 999)):
            out.append(f"  -- {names[ins]} ({ins}): {ascii_comment(src)}\n" + pk_block(seq, "T_BOX_ENGDAYS_MATURED_S")
                       + "  INSERT INTO BOX_FE.T_BOX_ENGDAYS_MATURED_S (PK, FK_OWNER_OBJ, DDATE, FK_INSTRUMENT, NUM_DAYS)\n"
                       f"  VALUES (v_pk, c_owner_days_matured, {ddate_sql}, {ins}, {nd});\n")
            v11.append((ins, nd))
            dm_instruments.append(ins)
        n14 = len(out)
        subs["STEP_14A_ROWS"] = "\n".join(out).rstrip("\n")
        subs["SRC_14A"] = ascii_comment(s14.get("source", "")) + f"; decision(s) {', '.join(map(str, s14.get('decisions') or []))}"
        subs["V11_14A"] = v11

    # --- the target's columns (Q-G3d (e)): no ORA-00904 / ORA-01400 / ORA-12899 at apply time --
    if core_ready:
        nulls = {"T_BOX_ENGACCRCONF_S": {c for _, vals in subs.get("V11_6", []) for c, x in zip(STEP6_COLS, vals)
                                         if x == "NULL"},
                 "T_BOX_CONFIG_ACCRUAL_S": {c for row in exc_rows for c, x in zip(STEP7_COLS, row) if x is None}}
        check_target_columns(folder, emitted, {"T_BOX_ENGCONF_S": conf_desc, "T_BOX_ENGFCURVE_S": curve_desc}, res,
                             nulls)

    # --- anything cited but not in the log -------------------------------------------------
    if decisions and v.cited:
        unused = sorted(set(decisions) - v.cited)
        if unused:
            res.warn("decision-not-cited", "00-decisions.md", f"decision(s) {unused} are cited by no value")

    if res.errors:
        return res
    if not core_ready:
        res.nothing_to_render = ("steps 2-5 are not all ready (" + ", ".join(f"{s} {status.get(s, '?')}" for s in CORE)
                                 + ") - no SQL until the configuration itself can be built")
        return res

    # --- substitutions shared by the four files --------------------------------------------
    digest = hashlib.sha256(raw_bytes).hexdigest()[:16]
    subs.update(
        BRANCH_CODE=branch_code, TARGET_ENV=ascii_comment(target_env), BASE=base,
        RENDERED_LINE=(f"RENDERED by scripts/render_sql.py from 03-sql/values.json (sha256 {digest}), run "
                       f"{ascii_comment(run_no)}, {run_date}. Do not edit: change values.json and render again."),
        HELD_STEPS=", ".join(held) if held else "none",
        TARGET_AUTH_CODE=auth or "", TARGET_PK_FRACTION=fraction or "", SRC_TARGET_AUTH_CODE=ascii_comment(src_auth),
        BRANCH_PK=branch_pk or "", SRC_BRANCH_PK=ascii_comment(src_branch),
        SOURCE_FRONT=source_front or "", SRC_SOURCE_FRONT=ascii_comment(src_front),
        GBO_CONFIG_PK=gbo_conf or "", SRC_GBO_CONFIG_PK=ascii_comment(src_gbo_conf),
        GBO_CURVE_PK=gbo_curve or "", SRC_GBO_CURVE_PK=ascii_comment(src_gbo_curve),
        CONF_DESCRIPTION_SQL=sql_text(conf_desc or ""), CURVE_DESCRIPTION_SQL=sql_text(curve_desc or ""),
        SEQ=seq, PKG=pkg, APPROVED_INSTRUMENTS=", ".join(approved),
        DAYS_MATURED_INSTRUMENTS=", ".join(dm_instruments) or "-1",
        N_STEP6=str(n6), N_STEP11=str(n11), N_STEP12=str(n12), N_STEP14A=str(n14),
        STATUS_8=status.get("8", ""), SRC_8=ascii_comment((steps.get("8") or {}).get("source", "")),
    )
    for key, ph, obj, kind in IDENTITY:
        subs[ph] = idv[key] or ""
        subs["SRC_" + ph] = ascii_comment(idsrc[key])
    for s in WALK:
        subs["STATUS_" + s.upper()] = status.get(s, "")
    subs["SELF_CHECK"] = self_check(emitted, len(quote_refs), n6, len(exc_rows), n11, n12, n14, dm_instruments)
    subs["V6"] = v6_query(emitted, subs)
    subs["V11"] = v11_queries(subs)
    subs["V12"] = v12_query(emitted, subs, approved, books, dummy or "")
    for k in [k for k in subs if k.startswith("V11_")]:
        subs.pop(k)

    keys = {f"step{s}" for s in emitted} | ({"draft"} if held else set())
    if status.get("14a") == "CONFIRMED_PRESENT":
        keys.add("days_present")
    config_tpl = (TPL / "config.sql.tmpl").read_text(encoding="utf-8")
    for role, tpl, extra in (("rehearsal", config_tpl, {"rehearsal"}), ("config", config_tpl, {"apply"}),
                             ("verify", (TPL / "verify.sql.tmpl").read_text(encoding="utf-8"), set()),
                             ("rollback", (TPL / "rollback.sql.tmpl").read_text(encoding="utf-8"), set())):
        text = fill(apply_sections(tpl, keys | extra, res, role), subs, res, role)
        text = re.sub(r"\n{3,}", "\n\n", text)
        bad = sorted({c for c in text if ord(c) > 126 or (ord(c) < 32 and c not in "\n\t")})
        if bad:
            res.err("output-not-ascii", role, f"non-ASCII character(s) {bad[:5]} in the rendered file")
        if "{{" in text or "@@" in text:
            res.err("template-broken", role, "a placeholder or section marker survived rendering")
        res.files[f"{base}-{role}.sql"] = text

    # --- report ------------------------------------------------------------------------------
    head = [f"# Render report - {base}", "",
            f"Rendered by `scripts/render_sql.py` from `03-sql/values.json` (sha256 `{digest}`), run {run_no}, {run_date}.",
            "**Do not edit the SQL files.** Change `values.json` (or the evidence) and render again; the validator "
            "re-renders and fails any file that differs.", ""]
    if held:
        waits = ", ".join("step %s (%s, waits on %s)" % (s, status[s], ascii_comment(steps[s].get("waits_on", "")))
                          for s in held)
        head += [f"**DRAFT - not for apply.** Held: {waits}. "
                 "The config file stops on its first statement; the rehearsal still runs the rest.", ""]
    head += ["## Files", "", "| Run | File | Lines |", "|---|---|---|"]
    for i, role in enumerate(OUTPUT_ROLES, 1):
        fn = f"{base}-{role}.sql"
        head.append(f"| {i} | `{fn}` | {res.files[fn].count(chr(10))} |")
    head += ["", "## Rows per step", "", "| Step | Status | Rows | Source |", "|---|---|---|---|"]
    counts = {"2": 1, "3": 1, "4": len(quote_refs), "5": 1, "6": n6, "7": len(exc_rows) if "7" in emitted else 0,
              "11": n11, "12": n12, "14a": n14}
    for s in WALK:
        st = steps.get(s) or {}
        head.append(f"| {s} | {status.get(s, '?')} | {counts[s] if s in counts else '-'} | "
                    f"{ascii_comment(st.get('source', '')).replace('|', '/')} |")
    head += ["", "## Evidence used", ""] + (report or ["- (none)"])
    if res.warnings:
        head += ["", "## Warnings", ""] + [f"- `{c}` {p}: {m}" for c, p, m in res.warnings]
    head += ["", "## How the operator runs it", "",
             f"1. `{base}-rehearsal.sql` - last line must read **REHEARSAL OK**. Anything else: stop and send the output.",
             f"2. `{base}-config.sql` - last line must read **DONE - committed**.",
             f"3. `{base}-verify.sql` - on the read-only account; every query's result must match its `Expect`.",
             f"4. `{base}-rollback.sql` - only to undo step 2; it prints counts and waits for COMMIT.", ""]
    res.report = head
    return res


def _read_csv(path: Path, res: Result):
    try:
        return evidence_to_sql.read_rows(path)
    except SystemExit as e:
        res.err("evidence-unreadable", str(path.name), str(e))
    except (OSError, UnicodeDecodeError, StopIteration) as e:
        res.err("evidence-unreadable", str(path.name), f"cannot read: {e}")
    return None


def check_target_columns(folder: Path, emitted: set[str], texts: dict[str, str | None], res: Result,
                         nulls: dict[str, set[str]] | None = None) -> None:
    cp = folder / Q_G3D_COLUMNS
    if not cp.exists():
        res.err("evidence-missing", Q_G3D_COLUMNS, "Q-G3d (e), the target's columns - the renderer checks every "
                "column it writes exists and every NOT NULL column is written, before anything runs")
        return
    rows = _read_csv(cp, res)
    if rows is None:
        return
    need = {"TABLE_NAME", "COLUMN_NAME", "DATA_TYPE", "DATA_LENGTH", "NULLABLE", "HAS_DEFAULT"}
    if rows and not need <= set(rows[0]):
        res.err("evidence-bad-shape", Q_G3D_COLUMNS, f"expected columns {sorted(need)}; have {sorted(rows[0])}")
        return
    cols: dict[str, dict[str, dict[str, str]]] = {}
    for r in rows:
        cols.setdefault(r["TABLE_NAME"].strip().upper(), {})[r["COLUMN_NAME"].strip().upper()] = r
    for table, (step, written) in WRITES.items():
        have = cols.get(table)
        if have is None:
            res.err("target-table-missing", Q_G3D_COLUMNS, f"no columns listed for BOX_FE.{table} - is the table "
                    "missing in the target (Q-G4), or was it left out of the query?")
            continue
        used = written if step in emitted else ALWAYS_READ.get(table, [])
        for c in used:
            if c not in have:
                res.err("target-column-missing", f"{Q_G3D_COLUMNS} {table}", f"column {c} does not exist in the "
                        "target (ORA-00904 at apply) - a template defect or a different DDL: report it, do not work round it")
        if step in emitted:
            for c, r in have.items():
                if r["NULLABLE"].strip().upper() == "N" and r["HAS_DEFAULT"].strip().upper() != "Y" and c not in written:
                    res.err("target-not-null-not-written", f"{Q_G3D_COLUMNS} {table}", f"{c} is NOT NULL with no default "
                            "and the template does not write it (ORA-01400 at apply) - report it as a template defect")
        for c in sorted((nulls or {}).get(table, set()) if step in emitted else set()):
            r = have.get(c)
            if r and r["NULLABLE"].strip().upper() == "N":
                res.err("target-null-in-not-null", f"{Q_G3D_COLUMNS} {table}", f"a NULL is written into {c}, which is "
                        "NOT NULL in the target (ORA-01400 at apply) - the value or the evidence is wrong")
        text = texts.get(table)
        d = have.get("DESCRIPTION")
        if text and d and re.match(r"N?VARCHAR2|N?CHAR", d["DATA_TYPE"].strip().upper()):
            size = canon(d["DATA_LENGTH"])
            if size and len(text.encode("utf-8")) > int(Decimal(size)):
                res.err("target-text-too-long", f"{table}.DESCRIPTION", f"{len(text.encode('utf-8'))} bytes, the "
                        f"column holds {size} (ORA-12899 at apply)")
    dd = cols.get("T_BOX_ENGDAYS_MATURED_S", {}).get("DDATE")
    if "14a" in emitted and dd and not re.match(r"DATE|TIMESTAMP", dd["DATA_TYPE"].strip().upper()):
        res.err("target-column-type", "T_BOX_ENGDAYS_MATURED_S.DDATE", f"type {dd['DATA_TYPE']}, not a date")


def v12_query(emitted, subs, approved, books, dummy) -> str:
    """Every reference value written exists in its master table (the verify account sees them)."""
    curve = f"(SELECT PK FROM BOX_FE.T_BOX_ENGFCURVE_S WHERE DESCRIPTION = {subs['CURVE_DESCRIPTION_SQL']})"
    parts = [
        ("instrument", f"TABLE(sys.odcinumberlist({', '.join(approved)}))", "PGT_SYS.T_PGT_SUB_PRODUCT_S"),
        ("source system", f"TABLE(sys.odcinumberlist({subs['SOURCE_FRONT']}, 586.4))", "PGT_SYS.T_PGT_SOURCE_S"),
    ]
    if "11" in emitted:
        parts.append(("book or dummy label", f"TABLE(sys.odcinumberlist({', '.join(books + [dummy])}))",
                      "PGT_SYS.PGT_DOMAINS"))
    out = [f"SELECT '{what}' AS kind, x.COLUMN_VALUE AS pk FROM {src} x\n"
           f"WHERE  NOT EXISTS (SELECT 1 FROM {master} m WHERE m.PK = x.COLUMN_VALUE)" for what, src, master in parts]
    out.append("SELECT 'quote reference' AS kind, q.FK_BS AS pk FROM BOX_FE.T_BOX_ENGLKFC_X q\n"
               f"WHERE  q.FK_PARENT = {curve}\n"
               "AND    NOT EXISTS (SELECT 1 FROM PGT_MRK.T_PGT_QUOTE_REFERENCE_S m WHERE m.PK = q.FK_BS)")
    return "\nUNION ALL\n".join(out) + ";"


def self_check(emitted, n4, n6, n7, n11, n12, n14, dm) -> str:
    chk = [("step 2  T_BOX_ENGCONF_S", "BOX_FE.T_BOX_ENGCONF_S WHERE PK = v_conf_pk", 1),
           ("step 3  T_BOX_ENGFCURVE_S", "BOX_FE.T_BOX_ENGFCURVE_S WHERE PK = v_curve_pk", 1),
           ("step 4  T_BOX_ENGLKFC_X", "BOX_FE.T_BOX_ENGLKFC_X WHERE FK_PARENT = v_curve_pk", n4),
           ("step 5  T_BOX_ENGCONF_X", "BOX_FE.T_BOX_ENGCONF_X WHERE FK_PARENT = v_conf_pk", 1),
           ("step 6  T_BOX_ENGACCRCONF_S", "BOX_FE.T_BOX_ENGACCRCONF_S WHERE FK_PARENT = v_conf_pk", n6),
           ("step 7  T_BOX_CONFIG_ACCRUAL_S", "BOX_FE.T_BOX_CONFIG_ACCRUAL_S WHERE FK_PARENT = v_conf_pk", n7 if "7" in emitted else 0),
           ("step 11 T_BOX_CONF_BY_BOOK_S", "BOX_FE.T_BOX_CONF_BY_BOOK_S WHERE FK_PARENT = v_conf_pk", n11)]
    if "12" in emitted:
        chk.append(("step 12 T_BOX_ERRORS_FE_S", "BOX_FE.T_BOX_ERRORS_FE_S WHERE FK_BRANCH = c_branch_pk", n12))
    if "14a" in emitted:
        chk.append(("step 14a T_BOX_ENGDAYS_MATURED_S",
                    f"BOX_FE.T_BOX_ENGDAYS_MATURED_S WHERE FK_INSTRUMENT IN ({', '.join(dm)})", n14))
    return "\n".join(f"  SELECT COUNT(*) INTO v_n FROM {q};\n  expect_rows('self-check: {w}', v_n, {n});"
                     for w, q, n in chk)


def v6_query(emitted, subs) -> str:
    conf = f"(SELECT PK FROM BOX_FE.T_BOX_ENGCONF_S WHERE DESCRIPTION = {subs['CONF_DESCRIPTION_SQL']})"
    appr, bpk = subs["APPROVED_INSTRUMENTS"], subs["BRANCH_PK"]
    parts = []
    for step, table, where in (("6", "T_BOX_ENGACCRCONF_S", f"FK_PARENT = {conf}"),
                               ("7", "T_BOX_CONFIG_ACCRUAL_S", f"FK_PARENT = {conf}"),
                               ("11", "T_BOX_CONF_BY_BOOK_S", f"FK_BRANCH = {bpk}"),
                               ("12", "T_BOX_ERRORS_FE_S", f"FK_BRANCH = {bpk}")):
        if step in emitted:
            parts.append(f"SELECT '{table}' AS t, FK_INSTRUMENT FROM BOX_FE.{table}\n"
                         f"WHERE  {where}\nAND   (FK_INSTRUMENT IS NULL OR FK_INSTRUMENT NOT IN ({appr})))")
    if not parts:
        return "-- (no instrument-keyed step emitted)"
    return "\nUNION ALL\n".join(parts) + ";"


def v11_queries(subs) -> str:
    conf = f"(SELECT PK FROM BOX_FE.T_BOX_ENGCONF_S WHERE DESCRIPTION = {subs['CONF_DESCRIPTION_SQL']})"
    out = []

    def q(label, cols, rows, table, where):
        exp = "\n  UNION ALL ".join(
            "SELECT " + ", ".join(f"TO_CHAR({x if x is not None else 'CAST(NULL AS NUMBER)'}) AS {sql_ident(c)}"
                                  for x, c in zip(r, cols)) + " FROM dual" for r in rows)
        act = "SELECT " + ", ".join(f"TO_CHAR({sql_ident(c)}) AS {sql_ident(c)}" for c in cols) + f" FROM {table} WHERE {where}"
        return (f"-- V11 {label}   Expect: 0 rows.\n"
                f"WITH expected AS (\n  {exp}),\n     actual AS (\n  {act})\n"
                "SELECT 'in values.json, not in BOX' AS side, e.* FROM (SELECT * FROM expected MINUS SELECT * FROM actual) e\n"
                "UNION ALL\n"
                "SELECT 'in BOX, not in values.json', a.* FROM (SELECT * FROM actual MINUS SELECT * FROM expected) a;")
    if subs.get("V11_6"):
        out.append(q("step 6 - the accrual values", ["FK_INSTRUMENT"] + STEP6_COLS,
                     [[ins] + [None if x == "NULL" else x for x in vals] for ins, vals in subs["V11_6"]],
                     "BOX_FE.T_BOX_ENGACCRCONF_S", f"FK_PARENT = {conf}"))
    if subs.get("V11_11"):
        out.append(q("step 11 - (instrument, label) pairs, books and dummy", ["FK_INSTRUMENT", "FK_LABEL"],
                     subs["V11_11"], "BOX_FE.T_BOX_CONF_BY_BOOK_S", f"FK_PARENT = {conf}"))
    if subs.get("V11_12"):
        out.append(q("step 12 - the limits", ["FK_INSTRUMENT", "LIMIT_ERRORS"], subs["V11_12"],
                     "BOX_FE.T_BOX_ERRORS_FE_S", f"FK_BRANCH = {subs['BRANCH_PK']}"))
    if subs.get("V11_14A"):
        ins = ", ".join(r[0] for r in subs["V11_14A"])
        out.append(q("step 14a - the days", ["FK_INSTRUMENT", "NUM_DAYS"], subs["V11_14A"],
                     "BOX_FE.T_BOX_ENGDAYS_MATURED_S", f"FK_INSTRUMENT IN ({ins})"))
    return "\n\n".join(out) if out else "-- (no decided step emitted)"


# ------------------------------------------------------------------------------------------------

def rendered_names(base: str) -> list[str]:
    return [f"{base}-{r}.sql" for r in OUTPUT_ROLES]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render a run's SQL from 03-sql/values.json.")
    ap.add_argument("run_folder", type=Path)
    ap.add_argument("--no-validate", action="store_true", help="skip the validator run (tests only)")
    a = ap.parse_args(argv)
    if not a.run_folder.is_dir():
        print(f"not a directory: {a.run_folder}", file=sys.stderr)
        return 2
    res = render(a.run_folder)
    print(f"\nrender_sql - {a.run_folder}\n" + "=" * 72)
    for c, p, m in res.errors:
        print(f"  REFUSED {c:<28} {p}: {m}")
    for c, p, m in res.warnings:
        print(f"  WARN    {c:<28} {p}: {m}")
    if res.errors:
        print("=" * 72 + f"\n  {len(res.errors)} problem(s) in the values - nothing written. Fix values.json "
              "(or the file named) and run again.\n")
        return 1
    sql_dir = a.run_folder / "03-sql"
    if res.nothing_to_render:
        print(f"  nothing to render: {res.nothing_to_render}\n")
        return 3
    for old in sql_dir.glob(f"{res.base}-*.sql"):
        if old.name not in res.files and old.name in rendered_names(res.base):
            old.unlink()
    for name, text in res.files.items():
        (sql_dir / name).write_text(text, encoding="ascii", newline="\n")
        print(f"  wrote   03-sql/{name}  ({text.count(chr(10))} lines)")
    (sql_dir / "render-report.md").write_text("\n".join(res.report) + "\n", encoding="utf-8")
    print("  wrote   03-sql/render-report.md\n" + "=" * 72)
    if a.no_validate:
        return 0
    return subprocess.run([sys.executable, str(HERE / "validate_run_output.py"), str(a.run_folder)]).returncode


if __name__ == "__main__":
    sys.exit(main())
