#!/usr/bin/env python3
"""
set_up_book_labels.py - the script of skill `set-up-book-labels` [operator, 2026-09-30].

    python3 scripts/set_up_book_labels.py runs/<BRANCH>/<env>/books/

A branch's books must exist as BOX labels (PGT_SYS.PGT_DOMAINS, FK_OWNER_OBJ = 17910.4) in the target before
FE step 11, the ACC MBJ properties or any batch job can use them - and so must its dummy book label. This
script reads the book folder, sorts every label into exists / to create / conflict, and writes:

  books-register.csv          every book and the dummy, with its label PK once it exists - what agents read
  book-labels-PROPOSAL.sql    only when labels are missing: the inserts, for the operator to review and run (the agent never runs it)
  book-labels-report.md       what was found, what is proposed, what blocks

Inputs, all in the book folder (it spans runs - never archived with a run):

  00-books.csv                 seq, label_code_proposed, label_description, description_source, label_pk, ...
  book-labels.json             branch PK, country code, the dummy decision, and - when labels are missing -
                               the PK rule and the model row (see skills/set-up-book-labels/SKILL.md)
  00-decisions.md              the operator's decisions the config cites (decision N)
  01-evidence/Q-10f-book-labels-target.csv    which labels exist in the target (PK, CODE, DESCRIPTION)
  01-evidence/Q-10c-dummy-book-target.csv     branches already using an existing dummy (FK_BRANCH, count)
  01-evidence/Q-10e-domains-columns.csv       the label table's columns - only when labels are missing

Exit 0 every label exists (register complete) · 1 refused · 2 bad invocation · 4 labels to create (proposal
written). scripts/render_sql.py calls evaluate() for FE step 11, so the register can never go stale.
Standard library only.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_sql  # noqa: E402
import evidence_to_sql  # noqa: E402
from render_sql import Result, V, canon, sql_text, fill, apply_sections, read_decisions  # noqa: E402

ROOT = HERE.parent
TEMPLATE = ROOT / "skills/set-up-book-labels/templates/book-labels-proposal.sql.tmpl"
BOOKS_DIR = "books"
LIST = "00-books.csv"
CONFIG = "book-labels.json"
DECISIONS = "00-decisions.md"
Q10F = "01-evidence/Q-10f-book-labels-target.csv"
Q10C_TARGET = "01-evidence/Q-10c-dummy-book-target.csv"
Q10E = "01-evidence/Q-10e-domains-columns.csv"
PROPOSAL = "book-labels-PROPOSAL.sql"
REGISTER = "books-register.csv"
REPORT = "book-labels-report.md"
LABEL_TABLE = "PGT_SYS.PGT_DOMAINS"
LABEL_OWNER_OBJ = "17910.4"                              # the Label Config screen's rows
CODE_RE = re.compile(r"X([A-Z]{2,3})(\d{2})")            # X + country code + 01.. [stated: operator, 2026-09-30]
PK_EXPR_RE = render_sql.PK_EXPR_RE
REGISTER_COLS = ["kind", "seq", "code", "description", "pk", "status", "origin", "evidence"]
# What SIGOM's Label Config screen does on save [read: DB trace of a label insert, Tier 2, operator, 2026-10-02]:
#   :RETURN := PGT_SYS.F___SEQUENCE(TABLE_NAME => PGT_DOMAINS, SEQ_RANGE => 1)   -> 24044.44 (auth code .44)
#   insert into PGT_SYS.PGT_DOMAINS (PK, FK_OWNER_OBJ, CODE, DESCRIPTION) values (...)
#   PGT_SYS.Pkg_SysPrecommit.p_DomainsPreCommit(PK => <pk>)                      -> the screen's pre-commit
# Corrected 2026-10-02 (run 7): called from SQL, SEQ_RANGE => 1 returns an INTEGER (24038, 24039 - operator); the
# auth-code fraction is added by F___SEQUENCE only for SEQ_RANGE = 'X' (Q-G3: `IF seq_range = 'X' THEN + fraction`),
# so the screen's .44 does not come from the call the trace shows. The script uses 'X' and still checks the fraction.
SCREEN_SEQ = "PGT_SYS.F___SEQUENCE(TABLE_NAME => 'PGT_DOMAINS', SEQ_RANGE => 'X')"
PRECOMMIT = "PGT_SYS.Pkg_SysPrecommit.p_DomainsPreCommit"
PK_MODES = ("screen", "fixed", "expression")


def undecided(x) -> bool:
    return x is None or (isinstance(x, str) and (not x.strip() or render_sql.PLACEHOLDER_RE.search(x) is not None))


def read_list(path: Path, res: Result) -> list[dict]:
    """Read as written: a description must match the data-lake book label exactly, spaces included."""
    try:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            return [{(k or "").strip().lower(): (x if x is not None else "") for k, x in r.items()}
                    for r in csv.DictReader(fh) if any((x or "").strip() for x in r.values())]
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        res.err("evidence-unreadable", LIST, f"cannot read: {e}")
        return []


def read_csv(path: Path, res: Result) -> list[dict]:
    try:
        return evidence_to_sql.read_rows(path)
    except SystemExit as e:
        res.err("evidence-unreadable", path.name, str(e))
    except (OSError, UnicodeDecodeError, StopIteration) as e:
        res.err("evidence-unreadable", path.name, f"cannot read: {e}")
    return []


def evaluate(folder: Path) -> tuple[Result, dict]:
    """The whole skill, without writing anything. state: books {code: pk|None}, dummy pk|None, to_create
    [codes], register [rows]; res.files holds the files to write."""
    res = Result()
    folder = Path(folder)
    state = {"books": {}, "dummy": None, "to_create": [], "register": [], "complete": False}

    # --- the book list -------------------------------------------------------------------------
    lp = folder / LIST
    if not lp.exists():
        res.err("book-list-missing", LIST, "ask the operator for the branch's books - the book labels exactly as "
                "the data lake sends them - and write 00-books.csv (skill set-up-book-labels, step 1)")
        return res, state
    books, seen_c, seen_d = [], set(), set()
    for i, r in enumerate(read_list(lp, res), 1):
        p = f"{LIST} row {i}"
        code = (r.get("label_code_proposed") or "").strip()
        desc = r.get("label_description") or ""
        if not CODE_RE.fullmatch(code):
            res.err("book-label-code-bad", p, f"{code!r}: a BOX label code is X + country code + two digits from 01 "
                    "(e.g. XNY01) - 04-add-book-procedure.md 2.4")
        if not desc.strip() or desc != desc.strip():
            res.err("values-bad-text", p, "label_description must be the data-lake book label exactly: not empty, "
                    "no leading/trailing spaces")
        if code in seen_c or desc in seen_d:
            res.err("values-duplicate", p, f"{code} / {desc!r} appears twice")
        seen_c.add(code)
        seen_d.add(desc)
        books.append({"seq": (r.get("seq") or str(i)).strip(), "code": code, "desc": desc,
                      "pk": canon(r.get("label_pk") or "")})
    if not books:
        res.err("book-list-missing", LIST, "the list has no books")
        return res, state

    # --- the configuration ---------------------------------------------------------------------
    cp = folder / CONFIG
    if not cp.exists():
        res.err("book-config-missing", CONFIG, "write book-labels.json from skills/set-up-book-labels/"
                "book-labels.example.json (branch PK, country code, the dummy decision)")
        return res, state
    try:
        cfg = json.loads(cp.read_text(encoding="utf-8-sig"), parse_float=Decimal)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        res.err("values-not-json", CONFIG, f"not valid JSON: {e}")
        return res, state
    v = V(res, read_decisions(folder / DECISIONS))
    branch_pk, _ = v.leaf_num(cfg, "branch_pk", CONFIG)
    cc, _ = v.leaf_text(cfg, "country_code", CONFIG)
    if cc and undecided(cc):
        res.err("values-placeholder", f"{CONFIG}.country_code", f"{cc!r} is not decided yet")
        cc = None
    for b in books:
        m = CODE_RE.fullmatch(b["code"])
        if m and cc and m.group(1) != cc:
            res.err("book-label-code-bad", LIST, f"{b['code']}: not X{cc}.. - the country code is {cc!r}")

    # --- what exists in the target -------------------------------------------------------------
    fp = folder / Q10F
    if not fp.exists():
        res.err("evidence-missing", Q10F, "Q-10f, in the target: which of the books' labels (and the dummy) exist")
        return res, state
    existing = [(canon(evidence_to_sql.norm_safe(r.get("PK", "")) or ""), (r.get("CODE") or "").strip(),
                 r.get("DESCRIPTION") or "") for r in read_csv(fp, res)]

    def classify(code, desc, what):
        by_code = [e for e in existing if e[1] == code]
        by_desc = [e for e in existing if desc is not None and e[2] == desc]
        if by_code and desc is not None and by_code[0][2] != desc:
            res.err("book-label-conflict", Q10F, f"{what} {code} exists with description {by_code[0][2]!r}, not "
                    f"{desc!r} - a person decides: another code, or correct the list")
            return "conflict", None
        if by_desc and by_desc[0][1] != code:
            res.err("book-label-conflict", Q10F, f"{what}: description {desc!r} exists under code {by_desc[0][1]} "
                    f"(PK {by_desc[0][0]}) - never reuse or duplicate it silently; a person decides")
            return "conflict", None
        if by_code:
            return "exists", by_code[0][0]
        return "to_create", None

    to_create = []   # (kind, code, desc, pk)
    for b in books:
        st, pk = classify(b["code"], b["desc"], "book")
        state["books"][b["code"]] = pk
        b["status"] = st
        b["found_pk"] = pk
        if st == "to_create":
            to_create.append(("book", b["code"], b["desc"], b["pk"]))

    # --- the dummy book label ------------------------------------------------------------------
    dn = cfg.get("dummy") if isinstance(cfg.get("dummy"), dict) else None
    dummy_row = None
    if not dn or undecided(dn.get("mode")):
        res.err("dummy-missing", f"{CONFIG}.dummy", "put the dummy card to the operator: the existing label other "
                "branches already use as their dummy (Q-10d) - accept it - or create one (code <CC>DUM, e.g. NYDUM; description "
                "<CC> EMPTY, e.g. NY EMPTY - both changeable, code max 5 characters)")
    else:
        dsrc = v.source(dn.get("source"), f"{CONFIG}.dummy.source")
        if not re.search(r"decision\s+\d+", dsrc, re.I):
            res.err("decision-missing", f"{CONFIG}.dummy.source", "the dummy label is the operator's decision: cite it (decision N)")
        mode = str(dn.get("mode")).strip().lower()
        dcode = str(dn.get("code") or "").strip()
        if not dcode:
            res.err("values-missing-field", f"{CONFIG}.dummy.code", "the dummy label's CODE")
        elif len(dcode) > 5:
            res.err("dummy-code-too-long", f"{CONFIG}.dummy.code", f"{dcode!r}: a label code is at most 5 characters - "
                    f"propose {(cc or '<CC>')}DUM")
        elif dcode in {b["code"] for b in books}:
            res.err("dummy-is-a-book", f"{CONFIG}.dummy.code", f"{dcode} is one of the branch's books - the dummy is "
                    "a BOX FE rule and never a real book's label (run 4, run 6)")
        elif mode == "existing":
            st, pk = classify(dcode, None, "dummy")
            if st != "exists":
                res.err("dummy-label-not-in-target", Q10F, f"{dcode} is not in the target - put the dummy card again "
                        "(another existing label, or create one)")
            else:
                others = []
                tp = folder / Q10C_TARGET
                if not tp.exists():
                    res.err("evidence-missing", Q10C_TARGET, "Q-10c (c) in the target with the dummy's PK: the branches "
                            "already using it - a dummy is shared")
                for r in read_csv(tp, res) if tp.exists() else []:
                    bb = canon(evidence_to_sql.norm_safe(r.get("FK_BRANCH", "")) or "")
                    n = next((canon(evidence_to_sql.norm_safe(x) or "") for k, x in r.items() if k != "FK_BRANCH"), None)
                    if bb and bb != branch_pk and n and Decimal(n) > 0:
                        others.append(bb)
                if tp.exists() and not others:
                    res.err("dummy-not-in-use", Q10C_TARGET, f"no other branch uses {dcode} (PK {pk}) - a dummy is "
                            "shared by many branches (run 6 picked the branch's own book). Put the dummy card again")
                state["dummy"] = pk
                dummy_row = {"code": dcode, "desc": next((e[2] for e in existing if e[1] == dcode), ""), "pk": pk,
                             "status": "exists", "origin": "existing", "evidence": f"{Q10F}; {Q10C_TARGET}"}
        elif mode == "create":
            ddesc = dn.get("description")
            if undecided(ddesc):
                res.err("values-missing-field", f"{CONFIG}.dummy.description", "the new dummy label's DESCRIPTION")
            else:
                st, pk = classify(dcode, str(ddesc), "dummy")
                if st == "exists":       # created by an earlier round of this skill: no users yet, that is expected
                    state["dummy"] = pk
                    dummy_row = {"code": dcode, "desc": str(ddesc), "pk": pk, "status": "exists", "origin": "created",
                                 "evidence": Q10F}
                elif st == "to_create":
                    to_create.append(("dummy", dcode, str(ddesc), canon(dn.get("pk") or "")))
                    dummy_row = {"code": dcode, "desc": str(ddesc), "pk": "", "status": "to_create",
                                 "origin": "created", "evidence": f"{CONFIG} (decision)"}
        else:
            res.err("dummy-missing", f"{CONFIG}.dummy.mode", "'existing' or 'create'")

    # --- the proposal for what is missing -------------------------------------------------------
    state["to_create"] = [c for _, c, _, _ in to_create]
    if to_create:
        render_proposal(folder, cfg, v, res, to_create, existing, len(books) - sum(1 for k, *_ in to_create if k == "book"))

    # --- the register ------------------------------------------------------------------------
    rows = [{"kind": "book", "seq": b["seq"], "code": b["code"], "description": b["desc"], "pk": b.get("found_pk") or "",
             "status": b.get("status", "?"), "origin": "existing" if b.get("status") == "exists" else "",
             "evidence": Q10F} for b in books]
    if dummy_row:
        rows.append({"kind": "dummy", "seq": "", "code": dummy_row["code"], "description": dummy_row["desc"],
                     "pk": dummy_row["pk"] or "", "status": dummy_row["status"], "origin": dummy_row["origin"],
                     "evidence": dummy_row["evidence"]})
    state["register"] = rows
    state["complete"] = not res.errors and not to_create and state["dummy"] is not None
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=REGISTER_COLS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    res.files[REGISTER] = out.getvalue()
    res.files[REPORT] = report(rows, res, state)
    return res, state


def render_proposal(folder, cfg, v, res, to_create, existing, n_found) -> None:
    P = CONFIG
    pkn = cfg.get("pk_rule") if isinstance(cfg.get("pk_rule"), dict) else {}
    mode = str(pkn.get("mode", "")).strip().lower()
    if not pkn or undecided(pkn.get("mode")):
        res.err("book-labels-rule-missing", f"{P}.pk_rule", f"{len(to_create)} label(s) to create "
                f"({', '.join(c for _, c, _, _ in to_create)}): write pk_rule - 'screen' (what SIGOM's Label Config does, "
                "source Q-10g) unless the BOX FE team gave fixed PKs - and model_columns")
        return
    src = v.source(pkn.get("source"), f"{P}.pk_rule.source")
    if mode != "screen" and not re.search(r"decision\s+\d+", src, re.I):
        res.err("decision-missing", f"{P}.pk_rule.source", "fixed PKs or another expression are a decision: cite it")
    auth, frac = None, None
    if cfg.get("auth_code") is not None or mode == "screen":
        auth, _ = v.leaf_num(cfg, "auth_code", CONFIG)
        if auth:
            frac = Decimal("0." + str(auth).split(".")[0])
        elif mode == "screen":
            res.err("book-label-auth-code", f"{P}.auth_code", "the target's auth code (FE Q-G3c, e.g. 44): every PK the "
                    "sequence gives must carry it as its fraction")
    expr = None
    if mode == "screen":
        expr = SCREEN_SEQ
    elif mode == "expression":
        expr = str(pkn.get("value", "")).strip()
        if not PK_EXPR_RE.fullmatch(expr):
            res.err("book-label-pk-rule", f"{P}.pk_rule.value", "the allocation expression the BOX FE team names, "
                    "e.g. <OWNER>.F___SEQUENCE('<TABLE>','X')")
    elif mode == "fixed":
        used = {e[0] for e in existing}
        seen = set()
        for kind, code, _, pk in to_create:
            if pk is None:
                res.err("book-label-pk-missing", LIST if kind == "book" else f"{P}.dummy.pk",
                        f"{code}: no PK - with pk_rule fixed the BOX FE team gives each one")
            elif pk in seen or pk in used:
                res.err("values-duplicate", LIST, f"{code}: PK {pk} is used twice or already exists")
            elif frac is not None and Decimal(pk) % 1 != frac:
                res.err("book-label-pk-auth-code", LIST, f"{code}: PK {pk} does not carry the auth code .{auth}")
            seen.add(pk)
    else:
        res.err("book-label-pk-rule", f"{P}.pk_rule.mode", "'screen' (default, as SIGOM does), 'fixed' or 'expression'")
    cp = folder / Q10E
    if not cp.exists():
        res.err("evidence-missing", Q10E, "Q-10e, the target's columns of PGT_SYS.PGT_DOMAINS")
        return
    have = {r["COLUMN_NAME"].strip().upper(): r for r in read_csv(cp, res) if r.get("COLUMN_NAME")}
    names, lits = ["PK", "CODE", "DESCRIPTION"], []
    for i, c in enumerate(cfg.get("model_columns") or []):
        p = f"{P}.model_columns[{i}]"
        if not isinstance(c, dict) or not c.get("name"):
            res.err("values-wrong-type", p, "expected {name, value, source}")
            continue
        name = str(c["name"]).strip().upper()
        v.source(c.get("source"), p + ".source")
        if name in names:
            res.err("values-duplicate", p, f"{name}: PK, CODE and DESCRIPTION come from the list, not here")
            continue
        col = have.get(name)
        if not col:
            res.err("target-column-missing", p, f"{LABEL_TABLE} has no column {name} (Q-10e)")
            continue
        x, typ = c.get("value"), col.get("DATA_TYPE", "").upper()
        if x is None:
            if col.get("NULLABLE", "Y").strip().upper() == "N":
                res.err("target-null-in-not-null", p, f"{name} is NOT NULL")
            lit = "NULL"
        elif re.match(r"N?VARCHAR2|N?CHAR", typ):
            lit = sql_text(str(x))
        elif re.match(r"NUMBER|FLOAT|INTEGER", typ):
            lit = canon(x) or ""
            if not lit:
                res.err("values-not-a-number", p, f"{name}: {x!r}")
        elif re.match(r"DATE|TIMESTAMP", typ) and str(x).strip().upper() == "SYSDATE":
            lit = "SYSDATE"
        else:
            res.err("target-column-type", p, f"{name}: type {typ} / value {x!r} not supported")
            continue
        if name == "FK_OWNER_OBJ" and lit != LABEL_OWNER_OBJ:
            res.err("book-label-owner", p, f"FK_OWNER_OBJ must be {LABEL_OWNER_OBJ} (the Label Config screen)")
        names.append(name)
        lits.append(lit)
    if "FK_OWNER_OBJ" not in names:
        res.err("values-missing-field", f"{P}.model_columns", f"FK_OWNER_OBJ = {LABEL_OWNER_OBJ} is required")
    for name, col in have.items():
        if col.get("NULLABLE", "Y").strip().upper() == "N" and col.get("HAS_DEFAULT", "N").strip().upper() != "Y" \
                and name not in names:
            res.err("target-not-null-not-written", P, f"{name} is NOT NULL in {LABEL_TABLE} and not set")
    dlen = canon((have.get("DESCRIPTION") or {}).get("DATA_LENGTH", ""))
    clen = canon((have.get("CODE") or {}).get("DATA_LENGTH", ""))
    for _, c, d, _ in to_create:
        if dlen and len(d.encode("utf-8")) > int(Decimal(dlen)):
            res.err("target-text-too-long", LIST, f"{c}: description longer than {dlen} bytes")
        if clen and len(c) > int(Decimal(clen)):
            res.err("target-text-too-long", LIST, f"{c}: code longer than {clen} bytes")
    if res.errors:
        return
    ins, decls = [], ""
    cols = ", ".join(names)
    if mode == "screen":                 # as the screen: allocate and check every PK first, then insert + pre-commit
        decls = "  TYPE t_pk IS TABLE OF NUMBER INDEX BY PLS_INTEGER;\n  v_pk t_pk;"
        for i, (kind, c, d, _) in enumerate(to_create, 1):
            ins.append(f"  v_pk({i}) := {SCREEN_SEQ};   -- {c} ({kind})\n"
                       f"  IF MOD(v_pk({i}), 1) <> {frac} THEN\n"
                       f"    RAISE_APPLICATION_ERROR(-20003, 'LABELS STOPPED - PK ' || v_pk({i}) || ' for {c} does not "
                       f"carry auth code .{auth}. Nothing inserted.');\n  END IF;\n"
                       f"  SELECT COUNT(*) INTO v_n FROM {LABEL_TABLE} WHERE PK = v_pk({i});\n"
                       f"  IF v_n > 0 THEN\n"
                       f"    RAISE_APPLICATION_ERROR(-20004, 'LABELS STOPPED - PK ' || v_pk({i}) || ' for {c} is already used. "
                       f"Nothing inserted.');\n  END IF;")
        for i, (kind, c, d, _) in enumerate(to_create, 1):
            ins.append(f"  INSERT INTO {LABEL_TABLE} ({cols})\n"
                       f"  VALUES (v_pk({i}), {sql_text(c)}, {sql_text(d)}{''.join(', ' + x for x in lits)});\n"
                       f"  {PRECOMMIT}(PK => v_pk({i}));\n"
                       f"  DBMS_OUTPUT.PUT_LINE('{c} -> PK ' || v_pk({i}));")
    else:
        for kind, c, d, pk in to_create:
            pk_lit = expr if mode == "expression" else pk
            ins.append(f"  -- {c} ({kind})\n  INSERT INTO {LABEL_TABLE} ({cols})\n"
                       f"  VALUES ({pk_lit}, {sql_text(c)}, {sql_text(d)}{''.join(', ' + x for x in lits)});\n"
                       + (f"  {PRECOMMIT}(PK => {pk});" if mode == "fixed" else
                          f"  SELECT MAX(PK) INTO v_n FROM {LABEL_TABLE} WHERE FK_OWNER_OBJ = {LABEL_OWNER_OBJ} "
                          f"AND CODE = {sql_text(c)};\n  {PRECOMMIT}(PK => v_n);"))
    pk_guard = ""
    if mode == "fixed":
        pk_guard = (f"  SELECT COUNT(*) INTO v_n FROM {LABEL_TABLE} WHERE PK IN ({', '.join(pk for *_, pk in to_create)});\n"
                    "  IF v_n > 0 THEN\n"
                    "    RAISE_APPLICATION_ERROR(-20002, 'LABELS STOPPED - ' || v_n || ' of the fixed PKs are already used. Nothing inserted.');\n"
                    "  END IF;")
    subs = dict(BRANCH_CODE=render_sql.ascii_comment(cfg.get("branch_code", "")),
                TARGET_ENV=render_sql.ascii_comment(cfg.get("env", "")), TABLE=LABEL_TABLE, OWNER_OBJ=LABEL_OWNER_OBJ,
                N=str(len(to_create)), N_FOUND=str(n_found), CODES=", ".join(sql_text(c) for _, c, _, _ in to_create),
                DESCS=", ".join(sql_text(d) for _, _, d, _ in to_create), INSERTS="\n".join(ins), PK_GUARD=pk_guard,
                DECLS=decls, PK_RULE=("fixed PKs given by the BOX FE team" if mode == "fixed" else
                                      f"allocated by {expr}, as the SIGOM Label Config screen does (Q-10g)"
                                      if mode == "screen" else f"allocated by {expr}"),
                DECISIONS=", ".join(re.findall(r"decision\s+(\d+)", src, re.I)) or "-")
    text = fill(apply_sections(TEMPLATE.read_text(encoding="utf-8"), set(), res, "labels"), subs, res, "labels")
    if any(ord(ch) > 126 for ch in text):
        res.err("output-not-ascii", PROPOSAL, "non-ASCII character in the rendered file")
    res.files[PROPOSAL] = re.sub(r"\n{3,}", "\n\n", text)


def report(rows, res: Result, state: dict) -> str:
    n = {s: sum(1 for r in rows if r["status"] == s) for s in ("exists", "to_create", "conflict")}
    lines = ["# Book labels - report", "", "Written by `scripts/set_up_book_labels.py` (skill `set-up-book-labels`). "
             "Do not edit; change the inputs and run it again.", "",
             f"- Books: {sum(1 for r in rows if r['kind'] == 'book')} - exist {n['exists'] - (1 if state['dummy'] else 0)}, "
             f"to create {n['to_create']}, conflicts {n['conflict']}",
             f"- Dummy: {next((r['code'] + ' (' + r['status'] + ')' for r in rows if r['kind'] == 'dummy'), 'not decided')}",
             f"- Complete (every label exists): **{'yes' if state['complete'] else 'no'}**", ""]
    if res.errors:
        lines += ["## Blocking", ""] + [f"- `{c}` {p}: {m}" for c, p, m in res.errors] + [""]
    if PROPOSAL in res.files:
        lines += ["## Next", "", f"The operator reviews and runs `{PROPOSAL}` (it stops if any label already exists, "
                  "and does not commit), then the operator re-runs Q-10f and this script.", ""]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or not Path(argv[0]).is_dir():
        print("usage: set_up_book_labels.py <BOOK_FOLDER>   (runs/<BRANCH>/<env>/books/)", file=sys.stderr)
        return 2
    folder = Path(argv[0])
    res, state = evaluate(folder)
    print(f"\nset_up_book_labels - {folder}\n" + "=" * 72)
    for c, p, m in res.errors:
        print(f"  REFUSED {c:<28} {p}: {m}")
    for name in (REGISTER, REPORT):
        if name in res.files:
            (folder / name).write_text(res.files[name], encoding="utf-8")
            print(f"  wrote   {name}")
    prop = folder / PROPOSAL
    if PROPOSAL in res.files and not res.errors:
        prop.write_text(res.files[PROPOSAL], encoding="ascii", newline="\n")
        print(f"  wrote   {PROPOSAL}  - for the operator to run: {len(state['to_create'])} label(s) to create")
    elif prop.exists() and not state["to_create"]:
        prop.unlink()
    print("=" * 72)
    if res.errors:
        return 1
    if state["to_create"]:
        return 4
    print("  every label exists - the register is complete.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
