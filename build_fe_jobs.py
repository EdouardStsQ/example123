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
  <PREREQ_FOLDER>.json    each prerequisite folder (e.g. load prices), written first - it runs first
  descriptors/<folder>/<env>.json   the reference's per-environment descriptors, re-pointed to the target
  mapping.csv             every reference job -> every target job, with level, book, folder and where it came from
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
Prerequisite folders [2026-10-06] (inputs `prerequisites`): another Control-M folder whose jobs the chain waits for (e.g.
the load-prices folder) - the jobs the copied chain waits for, and theirs, are copied to the target's own folder first
(old names -> GMBX0<TT>00D01, D02... in chain order), their db.conf lines first. Environment descriptors (inputs
`reference.descriptor_dir`, `prerequisites[].descriptor_dir`: the environment config repo's <repo>/<env>.json,
`DeployDescriptor`) are read as waits too (the reference may add a dependency in PRO only) and re-pointed to the
target's folders and jobs into out/descriptors/<folder>/<env>.json; an entry carrying a reference environment value,
or only one reference book, is listed for review, never guessed.
BOX expert review fixes [2026-10-07]:
  - instrument scope: another instrument's job (GMBX<n>, n not this one's and not 0) is never copied; a wait on it is
    replaced by its own waits (inheritance), unless that instrument is built for the target (instrument-plan.csv
    status built / done: the wait is kept, renamed); OR-groups: empty groups and duplicates dropped;
  - every event is renamed, the If:CompletionStatus -> Event:Add ones (`-NOK`) too, and counts as emitted;
  - "ended" = a past When.EndDate that no descriptor deletes (a Delete of it re-enables the job: copied, no EndDate);
  - descriptors: every entry type (Property Replace / Assign, Add, Delete) per environment; per-environment values
    (Host, ControlmServer, OrderMethod, StartDate ...) from `controlm.env.<env file>`, Host never guessed; a Data Lake
    wait keeps its environment letter (PAUKI = PRO, IAUKI = PRE);
  - an old-named job's suggested name follows the reference's new-named siblings of the same group; KEEP of the
    reference branch's own job's event is refused;
  - `target.dbconf_format: pgt_prg` writes every group line as the core call PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup
    (T:P, 8 arguments) as Mexico's db.conf with the BOX job expert's corrections: branch PK on every line, CST_PK_VACIO
    -> NULL, P_TIME = to_char(sysdate,'RRRR-mm-DD HH24:MI:SS') - the label fits, no OPEN line;
  - a GBO wait's target look-alike is ranked by function name, then first argument by value (`constant_values`).
[2026-10-08] `instrument` may be a LIST: every instrument in one run (each built as above into out/parts/<instrument>/,
knowing the others are built - their waits on each other kept), merged into one set of outputs (a shared job once).
`initial_accounting.group` (2409.65): per instrument the reference's Initial Accounting job (defined in the ACC folder,
run from db.conf) gets its db.conf core line here, the FE waits on it are re-wired with no question, and it is handed
to box-acc-jobs-agent in out/acc-handoff.json (with a draft ACC job when reference.controlm_other has it).
OrderMethod is never copied from the reference (time zone). out/unix/job_unix.sh (scripts/unix_package.py): the Unix
deployment of the db.conf lines - add_new_jobs.ksh, then cp db_job + chmod 755 per job.
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
import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from find_jobs import ALIASES, PRODUCTS  # noqa: E402
from parse_job_confs import split_args  # noqa: E402
import explain_job  # noqa: E402  (skill explain-box-job: who emits an event, what a job is)
import unix_package  # noqa: E402  (job_unix.sh: the Unix deployment of the db.conf lines)

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


def added_events(o) -> list:
    """Every event a job emits: eventsToAdd and the Event:Add of its If blocks (e.g. `IfBase:Folder:CompletionStatus_0`
    NOTOK -> `<JOB>-NOK`) [read: cib-boxfin-t1mdslbfe.json GMBX7LB15D11, 2026-10-07]."""
    out = [it["Event"] for it in event_items(o.get("eventsToAdd", {}))] if isinstance(o, dict) else []

    def walk(n):
        if isinstance(n, dict):
            if n.get("Type") == "Event:Add" and isinstance(n.get("Event"), str):
                out.append(n["Event"])
            for k, v in n.items():
                if k not in ("eventsToWaitFor", "eventsToAdd"):
                    walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(o)
    return out


def delete_paths(e) -> list:
    """The paths a descriptor `Delete` entry removes (a string, {Path}, or a list of them)."""
    d = e.get("Delete") if isinstance(e, dict) else None
    if isinstance(d, str):
        return [d]
    if isinstance(d, dict):
        return [str(d["Path"])] if d.get("Path") else [x for x in d.values() if isinstance(x, str) and x.startswith("$.")]
    if isinstance(d, list):
        return [x if isinstance(x, str) else str(x.get("Path", "")) for x in d if isinstance(x, (str, dict))]
    if d and isinstance(e.get("Path"), str):
        return [e["Path"]]
    return []


def replace_strings(node, old: str, new: str):
    """Deep copy of node with every string equal to `old` replaced by `new`."""
    if isinstance(node, dict):
        return {k: replace_strings(v, old, new) for k, v in node.items()}
    if isinstance(node, list):
        return [replace_strings(v, old, new) for v in node]
    return new if node == old else node


PENDING = "pending-questions.md"


def _as_list(v):
    if undecided(v):
        return []
    return [x for x in (v if isinstance(v, list) else [v]) if not undecided(x)]


def load_descriptors(d: Path) -> dict:
    """{env file: [DeployDescriptor entries]} of an environment descriptor folder (e.g. cib-auki-aukicnfgsrvc/<repo>/
    pro.json): per-environment changes applied to a Control-M folder at deployment."""
    out = {}
    for f in sorted(d.glob("*.json")) if d.is_dir() else ([d] if d.exists() else []):
        try:
            root = json.loads(f.read_text(encoding="utf-8-sig", errors="replace"))
        except json.JSONDecodeError:
            continue
        if isinstance(root, dict) and isinstance(root.get("DeployDescriptor"), list):
            out[f.name] = root["DeployDescriptor"]
    return out


DL_RE = re.compile(r"^[PI]AUKI(?:SCIB)?(DD|FD|MD)(.*?)(OTCSQL|OTC|SQL)?\d{3}D$")
BUILT = {"built", "done", "deployed", "in box", "merged"}
NEVER_COPIED = ("Host", "OrderMethod")   # per-environment descriptor values never taken from the reference
TIME_ARG = "to_char(sysdate,'RRRR-mm-DD HH24:MI:SS')"   # P_TIME of the core call [BOX job expert via operator, 2026-10-07]     # instrument-plan.csv statuses of an instrument already built


def dl_key(job: str) -> str:
    """A Data Lake job name in its PRO spelling: the environment letter is the first one (P = PRO, I = PRE:
    `IAUKISCIB...` in a pre.json is `PAUKISCIB...` in pro.json) [read: SLB descriptors, 2026-10-07]."""
    return "P" + job[1:] if job.startswith("IAUKI") else job


def dl_spell(target_job: str, like: str) -> str:
    """The target Data Lake job in the environment letter of the reference event it replaces."""
    return like[0] + target_job[1:] if like[:1] in ("P", "I") and target_job[:1] in ("P", "I") else target_job
BOOK_VR_RE = re.compile(r'book_vr[\\"\s]*:[\\"\s]*([^\\"]+)')


def norm_book(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


def load_datalake(paths) -> dict:
    """Data Lake (AUKI) Control-M jobs: job -> {book (book_vr), key (DD|FD|MD, variant), file, line} - one job per
    book and data type: deal data (base, OTC, SQL, OTCSQL), flow data, market data (control-m-batch-layer.md)."""
    out = {}
    for p in paths:
        p = Path(p)
        for f in (sorted(p.rglob("*.json")) if p.is_dir() else [p]):
            try:
                text = f.read_text(encoding="utf-8-sig", errors="replace")
                root = json.loads(text)
            except (OSError, json.JSONDecodeError):
                continue
            stack = [root]
            while stack:
                node = stack.pop()
                if not isinstance(node, dict):
                    continue
                for k, v in node.items():
                    if not isinstance(v, dict):
                        continue
                    m = DL_RE.match(k)
                    if m and str(v.get("Type", "")).startswith("Job"):
                        b = BOOK_VR_RE.search(json.dumps(v.get("Arguments", []), ensure_ascii=False).replace("\\\\", "\\"))
                        if b:
                            mm = re.search(r'"' + re.escape(k) + r'"\s*:', text)
                            out[k] = {"book": b.group(1).strip(), "key": (m.group(1), m.group(3) or ""),
                                      "file": f.name, "line": text.count("\n", 0, mm.start()) + 1 if mm else 0}
                    else:
                        stack.append(v)
    return out


def descriptor_waits(descs: dict, folder_name: str) -> dict:
    """job -> [(env file, event)] the descriptors add to its eventsToWaitFor."""
    out, pre = defaultdict(list), f"$.{folder_name}."
    for env, entries in descs.items():
        for e in entries:
            add = e.get("Add") if isinstance(e, dict) else None
            if isinstance(add, dict) and add.get("propertyName") == "eventsToWaitFor" \
                    and str(add.get("Path", "")).startswith(pre):
                for it in event_items(add.get("propertyValue", {})):
                    out[str(add["Path"])[len(pre):]].append((env, it["Event"]))
    return out


def _pending_done(folder: Path):
    p = folder / PENDING
    if p.exists():
        p.write_text("# Pending questions\n\nNone - every rename and external event is answered in "
                     f"`{INPUTS}`.\n", encoding="utf-8")


def next_free(n: str, tok: str, step: str, taken: set) -> str:
    k = int(step) if step.isdigit() else 1
    while f"GMBX{n}{tok}00D{k:02d}" in taken and k < 99:
        k += 1
    return f"GMBX{n}{tok}00D{k:02d}"


def write_pending(folder: Path, cfg: dict, res: Result, inv: list, cmp_: Path, q_ren: list, q_ext: dict, ctx: dict,
                  q_dup: list = (), q_dl: list = ()):
    """<folder>/pending-questions.md: one row per missing rename / external event, with who emits it, where, what it
    is and a suggested answer (skill explain-box-job). Suggestions only - the operator answers in the inputs file."""
    ref, tgt = cfg["reference"], cfg["target"]
    paths = [cmp_, *ctx.get("prereq_paths", [])] + [resolve(folder, p) for p in _as_list(ref.get("controlm_other"))]
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
    tinv = []                                                  # the target environment's own jobs (its job confs)
    if not undecided(tgt.get("env_folder")):
        tp = resolve(folder, tgt["env_folder"]) / "jobs-inventory.csv"
        if tp.exists():
            tinv = [r for r in csv.DictReader(tp.open(encoding="utf-8")) if r.get("active") == "Y" and r.get("entry")]
        else:
            res.warn("target-inventory-missing", str(tp), "run scripts/parse_job_confs.py on the target's job confs")

    rvals = {k.upper(): str(v) for k, v in (ref.get("constant_values") or {}).items() if not k.startswith("_")}
    tvals = {k.upper(): str(v) for k, v in (tgt.get("constant_values") or {}).items() if not k.startswith("_")}

    def argvals(row, vals):
        """The call's arguments without dates, constants as their values (inputs `constant_values`, query J-E4)."""
        a = [x.strip() for x in (row.get("params") or "").split(" | ") if x.strip()]
        return [vals.get(x.upper(), x) for x in a if not re.search(r"to_date|odate|f_get", x, re.I)]

    rconst = explain_job.load_constants([resolve(folder, ref["env_folder"])])
    tconst = explain_job.load_constants([resolve(folder, tgt["env_folder"])]) if not undecided(tgt.get("env_folder")) else {}
    rconst.update({k: v for k, v in rvals.items()})
    tconst.update({k: v for k, v in tvals.items()})

    def equivalents(job):
        """The target's look-alikes of a reference (GBO / non-BOX) job - skill explain-box-job's matcher: same group
        (constants resolved, J-E4b), same script, same function + first argument [2026-10-08]."""
        r = next((x for x in inv if x["job"] == job and x.get("active") == "Y" and x.get("entry")), None)
        if not r or not tinv:
            return r, [], False
        top, sure = explain_job.lookalikes(r, tinv, rconst, tconst)
        return r, top, sure

    def gbo_suggestion(job):
        r, cands, sure = equivalents(job)
        runs = f"runs `{explain_job.call_of(r)}`" if r else "not in the reference job confs"
        if r and r.get("group"):
            runs += f" (group {explain_job._resolve(r['group'], rconst)})"
        c = "; ".join(f"`{x['job']}` runs `{explain_job.call_of(x)}` - {why} (score {sc})" for sc, x, why in cands)
        if cands and sure:
            return runs, (f"**candidate(s) in the target** (INFERRED): {c} — confirm with the GBO team; its event is "
                          "in the target's GBO Control-M folder (likely `<JOB>-OK`)")
        hint = "" if tinv else " (attach the target's job confs as `target.env_folder` to find candidates)"
        weak = f" Closest, **not** a match: {c}." if cands else ""
        return runs, ("**no confident match in the target** — ask the GBO team for the target's job doing the same "
                      f"(`KEEP` only if the target waits for this same GBO job; `DROP-REVIEW` to drop it and list it)"
                      f"{hint}.{weak}")
    approved = {ALIASES.get(str(x).lower(), str(x).lower()) for x in _as_list(tgt.get("instruments"))} | {ctx["prod"]}
    fams = {PRODUCTS[p][0]: p for p in approved if p in PRODUCTS}
    today = datetime.date.today().strftime("%Y%m%d")
    rtok, ttok = ctx["rtok"], ctx["ttok"]

    def sibling(job):
        """The reference branch's new-named branch-level jobs running the same group as an old-named job (e.g.
        GMBOX0114D01 ~ GMBX3LB00D01, group 2608.65 'Create Process Queues by Book') -> the target name in the same
        step; this instrument's family if the siblings are product jobs, else 0 [BOX expert review, 2026-10-07]."""
        g = next((x.get("group") for x in inv if x["job"] == job and x.get("group")), "")
        if not g:
            g = explain_job.describe(job, inv, cm_all, dml, mbj).get("group") or ""
        if not g:
            return None, [], ""
        sibs = sorted({x["job"]: x for x in inv if x.get("naming") == "new" and x.get("token") == rtok
                       and x.get("book_no") == "00" and x.get("group") == g and x.get("active") == "Y"}.values(),
                      key=lambda x: x["job"])
        if not sibs:
            return None, [], g
        step = Counter(x["step"][1:] for x in sibs).most_common(1)[0][0]
        n = ctx["fam"] if any(x.get("instr_no") not in ("0", "") for x in sibs) else "0"
        return f"GMBX{n}{ttok}00D{step}", [x["job"] for x in sibs], g

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
           f"The build stopped: {len(q_ren) + len(q_ext) + len(q_dup) + len(q_dl)} answer(s) needed in `{INPUTS}`. Ask them **one at a time**; "
           "the suggestion is a proposal, the operator decides. For more on any job: skill `explain-box-job` "
           "(\"what does <JOB> do?\"), then come back to the question.", ""]
    if q_dup:
        out += ["## Name conflicts (`renames`): one name per job — the job name is also its script name", "",
                "| Name | Given to | Suggested answer |", "|---|---|---|"]
        for name, jobs, sug in q_dup:
            out.append(f"| `{name}` | {', '.join(f'`{j}`' for j in jobs)} | {sug} |")
        out.append("")
    if q_dl:
        out += ["## Data Lake books (`datalake.book_map`): each target book waits for its own Data Lake job", "",
                "The link is the book label description = the Data Lake `book_vr`; these target books have no Data Lake "
                "job of that type under their description.", "",
                "| Target book | Description | Needs (type, variant) | For event | Closest Data Lake books | Answer |",
                "|---|---|---|---|---|---|"]
        for code, desc, key, ev, cands in q_dl:
            out.append(f"| `{code}` | {desc} | {key[0]} {key[1] or 'base'} | `{ev}` | "
                       f"{', '.join(f'`{c}`' for c in cands) or '-'} | the `book_vr` to use, or `DROP` |")
        out.append("")
    if q_ren:
        out += ["## Renames (`renames`): old-named reference jobs the chain needs", "",
                "| Old job | What it is | Folder · repo:line | Side · product · level | Waited for by | Suggested answer |",
                "|---|---|---|---|---|---|"]
        for j in q_ren:
            i, where, what, side, _ = card(j)
            m = re.fullmatch(r"GMBOX\d{4}D(\d{2})", j)
            step = m.group(1) if m else "01"
            n = ctx["fam"] if ctx["fe_rows"].get(j, {}).get("instrument") == ctx["inst_const"] else "0"
            sib, sibs, g = sibling(j)
            users = sorted(k for k, c in cm_all.items() if any(split_event(e)[1] == j for e in c["waits"]))
            if sib and sib not in ctx["taken"]:
                txt = (f"`{sib}` - same group `{g}` as the reference's {', '.join(f'`{x}`' for x in sibs)} (branch level, "
                       f"{'this instrument' if sib[4] != '0' else 'generic'})")
            else:
                sug = next_free(n, ttok, step, ctx["taken"])
                txt = f"`{sug}` - branch level (book 00), {'this instrument' if n != '0' else 'generic'}"
            out.append(f"| `{j}` | {what} | {where} | {side} | {', '.join(users) or '-'} | {txt} |")
        out.append("")
    if q_ext:
        out += ["## External events (`external_events`): waited for, emitted by no job of the reference folder", "",
                "| Event | Waited for by | Emitted by | Folder · repo:line | What it is | Side · product · level | "
                "Suggested answer |", "|---|---|---|---|---|---|---|"]
        for e, who in q_ext.items():
            pre, job, suf = split_event(e)
            ems = sorted(emitters.get(job, ())) or ([job] if job in cm_all else [])
            if not ems and job.startswith("GMGB"):
                runs, sug = gbo_suggestion(job)
                row = ("a GBO job (not in the Control-M repos given)", "-", runs, "GBO", sug)
            elif not ems and DL_RE.match(job):
                row = ("a Data Lake job (not in the repos given)", "-", "-", "Data Lake",
                       "per book: attach the Data Lake Control-M JSONs as `datalake.reference_json` / `target_json` "
                       "(a branch-level job waiting for one book's Data Lake job: **ask the BOX team**)")
            elif not ems:
                row = ("nobody in the repos given", "-", "-", "-",
                       "**ask the BOX team** which folder emits it (attach that repo as `reference.controlm_other` "
                       "and run again); `DROP` if it no longer exists")
            else:
                p = ems[0]
                i, where, what, side, ended = card(p)
                m = NEW_RE.fullmatch(p)
                sib = sibling(p) if not m and not p.startswith("GMGB") else (None, [], "")
                if ended:
                    sug = f"`DROP` - its emitter ended (EndDate {ended})"
                elif p.startswith("GMGB") or i["family"] == "GBO":
                    runs, sug = gbo_suggestion(p)
                    what = f"{what} · {runs}"
                elif sib[0]:
                    sug = (f"`{pre}{sib[0]}{suf}` - the target's job of the same group `{sib[2]}` as the reference's "
                           f"{', '.join(f'`{x}`' for x in sib[1])}"
                           + ("; it is an ACC job: `DROP` until the target's ACC folder has it" if i["side"] == "ACC"
                              else "") + " - never `KEEP` (the reference branch's own job)")
                elif i["side"] == "ACC":
                    sug = ("`DROP` for now - ACC jobs are not built yet; later the target's ACC equivalent "
                           "(once its ACC folder exists) - never `KEEP` (the reference branch's own job)")
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
    out += ["Answer format: `datalake.book_map: {\"<target book code>\": \"<book_vr>\" | \"DROP\"}`; "
            "`renames: {\"<old>\": \"<new>\"}`; `external_events: {\"<event>\": \"<target event>\" | "
            "\"KEEP\" | \"DROP\" | \"DROP-REVIEW\"}` (DROP-REVIEW = dropped and listed in the report as a decision "
            "to review). Then run the script again."]
    pf = ctx.get("pend") or folder
    (pf / PENDING).write_text("\n".join(out) + "\n", encoding="utf-8")
    res.warn("pending-questions", str(pf / PENDING), f"{len(q_ren) + len(q_ext) + len(q_dup) + len(q_dl)} question(s) with "
             "suggestions")


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
    if isinstance(cfg.get("instrument"), list):                # several instruments in one run [2026-10-08]
        rc = build_multi(folder, res, cfg)
    else:
        rc = build_one(folder, res, cfg)
    if rc in (0, 4):
        write_unix(folder, cfg, folder / OUT, res)
    return rc


def write_unix(folder: Path, cfg: dict, od: Path, res: Result):
    """out/unix/: job_unix.sh, db_nuevo.conf, db_delete.txt and the target's delete_jobsBX.ksh / add_new_jobs.ksh
    (scripts/unix_package.py) [BOX job expert, 2026-10-08 / 2026-10-09]."""
    ux = cfg.get("unix") if isinstance(cfg.get("unix"), dict) else {}
    scripts_dir = cfg["controlm"]["FilePath"] if undecided(ux.get("scripts_dir")) else str(ux["scripts_dir"])
    templates = None if undecided(ux.get("templates_dir")) else str(ux["templates_dir"])
    etc = None if undecided(ux.get("etc_dir")) else str(ux["etc_dir"])
    ref_unix = resolve(folder, ux["reference_unix_dir"]) if not undecided(ux.get("reference_unix_dir")) \
        else resolve(folder, cfg["reference"]["env_folder"]) / "unix"
    ref_etc = "/appl/gm/etc" if undecided(ux.get("reference_etc_dir")) else str(ux["reference_etc_dir"])
    r = unix_package.write(od / "unix", od / "db.conf.proposal", None, scripts_dir, templates, etc, ref_unix, ref_etc)
    if not etc:
        res.warn("unix-etc-missing", f"{INPUTS}.unix.etc_dir", "the target's etc folder - the sh lines of "
                 "job_unix.sh are written commented OPEN")
    for m in r["missing"]:
        res.warn("unix-script-missing", m, f"not in {ref_unix} - the target's copy is not in the package (the BOX "
                 "team provides it, or add the reference script there and run again)")
    for n in r["notes"]:
        res.warn("unix-note", "db_delete.txt", n)
    rp = od / "report.md"
    if rp.exists():
        e = etc or "<etc>"
        with rp.open("a", encoding="utf-8") as f:
            f.write(f"\n## Unix package - `unix/` (copy its files to `{e}`)\n\n"
                    f"- `job_unix.sh`: `delete_jobsBX.ksh db.conf db_delete.txt` (removes our jobs' lines if present - "
                    f"nothing the first time), `add_new_jobs.ksh db.conf db_nuevo.conf`, then for each of the "
                    f"{r['db']} jobs `cp …/db_job {scripts_dir.rstrip('/')}/<JOB>` and `chmod 755`"
                    f"{'' if etc else ' - **etc folder OPEN**'}\n"
                    "- `db_nuevo.conf` = this `db.conf.proposal`; `db_delete.txt` = its jobs and banners\n"
                    f"- target copies of the reference scripts: "
                    f"{', '.join(n for n in unix_package.SCRIPTS if n not in r['missing']) or 'none'}"
                    + (f"; **missing**: {', '.join(r['missing'])}" if r["missing"] else "") + "\n")


def _merge_events_ok(fd: dict, ia: set, ttok: str) -> list:
    """Waits on the target's own job names that no merged folder job emits (nor an Initial Accounting job)."""
    emitted = {split_event(e)[1] for f_ in fd.values() for v in f_.values() if isinstance(v, dict)
               for e in added_events(v)}
    bad = []
    for f_ in fd.values():
        for t, o in f_.items():
            if not isinstance(o, dict):
                continue
            for it in event_items(o.get("eventsToWaitFor", {})):
                jb = split_event(it["Event"])[1]
                m = NEW_RE.fullmatch(jb)
                if m and m.group(2) == ttok and jb not in emitted and jb not in ia:
                    bad.append((t, it["Event"]))
    return bad


def build_multi(folder: Path, res: Result, cfg: dict) -> int:
    """Several instruments in one run [operator, 2026-10-08]: each built as in a one-instrument run (its own
    reference template book: `reference.template_book` may be {instrument: book}) knowing the others are built
    too, into out/parts/<instrument>/; then merged into ONE set of outputs - each job once (a shared job built by
    two instruments must be the same), descriptors and db.conf lines de-duplicated, one hand-off, one report."""
    prods = []
    for x in cfg["instrument"]:
        p = ALIASES.get(str(x).lower(), str(x).lower())
        if p not in PRODUCTS:
            res.err("instrument-unknown", f"{INPUTS}.instrument", f"{x!r} - one of {', '.join(PRODUCTS)}")
        elif p not in prods:
            prods.append(p)
    if res.errors or not prods:
        return 1
    od = folder / OUT
    rcs, parts = {}, {}
    tbs = cfg["reference"].get("template_book")
    for p in prods:
        c = copy.deepcopy(cfg)
        c["instrument"] = p
        if isinstance(tbs, dict):
            c["reference"]["template_book"] = tbs.get(p, "")
        r = Result()
        pd = od / "parts" / p
        if pd.exists():
            for f in sorted(pd.rglob("*"), reverse=True):
                f.unlink() if f.is_file() else f.rmdir()
        rcs[p] = build_one(folder, r, c, od=pd, pend=pd, run_products=tuple(prods))
        parts[p] = pd
        res.errors += [(code, f"[{p}] {w}", m) for code, w, m in r.errors]
        res.warns += [(code, f"[{p}] {w}", m) for code, w, m in r.warns]
    pq = [(p, parts[p] / PENDING) for p in prods if (parts[p] / PENDING).exists()
          and not (parts[p] / PENDING).read_text(encoding="utf-8").startswith("# Pending questions\n\nNone")]
    if pq:
        (folder / PENDING).write_text("# Pending questions - every instrument of the run\n\n" + "\n".join(
            f"<!-- {p} -->\n" + f.read_text(encoding="utf-8").replace("\n# ", "\n## ", 1).replace("# Pending", "## Pending", 1)
            for p, f in pq), encoding="utf-8")
    else:
        _pending_done(folder)
    if any(v == 1 for v in rcs.values()):
        return 1
    # --- merge -------------------------------------------------------------------------------------------------
    names = [cfg["controlm"]["folder_name"], *[x.get("folder_name") for x in (cfg.get("prerequisites") or [])
                                                if isinstance(x, dict)]]
    fd = {}
    for n in names:
        for p in prods:
            f = parts[p] / f"{n}.json"
            if not f.exists():
                continue
            src = json.loads(f.read_text(encoding="utf-8"))[n]
            dst = fd.setdefault(n, {k: v for k, v in src.items() if not isinstance(v, dict)})
            for k, v in src.items():
                if not isinstance(v, dict):
                    continue
                if k in dst and dst[k] != v:
                    res.warn("merge-differs", k, f"built differently by {p} - the first instrument's kept; check it")
                dst.setdefault(k, v)
    for n, f_ in fd.items():
        (od / f"{n}.json").write_text(json.dumps({n: f_}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ia = set()
    hand = []
    for p in prods:
        hf = parts[p] / "acc-handoff.json"
        if hf.exists():
            for h in json.loads(hf.read_text(encoding="utf-8"))["initial_accounting"]:
                if h["target_job"] not in ia:
                    ia.add(h["target_job"])
                    hand.append(h)
    if hand:
        all_jobs = [kv for f_ in fd.values() for kv in f_.items() if isinstance(kv[1], dict)]
        for h in hand:                                         # waited-by over the merged folders
            h["waited_by"] = sorted(k for k, o in all_jobs for it in event_items(o.get("eventsToWaitFor", {}))
                                    if split_event(it["Event"])[1] == h["target_job"])
        (od / "acc-handoff.json").write_text(json.dumps({"for": "box-acc-jobs-agent", "branch": cfg["target"]["branch_code"],
                                                         "initial_accounting": hand}, indent=2, ensure_ascii=False)
                                             + "\n", encoding="utf-8")
    for t, e in _merge_events_ok(fd, ia, cfg["target"]["token"].upper()):
        res.err("wait-unresolved", t, f"waits for {e}: no job of the merged folders emits it")
    dd = {}
    for p in prods:
        for f in sorted((parts[p] / "descriptors").glob("*/*.json")) if (parts[p] / "descriptors").exists() else []:
            lst = dd.setdefault((f.parent.name, f.name), [])
            seen = {json.dumps(x, sort_keys=True) for x in lst}
            for x in json.loads(f.read_text(encoding="utf-8"))["DeployDescriptor"]:
                k = json.dumps(x, sort_keys=True)
                if k not in seen:
                    seen.add(k)
                    lst.append(x)
    for (fn, env), lst in dd.items():
        (od / "descriptors" / fn).mkdir(parents=True, exist_ok=True)
        (od / "descriptors" / fn / env).write_text(json.dumps({"DeployDescriptor": lst}, indent=4, ensure_ascii=False)
                                                  + "\n", encoding="utf-8")
    blocks, seen_jobs, order = {}, set(), []
    for p in prods:
        cur = None
        for line in (parts[p] / "db.conf.proposal").read_text(encoding="utf-8").splitlines():
            if line.startswith("##########"):
                cur = line
                if cur not in blocks:
                    blocks[cur] = []
                    order.append(cur)
                continue
            m = re.match(r"^#?\s*([A-Z][A-Z0-9_]{3,})\s*:", line)
            if m and m.group(1) in seen_jobs:
                continue
            if m:
                seen_jobs.add(m.group(1))
            blocks.setdefault(cur, []).append(line)
    pre_ = [b for b in order if " - FE - " not in b and "Initial accounting" not in b]
    ia_b = [b for b in order if "Initial accounting" in b]
    fe_b = [b for b in order if " - FE - " in b]
    out_lines = [x for b in [*pre_, *ia_b, *fe_b] if blocks[b] for x in [b, *blocks[b]]]
    (od / "db.conf.proposal").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    rows, keys = [], set()
    for p in prods:
        for r in csv.DictReader((parts[p] / "mapping.csv").open(encoding="utf-8")):
            k = (r["reference_job"], r["target_job"])
            if k not in keys:
                keys.add(k)
                rows.append(dict(r, instrument=p))
    with (od / "mapping.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    njobs = sum(1 for f_ in fd.values() for v in f_.values() if isinstance(v, dict))
    rep = [f"# BOX FE jobs - {cfg['target']['branch_code']} - {', '.join(prods)} (one run)", "",
           f"**{njobs} jobs** in {len(fd)} folder(s) ({', '.join(f'`{n}`' for n in fd)}); db.conf lines: "
           f"{len(seen_jobs)}; Initial Accounting jobs handed to box-acc-jobs-agent: {len(hand)}. Each instrument's "
           "detail follows (and `parts/<instrument>/`); a shared job is written once.", ""]
    if res.warns:
        rep += ["## Warnings (all instruments)", ""] + [f"- `{c}` {w}: {m}" for c, w, m in res.warns] + [""]
    for p in prods:
        txt = (parts[p] / "report.md").read_text(encoding="utf-8")
        rep += [re.sub(r"(?m)^(#+) ", lambda m_: "#" + m_.group(1) + " ", txt).rstrip(), ""]
    (od / "report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    if res.errors:
        return 1
    return 4 if any(v == 4 for v in rcs.values()) else 0


def build_one(folder: Path, res: Result, cfg: dict, od: Path | None = None, pend: Path | None = None,
              run_products: tuple = ()) -> int:
    """One instrument. `od` = where out/ goes, `pend` = where pending-questions.md goes, `run_products` = the
    instruments built in the same run (their waits on each other are kept)."""
    od = od or folder / OUT
    pend = pend or folder
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

    def ended_in_base(jobs_):
        return sorted(j for j, v in jobs_.items()
                      if isinstance(v.get("When"), dict) and str(v["When"].get("EndDate") or "99991231") < today)

    def reenabled(descs, fname, jobs_):
        """Jobs ended in the folder file whose EndDate a descriptor deletes: they run in that environment."""
        out = defaultdict(set)
        for env, entries in descs.items():
            for e in entries:
                for pth in delete_paths(e):
                    m = re.fullmatch(re.escape(f"$.{fname}.") + r"([^.]+)\.When\.EndDate", pth)
                    if m and m.group(1) in jobs_:
                        out[m.group(1)].add(env)
        return out

    def parts(j):
        m = NEW_RE.fullmatch(j)
        return m.groups() if m and m.group(2) == rtok else None

    # --- prerequisite folders (e.g. load prices) and environment descriptors [2026-10-06] ------------------
    # A prerequisite folder holds jobs the FE chain waits for from another Control-M folder / repo; its jobs that the
    # copied chain waits for (in the folder JSON or in a descriptor) are copied to their own target folder.
    rdesc = {}
    if not undecided(ref.get("descriptor_dir")):
        dp = resolve(folder, ref["descriptor_dir"])
        if not dp.exists():
            res.err("descriptor-missing", f"{INPUTS}.reference.descriptor_dir", f"{dp} not found - attach the "
                    "environment config repo (read-only) or remove the key")
        rdesc = load_descriptors(dp)
    prereqs, pproducer, rre_p = [], defaultdict(set), {}
    plist = cfg.get("prerequisites") or []
    for i, pc in enumerate(plist if isinstance(plist, list) else []):
        if not isinstance(pc, dict):
            continue
        w = f"{INPUTS}.prerequisites[{i}]"
        if undecided(pc.get("controlm_json")):
            res.err("input-missing", f"{w}.controlm_json", "ask the operator: the reference's prerequisite folder JSON "
                    "(e.g. the load-prices repo's projects/<repo>.json), or remove the entry")
            continue
        pth = resolve(folder, pc["controlm_json"])
        if not pth.exists():
            res.err("prerequisite-missing", f"{w}.controlm_json", f"{pth} not found - attach that repo (read-only)")
            continue
        if undecided(pc.get("folder_name")):
            res.err("input-missing", f"{w}.folder_name", "ask the operator: the target's folder name for it")
        pn, ph, pj, pl = load_folder(pth)
        if not pj:
            res.err("controlm-not-folder", str(pth), "no SimpleFolder with Job:* entries")
            continue
        pd = {}
        if not undecided(pc.get("descriptor_dir")):
            dp = resolve(folder, pc["descriptor_dir"])
            if not dp.exists():
                res.err("descriptor-missing", f"{w}.descriptor_dir", f"{dp} not found")
            pd = load_descriptors(dp)
        pre_ = reenabled(pd, pn, pj)
        pexp = [j for j in ended_in_base(pj) if j not in pre_]
        for j in pexp:
            pj.pop(j)
        rre_p.update({f"{j} ({pn})": envs for j, envs in pre_.items()})
        cmx = dict(cm, **{k: v for k, v in (pc.get("controlm") or {}).items()
                          if not k.startswith("_") and not undecided(v)})
        prereqs.append({"i": i, "path": pth, "name": pn, "header": ph, "jobs": pj, "lines": pl, "expired": pexp,
                        "tname": pc.get("folder_name"), "desc": pd, "dwaits": descriptor_waits(pd, pn), "cm": cmx,
                        "explicit": [j for j in _as_list(pc.get("jobs"))]})
        for j, v in pj.items():
            for e in added_events(v):
                pproducer[split_event(e)[1]].add((len(prereqs) - 1, j))
    rdwaits = descriptor_waits(rdesc, rname)
    # "ended" = a past When.EndDate in the folder file that no descriptor deletes [BOX expert review, 2026-10-07]
    rre = reenabled(rdesc, rname, rjobs)
    expired = [j for j in ended_in_base(rjobs) if j not in rre]
    for j in expired:                                          # the job no longer runs in any environment
        rjobs.pop(j)
    producer = defaultdict(set)
    for j, v in rjobs.items():
        for e in added_events(v):
            producer[split_event(e)[1]].add(j)                 # producers keyed by the job part of the event
    dlc = cfg.get("datalake") if isinstance(cfg.get("datalake"), dict) else {}
    dl_paths = {}
    for side_ in ("reference_json", "target_json"):
        dl_paths[side_] = [resolve(folder, x) for x in _as_list(dlc.get(side_))]
        for x in dl_paths[side_]:
            if not x.exists():
                res.err("datalake-missing", f"{INPUTS}.datalake.{side_}", f"{x} not found - the Data Lake Control-M JSON "
                        "(cib-auki-aukictrlmcntrm, or its copy under runs/_reference/external/)")
    dl_ref, dl_tgt = load_datalake(dl_paths["reference_json"]), load_datalake(dl_paths["target_json"])
    dl_events = {}                                             # event -> reference Data Lake job (per-book waits)

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
    # books with no BOX jobs [operator, 2026-10-08]: books-excluded.csv beside the register (or target.books_excluded),
    # columns code, description, scope (jobs | all), reason, source, date. To create a book's jobs later, delete its row.
    exp_ = resolve(folder, tgt["books_excluded"]) if not undecided(tgt.get("books_excluded")) \
        else regp.parent / "books-excluded.csv"
    excluded = []
    if exp_.exists():
        codes = {b["code"] for b in tbooks}
        for r in csv.DictReader(exp_.open(encoding="utf-8-sig")):
            c = (r.get("code") or "").strip()
            if not c or c.startswith("#"):
                continue
            if c not in codes:
                res.err("excluded-book-unknown", str(exp_), f"{c} is not a book of {regp.name}")
                continue
            excluded.append((c, (r.get("description") or "").strip(), (r.get("reason") or "").strip()))
        tbooks = [b for b in tbooks if b["code"] not in {c for c, _, _ in excluded}]
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
    tb_in = cfg.get("reference", {}).get("template_book")
    tb = str((tb_in.get(prod) if isinstance(tb_in, dict) else tb_in) or "").strip()
    if undecided(tb):
        normal = [b for b in books_seen if b != "99"]
        tb = normal[0] if normal else (books_seen[0] if books_seen else "")
        res.warn("template-book-chosen", f"{INPUTS}.reference.template_book", f"none given - using book {tb} "
                 f"(reference books with this chain: {', '.join(books_seen) or 'none'})")
    seed = [j for j in cand if parts(j) and parts(j)[2] in (tb, "00")]
    old_product = sorted(j for j in cand if not parts(j))     # reported, not copied: they enter only as prerequisites
    if not seed:
        res.err("nothing-to-copy", "reference", f"no executed FE {prod} job of token {rtok} found in both "
                f"jobs-inventory.csv and {cmp_.name} - another reference branch (find_jobs.py --references), or, if no "
                "onboarded branch runs it in BOX yet, mark the instrument `skip` in the run's instrument-plan.csv")
        return 1

    # --- 2. closure over same-folder producers --------------------------------------------------------------
    # Instrument scope [BOX expert review, 2026-10-07]: a job of ANOTHER instrument family (GMBX<n>, n not this
    # instrument's and not 0) is never copied. A wait on it is replaced by that job's own waits (inheritance:
    # GMBX0LB15D03 waits GMBX6/7LB15D11 -> waits GMBX0LB15D02), unless that instrument is already built for the target
    # (instrument-plan.csv status built / done): then the wait is kept, renamed to the target's job.
    built_fams = set()
    planp = resolve(folder, tgt["instrument_plan"]) if not undecided(tgt.get("instrument_plan")) \
        else folder.parent / "instrument-plan.csv"
    if planp.exists():
        for r in csv.DictReader(planp.open(encoding="utf-8-sig")):
            pr = ALIASES.get(str(r.get("instrument", "")).strip().lower(), str(r.get("instrument", "")).strip().lower())
            if str(r.get("status", "")).strip().lower() in BUILT and pr in PRODUCTS and pr != prod:
                built_fams.add(PRODUCTS[pr][0])
    run_set = {prod} | {p for p in run_products if p in PRODUCTS}
    built_fams |= {PRODUCTS[p][0] for p in run_set if p != prod}

    # Initial Accounting [BOX job expert via operator, 2026-10-08]: group 2409.65 "BOX - Initial accounting (PP, Recla,
    # Reval)", one branch-level job per instrument (SLB GMBOX0028D01 depos, GMBX3..8LB00D02). Defined in the ACC
    # Control-M folder, run from db.conf, and waited for by the FE chain (the book's D02). This agent writes its db.conf
    # line and hands the job to box-acc-jobs-agent; the FE waits on it are re-wired with no question.
    iac = cfg.get("initial_accounting") if isinstance(cfg.get("initial_accounting"), dict) else {}
    ia_group = "" if undecided(iac.get("group")) else str(iac["group"]).strip()
    ia_ref = {}                                                # reference job -> (instrument, target name)
    if ia_group:
        grp = [r for r in inv if r.get("file") == "db.conf" and r.get("active") == "Y" and r.get("group") == ia_group
               and (r.get("branch") == ref["branch_const"] or r.get("token") == rtok)]
        sib_steps = Counter(r["step"][1:] for r in grp if r.get("naming") == "new" and r.get("book_no") == "00")
        dstep = sib_steps.most_common(1)[0][0] if sib_steps else "02"
        for pr, (n, const) in PRODUCTS.items():
            if n in ("0", "?"):
                continue
            for r in grp:
                if r.get("instrument", "").upper() == const.upper():
                    step = r["step"][1:] if r.get("naming") == "new" else dstep
                    ia_ref[r["job"]] = (pr, f"GMBX{n}{ttok}00D{step}")
        if not any(pr == prod for pr, _ in ia_ref.values()):
            res.warn("initial-accounting-missing", prod, f"no db.conf job of group {ia_group} for {prod} in the reference "
                     f"({ref['branch_const']}) - none created for it")
    ia_targets = {t for _, t in ia_ref.values()}
    ia_waits = defaultdict(set)                                # reference event -> who waits

    def fam_of(j):
        pp = parts(j)
        return pp[0] if pp else None

    def other_fam(j):
        n = fam_of(j)
        return n is not None and n not in (fam, "0")

    # old-named PER-BOOK jobs of other reference books [Devin all-instruments run, 2026-10-08]: SLB books 03-12 keep old
    # names (GMBOX0031D02 ... GMBOX0049D03), recognised by their db.conf label (f_getPKByLabel('XLB03')); the template
    # book's job running the same group is their twin (GMBOX0031D02 2629.65 ~ GMBX0LB15D02). A wait on one becomes a
    # wait on each target book's job of that step - nothing renamed, nothing copied.
    grp_of = {r["job"]: r.get("group", "") for r in inv if r.get("file") == "db.conf" and r.get("active") == "Y"}
    tb_by_grp = defaultdict(list)
    for j in rjobs:
        pp = parts(j)
        if pp and pp[2] == tb and grp_of.get(j):
            tb_by_grp[grp_of[j]].append(j)
    old_book = {}
    for r in inv:
        lm = re.fullmatch(r"label:X" + re.escape(rtok) + r"(\d{2})", r.get("label") or "")
        if r.get("file") != "db.conf" or r.get("active") != "Y" or not lm or lm.group(1) == tb or parts(r["job"]):
            continue
        tw = tb_by_grp.get(r.get("group", ""), [])
        if len(tw) == 1:
            old_book[r["job"]] = tw[0]
        elif r["job"] in rjobs:
            res.warn("old-book-job-unmatched", r["job"], f"label {r['label']}, group {r.get('group')}: "
                     f"{'no' if not tw else len(tw)} template-book job(s) of that group - asked as a rename")

    def twin_of(j):
        if j in old_book:
            return old_book[j]
        pp = parts(j)
        return f"GMBX{pp[0]}{rtok}{tb}D{pp[3]}" if pp and pp[2] not in (tb, "00") else j

    include, external, stack, psel = set(), defaultdict(set), [(j, False) for j in seed], set()
    oos, oos_by, cross = {}, defaultdict(set), defaultdict(set)   # out of scope -> its waits / who / built elsewhere
    while stack:
        j, virtual = stack.pop()
        if (j in oos) if virtual else (j in include):
            continue
        if virtual:
            oos[j] = [it["Event"] for it in event_items(rjobs[j].get("eventsToWaitFor", {}))]
            waits = [(e, f"{j} (inherited)") for e in oos[j]]
        else:
            include.add(j)
            waits = [(it["Event"], j) for it in event_items(rjobs[j].get("eventsToWaitFor", {}))]
            waits += [(e, f"{j} [{env}]") for env, e in rdwaits.get(j, [])]   # added by a descriptor (e.g. PRO only)
        for ev, who in waits:
            _, job, _ = split_event(ev)
            if job in ia_ref:                                  # an Initial Accounting job: never copied here
                ia_waits[ev].add(who)
                continue
            ps = producer.get(job, set())
            if not ps and pproducer.get(job):
                psel |= pproducer[job]                         # a prerequisite folder's job
                continue
            if not ps and dl_key(job) in dl_ref and parts(j) and parts(j)[2] == tb:
                dl_events[ev] = dl_key(job)                    # a book job waiting for its book's Data Lake job
                continue
            if not ps:
                external[ev].add(who)
                continue
            for p in ps:
                q = twin_of(p)                                 # another reference book: its template-book twin
                if q not in rjobs:
                    continue
                if other_fam(q):
                    if fam_of(q) in built_fams:
                        cross[ev].add(who)
                    else:
                        oos_by[q].add(who.split(" ")[0])
                        stack.append((q, True))
                    continue
                stack.append((q, False))

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
    # prerequisite jobs: the ones the chain waits for + what they wait for in their own folder
    for k, p in enumerate(prereqs):
        sel = {j for kk, j in psel if kk == k} | {j for j in p["explicit"] if j in p["jobs"]}
        if not sel:
            res.err("prerequisite-not-linked", f"{INPUTS}.prerequisites[{p['i']}]", f"no copied job waits for a job of "
                    f"{p['name']} (in the folder JSON or a descriptor) - give `descriptor_dir` (e.g. the reference's "
                    "pro.json in the environment config repo) or `jobs` (the reference jobs to copy)")
            continue
        prod_p = defaultdict(set)
        for j, v in p["jobs"].items():
            for e in added_events(v):
                prod_p[split_event(e)[1]].add(j)
        pinc, st = set(), list(sel)
        while st:
            j = st.pop()
            if j in pinc:
                continue
            pinc.add(j)
            ws = [(it["Event"], j) for it in event_items(p["jobs"][j].get("eventsToWaitFor", {}))]
            ws += [(e, f"{j} [{env}]") for env, e in p["dwaits"].get(j, [])]
            for ev, who in ws:
                ps = prod_p.get(split_event(ev)[1])
                if ps:
                    st.extend(ps)
                elif not (producer.get(split_event(ev)[1]) or pproducer.get(split_event(ev)[1])):
                    external[ev].add(who)

        def depth(j, seen=()):
            ds = [depth(q, seen + (j,)) for it in event_items(p["jobs"][j].get("eventsToWaitFor", {}))
                  for q in prod_p.get(split_event(it["Event"])[1], ()) if q in pinc and q not in seen]
            return 1 + max(ds, default=0)
        p["include"] = sorted(pinc, key=lambda j: (depth(j), p["lines"].get(j, 0)))
    fe_taken = {t for ts in targets.values() for t in ts}
    auto, ren_given = defaultdict(int), set(renames)
    for p in prereqs:
        for j in p.get("include", []):
            level[j] = "branch"
            pp, new = parts(j), renames.get(j)
            if not undecided(new):
                targets[j] = [new]
            elif pp:
                targets[j] = [f"GMBX{pp[0]}{ttok}{pp[2]}D{pp[3]}"]
            else:                                              # old name: GMBX<n><TT>00D<nn> in chain order
                n = fam if fe_rows.get(j, {}).get("instrument") == inst_const else "0"
                auto[n] += 1
                while f"GMBX{n}{ttok}00D{auto[n]:02d}" in fe_taken - {t for r in ren_given for t in targets.get(r, [])}:
                    auto[n] += 1
                targets[j] = [f"GMBX{n}{ttok}00D{auto[n]:02d}"]
    owners = defaultdict(list)
    for j, ts in targets.items():
        for t in ts:
            owners[t].append(j)
    q_dup = []
    all_taken = set(owners) | known_names
    for t, js in sorted(owners.items()):
        if len(js) > 1:
            res.err("target-name-duplicate", t, f"given to {', '.join(sorted(js))} - one name per job (it is also the "
                    "script name)")
            mv = [j for j in js if j in ren_given] or sorted(js)[1:]
            m = NEW_RE.fullmatch(t)
            sug = "; ".join(f"`{j}` → `{next_free(m.group(1), ttok, m.group(4), all_taken) if m else '<new name>'}`"
                            for j in mv)
            q_dup.append((t, sorted(js), sug + " (`renames`)"))
    tgt_names = set()                                          # the target environment's own jobs [2026-10-07]
    if not undecided(tgt.get("env_folder")):
        tip = resolve(folder, tgt["env_folder"]) / "jobs-inventory.csv"
        if tip.exists():
            tgt_names = {r["job"] for r in csv.DictReader(tip.open(encoding="utf-8"))}
    for j, ts in targets.items():
        for t in ts:
            if t in known_names:
                res.err("target-name-exists", j, f"{t} already exists in the reference inventory")
            if t in tgt_names:
                res.err("target-name-exists", j, f"{t} already exists in the target environment's job confs "
                        f"({tgt['env_folder']}) - a job of that name runs there already")
            if len(t) > 20:
                res.err("target-name-too-long", j, f"{t}: JOB_NAME is VARCHAR2(20)")
    # Data Lake: the reference book's Data Lake job -> the same type of job of each target book (book_vr = label)
    bmap = {k: v for k, v in (dlc.get("book_map") or {}).items() if not k.startswith("_")}
    dl_tgt_idx = defaultdict(list)
    for jn, d in dl_tgt.items():
        dl_tgt_idx[(norm_book(d["book"]), d["key"])].append(jn)
    dl_map, q_dl, dl_rows = {}, [], []
    for ev, rjn in sorted(dl_events.items()):
        d = dl_ref[rjn]
        if rbooks.get(tb) and norm_book(rbooks[tb]) != norm_book(d["book"]):
            res.warn("datalake-link-unverified", ev, f"reference book {tb} is '{rbooks[tb]}' but {rjn} loads book_vr "
                     f"'{d['book']}' - check that the label description is the Data Lake book")
        for x in tbooks:
            bv = bmap.get(x["code"]) or x["desc"]
            if str(bv).strip().upper() == "DROP":
                dl_map[(ev, x["no"])] = None
                continue
            hits = dl_tgt_idx.get((norm_book(bv), d["key"]), [])
            if len(hits) == 1:
                dl_map[(ev, x["no"])] = hits[0]
                dl_rows.append((x["code"], ev, hits[0]))
                continue
            if len(hits) > 1:
                res.warn("datalake-book-ambiguous", x["code"], f"{', '.join(hits)} - using {hits[0]}")
                dl_map[(ev, x["no"])] = hits[0]
                dl_rows.append((x["code"], ev, hits[0]))
                continue
            books_k = sorted({dl_tgt[j]["book"] for j in dl_tgt if dl_tgt[j]["key"] == d["key"]})
            close = difflib.get_close_matches(str(bv), books_k, n=3, cutoff=0.4)
            res.err("datalake-book-unmapped", f"{INPUTS}.datalake.book_map.{x['code']}", f"no {d['key'][0]} "
                    f"{d['key'][1] or 'base'} Data Lake job for book '{bv}' (for {ev}) - its book_vr, or DROP")
            q_dl.append((x["code"], x["desc"], d["key"], ev, close))
    if dl_events and not dl_tgt:
        res.err("datalake-missing", f"{INPUTS}.datalake.target_json", "the target's Data Lake Control-M JSON - each "
                "target book waits for its own Data Lake job")
    emap = {k: v for k, v in (cfg.get("external_events") or {}).items() if not k.startswith("_")}
    for e, v in sorted(emap.items()):                          # KEEP = the target waits for the SAME event
        if str(v).strip().upper() != "KEEP":
            continue
        mm = NEW_RE.fullmatch(split_event(e)[1])
        if mm and mm.group(2) == rtok:
            res.err("keep-reference-event", f"{INPUTS}.external_events.{e}", f"KEEP would make the target wait for the "
                    f"reference branch's own job ({split_event(e)[1]}) - its target equivalent, or DROP")
        elif re.fullmatch(r"GMBOX\d{4}D\d{2}", split_event(e)[1]):
            res.warn("keep-old-box-event", e, "KEEP of an old-named BOX job's event: only if that job really runs for the "
                     "target too - usually it is the reference branch's own job (BOX expert review, 2026-10-07)")
    for e, who in sorted(external.items()):
        if undecided(emap.get(e)):
            res.err("external-event-unmapped", f"{INPUTS}.external_events.{e}", f"waited for by {', '.join(sorted(who))}; "
                    "no job of the reference folder emits it - ask the operator: the target's event, KEEP (the same "
                    "shared event), or DROP")
    if res.errors:
        q_ren = [j for j in sorted(include) if not parts(j) and undecided(renames.get(j))]
        q_ext = {e: who for e, who in sorted(external.items()) if undecided(emap.get(e))}
        if q_ren or q_ext or q_dup or q_dl:
            taken = {t for ts in targets.values() for t in ts} | known_names
            write_pending(folder, cfg, res, inv, cmp_, q_ren, q_ext, dict(pend=pend,
                rtok=rtok, ttok=ttok, fam=fam, inst_const=inst_const, prod=prod, fe_rows=fe_rows, taken=taken,
                prereq_paths=[p["path"] for p in prereqs]), q_dup, q_dl)
        return 1
    _pending_done(pend)

    def map_job_for_book(job: str, book_no: str | None) -> list[str]:
        """target job name(s) for a reference job referenced from a target job of book `book_no`."""
        if job in old_book:                                    # an old-named job of another reference book
            n, _, _, s = parts(old_book[job])
            return [f"GMBX{n}{ttok}{book_no}D{s}"] if book_no is not None else \
                [f"GMBX{n}{ttok}{x['no']}D{s}" for x in tbooks]
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
        if pp and other_fam(job) and fam_of(job) in built_fams:   # branch-level job of an instrument already built
            return [f"GMBX{pp[0]}{ttok}00D{pp[3]}"]
        return []

    def map_event(e: str, book_no: str | None, _seen=frozenset()) -> list[str]:
        pre, job, suf = split_event(e)
        if job in ia_ref:                                      # Initial Accounting: the target's, if built in this run
            pr_, t_ = ia_ref[job]
            return [f"{pre}{t_}{suf}"] if pr_ in run_set else []
        if e in dl_events:
            if book_no is None:
                return [e]
            t = dl_map.get((e, book_no))
            return [f"{pre}{dl_spell(t, job)}{suf}"] if t else []
        if e in external:
            v = str(emap[e]).strip()
            return [] if v.upper() in ("DROP", "DROP-REVIEW") else ([e] if v.upper() == "KEEP" else [v])
        oj = job if job in oos else (twin_of(job) if parts(job) and twin_of(job) in oos else None)
        if oj:                                                 # another instrument's job: inherit its waits
            if oj in _seen:
                return []
            out = []
            for e2 in oos[oj]:
                out += [x for x in map_event(e2, book_no, _seen | {oj}) if x not in out]
            return out
        ts = map_job_for_book(job, book_no)
        return [f"{pre}{t}{suf}" for t in ts] if ts else [e]

    def remap_list(v, book_no):
        """A list of events, possibly in OR-groups (`[{..}, {..}, "OR", {..}]`): each event mapped (one may become
        several, or none); inside a group duplicates go; an empty group goes; identical groups go [2026-10-07]."""
        groups, cur = [], []
        for x in v:
            if isinstance(x, str) and x.strip().upper() == "OR":
                groups.append(cur)
                cur = []
            else:
                cur.append(x)
        groups.append(cur)
        new_groups, keys = [], []
        for g in groups:
            out, seen = [], set()
            for x in g:
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
            key = tuple(sorted(json.dumps(y, sort_keys=True) for y in out))
            if out and key not in keys:
                keys.append(key)
                new_groups.append(out)
        res_ = []
        for i, g in enumerate(new_groups):
            res_ += (["OR"] if i else []) + g
        return res_

    def remap_events(node, book_no):
        """Every event under a node - waits, adds and the Event:Add / Event:Delete of If blocks (a `-NOK` too)."""
        if isinstance(node, dict):
            if isinstance(node.get("Event"), str):
                ne = map_event(node["Event"], book_no)
                if ne:
                    node["Event"] = ne[0]
            for k, v in list(node.items()):
                if isinstance(v, list) and any((isinstance(x, dict) and "Event" in x) or
                                               (isinstance(x, str) and x.strip().upper() == "OR") for x in v):
                    node[k] = remap_list(v, book_no)
                elif isinstance(v, (dict, list)):
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

    # --- the Control-M folders: prerequisite folders first, then the FE folder --------------------------------
    envspecific = ("Host", "RunAs", "Application", "FilePath")
    times = defaultdict(set)

    def make_header(cmx, rhead, rn):
        h = {"Type": "SimpleFolder"}
        for k in ("ControlmServer", "SiteStandard", "OrderMethod"):
            h[k] = cmx[k]
        for k, v in rhead.items():
            if k not in h:
                h[k] = v
                res.warn("header-copied", f"{rn}.{k}", f"copied from the reference ({v!r}) - check it for the target")
        return h

    def copy_job(src, j, t, tbk, cmx):
        o = copy.deepcopy(src)
        o["FileName"] = t
        for k in envspecific:
            if k in o:
                o[k] = cmx[k]
        if "CreatedBy" in o:
            if str(cmx["CreatedBy"]).strip().lower() == "omit":
                del o["CreatedBy"]
            else:
                o["CreatedBy"] = cmx["CreatedBy"]
        if isinstance(o.get("When"), dict) and "MonthDaysCalendar" in o["When"]:
            o["When"]["MonthDaysCalendar"] = cmx["MonthDaysCalendar"]
        if isinstance(o.get("When"), dict):
            if "EndDate" in o["When"]:                         # a live reference job with an end date: not carried over
                del o["When"]["EndDate"]
                res.warn("end-date-dropped", t, f"{j} has a future EndDate - not copied")
            if o["When"].get("FromTime"):
                times[o["When"]["FromTime"]].add(t)
        doc = {k: v for k, v in (cmx.get("DocumentationFile") or {}).items() if not k.startswith("_")} \
            if isinstance(cmx.get("DocumentationFile"), dict) else {}
        if doc:
            o["DocumentationFile"] = doc
        pp = parts(j)
        if "Description" in o:
            o["Description"], ok = describe(o["Description"], pp[2] if pp and level[j] == "book" else None, tbk)
            if not ok:
                res.warn("description-not-renamed", t, f"the reference book's description is not in {j}'s "
                         "Description - check it")
        remap_events(o, tbk["no"] if tbk else None)            # every event of the job, If blocks included
        if "eventsToWaitFor" in o and not list(event_items(o["eventsToWaitFor"])):
            del o["eventsToWaitFor"]                           # every wait dropped or inherited away
        return o

    mapping, pfolders = [], []
    for p in prereqs:
        pf = make_header(p["cm"], p["header"], p["name"])
        for j in p.get("include", []):
            t = targets[j][0]
            pf[t] = copy_job(p["jobs"][j], j, t, None, p["cm"])
            mapping.append({"reference_job": j, "reference_line": f"{p['path'].name}:{p['lines'].get(j, 0)}",
                            "level": "prerequisite", "target_job": t, "target_book": "",
                            "shared_across_instruments": "yes", "db_conf": "", "status": "",
                            "target_folder": p["tname"]})
        pfolders.append((p, pf))
    newfolder = make_header(cm, rheader, rname)
    for j in sorted(include, key=lambda x: (rjline.get(x, 0), x)):
        book_list = [b for b in tbooks] if level[j] == "book" else [None]
        for tbk, t in zip(book_list, targets[j]):
            newfolder[t] = copy_job(rjobs[j], j, t, tbk, cm)
            shared = t.startswith("GMBX0") or not parts(j)     # generic per book / branch: shared by all instruments
            mapping.append({"reference_job": j, "reference_line": f"{cmp_.name}:{rjline.get(j, 0)}", "level": level[j],
                            "target_job": t, "target_book": tbk["code"] if tbk else "",
                            "shared_across_instruments": "yes" if shared else "", "db_conf": "", "status": "",
                            "target_folder": cm["folder_name"]})
    acc = cfg.get("acc") if isinstance(cfg.get("acc"), dict) else {}
    acc_folder = "<the target's ACC folder - box-acc-jobs-agent>" if undecided(acc.get("folder_name")) \
        else str(acc["folder_name"])
    own_ia = sorted((j, t) for j, (pr, t) in ia_ref.items() if pr == prod)
    for j, t in own_ia:                                        # this instrument's Initial Accounting job
        rr = next((r for r in inv if r["job"] == j and r.get("file") == "db.conf"), {})
        mapping.append({"reference_job": j, "reference_line": f"db.conf:{rr.get('line', '')}",
                        "level": "initial-accounting", "target_job": t, "target_book": "",
                        "shared_across_instruments": "", "db_conf": "", "status": "", "target_folder": acc_folder})

    # --- environment descriptors: the reference's per-environment changes, re-pointed to the target ------------
    ref_env_values = set()
    for jobs_ in [rjobs, *(p["jobs"] for p in prereqs)]:
        for o in jobs_.values():
            ref_env_values |= {str(o.get(k)) for k in (*envspecific, "CreatedBy") if o.get(k)}
            if isinstance(o.get("When"), dict) and o["When"].get("MonthDaysCalendar"):
                ref_env_values.add(str(o["When"]["MonthDaysCalendar"]))
    ref_env_values |= {str(h.get("ControlmServer")) for h in [rheader, *(p["header"] for p in prereqs)] if h.get("ControlmServer")}

    def env_literal(node) -> str:
        texts = [x for x in json.dumps(node, ensure_ascii=False).replace('"', " ").split() if x]
        blob = json.dumps(node, ensure_ascii=False)
        for v in ref_env_values:
            if (len(v) >= 4 and v in blob) or v in texts:
                return v
        return ""

    def translate(descs, rn, tn, inc_jobs, cmx):
        """{env: (entries, review [(n, why)], skipped [str], notes [str])} - every DeployDescriptor entry type
        [read: SLB FE + load-prices pre.json / pro.json, 2026-10-07]:
          Property + Replace (regex)   copied when it carries no reference value (SiteStandard _D_ -> _I_/_P_,
                                       Application -D-..._Des, folder JACD- -> JACI-/JACP-); with a reference value,
                                       the target's per-environment value (controlm.env.<env>.<Property>) or review
          Property + Assign            the target's value from controlm.env.<env>; Host is never guessed; another
                                       property keeps the reference value, listed to confirm
          Add  $.<folder>.<job>[.x]    re-pointed to the target job(s), events re-wired; StartDate (activation date)
                                       from controlm.env.<env>.StartDate; $.<other> (e.g. $.DocumentationFile) copied
          Delete <path>                re-pointed; a When.EndDate delete is not copied (the target jobs carry none)"""
        out = {}
        pre = f"$.{rn}"

        def target_paths(path):
            """[(new path, book)] for a path in the reference folder; None = not this folder; [] = a job not built."""
            if path != pre and not path.startswith(pre + "."):
                return None
            rest = path[len(pre):].lstrip(".")
            if not rest:
                return [(f"$.{tn}", None)]
            j, _, tail = rest.partition(".")
            tail = "." + tail if tail else ""
            if j not in inc_jobs:
                return []
            books = tbooks if level.get(j) == "book" else [None]
            return [(f"$.{tn}.{t}{tail}", tbk) for tbk, t in zip(books, targets[j])]

        for env, entries in descs.items():
            envv = {k: v for k, v in ((cmx.get("env") or {}).get(env) or {}).items()
                    if not k.startswith("_") and not undecided(v)}
            new, review, skipped, notes = [], [], [], []
            with_entry = {str(e["Add"].get("Path", ""))[len(pre) + 1:].split(".")[0] for e in entries
                          if isinstance(e, dict) and isinstance(e.get("Add"), dict)}
            for n, e in enumerate(entries, 1):
                if not isinstance(e, dict):
                    review.append((n, "not an object"))
                    continue
                add = e.get("Add")
                if isinstance(add, dict):
                    path = str(add.get("Path", ""))
                    tps = target_paths(path)
                    if tps is None:                            # not a path of this folder, e.g. $.DocumentationFile
                        lit = env_literal(e)
                        if lit:
                            review.append((n, f"`{path}` carries the reference value `{lit}`"))
                        else:
                            new.append(copy.deepcopy(e))
                            notes.append(f"entry {n} `{path}` {add.get('propertyName', '')} = "
                                         f"`{add.get('propertyValue')}` copied as the reference's")
                        continue
                    if not tps and path[len(pre) + 1:].split(".")[0] in old_book:
                        j = path[len(pre) + 1:].split(".")[0]
                        tw = old_book[j]
                        if tw in with_entry:
                            skipped.append(f"{j} (old-named book job: as the template book's {tw})")
                        else:
                            review.append((n, f"`{j}` (old-named job of another reference book, twin `{tw}`): only "
                                              "that book gets it - which target books?"))
                        continue
                    if not tps:
                        j = path[len(pre) + 1:].split(".")[0]
                        pp = parts(j)
                        twin = pp and f"GMBX{pp[0]}{rtok}{tb}D{pp[3]}" in include and pp[2] not in (tb, "00")
                        if twin and f"GMBX{pp[0]}{rtok}{tb}D{pp[3]}" in with_entry:
                            skipped.append(f"{j} (book {pp[2]}: as the template book's)")
                        elif twin:
                            review.append((n, f"`{j}`: only reference book {pp[2]} gets it - which target books?"))
                        else:
                            skipped.append(j)
                        continue
                    for npath, tbk in tps:
                        y = copy.deepcopy(e)
                        y["Add"]["Path"] = npath
                        remap_events(y["Add"].get("propertyValue"), tbk["no"] if tbk else None)
                        if add.get("propertyName") in ("eventsToWaitFor", "eventsToAdd") \
                                and not list(event_items(y["Add"].get("propertyValue"))):
                            continue                           # every event DROPped
                        if add.get("propertyName") == "StartDate":
                            if envv.get("StartDate"):
                                y["Add"]["propertyValue"] = str(envv["StartDate"])
                            else:
                                review.append((n, f"`{npath}` StartDate (activation date) is the reference's "
                                                  f"`{add.get('propertyValue')}` - the target's: "
                                                  f"controlm.env.{env}.StartDate"))
                                continue
                        lit = env_literal(y["Add"].get("propertyValue"))
                        if lit:
                            review.append((n, f"`{npath}`: carries the reference value `{lit}`"))
                            continue
                        new.append(y)
                    continue
                dps = delete_paths(e)
                if "Delete" in e:
                    y, ok = copy.deepcopy(e), True
                    for path in dps:
                        if path.endswith(".When.EndDate"):
                            skipped.append(f"{path} (EndDate delete: the target jobs carry no EndDate)")
                            ok = False
                            break
                        tps = target_paths(path)
                        if tps is None:
                            continue
                        if not tps:
                            skipped.append(path)
                            ok = False
                            break
                        if len(tps) > 1:                       # per-book job: one Delete entry per target book
                            for npath, _ in tps[1:]:
                                new.append(replace_strings(e, path, npath))
                        y = replace_strings(y, path, tps[0][0])
                    if ok:
                        new.append(y)
                    continue
                if "Property" in e and ("Replace" in e or "Assign" in e):
                    prop = str(e["Property"])
                    if prop in envv:
                        y = copy.deepcopy(e)
                        if "Assign" in e:
                            y["Assign"] = envv[prop]
                        else:
                            dev = cmx.get(prop)
                            if undecided(dev):
                                review.append((n, f"`{prop}` replace: the target folder file has no {prop} to replace"))
                                continue
                            y["Replace"] = [{"^" + re.escape(str(dev)) + "$": str(envv[prop])}]
                        new.append(y)
                        continue
                    lit = (str(e["Assign"]) if str(e["Assign"]) in ref_env_values else "") if "Assign" in e \
                        else env_literal(e)                    # an Assign value is per environment by definition
                    if lit:
                        review.append((n, f"`{prop}` {'assign' if 'Assign' in e else 'replace'} carries the reference "
                                          f"value `{lit}` - the target's value per environment "
                                          f"(controlm.env.{env}.{prop})"))
                    elif prop in NEVER_COPIED:                 # Host; OrderMethod (time zone) [BOX expert, 2026-10-08]
                        review.append((n, f"`{prop}` = `{e.get('Assign', e.get('Replace'))}` is the reference's - "
                                          f"the target's {prop} for {env}: controlm.env.{env}.{prop}"))
                    else:
                        new.append(copy.deepcopy(e))
                        if "Assign" in e:
                            notes.append(f"entry {n} `{prop}` = `{e['Assign']}` copied from the reference - confirm "
                                         f"for the target (or set controlm.env.{env}.{prop})")
                    continue
                review.append((n, "entry type not translated"))
            done = {str(x.get("Property")) for x in new if isinstance(x, dict)}
            for prop in ("Host", "ControlmServer"):            # mandatory per environment [BOX expert, 2026-10-07]
                if prop not in done:
                    notes.append(f"**no `{prop}` entry for {env}** - mandatory: add one (the reference descriptor has "
                                 f"none, or it went to review)")
            out[env] = (new, review, skipped, notes)
        return out

    dtrans = [(cm["folder_name"], translate(rdesc, rname, cm["folder_name"], include, cm))]
    dtrans += [(p["tname"], translate(p["desc"], p["name"], p["tname"], set(p.get("include", [])), p["cm"]))
               for p in prereqs]

    # --- 5. checks ------------------------------------------------------------------------------------------
    emitted = {split_event(e)[1] for f_ in [newfolder, *(pf for _, pf in pfolders)] for v in f_.values()
               if isinstance(v, dict) for e in added_events(v)}
    ext_ok = {e for e, v in emap.items() if not undecided(v)}
    ext_ok |= {f"{split_event(e)[0]}{dl_spell(t, split_event(e)[1])}{split_event(e)[2]}" for (e, _), t in dl_map.items() if t}
    graph = defaultdict(set)
    for t, o in [kv for f_ in [newfolder, *(pf for _, pf in pfolders)] for kv in f_.items()]:
        if not isinstance(o, dict):
            continue
        for it in event_items(o.get("eventsToWaitFor", {})):
            e = it["Event"]
            _, job, _ = split_event(e)
            mm = NEW_RE.fullmatch(job)
            if job in emitted:
                graph[t].add(job)
            elif job in ia_targets:
                pass                                           # an Initial Accounting job (db.conf here, ACC folder)
            elif mm and mm.group(2) == ttok and mm.group(1) in built_fams:
                pass                                           # another instrument's job, already built for the target
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
    open_lines, conf, conf_by = 0, [], defaultdict(list)
    fmt = "wrapper" if undecided(tgt.get("dbconf_format")) else str(tgt["dbconf_format"]).strip().lower()
    if fmt not in ("wrapper", "pgt_prg"):
        res.err("dbconf-format-bad", f"{INPUTS}.target.dbconf_format", f"{fmt!r}: wrapper or pgt_prg")
        return 1
    core_call = "PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup" if undecided(tgt.get("core_call")) else str(tgt["core_call"])
    core_time = TIME_ARG if undecided(tgt.get("core_time")) else str(tgt["core_time"])
    core_other, core_vals = [], {k.upper(): str(v) for k, v in (tgt.get("constant_values") or {}).items()
                                 if not k.startswith("_")}
    if fmt == "pgt_prg" and undecided(tgt.get("branch_pk")):
        res.err("input-missing", f"{INPUTS}.target.branch_pk", "ask the operator: the target branch's PK (the value of "
                f"{tgt['branch_const']}, J-E4) - the core call takes the branch PK on every line")
        return 1

    def to_core(line: str, t: str) -> str:
        """The wrapper call -> the core call, 8 arguments (order: all_arguments + package spec):
        <JOB>:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(P_GROUP, P_BRANCH, P_DATE, P_INSTRUMENT, P_TIME, P_VSTATIC,
        P_LABEL, P_SUBLABEL). As Mexico's db.conf, with the BOX job expert's two corrections [operator, 2026-10-07]:
          P_GROUP       the reference's group
          P_BRANCH      the target branch PK (target.branch_pk) on EVERY line, per-book ones too (Mexico: NULL there)
          P_DATE        the reference's date argument (to_date('$ODATE','YYYYMMDD'))
          P_INSTRUMENT  the reference's instrument constant (owner swapped); CST_PK_VACIO -> NULL
          P_TIME        to_char(sysdate,'RRRR-mm-DD HH24:MI:SS') (target.core_time; Mexico repeats the date: wrong)
          P_VSTATIC     the reference's mode by value (CST_PK_DINAMIC -> 0, target.constant_values)
          P_LABEL       BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('<target book>'), NULL for a branch-level job
          P_SUBLABEL    the reference's, else NULL (CST_PK_VACIO -> NULL)"""
        m = re.match(r"^([^:]+):([^:]*):([^:]*):(.*)$", line)
        cm_ = re.search(r"((?:[A-Za-z_][\w$#]*\.){1,2})([A-Za-z_][\w$#]*)\s*\(", m.group(4)) if m else None
        if not cm_ or cm_.group(2).lower() == "p_executegroup":
            return line
        if not cm_.group(2).lower().startswith("f_executegroup"):
            core_other.append(f"{t} ({cm_.group(1)}{cm_.group(2)})")
            return line
        a = split_args(m.group(4)[cm_.end():])
        a += ["NULL"] * (7 - len(a))
        g, _, dt, ins, mode, lab, sub = a[:7]

        def empty(x):
            return "NULL" if re.search(r"\bCST_PK_VACIO\b", x, re.I) else x
        mc = re.search(r"\b(CST_[A-Z0-9_]+)\s*$", mode, re.I)
        vst = core_vals.get(mc.group(1).upper(), mode) if mc else mode
        args = [g, str(tgt["branch_pk"]), dt, empty(ins), core_time, vst, empty(lab), empty(sub)]
        return f"{m.group(1)}:T:P:{core_call}({', '.join(args)});"
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
        if fmt == "pgt_prg":
            line = to_core(line, t)
        if lab and fmt == "wrapper" and str(tgt["wrapper_args"]) == "5":
            conf_by[row["target_folder"]].append(f"# OPEN checkpoint 3 - {tgt['wrapper_owner']}.f_ExecuteGroup takes "
                                                 f"no label: {line}")
            row["status"] = "OPEN - wrapper has no label argument"
            open_lines += 1
        else:
            conf_by[row["target_folder"]].append(line)
            row["status"] = "ready"
        row["db_conf"] = f"db.conf:{r['line']}"
    if res.errors:
        return 1

    # --- write -----------------------------------------------------------------------------------------------
    od.mkdir(parents=True, exist_ok=True)
    blocks = []
    for p, _ in pfolders:                                      # prerequisite folders first (they run first)
        if conf_by[p["tname"]]:
            blocks += [f"########## BOX - {tgt['branch_code']} - {p['tname']} (from {p['name']}) ##########",
                       *conf_by[p["tname"]]]
    if conf_by[acc_folder]:
        blocks += [f"########## BOX - {tgt['branch_code']} - Initial accounting ({ia_group}) - {prod} - Control-M: "
                   f"{acc_folder} (box-acc-jobs-agent) ##########", *conf_by[acc_folder]]
    blocks += [f"########## BOX - {tgt['branch_code']} - FE - {prod} (from {rtok}, book {tb}) ##########",
               *conf_by[cm["folder_name"]]]
    conf = [x for x in blocks if not x.startswith("##########")]
    blocks = [re.sub(r"[/\[\]*]", "-", x) if x.startswith("##########") else x for x in blocks]   # sed-safe banners
    (od / "db.conf.proposal").write_text("\n".join(blocks) + "\n", encoding="utf-8")
    for p, pf in pfolders:
        (od / f"{p['tname']}.json").write_text(json.dumps({p["tname"]: pf}, indent=2, ensure_ascii=False) + "\n",
                                               encoding="utf-8")
    (od / f"{cm['folder_name']}.json").write_text(json.dumps({cm["folder_name"]: newfolder}, indent=2, ensure_ascii=False)
                                                  + "\n", encoding="utf-8")
    dwritten = []
    for tn, envs in dtrans:
        for env, (entries, _, _, _) in envs.items():
            if entries:
                dd = od / "descriptors" / tn
                dd.mkdir(parents=True, exist_ok=True)
                (dd / env).write_text(json.dumps({"DeployDescriptor": entries}, indent=4, ensure_ascii=False) + "\n",
                                      encoding="utf-8")
                dwritten.append(f"descriptors/{tn}/{env}")
    with (od / "mapping.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(mapping[0]))
        w.writeheader()
        w.writerows(mapping)
    # hand-off to box-acc-jobs-agent: the Initial Accounting jobs its ACC folder must define [2026-10-08]
    handoff = []
    if own_ia:
        acc_cm = explain_job.load_controlm([p for p in (resolve(folder, x) for x in _as_list(ref.get("controlm_other")))
                                            if p.exists()])
        all_jobs = [kv for f_ in [newfolder, *(pf for _, pf in pfolders)] for kv in f_.items() if isinstance(kv[1], dict)]
        for j, t in own_ia:
            c = acc_cm.get(j)
            line = next((x for x in conf_by[acc_folder] if x.startswith(t + ":")), "")
            waited = sorted(k for k, o in all_jobs for it in event_items(o.get("eventsToWaitFor", {}))
                            if split_event(it["Event"])[1] == t)
            if c:
                emits = [f"{pre_}{t}{suf_}" for pre_, jb, suf_ in map(split_event, added_events(c["obj"])) if jb == j]
                d = copy.deepcopy(c["obj"])
                d["FileName"] = t
                for k in ("Host", "RunAs", "FilePath"):
                    if k in d:
                        d[k] = cm[k]
                d["Application"] = acc.get("Application") if not undecided(acc.get("Application")) else \
                    "<ask - the target's ACC Application (the reference uses its own ACC application)>"
                if "CreatedBy" in d:
                    if str(cm["CreatedBy"]).strip().lower() == "omit":
                        del d["CreatedBy"]
                    else:
                        d["CreatedBy"] = cm["CreatedBy"]
                if isinstance(d.get("When"), dict):
                    d["When"].pop("EndDate", None)
                    if "MonthDaysCalendar" in d["When"]:
                        d["When"]["MonthDaysCalendar"] = cm["MonthDaysCalendar"]
                if "Description" in d:
                    d["Description"] = re.sub(r"\b" + re.escape(ref["display"]) + r"\b", tgt["display"], d["Description"])
                d = replace_strings(d, f"{j}-OK", f"{t}-OK")
                for pre_ in ("G010014-", "G010012-"):
                    d = replace_strings(d, f"{pre_}{j}-OK", f"{pre_}{t}-OK")
                d = replace_strings(d, f"{j}-NOK", f"{t}-NOK")
                where = {"repo": c["repo"], "file": c["file"], "line": c["line"], "folder": c["folder"]}
            else:
                emits, d, where = [f"{t}-OK", f"G010014-{t}-OK", f"G010012-{t}-OK"], None, None
                res.warn("initial-accounting-not-found", j, "not in reference.controlm_other (the reference's ACC "
                         "folder repo) - hand-off without a draft job; events as the reference's new-named ones")
            handoff.append({"target_job": t, "instrument": prod, "reference_job": j, "group": ia_group,
                            "group_name": iac.get("name", ""), "group_events": iac.get("events", []),
                            "db_conf": line, "acc_folder": acc_folder, "waited_by": waited, "emits": emits,
                            "reference_controlm": where, "draft_job": d})
        (od / "acc-handoff.json").write_text(json.dumps({"for": "box-acc-jobs-agent", "branch": tgt["branch_code"],
                                                         "initial_accounting": handoff}, indent=2, ensure_ascii=False)
                                             + "\n", encoding="utf-8")
    hand = sorted({e for o in newfolder.values() if isinstance(o, dict) for it in event_items(o.get("eventsToAdd", {}))
                   for e in [it["Event"]] if re.match(r"G\d{6}-", e)})
    rep = [f"# BOX FE jobs - {tgt['branch_code']} - {prod}", "",
           f"From reference token `{rtok}` (template book `{tb}`, `{cmp_.name}`), {len(include)} reference jobs -> "
           f"**{len(mapping)} target jobs** for {len(tbooks)} books; db.conf lines: {len(conf)} "
           f"({open_lines} OPEN). Folder `{cm['folder_name']}`.", "",
           *(["**Prerequisite folders (run first):** " + "; ".join(
               f"`{p['tname']}` ← `{p['name']}`: {', '.join(f'{j} → {targets[j][0]}' for j in p.get('include', []))}"
               for p, _ in pfolders), ""] if pfolders else []),
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
    if excluded:
        rep += [f"- **books excluded** (`{exp_.name}`: no BOX job, no db.conf line, no Data Lake question; delete a row to "
                "create its jobs): " + ", ".join(f"{c} ({d})" for c, d, _ in excluded)]
    if rre or rre_p:
        rep += ["- ended in the folder file but **re-enabled by a descriptor** (its EndDate deleted) - copied, without "
                "EndDate: " + ", ".join(f"{j} ({', '.join(sorted(v))})" for j, v in sorted({**rre, **rre_p}.items()))]
    if ia_group:
        rep += ["", f"## Initial Accounting ({ia_group}) - db.conf here, Control-M by box-acc-jobs-agent", "",
                "| Target job | Reference | Waited for by | db.conf |", "|---|---|---|---|"]
        rep += [f"| `{h['target_job']}` | `{h['reference_job']}` | {', '.join(h['waited_by']) or '-'} | "
                f"{'written' if h['db_conf'] else '-'} |" for h in handoff] or ["| - | - | - | - |"]
        dropped = sorted({split_event(e)[1] for e in ia_waits if ia_ref[split_event(e)[1]][0] not in run_set})
        rep += ["", f"Hand-off: `acc-handoff.json` (folder `{acc_folder}`)." + (
            f" Waits on instruments not built in this run, dropped: {', '.join(dropped)}." if dropped else "")]
    if oos:
        rep += ["", "## Other instruments' jobs - not copied, their waits inherited", "",
                "A copied job waited for another instrument's job (not built for the target yet: instrument-plan.csv). "
                "That wait is replaced by the job's own waits; OR-groups that became identical are merged. **When that "
                "instrument is built, these waits must point to its jobs again.**", "",
                "| Other instrument's job | Its waits (inherited) | Waited for by |", "|---|---|---|"]
        rep += [f"| `{j}` ({explain_job.INSTR_FAMILY.get(fam_of(j), '?')}) | {', '.join(f'`{e}`' for e in oos[j]) or '-'} "
                f"| {', '.join(sorted(oos_by[j]))} |" for j in sorted(oos)]
    if cross:
        rep += ["", "## Waits on instruments built for the target - in this run or before (kept, renamed)", ""]
        rep += [f"- `{e}` (waited by {', '.join(sorted(w))})" for e, w in sorted(cross.items())]
    if dtrans and any(envs for _, envs in dtrans):
        rep += ["", "## Environment descriptors (per-environment changes, e.g. `pro.json`)", "",
                "Waits the reference adds **only through a descriptor** (e.g. PRO only) are kept in the target's "
                "descriptor, not in its folder file — as the reference. Proposals for the environment config repo "
                f"({cm.get('host_config_repo') or 'see the inputs'}); the agent does not write there.", ""]
        for tn, envs in dtrans:
            for env, (entries, review, skipped, dnotes) in envs.items():
                rep.append(f"- `{tn}` / `{env}`: {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} written"
                           + (f"; not in this build (other jobs): {', '.join(sorted(set(skipped)))}" if skipped else ""))
                rep += [f"  - **review** entry {n}: {why}" for n, why in review]
                rep += [f"  - {x}" for x in dnotes]
    if dl_events:
        rep += ["", "## Data Lake waits — per book (book label description = Data Lake `book_vr`)", "",
                "| Target book | Reference event | Target Data Lake job |", "|---|---|---|"]
        rep += [f"| `{c}` | `{e}` | `{t}` |" for c, e, t in dl_rows]
        rep += [f"| `{x['code']}` | `{e}` | DROP |" for (e, no), t in dl_map.items() if t is None
                for x in tbooks if x["no"] == no]
    to_review = sorted(e for e in external if str(emap.get(e, "")).strip().upper() == "DROP-REVIEW")
    if to_review:
        rep += ["", "## Decisions to review (`DROP-REVIEW`: dropped, to confirm with the BOX team)", ""]
        rep += [f"- `{e}` (waited by {', '.join(sorted(external[e]))})" for e in to_review]
    rep += ["", "## External events (waited for, emitted by no job of the folder)", ""]
    rep += [f"- `{e}` -> `{emap[e]}` (waited by {', '.join(sorted(who))})" for e, who in sorted(external.items())] or ["- none"]
    rep += ["", "## Hand-offs - events other folders may wait for (G0100xx- prefix, as the reference emits)", ""]
    rep += [f"- `{e}`" for e in hand] or ["- none"]
    if fmt == "pgt_prg":
        rep += ["", f"## db.conf: the core call `{core_call}` (T:P, 8 arguments)", "",
                "Every `f_ExecuteGroup` line of the reference is written as the core call, as Mexico's `db.conf` with the "
                "BOX job expert's corrections [operator, 2026-10-07]: (group, **branch PK " f"`{tgt['branch_pk']}` on every "
                "line**, date, instrument - `NULL` for `CST_PK_VACIO`, **time** " f"`{core_time}`, vstatic by value, label "
                "- `NULL` at branch level, sub-label `NULL`)."]
        if core_other:
            rep += ["", "Not group calls - kept as the reference's function (owner swapped): " + ", ".join(core_other)]
    if open_lines:
        rep += ["", f"## OPEN - {open_lines} db.conf line(s) need the label argument",
                "", f"`{tgt['wrapper_owner']}.f_ExecuteGroup` takes {tgt['wrapper_args']} arguments; these lines are "
                "written commented. They wait on checkpoint 3 (BOX Lead)."]
    if res.warns:
        rep += ["", "## Warnings", ""] + [f"- `{c}` {w}: {m}" for c, w, m in res.warns]
    rep += ["", "Not done here: the repos, any deployment. The Unix scripts per job are created by `unix/job_unix.sh` "
            "(below, from the `db_job` template). A proposal for the BOX team."]
    (od / "report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    return 4 if open_lines else 0


if __name__ == "__main__":
    sys.exit(main())
