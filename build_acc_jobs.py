#!/usr/bin/env python3
"""build_acc_jobs.py - box-acc-jobs-agent: a new branch's BOX ACC jobs from a reference branch's ACC chain.

    python3 scripts/build_acc_jobs.py runs/<BRANCH>/<tier>-<env>/acc-jobs/<name>_<YYYYMMDD>_<n>/

Reads <run>/acc-jobs-inputs.json; writes <run>/out/ (a proposal for the BOX team - nothing is deployed, nothing is run):

  <FOLDER>.json            the target's ACC Control-M SimpleFolder: the Initial Accounting jobs (from box-fe-jobs-agent's
                           out/acc-handoff.json), per instrument the template book's per-book ACC steps once per target
                           book, the branch-level steps once (ruler update, MIC end-of-day revaluation)
  shell.conf.proposal      every per-book step and branch MIC step as `<JOB>:<debug>:<chdir>:mbjbox.sh <JOB> ...` -
                           a new branch's ACC steps run through MBJ [operator, 2026-10-21]
  db.conf.proposal         the branch-level steps the reference runs from db.conf (the ruler update), as the core call
                           PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup; the Initial Accounting lines are the FE agent's
  sql/<BASE>-mbj-*.sql     one BOX_ACC.T_BOX_MBJ_PROPERTIES_S row per shell.conf job: rehearsal (ROLLBACK), config
                           (COMMIT), verify (read-only), rollback (the only undo). PKs from the call given in
                           `mbj.pk_call` (SIGOM's own - box-acc-model.md section 6), checked against the installation's
                           auth code; labels by code (f_getPKByLabel), never a typed PK
  mapping.csv, report.md   reference job -> target job(s), how each runs, where its MBJ values came from
  unix/                    the Unix package (scripts/unix_package.py, shell.conf + db.conf)
  ../pending-questions.md  (in the run folder) what is still to answer, with a suggestion each

How (SLB's ACC folder, Devin read-only audit 2026-10-21, runs/NY_SCH/tier2-pre/acc-jobs/00-discovery.md):
  - per instrument family n: seed = the ACC folder's GMBX<n><RT><tb>D<ss> (template book tb) and GMBX<n><RT>00D<ss>;
    closure = every job of the ACC folder they wait for (an old-named branch job, e.g. depos' ruler update, is asked a
    new name: `renames`). Initial Accounting jobs (box-fe-jobs-agent's hand-off, or a db.conf group in
    `initial_accounting.group`) are never rebuilt: their names, draft jobs and db.conf lines are the FE agent's -
    target.fe_run is required: it must have built every instrument of the run and name the same ACC folder.
  - waits: on a copied job -> the target's; on the same step of every reference book -> every target book's; on an FE
    job (not in the ACC folder) -> the target's FE job of that book (checked against target.fe_run's out/); on a
    dropped job -> its own waits; on another instrument's ACC job not in the run -> its own waits; anything else ->
    `external_events` (target event, KEEP, DROP, DROP-REVIEW, `<OPEN ...>`).
  - MIC end-of-day steps (MBJ row MIC_EOD = 1, else D12 / D13) and MIC_SENDER_TYPE are ASKED per instrument, every run
    (`mic.<instrument>.eod_steps` keep | drop, or none when the reference has none; `mic.<instrument>.sender_type`
    reference | lastly | none) [operator, 2026-10-21].
  - an MBJ row copies the reference row of the same job (else of the same step in another book - warned): branch,
    label and calendar are the target's (`mbj.calendar` is asked: the reference's rows use a processing calendar, not
    the branch's); the group is the reference's global group unless `mbj.group_map` maps it. A step with no row in any
    book (e.g. one the reference runs from db.conf only) is asked: `mbj.missing_rows.<reference job>` =
    `from:<reference job of the same instrument>` (that row's values; the group from the step's own db.conf line) or
    `<OPEN - what, who>` (the job is built, its row left out of the SQL, exit 4) [operator, 2026-10-21].
  - `test_values`: the input fields given for a test only -> the report and the SQL say TEST, the rehearsal and config
    blocks stop at their first statement, exit 4; stage_target_pr.py refuses the run [operator, 2026-10-21].
  - `unix.existing_scripts`: the Unix scripts already in the target's etc folder (not reported missing).
  - the core call's branch argument is the target wrapper's branch constant (`target.branch_const`, checked in the FE
    run's J-E4 CSV and against the FE run's), never the PK typed in [BOX team via operator, 2026-10-22].
Readiness (never blocking): the MBJ engine BOX_ACC.PKG_BATCHPROCESS_MBJ must be deployed in the target
(`readiness.mbj_engine`); the verify file checks it. Exit 0 written · 4 written with OPEN lines · 1 refused.
Standard library only.
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
import build_fe_jobs as bfj  # noqa: E402
import parse_job_confs as pjc  # noqa: E402
import unix_package  # noqa: E402
from find_jobs import ALIASES  # noqa: E402

INPUTS = "acc-jobs-inputs.json"
OUT = "out"
PENDING = "pending-questions.md"
FAMILY = {"generic": "0", "depos": "1", "commodities": "2", "irs": "3", "ccs": "4", "cfm": "5", "fra": "6", "otc": "7",
          "cap": "8", "cds": "9"}   # GMBX9 = CDS [read: SLB MBJ rows, 2026-10-21]
NEW_RE = re.compile(r"^GMBX(\d)([A-Z]{2})(\d{2})D(\d{2})$")
LABEL_CODE_RE = re.compile(r"^X([A-Z]{2,3})(\d{2})$")
MBJ_TABLE = "T_BOX_MBJ_PROPERTIES_S"
MBJ_OWNER_OBJ = "35000182.65"   # BOX - MBJ Properties, same object in both tiers [J-T8, 2026-10-01]
MBJ_NUM = ["FK_EXTENSION", "WORKERS", "MONITOR_FILE_MAX_DAYS"]
MBJ_TXT = ["INSTANZE", "CONCURRENT_EVENTS", "CONCURRENT_EVENTS_DEPENDENCY", "TASKS_PER_WORKER", "WORKERS_BY_EVENTS",
           "MIC_FILE_TYPE", "MIC_EOD", "MIC_FLOW_MODE", "MONITOR_TYPES", "MONITOR_FILE_PATTERN", "RETURN_DATA",
           "RECOVER_MANUAL_MOVS", "RECOVER_RECLASSIFICATION_MOVS", "RECOVER_REGULARIZATION_MOVS"]
SENDER = {"reference", "lastly", "none"}
REQUIRED = {
    "reference.env_folder": "the reference environment folder with its db.conf and shell.conf (runs/_reference/<env>/)",
    "reference.controlm_json": "the reference branch's ACC Control-M JSON (registry acc_controlm_repo: projects/<repo>.json)",
    "reference.token": "the reference branch's token (registry)",
    "reference.wrapper_owner": "the reference wrapper owner (registry)",
    "reference.display": "the reference branch's display name (registry)",
    "reference.books_csv": "J-R3b in the reference tier (the reference's book labels)",
    "reference.mbj_csv": "J-R2: the reference branch's MBJ rows (BOX_ACC.T_BOX_MBJ_PROPERTIES_S) as CSV",
    "instrument": "the instrument(s) to build (registry column instruments minus the skip ones)",
    "target.branch_code": "the target branch code (registry)",
    "target.token": "the target branch token (registry)",
    "target.display": "the target branch display name",
    "target.branch_pk": "the target branch PK (J-E4: the branch constant's value)",
    "target.branch_const": "the target branch constant in its wrapper (J-E4; registry dbconf_branch_const) - the core call's branch argument",
    "target.wrapper_owner": "the target wrapper owner (registry)",
    "target.books_register": "the target's books register (skill set-up-book-labels)",
    "target.fe_run": "the branch's finished box-fe-jobs-agent run of this environment that built every instrument of "
                     "this run (its out/acc-handoff.json names the Initial Accounting jobs)",
    "controlm.folder_name": "the target's ACC Control-M folder name",
    "controlm.ControlmServer": "the ACC folder's Control-M server (the folder file carries the DEV one)",
    "controlm.SiteStandard": "the ACC folder's site standard",
    "controlm.OrderMethod": "the ACC folder's order method (DEV file)",
    "controlm.Host": "the DEV host of the target's ACC jobs",
    "controlm.FilePath": "the target's job scripts folder (e.g. /gmny/scripts)",
    "controlm.RunAs": "the target's run-as user",
    "controlm.Application": "the target's ACC Control-M Application",
    "controlm.MonthDaysCalendar": "the target's Control-M calendar",
    "controlm.CreatedBy": "the job-owner ID for the target (or `omit`)",
    "mbj.calendar": "the calendar PK for the target's MBJ rows (PGT_STC.T_PGT_CALENDAR_S) - the reference's rows use a "
                    "processing calendar, not the branch's: BOX expert",
    "mbj.pk_call": "how a T_BOX_MBJ_PROPERTIES_S PK is allocated, with {table} for the table name (SIGOM's own: "
                   "box-acc-model.md section 6, P_SETHEADER / F_GetPK) - BOX dev to confirm",
    "mbj.auth_code": "the target installation's auth code (GOM_GLB_SYS.T__CORE_INFO_S, Q-G3c)",
}


class Result(bfj.Result):
    pass


def get(d, path):
    return bfj.get(d, path)


def undecided(v) -> bool:
    return bfj.undecided(v)


def conf_lines(path: Path) -> dict:
    """{job: (line number, text)} of the active lines of a db.conf / shell.conf (a job's first active line)."""
    out = {}
    if not path.exists():
        return out
    for i, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = pjc.JOB_RE.match(s)
        if m and m.group(1) not in out:
            out[m.group(1)] = (i, s)
    return out


def call_args(line: str):
    """(procedure, [arguments]) of a db.conf line's call."""
    m = re.match(r"^([^:]+):([^:]*):([^:]*):(.*)$", line)
    if not m:
        return "", []
    cm = pjc.CALL_RE.search(m.group(4))
    if not cm:
        return "", []
    body = m.group(4)[cm.end():]
    depth, end = 1, len(body)
    for i, ch in enumerate(body):
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0:
            end = i
            break
    return cm.group(1) + cm.group(2), pjc.split_args(body[:end])


def read_csv_upper(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append({(k or "").strip().upper(): (v or "").strip() for k, v in r.items()})
    return rows


def sql_txt(v) -> str:
    v = "" if v is None else str(v)
    if v == "" or v.lower() == "(null)":
        return "NULL"
    return "'" + v.replace("'", "''") + "'"


def sql_num(v) -> str:
    v = "" if v is None else str(v).strip()
    if v == "" or v.lower() == "(null)":
        return "NULL"
    if not re.fullmatch(r"-?\d+(\.\d+)?", v):
        raise ValueError(v)
    return v


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or not Path(argv[0]).is_dir():
        print("usage: build_acc_jobs.py <runs/<BRANCH>/<tier>-<env>/acc-jobs/<run>/>", file=sys.stderr)
        return 2
    folder = Path(argv[0])
    res = Result()
    rc = build(folder, res)
    print(f"\nbuild_acc_jobs - {folder}\n" + "=" * 72)
    for c, w, m in res.errors:
        print(f"  REFUSED {c:<30} {w}: {m}")
    for c, w, m in res.warns:
        print(f"  WARN    {c:<30} {w}: {m}")
    bad_out = any(c == "excluded-book-built" for c, *_ in res.errors)
    print(("  wrote out/ - see out/report.md" if rc in (0, 4) else "  out/ written but NOT to be used (see REFUSED)"
           if bad_out else "  nothing written") + "\n" + "=" * 72)
    return rc


def build(folder: Path, res: Result) -> int:
    if (folder / ".frozen").exists():
        res.err("run-frozen", str(folder), "this run is finished (.frozen) - start a new version: scripts/new_run.py")
        return 1
    ip = folder / INPUTS
    if not ip.exists():
        res.err("inputs-missing", INPUTS, "copy agents/box-acc-jobs-agent/templates/acc-jobs-inputs.example.json here "
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
    rc = build_run(folder, cfg, res)
    if rc in (0, 4) and bfj.excluded_built(folder, cfg, folder / OUT, res):
        return 1
    return rc


def build_run(folder: Path, cfg: dict, res: Result) -> int:  # noqa: C901 - one pass, in the order the files are written
    ref, tgt, cm = cfg["reference"], cfg["target"], cfg["controlm"]
    mic, mbjc = cfg.get("mic") or {}, cfg.get("mbj") or {}
    renames, ext = cfg.get("renames") or {}, cfg.get("external_events") or {}
    rt, tt = str(ref["token"]), str(tgt["token"])
    prods = [ALIASES.get(str(x).lower(), str(x).lower()) for x in bfj._as_list(cfg["instrument"])]
    for p in prods:
        if p not in FAMILY or p == "generic":
            res.err("instrument-unknown", f"{INPUTS}.instrument", f"{p!r} - one of {', '.join(k for k in FAMILY if k != 'generic')}")
    today = datetime.date.today().strftime("%Y%m%d")

    # --- reference: confs, ACC folder, FE folder, MBJ rows, books -------------------------------------------------
    envd = bfj.resolve(folder, ref["env_folder"])
    dbl, shl = conf_lines(envd / "db.conf"), conf_lines(envd / "shell.conf")
    if not dbl and not shl:
        res.err("reference-confs-missing", f"{INPUTS}.reference.env_folder", f"{envd}: no db.conf / shell.conf")
    cmp_ = bfj.resolve(folder, ref["controlm_json"])
    if not cmp_.exists():
        res.err("controlm-missing", f"{INPUTS}.reference.controlm_json", f"{cmp_} not found - attach the reference "
                "branch's ACC Control-M repo")
        return 1
    rname, rheader, rjobs, rjline = bfj.load_folder(cmp_)
    if not rjobs:
        res.err("controlm-not-folder", str(cmp_), "no SimpleFolder with Job:* entries")
        return 1
    fe_ref_jobs = set()
    if not undecided(ref.get("fe_controlm_json")):
        fp = bfj.resolve(folder, ref["fe_controlm_json"])
        if fp.exists():
            fe_ref_jobs = set(bfj.load_folder(fp)[2])
        else:
            res.warn("fe-controlm-missing", str(fp), "not found - FE waits recognised by name only")
    mp = bfj.resolve(folder, ref["mbj_csv"])
    if not mp.exists():
        res.err("mbj-csv-missing", f"{INPUTS}.reference.mbj_csv", f"{mp} - J-R2 (the reference's MBJ rows) as CSV")
        return 1
    mbj = {r.get("JOB_NAME", "").upper(): r for r in read_csv_upper(mp) if r.get("JOB_NAME")}
    if not mbj:
        res.err("mbj-csv-empty", str(mp), "no JOB_NAME rows")
        return 1
    rbp = bfj.resolve(folder, ref["books_csv"])
    rbooks = {}
    if rbp.exists():
        for r in read_csv_upper(rbp):
            m = LABEL_CODE_RE.match(r.get("CODE", ""))
            if m and m.group(1) == rt:
                rbooks[m.group(2)] = r.get("DESCRIPTION", "")
    else:
        res.err("reference-books-missing", f"{INPUTS}.reference.books_csv", f"{rbp} - J-R3b in the reference tier")

    # --- target books (register minus excluded) -------------------------------------------------------------------
    regp = bfj.resolve(folder, tgt["books_register"])
    tbooks = []
    if not regp.exists():
        res.err("books-missing", f"{INPUTS}.target.books_register", f"{regp} - skill set-up-book-labels")
    else:
        for r in csv.DictReader(regp.open(encoding="utf-8")):
            if r.get("kind") != "book":
                continue
            m = LABEL_CODE_RE.match(r.get("code", ""))
            if not m or m.group(1) != tt:
                res.err("book-code-bad", str(regp), f"{r.get('code')!r} (target token {tt})")
                continue
            tbooks.append({"no": m.group(2), "code": r["code"], "desc": r.get("description", ""),
                           "status": r.get("status", "")})
            if r.get("status") != "exists":
                res.warn("book-label-pending", str(regp), f"{r['code']} is {r.get('status')!r} - its MBJ rows look the "
                         "label up by code: the SQL stops until the label exists")
    exp_ = bfj.resolve(folder, tgt["books_excluded"]) if not undecided(tgt.get("books_excluded")) \
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
            excluded.append(c)
        tbooks = [b for b in tbooks if b["code"] not in excluded]
    if not tbooks and regp.exists():
        res.err("books-missing", str(regp), "no book rows")

    # --- the FE agent's run: hand-off (Initial Accounting) and FE jobs - REQUIRED [operator, 2026-10-21] -------------
    # Which FE run: the one in target.fe_run, chosen by the operator (prompts/build.md Step 2) - never picked here. It
    # must cover every instrument of this run, hold out/acc-handoff.json and expect the same ACC folder.
    handoff, fe_tgt_jobs = {}, set()
    fe_run = bfj.resolve(folder, tgt["fe_run"])
    hp = fe_run / "out" / "acc-handoff.json"
    fip = fe_run / bfj.INPUTS
    if not fe_run.is_dir() or not fip.exists():
        res.err("fe-run-missing", f"{INPUTS}.target.fe_run", f"{fe_run} is not a box-fe-jobs-agent run (no "
                f"{bfj.INPUTS}) - give the branch's finished FE jobs run of this environment")
    elif not hp.exists():
        res.err("handoff-missing", str(hp), "the FE run has no out/acc-handoff.json - build it (build_fe_jobs.py) first")
    else:
        fe_cfg = json.loads(fip.read_text(encoding="utf-8-sig"))
        fe_prods = {ALIASES.get(str(x).lower(), str(x).lower()) for x in bfj._as_list(fe_cfg.get("instrument"))}
        miss = [p for p in prods if p not in fe_prods]
        if miss:
            res.err("fe-run-instruments-missing", f"{INPUTS}.target.fe_run", f"{fe_run.name} built "
                    f"{', '.join(sorted(fe_prods)) or 'nothing'}; this run also needs {', '.join(miss)} - give the FE run "
                    "that built every instrument of this run (they are built in one FE run)")
        if not (fe_run / ".frozen").exists():
            res.warn("fe-run-not-frozen", str(fe_run), "the FE run is not finished (.frozen): its out/ may still change")
        fe_bc = (fe_cfg.get("target") or {}).get("branch_const")
        if not undecided(fe_bc) and str(fe_bc).upper() != str(tgt["branch_const"]).upper():
            res.err("branch-const-mismatch", f"{INPUTS}.target.branch_const", f"{tgt['branch_const']}, but the FE run "
                    f"passes {fe_bc} - the two agents must pass the same branch constant")
        bfj.branch_const_check(fe_run / "01-evidence" / "J-E4-wrapper-TGT.csv", str(tgt["branch_const"]), res,
                               f"{INPUTS}.target.branch_const")
        for h in json.loads(hp.read_text(encoding="utf-8")).get("initial_accounting", []):
            handoff[h["reference_job"]] = h
            af = h.get("acc_folder")
            if undecided(af):
                res.warn("acc-folder-unchecked", h.get("target_job", "?"), "the FE run did not know the ACC folder "
                         f"(acc.folder_name) - this run's is {cm['folder_name']}: check they agree")
            elif str(af) != str(cm["folder_name"]):
                res.err("acc-folder-mismatch", f"{INPUTS}.controlm.folder_name", f"{cm['folder_name']}, but the FE run "
                        f"put {h.get('target_job')} in {af} (its acc.folder_name) - the two agents must name the same folder")
        for f in sorted((fe_run / "out").glob("*.json")):
            try:
                _, _, jj, _ = bfj.load_folder(f)
            except (ValueError, AttributeError, json.JSONDecodeError):
                continue
            fe_tgt_jobs |= set(jj)
    ia_groups = {str(x) for x in bfj._as_list(get(cfg, "initial_accounting.group")) if not undecided(x)} or {"2409.65"}

    def group_of(j):
        ln = dbl.get(j)
        if not ln:
            return ""
        _, a = call_args(ln[1])
        return a[0].strip() if a else ""

    def is_ia(j):
        return j in handoff or group_of(j) in ia_groups

    def parse(j):
        m = NEW_RE.match(j)
        return (m.group(1), m.group(2), m.group(3), m.group(4)) if m else None

    def ended(j):
        w = rjobs.get(j, {}).get("When")
        return isinstance(w, dict) and str(w.get("EndDate") or "99991231") < today

    producer = defaultdict(set)
    for j, o in rjobs.items():
        for e in bfj.added_events(o):
            producer[bfj.split_event(e)[1]].add(j)

    if res.errors:
        return 1

    # --- per instrument: template book, included jobs, MIC decision -----------------------------------------------
    tbmap = ref.get("template_book") if isinstance(ref.get("template_book"), dict) else \
        ({p: ref.get("template_book") for p in prods} if not undecided(ref.get("template_book")) else {})
    plan = {}          # p -> dict(n, tb, include[list], ia[list], dropped[set], eod[list], sender)
    fam_of_prod = {FAMILY[p]: p for p in prods}
    for p in prods:
        n = FAMILY[p]
        counts = defaultdict(int)
        for j in rjobs:
            q = parse(j)
            if q and q[0] == n and q[1] == rt and q[2] not in ("00", "99") and not ended(j):
                counts[q[2]] += 1
        if not counts:
            res.err("nothing-to-copy", p, f"no GMBX{n}{rt}<book>D.. job in {rname} - the reference does not run {p} "
                    "ACC jobs: mark it skip")
            continue
        tb = str(tbmap.get(p) or "").zfill(2) if tbmap.get(p) else ""
        if not tb:
            best = max(counts.values())
            tb = max(b for b, c in counts.items() if c == best)
            res.warn("template-book-chosen", p, f"book {tb} ({best} ACC jobs; per book: "
                     + ", ".join(f"{b}={c}" for b, c in sorted(counts.items())) + ") - confirm with the operator")
        elif tb not in counts:
            res.err("template-book-unusable", f"{INPUTS}.reference.template_book.{p}", f"book {tb} has no GMBX{n}{rt}"
                    f"{tb}D.. job in {rname} (books with jobs: {', '.join(sorted(counts))})")
            continue
        seed = [j for j in rjobs if (q := parse(j)) and q[0] == n and q[1] == rt and q[2] in (tb, "00")
                and not ended(j)]
        include, ia, seen, stack = [], [], set(), list(seed)
        while stack:
            j = stack.pop(0)
            if j in seen:
                continue
            seen.add(j)
            if is_ia(j):
                ia.append(j)
                continue
            q = parse(j)
            if q and (q[0] != n and q[0] != "0"):
                continue                                   # another instrument's job: mapped at wait time
            if q and q[2] not in (tb, "00"):
                continue                                   # another book's step: "every book" at wait time
            include.append(j)
            for it in bfj.event_items(rjobs[j].get("eventsToWaitFor", {})):
                for e in producer.get(bfj.split_event(it["Event"])[1], ()):
                    if e not in seen and not ended(e):
                        stack.append(e)
        eod = [j for j in include if (mbj.get(j, {}).get("MIC_EOD") == "1") or (j not in mbj and parse(j)
               and parse(j)[3] in ("12", "13"))]
        d = mic.get(p) if isinstance(mic.get(p), dict) else {}
        steps_txt = ", ".join(sorted({(parse(j)[2] == "00" and "00D" or "<book>D") + parse(j)[3] for j in eod
                                      if parse(j)})) or "none"
        dropped = set()
        if eod:
            v = str(d.get("eod_steps") or "").strip().lower()
            if v not in ("keep", "drop"):
                res.err("mic-decision-missing", f"{INPUTS}.mic.{p}.eod_steps", f"the reference's {p} has MIC "
                        f"end-of-day steps ({steps_txt}; MBJ MIC_EOD = 1): `keep` or `drop` for the target? (BOX expert)")
            elif v == "drop":
                dropped = set(eod)
        else:
            v = str(d.get("eod_steps") or "").strip().lower()
            if v != "none":
                res.err("mic-decision-missing", f"{INPUTS}.mic.{p}.eod_steps", f"the reference's {p} has NO MIC "
                        "end-of-day steps (D12 / D13): answer `none` (the target gets none - adding them is the BOX "
                        "team's change, not a copy)")
        snd = str(d.get("sender_type") or "").strip().lower()
        ref_snd = sorted({mbj[j].get("MIC_SENDER_TYPE", "") or "(empty)" for j in include if j in mbj})
        if snd not in SENDER:
            res.err("mic-decision-missing", f"{INPUTS}.mic.{p}.sender_type", f"MIC_SENDER_TYPE of the target's {p} "
                    f"MBJ rows: `reference` (as each copied row: {', '.join(ref_snd) or 'none'}), `lastly` or `none`? "
                    "(BOX expert)")
        plan[p] = {"n": n, "tb": tb, "include": [j for j in include if j not in dropped], "ia": ia,
                   "dropped": dropped, "eod": eod, "sender": snd, "all": include}
    if res.errors:
        return 1

    # --- target names ---------------------------------------------------------------------------------------------
    names = {}          # reference job -> {book_no or None: target job}
    kind = {}           # reference job -> "book" | "branch" | "ia"
    prod_of = {}
    q_ren = []
    for p, pl in plan.items():
        n = pl["n"]
        for j in pl["ia"]:
            h = handoff.get(j)
            if not h:
                res.err("ia-not-in-handoff", j, f"the reference's Initial Accounting job for {p} is not in the FE run's "
                        "acc-handoff.json - the FE run did not build it (rebuild the FE jobs with this instrument)")
                continue
            names[j], kind[j], prod_of[j] = {None: h["target_job"]}, "ia", p
        for j in pl["include"]:
            q = parse(j)
            prod_of[j] = p
            if q and q[2] != "00":
                kind[j] = "book"
                names[j] = {b["no"]: f"GMBX{q[0]}{tt}{b['no']}D{q[3]}" for b in tbooks}
            elif q:
                kind[j], names[j] = "branch", {None: f"GMBX{q[0]}{tt}00D{q[3]}"}
            else:
                kind[j] = "branch"
                t = renames.get(j)
                if undecided(t):
                    sib = sorted({f"GMBX{n}{tt}00D{parse(x)[3]}" for x in rjobs if parse(x) and parse(x)[2] == "00"
                                  and parse(x)[1] == rt and group_of(x) and group_of(x) == group_of(j)})
                    sug = sib[0] if sib else f"GMBX{n}{tt}00D<ss>"
                    res.err("rename-missing", f"{INPUTS}.renames.{j}", f"old-named reference job ({group_of(j) or 'no '}"
                            f"db.conf group) - its new-convention name for the target (suggested: {sug}, the step its "
                            "siblings of the same group use)")
                    q_ren.append((j, sug))
                    continue
                names[j] = {None: str(t)}
    all_targets = defaultdict(list)
    for j, m in names.items():
        for t in m.values():
            all_targets[t].append(j)
    for t, js in all_targets.items():
        if len(js) > 1:
            res.err("target-name-duplicate", t, f"built from {', '.join(sorted(js))}")
    if not undecided(tgt.get("env_folder")):
        te = bfj.resolve(folder, tgt["env_folder"])
        used = set(conf_lines(te / "db.conf")) | set(conf_lines(te / "shell.conf"))
        for t in all_targets:
            if t in used and not any(kind.get(j) == "ia" for j in all_targets[t]):
                res.err("target-name-exists", t, f"already in {te}'s confs - rename it (renames) or check the target")

    # --- waits ----------------------------------------------------------------------------------------------------
    q_ext, ph_events, review, fe_unchecked = {}, [], [], set()

    def tmpl_equiv(j):
        """A per-book job of another reference book -> the template book's job of the same step."""
        q = parse(j)
        if not q:
            return None
        p = fam_of_prod.get(q[0])
        if not p:
            return None
        return f"GMBX{q[0]}{rt}{plan[p]['tb']}D{q[3]}" if p in plan else None

    def map_event(e: str, book, owner: str, _seen=frozenset()) -> list[str]:
        pre, j, suf = bfj.split_event(e)
        if j in _seen:
            return []
        q = parse(j)
        if j in names:
            if kind[j] == "book":
                return [f"{pre}{t}{suf}" for b, t in names[j].items() if book is None or b == book]
            return [f"{pre}{names[j][None]}{suf}"]
        drop_src = next((pl for pl in plan.values() if j in pl["dropped"]), None)
        if drop_src is not None or (q and q[1] == rt and j in rjobs and q[0] != "0"
                                    and fam_of_prod.get(q[0]) is None):
            out = []                                       # a dropped job, or another instrument's not in the run:
            for it in bfj.event_items(rjobs.get(j, {}).get("eventsToWaitFor", {})):   # its own waits
                out += map_event(it["Event"], book, owner, _seen | {j})
            review.append(f"`{owner}`: wait on `{j}` replaced by its own waits ({'dropped' if drop_src else 'instrument not in the run'})")
            return out
        if q and q[1] == rt and j in rjobs:                # same instrument, another reference book's step
            eq = tmpl_equiv(j)
            if eq and eq in names:
                if book is not None:
                    res.err("reference-cross-book-wait", owner, f"{owner}'s reference job waits for another book's "
                            f"`{j}` - a reference defect: never copied (BOX team)")
                    return []
                return [f"{pre}{t}{suf}" for t in names[eq].values()]
            if eq and any(eq in pl["dropped"] for pl in plan.values()):
                return map_event(f"{pre}{eq}{suf}", book, owner, _seen | {j})
            review.append(f"`{owner}`: wait on `{j}` dropped - the template book has no such step")
            return []
        if j not in rjobs and (j in fe_ref_jobs or (q and q[1] == rt)):    # an FE job (another folder)
            if not q:
                res.err("fe-wait-old-named", owner, f"waits for FE job `{j}` (old name) - answer it in external_events")
                return []
            if q[2] == "00":
                tj = [f"GMBX{q[0]}{tt}00D{q[3]}"]
            elif book is not None:
                if q[2] not in {pl["tb"] for pl in plan.values()}:
                    res.err("reference-cross-book-wait", owner, f"waits for another book's FE job `{j}`")
                    return []
                tj = [f"GMBX{q[0]}{tt}{book}D{q[3]}"]
            else:
                tj = [f"GMBX{q[0]}{tt}{b['no']}D{q[3]}" for b in tbooks]
            for t in tj:
                if fe_tgt_jobs and t not in fe_tgt_jobs:
                    fe_unchecked.add(t)
            return [f"{pre}{t}{suf}" for t in tj]
        ans = ext.get(e)
        if bfj.unanswered_event(ans):
            q_ext.setdefault(e, set()).add(owner)
            return []
        a = str(ans).strip()
        if a.upper() == "KEEP":
            if j.startswith("GMBX") and q and q[1] == rt:
                res.err("keep-reference-event", e, "the reference branch's own event cannot be kept")
            return [e]
        if a.upper() == "DROP":
            return []
        if a.upper() == "DROP-REVIEW":
            review.append(f"`{owner}`: wait on `{e}` dropped (DROP-REVIEW)")
            return []
        if bfj.undecided(a) or "{" in a:
            ph_events.append((e, a))
        return [a]

    def remap_list(v, book, owner):
        groups, cur = [], []
        for x in v:
            if isinstance(x, str) and x.strip().upper() == "OR":
                groups.append(cur)
                cur = []
            else:
                cur.append(x)
        groups.append(cur)
        out_g, keys = [], []
        for g in groups:
            out, seen = [], set()
            for x in g:
                if isinstance(x, dict) and isinstance(x.get("Event"), str):
                    for ne in map_event(x["Event"], book, owner):
                        if ne not in seen:
                            seen.add(ne)
                            y = dict(x)
                            y["Event"] = ne
                            out.append(y)
                else:
                    out.append(x)
            key = tuple(sorted(json.dumps(y, sort_keys=True) for y in out))
            if out and key not in keys:
                keys.append(key)
                out_g.append(out)
        r_ = []
        for i, g in enumerate(out_g):
            r_ += (["OR"] if i else []) + g
        return r_

    def rename_own(node, j, t):
        """Every event of the job itself (eventsToAdd, If blocks: Event:Add / Event:Delete, -NOK) renamed."""
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if k == "eventsToWaitFor":
                    continue
                if k == "Event" and isinstance(v, str):
                    pre, jj, suf = bfj.split_event(v)
                    if jj == j:
                        node[k] = f"{pre}{t}{suf}"
                else:
                    rename_own(v, j, t)
        elif isinstance(node, list):
            for v in node:
                rename_own(v, j, t)

    def set_created_by(o):
        """controlm.CreatedBy: `omit` -> removed, else the answer - on every job, the hand-off drafts too [2026-10-21]."""
        if str(cm["CreatedBy"]).strip().lower() == "omit":
            o.pop("CreatedBy", None)
        else:
            o["CreatedBy"] = cm["CreatedBy"]

    def make_job(j, t, book):
        o = copy.deepcopy(rjobs[j])
        o["FileName"] = t
        for k in ("Host", "RunAs", "FilePath", "Application"):
            if k in o or k in ("Host", "Application"):
                o[k] = cm[k]
        set_created_by(o)
        if isinstance(o.get("When"), dict):
            o["When"].pop("EndDate", None)
            o["When"]["MonthDaysCalendar"] = cm["MonthDaysCalendar"]
        if isinstance(o.get("Description"), str):
            dsc = o["Description"]
            q = parse(j)
            if book is not None and q and rbooks.get(q[2]):
                tbk = next((b for b in tbooks if b["no"] == book), None)
                if tbk:
                    dsc = dsc.replace(rbooks[q[2]], tbk["desc"])
            o["Description"] = re.sub(r"\b" + re.escape(ref["display"]) + r"\b", tgt["display"], dsc)
        rename_own(o, j, t)
        w = o.get("eventsToWaitFor")
        if isinstance(w, dict) and isinstance(w.get("Events"), list):
            w["Events"] = remap_list(w["Events"], book, t)
            if not w["Events"]:
                o.pop("eventsToWaitFor")
        return o

    # --- the folder -----------------------------------------------------------------------------------------------
    jobs_out, mapping = {}, []
    for p, pl in plan.items():
        for j in pl["ia"]:
            if j not in names:                             # not in the hand-off: refused above
                continue
            t = names[j][None]
            h = handoff.get(j)
            if h and isinstance(h.get("draft_job"), dict):
                o = copy.deepcopy(h["draft_job"])
                for k in ("Host", "RunAs", "FilePath", "Application"):
                    o[k] = cm[k]
                set_created_by(o)
                if isinstance(o.get("When"), dict):
                    o["When"]["MonthDaysCalendar"] = cm["MonthDaysCalendar"]
                src = "acc-handoff.json (draft job)"
            else:
                o = make_job(j, t, None)
                src = f"{rname} (no hand-off draft)"
            jobs_out[t] = o
            mapping.append({"instrument": p, "reference_job": j, "target_job": t, "level": "initial-accounting",
                            "book": "", "runs_from": "db.conf (box-fe-jobs-agent)", "mbj_row_from": "", "note": src})
    for p, pl in plan.items():
        order = sorted(pl["include"], key=lambda j: (kind[j] == "branch", parse(j)[3] if parse(j) else "99", j))
        for b in tbooks:
            for j in [x for x in order if kind[x] == "book"]:
                jobs_out[names[j][b["no"]]] = make_job(j, names[j][b["no"]], b["no"])
        for j in [x for x in order if kind[x] == "branch" and x in names]:
            jobs_out[names[j][None]] = make_job(j, names[j][None], None)
    if q_ext:
        for e, owners in sorted(q_ext.items()):
            emitter = ", ".join(sorted(producer.get(bfj.split_event(e)[1], set()))) or "not in the ACC folder"
            res.err("external-event-unmapped", f"{INPUTS}.external_events.{e}", f"waited for by "
                    f"{', '.join(sorted(owners)[:4])}{' ...' if len(owners) > 4 else ''}; emitter: {emitter}")
    if res.errors:
        _pending(folder, q_ren, q_ext, producer)
        return 1

    # --- confs ----------------------------------------------------------------------------------------------------
    pattern = next((s for _, s in shl.values() if re.search(r"\bmbjbox\.sh\b", s)), None)
    core_call = tgt.get("core_call") if not undecided(tgt.get("core_call")) else "PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup"
    core_time = tgt.get("core_time") if not undecided(tgt.get("core_time")) else bfj.TIME_ARG
    cmap = tgt.get("constants") if isinstance(tgt.get("constants"), dict) else {}
    cvals = tgt.get("constant_values") if isinstance(tgt.get("constant_values"), dict) else {}
    shell_blocks, db_blocks, shell_jobs = [], [], []
    for p, pl in plan.items():
        sh, db = [], []
        for j in pl["include"]:
            if j not in names:
                continue
            per_book = kind[j] == "book"
            form = "shell" if per_book or j in shl else ("db" if j in dbl else "")
            if not form:
                res.err("no-conf-line", j, "branch-level job with no db.conf / shell.conf line in the reference")
                continue
            for b, t in names[j].items():
                if form == "shell":
                    src = shl.get(j, (0, None))[1]
                    if src is None:
                        review.append(f"`{j}`: the reference runs it from {'db.conf' if j in dbl else 'no conf line'} - "
                                      "built as shell.conf (mbjbox.sh) + MBJ row, the target's form")
                        if not pattern:
                            res.err("shell-pattern-missing", j, "no mbjbox.sh line in the reference shell.conf to copy")
                            continue
                        src, pj = pattern, pjc.JOB_RE.match(pattern).group(1)
                    else:
                        pj = j
                    line = src.replace(pj, t)
                    if "mbjbox.sh" not in line:
                        res.err("shell-not-mbj", j, f"its shell.conf line does not run mbjbox.sh: {src[:80]}")
                        continue
                    sh.append(line)
                    shell_jobs.append((p, j, t, b))
                else:
                    proc, a = call_args(dbl[j][1])
                    if len(a) < 4:
                        res.err("dbconf-unreadable", j, f"db.conf:{dbl[j][0]} - {proc}")
                        continue
                    a += ["NULL"] * (7 - len(a))
                    g, _, dt, ins, mode, lab, sub = a[:7]
                    if re.search(r"f_getPKByLabel", lab, re.I):
                        res.err("label-on-branch-job", j, "a branch-level db.conf job passing a label")
                        continue
                    ins = re.sub(r"\b" + re.escape(ref["wrapper_owner"]) + r"\.", tgt["wrapper_owner"] + ".", ins, flags=re.I)
                    for c in sorted({c.upper() for c in bfj.CONST_RE.findall(ins)}):
                        if c == "CST_PK_VACIO":
                            continue
                        new = cmap.get(c)
                        if isinstance(new, str) and new.strip().upper() == "SAME":
                            continue
                        if undecided(new):
                            res.err("constant-unmapped", f"{INPUTS}.target.constants.{c}", f"{c} (in {j}) - its name in "
                                    f"{tgt['wrapper_owner']}.PKG_GMBATCHPROCESS (J-E4 in the target), or SAME")
                            continue
                        ins = re.sub(r"\b" + re.escape(c) + r"\b", new, ins, flags=re.I)
                    ins = "NULL" if re.search(r"\bCST_PK_VACIO\b", ins, re.I) else ins
                    mc = re.search(r"\b(CST_[A-Z0-9_]+)\s*$", mode, re.I)
                    vst = mode
                    if mc:
                        vst = cvals.get(mc.group(1).upper())
                        if undecided(vst):
                            res.err("constant-value-missing", f"{INPUTS}.target.constant_values.{mc.group(1).upper()}",
                                    f"the value of {mc.group(1)} (the core call's P_VSTATIC, by value)")
                            continue
                    db.append(f"{t}:T:P:{core_call}({g}, {bfj.branch_arg(tgt)}, {dt}, {ins}, {core_time}, {vst}, NULL, NULL);")
        if sh:
            shell_blocks += [f"########## BOX - {tgt['branch_code']} - ACC - {p} - MBJ (from {rt}, book {pl['tb']}) "
                             "##########", *sh]
        if db:
            db_blocks += [f"########## BOX - {tgt['branch_code']} - ACC - {p} - branch level (from {rt}) ##########", *db]
    bad = bfj.dbconf_colon(db_blocks)
    if bad:
        res.err("dbconf-colon", f"{INPUTS}.target.core_time", f"{len(bad)} db.conf line(s) with a ':' inside the call "
                f"({', '.join(bad[:5])}): the runner keeps field 4 only - build the colons with CHR(58)")
    if res.errors:
        return 1

    # --- MBJ rows -------------------------------------------------------------------------------------------------
    gmap = mbjc.get("group_map") if isinstance(mbjc.get("group_map"), dict) else {}
    mrows = mbjc.get("missing_rows") if isinstance(mbjc.get("missing_rows"), dict) else {}
    rows, mbj_from, name_label, other_book, open_rows, own_group = [], {}, set(), {}, {}, {}
    for p, j, t, b in shell_jobs:
        q = parse(j)
        src = mbj.get(j)
        how = j
        if src is None and q:
            alts = sorted((x for x in mbj if (qq := parse(x)) and qq[0] == q[0] and qq[1] == rt and qq[3] == q[3]
                           and (qq[2] == "00") == (q[2] == "00")), reverse=True)
            if alts:
                src, how = mbj[alts[0]], alts[0]
                other_book.setdefault((j, alts[0]), []).append(t)     # one warning per step, not per book
        if src is None:
            # mbj.missing_rows.<reference job>: from:<reference job> | <OPEN - what, who> [operator, 2026-10-21]
            ans = mrows.get(j)
            if isinstance(ans, str) and ans.strip().upper().startswith("<OPEN"):
                open_rows.setdefault(j, (ans.strip(), []))[1].append(t)
                mbj_from[t] = "OPEN"
                continue
            if isinstance(ans, str) and ans.strip().lower().startswith("from:"):
                sj = ans.split(":", 1)[1].strip()
                sq = parse(sj)
                if sj not in mbj:
                    res.err("mbj-row-source-unknown", f"{INPUTS}.mbj.missing_rows.{j}", f"{sj} has no MBJ row in J-R2")
                    continue
                if not sq or not q or sq[0] != q[0]:
                    res.err("mbj-row-source-other-instrument", f"{INPUTS}.mbj.missing_rows.{j}",
                            f"{sj} is not a job of {j}'s instrument - its FK_INSTRUMENT would be wrong")
                    continue
                src, how = mbj[sj], sj
                if j not in own_group:
                    g_ = call_args(dbl[j][1])[1][:1] if j in dbl else []
                    own_group[j] = g_[0].strip() if g_ and re.fullmatch(r"\d+(\.\d+)?", g_[0].strip()) else None
                    res.warn("mbj-row-from-other-step", j, f"no MBJ row for {j}: values from {sj} (mbj.missing_rows), "
                             + (f"group {own_group[j]} from its own db.conf line" if own_group[j] else
                                f"group {src.get('GROUP_PK', '') or 'none'} from {sj} - BOX team to confirm"))
            else:
                res.err("mbj-row-missing", f"{INPUTS}.mbj.missing_rows.{j}", f"no MBJ row for {j} nor for its step in "
                        "another book (J-R2) - ask the BOX team: `from:<reference job>` (copy that row's values) or "
                        "`<OPEN - what, who>`")
                continue
        if q and q[2] != "00" and src.get("LABEL_CODE") and src["LABEL_CODE"] != f"X{rt}{parse(how)[2]}":
            name_label.add(f"`{how}` carries label `{src['LABEL_CODE']}` (not its name's book) - the target's row "
                              "takes its own book's label")
        if src.get("SUBLABEL_PK") not in ("", None, "(null)"):
            res.err("mbj-sublabel", how, "the reference row has a sub-label - not supported, BOX team")
            continue
        snd = plan[p]["sender"]
        grp = own_group.get(j) or src.get("GROUP_PK", "")
        row = {"JOB_NAME": t, "FK_INSTRUMENT": src.get("INSTR_PK", ""),
               "FK_GROUP": gmap.get(grp, grp),
               "LABEL": f"X{tt}{b}" if b else None,
               "MIC_SENDER_TYPE": src.get("MIC_SENDER_TYPE", "") if snd == "reference" else snd,
               **{c: src.get(c, "") for c in MBJ_NUM + MBJ_TXT}}
        if src.get("FK_OWNER_OBJ") and src["FK_OWNER_OBJ"] != MBJ_OWNER_OBJ:
            res.warn("mbj-owner-differs", how, f"FK_OWNER_OBJ {src['FK_OWNER_OBJ']} (expected {MBJ_OWNER_OBJ})")
        row["_from"] = how
        rows.append(row)
        mbj_from[t] = how
    for (j, alt), ts in other_book.items():
        q = parse(ts[0])
        w = f"GMBX{q[0]}{tt}<book>D{q[3]}" if q and len(ts) > 1 else ts[0]
        res.warn("mbj-row-from-other-book", w, f"{len(ts)} job(s): no MBJ row for {j}: values from {alt} (same step)")
    if res.errors:
        return 1
    try:
        sql = render_sql(cfg, rows, folder)
    except ValueError as e:
        res.err("mbj-value-not-number", "reference.mbj_csv", f"a numeric column holds {e}")
        return 1

    # --- write ----------------------------------------------------------------------------------------------------
    od = folder / OUT
    if od.exists():
        for f in sorted(od.rglob("*"), reverse=True):
            if "pr" in f.relative_to(od).parts[:1]:
                continue
            f.unlink() if f.is_file() else (f.rmdir() if not any(f.iterdir()) else None)
    od.mkdir(parents=True, exist_ok=True)
    header = {k: v for k, v in rheader.items() if k not in ("ControlmServer", "SiteStandard", "OrderMethod")}
    header.update({"ControlmServer": cm["ControlmServer"], "SiteStandard": cm["SiteStandard"],
                   "OrderMethod": cm["OrderMethod"]})
    header.setdefault("Type", "SimpleFolder")
    (od / f"{cm['folder_name']}.json").write_text(json.dumps({cm["folder_name"]: {**header, **jobs_out}}, indent=2,
                                                             ensure_ascii=False) + "\n", encoding="utf-8")
    shell_blocks = [re.sub(r"[/\[\]*]", "-", x) if x.startswith("##########") else x for x in shell_blocks]
    db_blocks = [re.sub(r"[/\[\]*]", "-", x) if x.startswith("##########") else x for x in db_blocks]
    (od / "shell.conf.proposal").write_text("\n".join(shell_blocks) + "\n", encoding="utf-8", newline="\n")
    if db_blocks:
        (od / "db.conf.proposal").write_text("\n".join(db_blocks) + "\n", encoding="utf-8", newline="\n")
    sd = od / "sql"
    sd.mkdir()
    for role, text in sql.items():
        (sd / f"{base_name(cfg, folder)}-mbj-{role}.sql").write_text(text, encoding="ascii", newline="\n")
    for p, pl in plan.items():
        for j in pl["include"]:
            for b, t in names.get(j, {}).items():
                form = "shell.conf (mbjbox.sh) + MBJ row" if kind[j] == "book" or j in shl else "db.conf (core call)"
                mapping.append({"instrument": p, "reference_job": j, "target_job": t, "level": kind[j],
                                "book": b or "", "runs_from": form, "mbj_row_from": mbj_from.get(t, ""), "note": ""})
        for j in sorted(pl["dropped"]):
            mapping.append({"instrument": p, "reference_job": j, "target_job": "", "level": "dropped",
                            "book": "", "runs_from": "", "mbj_row_from": "", "note": "MIC end-of-day: drop (mic decision)"})
    with (od / "mapping.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["instrument", "reference_job", "target_job", "level", "book", "runs_from",
                                          "mbj_row_from", "note"])
        w.writeheader()
        w.writerows(mapping)
    ux = cfg.get("unix") if isinstance(cfg.get("unix"), dict) else {}
    upk = unix_package.write(
        od / "unix", db_conf=(od / "db.conf.proposal") if db_blocks else None, shell_conf=od / "shell.conf.proposal",
        scripts=str(cm["FilePath"]) if undecided(ux.get("scripts_dir")) else str(ux["scripts_dir"]),
        templates=None if undecided(ux.get("templates_dir")) else str(ux["templates_dir"]),
        etc=None if undecided(ux.get("etc_dir")) else str(ux["etc_dir"]),
        ref_unix=bfj.resolve(folder, ux["reference_unix_dir"]) if not undecided(ux.get("reference_unix_dir")) else None,
        ref_etc=str(ux.get("reference_etc_dir") or "/appl/gm/etc"))
    if fe_unchecked:
        res.warn("fe-job-not-in-fe-run", f"{INPUTS}.target.fe_run", f"{len(fe_unchecked)} FE job(s) waited for are not "
                 f"in the FE run's out/: {', '.join(sorted(fe_unchecked)[:6])}")
    readiness = str(get(cfg, "readiness.mbj_engine") or "").strip().lower()
    if readiness != "deployed":
        res.warn("mbj-engine-not-ready", "readiness.mbj_engine", "BOX_ACC.PKG_BATCHPROCESS_MBJ "
                 + ("is NOT deployed in the target" if readiness == "not deployed" else "not confirmed in the target")
                 + " - the files are built; the jobs cannot run there until the BOX team deploys it (verify V2)")
    have = {str(x) for x in (ux.get("existing_scripts") or []) if not undecided(x)}   # already in the target's etc
    upk["have"] = sorted(m for m in upk["missing"] if m in have)
    upk["missing"] = [m for m in upk["missing"] if m not in have]
    tv = test_values(cfg)
    rc = 4 if ph_events or open_rows or tv else 0
    _report(od, cfg, plan, names, kind, mapping, rows, excluded, tbooks, review, ph_events, name_label, upk, readiness,
            handoff, rname, res, {"open_rows": open_rows, "test_values": tv})
    _pending(folder, [], {}, producer)
    return rc


def test_values(cfg: dict) -> list[str]:
    """`test_values`: the input fields the operator gave for a test only - the run is not deliverable [2026-10-21]."""
    v = cfg.get("test_values")
    return [str(x).strip() for x in (v if isinstance(v, list) else [v] if isinstance(v, str) else []) if str(x).strip()]


def base_name(cfg: dict, folder: Path) -> str:
    env = folder.resolve().parent.parent.name if folder.resolve().parent.name == "acc-jobs" else "env"
    return f"{cfg['target']['branch_code']}-{env}"


def render_sql(cfg: dict, rows: list[dict], folder: Path) -> dict:
    """The four SQL files of the MBJ rows. Every value from a reference row or an input, its source beside it."""
    tgt, mbjc = cfg["target"], cfg["mbj"]
    auth = str(mbjc["auth_code"]).strip()
    if not re.fullmatch(r"\d+", auth):
        raise ValueError(f"mbj.auth_code {auth!r}")
    pk_call = str(mbjc["pk_call"]).replace("{table}", MBJ_TABLE)
    cal = sql_num(mbjc["calendar"])
    base = base_name(cfg, folder)
    jobs = [r["JOB_NAME"] for r in rows]
    jl = ",\n    ".join(", ".join(f"'{j}'" for j in jobs[i:i + 6]) for i in range(0, len(jobs), 6))
    head = [
        "SET DEFINE OFF",
        "-- ============================================================================",
        f"-- {tgt['branch_code']} - BOX ACC MBJ rows (BOX_ACC.{MBJ_TABLE}) - {base}",
        "-- Rendered by scripts/build_acc_jobs.py (box-acc-jobs-agent). Never edit: change the inputs and build again.",
        "-- Run order (operator / BOX team): 1 rehearsal (ROLLBACK), 2 config (COMMIT), 3 verify (read-only),",
        "-- 4 rollback (ONLY to undo 2). Any error stops the block and Oracle undoes everything it did.",
        f"-- PKs: {pk_call} (mbj.pk_call - SIGOM's own allocation, box-acc-model.md section 6; BOX dev to confirm),",
        "--      each checked against the installation's auth code (GOM_GLB_SYS.T__CORE_INFO_S).",
        "-- Labels: looked up by code (BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel) - never a typed PK.",
        f"-- Values: each row copies the reference MBJ row named beside it; branch, label, calendar ({cal}) are the target's.",
        "-- ============================================================================",
    ]
    tv = test_values(cfg)
    if tv:                                                   # [2026-10-21] test answers: never to be run
        head += [f"-- TEST VALUES ({', '.join(tv)}): NOT DELIVERABLE - DO NOT RUN. The rehearsal and config blocks stop",
                 "-- at their first statement. Build again with the confirmed values (and no test_values).",
                 "-- ============================================================================"]
    decl = [
        "SET AUTOCOMMIT OFF",
        "SET SERVEROUTPUT ON SIZE UNLIMITED",
        "ALTER SESSION SET NLS_NUMERIC_CHARACTERS = '.,';",
        "DECLARE",
        f"  c_expected_auth_code  CONSTANT NUMBER := {auth};   -- mbj.auth_code",
        f"  c_branch_pk           CONSTANT NUMBER := {sql_num(tgt['branch_pk'])};   -- target.branch_pk",
        f"  c_owner_mbj           CONSTANT NUMBER := {MBJ_OWNER_OBJ};   -- BOX - MBJ Properties (J-T8)",
        f"  c_calendar            CONSTANT NUMBER := {cal};   -- mbj.calendar",
        f"  c_expected_rows       CONSTANT PLS_INTEGER := {len(rows)};",
        f"  v_jobs                sys.odcivarchar2list := sys.odcivarchar2list(\n    {jl});",
        "  v_auth      NUMBER;",
        "  v_fraction  NUMBER;",
        "  v_pk        NUMBER;",
        "  v_label     NUMBER;",
        "  v_n         PLS_INTEGER;",
        "  PROCEDURE chk_pk (p_pk NUMBER) IS",
        "  BEGIN",
        "    IF p_pk IS NULL OR p_pk - TRUNC(p_pk) <> v_fraction THEN",
        f"      RAISE_APPLICATION_ERROR(-20001, '{MBJ_TABLE}: PK ' || p_pk || ' does not carry the installation fraction '",
        "        || v_fraction || '. Nothing has been kept.');",
        "    END IF;",
        "  END chk_pk;",
        "  PROCEDURE expect_rows (p_what VARCHAR2, p_got PLS_INTEGER, p_want PLS_INTEGER) IS",
        "  BEGIN",
        "    DBMS_OUTPUT.PUT_LINE(RPAD(p_what, 64) || LPAD(TO_CHAR(p_got), 5) || '  (expected ' || p_want || ')');",
        "    IF p_got <> p_want THEN",
        "      RAISE_APPLICATION_ERROR(-20002, p_what || ': ' || p_got || ' row(s), expected ' || p_want",
        "        || '. Stopped; nothing has been kept.');",
        "    END IF;",
        "  END expect_rows;",
        "BEGIN",
        *([f"  RAISE_APPLICATION_ERROR(-20098, 'Built with TEST VALUES ({', '.join(tv)}) - not deliverable. "
           "Nothing has been done.');"] if tv else []),
        "  IF DBMS_TRANSACTION.LOCAL_TRANSACTION_ID IS NOT NULL THEN",
        "    RAISE_APPLICATION_ERROR(-20097, 'This session has an open transaction. Type ROLLBACK; and run this file '",
        "      || 'again. Nothing has been done.');",
        "  END IF;",
        "  SELECT auth_code INTO v_auth FROM gom_glb_sys.t__core_info_s;",
        "  IF v_auth <> c_expected_auth_code THEN",
        "    RAISE_APPLICATION_ERROR(-20003, 'Built for auth code ' || c_expected_auth_code || ', this installation is '",
        "      || v_auth || '. Wrong environment? Nothing has been done.');",
        "  END IF;",
        "  v_fraction := v_auth / POWER(10, LENGTH(TO_CHAR(v_auth)));",
        "  SELECT COUNT(*) INTO v_n FROM pgt_stc.t_pgt_calendar_s WHERE pk = c_calendar;",
        "  expect_rows('pre-flight: the MBJ calendar exists', v_n, 1);",
        f"  SELECT COUNT(*) INTO v_n FROM box_acc.{MBJ_TABLE} WHERE job_name IN (SELECT column_value FROM TABLE(v_jobs));",
        "  expect_rows('pre-flight: MBJ rows already there for these jobs', v_n, 0);",
        "",
    ]
    cols = ["PK", "FK_OWNER_OBJ", "FK_PARENT", "FK_EXTENSION", "JOB_NAME", "INSTANZE", "FK_BRANCH", "FK_INSTRUMENT",
            "FK_GROUP", "CONCURRENT_EVENTS", "CONCURRENT_EVENTS_DEPENDENCY", "WORKERS", "TASKS_PER_WORKER",
            "WORKERS_BY_EVENTS", "RETURN_DATA", "RECOVER_MANUAL_MOVS", "RECOVER_RECLASSIFICATION_MOVS",
            "RECOVER_REGULARIZATION_MOVS", "FK_LABEL", "FK_SUBLABEL", "FK_CALENDAR", "MONITOR_TYPES",
            "MONITOR_FILE_MAX_DAYS", "MONITOR_FILE_PATTERN", "MIC_SENDER_TYPE", "MIC_FILE_TYPE", "MIC_EOD",
            "MIC_FLOW_MODE"]
    body = []
    for r in rows:
        if r["LABEL"]:
            body += [f"  v_label := BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('{r['LABEL']}');",
                     "  IF v_label IS NULL THEN",
                     f"    RAISE_APPLICATION_ERROR(-20004, 'Label {r['LABEL']} does not exist: create it first (skill "
                     "set-up-book-labels). Nothing has been kept.');",
                     "  END IF;"]
            lab = "v_label"
        else:
            lab = "NULL"
        vals = ["v_pk", "c_owner_mbj", "NULL", sql_num(r["FK_EXTENSION"]), sql_txt(r["JOB_NAME"]), sql_txt(r["INSTANZE"]),
                "c_branch_pk", sql_num(r["FK_INSTRUMENT"]), sql_num(r["FK_GROUP"]), sql_txt(r["CONCURRENT_EVENTS"]),
                sql_txt(r["CONCURRENT_EVENTS_DEPENDENCY"]), sql_num(r["WORKERS"]), sql_txt(r["TASKS_PER_WORKER"]),
                sql_txt(r["WORKERS_BY_EVENTS"]), sql_txt(r["RETURN_DATA"]), sql_txt(r["RECOVER_MANUAL_MOVS"]),
                sql_txt(r["RECOVER_RECLASSIFICATION_MOVS"]), sql_txt(r["RECOVER_REGULARIZATION_MOVS"]), lab, "NULL",
                "c_calendar", sql_txt(r["MONITOR_TYPES"]), sql_num(r["MONITOR_FILE_MAX_DAYS"]),
                sql_txt(r["MONITOR_FILE_PATTERN"]), sql_txt(r["MIC_SENDER_TYPE"]), sql_txt(r["MIC_FILE_TYPE"]),
                sql_txt(r["MIC_EOD"]), sql_txt(r["MIC_FLOW_MODE"])]
        body += [f"  -- {r['JOB_NAME']}: values from the reference row of {r.get('_from', '')}".rstrip(": "),
                 f"  v_pk := {pk_call};  chk_pk(v_pk);",
                 f"  INSERT INTO BOX_ACC.{MBJ_TABLE}\n    ({', '.join(cols)})\n  VALUES\n    ({', '.join(vals)});", ""]
    tail_check = [
        f"  SELECT COUNT(*) INTO v_n FROM box_acc.{MBJ_TABLE} WHERE fk_branch = c_branch_pk",
        "    AND job_name IN (SELECT column_value FROM TABLE(v_jobs));",
        "  expect_rows('self-check: MBJ rows written for the branch', v_n, c_expected_rows);",
    ]
    reh = head + ["-- REHEARSAL (1 of 4). Every statement, then ROLLBACK. Nothing is kept."] + decl + body + tail_check + [
        "  ROLLBACK;",
        "  DBMS_OUTPUT.PUT_LINE('REHEARSAL OK - ' || c_expected_rows || ' MBJ row(s) inserted and rolled back.');",
        "END;", "/"]
    cfg_ = head + ["-- CONFIG (2 of 4). APPLIES AND COMMITS (its last statement)."] + decl + body + tail_check + [
        "  COMMIT;",
        "  DBMS_OUTPUT.PUT_LINE('DONE - committed ' || c_expected_rows || ' MBJ row(s).');",
        "END;", "/"]
    ver = head + ["-- VERIFY (3 of 4). Read-only. Each query states its expected result.", "",
                  "-- V1 - the installation (expected: 1 row, auth code " + auth + ")",
                  "SELECT COUNT(*) AS n_rows, MAX(auth_code) AS auth_code FROM gom_glb_sys.t__core_info_s;", "",
                  "-- V2 - readiness: the MBJ engine is deployed (expected: PACKAGE and PACKAGE BODY, VALID). Not there ->",
                  "--      the rows are fine but no mbjbox.sh job can run here until the BOX team deploys it.",
                  "SELECT object_type, status, last_ddl_time FROM all_objects",
                  "WHERE  owner = 'BOX_ACC' AND object_name = 'PKG_BATCHPROCESS_MBJ' ORDER BY object_type;", "",
                  f"-- V3 - the rows (expected: {len(rows)})",
                  f"SELECT COUNT(*) AS n_rows FROM box_acc.{MBJ_TABLE} WHERE fk_branch = {sql_num(tgt['branch_pk'])}",
                  f"AND    job_name IN (\n    {jl});", "",
                  "-- V4 - each row: label, group, calendar, owner (expected: every label_code = the job's book, calendar "
                  f"{cal}, owner {MBJ_OWNER_OBJ})",
                  "SELECT m.job_name, m.fk_instrument, m.fk_group, d.code AS label_code, m.fk_calendar, m.fk_owner_obj,",
                  "       m.mic_sender_type, m.mic_eod",
                  f"FROM   box_acc.{MBJ_TABLE} m LEFT JOIN pgt_sys.pgt_domains d ON d.pk = m.fk_label",
                  f"WHERE  m.fk_branch = {sql_num(tgt['branch_pk'])}",
                  f"AND    m.job_name IN (\n    {jl})", "ORDER  BY m.job_name;"]
    rb = head + ["-- ROLLBACK (4 of 4). ONLY to undo the config file: deletes exactly its rows.",
                 "SET AUTOCOMMIT OFF", "SET SERVEROUTPUT ON SIZE UNLIMITED", "DECLARE",
                 f"  c_branch_pk     CONSTANT NUMBER := {sql_num(tgt['branch_pk'])};",
                 f"  c_expected_rows CONSTANT PLS_INTEGER := {len(rows)};",
                 f"  v_jobs          sys.odcivarchar2list := sys.odcivarchar2list(\n    {jl});",
                 "  v_n             PLS_INTEGER;", "BEGIN",
                 f"  DELETE FROM box_acc.{MBJ_TABLE} WHERE fk_branch = c_branch_pk",
                 "    AND job_name IN (SELECT column_value FROM TABLE(v_jobs));",
                 "  v_n := SQL%ROWCOUNT;",
                 "  IF v_n <> c_expected_rows THEN",
                 "    ROLLBACK;",
                 "    RAISE_APPLICATION_ERROR(-20005, v_n || ' row(s) found, expected ' || c_expected_rows",
                 "      || '. Nothing deleted.');",
                 "  END IF;",
                 "  COMMIT;",
                 "  DBMS_OUTPUT.PUT_LINE('ROLLED BACK - deleted ' || v_n || ' MBJ row(s).');",
                 "END;", "/"]
    out = {"rehearsal": "\n".join(reh) + "\n", "config": "\n".join(cfg_) + "\n", "verify": "\n".join(ver) + "\n",
           "rollback": "\n".join(rb) + "\n"}
    for k, v in out.items():
        bad = [c for c in v if ord(c) > 126]
        if bad:
            raise ValueError(f"non-ASCII in the {k} file: {bad[:3]}")
    return out


def _pending(folder: Path, q_ren, q_ext, producer):
    lines = ["# Pending questions - box-acc-jobs-agent", ""]
    if not q_ren and not q_ext:
        lines.append("None - every rename and external event is answered.")
    if q_ren:
        lines += ["## Renames (old-named reference jobs)", "", "| reference job | suggested target name |", "|---|---|"]
        lines += [f"| `{j}` | `{s}` |" for j, s in q_ren] + [""]
    if q_ext:
        lines += ["## External events", "", "| event | waited for by | emitter |", "|---|---|---|"]
        for e, owners in sorted(q_ext.items()):
            em = ", ".join(sorted(producer.get(bfj.split_event(e)[1], set()))) or "not in the ACC folder"
            lines.append(f"| `{e}` | {', '.join(f'`{o}`' for o in sorted(owners)[:4])} | {em} |")
    (folder / PENDING).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _report(od, cfg, plan, names, kind, mapping, rows, excluded, tbooks, review, ph_events, name_label, upk, readiness,
            handoff, rname, res, extra=None):
    tgt, ref = cfg["target"], cfg["reference"]
    extra = extra or {}
    tv, open_rows = extra.get("test_values") or [], extra.get("open_rows") or {}
    rep = [f"# BOX ACC jobs - {tgt['branch_code']}", ""]
    if tv:
        rep += [f"> **TEST VALUES - not deliverable** ({', '.join(f'`{x}`' for x in tv)}): the SQL rehearsal and config "
                "files stop at their first statement; no PR. Build again with the confirmed values.", ""]
    rep += [
           f"From `{rname}` (reference `{ref['token']}`), {len(tbooks)} target book(s)"
           f"{f', {len(excluded)} excluded ({chr(44).join(excluded)})' if excluded else ''}. "
           f"**{len([m for m in mapping if m['target_job']])} target jobs**, {len(rows)} MBJ row(s). A proposal for the "
           "BOX team - nothing deployed.", "",
           "## Per instrument", "", "| instrument | template book | per-book steps | branch steps | Initial Accounting | "
           "MIC end-of-day | MIC sender |", "|---|---|---|---|---|---|---|"]
    for p, pl in plan.items():
        bs = sorted({j[-3:] for j in pl["include"] if kind.get(j) == "book"})
        br = sorted(names[j][None] for j in pl["include"] if kind.get(j) == "branch" and j in names)
        ia = ", ".join(names[j][None] for j in pl["ia"]) or "-"
        eod = "none in the reference" if not pl["eod"] else ("dropped" if pl["dropped"] else "kept")
        rep.append(f"| {p} | {pl['tb']} | {', '.join(bs) or '-'} | {', '.join(br) or '-'} | {ia} | {eod} | {pl['sender']} |")
    rep += ["", "## How they run", "",
            "- per-book steps and branch MIC steps: `shell.conf` (`mbjbox.sh <JOB>`) + one MBJ row each "
            "(`out/sql/`) [operator, 2026-10-21]",
            "- branch-level steps the reference runs from `db.conf` (ruler update): the core call (`db.conf.proposal`)",
            "- Initial Accounting: the FE agent's `db.conf` lines (`acc-handoff.json`)"
            + f" - from `{tgt['fe_run']}`", "",
            "## Readiness", "",
            f"- MBJ engine `BOX_ACC.PKG_BATCHPROCESS_MBJ` in the target: **{readiness or 'not confirmed'}** - "
            "verify V2. Not deployed: the files are right, the jobs cannot run there yet.",
            "- Environment descriptors (`pre.json` / `pro.json`) for the ACC folder: **not generated in this version** - "
            "per-environment Host / ControlmServer / OrderMethod to be written by the BOX team (or a later version, "
            "once the reference ACC descriptors are copied under runs/_reference/external/).", ""]
    if review or name_label:
        rep += ["## Decisions to review", ""] + [f"- {x}" for x in sorted(set(review)) + sorted(name_label)] + [""]
    if ph_events or open_rows or tv:
        rep += ["## OPEN", ""] + [f"- `{e}` answered `{a}` - a placeholder: not deliverable" for e, a in ph_events]
        rep += [f"- `{j}` - no MBJ row: {a} - its {len(ts)} job(s) ({', '.join(ts[:3])}{' ...' if len(ts) > 3 else ''}) "
                "are built in shell.conf, their rows are not in the SQL" for j, (a, ts) in sorted(open_rows.items())]
        rep += [f"- test value `{x}` - not deliverable" for x in tv] + [""]
    rep += ["## Unix package", "", f"`unix/job_unix.sh`: {upk['shell']} shell.conf job(s), {upk['db']} db.conf job(s)"
            + (f"; already in the target's etc folder: {', '.join(upk['have'])}" if upk.get("have") else "")
            + (f"; missing reference scripts: {', '.join(upk['missing'])}" if upk["missing"] else ""), ""]
    if res.warns:
        rep += ["## Warnings", ""] + [f"- `{c}` {w}: {m}" for c, w, m in res.warns] + [""]
    (od / "report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
