#!/usr/bin/env python3
"""
unix_package.py - the Unix deployment script of an agent's job confs (job_unix.sh) [2026-10-08].

    python3 scripts/unix_package.py --db <db.conf.proposal> [--shell <shell.conf.proposal>] \
        --scripts /gmny/scripts [--templates /gmny/scripts/templates] [--etc <etc folder>] --out <folder>

Modelled on the BOX team's Tier 1 CDS package [read: job_unix.sh via operator, 2026-10-08]:

  sh -x <etc>/add_new_jobs.ksh db.conf <etc>/db_nuevo.conf          the new db.conf lines (db_nuevo.conf = the agent's
                                                                    db.conf.proposal)
  sh -x <etc>/add_new_jobs.ksh shell.conf <etc>/shell_nuevo.conf    the same for shell.conf (only when given)
  cp <templates>/db_job    <scripts>/<JOB>                          one script per db.conf job
  cp <templates>/shell_job <scripts>/<JOB>                          one script per shell.conf job
  chmod 755 <scripts>/<JOB>                                         every job

A new branch deletes nothing (no delete_jobsBX.ksh step) [operator, 2026-10-08]. One package per agent:
box-fe-jobs-agent (db.conf) now, box-acc-jobs-agent (shell.conf + its db.conf lines) later. Without the etc
folder the two `sh` lines are written commented OPEN. A proposal for the BOX / Unix team - never run by an agent.
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

SCRIPT = "job_unix.sh"
JOB_LINE = re.compile(r"^\s*([A-Z][A-Z0-9_]{3,})\s*:")


def job_names(path: Path | None) -> list[str]:
    """The job names of a conf proposal, in file order, once each; comments (#...) and OPEN lines are skipped."""
    if not path or not Path(path).exists():
        return []
    out = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = JOB_LINE.match(line)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def render(db_jobs: list[str], shell_jobs: list[str], scripts: str, templates: str, etc: str | None,
           title: str) -> str:
    scripts, templates = scripts.rstrip("/"), templates.rstrip("/")
    ln = ["#!/bin/sh", f"# {SCRIPT} - {title} ({datetime.date.today().isoformat()})",
          "# Proposal for the BOX / Unix team (scripts/unix_package.py). Before running it, copy the agent's",
          "# db.conf.proposal to <etc>/db_nuevo.conf" + (" and its shell.conf proposal to <etc>/shell_nuevo.conf"
                                                         if shell_jobs else "") + ".", ""]
    pre = "" if etc else "# OPEN - the etc folder of this environment is not given: "
    e = (etc or "<etc>").rstrip("/")
    if db_jobs:
        ln.append(f"{pre}sh -x {e}/add_new_jobs.ksh db.conf {e}/db_nuevo.conf")
    if shell_jobs:
        ln.append(f"{pre}sh -x {e}/add_new_jobs.ksh shell.conf {e}/shell_nuevo.conf")
    ln.append("")
    ln += [f"cp {templates}/db_job {scripts}/{j}" for j in db_jobs]
    if shell_jobs:
        ln.append("")
        ln += [f"cp {templates}/shell_job {scripts}/{j}" for j in shell_jobs]
    ln.append("")
    ln += [f"chmod 755 {scripts}/{j}" for j in [*db_jobs, *shell_jobs]]
    return "\n".join(ln) + "\n"


def write(out_dir: Path, db_conf: Path | None, shell_conf: Path | None, scripts: str, templates: str | None = None,
          etc: str | None = None, title: str = "BOX jobs") -> tuple[Path, int, int]:
    db_jobs, shell_jobs = job_names(db_conf), job_names(shell_conf)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / SCRIPT
    p.write_text(render(db_jobs, shell_jobs, scripts, templates or scripts.rstrip("/") + "/templates", etc, title),
                 encoding="utf-8", newline="\n")
    return p, len(db_jobs), len(shell_jobs)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--db", type=Path, help="db.conf proposal")
    ap.add_argument("--shell", type=Path, help="shell.conf proposal")
    ap.add_argument("--scripts", required=True, help="the job scripts folder, e.g. /gmny/scripts")
    ap.add_argument("--templates", help="the templates folder (default <scripts>/templates)")
    ap.add_argument("--etc", help="the etc folder holding add_new_jobs.ksh (default: OPEN)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--title", default="BOX jobs")
    a = ap.parse_args(argv)
    if not a.db and not a.shell:
        print("give --db and/or --shell", file=sys.stderr)
        return 2
    p, nd, ns = write(a.out, a.db, a.shell, a.scripts, a.templates, a.etc, a.title)
    print(f"wrote {p}: {nd} db.conf job(s), {ns} shell.conf job(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
