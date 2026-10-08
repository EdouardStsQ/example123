#!/usr/bin/env python3
"""
unix_package.py - the Unix deployment package of an agent's job confs [2026-10-08, BOX job expert review 2026-10-09].

    python3 scripts/unix_package.py --db <db.conf.proposal> [--shell <shell.conf.proposal>] \
        --scripts /gmny/scripts [--templates /gmny/scripts/templates] --etc /gmny/etc \
        [--ref-unix runs/_reference/tier1-prod/unix] [--ref-etc /appl/gm/etc] --out <out>/unix

Writes, for the BOX / Unix team to drop into the target's etc folder (as the Tier 1 CDS package):

  job_unix.sh        sh -x <etc>/delete_jobsBX.ksh  db.conf <etc>/db_delete.txt     remove our jobs' lines first
                     sh -x <etc>/add_new_jobs.ksh db.conf <etc>/db_nuevo.conf       then add them
                     (the same two lines for shell.conf, when given)
                     cp <templates>/db_job <scripts>/<JOB>   (shell_job for shell.conf jobs)   one script per job
                     chmod 755 <scripts>/<JOB>
  db_nuevo.conf      the db.conf proposal, under the name add_new_jobs.ksh reads (shell_nuevo.conf the same)
  db_delete.txt      every job of db_nuevo.conf + its banner lines: delete_jobsBX.ksh removes each line containing
                     one (`sed '/<line>/D'`; jobs not there yet = nothing removed) -> the package can be run again
                     without duplicating lines
  delete_jobsBX.ksh  the target's copy of the reference script (--ref-unix): its `cd <reference etc>` points to the
  add_new_jobs.ksh   target's etc folder; author lines (`#by ...`, personal IDs) left out. A script not in --ref-unix
                     is reported missing (the BOX team provides it).

delete_jobsBX.ksh accepts in a list file job names GMBX + 8 characters / GMGB + 7, or lines containing `#` (banners);
a line with `/` or `[` would break its sed - such banners are not listed (reported). One package per agent:
box-fe-jobs-agent (db.conf) now, box-acc-jobs-agent (shell.conf) later. Without --etc the sh lines are OPEN
(commented). A proposal - never run by an agent. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT = "job_unix.sh"
JOB_LINE = re.compile(r"^\s*([A-Z][A-Z0-9_]{3,})\s*:")
DELETABLE = re.compile(r"^(GMBX.{8}|GMGB.{7})$")
SCRIPTS = ("delete_jobsBX.ksh", "add_new_jobs.ksh")


def job_names(path) -> list[str]:
    """The job names of a conf proposal, in file order, once each; comments (#...) skipped."""
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


def banners(path) -> list[str]:
    if not path or not Path(path).exists():
        return []
    return [x.strip() for x in Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
            if x.strip().startswith("#")]


def delete_list(conf, notes: list) -> list[str]:
    out = []
    for j in job_names(conf):
        if DELETABLE.match(j):
            out.append(j)
        else:
            notes.append(f"{j}: not GMBX + 8 / GMGB + 7 characters - delete_jobsBX.ksh would skip it")
    for b in banners(conf):
        if "/" in b or "[" in b:
            notes.append(f"banner not listed (its / or [ would break delete_jobsBX.ksh's sed): {b}")
        elif b not in out:
            out.append(b)
    return out


def target_script(src: Path, ref_etc: str, etc: str) -> str:
    """The reference script for the target: its etc folder replaced, author lines left out."""
    lines = []
    for ln in src.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").split("\n"):
        if re.match(r"^\s*#\s*by\b", ln, re.I):
            continue
        lines.append(ln.replace(ref_etc.rstrip("/"), etc.rstrip("/")))
    return "\n".join(lines)


def render(db_jobs, shell_jobs, scripts: str, templates: str, etc: str | None) -> str:
    scripts, templates = scripts.rstrip("/"), templates.rstrip("/")
    pre = "" if etc else "# OPEN - the etc folder is not given: "
    e = (etc or "<etc>").rstrip("/")
    ln = []
    if db_jobs:
        ln += [f"{pre}sh -x {e}/delete_jobsBX.ksh  db.conf {e}/db_delete.txt",
               f"{pre}sh -x {e}/add_new_jobs.ksh db.conf {e}/db_nuevo.conf", ""]
    if shell_jobs:
        ln += [f"{pre}sh -x {e}/delete_jobsBX.ksh  shell.conf {e}/shell_delete.txt",
               f"{pre}sh -x {e}/add_new_jobs.ksh shell.conf {e}/shell_nuevo.conf", ""]
    ln += [f"cp {templates}/db_job {scripts}/{j}" for j in db_jobs]
    if shell_jobs:
        ln += ["", "", ""] + [f"cp {templates}/shell_job {scripts}/{j}" for j in shell_jobs]
    ln += ["", "", ""] + [f"chmod 755 {scripts}/{j}" for j in [*db_jobs, *shell_jobs]]
    return "\n".join(ln) + "\n"


def write(out_dir, db_conf=None, shell_conf=None, scripts: str = "", templates: str | None = None,
          etc: str | None = None, ref_unix=None, ref_etc: str = "/appl/gm/etc") -> dict:
    """Writes the package; returns {path, db, shell, notes, missing}."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    db_jobs, shell_jobs, notes, missing = job_names(db_conf), job_names(shell_conf), [], []
    for kind, conf in (("db", db_conf), ("shell", shell_conf)):
        if conf and Path(conf).exists() and job_names(conf):
            (out_dir / f"{kind}_nuevo.conf").write_text(Path(conf).read_text(encoding="utf-8"), encoding="utf-8",
                                                       newline="\n")
            (out_dir / f"{kind}_delete.txt").write_text("\n".join(delete_list(conf, notes)) + "\n", encoding="utf-8",
                                                       newline="\n")
    for name in SCRIPTS:
        src = Path(ref_unix) / name if ref_unix else None
        if src and src.exists() and etc:
            (out_dir / name).write_text(target_script(src, ref_etc, etc), encoding="utf-8", newline="\n")
        else:
            missing.append(name)
    p = out_dir / SCRIPT
    p.write_text(render(db_jobs, shell_jobs, scripts, templates or scripts.rstrip("/") + "/templates", etc),
                 encoding="utf-8", newline="\n")
    return {"path": p, "db": len(db_jobs), "shell": len(shell_jobs), "notes": notes, "missing": missing}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--db", type=Path, help="db.conf proposal")
    ap.add_argument("--shell", type=Path, help="shell.conf proposal")
    ap.add_argument("--scripts", required=True, help="the job scripts folder, e.g. /gmny/scripts")
    ap.add_argument("--templates", help="the templates folder (default <scripts>/templates)")
    ap.add_argument("--etc", help="the target's etc folder (default: OPEN)")
    ap.add_argument("--ref-unix", type=Path, help="the reference's delete_jobsBX.ksh / add_new_jobs.ksh folder")
    ap.add_argument("--ref-etc", default="/appl/gm/etc", help="the reference's etc folder (in those scripts)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if not a.db and not a.shell:
        print("give --db and/or --shell", file=sys.stderr)
        return 2
    r = write(a.out, a.db, a.shell, a.scripts, a.templates, a.etc, a.ref_unix, a.ref_etc)
    print(f"wrote {r['path'].parent}: {r['db']} db.conf job(s), {r['shell']} shell.conf job(s)")
    for n in r["notes"]:
        print(f"  NOTE {n}")
    for m in r["missing"]:
        print(f"  MISSING {m} - not in --ref-unix (or no --etc): the BOX team provides the target's copy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
