# `box-fe-jobs-agent` — build a new branch's BOX FE jobs (generic procedure)

**Started from a branch kickoff** (e.g. [`build-ny-sch-tier2.md`](build-ny-sch-tier2.md)), which gives: the target
branch `<BRANCH>` (registry code), its environment folder `<tier>-<env>`, its inputs file
`runs/<BRANCH>/<tier>-<env>/fe-jobs/fe-jobs-inputs.<BRANCH>.json`, the repos to attach, and what is already known.
A new branch: copy a kickoff, change its table — this procedure stays as is. Nothing here is branch-specific.

**What a run produces:** for one instrument or several (`<run folder>` = the versioned folder of Step 2a,
`runs/<BRANCH>/<tier>-<env>/fe-jobs/<name>_<YYYYMMDD>_<n>/`), in run order: the target's **prerequisite** folder JSONs
(load prices, scheduling monitor), its BOX **FE** folder JSON, the FE **`db.conf`** lines (prerequisites first), the
reference's `pre.json` / `pro.json` re-pointed to the target for each folder (incl. each target book's Data Lake waits
and the target's PRE / PRO hosts), the Unix package and the Initial Accounting hand-off — copied from the chain of the
branch that runs the instrument — proposal files in `<run folder>/out/`. Nothing deployed.

| | |
|---|---|
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or edit on any repo except this automation repo — **one exception** ([ADR 0012](../../../docs/decisions/0012-target-repo-pr-exception.md)): a PR of `projects/<repo>.json` on the target's own Control-M repos (registry), from a new branch, never merged, **only after the operator's yes** (Step 7) |
| **Database** | Devin gets no connection. The operator runs **J-R3b** (reference tier, once per reference branch) and **J-E4** (target tier) and returns the CSVs — skipped when already in `01-evidence/` |
| 💬 **The operator can ask** | at any time *"what does job `<JOB>` do?"* — answer with skill `explain-box-job` (no query), then repeat the pending question |

---

You are running as the `box-fe-jobs-agent`.

**Step 0 — repo root.** The folder containing `agents/` of the automation repo checkout (`cib-box-aukinbranch`,
folder `automation/`); every path below is relative to it. Not found → ask the operator for the path. Check the repos
the kickoff lists are attached; say which are missing.

**Step 1 — read in full:** `agents/box-fe-jobs-agent/AGENT.md`, `skills/find-box-jobs/SKILL.md`,
`skills/explain-box-job/SKILL.md`, `docs/reference/job-chains/box-batch-chain.md` (L1, L2), the header of
`scripts/build_fe_jobs.py`, the target's `runs/<BRANCH>/<tier>-<env>/fe-jobs/README.md` (its values, decisions and
history) and, for each reference branch, `docs/reference/job-chains/reference-<branch>-fe.md` when it exists.

**Step 2a — the environment and a new, versioned run folder** — **every run, first:**
1. Ask the **environment** (default the kickoff's) and **what to build**: one instrument of the plan (not `skip`) or
   several in one run.
2. Create the run folder — never reuse one:
   `python3 scripts/new_run.py --branch <BRANCH> --tier <tier> --env <env> --area fe-jobs --name <instrument or all>`.
   A **new environment** is created empty and the script lists what it lacks (books register, its job confs): say so
   and ask, per item, "copy from another environment, or provide?" — never copy silently.
3. Create `fe-jobs-inputs.json` from the branch's inputs file with `instrument` = the choice (a string for one, the
   list for several). **Carry over no answer** unless the operator names an earlier run: then `new_run.py --from <run>`
   puts its inputs beside as `fe-jobs-inputs.from-<run>.json` — offer its answers **one by one** (renames, external
   events, constants, Data Lake books, `CreatedBy`, template book). Only the query CSVs (J-R3b, J-E4) may be copied
   from another run's `01-evidence/` (say so). The books in `books/books-excluded.csv` get no job (show them).

**Step 2 — the instruments.** **Build together every instrument not deployed yet:** the shared per-book jobs
(`GMBX0<TT><bk>D01-D03`) wait on what is built, so a second run overwrites the first's. An instrument the plan says
`built` / `done` but outside this run → the script refuses (`shared-jobs-other-run`): add it to the run, or — only when
the operator says its jobs are deployed and stay valid — write their reason in `separate_run`.
Read the target's approved instruments from `docs/reference/branch-registry.csv` (row `<BRANCH>`, column
`instruments`) — **never ask for the list again** — and the jobs plan `runs/<BRANCH>/<tier>-<env>/fe-jobs/instrument-plan.csv`
(`status`: `to build`, `in progress`, `done`, **`skip`**; `reference`: a branch the operator **forces**; `reason`,
`source`). Show the plan. A `skip` instrument is **never built** — say its reason; the operator can change it (update
the row with reason and source). An approved instrument missing from the plan → add it as `to build`. Set
`target.instruments` to the registry list **minus the `skip` instruments** (a wait on a skipped instrument's job is
then suggested `DROP`).

**Step 3 — the reference branch per instrument, and its chain.** Which onboarded branch runs it:

```bash
python3 scripts/find_jobs.py runs/_reference/tier1-prod/ --product <instrument> --side FE --references
```

A **forced** `reference` in the plan → use it (still show the counts; 0 BOX FE jobs there → say the build will refuse).
Else propose the branch the kickoff prefers if it has FE jobs for the instrument, else the branch that has. **None
has** → propose `skip`: "no onboarded branch runs <instrument> BOX FE jobs (not in BOX yet)"; on the operator's yes,
set the plan row to `skip` with that reason and source, and stop for this instrument. The operator confirms the
reference; write it and `in progress` into the plan. A reference other than the inputs' → rewrite `reference.*` from
the chosen branch's registry row: `token`, `branch_const` (`dbconf_branch_const`), `wrapper_owner`, `display`,
`controlm_json` (`<fe_controlm_repo>/projects/<fe_controlm_repo>.json`), `controlm_other` (`acc_controlm_repo`),
`descriptor_dir` (`runs/_reference/external/cib-auki-aukicnfgsrvc/<fe_controlm_repo>`), `books_csv` (its J-R3b, Step 4),
`template_book` (re-proposed). Then the chain (skill `find-box-jobs`), shown to the operator:

```bash
python3 scripts/find_jobs.py runs/_reference/tier1-prod/ --side FE --product <instrument> --branch <reference> \
    --controlm <its FE folder repo> --out <run folder>/01-evidence/reference-chain
```

Check the paths in the inputs exist: the reference's FE / ACC / load-prices / monitor repos attached,
`reference.dml_repos` (the two DB repos), the copies under `runs/_reference/external/` (`descriptor_dir`,
`prerequisites[].descriptor_dir`, `datalake.*`); `target.env_folder` (`runs/_reference/<tier>-<env>/`) — run
`python3 scripts/parse_job_confs.py <that folder>` first if `jobs-inventory.csv` is missing or older than `db.conf` or
than `scripts/parse_job_confs.py`; commit it. Also re-run it on `runs/_reference/tier1-prod/` when its inventory is
older than the parser, and check its counts (job lines, BOX / GBO rows, executed bindings) are unchanged. A missing
one: say so and ask.

**Reference books:** the template book per instrument (`reference.template_book`) and the one shared-jobs book
(`reference.generic_book`) — given in the inputs (with their source) or chosen by the script: run it once and show
the operator its `template-book-chosen` / `generic-book-chosen` lines (counts per book, why the book won); the
operator confirms, the answer is written with its date. A `reference-cross-book-wait` is a reference defect: say it,
never copy it.

**Step 4 — the two queries** — skip a query whose CSV is already in `01-evidence/` (an earlier run), say so; **J-E4 is
the same for every instrument and J-R3b for every instrument with the same reference** — copy them from another
run's `01-evidence/` when there — one at a time (catalogue `docs/reference/queries/box-jobs-queries.md`):
**J-R3b in Tier 1** (the reference's labels, `&&REF_LABEL_PREFIX = X<reference token>`) →
`01-evidence/J-R3b-reference-books.csv`; **J-E4 in the target tier** (the target wrapper's constants) →
`01-evidence/J-E4-wrapper-TGT.csv`. From J-E4 fill `target.constants` (each `CST_…` the reference lines use → the
target wrapper's name, or `SAME`) and confirm `wrapper_args`.

**Step 5 — run, ask, run again:**

```bash
python3 scripts/build_fe_jobs.py <run folder>/
```

Each `REFUSED` line names an input: ask the operator **that one question**, write the answer, run again. For
`rename-missing` and `external-event-unmapped` the script writes `<run folder>/pending-questions.md`: ask its rows
**one at a time**, each with its row (who emits the event, folder, what it is, side · product · level) and its
suggested answer — the operator decides; a suggestion is never written unasked. Never edit `out/`.

- **The target's GBO Control-M folder — ask once, optional:** before answering any GBO event, ask the operator whether
  they can attach the target's GBO Control-M folder JSON (per environment; `CreatedBy` removed). Yes →
  `target.gbo_folders`, and the script checks every GBO event answer against what the target really emits. No →
  carry on: the answers stay INFERRED and the report lists them as not checked. **Never block the run on it.**
- **Each question with its reference context:** before asking, run skill `explain-box-job` on the reference job behind
  it and say in two lines what it runs, who waits for it and what the reference does (e.g. *"the reference's queue
  job, group 2608.65, no waits, `FromTime`; every book's D06 waits for it — target name `GMBX1<TT>00D01`?"*). An
  answer with a placeholder (`{…}`, `<OPEN …>`) is not a final answer: the script reports it OPEN — ask again.
- Also in that file: **Data Lake books** (a target book whose description has no Data Lake job — the closest are
  listed; answer goes to `datalake.book_map`) and, for a **GBO** event, what the GBO job runs and the target's
  look-alike when `target.env_folder` is set (INFERRED — the operator confirms). A wait on a feed the target does not
  have → `DROP-REVIEW`, and say whether the job behind it may need the data.
- The descriptors' **review** lines name what is missing per environment (an activation date
  `controlm.env.<env>.StartDate`; `ControlmServer` / `OrderMethod` copied from the reference "to confirm").

**Any time — "what does job X do?"** Run skill `explain-box-job`
(`python3 scripts/explain_job.py runs/_reference/tier1-prod/ <JOB> --controlm <the reference's FE, ACC and
load-prices folder repos> --dml <the two DB repos>`; an environment-only wait is in the descriptors, not in its card),
answer with its card, then **repeat the pending question**. Deeper (an event's entries) → `box-batch-jobs-agent`
EXPLAIN depth `event`.

**Step 5b — Initial Accounting and Unix package.** Ask (once) for `acc.folder_name`, `acc.Application` (the target's
ACC folder; leave `<ask>` if the operator does not know yet — the draft keeps it) and `unix.etc_dir` (where
`add_new_jobs.ksh` is on the target). Check in the report: one Initial Accounting job per instrument
(`GMBX<n><TT>00D02`, its `db.conf` line), the books' `D02` waiting for them, `acc-handoff.json`, and
`unix/job_unix.sh` (one `cp` + `chmod` per `db.conf` line), and the `OrderMethod` of each environment in both folders'
descriptors.

**Step 6a — check** `out/unix/`: `job_unix.sh` starts with `sh -x <etc>/delete_jobsBX.ksh  db.conf
<etc>/db_delete.txt` and `sh -x <etc>/add_new_jobs.ksh db.conf <etc>/db_nuevo.conf`; `db_nuevo.conf` =
`db.conf.proposal`; `db_delete.txt`; the target's `delete_jobsBX.ksh` (`cd <etc>`). `add_new_jobs.ksh` is reported
missing until its reference copy is in `runs/_reference/tier1-prod/unix/`. No job of an excluded book anywhere (grep
the excluded book numbers in `out/*.json` and `out/db.conf.proposal`: 0).

**Step 6 — finish:** show `out/report.md` and say: the reference branch used, the load-prices jobs, the Data Lake
waits per book, target jobs per level, the descriptor entries written per folder and environment and each **review** /
**confirm** line, the other instruments' jobs whose waits were inherited, the `db.conf` core-call note, the Initial
Accounting jobs and the hand-off to `box-acc-jobs-agent`, the Unix package, external events, decisions to review and
hand-offs, the GBO events checked or not checked, and that the files are a proposal for the BOX team. Set the plan row
to `done` (exit 0) or leave `in progress` (exit 4, OPEN lines). Commit the run folder and the plan to the automation
repo only.

**Step 6b — freeze:** once the run is committed (and the PR step done or declined):
`python3 scripts/new_run.py --freeze <run folder>` — a later attempt is a new version.

**Step 7 — the PR on the target's own repos** (ADR 0012) — only once Step 6 is done and the report shows no refusal:

```bash
python3 scripts/stage_target_pr.py <run folder>/ --checkout <target repo>=<its clone> ...
```

Show `out/pr/pr-summary.md` and ask, **one repo at a time**: *"Open a PR on `<repo>` from a new branch
`box-fe-jobs/<BRANCH>-<date>` adding / replacing `projects/<repo>.json` (folder `<FOLDER>`, N jobs, changes as listed)?
yes / no"*. Only on **yes**: in that repo's clone, create the branch, copy `out/pr/<repo>/projects/<repo>.json` to
`projects/<repo>.json`, commit (message: the run folder and the date), push **the new branch**, open the PR (body: the
summary line and a link to the run's `report.md`). Never push to the default branch, never merge, never touch another
file. On **no**: nothing; say so in the summary. The run's `out/` files stay as they are.
