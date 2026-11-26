#!/usr/bin/env python3
"""
fe_assess.py - the GBO vs BOX FE assessment of a parallel / Y test run: which deals can be compared, do they match,
and every difference classed by a known cause [operator, 2026-11-25 - ADR 0030].

    python3 scripts/fe_assess.py <run>                 every date of 01-evidence/
    python3 scripts/fe_assess.py <run> --date 2026-09-25

Reads what `fe_reconcile.py pack` asks the operator to export, per date and product (01-evidence/<date>/):
  gbo-<p>-financial.csv (or gbo-<p>-financial-*.csv), box-<p>-financial.csv   required
  gbo-<p>-deal.csv, box-<p>-deal.csv                                          optional (funnel step b, deal fields)
  box-<p>-flows.csv  (GBO_DEAL_ID, N_DIRECTIONS, N_DIR_CURRENT_INTEREST, N_DIR_DATED - sql/12)   optional (step c)
the field map (keys: docs/reference/gbo-box-fe-field-map.csv) and the rules (docs/reference/fe-recon-rules.csv).

1. The CLEAN set - deals BOX holds completely; the others are counted per reason and left out (missing data is
   followed separately, never mixed with calculation differences):
     a. legs: the same legs (key after GBO_DEAL_ID, e.g. direction x currency) on both sides, all-zero rows dropped
     b. deal data: every leg (or the deal) in both deal extracts
     c. flows: BOX has a current interest flow (start <= date < end) on every direction of the deal
     d. inputs: no BOX input column blank where GBO fills it (rules `input_required`)
2. Each field of each clean leg compared (amounts within 0.01, dates by day, text case-blind, codes numerically), then
   the rules: exclude, blank_zero, decode, gbo_sentinel, rename, and for what still differs, in order: rebook (the deal
   is flagged by a `rebook_flag` rule), by_design / to_confirm (BOX blank / 0), date_lag, gbo_zero, box_zero - else
   "DIFF - unexplained", the only class that needs a person (and the BOX FE code first: cib-boxfin-dbboxfe).
3. Outputs: 03-assessment.md in the run (counts only - it can be committed); in <run>/local/ (git-ignored, trade
   level): <date>-<p>-assessment.xlsx (Summary, Issues with one real example per type, Deals, Details, Excluded,
   Rules) and <date>-<p>-details.csv.
Full match = a clean deal with no field in a mismatch class (unexplained, rebooked, functional). Standard library
only. Exit 0 written · 1 refused · 2 bad invocation.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fe_reconcile as R  # noqa: E402
import xlsx_lite  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "docs/reference/fe-recon-rules.csv"
MISMATCH = ("DIFF", "rebooked", "functional")
UNEXPLAINED = "DIFF - unexplained"


# --- rules -------------------------------------------------------------------------------------------------------
def load_rules(path: Path, product: str) -> list:
    out = []
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if r["product"].strip().lower() in ("*", product):
            r = {k: (v or "").strip() for k, v in r.items()}
            r["pats"] = [re.compile(p, re.I) for p in r["columns"].split("|") if p]
            out.append(r)
    return out


def rules_for(rules, kind, area, col=None):
    return [r for r in rules if r["rule"] == kind and r["area"] in ("*", area)
            and (col is None or not r["pats"] or any(p.fullmatch(col) for p in r["pats"]))]


def excluded(rules, area, col) -> bool:
    return bool(rules_for(rules, "exclude", area, col)) or bool(R.SKIP_AUTO.match(col))


# --- values ------------------------------------------------------------------------------------------------------
def num(v):
    return R.num(v)


def blank(v) -> bool:
    return not str(v if v is not None else "").strip()


def zeroish(v) -> bool:
    n = num(v)
    return blank(v) or (n is not None and abs(n) < 1e-12)


def days(a, b):
    """b - a in days, or None."""
    import datetime
    try:
        x = datetime.date.fromisoformat(R.day(a))
        y = datetime.date.fromisoformat(R.day(b))
        return (y - x).days
    except ValueError:
        return None


def equal(kind, g, b, blank_zero: bool) -> tuple[bool, str]:
    if kind == "amount":
        x, y = num(g), num(b)
        if blank_zero:
            x = 0.0 if blank(g) else x
            y = 0.0 if blank(b) else y
        if x is None and y is None:
            return str(g).strip() == str(b).strip(), ""
        if x is None or y is None:
            return False, ""
        d = y - x
        return abs(d) <= 0.01, f"{d:.6f}".rstrip("0").rstrip(".")
    if kind == "date":
        return (R.day(g) == R.day(b)) if not (blank(g) and blank(b)) else True, ""
    a_, b_ = R.key_part(g).upper(), R.key_part(b).upper()
    return a_ == b_, ""


# --- one date x product ------------------------------------------------------------------------------------------
class Out:
    def __init__(self):
        self.funnel, self.excluded, self.details, self.notes = [], [], [], []


def key_cols(fmap, area):
    k = (fmap[area].get("key") or {}).get("gbo_column", "")
    return [c.strip() for c in k.split(",") if c.strip()] if k and "<" not in k else []


def read_side(ev, d, prod, area, side):
    files = ([ev / d / f"{side}-{prod}-{area}.csv"] + sorted((ev / d).glob(f"{side}-{prod}-{area}-*.csv")))
    files = [f for f in files if f.exists()]
    return [r for f in files for r in R.rows_of(f, d)] if files else None


def col_of(row, name):
    return next((c for c in row if c.upper() == name.upper()), None)


def assess_one(run: Path, d: str, prod: str, fmap, rules, res: R.Result):
    ev, o = run / "01-evidence", Out()
    G = read_side(ev, d, prod, "financial", "gbo")
    B = read_side(ev, d, prod, "financial", "box")
    if G is None or B is None:
        res.err("evidence-missing", f"01-evidence/{d}", f"gbo-{prod}-financial.csv / box-{prod}-financial.csv")
        return None
    fk = key_cols(fmap, "financial") or ["GBO_DEAL_ID"]
    for side, rows in (("GBO", G), ("BOX", B)):
        if rows and any(col_of(rows[0], c) is None for c in fk):
            res.err("key-missing", f"{side} financial {d}", f"key {','.join(fk)} not in the CSV")
            return None
    dk = fk[0]

    # all-zero rows (e.g. BOX's USD settlement row) are not legs
    amt_cols = [c for c in (G[0] if G else {}) if c in (B[0] if B else {}) and not excluded(rules, "financial", c)
                and not c.upper().startswith(("FK_", "ID_")) and c.upper() not in {x.upper() for x in fk}
                and R.kind_of([r.get(c) for r in G + B]) == "amount"]
    zero_drop = Counter()
    if rules_for(rules, "all_zero_row", "financial"):
        def nonzero(r):
            return any(not zeroish(r.get(c)) for c in amt_cols)
        for side, rows in (("GBO", G), ("BOX", B)):
            keep = [r for r in rows if nonzero(r)]
            zero_drop[side] = len(rows) - len(keep)
            if side == "GBO":
                G = keep
            else:
                B = keep

    def legs(rows):
        out = defaultdict(set)
        for r in rows:
            out[R.key_part(r[col_of(r, dk)])].add("|".join(R.key_part(r[col_of(r, c)]) for c in fk[1:]))
        return out
    gl, bl = legs(G), legs(B)
    deals = sorted(set(gl) | set(bl))
    o.funnel.append(("deals on either side (financial data)", len(deals)))
    o.funnel.append(("GBO deals / BOX deals", f"{len(gl)} / {len(bl)}"))
    o.notes.append(f"all-zero financial rows dropped before matching legs: GBO {zero_drop['GBO']}, BOX {zero_drop['BOX']}")

    clean = []
    for x in deals:
        if x not in bl:
            o.excluded.append((x, "GBO only (not in BOX)"))
        elif x not in gl:
            o.excluded.append((x, "BOX only (not in GBO)"))
        elif gl[x] != bl[x]:
            miss = sorted(gl[x] - bl[x])
            o.excluded.append((x, f"a. legs differ - BOX lacks {miss}" if miss else f"a. legs differ - BOX extra {sorted(bl[x] - gl[x])}"))
        else:
            clean.append(x)
    o.funnel.append(("a. same legs on both sides", len(clean)))

    # b. deal data
    GD = read_side(ev, d, prod, "deal", "gbo")
    BD = read_side(ev, d, prod, "deal", "box")
    dkc = key_cols(fmap, "deal") or [dk]
    if GD is not None and BD is not None and GD and BD:
        def dkeys(rows):
            return {"|".join(R.key_part(r[col_of(r, c)]) for c in dkc) for r in rows if all(col_of(r, c) for c in dkc)}
        gdk, bdk = dkeys(GD), dkeys(BD)
        keep = []
        for x in clean:
            need = {x + ("|" + leg if leg and len(dkc) > 1 else "") for leg in gl[x]} if len(dkc) > 1 else {x}
            if need <= gdk and need <= bdk:
                keep.append(x)
            else:
                o.excluded.append((x, "b. deal data row missing" + (" in BOX" if need <= gdk else " in GBO")))
        clean = keep
        o.funnel.append(("b. every leg in both deal extracts", len(clean)))
    else:
        GD = BD = None
        o.notes.append("step b skipped: no deal extracts for this date")

    # c. flows
    fl = ev / d / f"box-{prod}-flows.csv"
    if fl.exists():
        F = {}
        for r in R.rows_of(fl, d):
            c = col_of(r, "GBO_DEAL_ID")
            if c:
                F[R.key_part(r[c])] = r
        keep = []
        for x in clean:
            ndir = len({leg.split("|")[0] for leg in bl[x]}) if len(fk) > 1 else 1
            r = F.get(x)
            cur = num(r.get(col_of(r, "N_DIR_CURRENT_INTEREST") or "", "")) if r else None
            if r is None or cur is None or cur < ndir:
                o.excluded.append((x, "c. BOX lacks the current interest flow on a direction"
                                   + ("" if r else " (no BOX flow at all)")))
            else:
                keep.append(x)
        clean = keep
        o.funnel.append(("c. BOX current interest flow on every direction", len(clean)))
    else:
        o.notes.append(f"step c skipped: no box-{prod}-flows.csv (sql/12) for this date")

    # d. inputs
    req = rules_for(rules, "input_required", "deal")
    if req and BD is not None:
        bidx = {R.key_part(r[col_of(r, dk)]): r for r in BD if col_of(r, dk)}
        gidx = {R.key_part(r[col_of(r, dk)]): r for r in GD if col_of(r, dk)}
        keep = []
        for x in clean:
            br, gr = bidx.get(x, {}), gidx.get(x, {})
            bad = [c for c in br for rr in req if any(p.fullmatch(c) for p in rr["pats"])
                   and blank(br.get(c)) and not blank(gr.get(col_of(gr, c) or "", ""))]
            if bad:
                o.excluded.append((x, f"d. BOX input blank: {', '.join(sorted(set(bad)))}"))
            else:
                keep.append(x)
        clean = keep
        o.funnel.append(("d. inputs complete", len(clean)))
    o.funnel.append(("CLEAN - compared", len(clean)))
    cs = set(clean)

    # rebook flags (deal level)
    reb = set()
    for area, GG, BB in (("financial", G, B), ("deal", GD, BD)):
        if GG is None or BB is None:
            continue
        gi = defaultdict(list)
        for r in GG:
            gi[R.key_part(r[col_of(r, dk)])].append(r)
        bi = defaultdict(list)
        for r in BB:
            bi[R.key_part(r[col_of(r, dk)])].append(r)
        for rr in rules_for(rules, "rebook_flag", area):
            for x in cs:
                gcols = [c for c in (gi[x][0] if gi[x] else {}) if any(p.fullmatch(c) for p in rr["pats"])]
                for c in gcols:
                    gv = [r.get(c) for r in gi[x]]
                    bv = [r.get(col_of(r, c) or "") for r in bi[x]]
                    if rr["param"] == "gbo_later":
                        if any(days(b_, g_) is not None and days(b_, g_) > 0 for g_ in gv for b_ in bv):
                            reb.add(x)
                    elif rr["param"] == "gbo_zero_box_nonzero":
                        if gv and bv and all(zeroish(v) for v in gv) and any(not zeroish(v) for v in bv):
                            reb.add(x)

    # compare the clean legs
    for area, GG, BB in (("financial", G, B), ("deal", GD, BD)):
        if GG is None or BB is None:
            continue
        akc = key_cols(fmap, area) or [dk]
        def index(rows):
            ix = {}
            for r in rows:
                cs_ = [col_of(r, c) for c in akc]
                if all(cs_):
                    k = "|".join(R.key_part(r[c]) for c in cs_)
                    if k.split("|")[0] in cs:
                        ix.setdefault(k, r)
            return ix
        gi, bi = index(GG), index(BB)
        if not gi or not bi:
            continue
        g0, b0 = next(iter(gi.values())), next(iter(bi.values()))
        bup = {c.upper(): c for c in b0}
        pairs = []
        for cg in g0:
            if excluded(rules, area, cg) or cg.upper() in {k.upper() for k in akc}:
                continue
            rn = rules_for(rules, "rename", area, cg)
            cb = bup.get((rn[0]["box_value"] if rn else cg).upper())
            if cb:
                pairs.append((cg, cb))
        kd = {cg: R.kind_of([r.get(cg) for r in gi.values()] + [r.get(cb) for r in bi.values()]) for cg, cb in pairs}
        bz = bool(rules_for(rules, "blank_zero", area))
        for k in sorted(set(gi) & set(bi)):
            x = k.split("|")[0]
            gr, br = gi[k], bi[k]
            box_id = br.get(col_of(br, "DEAL_ID") or "", "")
            for cg, cb in pairs:
                gv, bv = gr.get(cg, ""), br.get(cb, "")
                ok, diff = equal(kd[cg], gv, bv, bz)
                cls = None
                if not ok:
                    for rr in rules_for(rules, "decode", area, cg) + rules_for(rules, "decode", area, cb):
                        if R.key_part(gv) in [R.key_part(v) for v in rr["gbo_value"].split("|")] and \
                                R.key_part(bv) in [R.key_part(v) for v in rr["box_value"].split("|")]:
                            ok = True
                for rr in rules_for(rules, "gbo_sentinel", area, cg):
                    if R.day(gv) in {R.day(v) for v in rr["gbo_value"].split("|")}:
                        ok, cls = (True, None) if blank(bv) else (False, rr["class"])
                if ok:
                    continue
                if cls is None:
                    cls = classify(rules, area, cg, cb, kd[cg], gv, bv, x in reb)
                o.details.append((x, box_id, area, "|".join(k.split("|")[1:]), f"{cg}" + (f" / {cb}" if cb != cg else ""),
                                  gv, bv, diff, cls))
    o.clean, o.rebooked = clean, reb
    return o


def classify(rules, area, cg, cb, kind, gv, bv, rebooked: bool) -> str:
    if rebooked and (rules_for(rules, "rebook", area, cg) or rules_for(rules, "rebook", area, cb)):
        return rules_for(rules, "rebook", area, cg)[0]["class"] if rules_for(rules, "rebook", area, cg) \
            else rules_for(rules, "rebook", area, cb)[0]["class"]
    for kind_ in ("by_design", "to_confirm"):
        rr = rules_for(rules, kind_, area, cg) or rules_for(rules, kind_, area, cb)
        if rr and zeroish(bv):
            return rr[0]["class"]
    for rr in rules_for(rules, "date_lag", area, cg):
        lo, hi = (int(x) for x in (rr["param"] or "1:7").split(":"))
        n = days(gv, bv)
        if n is not None and lo <= n <= hi:
            return rr["class"]
    for rr in rules_for(rules, "gbo_zero", area, cg):
        if zeroish(gv) and not zeroish(bv):
            return rr["class"]
    for rr in rules_for(rules, "box_zero", area, cg):
        if zeroish(bv) and not zeroish(gv):
            return rr["class"]
    return UNEXPLAINED


# --- reports -----------------------------------------------------------------------------------------------------
def summarise(o):
    by_deal = defaultdict(list)
    for det in o.details:
        by_deal[det[0]].append(det)
    mism = {x for x, ds in by_deal.items() if any(det[8].startswith(MISMATCH) for det in ds)}
    func_only = {x for x in mism if all(det[8].startswith(("functional",)) or not det[8].startswith(MISMATCH)
                                        for det in by_deal[x])}
    types = defaultdict(lambda: {"fields": Counter(), "deals": set(), "legs": 0, "ex": None})
    for det in o.details:
        cls = det[8]
        key = (cls, det[4].split(" / ")[0]) if cls == UNEXPLAINED else (cls, "")
        t = types[key]
        t["fields"][det[4]] += 1
        t["deals"].add(det[0])
        t["legs"] += 1
        if t["ex"] is None or (det[7] and abs(num(det[7]) or 0) > abs(num(t["ex"][7]) or 0)):
            t["ex"] = det
    order = lambda kv: (0 if kv[0][0].startswith("rebooked") else 1 if kv[0][0].startswith("functional") else
                        2 if kv[0][0] == UNEXPLAINED else 3 if kv[0][0].startswith("not calculated") else 4,
                        -len(kv[1]["deals"]))
    return mism, func_only, sorted(types.items(), key=order)


def write_reports(run: Path, d: str, prod: str, o, rules):
    mism, func_only, types = summarise(o)
    n = len(o.clean)
    full = n - len(mism)
    head = [("clean deals compared", n), ("full match (no mismatch class)", full),
            ("full match leaving aside the functional differences", full + len(func_only)),
            ("rebooked deals (flagged)", len(o.rebooked & set(o.clean)))]
    md = [f"## {d} - {prod}", "", "| Funnel | Deals |", "|---|---|"] + [f"| {a} | {b} |" for a, b in o.funnel]
    md += ["", "| Headline | Deals |", "|---|---|"] + [f"| {a} | {b} |" for a, b in head]
    md += ["", "| # | Mismatch type | Class | Fields | Deals | Leg x field rows |", "|---|---|---|---|---|---|"]
    for i, ((cls, f), t) in enumerate(types, 1):
        label = f"{f} differs - no rule explains it" if cls == UNEXPLAINED else cls
        md.append(f"| {i} | {label} | {cls.split(' - ')[0]} | {', '.join(sorted(t['fields']))} | {len(t['deals'])} | "
                  f"{t['legs']} |")
    ex = Counter(r for _, r in o.excluded)
    md += ["", "| Left out of the comparison (missing data) | Deals |", "|---|---|"] + \
          [f"| {r} | {c} |" for r, c in sorted(ex.items(), key=lambda kv: -kv[1])]
    md += ["", *[f"- {nt}" for nt in o.notes], ""]
    loc = run / "local"
    loc.mkdir(exist_ok=True)
    hdr = ["GBO_DEAL_ID", "BOX_DEAL_ID", "area", "leg", "field (GBO / BOX)", "GBO", "BOX", "difference", "class"]
    with (loc / f"{d}-{prod}-details.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(hdr)
        w.writerows(o.details)
    V = xlsx_lite.as_number
    issues = [["#", "Mismatch type", "Class", "Fields", "Deals", "Rows", "Example GBO DEAL_ID", "Example BOX DEAL_ID",
               "Leg", "Field", "GBO value", "BOX value", "Difference"]]
    for i, ((cls, f), t) in enumerate(types, 1):
        e = t["ex"]
        issues.append([i, f"{f} differs - no rule explains it" if cls == UNEXPLAINED else cls, cls.split(" - ")[0],
                       ", ".join(sorted(t["fields"])), len(t["deals"]), t["legs"], e[0], e[1], e[3], e[4], V(e[5]),
                       V(e[6]), V(e[7])])
    by_deal = defaultdict(list)
    for det in o.details:
        by_deal[det[0]].append(det)
    deals = [["GBO_DEAL_ID", "Rebooked", "Status", "Mismatch fields", "Other (explained) fields"]]
    for x in o.clean:
        ds = by_deal.get(x, [])
        mf = sorted({det[4] for det in ds if det[8].startswith(MISMATCH)})
        of = sorted({det[4] for det in ds if not det[8].startswith(MISMATCH)})
        deals.append([x, "yes" if x in o.rebooked else "", "MATCH" if not mf else "MISMATCH", ", ".join(mf), ", ".join(of)])
    summary = [["Item", "Value"]] + [[a, b] for a, b in o.funnel] + [["", ""]] + [[a, b] for a, b in head] + \
              [["note", nt] for nt in o.notes]
    rl = [["product", "area", "rule", "columns", "gbo_value", "box_value", "param", "class", "status", "source", "note"]] + \
         [[r[k] for k in rl_keys] for r in rules for rl_keys in [("product", "area", "rule", "columns", "gbo_value",
                                                                  "box_value", "param", "class", "status", "source", "note")]]
    xlsx_lite.write(loc / f"{d}-{prod}-assessment.xlsx", [
        ("Summary", summary), ("Issues", issues), ("Deals", deals),
        ("Details", [hdr] + [[a, b, c, e, f, V(g), V(h), V(i), j] for a, b, c, e, f, g, h, i, j in o.details]),
        ("Excluded", [["GBO_DEAL_ID", "reason"]] + [[x, r] for x, r in o.excluded]), ("Rules", rl)])
    return md, n, full, len([1 for (c, _), _t in types if c == UNEXPLAINED])


def assess(run: Path, res: R.Result, only=None) -> int:
    mode, cfg = R.read_inputs(run, res)
    if cfg is None:
        return 1
    rp = Path(cfg.get("rules") or RULES)
    rp = rp if rp.is_absolute() else ROOT / rp
    mp = Path(cfg.get("field_map") or R.MAP)
    mp = mp if mp.is_absolute() else ROOT / mp
    for p_, what in ((rp, "rules-missing"), (mp, "map-missing")):
        if not p_.exists():
            res.err(what, str(p_), "the rules / field map file")
            return 1
    ev = run / "01-evidence"
    dates = sorted(p.name for p in ev.iterdir() if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name)) \
        if ev.exists() else []
    dates = [x for x in dates if not only or x == only]
    if not dates:
        res.err("evidence-missing", str(ev), "no 01-evidence/<YYYY-MM-DD>/ folder")
        return 1
    md = [f"# Assessment - {'Y test' if mode == 'y' else 'parallel test'} {cfg.get('branch', '')} "
          f"({', '.join(R.products_of(cfg))})", "",
          "Counts only (trade-level detail in the run's git-ignored `local/`). Classes and rules: "
          "`docs/reference/fe-recon-rules.csv`; method: ADR 0030. Only **DIFF - unexplained** needs a person - BOX FE "
          "code first (`cib-boxfin-dbboxfe`).", ""]
    lines = []
    for d in dates:
        for prod in R.products_of(cfg):
            fmap = R.load_map(mp, prod, R.AREAS)
            o = assess_one(run, d, prod, fmap, load_rules(rp, prod), res)
            if o is None:
                return 1
            m, n, full, unex = write_reports(run, d, prod, o, load_rules(rp, prod))
            md += m
            lines.append(f"  {d} {prod}: {n} clean deal(s), {full} full match, {unex} unexplained type(s) -> "
                         f"local/{d}-{prod}-assessment.xlsx")
    (run / "03-assessment.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {run / '03-assessment.md'}")
    print("\n".join(lines))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("run")
    ap.add_argument("--date")
    a = ap.parse_args(argv)
    run = Path(a.run)
    if not run.is_dir():
        print(f"not a folder: {run}", file=sys.stderr)
        return 2
    res = R.Result()
    if (run / ".frozen").exists():
        res.err("run-frozen", str(run), "start a new version (scripts/new_run.py)")
        return 1
    return assess(run, res, a.date)


if __name__ == "__main__":
    sys.exit(main())
