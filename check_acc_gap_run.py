#!/usr/bin/env python3
"""
check_acc_gap_run.py - sigom-box-acc-configs-agent phase 1: is a gap run FINISHED? [operator, 2026-11-13]

    python3 scripts/check_acc_gap_run.py runs/<BRANCH>/<tier>-<env>/acc-configs/gap_<date>_<n>/

The agent runs it before it says a gap run is done, and fixes every FAIL first. NY's first PRE-PARALELO gap run
(gap_20261112_1) called itself complete with half the template, CSVs never saved and the scope wrong - nothing
checked it. This does, mechanically (the content is still the agent's and the reviewers'):

  files      02-acc-gap-matrix.md, 03-portfolio-properties-report.md, 04-net-ccs-handover.md (ADR 0025),
             01-evidence/ with CSVs, the branch's condition map (runs/<BRANCH>/branch/acc-configs/condition-map.csv)
  sections   every "## " section of the matrix and report templates is there (by its first words)
  filled     no template placeholder ({{...}}) left
  evidence   every CSV file the matrix / report / handover names is in 01-evidence/ (or in a REF provenance note)
  scope      the matrix's "counted once" line adds up: in scope = Valid + InValid + OPEN
  globals    outside DEV, global .65 objects to create name the global installation (DGBOBOX - ADR 0027)

Exit: 0 every check passed · 1 a FAIL · 2 bad invocation. Standard library only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "agents/sigom-box-acc-configs-agent/templates"
FILES = {"matrix": "02-acc-gap-matrix.md", "report": "03-portfolio-properties-report.md",
         "handover": "04-net-ccs-handover.md"}
TEMPLATES = {"matrix": TPL / "acc-gap-matrix.md.tmpl", "report": TPL / "portfolio-properties-report.md.tmpl",
             "handover": TPL / "net-ccs-handover.md.tmpl"}
CSV = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9_.\-]*\.csv)\b")
SCOPE = re.compile(r"(\d+)\s*=\s*(\d+)\s*created\s*`?Valid`?.*?\+\s*(\d+)\s*created\s*`?InValid`?.*?\+\s*(\d+)\s*OPEN",
                   re.S)


def words(heading: str, n: int = 4) -> str:
    h = re.sub(r"\{\{.*?\}\}", "", heading)
    h = re.sub(r"[`*_—–:()\[\],.]", " ", h.lower())
    return " ".join(h.split()[:n])


def headings(text: str) -> list[str]:
    return [ln[3:].strip() for ln in text.splitlines() if ln.startswith("## ")]


def check(run: Path) -> list[tuple[str, str]]:
    fails: list[tuple[str, str]] = []
    texts = {}
    for k, name in FILES.items():
        f = run / name
        if not f.exists():
            fails.append(("file-missing", f"{name} (from its template; the Net CCS handover: ADR 0025)"))
        else:
            texts[k] = f.read_text(encoding="utf-8", errors="replace")
    ev = run / "01-evidence"
    have = {p.name for p in ev.rglob("*.csv")} if ev.is_dir() else set()
    if not have:
        fails.append(("evidence-missing", "01-evidence/ has no CSV - every query result is saved there as it arrives"))
    branch = next((p.name for p in run.parents if p.parent.name == "runs"), None)
    if branch and not (ROOT / "runs" / branch / "branch/acc-configs/condition-map.csv").exists():
        fails.append(("condition-map-missing", f"runs/{branch}/branch/acc-configs/condition-map.csv"))
    for k, tpl in TEMPLATES.items():
        if k not in texts or not tpl.exists():
            continue
        got = [words(h, 12) for h in headings(texts[k])]
        for h in headings(tpl.read_text(encoding="utf-8")):
            key = words(h.split("{{")[0])     # the words before any placeholder
            if not any(g == key or g.startswith(key + " ") for g in got):
                fails.append(("section-missing", f"{FILES[k]}: '## {h}' (template {tpl.name})"))
    for k, t in texts.items():
        if "{{" in t:
            fails.append(("placeholder-left", f"{FILES[k]}: {t[t.index('{{'):t.index('{{') + 40]!r}"))
    prov = " ".join(p.read_text(encoding="utf-8", errors="replace") for p in run.glob("*provenance*.md"))
    prov += " ".join(p.read_text(encoding="utf-8", errors="replace") for p in ev.glob("*provenance*.md")) \
        if ev.is_dir() else ""
    named = sorted({c for t in texts.values() for c in CSV.findall(t)})
    # the branch's own files (condition map, label aliases...) live in runs/<BRANCH>/branch/, not in the run
    branch_files = {p.name for p in (ROOT / "runs" / branch / "branch").rglob("*.csv")} if branch else set()
    for c in named:
        if c not in have and c not in prov and c not in branch_files and "*" not in c:
            fails.append(("evidence-not-saved", f"{c} is named in the run's files but not in 01-evidence/"))
    if "matrix" in texts:
        m = SCOPE.search(texts["matrix"])
        if not m:
            fails.append(("scope-line", f"{FILES['matrix']}: the 'counted once' line (N = a created `Valid` + b created "
                          "`InValid` + c OPEN) not found"))
        elif int(m[1]) != int(m[2]) + int(m[3]) + int(m[4]):
            fails.append(("scope-sum", f"{FILES['matrix']}: {m[1]} in scope but {m[2]} Valid + {m[3]} InValid + "
                          f"{m[4]} OPEN = {int(m[2]) + int(m[3]) + int(m[4])}"))
        env = run.parent.parent.name.lower()
        if "-dev" not in env and ".65" in texts["matrix"] and "dgbobox" not in texts["matrix"].lower():
            fails.append(("globals-not-dgbobox", f"{FILES['matrix']}: outside DEV the global .65 objects are created "
                          "in the global installation (DGBOBOX) and imported - say so (ADR 0027)"))
    return fails


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or not Path(argv[0]).is_dir():
        print(__doc__.split("\n")[3].strip(), file=sys.stderr)
        return 2
    run = Path(argv[0]).resolve()
    fails = check(run)
    for code, what in fails:
        print(f"FAIL  {code:22} {what}")
    print(f"{len(fails)} FAIL" if fails else f"OK - {run.name}: every check passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
