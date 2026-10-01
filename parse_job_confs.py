#!/usr/bin/env python3
"""
parse_job_confs.py - read an environment's batch job configuration into one inventory [operator, 2026-10-01].

    python3 scripts/parse_job_confs.py runs/_reference/<env>/

Two files on the Unix app tree bind a Control-M job name to what it runs (the job name is the link):

  db.conf     database jobs   <JOB>:<type>:<flag>:<PL/SQL call>;      e.g. ...f_ExecuteGroup(group, branch, ...)
  shell.conf  Unix scripts    <JOB>:<debug>:<chdir>:<script> <params>  e.g. mbjbox.sh <JOB> $ODATE 0000

Writes <folder>/jobs-inventory.csv - one row per job line (active or commented out) - and prints counts.
Nothing is inferred beyond what a line says: the banner/comment above it, the call and its arguments, and
the job name decoded by the conventions below. Standard library only.

Job names (box-batch-chain.md L2):
  GMBX<n><CC><nn>D<ss>   new BOX convention: n = instrument family (0 = generic), CC = branch token
                         (label code without its X: XES02 -> ES02), nn = book number, ss = step
  GMBOX<nnnn>D<ss>       old BOX numbering [stated: BOX dev via operator, 2026-10-01 - old jobs keep it]
  GMBOX<CC><nn>D<ss>     BOX branch-level jobs (e.g. ALM flags per branch)
  GMGB...                GBO jobs - context only, never a template
A job is classed BOX by its name, or by what it runs (mbjbox.sh; a BOX_* schema in the call), or by a
'BOX' banner - the reason is recorded, so an old or odd name is still found.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

FILES = ("db.conf", "shell.conf")
OUT = "jobs-inventory.csv"
COLS = ["file", "line", "active", "job", "family", "box_reason", "naming", "instr_no", "token", "book_no", "step",
        "scope", "banner", "note", "flags", "chdir", "entry", "group", "branch", "date", "instrument", "mode", "label",
        "sublabel", "params"]
NEW_RE = re.compile(r"GMBX(\d)([A-Z]{2})(\d{2})D(\d{2})")
OLD_RE = re.compile(r"GMBOX(\d{4})D(\d{2})")
BRANCH_LEVEL_RE = re.compile(r"GMBOX([A-Z]{2})(\d{2})D(\d{2})")
JOB_RE = re.compile(r"\s*([A-Z][A-Z0-9_]{3,})\s*:")
CALL_RE = re.compile(r"((?:[A-Za-z_][\w$#]*\.){1,2})([A-Za-z_][\w$#]*)\s*\(")
EXEC_GROUP_ARGS = ["group", "branch", "date", "instrument", "mode", "label", "sublabel"]
# instrument families of GMBX<n> - 0, 1, 3 [stated: team runbook]; 6 FRA [shell.conf banners]; 2, 5 [Devin];
# 4 CCS, 6 FRA, 7 OTC Option [read: Madrid MBJ rows, 2026-10-01]
INSTR_FAMILY = {"0": "generic", "1": "depos / MM", "2": "commodities", "3": "IRS / swap", "4": "CCS",
                "5": "CFM", "6": "FRA", "7": "OTC option"}


def split_args(s: str) -> list[str]:
    """Top-level comma split of an argument list (respects nested parentheses and quotes)."""
    out, depth, cur, q = [], 0, "", False
    for ch in s:
        if ch == "'":
            q = not q
        if not q and ch == "(":
            depth += 1
        elif not q and ch == ")":
            if depth == 0:
                break
            depth -= 1
        if not q and depth == 0 and ch == ",":
            out.append(cur.strip())
            cur = ""
            continue
        cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def short(arg: str) -> str:
    """PGT_ES.PKG_GMBATCHPROCESS.CST_PK_SWAP -> CST_PK_SWAP; f_getPKByLabel('XES02') -> label:XES02."""
    m = re.search(r"f_getPKByLabel\s*\(\s*'([^']*)'", arg, re.I)
    if m:
        return f"label:{m.group(1)}"
    a = arg.strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", a):
        return a
    return a.split(".")[-1] if re.fullmatch(r"[A-Za-z_][\w$#.]*", a) else a


def decode_name(job: str) -> dict:
    m = NEW_RE.fullmatch(job)
    if m:
        return {"naming": "new", "instr_no": m.group(1), "token": m.group(2), "book_no": m.group(3), "step": "D" + m.group(4),
                "scope": "generic" if m.group(1) == "0" else f"product: {INSTR_FAMILY.get(m.group(1), '?')}"}
    m = OLD_RE.fullmatch(job)
    if m:
        return {"naming": "old-numbered", "step": "D" + m.group(2), "scope": "unknown (old name)"}
    m = BRANCH_LEVEL_RE.fullmatch(job)
    if m:
        return {"naming": "box-branch-level", "token": m.group(1), "book_no": m.group(2), "step": "D" + m.group(3),
                "scope": "branch-level"}
    if job.startswith("GMGB"):
        return {"naming": "gbo"}
    if job.startswith(("GMBX", "GMBOX")):
        return {"naming": "box-other", "scope": "unknown"}
    return {"naming": "other"}


def parse_file(path: Path) -> list[dict]:
    kind = path.name
    rows, top, sub, note = [], "", "", ""
    for n, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        active = "Y"
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            if JOB_RE.match(body) and body.count(":") >= 3:     # a commented-out job line
                line, active = body, "N"
            else:
                text = body.rstrip("#").strip()
                if re.match(r"^#{10,}", line):
                    top, sub, note = text, "", ""
                elif re.match(r"^#{3,}", line):
                    sub, note = text, ""
                elif text and not text.startswith("$Header"):
                    note = text
                continue
        m = JOB_RE.match(line)
        if not m:
            continue
        parts = [p.strip() for p in line.split(":", 3 if kind == "db.conf" else 4)]
        job = parts[0]
        banner = top + (" / " + sub if sub else "")
        r = {c: "" for c in COLS}
        r.update(file=kind, line=str(n), active=active, job=job, banner=banner, note=note)
        r.update(decode_name(job))
        call = parts[3].rstrip(";").strip() if len(parts) > 3 else ""
        if kind == "db.conf":
            r["flags"] = ":".join(parts[1:3])
            cm = CALL_RE.search(call)
            if cm:
                r["entry"] = (cm.group(1) + cm.group(2))
                args = split_args(call[cm.end():])
                if cm.group(2).lower().startswith("f_executegroup"):
                    for k, a in zip(EXEC_GROUP_ARGS, args):
                        r[k] = short(a)
                else:
                    r["params"] = " | ".join(short(a) for a in args)
        else:                       # jobs : debug : chdir : shell script : params
            r["flags"] = parts[1] if len(parts) > 1 else ""
            r["chdir"] = parts[2] if len(parts) > 2 else ""
            if len(parts) > 4:
                r["entry"], r["params"] = call, parts[4].strip()
            else:
                sp = call.split(None, 1)
                r["entry"] = sp[0] if sp else ""
                r["params"] = sp[1] if len(sp) > 1 else ""
            call = (r["entry"] + " " + r["params"]).strip()
        reasons = []
        if r["naming"] in ("new", "old-numbered", "box-branch-level", "box-other"):
            reasons.append("name")
        if r["entry"].lower().endswith("mbjbox.sh"):
            reasons.append("mbjbox.sh")
        if re.search(r"\bBOX_(SYS|FE|ACC)\.", call, re.I):
            reasons.append("BOX schema in call")
        if re.search(r"\bBOX\b", banner + " " + note):
            reasons.append("BOX banner")
        r["box_reason"] = "+".join(reasons)
        if r["naming"] == "gbo":     # GMGB = GBO [stated: operator, 2026-09-29], whatever banner it sits under
            r["family"], r["box_reason"] = "GBO", ""
        else:
            r["family"] = "BOX" if reasons else "OTHER"
        rows.append(r)
    return rows


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or not Path(argv[0]).is_dir():
        print("usage: parse_job_confs.py <ENV_FOLDER>   (holds db.conf and/or shell.conf)", file=sys.stderr)
        return 2
    folder = Path(argv[0])
    found = [folder / f for f in FILES if (folder / f).exists()]
    if not found:
        print(f"no db.conf or shell.conf in {folder}", file=sys.stderr)
        return 1
    rows = [r for p in found for r in parse_file(p)]
    with (folder / OUT).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    box = [r for r in rows if r["family"] == "BOX" and r["active"] == "Y"]
    print(f"\nparse_job_confs - {folder}\n" + "=" * 72)
    print(f"  job lines: {len(rows)} ({sum(r['active'] == 'N' for r in rows)} commented out)")
    for k, v in sorted(Counter((r["file"], r["family"]) for r in rows if r["active"] == "Y").items()):
        print(f"  {k[0]:<11} {k[1]:<6} {v}")
    print(f"  active BOX jobs by naming: {dict(Counter(r['naming'] for r in box))}")
    print(f"  active BOX jobs by token : {dict(Counter(r['token'] or '-' for r in box))}")
    print(f"  active BOX jobs by scope : {dict(Counter(r['scope'] or '-' for r in box))}")
    print(f"  wrote {OUT}\n" + "=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
