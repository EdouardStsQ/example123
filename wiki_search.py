#!/usr/bin/env python3
"""wiki_search.py — stdlib BM25 search over the wiki, IP-zone-safe. No dependencies.

  python3 scripts/wiki_search.py "<query>" [--top N] [--layer qaracter|santander|project] [--visibility V] [--type T]
  python3 scripts/wiki_search.py --backlinks <note-or-id>
  python3 scripts/wiki_search.py --top-linked [N]

--layer is the IP guard: scoping to `qaracter` never returns santander/project rows.
"""
import collections
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _wikilib as W


def tok(s):
    return re.findall(r"[a-z0-9_]+", (s or "").lower())


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        return args[i + 1] if i + 1 < len(args) else default
    return default


def search(query, pages, top):
    docs = [(p, tok(p["title"] + " " + p["body"])) for p in pages]
    N = len(docs) or 1
    df = collections.Counter()
    for _p, t in docs:
        for w in set(t):
            df[w] += 1
    avgdl = (sum(len(t) for _p, t in docs) / N) or 1
    k1, b = 1.5, 0.75
    q = tok(query)
    scored = []
    for p, t in docs:
        tf = collections.Counter(t)
        dl = len(t) or 1
        s = 0.0
        for w in q:
            if w not in tf:
                continue
            idf = math.log((N - df[w] + 0.5) / (df[w] + 0.5) + 1)
            s += idf * (tf[w] * (k1 + 1)) / (tf[w] + k1 * (1 - b + b * dl / avgdl))
        if s > 0:
            scored.append((s, p))
    scored.sort(key=lambda x: -x[0])
    for s, p in scored[:top]:
        snip = re.sub(r"\s+", " ", p["body"]).strip()[:140]
        print(f"{s:5.2f}  [{p['layer']}] {p['relpath']}\n        {snip}")
    if not scored:
        print("(no matches)")


def main():
    a = sys.argv[1:]
    if not a:
        return print(__doc__)
    if a[0] == "--backlinks" and len(a) > 1:
        for p in W.iter_pages():
            if a[1] in p["wikilinks"]:
                print(f"[{p['layer']}] {p['relpath']}")
        return
    if a[0] == "--top-linked":
        nn = int(a[1]) if len(a) > 1 and a[1].isdigit() else 10
        inbound = collections.Counter(l for p in W.iter_pages() for l in p["wikilinks"])
        for t, c in inbound.most_common(nn):
            print(f"{c:4d}  {t}")
        return
    query = a[0]
    layer, vis, typ = opt(a, "--layer"), opt(a, "--visibility"), opt(a, "--type")
    top = int(opt(a, "--top", "10"))
    pages = [p for p in W.iter_pages()
             if (not layer or p["layer"] == layer)
             and (not vis or p["fm"].get("visibility") == vis)
             and (not typ or typ in (p["fm"].get("source_type"), p["fm"].get("page_type")))]
    search(query, pages, top)


if __name__ == "__main__":
    main()
