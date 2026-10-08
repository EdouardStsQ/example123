#!/usr/bin/env python3
"""
stage_target_pr.py - stage the target branch's Control-M folder JSONs for a PR on its own repos [2026-10-09].

    python3 scripts/stage_target_pr.py runs/<BRANCH>/<env>/fe-jobs/<run>/ [--checkout <repo>=<path to its clone> ...]

The only write the agents may do outside this automation repo [operator, 2026-10-09]: the target branch's own new
Control-M repos (registry columns fe_controlm_repo, prereq_controlm_repos, acc_controlm_repo - NY: cib-boxfin-t2usnyfe,
cib-boxfin-t2nyloadprices, cib-boxacc-t2usnyac), one file each, `projects/<repo>.json`, by a PR from a new branch -
never a push to the default branch, never a merge, and only after the operator said yes to the summary below.

Reads <run>/fe-jobs-inputs.json (`controlm.target_repo`, `prerequisites[].target_repo`) and <run>/out/<FOLDER>.json.
Writes <run>/out/pr/<repo>/projects/<repo>.json (the same content: only the file name changes - it is the repo's name,
the Control-M folder inside keeps its own) and <run>/out/pr/pr-summary.md: per repo the file, the folder, the job
count and, with --checkout, new file / jobs added, removed, changed against the repo's current file. The run's out/
files are not touched. The agent shows pr-summary.md and asks, once per repo, before any git command.
Exit 0 staged · 1 refused · 2 bad invocation. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def jobs_of(path: Path) -> tuple[str, dict]:
    root = json.loads(path.read_text(encoding="utf-8"))
    name, folder = next(((k, v) for k, v in root.items() if isinstance(v, dict)), (None, {}))
    return name, {k: v for k, v in folder.items() if isinstance(v, dict) and str(v.get("Type", "")).startswith("Job")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("run")
    ap.add_argument("--checkout", nargs="*", default=[], help="<repo>=<path to its clone>: compare with its file")
    a = ap.parse_args(argv)
    run = Path(a.run)
    ip = run / "fe-jobs-inputs.json"
    if not ip.exists():
        print(f"REFUSED inputs-missing: {ip}", file=sys.stderr)
        return 2
    cfg = json.loads(ip.read_text(encoding="utf-8-sig"))
    pairs = [(cfg["controlm"].get("folder_name"), cfg["controlm"].get("target_repo"))]
    pairs += [(p.get("folder_name"), p.get("target_repo")) for p in (cfg.get("prerequisites") or []) if isinstance(p, dict)]
    clones = dict(x.split("=", 1) for x in a.checkout if "=" in x)
    errors, out = [], ["# PR summary - for the operator's yes / no (one per repo)", ""]
    pr = run / "out" / "pr"
    for folder, repo in pairs:
        if not folder or not repo or str(repo).startswith("<"):
            errors.append(f"target-repo-missing: {folder}: give `target_repo` (registry: fe_controlm_repo / "
                          "prereq_controlm_repos)")
            continue
        src = run / "out" / f"{folder}.json"
        if not src.exists():
            errors.append(f"folder-json-missing: {src} - run build_fe_jobs.py first")
            continue
        name, jobs = jobs_of(src)
        if name != folder:
            errors.append(f"folder-name-mismatch: {src} holds {name!r}, not {folder!r}")
            continue
        dst = pr / repo / "projects" / f"{repo}.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        line = f"- **`{repo}`**: `projects/{repo}.json` <- `out/{folder}.json` - folder `{folder}`, {len(jobs)} jobs"
        cur = Path(clones[repo]) / "projects" / f"{repo}.json" if repo in clones else None
        if cur and cur.exists():
            _, old = jobs_of(cur)
            add, rem = sorted(set(jobs) - set(old)), sorted(set(old) - set(jobs))
            chg = sorted(j for j in set(jobs) & set(old) if jobs[j] != old[j])
            line += (f"; vs the repo's file: {len(add)} added, {len(rem)} removed, {len(chg)} changed"
                     + (f" (removed: {', '.join(rem[:10])})" if rem else ""))
        elif cur:
            line += "; **new file** in the repo"
        else:
            line += "; not compared (no --checkout for this repo)"
        out.append(line)
    out += ["", "Question to the operator, per repo: *open a PR on `<repo>` from a new branch `box-fe-jobs/<BRANCH>-<date>` "
            "adding / replacing `projects/<repo>.json` (above)? yes / no*. No -> nothing is pushed. Never merged by the "
            "agent."]
    for e in errors:
        print(f"REFUSED {e}", file=sys.stderr)
    if errors:
        return 1
    (pr / "pr-summary.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
