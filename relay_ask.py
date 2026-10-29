#!/usr/bin/env python3
"""
relay_ask.py - the agent's side of the DB relay: send a batch of read-only queries, wait for the CSVs
[operator, 2026-10-28 - ADR 0021, PROPOSED: used only when the run's DB access mode is "relay" (skill run-db-queries)].

    python3 scripts/relay_ask.py <run folder> --env tier2-dev \
        BOX_ACC:A-01-TGT=/tmp/a01.sql  GBO:A-04d-GBO=/tmp/a04d.sql  [--timeout 900] [--poll 10]

Each query: `SYSTEM:NAME=FILE` - SYSTEM picks the account on the operator's side (docs/reference/db-routes.csv:
GBO, DEVENG, BOX_ACC, BOX_FE, BOX_SYS, BOX_STC), NAME is the evidence file (`<run>/01-evidence/NAME.csv`, the
catalogue's name), FILE holds ONE statement with every value filled in. Send every query of a step that does not
need another's result in one call: one push, one answer.

1. Checks every query with the relay's own guard (scripts/db_relay.check_sql) and the route (environment allowed,
   system known) - a refusal stops the batch before anything is pushed (exit 2): fix the query, or hand it to the
   operator (manual mode).
2. Writes `<run>/relay/<NNN>-<NAME>.sql` (header + statement), commits, pushes the current branch.
3. Pulls every --poll seconds until each request has its `.log.json` (the relay on the operator's PC answered), then
   prints, per query: status, rows, truncated, the CSV path - and the problems / database error when not ok.

Exit: 0 every query ok · 1 one refused or failed on the operator's side (see its log) · 2 refused before sending /
bad invocation · 3 no answer within --timeout (the relay is not running: say so to the operator and go on in manual
mode - the requests stay pushed; the relay answers them when it starts).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_relay as dr

SPEC = re.compile(r"^([A-Za-z_]+):([A-Za-z0-9][\w.-]*)=(.+)$")


def git(*args, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def prepare(run: Path, env: str, specs: list[str], routes: list[dict]):
    """[(system, name, sql)] or the list of problems - nothing written when there is one."""
    items, res = [], dr.Result()
    if not run.is_dir():
        res.err("run-missing", str(run), "run folder not found")
        return None, res.errors
    for sp in specs:
        m = SPEC.match(sp)
        if not m:
            res.err("spec-bad", repr(sp), "expected SYSTEM:NAME=FILE")
            continue
        system, name, f = m.groups()
        fp = Path(f)
        if not fp.is_file():
            res.err("file-missing", name, f"file {f} not found")
            continue
        sql = fp.read_text(encoding="utf-8").strip().rstrip(";").strip()
        route = dr.route_for(routes, env, system)
        if not route:
            res.err("route-unknown", name, f"no route for env {env} system {system} (db-routes.csv)")
        elif (route.get("relay_allowed") or "").lower() != "yes":
            res.err("env-not-allowed", name, f"env {env} not allowed for the relay")
        res.errors += [f"{name}: {p}" for p in dr.check_sql(sql)]
        if (run / "01-evidence" / f"{name}.csv").exists():
            res.err("evidence-exists", name, f"01-evidence/{name}.csv exists already - a new name, or delete it first")
        items.append((system.upper(), name, sql))
    names = [n for _, n, _ in items]
    for n in sorted({n for n in names if names.count(n) > 1}):
        res.err("name-twice", n, "twice in the batch")
    return (None, res.errors) if res.errors else (items, [])


def write_requests(run: Path, env: str, items) -> list[Path]:
    rel = run / "relay"
    rel.mkdir(exist_ok=True)
    (run / "01-evidence").mkdir(exist_ok=True)
    nums = [int(m.group(1)) for p in rel.glob("*.sql") if (m := re.match(r"(\d+)-", p.name))]
    n = max(nums, default=0)
    reqs = []
    for system, name, sql in items:
        n += 1
        req = rel / f"{n:03d}-{name}.sql"
        req.write_text(f"-- relay: env={env} system={system} out=01-evidence/{name}.csv\n{sql}\n", encoding="utf-8")
        reqs.append(req)
    return reqs


def summary(run: Path, reqs: list[Path]) -> int:
    rc = 0
    for req in reqs:
        lg = json.loads(req.with_suffix(".log.json").read_text(encoding="utf-8"))
        if lg["status"] == "ok":
            trunc = " TRUNCATED at the row cap" if lg.get("truncated") else ""
            print(f"ok       {req.stem}: {lg.get('rows', 0)} rows{trunc} -> {run / lg['out']}"
                  + (f" ({lg['note']})" if lg.get("note") else ""))
        else:
            rc = 1
            why = "; ".join(lg.get("problems", [])) or lg.get("error", "")
            print(f"{lg['status']:8} {req.stem}: {why}")
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("run", help="the run folder (its relay/ and 01-evidence/ are used)")
    ap.add_argument("queries", nargs="+", help="SYSTEM:NAME=FILE, one per query")
    ap.add_argument("--env", required=True, help="e.g. tier2-dev")
    ap.add_argument("--timeout", type=int, default=900, help="seconds to wait for the answers (default 900)")
    ap.add_argument("--poll", type=int, default=10, help="seconds between two pulls (default 10)")
    ap.add_argument("--no-wait", action="store_true", help="push and return (exit 0)")
    ap.add_argument("--routes", default=str(dr.ROUTES))
    a = ap.parse_args(argv)
    run = Path(a.run).resolve()
    items, probs = prepare(run, a.env, a.queries, dr.load_routes(Path(a.routes)))
    if probs:
        print("REFUSED before sending (nothing pushed):\n  " + "\n  ".join(probs), file=sys.stderr)
        return 2
    top = Path(git("rev-parse", "--show-toplevel", cwd=run).stdout.strip())
    branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=top).stdout.strip()
    if not top.is_dir() or branch in ("", "HEAD"):
        print("REFUSED: not on a git branch", file=sys.stderr)
        return 2
    reqs = write_requests(run, a.env, items)
    git("add", *[str(r) for r in reqs], str(run / "01-evidence"), cwd=top)
    git("commit", "-m", f"relay request: {len(reqs)} query(ies) - {', '.join(r.stem for r in reqs[:5])}", cwd=top)
    push = git("push", "origin", f"HEAD:{branch}", cwd=top)
    if push.returncode:
        print(f"REFUSED: push of {branch} failed: {push.stderr.strip()[:300]}", file=sys.stderr)
        return 2
    print(f"sent {len(reqs)} query(ies) on branch {branch} - waiting for the relay (up to {a.timeout} s)")
    if a.no_wait:
        return 0
    t0 = time.time()
    while time.time() - t0 < a.timeout:
        git("pull", "--rebase", "--autostash", "origin", branch, cwd=top)
        if all(r.with_suffix(".log.json").exists() for r in reqs):
            return summary(run, reqs)
        time.sleep(a.poll)
    left = [r.stem for r in reqs if not r.with_suffix(".log.json").exists()]
    print(f"NO ANSWER within {a.timeout} s for {', '.join(left)} - the relay is not running on the operator's PC. "
          "Tell the operator; go on in manual mode (the requests stay pushed and are answered when the relay starts).")
    return 3


if __name__ == "__main__":
    sys.exit(main())
