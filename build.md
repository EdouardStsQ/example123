# `box-fe-jobs-agent` — build a branch's BOX FE jobs (the procedure, any branch, any tier)

> **How to start — nothing to paste.** Open a Devin session with this repo attached and type:
> **`Run automation/agents/box-fe-jobs-agent/prompts/build.md`** — Devin asks the branch and the environment, then
> everything else one question at a time. A branch may also have a short kickoff that names them for you (e.g.
> [`build-ny-sch-tier2.md`](build-ny-sch-tier2.md)); it adds no step.

The procedure is the same for every branch and tier; **a branch is data**: its row in
`docs/reference/branch-registry.csv`, its inputs file `runs/<BRANCH>/<tier>-<env>/fe-jobs/fe-jobs-inputs.<BRANCH>.json`
(its known values and answers), its `runs/<BRANCH>/<tier>-<env>/fe-jobs/README.md` (decisions, history) and its open
items. Nothing here is branch-specific — a new branch needs no new prompt.

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

**Step 0 — repo root, branch, repos.**
1. The repo root: the folder containing `agents/` of the automation repo checkout (`cib-box-aukinbranch`, folder
   `automation/`); every path below is relative to it. Not found → ask the operator for the path.
2. **The branch** `<BRANCH>` and **its environment folder** `<tier>-<env>` — from the kickoff if one named them, else
   **ask** (show the `docs/reference/branch-registry.csv` codes and the folders under `runs/<BRANCH>/`). A code not in
   the registry → stop: the branch gets its registry row first.
3. **Its inputs file** `runs/<BRANCH>/<tier>-<env>/fe-jobs/fe-jobs-inputs.<BRANCH>.json`. None (a new branch) → copy
   `agents/box-fe-jobs-agent/templates/fe-jobs-inputs.example.json` there, fill what the registry row gives (`token`,
   `dbconf_branch_const`, `wrapper_owner`, `display`, the repos) and say every `<ask …>` left — they are asked in Steps
   2a–5b, never guessed.
4. **The repos to attach**, from the registry rows of the target and of the reference in the inputs: read-only — the
   reference's `fe_controlm_repo`, `acc_controlm_repo`, `prereq_controlm_repos`, and `reference.dml_repos`
   (`cib-boxfin-dbboxfe`, `cib-boxacc-dbboxacc`); the PR step only — the target's `fe_controlm_repo` and
   `prereq_controlm_repos`. Not attachable (another organisation): `env_descriptor_repo` and the Data Lake repo — check
   their copies are under `runs/_reference/external/`. Say which are missing.

**Step 1 — read now:** `agents/box-fe-jobs-agent/AGENT.md`, the inputs file, the target's
`runs/<BRANCH>/<tier>-<env>/fe-jobs/README.md` and its open items. **Read the rest when its step comes** (each step
names it): the skills' `SKILL.md` and `box-batch-chain.md` at Step 3, the reference's facts at Step 3, the header of
`scripts/build_fe_jobs.py` at Step 5.

**Step 2a — the environment and a new, versioned run folder** — **every run, first:**
1. Confirm the **environment** (Step 0's) and ask **what to build**: one instrument of the plan (not `skip`) or
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
4. **Before the first build, list every value you did not ask in this session** — copied from the branch's inputs
   file, an earlier run or another agent's run (e.g. `controlm.Host`, `CreatedBy`, an auth code) — one line each with
   its source, and get the operator's confirmation in one answer. Never fill an `<ask …>` silently.

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
Else propose the inputs' reference (`reference.*`) if it has FE jobs for the instrument, else a branch that has. **None
has** → propose `skip`: "no onboarded branch runs <instrument> BOX FE jobs (not in BOX yet)"; on the operator's yes,
set the plan row to `skip` with that reason and source, and stop for this instrument. The operator confirms the
reference; write it and `in progress` into the plan. A reference other than the inputs' → rewrite `reference.*` from
the chosen branch's registry row: `token`, `branch_const` (`dbconf_branch_const`), `wrapper_owner`, `display`,
`controlm_json` (`<fe_controlm_repo>/projects/<fe_controlm_repo>.json`), `controlm_other` (`acc_controlm_repo`),
`descriptor_dir` (`runs/_reference/external/cib-auki-aukicnfgsrvc/<fe_controlm_repo>`), `books_csv` (its J-R3b, Step 4),
`template_book` (re-proposed). **Read now:** `skills/find-box-jobs/SKILL.md`, `docs/reference/job-chains/box-batch-chain.md` (L1, L2) and the chosen
reference's facts `docs/reference/job-chains/reference-<reference>-fe.md` when it exists (none → say so: its facts are
then only what the chain and the queries show). Then the chain (skill `find-box-jobs`), shown to the operator:

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

**Step 5 — run, ask, run again.** **Read now:** the header of `scripts/build_fe_jobs.py` and
`skills/explain-box-job/SKILL.md`.

```bash
python3 scripts/build_fe_jobs.py <run folder>/
```

Each `REFUSED` line names an input: ask the operator **that one question**, write the answer, run again. For
`rename-missing` and `external-event-unmapped` the script writes `<run folder>/pending-questions.md`: ask its rows
**one at a time**, each with its row (who emits the event, folder, what it is, side · product · level) and its
suggested answer — the operator decides; a suggestion is never written unasked. Never edit `out/`.
**Offer only answers the script has an input for** (the `REFUSED` line names it; the script's header lists the
values). A refusal no input can answer is a script gap: stop, say so, and change nothing (no edit of the script, an
evidence CSV or `out/`); the operator decides how to go on.

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

**Any time — "what does job X do?"** Run skill `explain-box-job` (read its `SKILL.md` the first time)
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
missing until its reference copy is in `runs/_reference/tier1-prod/unix/`. The excluded books: the script refuses
`excluded-book-built` if any of their jobs or labels is in `out/` — nothing to grep.

**Step 6 — finish:** show `out/report.md` and say: the reference branch used, the load-prices jobs, the Data Lake
waits per book, target jobs per level, the descriptor entries written per folder and environment and each **review** /
**confirm** line, the other instruments' jobs whose waits were inherited, the `db.conf` core-call note, the Initial
Accounting jobs and the hand-off to `box-acc-jobs-agent`, the Unix package, external events, decisions to review and
hand-offs, the GBO events checked or not checked, and that the files are a proposal for the BOX team. Set the plan row
to `done` (exit 0) or leave `in progress` (exit 4, OPEN lines). Commit the run folder and the plan to the automation
repo only. **Do not freeze yet** — the PR step comes first (Step 8).

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

**Step 8 — freeze, last:** once the run is committed **and** Step 7 is done or declined:
`python3 scripts/new_run.py --freeze <run folder>`, commit the `.frozen` mark — a later attempt is a new version.
`stage_target_pr.py` refuses a frozen run (`run-frozen`): never freeze before the PR question.

**Regression check — when the agent's scripts, inputs format or prompts changed since the branch's last finished
run, or the operator asks "does it still give the same files?":**

```bash
python3 scripts/regress_fe_jobs.py <the last frozen run folder>/ [--map <its old repo path>=<this session's>]
```

It rebuilds the run from its own answers in a temporary copy (the run is not written) and compares every file of
`out/`. Exit 0 = identical deliverables. Exit 1 = show each `DIFFERS` file with its diff and say, per difference,
whether a change since that run explains it (CHANGELOG) — an unexplained difference is a regression: report it, do
not build on it. Exit 2 = the rebuild refused (a repo path of another session: `--map`).
