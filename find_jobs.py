#!/usr/bin/env python3
"""
find_jobs.py - answer "which BOX jobs ... and in what order" from the job inventory and Control-M [2026-10-01].

    python3 scripts/find_jobs.py runs/_reference/tier1-prod/ --side FE --product depos --branch SLB \
        --controlm <dir of a Control-M folder repo> [<another dir> ...] [--out <file stem>]

Reads <env folder>/jobs-inventory.csv (written by parse_job_confs.py). Keeps active BOX rows that are
EXECUTED (a db.conf line of a job also in shell.conf is legacy - box-batch-chain.md L2), then filters:

  --side     FE  = db.conf rows (BOX FE runs from db.conf through the branch wrapper)
             ACC = shell.conf rows running mbjbox.sh (BOX ACC runs through MBJ)    [stated: BOX dev, 2026-10-01]
             ALL = every executed BOX row (default)
  --product  a family name (depos, commodities, irs, ccs, cfm, fra, otc, cap, generic) - matched on the job
             name's GMBX<n> OR, for db.conf rows, the instrument constant (so old-named jobs are found too)
  --branch   a known branch (Madrid, SLB) - matched on the name token OR, for db.conf rows, the branch
             constant. Any other branch: --token XX and/or --branch-const CST_PK_...
  --controlm Control-M folder repos (directories of .json). Adds each job's folder, file:line, the events it
             waits for and emits, and its ORDER: a job comes after every selected job whose -OK event it
             waits for (levels 1, 2, ...). Events emitted by jobs outside the selection are named too.

Writes nothing unless --out is given (then <out>.csv and <out>.md). Prints a markdown answer. Also says
what the filter cannot see: executed BOX rows whose product or branch is not in the line (old-named or
token-less shell.conf jobs - their MBJ row has them, J-R2). Standard library only. Nothing is inferred.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

INV = "jobs-inventory.csv"
# product -> (GMBX<n>, db.conf instrument constant)  [parser summary, Tier 1 PROD, 2026-10-01; 8 = CF, BOX dev]
PRODUCTS = {"generic": ("0", "CST_PK_VACIO"), "depos": ("1", "CST_PK_DEP"), "commodities": ("2", "CST_PK_CES"),
            "irs": ("3", "CST_PK_SWAP"), "ccs": ("4", "CST_PK_CCS"), "cfm": ("5", "CST_PK_CFM"),
            "fra": ("6", "CST_PK_FRA"), "otc": ("7", "CST_PK_OTC"), "cap": ("8", "CST_PK_CAP")}
ALIASES = {"deposits": "depos", "deposit": "depos", "mm": "depos", "money market": "depos", "swap": "irs",
           "swaps": "irs", "interest rate swap": "irs", "cross currency swap": "ccs", "forward rate agreement": "fra",
           "otc option": "otc", "cf": "cap", "cap & floor": "cap", "caps": "cap", "commodity": "commodities"}
# branch -> (job-name token, db.conf branch constant)  [jobs-inventory, Tier 1 PROD, 2026-10-01]
BRANCHES = {"madrid": ("ES", "CST_PK_BRANC_MAD"), "slb": ("LB", "CST_PK_BRANC_LND")}
B_ALIASES = {"mad": "madrid", "es": "madrid", "london": "slb", "lnd": "slb", "lb": "slb"}
OUT_COLS = ["order", "job", "side", "product", "branch", "book_no", "step", "group", "conf", "match",
            "controlm", "folder", "waits_for", "after_selected", "after_outside", "emits", "note"]


def side_of(r: dict) -> str:
    if r["file"] == "db.conf":
        return "FE"
    return "ACC" if r["entry"].lower().endswith("mbjbox.sh") else "other script"


def product_match(r: dict, prod: str | None) -> str:
    if not prod:
        return "-"
    n, const = PRODUCTS[prod]
    if r["instr_no"] == n:
        return "name"
    if r["file"] == "db.conf" and r["instrument"] == const:
        return "instrument arg"
    return ""


def branch_match(r: dict, token: str | None, const: str | None) -> str:
    if not (token or const):
        return "-"
    if token and r["token"] == token:
        return "token"
    if const and r["file"] == "db.conf" and r["branch"] == const:
        return "branch arg"
    return ""


def load_controlm(dirs: list[Path]) -> tuple[dict, list[str]]:
    """job name -> {file, line, folder, waits, adds, when}; plus warnings."""
    jobs, warn = {}, []

    def events(node) -> list[str]:
        out = []
        if isinstance(node, dict):
            if isinstance(node.get("Event"), str):
                out.append(node["Event"])
            for v in node.values():
                out += events(v)
        elif isinstance(node, list):
            for v in node:
                out += events(v)
        return out

    def walk(node, folder: str, path: Path, text: str):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, dict) and isinstance(v.get("Type"), str):
                    t = v["Type"]
                    if t.startswith("Job"):
                        m = re.search(r'"' + re.escape(k) + r'"\s*:', text)
                        line = text.count("\n", 0, m.start()) + 1 if m else 0
                        if k in jobs:
                            warn.append(f"{k} defined twice: {jobs[k]['file']}:{jobs[k]['line']} and {path.name}:{line}")
                        jobs[k] = {"file": path.name, "line": line, "folder": folder,
                                   "waits": events(v.get("eventsToWaitFor", {})),
                                   "adds": events(v.get("eventsToAdd", {})),
                                   "when": json.dumps(v.get("When", ""), ensure_ascii=True)[:80]}
                        continue
                    if "Folder" in t:
                        walk(v, k, path, text)
                        continue
                walk(v, folder, path, text)
        elif isinstance(node, list):
            for v in node:
                walk(v, folder, path, text)

    for d in dirs:
        files = sorted(d.rglob("*.json")) if d.is_dir() else [d]
        for p in files:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                walk(json.loads(text), "", p, text)
            except (json.JSONDecodeError, OSError) as e:
                warn.append(f"skipped {p}: {e.__class__.__name__}")
    return jobs, warn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("env_folder")
    ap.add_argument("--side", default="ALL", choices=["FE", "ACC", "ALL", "fe", "acc", "all"])
    ap.add_argument("--product")
    ap.add_argument("--branch")
    ap.add_argument("--token")
    ap.add_argument("--branch-const")
    ap.add_argument("--controlm", nargs="*", default=[])
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    inv = Path(a.env_folder) / INV
    if not inv.exists():
        print(f"no {INV} in {a.env_folder} - run scripts/parse_job_confs.py first", file=sys.stderr)
        return 1
    prod = a.product.lower() if a.product else None
    prod = ALIASES.get(prod, prod)
    if prod and prod not in PRODUCTS:
        print(f"unknown product '{a.product}' - one of {', '.join(PRODUCTS)}", file=sys.stderr)
        return 2
    token, const = (a.token.upper() if a.token else None), a.branch_const
    if a.branch:
        b = B_ALIASES.get(a.branch.lower(), a.branch.lower())
        if b not in BRANCHES:
            print(f"unknown branch '{a.branch}' - use --token / --branch-const", file=sys.stderr)
            return 2
        token, const = token or BRANCHES[b][0], const or BRANCHES[b][1]
    side = a.side.upper()

    rows = list(csv.DictReader(inv.open(encoding="utf-8")))
    if "executed" not in rows[0]:
        print(f"{INV} has no 'executed' column - re-run scripts/parse_job_confs.py (2026-10-01 version)", file=sys.stderr)
        return 1
    live = [r for r in rows if r["family"] == "BOX" and r["active"] == "Y" and r["executed"] == "Y"]
    sel, blind = [], 0
    for r in live:
        s = side_of(r)
        if side != "ALL" and s != side:
            continue
        pm, bm = product_match(r, prod), branch_match(r, token, const)
        if pm and bm:
            sel.append((r, s, pm, bm))
        elif (prod and not r["instr_no"] and not (r["file"] == "db.conf" and r["instrument"])) or \
             ((token or const) and not r["token"] and not (r["file"] == "db.conf" and r["branch"])):
            blind += 1

    cm, warn = load_controlm([Path(d) for d in a.controlm]) if a.controlm else ({}, [])
    producer = defaultdict(set)
    for j, v in cm.items():
        for e in v["adds"]:
            producer[e].add(j)
    names = {r["job"] for r, *_ in sel}
    after = {n: set() for n in names}
    out = []
    for r, s, pm, bm in sel:
        c = cm.get(r["job"])
        known = r["scope"] if r["scope"].startswith(("product", "generic", "branch")) else ""
        rec = {"job": r["job"], "side": s, "product": known or r["instrument"] or r["scope"], "branch": r["token"] or r["branch"],
               "book_no": r["book_no"], "step": r["step"], "group": r["group"], "conf": f"{r['file']}:{r['line']}",
               "match": f"product {pm} / branch {bm}", "note": ""}
        if c:
            ins = {p for e in c["waits"] for p in producer.get(e, ())} - {r["job"]}
            after[r["job"]] = ins & names
            rec.update(controlm=f"{c['file']}:{c['line']}", folder=c["folder"], waits_for=" ".join(c["waits"]),
                       after_selected=" ".join(sorted(ins & names)), after_outside=" ".join(sorted(ins - names)),
                       emits=" ".join(c["adds"]))
            unmatched = [e for e in c["waits"] if e not in producer]
            if unmatched:
                rec["note"] = "waits for events no job here emits: " + " ".join(unmatched)
        elif a.controlm:
            rec["note"] = "not found in the Control-M repos given"
        out.append(rec)

    level, todo = {}, set(names)
    while todo:                                     # longest-path levels over the selected jobs
        ready = {n for n in todo if all(p in level for p in after[n])}
        if not ready:
            break
        for n in ready:
            level[n] = 1 + max((level[p] for p in after[n]), default=0)
        todo -= ready
    for rec in out:
        n = rec["job"]
        rec["order"] = str(level[n]) if (a.controlm and n in level and n in cm) else ("cycle" if n in todo else "-")
    out.sort(key=lambda x: (int(x["order"]) if x["order"].isdigit() else 10**6, x["job"]))

    title = f"BOX jobs - side {side}" + (f", product {prod}" if prod else "") + \
        (f", branch {a.branch or ''} (token {token}, {const})" if (token or const) else "")
    md = [f"# {title}", "", f"Source: `{inv}`" + (f" + Control-M: {', '.join(a.controlm)}" if a.controlm else ""), "",
          f"**{len(out)} executed jobs.** Not visible to this filter: **{blind}** executed BOX jobs whose "
          f"{'product' if prod else ''}{' / ' if prod and (token or const) else ''}{'branch' if (token or const) else ''} "
          f"is not in their conf line (old-named or token-less `shell.conf` jobs - their MBJ row has it, J-R2).", ""]
    if a.controlm:
        found = sum(1 for x in out if x.get("controlm"))
        md += [f"Control-M: {found} of {len(out)} found; **order** = level in the dependency chain (1 runs first; a "
               "job runs after every listed job whose -OK event it waits for). `after_outside` = prerequisites "
               "outside this list.", ""]
    cols = ["order", "job", "side", "product", "branch", "book_no", "step", "group", "conf"] + \
        (["folder", "after_selected", "after_outside", "note"] if a.controlm else [])
    md += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    md += ["| " + " | ".join(x.get(c, "") for c in cols) + " |" for x in out]
    if warn:
        md += ["", "Warnings: " + "; ".join(warn[:10])]
    text = "\n".join(md) + "\n"
    print(text)
    if a.out:
        with open(a.out + ".csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=OUT_COLS, extrasaction="ignore")
            w.writeheader()
            w.writerows(out)
        Path(a.out + ".md").write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
