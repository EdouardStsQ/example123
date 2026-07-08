#!/usr/bin/env python3
"""wiki_stats.py — size / shape / health of the LLM-Wiki, per IP layer + delivery rows. Pure stdlib.

  python3 scripts/wiki_stats.py
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _wikilib as W


def main():
    pages = list(W.iter_pages())
    n = len(pages)
    if not n:
        return print("no pages yet")
    by_layer = collections.Counter(p["layer"] for p in pages)
    by_type = collections.Counter((p["fm"].get("source_type") or p["fm"].get("page_type") or "—") for p in pages)
    by_status = collections.Counter((p["fm"].get("status") or "—") for p in pages)
    total_links = sum(len(p["wikilinks"]) for p in pages)
    names = {p["name"] for p in pages} | {p["id"] for p in pages}
    inbound = collections.Counter(l for p in pages for l in p["wikilinks"])
    oversized_hard = [p for p in pages if p["lines"] > 800]
    soft = sum(1 for p in pages if p["lines"] > 400)
    orphans = [p for p in pages if inbound.get(p["name"], 0) == 0 and inbound.get(p["id"], 0) == 0]
    proposed = [p for p in pages if p["fm"].get("status") in ("proposed", "open-question")]
    confirmed = [p for p in pages if p["fm"].get("status") == "confirmed"]
    unverified = sum(len(re.findall(r"\bUNVERIFIED\b", p["body"]))
                     for p in pages if "12_evidence-map" in p["relpath"] or "traceability" in p["relpath"])
    thr = next((str(t) for t in (50, 150, 300, 500, 1000) if n < t), ">=1000")

    print(f"PAGES: {n}   link-density: {total_links / n:.2f} links/page   "
          f"sources-cited: {sum(len(p['fm'].get('sources') or []) for p in pages)}")
    print("by layer:   " + "  ".join(f"{k}={v}" for k, v in sorted(by_layer.items())))
    print("by type:    " + "  ".join(f"{k}={v}" for k, v in sorted(by_type.items())))
    print("by status:  " + "  ".join(f"{k}={v}" for k, v in sorted(by_status.items())))
    print(f"oversized:  soft(>400)={soft}  hard(>800)={len(oversized_hard)}")
    for p in oversized_hard:
        print(f"    HARD {p['lines']:4d}  {p['relpath']}")
    print(f"orphans (no inbound links): {len(orphans)}")
    hubs = [(t, c) for t, c in inbound.most_common(8) if t in names]
    print("top-linked (hubs): " + (", ".join(f"{t}({c})" for t, c in hubs) or "—"))
    print("--- delivery ---")
    print(f"pages proposed/open-question (need a 2nd source to confirm): {len(proposed)}")
    print(f"pages confirmed: {len(confirmed)}")
    print(f"UNVERIFIED required-field markers in the spine: {unverified}")
    print(f"--- scale: {n} pages → next threshold {thr}  (shard index at 150, weekly lint at 500) ---")
    if total_links / n < 1.5:
        print("  ! low link density (<1.5/page) — run /lint-wiki --suggest cross-links")


if __name__ == "__main__":
    main()
