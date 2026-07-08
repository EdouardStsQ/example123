#!/usr/bin/env python3
"""wiki_lint.py — deterministic structural + GOVERNANCE lint. Pure stdlib.

Enforces, as code, what our skills state in prose:
  - frontmatter completeness (the 6 required keys) + layer matches its zone
  - broken wikilinks, oversized pages, duplicate ids, orphans
  - TWO-SOURCE rule (keystone): a `confirmed` page must cite >=2 distinct source classes,
    at least one NON-transcript (root CLAUDE.md §6)
  - fidelity heuristic: a concept page that cites a source but has no table (a dropped field/code
    table is the over-compression failure mode)

Findings are PROPOSED fixes — nothing is auto-applied. Exit 1 if any ERR.
  python3 scripts/wiki_lint.py
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _wikilib as W

NON_TRANSCRIPT = {"calypso", "murex", "gbo", "accounting_user"}


def src_class(rid):
    r = (rid or "").lower()
    for k in ("calypso", "murex", "gbo", "accounting_user"):
        if k in r:
            return k
    if "core-source" in r or "transcript" in r or "brs-core" in r:
        return "transcript"
    return "unknown"


def main():
    pages = list(W.iter_pages())
    names = {p["name"] for p in pages} | {p["id"] for p in pages}
    id_counts = collections.Counter(p["id"] for p in pages)
    inbound = collections.Counter(l for p in pages for l in p["wikilinks"])
    findings = []

    def add(sev, rule, msg):
        findings.append((sev, rule, msg))

    for p in pages:
        fm, rel = p["fm"], p["relpath"]
        miss = [k for k in W.REQUIRED_FM if k not in fm]
        if miss:
            add("ERR", "frontmatter", f"{rel}: missing {miss}")
        if fm.get("layer") and fm["layer"] != p["layer"]:
            add("ERR", "layer-mismatch", f"{rel}: layer={fm['layer']} but in {p['layer']} zone")
        for l in p["wikilinks"]:
            if l not in names:
                add("WARN", "broken-link", f"{rel}: [[{l}]] does not resolve")
        if p["lines"] > 800:
            add("ERR", "oversized", f"{rel}: {p['lines']} lines (>800 hard) — split into atomic pages")
        elif p["lines"] > 400:
            add("WARN", "oversized", f"{rel}: {p['lines']} lines (>400 soft)")
        if inbound.get(p["name"], 0) == 0 and inbound.get(p["id"], 0) == 0:
            add("INFO", "orphan", f"{rel}: no inbound links")
        if fm.get("status") == "confirmed":
            classes = {src_class(s) for s in (fm.get("sources") or [])} - {"unknown"}
            if len(classes) < 2 or not (classes & NON_TRANSCRIPT):
                add("ERR", "two-source", f"{rel}: status=confirmed but source classes = "
                    f"{classes or '∅'} (need >=2 classes incl. >=1 non-transcript)")
        if fm.get("source_type") in ("system", "concept") and fm.get("sources") and "|" not in p["body"]:
            add("INFO", "fidelity?", f"{rel}: concept page cites a source but has no table — "
                f"verify no field/code table was dropped")

    for i, c in id_counts.items():
        if c > 1:
            add("ERR", "dup-id", f"id '{i}' used by {c} pages")

    order = {"ERR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: order[f[0]])
    counts = collections.Counter(f[0] for f in findings)
    print(f"wiki-lint: {counts.get('ERR', 0)} ERR · {counts.get('WARN', 0)} WARN · {counts.get('INFO', 0)} INFO   "
          f"(PROPOSED fixes — apply with approval, never auto-rewrite)")
    for sev, rule, msg in findings:
        print(f"  [{sev}] {rule}: {msg}")
    sys.exit(1 if counts.get("ERR") else 0)


if __name__ == "__main__":
    main()
