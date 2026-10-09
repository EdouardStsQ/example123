#!/usr/bin/env python3
"""
new_run.py - a new, versioned run folder for any agent; never write over an earlier run [operator, 2026-10-09].

    python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env pre --area fe-jobs --name depos
        -> runs/NY_SCH/tier2-pre/fe-jobs/depos_<YYYYMMDD>_<n>/   (n = the next free number that day)
    python3 scripts/new_run.py --freeze runs/NY_SCH/tier2-pre/fe-jobs/depos_20261009_1     (a finished run)
    python3 scripts/new_run.py --list runs/NY_SCH/tier2-pre/fe-jobs

Layout: runs/<BRANCH>/<tier>-<env>/<area>/<name>_<YYYYMMDD>_<n>/. The environment folder is per environment (its
books register, its job confs reference, its Control-M values differ): a new one (e.g. tier2-dev) is created empty
and what it lacks is listed - never copied silently from another environment. Each run gets RUN.md (branch,
environment, area, name, date, from-run, status) and a line in <area>/RUNS.md. A frozen run (.frozen) is refused by
the scripts that write runs (build_fe_jobs.py, fe_tech_test.py): a new attempt is a new version. Carrying answers
over is explicit: --from <run folder> copies only its inputs file, as `<inputs>.from-<run>.json`, for the agent to
offer answer by answer. Standard library only. Exit 0 · 1 refused · 2 bad invocation.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "docs/reference/branch-registry.csv"
FROZEN = ".frozen"
INPUTS = {"fe-jobs": "fe-jobs-inputs.json", "tests/technical": "tech-test-inputs.json"}


def is_frozen(folder: Path) -> bool:
    return (Path(folder) / FROZEN).exists()


def env_gaps(envd: Path, tier: str, env: str, root: Path = ROOT) -> list[str]:
    gaps = []
    if not (envd / "books" / "books-register.csv").exists():
        gaps.append(f"{envd}/books/books-register.csv - the target's labels in this environment (skill set-up-book-labels)")
    ref = root / "runs" / "_reference" / f"{tier}-{env}"
    if not (ref / "db.conf").exists():
        gaps.append(f"{ref}/db.conf (+ shell.conf, jobs-inventory.csv) - this environment's job confs, if they differ")
    return gaps


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--branch")
    ap.add_argument("--tier")
    ap.add_argument("--env")
    ap.add_argument("--area", help="e.g. fe-jobs, tests/technical")
    ap.add_argument("--name", help="e.g. depos, all")
    ap.add_argument("--from", dest="src", help="an earlier run folder whose inputs file is offered (not applied)")
    ap.add_argument("--date", help="YYYYMMDD (default today)")
    ap.add_argument("--freeze", help="mark a finished run folder frozen")
    ap.add_argument("--list", help="an area folder: its RUNS.md")
    ap.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    root = Path(a.root)
    if a.freeze:
        f = Path(a.freeze)
        if not f.is_dir():
            print(f"REFUSED run-missing: {f}", file=sys.stderr)
            return 1
        (f / FROZEN).write_text(f"frozen {datetime.datetime.now().isoformat(timespec='minutes')}\n", encoding="utf-8")
        idx = f.parent / "RUNS.md"
        if idx.exists():
            txt = idx.read_text(encoding="utf-8")
            idx.write_text(re.sub(r"(\| `" + re.escape(f.name) + r"` \|[^\n]*\| )open( \|)", r"\1frozen\2", txt),
                           encoding="utf-8")
        print(f"frozen {f}")
        return 0
    if a.list:
        idx = Path(a.list) / "RUNS.md"
        print(idx.read_text(encoding="utf-8") if idx.exists() else f"no runs in {a.list}")
        return 0
    if not all([a.branch, a.tier, a.env, a.area, a.name]):
        print("give --branch --tier --env --area --name (or --freeze / --list)", file=sys.stderr)
        return 2
    if not re.fullmatch(r"tier\d", a.tier) or not re.fullmatch(r"[a-z0-9]+", a.env) \
            or not re.fullmatch(r"[a-z0-9-]+", a.name):
        print("REFUSED bad-name: tier like tier2, env and name lower-case letters / digits (name may use -)",
              file=sys.stderr)
        return 1
    if REGISTRY.exists():
        branches = {r["branch"] for r in csv.DictReader(REGISTRY.open(encoding="utf-8"))}
        if a.branch not in branches:
            print(f"REFUSED branch-unknown: {a.branch} is not in {REGISTRY.name} - add its row first", file=sys.stderr)
            return 1
    envd = root / "runs" / a.branch / f"{a.tier}-{a.env}"
    new_env = not envd.exists()
    day = a.date or datetime.date.today().strftime("%Y%m%d")
    area = envd / a.area
    area.mkdir(parents=True, exist_ok=True)
    n = 1
    while (area / f"{a.name}_{day}_{n}").exists():
        n += 1
    run = area / f"{a.name}_{day}_{n}"
    run.mkdir()
    src_note = "-"
    if a.src:
        sp = Path(a.src)
        inp = INPUTS.get(a.area, "")
        if inp and (sp / inp).exists():
            shutil.copyfile(sp / inp, run / f"{Path(inp).stem}.from-{sp.name}.json")
            src_note = f"`{sp}` (its inputs offered as `{Path(inp).stem}.from-{sp.name}.json` - answers confirmed one by one)"
        else:
            src_note = f"`{sp}` (no inputs file found there)"
    (run / "RUN.md").write_text(
        f"# Run `{run.name}`\n\n| | |\n|---|---|\n| Branch | {a.branch} |\n| Environment | {a.tier}-{a.env} |\n"
        f"| Area | {a.area} |\n| Name | {a.name} |\n| Created | {datetime.datetime.now().isoformat(timespec='minutes')} |\n"
        f"| From | {src_note} |\n| Status | open (frozen once finished: scripts/new_run.py --freeze) |\n", encoding="utf-8")
    idx = area / "RUNS.md"
    if not idx.exists():
        idx.write_text(f"# Runs - {a.branch} {a.tier}-{a.env} {a.area}\n\n| Run | Created | From | Status |\n"
                       "|---|---|---|---|\n", encoding="utf-8")
    with idx.open("a", encoding="utf-8") as f:
        f.write(f"| `{run.name}` | {day} | {src_note.split(' (')[0]} | open |\n")
    print(f"{run}")
    gaps = env_gaps(envd, a.tier, a.env, root) if a.area == "fe-jobs" or new_env else []
    if new_env:
        print(f"NEW ENVIRONMENT {envd} - created empty. Missing there:")
    elif gaps:
        print(f"Missing in {envd}:")
    for g in gaps:
        print(f"  - {g}")
    seed = envd / a.area / f"{Path(INPUTS.get(a.area, 'x.json')).stem}.{a.branch}.json"
    if seed.exists() and not a.src:
        print(f"Branch inputs for this area: {seed} - copy it to {run}/{INPUTS[a.area]} and confirm its <ask> values")
    return 0


if __name__ == "__main__":
    sys.exit(main())
