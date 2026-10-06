#!/usr/bin/env python3
"""
build_fe_jobs.py - a new branch's BOX FE jobs for one instrument, copied from a reference branch [2026-10-02].

    python3 scripts/build_fe_jobs.py runs/<BRANCH>/<env>/fe-jobs/<instrument>/

Agent `box-fe-jobs-agent`. Reads <folder>/fe-jobs-inputs.json (shape: agents/box-fe-jobs-agent/templates/
fe-jobs-inputs.example.json), the reference environment's jobs-inventory.csv + db.conf (parse_job_confs.py), the
reference branch's Control-M folder JSON, the target's books register (skill set-up-book-labels) and the reference
books' descriptions. Writes into <folder>/out/:

  db.conf.proposal        the target's FE db.conf lines (lines the target wrapper cannot run are commented OPEN)
  <FOLDER_NAME>.json      the target's Control-M folder: the reference chain, renamed, re-wired, re-hosted
  mapping.csv             every reference job -> every target job, with level, book and where it came from
  report.md               what was built, what is OPEN, what to hand to other folders

How (box-batch-chain.md L1/L2; agents/box-fe-jobs-agent/AGENT.md):
  1. seed  = the reference's EXECUTED db.conf BOX rows for the instrument (GMBX<n> or the instrument constant),
             in the template book or at branch level (book 00), found in the reference Control-M folder;
  2. close = add every same-folder job a seed waits for, transitively (e.g. the book's GMBX0..D01-D03 and the
             branch's queue job). A wait on an event no job of the folder emits is EXTERNAL: it must be mapped;
  3. copy  = a per-book job once per target book, a branch-level job once; names: token and book swapped
             (GMBX1LB15D04 -> GMBX1NY01D04), old names from `renames`; events renamed the same way
             (G010014-/G010012- prefixes kept); a wait on another reference book's job of the same step becomes
             a wait on every target book's;
  4. db.conf = the reference line with job name, wrapper owner, branch constant, other constants and label swapped;
  5. check = every wait resolves inside the folder or to a mapped external event; no cycle; new-convention names.
Nothing is guessed: an input still '<...>' is refused with the field to ask for. When renames or external events
are missing, <folder>/pending-questions.md says, per question, who emits the event, in which folder / repo, what the
job is (skill explain-box-job: inventory, every Control-M repo in reference.controlm_json + controlm_other, group
names from reference.dml_repos) and a suggested answer - the operator decides [2026-10-06]. Standard library only.
Exit 0 written · 1 refused · 4 written with OPEN lines (the target wrapper cannot take the label).
"""
from __future__ import annotations

import copy
import csv
import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from find_jobs import ALIASES, PRODUCTS  # noqa: E402
import explain_job  # noqa: E402  (skill explain-box-job: who emits an event, what a job is)

INPUTS = "fe-jobs-inputs.json"
OUT = "out"
NEW_RE = re.compile(r"GMBX(\d)([A-Z]{2})(\d{2})D(\d{2})")
EVENT_RE = re.compile(r"^((?:G\d{6}-)?)(.+?)(-(?:OK|NOK))$")
LABEL_RE = re.compile(r"f_getPKByLabel\s*\(\s*'([^']*)'\s*\)", re.I)
CONST_RE = re.compile(r"\bCST_[A-Z0-9_]+\b", re.I)
REQUIRED = {  # path -> what to ask the operator
    "reference.env_folder": "the reference environment folder (runs/_reference/<env>/)",
    "reference.controlm_json": "the reference branch's FE Control-M JSON (e.g. cib-boxfin-t1mdslbfe/projects/cib-boxfin-t1mdslbfe.json)",
    "reference.token": "the reference branch's job-name token (SLB: LB)",
    "reference.branch_const": "the reference branch constant in its db.conf (SLB: CST_PK_BRANC_LND)",
    "reference.wrapper_owner": "the reference wrapper owner (Tier 1: PGT_ES)",
    "reference.display": "how the reference branch is written in job descriptions (SLB: SLB)",
    "reference.books_csv": "the reference books' labels, CODE + DESCRIPTION (query J-R3b)",
    "instrument": "the instrument (depos, irs, ccs, cfm, fra, otc, cap, commodities)",
    "target.branch_code": "the target branch code (NY_SCH)",
    "target.token": "the target job-name token (the label code without X and number: XNY01 -> NY)",
    "target.display": "how the target branch is written in job descriptions (e.g. NY)",
    "target.wrapper_owner": "the target wrapper owner (J-E1 in the target: PGT_NY)",
    "target.wrapper_args": "the target f_ExecuteGroup argument count (J-E4: 5 = no label, 7 = label)",
    "target.branch_const": "the target branch constant in its wrapper (J-E4)",
    "target.books_register": "the target's books register (runs/<BRANCH>/<env>/books/books-register.csv)",
    "controlm.folder_name": "the target Control-M folder name",
    "controlm.ControlmServer": "the Control-M server of the target folder",
    "controlm.SiteStandard": "the site standard of the target folder",
    "controlm.OrderMethod": "the order method of the target folder",
    "controlm.Host": "the host the target jobs run on (in the folder file; per-environment hosts may be applied by a config repo)",
    "controlm.FilePath": "where the target's job scripts live (the reference uses /appl/gm/scripts)",
    "controlm.RunAs": "the user the target jobs run as",
    "controlm.Application": "the Control-M application of the target jobs",
    "controlm.MonthDaysCalendar": "the target branch's calendar",
    "controlm.CreatedBy": "CreatedBy for the new jobs (an ID, or 'omit')",
}


class Result:
    def __init__(self):
        self.errors, self.warns = [], []

    def err(self, code, where, msg):
        self.errors.append((code, where, msg))

    def warn(self, code, where, msg):
        self.warns.append((code, where, msg))


def get(d, path):
    for k in path.split("."):
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def undecided(v) -> bool:
    return v is None or (isinstance(v, str) and (not v.strip() or v.strip().startswith("<")))


def resolve(base: Path, p: str) -> Path:
    q = Path(p)
    if q.is_absolute() or q.exists():
        return q
    for root in (base, *base.parents):
        if (root / p).exists():
            return root / p
    return q


def load_folder(path: Path):
    """(folder name, header scalars, {job: object}, {job: line}) of a Control-M SimpleFolder export."""
    text = path.read_text(encoding="utf-8", errors="replace")
    root = json.loads(text)
    name, folder = next(((k, v) for k, v in root.items() if isinstance(v, dict) and "Folder" in str(v.get("Type", ""))),
                        (None, None))
    if folder is None:
        return None, {}, {}, {}
    header = {k: v for k, v in folder.items() if not isinstance(v, (dict, list))}
    jobs, lines = {}, {}
    for k, v in folder.items():
        if isinstance(v, dict) and str(v.get("Type", "")).startswith("Job"):
            jobs[k] = v
            m = re.search(r'"' + re.escape(k) + r'"\s*:\s*\{', text)
            lines[k] = text.count("\n", 0, m.start()) + 1 if m else 0
    return name, header, jobs, lines


def event_items(node):
    """Every {"Event": ...} dict under a node."""
    if isinstance(node, dict):
        if isinstance(node.get("Event"), str):
            yield node
        for v in node.values():
            yield from event_items(v)
    elif isinstance(node, list):
        for v in node:
            yield from event_items(v)


def split_event(e: str):
    m = EVENT_RE.match(e)
    return (m.group(1), m.group(2), m.group(3)) if m else ("", e, "")


PENDING = "pending-questions.md"


def _as_list(v):
    if undecided(v):
        return []
    return [x for x in (v if isinstance(v, list) else [v]) if not undecided(x)]


def _pending_done(folder: Path):
    p = folder / PENDING
    if p.exists():
        p.write_text("# Pending questions\n\nNone - every rename and external event is answered in "
                     f"`{INPUTS}`.\n", encoding="utf-8")


def write_pending(folder: Path, cfg: dict, res: Result, inv: list, cmp_: Path, q_ren: list, q_ext: dict, ctx: dict):
    """<folder>/pending-questions.md: one row per missing rename / external event, with who emits it, where, what it
    is and a suggested answer (skill explain-box-job). Suggestions only - the operator answers in the inputs file."""
    ref, tgt = cfg["reference"], cfg["target"]
    paths = [cmp_] + [resolve(folder, p) for p in _as_list(ref.get("controlm_other"))]
    for p in paths[1:]:
        if not p.exists():
            res.warn("controlm-other-missing", str(p), "not found - attach that repo for the emitter of an event")
    paths = [p for p in paths if p.exists()]
    dml_paths = [resolve(folder, p) for p in _as_list(ref.get("dml_repos"))]
    for p in dml_paths:
        if not p.exists():
            res.warn("dml-repo-missing", str(p), "not found - group names left out of pending-questions.md")
    cm_all = explain_job.load_controlm(paths)
    dml = explain_job.load_dml([p for p in dml_paths if p.exists()])
    mbj = explain_job.load_mbj(resolve(folder, ref["mbj_csv"]) if not undecided(ref.get("mbj_csv")) else None)
    emitters = defaultdict(set)
    for j, c in cm_all.items():
        for e in c["adds"]:
            emitters[split_event(e)[1]].add(j)
    approved = {ALIASES.get(str(x).lower(), str(x).lower()) for x in _as_list(tgt.get("instruments"))} | {ctx["prod"]}
    fams = {PRODUCTS[p][0]: p for p in approved if p in PRODUCTS}
    today = datetime.date.today().strftime("%Y%m%d")
    rtok, ttok = ctx["rtok"], ctx["ttok"]

    def card(job):
        i = explain_job.describe(job, inv, cm_all, dml, mbj)
        c = i["controlm"]
        where = f"`{c['folder']}` · `{c['repo']}/{c['file']}:{c['line']}`" if c else "not in the repos given"
        what = (c["obj"].get("Description", "") if c else "") or "-"
        if i["group"]:
            what += f" · group `{i['group']}` {i['group_name']}".rstrip()
        side = " · ".join(x for x in (i["family"], i["side"], i["product"], i["level"]) if x) or "-"
        when = c["obj"].get("When", {}) if c and isinstance(c["obj"].get("When"), dict) else {}
        ended = str(when.get("EndDate") or "") if str(when.get("EndDate") or "99991231") < today else ""
        return i, where, what.replace("|", "/"), side, ended

    out = [f"# Pending questions - {tgt.get('branch_code', '')} {ctx['prod']} (build_fe_jobs.py, "
           f"{datetime.date.today().isoformat()})", "",
           f"The build stopped: {len(q_ren) + len(q_ext)} answer(s) needed in `{INPUTS}`. Ask them **one at a time**; "
           "the suggestion is a proposal, the operator decides. For more on any job: skill `explain-box-job` "
           "(\"what does <JOB> do?\"), then come back to the question.", ""]
    if q_ren:
        out += ["## Renames (`renames`): old-named reference jobs the chain needs", "",
                "| Old job | What it is | Folder · repo:line | Side · product · level | Waited for by | Suggested answer |",
                "|---|---|---|---|---|---|"]
        for j in q_ren:
            i, where, what, side, _ = card(j)
            m = re.fullmatch(r"GMBOX\d{4}D(\d{2})", j)
            step = m.group(1) if m else "01"
            n = ctx["fam"] if ctx["fe_rows"].get(j, {}).get("instrument") == ctx["inst_const"] else "0"
            sug = f"GMBX{n}{ttok}00D{step}"
            if sug in ctx["taken"]:
                sug += " (taken - pick another D<ss>)"
            users = sorted(k for k, c in cm_all.items() if any(split_event(e)[1] == j for e in c["waits"]))
            out.append(f"| `{j}` | {what} | {where} | {side} | {', '.join(users) or '-'} | `{sug}` - branch level "
                       f"(book 00), {'this instrument' if n != '0' else 'generic'} |")
        out.append("")
    if q_ext:
        out += ["## External events (`external_events`): waited for, emitted by no job of the reference folder", "",
                "| Event | Waited for by | Emitted by | Folder · repo:line | What it is | Side · product · level | "
                "Suggested answer |", "|---|---|---|---|---|---|---|"]
        for e, who in q_ext.items():
            pre, job, suf = split_event(e)
            ems = sorted(emitters.get(job, ())) or ([job] if job in cm_all else [])
            if not ems:
                row = ("nobody in the repos given", "-", "-", "-",
                       "**ask the BOX team** which folder emits it (attach that repo as `reference.controlm_other` "
                       "and run again); `DROP` if it no longer exists")
            else:
                p = ems[0]
                i, where, what, side, ended = card(p)
                m = NEW_RE.fullmatch(p)
                if ended:
                    sug = f"`DROP` - its emitter ended (EndDate {ended})"
                elif p.startswith("GMGB") or i["family"] == "GBO":
                    sug = ("**ask the GBO team** for the target's GBO event of the same step (`KEEP` only if the "
                           "target waits for this same GBO job)")
                elif i["side"] == "ACC":
                    sug = ("`DROP` for now - ACC jobs are not built yet; later the target's ACC equivalent "
                           "(once its ACC folder exists)")
                elif m and m.group(2) == rtok:
                    n, _, b, s = m.groups()
                    if n in fams:
                        tb = b if b == "00" else "<book>"
                        sug = f"`{pre}GMBX{n}{ttok}{tb}D{s}{suf}` - {fams[n]} is approved for the target"
                    else:
                        sug = (f"`DROP` - {explain_job.INSTR_FAMILY.get(n, n)} is not approved for the target (add it to "
                               "`target.instruments` to map it instead)")
                elif m:
                    sug = "**ask the BOX team** - another branch's job; `KEEP` if the target shares it"
                else:
                    sug = "**ask the BOX team** - the target's equivalent of this old-named job, or `DROP`"
                more = f" (+{len(ems) - 1})" if len(ems) > 1 else ""
                row = (f"`{p}`{more}", where, what, side, sug)
            out.append(f"| `{e}` | {', '.join(sorted(who))} | " + " | ".join(row) + " |")
        out.append("")
    out += ["Answer format: `renames: {\"<old>\": \"<new>\"}`; `external_events: {\"<event>\": \"<target event>\" | "
            "\"KEEP\" | \"DROP\"}`. Then run the script again."]
    (folder / PENDING).write_text("\n".join(out) + "\n", encoding="utf-8")
    res.warn("pending-questions", str(folder / PENDING), f"{len(q_ren) + len(q_ext)} question(s) with suggestions")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or not Path(argv[0]).is_dir():
        print("usage: build_fe_jobs.py <runs/<BRANCH>/<env>/fe-jobs/<instrument>/>", file=sys.stderr)
        return 2
    folder = Path(argv[0])
    res = Result()
    rc = build(folder, res)
    print(f"\nbuild_fe_jobs - {folder}\n" + "=" * 72)
    for c, w, m in res.errors:
        print(f"  REFUSED {c:<28} {w}: {m}")
    for c, w, m in res.warns:
        print(f"  WARN    {c:<28} {w}: {m}")
    print(("  wrote out/ - see out/report.md" if rc in (0, 4) else "  nothing written") + "\n" + "=" * 72)
    return rc


def build(folder: Path, res: Result) -> int:
    ip = folder / INPUTS
    if not ip.exists():
        res.err("inputs-missing", INPUTS, "copy agents/box-fe-jobs-agent/templates/fe-jobs-inputs.example.json here "
                "and fill it - ask the operator for every <...>")
        return 1
    try:
        cfg = json.loads(ip.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        res.err("inputs-not-json", INPUTS, str(e))
        return 1
    for path, ask in REQUIRED.items():
        if undecided(get(cfg, path)):
            res.err("input-missing", f"{INPUTS}.{path}", f"ask the operator: {ask}")
    if res.errors:
        return 1
    ref, tgt, cm = cfg["reference"], cfg["target"], cfg["controlm"]
    prod = ALIASES.get(str(cfg["instrument"]).lower(), str(cfg["instrument"]).lower())
    if prod not in PRODUCTS:
        res.err("instrument-unknown", f"{INPUTS}.instrument", f"{cfg['instrument']!r} - one of {', '.join(PRODUCTS)}")
        return 1
    fam, inst_const = PRODUCTS[prod]
    rtok, ttok = ref["token"].upper(), tgt["token"].upper()
    if not re.fullmatch(r"[A-Z]{2}", ttok):
        res.err("target-token-bad", f"{INPUTS}.target.token", f"{ttok!r}: two letters (the label code without X/number)")
    if str(tgt["wrapper_args"]) not in ("5", "7"):
        res.err("wrapper-args-bad", f"{INPUTS}.target.wrapper_args", "5 (no label argument) or 7 (label, sub-label)")

    # --- reference inventory + db.conf --------------------------------------------------------------------
    envf = resolve(folder, ref["env_folder"])
    invp, dbp = envf / "jobs-inventory.csv", envf / "db.conf"
    if not invp.exists() or not dbp.exists():
        res.err("reference-confs-missing", str(envf), "jobs-inventory.csv and db.conf (run scripts/parse_job_confs.py)")
        return 1
    inv = list(csv.DictReader(invp.open(encoding="utf-8")))
    if inv and "executed" not in inv[0]:
        res.err("inventory-old", str(invp), "re-run scripts/parse_job_confs.py (2026-10-01 version)")
        return 1
    dblines = dbp.read_text(encoding="utf-8", errors="replace").splitlines()
    fe_rows = {r["job"]: r for r in inv if r["family"] == "BOX" and r["active"] == "Y" and r["executed"] == "Y"
               and r["file"] == "db.conf"}
    known_names = {r["job"] for r in inv}

    # --- reference Control-M folder ------------------------------------------------------------------------
    cmp_ = resolve(folder, ref["controlm_json"])
    if not cmp_.exists():
        res.err("controlm-missing", f"{INPUTS}.reference.controlm_json", f"{cmp_} not found - attach the reference "
                "branch's FE Control-M repo")
        return 1
    rname, rheader, rjobs, rjline = load_folder(cmp_)
    if not rjobs:
        res.err("controlm-not-folder", str(cmp_), "no SimpleFolder with Job:* entries")
        return 1
    today = datetime.date.today().strftime("%Y%m%d")
    expired = sorted(j for j, v in rjobs.items()
                     if isinstance(v.get("When"), dict) and str(v["When"].get("EndDate") or "99991231") < today)
    for j in expired:                                          # When.EndDate in the past: the job no longer runs
        rjobs.pop(j)
    producer = defaultdict(set)
    for j, v in rjobs.items():
        for it in event_items(v.get("eventsToAdd", {})):
            producer[split_event(it["Event"])[1]].add(j)       # producers keyed by the job part of the event

    def parts(j):
        m = NEW_RE.fullmatch(j)
        return m.groups() if m and m.group(2) == rtok else None

    # --- books ---------------------------------------------------------------------------------------------
    regp = resolve(folder, tgt["books_register"])
    rows_b = []
    if regp.exists():
        rows_b = list(csv.DictReader(regp.open(encoding="utf-8")))
    elif (regp.parent / "00-books.csv").exists():        # register not written yet: the book list, labels unchecked
        listp = regp.parent / "00-books.csv"
        rows_b = [{"kind": "book", "code": (r.get("label_code_proposed") or "").strip(),
                   "description": r.get("label_description") or "", "status": "not checked (no register yet)"}
                  for r in csv.DictReader(listp.open(encoding="utf-8-sig"))]
        res.warn("books-register-missing", str(regp), f"not written yet - using {listp.name}; run skill "
                 "set-up-book-labels (Q-10f) to check the labels exist")
        regp = listp
    else:
        res.err("books-missing", f"{INPUTS}.target.books_register", f"{regp} (or 00-books.csv beside it) - skill "
                "set-up-book-labels")
        return 1
    tbooks = []
    for r in rows_b:
        if r.get("kind") != "book":
            continue
        m = re.fullmatch(r"X([A-Z]{2,3})(\d{2})", r.get("code", ""))
        if not m:
            res.err("book-code-bad", str(regp), f"{r.get('code')!r}")
            continue
        if m.group(1) != ttok:
            res.err("book-token-mismatch", str(regp), f"{r['code']}: token {m.group(1)} is not target.token {ttok}")
        tbooks.append({"no": m.group(2), "code": r["code"], "desc": r.get("description", ""), "status": r.get("status", "")})
        if r.get("status") != "exists":
            res.warn("book-label-pending", str(regp), f"{r['code']} is {r.get('status')!r} in the target - the jobs "
                     "are written, but cannot run before the label exists")
    if not tbooks:
        res.err("books-missing", str(regp), "no book rows")
    rbp = resolve(folder, ref["books_csv"])
    rbooks = {}
    if not rbp.exists():
        res.err("reference-books-missing", f"{INPUTS}.reference.books_csv", f"{rbp} - J-R3b in the reference tier")
    else:
        for r in csv.DictReader(rbp.open(encoding="utf-8-sig")):
            m = re.fullmatch(r"X([A-Z]{2,3})(\d{2})", (r.get("CODE") or r.get("code") or "").strip())
            if m and m.group(1) == rtok:
                rbooks[m.group(2)] = (r.get("DESCRIPTION") or r.get("description") or "").strip()
    if res.errors:
        return 1

    # --- 1. seed --------------------------------------------------------------------------------------------
    def is_product(r):
        return r["instr_no"] == fam or r["instrument"] == inst_const

    cand = [j for j, r in fe_rows.items() if is_product(r) and (r["token"] == rtok or r["branch"] == ref["branch_const"])
            and j in rjobs]
    books_seen = sorted({parts(j)[2] for j in cand if parts(j) and parts(j)[2] not in ("00",)})
    tb = str(cfg.get("reference", {}).get("template_book") or "").strip()
    if undecided(tb):
        normal = [b for b in books_seen if b != "99"]
        tb = normal[0] if normal else (books_seen[0] if books_seen else "")
        res.warn("template-book-chosen", f"{INPUTS}.reference.template_book", f"none given - using book {tb} "
                 f"(reference books with this chain: {', '.join(books_seen) or 'none'})")
    seed = [j for j in cand if parts(j) and parts(j)[2] in (tb, "00")]
    old_product = sorted(j for j in cand if not parts(j))     # reported, not copied: they enter only as prerequisites
    if not seed:
        res.err("nothing-to-copy", "reference", f"no executed FE {prod} job of token {rtok} found in both "
                f"jobs-inventory.csv and {cmp_.name}")
        return 1

    # --- 2. closure over same-folder producers --------------------------------------------------------------
    include, external, stack = set(), defaultdict(set), list(seed)
    while stack:
        j = stack.pop()
        if j in include:
            continue
        include.add(j)
        for it in event_items(rjobs[j].get("eventsToWaitFor", {})):
            _, job, _ = split_event(it["Event"])
            ps = producer.get(job, set())
            if not ps:
                external[it["Event"]].add(j)
                continue
            for p in ps:
                pp = parts(p)
                if pp and pp[2] not in (tb, "00"):             # another reference book: its template-book twin
                    twin = f"GMBX{pp[0]}{rtok}{tb}D{pp[3]}"
                    if twin in rjobs:
                        stack.append(twin)
                    continue
                stack.append(p)

    # --- 3. names -------------------------------------------------------------------------------------------
    renames = {k: v for k, v in (cfg.get("renames") or {}).items() if not k.startswith("_")}
    level, targets = {}, {}
    for j in sorted(include):
        pp = parts(j)
        if pp:
            n, _, b, s = pp
            if b == tb:
                level[j] = "book"
                targets[j] = [f"GMBX{n}{ttok}{x['no']}D{s}" for x in tbooks]
            else:
                level[j] = "branch"
                targets[j] = [f"GMBX{n}{ttok}{b}D{s}"]
        else:
            level[j] = "branch"
            new = renames.get(j)
            if undecided(new):
                res.err("rename-missing", f"{INPUTS}.renames.{j}", f"{j} ({rjobs[j].get('Description', '')}) has an old "
                        f"name - ask the operator for the target's new-convention name (GMBX<n>{ttok}<nn>D<ss>)")
                continue
            if not NEW_RE.fullmatch(new) or NEW_RE.fullmatch(new).group(2) != ttok:
                res.err("rename-not-convention", f"{INPUTS}.renames.{j}", f"{new!r}: GMBX<n>{ttok}<nn>D<ss>")
            targets[j] = [new]
    for j, ts in targets.items():
        for t in ts:
            if t in known_names:
                res.err("target-name-exists", j, f"{t} already exists in the reference inventory")
            if len(t) > 20:
                res.err("target-name-too-long", j, f"{t}: JOB_NAME is VARCHAR2(20)")
    emap = {k: v for k, v in (cfg.get("external_events") or {}).items() if not k.startswith("_")}
    for e, who in sorted(external.items()):
        if undecided(emap.get(e)):
            res.err("external-event-unmapped", f"{INPUTS}.external_events.{e}", f"waited for by {', '.join(sorted(who))}; "
                    "no job of the reference folder emits it - ask the operator: the target's event, KEEP (the same "
                    "shared event), or DROP")
    if res.errors:
        q_ren = [j for j in sorted(include) if not parts(j) and undecided(renames.get(j))]
        q_ext = {e: who for e, who in sorted(external.items()) if undecided(emap.get(e))}
        if q_ren or q_ext:
            taken = {t for ts in targets.values() for t in ts} | known_names
            write_pending(folder, cfg, res, inv, cmp_, q_ren, q_ext, dict(
                rtok=rtok, ttok=ttok, fam=fam, inst_const=inst_const, prod=prod, fe_rows=fe_rows, taken=taken))
        return 1
    _pending_done(folder)

    def map_job_for_book(job: str, book_no: str | None) -> list[str]:
        """target job name(s) for a reference job referenced from a target job of book `book_no`."""
        if job in targets:
            ts = targets[job]
            if level[job] == "book" and book_no is not None:
                m = NEW_RE.fullmatch(ts[0])
                return [f"GMBX{m.group(1)}{ttok}{book_no}D{m.group(4)}"]
            return ts
        pp = parts(job)
        if pp and pp[2] != "00":                               # same step of another reference book
            n, _, _, s = pp
            if book_no is not None:
                return [f"GMBX{n}{ttok}{book_no}D{s}"]
            return [f"GMBX{n}{ttok}{x['no']}D{s}" for x in tbooks]
        return []

    def map_event(e: str, book_no: str | None) -> list[str]:
        pre, job, suf = split_event(e)
        if e in external:
            v = str(emap[e]).strip()
            return [] if v.upper() == "DROP" else ([e] if v.upper() == "KEEP" else [v])
        ts = map_job_for_book(job, book_no)
        return [f"{pre}{t}{suf}" for t in ts] if ts else [e]

    def remap_events(node, book_no):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if isinstance(v, list) and any(isinstance(x, dict) and "Event" in x for x in v):
                    out, seen = [], set()
                    for x in v:
                        if isinstance(x, dict) and isinstance(x.get("Event"), str):
                            for ne in map_event(x["Event"], book_no):
                                if ne not in seen:
                                    seen.add(ne)
                                    y = dict(x)
                                    y["Event"] = ne
                                    out.append(y)
                        else:
                            remap_events(x, book_no)
                            out.append(x)
                    node[k] = out
                else:
                    remap_events(v, book_no)
        elif isinstance(node, list):
            for v in node:
                remap_events(v, book_no)

    def describe(desc: str, ref_book: str | None, tbook: dict | None) -> tuple[str, bool]:
        ok = True
        if ref_book and tbook:
            rd = rbooks.get(ref_book)
            if rd and rd in desc:
                desc = desc.replace(rd, tbook["desc"])
            else:
                ok = False
        desc = re.sub(r"\b" + re.escape(ref["display"]) + r"\b", tgt["display"], desc)
        return desc, ok

    # --- the Control-M folder -------------------------------------------------------------------------------
    header = {"Type": "SimpleFolder"}
    for k in ("ControlmServer", "SiteStandard", "OrderMethod"):
        header[k] = cm[k]
    for k, v in rheader.items():
        if k not in header:
            header[k] = v
            res.warn("header-copied", f"{rname}.{k}", f"copied from the reference ({v!r}) - check it for the target")
    newfolder = dict(header)
    mapping, envspecific = [], ("Host", "RunAs", "Application", "FilePath")
    times = defaultdict(set)
    for j in sorted(include, key=lambda x: (rjline.get(x, 0), x)):
        book_list = [b for b in tbooks] if level[j] == "book" else [None]
        for tbk, t in zip(book_list, targets[j]):
            o = copy.deepcopy(rjobs[j])
            o["FileName"] = t
            for k in envspecific:
                if k in o:
                    o[k] = cm[k]
            if "CreatedBy" in o:
                if str(cm["CreatedBy"]).strip().lower() == "omit":
                    del o["CreatedBy"]
                else:
                    o["CreatedBy"] = cm["CreatedBy"]
            if isinstance(o.get("When"), dict) and "MonthDaysCalendar" in o["When"]:
                o["When"]["MonthDaysCalendar"] = cm["MonthDaysCalendar"]
            if isinstance(o.get("When"), dict):
                if "EndDate" in o["When"]:                     # a live reference job with an end date: not carried over
                    del o["When"]["EndDate"]
                    res.warn("end-date-dropped", t, f"{j} has a future EndDate - not copied")
                if o["When"].get("FromTime"):
                    times[o["When"]["FromTime"]].add(t)
            doc = {k: v for k, v in (cm.get("DocumentationFile") or {}).items() if not k.startswith("_")} \
                if isinstance(cm.get("DocumentationFile"), dict) else {}
            if doc:
                o["DocumentationFile"] = doc
            pp = parts(j)
            if "Description" in o:
                o["Description"], ok = describe(o["Description"], pp[2] if pp and level[j] == "book" else None, tbk)
                if not ok:
                    res.warn("description-not-renamed", t, f"the reference book's description is not in {j}'s "
                             "Description - check it")
            remap_events(o.get("eventsToWaitFor", {}), tbk["no"] if tbk else None)
            remap_events(o.get("eventsToAdd", {}), tbk["no"] if tbk else None)
            newfolder[t] = o
            shared = t.startswith("GMBX0") or not parts(j)     # generic per book / branch: shared by all instruments
            mapping.append({"reference_job": j, "reference_line": f"{cmp_.name}:{rjline.get(j, 0)}", "level": level[j],
                            "target_job": t, "target_book": tbk["code"] if tbk else "",
                            "shared_across_instruments": "yes" if shared else "", "db_conf": "", "status": ""})

    # --- 5. checks ------------------------------------------------------------------------------------------
    emitted = {split_event(it["Event"])[1] for v in newfolder.values() if isinstance(v, dict)
               for it in event_items(v.get("eventsToAdd", {}))}
    ext_ok = {e for e, v in emap.items() if not undecided(v)}
    graph = defaultdict(set)
    for t, o in newfolder.items():
        if not isinstance(o, dict):
            continue
        for it in event_items(o.get("eventsToWaitFor", {})):
            e = it["Event"]
            _, job, _ = split_event(e)
            if job in emitted:
                graph[t].add(job)
            elif not (e in ext_ok or any(str(v) == e for v in emap.values())):
                res.err("wait-unresolved", t, f"waits for {e}: no job of the new folder emits it and it is not a "
                        "mapped external event")
    seen, onstack = set(), set()

    def dfs(n):
        seen.add(n)
        onstack.add(n)
        for m in graph.get(n, ()):
            if m in onstack:
                res.err("chain-cycle", n, f"circular wait through {m}")
            elif m not in seen:
                dfs(m)
        onstack.discard(n)
    for n in list(graph):
        if n not in seen:
            dfs(n)

    # --- 4. db.conf -----------------------------------------------------------------------------------------
    cmap = {k.upper(): v for k, v in (tgt.get("constants") or {}).items() if not k.startswith("_")}
    open_lines, conf = 0, []
    for row in mapping:
        j, t = row["reference_job"], row["target_job"]
        r = fe_rows.get(j)
        if not r:
            row["db_conf"], row["status"] = "-", "no executed db.conf line in the reference (JSON only)"
            continue
        raw = dblines[int(r["line"]) - 1].strip()
        line = re.sub(r"^\s*" + re.escape(j) + r"\b", t, raw)
        line = re.sub(r"\b" + re.escape(ref["wrapper_owner"]) + r"\.", tgt["wrapper_owner"] + ".", line, flags=re.I)
        line = re.sub(r"\b" + re.escape(ref["branch_const"]) + r"\b", tgt["branch_const"], line, flags=re.I)
        for c in sorted({c.upper() for c in CONST_RE.findall(line)} - {tgt["branch_const"].upper()}):
            new = cmap.get(c)
            if isinstance(new, str) and new.strip().upper() == "SAME":
                continue
            if undecided(new):
                res.err("constant-unmapped", f"{INPUTS}.target.constants.{c}", f"{c} (in {j}) - its name in "
                        f"{tgt['wrapper_owner']}.PKG_GMBATCHPROCESS (J-E4 in the target)")
                continue
            line = re.sub(r"\b" + re.escape(c) + r"\b", new, line, flags=re.I)
        lab = LABEL_RE.search(line)
        if lab:
            tb_ = next((x for x in tbooks if x["code"] == row["target_book"]), None)
            if tb_ is None:
                res.err("label-without-book", t, f"{j} passes a label but is not a per-book job")
                continue
            line = LABEL_RE.sub(f"f_getPKByLabel('{tb_['code']}')", line)
        if lab and str(tgt["wrapper_args"]) == "5":
            conf.append(f"# OPEN checkpoint 3 - {tgt['wrapper_owner']}.f_ExecuteGroup takes no label: {line}")
            row["status"] = "OPEN - wrapper has no label argument"
            open_lines += 1
        else:
            conf.append(line)
            row["status"] = "ready"
        row["db_conf"] = f"db.conf:{r['line']}"
    if res.errors:
        return 1

    # --- write -----------------------------------------------------------------------------------------------
    od = folder / OUT
    od.mkdir(exist_ok=True)
    banner = f"########## BOX - {tgt['branch_code']} - FE - {prod} (from {rtok}, book {tb}) ##########"
    (od / "db.conf.proposal").write_text("\n".join([banner, *conf]) + "\n", encoding="utf-8")
    (od / f"{cm['folder_name']}.json").write_text(json.dumps({cm["folder_name"]: newfolder}, indent=2, ensure_ascii=False)
                                                  + "\n", encoding="utf-8")
    with (od / "mapping.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(mapping[0]))
        w.writeheader()
        w.writerows(mapping)
    hand = sorted({e for o in newfolder.values() if isinstance(o, dict) for it in event_items(o.get("eventsToAdd", {}))
                   for e in [it["Event"]] if re.match(r"G\d{6}-", e)})
    rep = [f"# BOX FE jobs - {tgt['branch_code']} - {prod}", "",
           f"From reference token `{rtok}` (template book `{tb}`, `{cmp_.name}`), {len(include)} reference jobs -> "
           f"**{len(mapping)} target jobs** for {len(tbooks)} books; db.conf lines: {len(conf)} "
           f"({open_lines} OPEN). Folder `{cm['folder_name']}`.", "",
           "| Level | Reference jobs | Target jobs |", "|---|---|---|"]
    for lv in ("branch", "book"):
        rj = sorted(j for j in include if level[j] == lv)
        rep.append(f"| {lv} | {len(rj)} | {sum(len(targets[j]) for j in rj)} |")
    nshared = sum(1 for m in mapping if m["shared_across_instruments"])
    rep += ["", f"**{nshared} job(s) are shared by every instrument** (`GMBX0…` per book, branch prerequisites — "
            "`shared_across_instruments` in mapping.csv): when another instrument is built, keep one copy of each."]
    rep += ["", "## Start times copied from the reference (check them for the target's time zone)", ""]
    rep += [f"- `FromTime {k}`: {', '.join(sorted(v))}" for k, v in sorted(times.items())] or ["- none"]
    if cm.get("host_config_repo"):
        rep += ["", f"**Host per environment** is applied by `{cm['host_config_repo']}` — the folder file carries "
                f"`{cm['Host']}`; add the target folder `{cm['folder_name']}` there for the other environments "
                f"({cm.get('host_by_env') or 'see the inputs'})."]
    rep += ["", "## Not copied", "", f"- reference jobs ended (`When.EndDate` in the past): {', '.join(expired) or 'none'}",
            "- reference books other than the template: "
            f"{', '.join(b for b in books_seen if b != tb) or 'none'} (an extra book like 99 is the operator's call)",
            f"- old-named {prod} jobs of the reference branch: {', '.join(old_product) or 'none'} (copied only when a "
            "copied job waits for them)"]
    rep += ["", "## External events (waited for, emitted by no job of the folder)", ""]
    rep += [f"- `{e}` -> `{emap[e]}` (waited by {', '.join(sorted(who))})" for e, who in sorted(external.items())] or ["- none"]
    rep += ["", "## Hand-offs - events other folders may wait for (G0100xx- prefix, as the reference emits)", ""]
    rep += [f"- `{e}`" for e in hand] or ["- none"]
    if open_lines:
        rep += ["", f"## OPEN - {open_lines} db.conf line(s) need the label argument",
                "", f"`{tgt['wrapper_owner']}.f_ExecuteGroup` takes {tgt['wrapper_args']} arguments; these lines are "
                "written commented. They wait on checkpoint 3 (BOX Lead)."]
    if res.warns:
        rep += ["", "## Warnings", ""] + [f"- `{c}` {w}: {m}" for c, w, m in res.warns]
    rep += ["", "Not done here: the Unix scripts `/appl/gm/scripts/<JOB>`, the repos, any deployment. A proposal "
            "for the BOX team."]
    (od / "report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    return 4 if open_lines else 0


if __name__ == "__main__":
    sys.exit(main())
