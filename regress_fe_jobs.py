#!/usr/bin/env python3
"""regress_fe_jobs.py - rebuild a finished box-fe-jobs-agent run and compare with its out/ (regression check).

    python3 scripts/regress_fe_jobs.py <run folder>/ [--as-of YYYYMMDD] [--map OLD=NEW ...] [--keep]

Use it after any change to the agent's scripts, inputs format or prompts, on the branch's last finished (frozen) run:
the same answers must give the same files. Nothing in the run folder is written: the run is copied to a temporary
folder (without out/, .frozen, pending-questions.md), its relative input paths are made absolute against the run's
own location, and scripts/build_fe_jobs.py is run there. Then every file of the run's out/ is compared with the
rebuild's.

- **Deliverables** (every file of out/ except report.md and pr/): any difference fails (exit 1) and is shown.
- **report.md** and **pending-questions.md**: compared for information only (they carry paths and wording).
- `--as-of`: the date the run was built (an ended job is one whose EndDate is before it). Default: the run folder's
  `_<YYYYMMDD>_<n>` suffix; none -> today, with a warning (a job ended since then would show as a difference).
- `--map OLD=NEW`: a path prefix in the inputs that points to another session's clone (e.g. Devin's repo paths),
  replaced before the rebuild. A path that still does not exist makes the rebuild refuse: the message names it.
- `--keep`: keep the temporary rebuild and print its path.

Exit: 0 identical deliverables, 1 differences, 2 usage / the rebuild refused (its REFUSED lines are printed).
[operator, 2026-10-20 - the regression check of box-fe-jobs-agent]
"""
from __future__ import annotations

import datetime
import difflib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_fe_jobs as bfj  # noqa: E402

INFO_ONLY = {"report.md", "pending-questions.md"}
SKIP_DIRS = {"pr"}
PATHLIKE = re.compile(r"\.(csv|json|conf|txt|md|ksh|sh)$")


def as_of_from(folder: Path) -> str | None:
    m = re.search(r"_(\d{8})_\d+$", folder.resolve().name)
    return m.group(1) if m else None


def fix_today(yyyymmdd: str) -> None:
    """build_fe_jobs reads datetime.date.today() to tell ended jobs: pin it to the run's date."""
    d = datetime.date(int(yyyymmdd[:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:]))

    class _Date(datetime.date):
        @classmethod
        def today(cls):
            return d

    class _Mod:
        date = _Date

    bfj.datetime = _Mod


def rewrite_paths(node, base: Path, maps: list[tuple[str, str]]):
    """Every string that is a path: --map prefixes replaced, then made absolute against the run's location."""
    if isinstance(node, dict):
        return {k: rewrite_paths(v, base, maps) for k, v in node.items()}
    if isinstance(node, list):
        return [rewrite_paths(v, base, maps) for v in node]
    if not isinstance(node, str) or node.strip().startswith("<"):
        return node
    s = node
    for old, new in maps:
        if s.startswith(old):
            s = new + s[len(old):]
    if ("/" in s or PATHLIKE.search(s)) and not Path(s).is_absolute() and "\n" not in s and len(s) < 400:
        r = bfj.resolve(base, s)
        if r.exists():
            return str(r.resolve())
    return s


def files_of(od: Path) -> dict[str, Path]:
    out = {}
    for f in sorted(od.rglob("*")):
        rel = f.relative_to(od)
        if f.is_file() and not (rel.parts and rel.parts[0] in SKIP_DIRS):
            out[rel.as_posix()] = f
    return out


def same(a: Path, b: Path) -> bool:
    ta, tb = a.read_bytes(), b.read_bytes()
    if ta == tb:
        return True
    if a.suffix == ".json":
        try:
            return json.loads(ta) == json.loads(tb)
        except ValueError:
            return False
    return False


def show_diff(a: Path, b: Path, name: str, limit: int = 20) -> list[str]:
    try:
        la, lb = a.read_text(encoding="utf-8").splitlines(), b.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return [f"    (binary file {name} differs)"]
    d = list(difflib.unified_diff(la, lb, f"run/{name}", f"rebuild/{name}", lineterm="", n=1))
    return ["    " + x for x in d[:limit]] + ([f"    ... {len(d) - limit} more diff lines"] if len(d) > limit else [])


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    keep = "--keep" in argv
    argv = [a for a in argv if a != "--keep"]
    as_of, maps, pos = None, [], []
    i = 0
    while i < len(argv):
        if argv[i] == "--as-of" and i + 1 < len(argv):
            as_of, i = argv[i + 1], i + 2
        elif argv[i] == "--map" and i + 1 < len(argv) and "=" in argv[i + 1]:
            maps.append(tuple(argv[i + 1].split("=", 1)))
            i += 2
        else:
            pos.append(argv[i])
            i += 1
    if len(pos) != 1 or not Path(pos[0]).is_dir():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    run = Path(pos[0]).resolve()
    if not (run / bfj.INPUTS).exists() or not (run / bfj.OUT).is_dir():
        print(f"{run}: needs {bfj.INPUTS} and out/ (a run that was built)", file=sys.stderr)
        return 2
    if as_of and not re.fullmatch(r"\d{8}", as_of):
        print("--as-of YYYYMMDD", file=sys.stderr)
        return 2
    warn = []
    as_of = as_of or as_of_from(run)
    if not as_of:
        as_of = datetime.date.today().strftime("%Y%m%d")
        warn.append(f"no date in the run folder name: built as of today ({as_of}) - pass --as-of the run's date")
    fix_today(as_of)

    tmp_root = Path(tempfile.mkdtemp(prefix="regress-fe-jobs-"))
    tmp = tmp_root / run.parent.name / run.name
    shutil.copytree(run, tmp, ignore=shutil.ignore_patterns(bfj.OUT, ".frozen", "pending-questions.md"))
    plan = run.parent / "instrument-plan.csv"                  # the default jobs plan sits beside the run folders
    if plan.exists():
        shutil.copy2(plan, tmp.parent / plan.name)
    cfg = json.loads((run / bfj.INPUTS).read_text(encoding="utf-8-sig"))
    (tmp / bfj.INPUTS).write_text(json.dumps(rewrite_paths(cfg, run, maps), indent=2), encoding="utf-8")

    res = bfj.Result()
    rc = bfj.build(tmp, res)
    print(f"\nregress_fe_jobs - {run}\n" + "=" * 72 + f"\n  rebuilt as of {as_of}: exit {rc}")
    for w in warn:
        print(f"  WARN    {w}")
    if rc not in (0, 4):
        for c, w, m in res.errors:
            print(f"  REFUSED {c:<28} {w}: {m}")
        print("  the rebuild refused - an input path from another session? use --map OLD=NEW\n" + "=" * 72)
        _cleanup(tmp_root, keep)
        return 2

    old, new = files_of(run / bfj.OUT), files_of(tmp / bfj.OUT)
    pq = "pending-questions.md"                                # beside out/, in the run folder
    if (run / pq).exists():
        old[f"../{pq}"] = run / pq
    if (tmp / pq).exists():
        new[f"../{pq}"] = tmp / pq
    bad, info, ok = [], [], 0
    for name in sorted(set(old) | set(new)):
        tag = Path(name).name in INFO_ONLY
        if name not in new:
            (info if tag else bad).append((name, ["    only in the run's out/ - the rebuild did not write it"]))
        elif name not in old:
            (info if tag else bad).append((name, ["    only in the rebuild - the run's out/ does not have it"]))
        elif same(old[name], new[name]):
            ok += 1
        else:
            (info if tag else bad).append((name, show_diff(old[name], new[name], name)))
    print(f"  {ok} file(s) identical")
    for name, lines in bad:
        print(f"  DIFFERS {name}")
        print("\n".join(lines))
    for name, lines in info:
        print(f"  info    {name} differs (not a deliverable)")
    print(("  REGRESSION: the same answers give different files - check the change, or explain each difference"
           if bad else "  no regression: every deliverable is identical") + "\n" + "=" * 72)
    _cleanup(tmp_root, keep)
    return 1 if bad else 0


def _cleanup(tmp_root: Path, keep: bool) -> None:
    if keep:
        print(f"  rebuild kept in {tmp_root}")
    else:
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
