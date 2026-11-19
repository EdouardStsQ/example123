#!/usr/bin/env python3
"""
compare_fixed_width.py - the same report from two systems, record by record (box-report-migration-agent, ADR 0028).

    python3 scripts/compare_fixed_width.py <gbo file> <box file> --layout <layout.csv>
        [--key 1,8,10,15] [--gbo-ids <csv id,key>] [--box-ids <csv id,key>] [--only 4=DEPOSIT,SWAP ...]
        [--expect <expected-differences.csv>] [--out <report.md>] [--detail <csv outside the repo>]

1. Each record is cut by the layout; a short record is right-padded (counted). Field 1 (the trade id) is replaced by
   its common key when an id file is given (`id,key` - e.g. GBO header PK -> FRONT_ID, the GBO / BOX common key):
   the two systems need not use the same id for the comparison to work. An id with no key is counted and kept as is.
2. `--only` keeps the records whose field holds one of the values (both files; repeatable, all must hold) - e.g. the
   products in the BOX scope.
3. Byte-identical records (after step 1) are matched first, as a multiset: a record present twice on one side and
   once on the other leaves one unmatched (duplicates are part of the file).
4. The rest are grouped by the key fields (default 1, 8, 10, 15: trade, direction, NEAR/FAR, asset/liability) and
   paired in order within each group: each pair gives its differing fields; a record with no partner is GBO-only or
   BOX-only.
5. `--expect` (`field,gbo_value,box_value,class`; `*` = any value; values trimmed) names the differences that are
   expected - a decision or deviation id in `class` (e.g. `D1`, `DV7`); every other difference is unexplained.

The report holds counts only (per field, per class, per instrument; a sensitive field's values hashed): it can go into
the run folder. `--detail` writes every unmatched record and difference with real values - refused inside this
repository (trade-level data stays local). Standard library only.
Exit 0 no unexplained difference · 3 unexplained differences · 1 bad input · 2 refused.
"""
from __future__ import annotations

import argparse
import collections
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixed_width as fw  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TOP = 10


def load_ids(path) -> dict:
    if not path:
        return {}
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8")))
    if rows and not {"id", "key"} <= set(rows[0]):
        raise ValueError(f"{path}: columns id,key expected")
    return {r["id"].strip(): r["key"].strip() for r in rows}


def load_expect(path) -> list[dict]:
    if not path:
        return []
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8")))
    if rows and not {"field", "gbo_value", "box_value", "class"} <= set(rows[0]):
        raise ValueError(f"{path}: columns field,gbo_value,box_value,class expected")
    return [{"field": int(r["field"]), "gbo": r["gbo_value"].strip(), "box": r["box_value"].strip(),
             "class": r["class"].strip()} for r in rows]


def parse_only(specs) -> list[tuple[int, set]]:
    out = []
    for s in specs or []:
        n, _, vals = s.partition("=")
        if not n.strip().isdigit() or not vals:
            raise ValueError(f"--only {s!r}: expected <field number>=<value>[,<value>...]")
        out.append((int(n), {v.strip() for v in vals.split(",")}))
    return out


def prepare(path, fields, ids, only):
    """Records as tuples of trimmed values, field 1 replaced by its key; facts for the report."""
    reclen = fw.record_length(fields)
    recs, facts = fw.read_records(path)
    out, padded, long_, no_key, filtered = [], 0, 0, 0, 0
    for rec in recs:
        if len(rec) > reclen:
            long_ += 1
            continue
        if len(rec) < reclen:
            padded += 1
            rec = rec + " " * (reclen - len(rec))
        vals = [fw.value(r) for r in fw.split(rec, fields)]
        if any(vals[n - 1] not in keep for n, keep in only):
            filtered += 1
            continue
        if ids:
            if vals[0] in ids:
                vals[0] = ids[vals[0]]
            else:
                no_key += 1
        out.append(tuple(vals))
    facts.update(padded=padded, long=long_, no_key=no_key, filtered=filtered, kept=len(out))
    return out, facts


def classify(expect, n, g, b):
    for e in expect:
        if e["field"] == n and e["gbo"] in ("*", g) and e["box"] in ("*", b):
            return e["class"]
    return None


def compare(gbo, box, fields, key, expect):
    cg, cb = collections.Counter(gbo), collections.Counter(box)
    identical = sum((cg & cb).values())
    rg, rb = cg - cb, cb - cg
    groups = collections.defaultdict(lambda: ([], []))
    for rec, c in rg.items():
        groups[tuple(rec[k - 1] for k in key)][0].extend([rec] * c)
    for rec, c in rb.items():
        groups[tuple(rec[k - 1] for k in key)][1].extend([rec] * c)
    pairs, only_g, only_b = [], [], []
    for _, (g, b) in sorted(groups.items()):
        g, b = sorted(g), sorted(b)
        pairs += list(zip(g, b))
        only_g += g[len(b):]
        only_b += b[len(g):]
    diffs = []  # (field, gbo value, box value, class or None, gbo rec, box rec)
    for g, b in pairs:
        for f in fields:
            gv, bv = g[f.n - 1], b[f.n - 1]
            if gv != bv:
                diffs.append((f, gv, bv, classify(expect, f.n, gv, bv), g, b))
    return identical, pairs, only_g, only_b, diffs


def report(args, fields, key, fg, fb, identical, pairs, only_g, only_b, diffs):
    unexplained = sum(1 for d in diffs if d[3] is None) + len(only_g) + len(only_b)
    inst = next((f for f in fields if f.name == "instrument"), None)
    out = [f"# Report comparison - `{Path(args.gbo).name}` (GBO) vs `{Path(args.box).name}` (BOX)", "",
           f"Key fields: {', '.join(f'{k} {fields[k - 1].name}' for k in key)}"
           + (f" · filter: {', '.join(args.only)}" if args.only else ""), "",
           "| | GBO | BOX |", "|---|---|---|",
           f"| Records in the file | {fg['lines']} | {fb['lines']} |",
           f"| Left out by the filter | {fg['filtered']} | {fb['filtered']} |",
           f"| Compared | {fg['kept']} | {fb['kept']} |",
           f"| Short records padded | {fg['padded']} | {fb['padded']} |",
           f"| Records longer than the layout (not compared) | {fg['long']} | {fb['long']} |",
           f"| Trade id with no key in the id file | {fg['no_key']} | {fb['no_key']} |",
           f"| Identical records | {identical} | {identical} |",
           f"| Paired records with differences | {len(pairs)} | {len(pairs)} |",
           f"| Only on this side | {len(only_g)} | {len(only_b)} |", ""]
    if inst:
        out += [f"## Per {inst.name}", "", "| Value | GBO-only | BOX-only | Paired with differences |", "|---|---|---|---|"]
        per = collections.defaultdict(lambda: [0, 0, 0])
        for r in only_g:
            per[r[inst.n - 1]][0] += 1
        for r in only_b:
            per[r[inst.n - 1]][1] += 1
        for g, _ in pairs:
            per[g[inst.n - 1]][2] += 1
        out += [f"| {v or '(blank)'} | {a} | {b} | {c} |" for v, (a, b, c) in sorted(per.items())] or ["| — | 0 | 0 | 0 |"]
        out.append("")
    out += ["## Differences per field", "", "| # | Field | Differences | Expected (class: count) | Unexplained | "
            "Most frequent GBO → BOX |", "|---|---|---|---|---|---|"]
    byf = collections.defaultdict(list)
    for d in diffs:
        byf[d[0].n].append(d)
    for f in fields:
        ds = byf.get(f.n, [])
        if not ds:
            continue
        exp = collections.Counter(d[3] for d in ds if d[3])
        top = collections.Counter((d[1], d[2]) for d in ds).most_common(TOP)
        out.append(f"| {f.n} | {f.name} | {len(ds)} | {', '.join(f'{k}: {v}' for k, v in sorted(exp.items())) or '—'} | "
                   f"{sum(1 for d in ds if d[3] is None)} | "
                   f"{'; '.join(f'{fw.shown(f, g)} → {fw.shown(f, b)} ({c})' for (g, b), c in top)} |")
    if not diffs:
        out.append("| — | — | 0 | — | 0 | — |")
    out += ["", f"UNEXPLAINED|{unexplained}", f"COMPARE {'OK' if unexplained == 0 else 'DIFFERENCES'}"]
    return out, unexplained


def write_detail(path, fields, key, only_g, only_b, diffs):
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "key", "field", "gbo", "box", "class"])
        for r in only_g:
            w.writerow(["gbo-only", "|".join(r[k - 1] for k in key), "", "|".join(r), "", ""])
        for r in only_b:
            w.writerow(["box-only", "|".join(r[k - 1] for k in key), "", "", "|".join(r), ""])
        for f, g, b, cls, gr, _ in diffs:
            w.writerow(["difference", "|".join(gr[k - 1] for k in key), f"{f.n} {f.name}", g, b, cls or ""])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("gbo")
    ap.add_argument("box")
    ap.add_argument("--layout", required=True)
    ap.add_argument("--key", default="1,8,10,15")
    ap.add_argument("--gbo-ids")
    ap.add_argument("--box-ids")
    ap.add_argument("--only", action="append")
    ap.add_argument("--expect")
    ap.add_argument("--out")
    ap.add_argument("--detail")
    ap.add_argument("--repo-root", default=str(ROOT), help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.detail:
        d = Path(a.detail).resolve()
        if d == Path(a.repo_root).resolve() or Path(a.repo_root).resolve() in d.parents:
            print(f"REFUSED detail-in-repo: {a.detail} - trade-level data stays outside the repository (ADR 0028)",
                  file=sys.stderr)
            return 2
    try:
        fields = fw.load_layout(a.layout)
        key = [int(k) for k in a.key.split(",")]
        if any(k < 1 or k > len(fields) for k in key):
            raise ValueError(f"--key {a.key}: fields 1..{len(fields)}")
        only = parse_only(a.only)
        expect = load_expect(a.expect)
        gbo, fg = prepare(a.gbo, fields, load_ids(a.gbo_ids), only)
        box, fb = prepare(a.box, fields, load_ids(a.box_ids), only)
    except (fw.LayoutError, ValueError, OSError) as exc:
        print(f"REFUSED input: {exc}", file=sys.stderr)
        return 1
    identical, pairs, only_g, only_b, diffs = compare(gbo, box, fields, key, expect)
    out, unexplained = report(a, fields, key, fg, fb, identical, pairs, only_g, only_b, diffs)
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(out[-2])
        print(out[-1])
    else:
        print(text)
    if a.detail:
        write_detail(a.detail, fields, key, only_g, only_b, diffs)
    return 0 if unexplained == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
