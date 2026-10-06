#!/usr/bin/env python3
"""
explain_job.py - what one BOX batch job is and runs, from files only (no database) [2026-10-06].

    python3 scripts/explain_job.py runs/_reference/<env>/ GMBOX0028D01 \
        --controlm <folder repo dir or .json> [...] --dml <cib-boxfin-dbboxfe dir> [<cib-boxacc-dbboxacc dir>] \
        [--mbj <J-R2 export .csv>]

Skill `explain-box-job` (overview depth). Reads, in this order (box-batch-chain.md):
  L1  the Control-M job in the folder repos given: folder, repo file:line, Description, When, waits / emits;
  L2  its binding in jobs-inventory.csv: the EXECUTED one (FE = db.conf f_ExecuteGroup; ACC = shell.conf mbjbox.sh,
      whose group / book come from the MBJ row - J-R2 export as .csv via --mbj, else "ask J-R2");
  L3  the group header and its events in order, by name, from the repo DML (dml/03-PGT_PRC/<newest rX.Y.Z>/
      05_Static-Data: data_groupevents_<PK>.sql, data_eventsheader_<PK>.sql / data_t_pgt_eve_s.sql).
Prints markdown; every line says where it came from. What a file cannot tell is said, not guessed: the event
lines are from names only (INFERRED); entries (debit / credit) need depth `event` (J-C3 / J-C4, or the repo file).
Used by box-batch-jobs-agent (EXPLAIN overview, optional shortcut) and box-fe-jobs-agent (questions mid-run, and
the cards build_fe_jobs.py writes). Standard library only. Exit 0 · 1 refused · 2 bad invocation.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from parse_job_confs import split_args, decode_name, INSTR_FAMILY  # noqa: E402

INV = "jobs-inventory.csv"
INSERT_RE = re.compile(r"insert\s+into\s+(?:\w+\.)?(T_PGT_BR_EVE_S|T_PGT_BR_EVE_EXT_S|T_PGT_EVE_S)\s*\(([^)]*)\)\s*values\s*\(",
                       re.I)


class Result:
    def __init__(self):
        self.errors = []

    def err(self, code, where, msg):
        self.errors.append((code, where, msg))


def _events(node):
    if isinstance(node, dict):
        if isinstance(node.get("Event"), str):
            yield node["Event"]
        for v in node.values():
            yield from _events(v)
    elif isinstance(node, list):
        for v in node:
            yield from _events(v)


def load_controlm(paths) -> dict:
    """job -> {repo, file, line, folder, obj, waits, adds} over every SimpleFolder JSON under the paths."""
    out = {}
    for p in paths:
        p = Path(p)
        files = sorted(p.rglob("*.json")) if p.is_dir() else [p]
        for f in files:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                root = json.loads(text)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(root, dict):
                continue
            for fname, folder in root.items():
                if not (isinstance(folder, dict) and "Folder" in str(folder.get("Type", ""))):
                    continue
                for k, v in folder.items():
                    if isinstance(v, dict) and str(v.get("Type", "")).startswith("Job"):
                        m = re.search(r'"' + re.escape(k) + r'"\s*:\s*\{', text)
                        out[k] = {"repo": p.name if p.is_dir() else f.parent.parent.name, "file": f.name,
                                  "line": text.count("\n", 0, m.start()) + 1 if m else 0, "folder": fname, "obj": v,
                                  "waits": list(_events(v.get("eventsToWaitFor", {}))),
                                  "adds": list(_events(v.get("eventsToAdd", {})))}
    return out


def _ver(path: Path):
    m = re.search(r"r(\d+)\.(\d+)\.(\d+)", str(path))
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def _num(s: str) -> str:
    s = s.strip().strip("'")
    try:
        return format(float(s), "f").rstrip("0").rstrip(".") if re.fullmatch(r"-?\d+(\.\d+)?", s) else s
    except ValueError:
        return s


def load_dml(repos) -> dict:
    """{'groups': {pk: name}, 'members': {group_pk: [(order, event_pk)]}, 'events': {pk: name}, 'src': {key: file}};
    the newest release folder wins (later releases re-insert the same PK)."""
    idx = {"groups": {}, "members": {}, "events": {}, "src": {}}
    files = []
    for r in repos:
        base = Path(r)
        files += [f for f in base.rglob("*.sql") if "03-PGT_PRC" in str(f) or "PGT_PRC" in f.name.upper()]
    for f in sorted(files, key=lambda x: (_ver(x), str(x))):     # oldest first: newer overwrite
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        seen_members = set()
        for m in INSERT_RE.finditer(text):
            table, cols = m.group(1).upper(), [c.strip().upper() for c in m.group(2).split(",")]
            vals = split_args(text[m.end():])
            row = dict(zip(cols, vals))
            where = f"{f.name}:{text.count(chr(10), 0, m.start()) + 1}"
            if table == "T_PGT_BR_EVE_S" and "PK" in row:
                pk = _num(row["PK"])
                idx["groups"][pk] = row.get("GROUPDESCRIP", "").strip().strip("'")
                idx["src"]["g" + pk] = where
            elif table == "T_PGT_BR_EVE_EXT_S" and "FK_PARENT" in row:
                g = _num(row["FK_PARENT"])
                if g not in seen_members:                      # a file re-defining a group replaces its members
                    idx["members"][g] = []
                    seen_members.add(g)
                idx["members"][g].append((_num(row.get("ORDERTOEXECUTE", "0")), _num(row.get("EVENTCODE", ""))))
                idx["src"]["m" + g] = where
            elif table == "T_PGT_EVE_S" and "PK" in row:
                pk = _num(row["PK"])
                idx["events"][pk] = row.get("NAME", "").strip().strip("'")
                idx["src"]["e" + pk] = where
    return idx


def load_mbj(path) -> dict:
    out = {}
    if path and Path(path).exists():
        for r in csv.DictReader(Path(path).open(encoding="utf-8-sig")):
            r = {k.upper(): v for k, v in r.items()}
            if r.get("JOB_NAME"):
                out[r["JOB_NAME"].strip()] = r
    return out


def describe(job: str, inv: list, cm: dict, dml: dict, mbj: dict) -> dict:
    """Everything the files say about one job. Keys: found, side, product, level, conf, group, group_name, events,
    controlm (dict or None), mbj (row or None), notes [str]."""
    rows = [r for r in inv if r["job"] == job]
    live = [r for r in rows if r.get("active") == "Y" and r.get("executed", "Y") == "Y"]
    legacy = [r for r in rows if r.get("executed") == "N-legacy"]
    d = decode_name(job)
    info = {"job": job, "found": bool(rows) or job in cm, "notes": [], "controlm": cm.get(job), "mbj": mbj.get(job),
            "family": (rows[0]["family"] if rows else ("GBO" if job.startswith("GMGB") else "")),
            "conf": "", "side": "", "group": "", "group_name": "", "events": [], "branch": "", "instrument": "",
            "level": ("branch level" if d.get("book_no") == "00" else f"book {d['book_no']}") if d.get("book_no")
            else ("old name: level not in the name" if d.get("naming") == "old-numbered" else ""),
            "product": INSTR_FAMILY.get(d.get("instr_no", ""), "")}
    r = live[0] if live else None
    if r:
        info["conf"] = f"{r['file']}:{r['line']}"
        info["side"] = "FE" if r["file"] == "db.conf" else ("ACC" if "mbjbox" in (r.get("entry") or "").lower() else "script")
        info["branch"], info["instrument"] = r.get("branch") or r.get("token", ""), r.get("instrument", "")
        if r["file"] == "db.conf":
            info["group"] = r.get("group", "")
    elif rows:
        info["notes"].append("no active executed conf line")
    if legacy:
        info["notes"].append(f"legacy db.conf line (not executed): db.conf:{legacy[0]['line']}")
    if info["side"] == "ACC":
        m = info["mbj"]
        if m:                                                  # J-R2 export columns
            info["group"] = _num(m.get("GROUP_PK") or m.get("FK_GROUP") or "")
            info["instrument"] = m.get("INSTRUMENT") or m.get("INSTR_PK") or info["instrument"]
            info["branch"] = m.get("BRANCH") or info["branch"]
            if m.get("LABEL_CODE"):
                info["notes"].append(f"MBJ row: label `{m['LABEL_CODE']}`")
        else:
            info["notes"].append("ACC job: its group, instrument and book are in its MBJ row - J-R2 (or --mbj)")
    if not info["side"] and info["controlm"]:
        sub = str(info["controlm"]["obj"].get("SubApplication", "")).upper()
        info["side"] = "FE" if "FINANCIAL" in sub else ("ACC" if "ACCOUNT" in sub else "")
    g = info["group"]
    if g:
        info["group_name"] = dml["groups"].get(g, "") or ((info["mbj"] or {}).get("GROUPDESCRIP") or "")
        ev = sorted(dml["members"].get(g, []), key=lambda x: float(x[0]) if re.fullmatch(r"-?\d+(\.\d+)?", x[0]) else 0)
        info["events"] = [(o, e, dml["events"].get(e, "")) for o, e in ev]
        if not ev:
            info["notes"].append(f"group {g}: its events are not in the repo DML given - J-C2 in the environment")
    return info


def render(info: dict) -> str:
    j, c = info["job"], info["controlm"]
    out = [f"### `{j}`", ""]
    if not info["found"]:
        return "\n".join(out + ["Not in the inventory nor in the Control-M repos given - which repo holds it?", ""])
    what = " · ".join(x for x in (info["family"], info["side"], info["product"] or "", info["level"]) if x)
    out.append(f"- **What:** {what or '-'}" + (f" — *{c['obj'].get('Description', '')}*" if c else ""))
    if c:
        w = c["obj"].get("When", {}) if isinstance(c["obj"].get("When"), dict) else {}
        when = ", ".join(f"{k} {w[k]}" for k in ("FromTime", "EndDate", "MonthDaysCalendar") if w.get(k))
        out.append(f"- **L1 Control-M:** folder `{c['folder']}` (`{c['repo']}/{c['file']}:{c['line']}`)"
                   + (f"; {when}" if when else "") + f"; waits {', '.join(c['waits']) or 'nothing'}; emits "
                   f"{', '.join(c['adds']) or 'nothing'}  — CONFIRMED")
    else:
        out.append("- **L1 Control-M:** not in the repos given")
    if info["conf"]:
        b = f"; branch `{info['branch']}`, instrument `{info['instrument']}`" if info["branch"] or info["instrument"] else ""
        out.append(f"- **L2 binding:** `{info['conf']}` ({'runs' if info['side'] else 'line'}){b}  — CONFIRMED")
    if info["group"]:
        out.append(f"- **L3 group:** `{info['group']}` {info['group_name'] or '(name: not in the repo DML given)'}")
        for o, e, n in info["events"]:
            out.append(f"  - {o}. `{e}` {n or '(name not found)'}  — meaning from its name only: INFERRED")
    out += [f"- *{n}*" for n in info["notes"]]
    out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("env_folder")
    ap.add_argument("jobs", nargs="+")
    ap.add_argument("--controlm", nargs="*", default=[])
    ap.add_argument("--dml", nargs="*", default=[])
    ap.add_argument("--mbj")
    a = ap.parse_args(argv)
    res = Result()
    invp = Path(a.env_folder) / INV
    if not invp.exists():
        res.err("inventory-missing", str(invp), "run scripts/parse_job_confs.py on the environment folder")
    for p in [*a.controlm, *a.dml, *([a.mbj] if a.mbj else [])]:
        if not Path(p).exists():
            res.err("path-missing", p, "not found - attach that repo (or fix the path) and run again")
    for c, w, m in res.errors:
        print(f"REFUSED {c}: {w}: {m}", file=sys.stderr)
    if res.errors:
        return 1
    inv = list(csv.DictReader(invp.open(encoding="utf-8")))
    cm, dml, mbj = load_controlm(a.controlm), load_dml(a.dml), load_mbj(a.mbj)
    for j in a.jobs:
        print(render(describe(j.strip(), inv, cm, dml, mbj)))
    if not a.controlm:
        print("*(no --controlm: Control-M level not read)*")
    if not a.dml:
        print("*(no --dml: group and event names not read - J-C2 / J-X2, or attach the DB repo)*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
