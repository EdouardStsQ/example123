#!/usr/bin/env python3
"""wiki_graph.py — optional graph layer over the LLM-Wiki, built on obsidiantools + networkx.

Markdown stays CANONICAL. obsidiantools parses the wiki/ vault (wikilinks + frontmatter + backlinks
+ orphans) into a networkx graph; we only ENRICH it with our `sources:` citations and typed `graph:`
edges. The graph is a CONFIDENTIAL, cross-layer, REBUILDABLE artifact under wiki/graph/ (gitignored)
— it is NOT part of the reusable qaracter IP.

Typed edges are declared in page frontmatter (pipe format), e.g.:
  graph:
    - "maps-to | murex-trade-model | core-source#8"

Run with the venv:  .venv/bin/python scripts/wiki_graph.py <cmd>
  build              rebuild + export wiki/graph/graph.graphml + graph.json, print stats
  orphans            isolated notes (no links)
  neighbors <note>   in/out edges of a note
  path <a> <b>       shortest connection a..b
  edges [rel]        list edges (optionally by relation)
  stats              summary
"""
import json, os, sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = os.path.join(ROOT, "wiki")
GRAPH = os.path.join(WIKI, "graph")

import networkx as nx
import obsidiantools.api as otools


def _layer(path):
    p = (path or "").replace(os.sep, "/")
    if "01_qaracter/" in p: return "qaracter"
    if "02_santander/" in p: return "santander"
    if "03_project/" in p: return "project"
    return "wiki"


def _fm(vault, note):
    idx = getattr(vault, "front_matter_index", None)
    if isinstance(idx, dict) and note in idx and idx[note]:
        return idx[note]
    try:
        return vault.get_front_matter(note) or {}
    except Exception:
        return {}


def _stem(p):
    return os.path.splitext(os.path.basename(str(p)))[0]


_META_STEMS = {"CLAUDE", "index", "log", "README", "CONVENTIONS", "ontology"}


def build_graph():
    """obsidiantools vault -> enriched networkx MultiDiGraph, keyed by canonical page id.

    Each wiki page becomes ONE node (its frontmatter `id`, else filename stem). obsidiantools
    path-qualifies on filename-stem collisions (a concept page vs a same-named source-summary) while
    our typed `graph:` edges use the bare id — so we re-key every reference to the canonical id,
    collapsing those phantom duplicates into a single node per page. Edges to non-pages are dropped.
    """
    vault = otools.Vault(Path(WIKI)).connect().gather()
    paths = getattr(vault, "md_file_index", {}) or {}

    def real(p):
        s = str(p)
        return not (s.endswith(".template.md") or _stem(s) in _META_STEMS)

    canon, attrs, alias, src_index = {}, {}, {}, {}
    # pass A — canonical id + attrs + authoritative id alias (a frontmatter id always wins)
    for k, p in paths.items():
        if not real(p):
            continue
        fm = _fm(vault, k)
        cid = str(fm.get("id") or _stem(p)).strip()
        canon[k] = cid
        attrs[cid] = {"layer": _layer(str(p)), "path": str(p), "type": str(fm.get("source_type", ""))}
        alias[cid] = cid
        if "08_source-summaries" in str(p).replace(os.sep, "/"):
            src_index[_stem(p)] = cid            # resolve `sources: [raw_id]` cites → the summary page
    # pass B — weak aliases (obsidiantools key + filename stem) that never override an id alias
    for k, p in paths.items():
        cid = canon.get(k)
        if cid:
            alias.setdefault(k, cid)
            alias.setdefault(_stem(p), cid)

    def rid(x):
        return alias.get(str(x), str(x))

    G = nx.MultiDiGraph()
    for cid, a in attrs.items():
        G.add_node(cid, **a)

    # wikilink edges from obsidiantools, re-keyed to canonical ids (drop dangling/meta targets)
    for u, v, d in nx.MultiDiGraph(vault.graph).edges(data=True):
        su, sv = rid(canon.get(u, u)), rid(canon.get(v, v))
        if su in G and sv in G and su != sv:
            G.add_edge(su, sv, rel=d.get("rel", "links"))

    # our enrichment edges, re-keyed, no self-loops
    for k, p in paths.items():
        cid = canon.get(k)
        if not cid:
            continue
        fm = _fm(vault, k)

        def link(tgt, rel, evidence=""):
            t = rid(tgt)
            if t in G and t != cid:
                G.add_edge(cid, t, rel=rel, evidence=evidence)

        for s in (fm.get("sources") or []):
            link(src_index.get(str(s), rid(s)), "cites")
        for c in (fm.get("composes") or []):
            link(c, "composes")
        if fm.get("generic_counterpart"):
            link(fm["generic_counterpart"], "refines")
        for g in (fm.get("graph") or []):
            parts = [x.strip() for x in str(g).split("|")]
            if len(parts) >= 2:
                link(parts[1], parts[0], parts[2] if len(parts) > 2 else "")
    return vault, G


def build():
    vault, G = build_graph()
    os.makedirs(GRAPH, exist_ok=True)
    H = nx.MultiDiGraph()
    for n, d in G.nodes(data=True):
        H.add_node(n, **{k: ("" if v is None else str(v)) for k, v in d.items()})
    for u, v, d in G.edges(data=True):
        H.add_edge(u, v, **{k: ("" if val is None else str(val)) for k, val in d.items()})
    nx.write_graphml(H, os.path.join(GRAPH, "graph.graphml"))
    with open(os.path.join(GRAPH, "graph.json"), "w", encoding="utf-8") as f:
        json.dump(nx.node_link_data(G, edges="links"), f, ensure_ascii=False, default=str)
    rels = {}
    for *_u, d in G.edges(data=True):
        r = d.get("rel", "links"); rels[r] = rels.get(r, 0) + 1
    print(f"✓ graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges → wiki/graph/ (graphml + json)")
    for r, c in sorted(rels.items()):
        print(f"    {c:4d}  {r}")
    iso = [n for n in G.nodes if G.degree(n) == 0]
    print(f"  isolated nodes: {len(iso)}" + (" — " + ", ".join(sorted(iso)) if iso else ""))


def orphans():
    _, G = build_graph()
    iso = sorted(n for n in G.nodes if G.degree(n) == 0)
    if not iso:
        return print("(no orphans)")
    for n in iso:
        print(" ", n)


def neighbors(note):
    _, G = build_graph()
    if note not in G:
        return print(f"(no node '{note}')")
    print(f"OUT {note}:")
    for _u, v, d in G.out_edges(note, data=True):
        print(f"  --{d.get('rel', 'links')}--> {v}" + (f"  [{d['evidence']}]" if d.get("evidence") else ""))
    print(f"IN  {note}:")
    for u, _v, d in G.in_edges(note, data=True):
        print(f"  <--{d.get('rel', 'links')}-- {u}")


def path(a, b):
    _, G = build_graph()
    try:
        print(" → ".join(nx.shortest_path(G.to_undirected(), a, b)))
    except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
        print(f"no path {a} → {b} ({type(e).__name__})")


def edges(rel=None):
    _, G = build_graph()
    for u, v, d in G.edges(data=True):
        r = d.get("rel", "links")
        if rel and r != rel:
            continue
        print(f"{u} --{r}--> {v}" + (f"  [{d['evidence']}]" if d.get("evidence") else ""))


def stats():
    _, G = build_graph()
    iso = sorted(n for n in G.nodes if G.degree(n) == 0)
    print(f"nodes: {G.number_of_nodes()}  edges: {G.number_of_edges()}  isolated: {len(iso)}")
    if iso:
        print("  isolated:", ", ".join(iso))


_HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Box Onboarding Brain — knowledge graph</title>
<script src="vis-network.min.js"></script>
<style>
 body{margin:0;font-family:system-ui,sans-serif;background:#0b1020;color:#e5e7eb}
 #net{width:100vw;height:100vh}
 #legend{position:fixed;top:12px;left:12px;background:#111827e0;padding:10px 14px;border-radius:8px;font-size:13px}
 .dot{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:7px;vertical-align:middle}
 h3{margin:0 0 8px;font-size:14px}
</style></head><body>
<div id="legend"><h3>LLM-Wiki graph</h3>
 <div><span class="dot" style="background:#3b82f6"></span>qaracter (reusable IP)</div>
 <div><span class="dot" style="background:#ef4444"></span>santander (confidential)</div>
 <div><span class="dot" style="background:#22c55e"></span>project (delivery)</div>
 <div><span class="dot" style="background:#9ca3af"></span>raw source / other</div>
</div>
<div id="net"></div>
<script>
 const nodes=new vis.DataSet(__NODES__), edges=new vis.DataSet(__EDGES__);
 new vis.Network(document.getElementById('net'),{nodes,edges},{
   nodes:{shape:'dot',scaling:{min:8,max:42},font:{color:'#e5e7eb',size:13}},
   edges:{color:{color:'#475569',highlight:'#f59e0b'},smooth:{type:'continuous'},
          arrows:{to:{scaleFactor:.5}},font:{size:9,color:'#94a3b8',strokeWidth:0,align:'middle'}},
   physics:{barnesHut:{gravitationalConstant:-9000,springLength:140},stabilization:{iterations:220}},
   interaction:{hover:true,tooltipDelay:120}
 });
</script></body></html>"""


def html():
    vault, G = build_graph()
    palette = {"qaracter": "#3b82f6", "santander": "#ef4444", "project": "#22c55e", "wiki": "#9ca3af"}
    nodes = [{"id": n, "label": n, "color": palette.get(d.get("layer", "wiki"), "#9ca3af"),
              "value": G.degree(n) + 1,
              "title": f"{n} · layer={d.get('layer', '')} · type={d.get('type', '')}"}
             for n, d in G.nodes(data=True)]
    es = [{"from": u, "to": v, "label": d.get("rel", ""), "arrows": "to",
           "title": d.get("evidence", "")} for u, v, d in G.edges(data=True)]
    os.makedirs(GRAPH, exist_ok=True)
    lib = os.path.join(GRAPH, "vis-network.min.js")
    if not os.path.exists(lib):  # vendor the lib locally → no external script at view time (offline + secure)
        try:
            import urllib.request
            urllib.request.urlretrieve(
                "https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js", lib)
        except Exception as e:
            print(f"  ! could not fetch vis-network.min.js ({e}) — place it in wiki/graph/ manually")
    out = os.path.join(GRAPH, "graph.html")
    doc = _HTML.replace("__NODES__", json.dumps(nodes, ensure_ascii=False)).replace("__EDGES__", json.dumps(es, ensure_ascii=False))
    open(out, "w", encoding="utf-8").write(doc)
    print(f"✓ wrote {out} — open it in a browser  ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")


def main():
    a = sys.argv[1:]
    if not a:
        return print(__doc__)
    c = a[0]
    if c == "build": build()
    elif c == "orphans": orphans()
    elif c == "stats": stats()
    elif c == "neighbors" and len(a) > 1: neighbors(a[1])
    elif c == "path" and len(a) > 2: path(a[1], a[2])
    elif c == "edges": edges(a[1] if len(a) > 1 else None)
    elif c == "html": html()
    else: print(__doc__)


if __name__ == "__main__":
    main()
