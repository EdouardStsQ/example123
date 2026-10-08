# Devin kickoff — `box-fe-jobs-agent` — NY_SCH BOX FE jobs, from SLB or Madrid (Tier 1) to Tier 2 PRE

> **How to start — nothing to paste.** Open a Devin session with the repos in the table below attached, and type:
> **`Run automation/agents/box-fe-jobs-agent/prompts/build-ny-sch-tier2.md`**
> Devin reads this file and asks you for anything it needs, one question at a time (with a default you can accept).

**What this run produces:** for **one instrument**, in run order: NY_SCH's **load-prices** folder JSON
(`JACD-T2NYLOADPRICES-BOX_FE-100068124`), its BOX **FE** folder JSON, the FE **`db.conf`** lines (load prices first), and
the reference's `pre.json` / `pro.json` re-pointed to NY for both folders (incl. each NY book's Data Lake wait and
NY's PRE / PRO host) — copied from the chain of the branch
that runs the instrument (SLB first, else Madrid) — proposal files in `runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/out/`. Nothing deployed.

## Before you start

| | |
|---|---|
| **Repos** | this automation repo `cib-box-auki-nbranch` (**read/write**); **read-only**: the reference branch's FE Control-M folder (`cib-boxfin-t1mdslbfe` for SLB, `cib-boxfin-t1mdesfe` for Madrid), its ACC folder (`cib-boxacc-t1mdslbac` / `cib-boxacc-t1mdesac` — who emits an ACC event), `cib-boxfin-t1mdloadprices` (load prices — they run first), `cib-boxfin-dbboxfe` and `cib-boxacc-dbboxacc` (group and event names) |
| **Not attachable (other organisation)** | `cib-auki-aukicnfgsrvc` (the `pro.json` waits) and `cib-auki-aukictrlmcntrm` (Data Lake jobs per book): their files are **copies in this repo**, `runs/_reference/external/` — check they are there |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or edit on any repo except this automation repo, ever |
| **Database** | Devin gets no connection. You run **J-R3b** (reference tier, once per reference branch) and **J-E4** (Tier 2) and return the CSVs — skipped when already in `01-evidence/` |
| **Already there** | `runs/_reference/tier1-prod/` (Madrid + SLB `db.conf`, `jobs-inventory.csv`); `runs/NY_SCH/tier2-pre/books/books-register.csv` (22 books; descriptions = Data Lake `book_vr`); NY's instruments in `docs/reference/branch-registry.csv` (`irs depos ccs otc cap cds`, gate 0c) |
| **Already there** `[2026-10-07]` | `runs/_reference/tier2-pre/` — NY's own Tier 2 `db.conf` / `shell.conf` (operator, 2026-10-07): generated names are checked against them, and NY's look-alike of a reference GBO job is proposed. `runs/_reference/external/cib-auki-aukicnfgsrvc/<repo>/{pre,pro}.json` for `cib-boxfin-t1mdslbfe` and `cib-boxfin-t1mdloadprices` — **both** environments |
| **BOX expert review applied** `[2026-10-07]` | DEV host in the folder files (PRE / PRO hosts in the descriptors), calendar `CALC-USA`, only this instrument's jobs (another instrument's waits inherited), `-NOK` events renamed, `db.conf` as the core call `PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup` (T:P, label included), known answers pre-filled (`GMBOX0114D01` → `GMBX1NY00D01`, `GMBOX0028D01` → `GMBX1NY00D02`, `GMGB1420D01/D02` → `GMNY0011D01_PR` / `GMNY0012D01_PR`) |
| **Already given** `[operator, 2026-10-06]` | NY's Control-M values in `fe-jobs-inputs.NY_SCH.json` (FE folder `JACD-T2USNYFE-BOXFE-100068124`, load prices `JACD-T2NYLOADPRICES-BOX_FE-100068124`, server, site standard, PRE host, `/gmny/scripts`, `gmny`, application, `CALC-USA`, documentation file) |
| ✏️ **Devin asks** | which instrument to build (from NY's list), confirms the reference branch, then the renames, external events, Data Lake books and constants the script asks for — one at a time, each with a suggestion |
| 💬 **You can ask** | at any time *"what does job `<JOB>` do?"* — Devin answers (skill `explain-box-job`, no query) and repeats its pending question |

---

**If you were pointed at this file**, it is your task prompt: skip the table above, check the repos are attached
(say which are missing), and start.

You are running as the `box-fe-jobs-agent`.

**Step 0 — repo root.** The folder containing `agents/` of the `cib-box-auki-nbranch` checkout's `automation/`
folder; every path below is relative to it. Not found → ask the operator for the path.

**Step 1 — read in full:** `agents/box-fe-jobs-agent/AGENT.md`, `skills/find-box-jobs/SKILL.md`,
`skills/explain-box-job/SKILL.md`, `docs/reference/job-chains/box-batch-chain.md` (L1, L2), the header of
`scripts/build_fe_jobs.py`.

**Step 2 — the instruments.** `[2026-10-08]` **One run builds every NY instrument** (`instrument` = the list): folder
`runs/NY_SCH/tier2-pre/fe-jobs/all/`. Create it from `fe-jobs-inputs.NY_SCH.json`, then carry over every answer of the
earlier run's `depos/fe-jobs-inputs.json` (renames, external events, constants, books, Data Lake, `CreatedBy`, template
book of depos) and say which; `depos/` stays as history. The rest of this step is for a one-instrument run.

**Step 2 (one instrument) — the instrument.** Read NY's approved instruments from `docs/reference/branch-registry.csv` (row `NY_SCH`,
column `instruments`) — **never ask for the list again** — and the jobs plan
`runs/NY_SCH/tier2-pre/fe-jobs/instrument-plan.csv` (`status`: `to build`, `in progress`, `done`, **`skip`**;
`reference`: a branch the operator **forces**; `reason`, `source`). Show the plan; ask only *which instrument to build
now* (default: the first `in progress`, else `to build`). A `skip` instrument is **never built** — say its reason; the
operator can change it (update the row with reason and source). An approved instrument missing from the plan → add it
as `to build`. The approved list is wrong → the operator updates the registry row and its source. Folder:
`runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/`. No `fe-jobs-inputs.json` there → copy
`runs/NY_SCH/tier2-pre/fe-jobs/fe-jobs-inputs.NY_SCH.json`. One there (an earlier run) → keep it and every answer in it,
and add each key of `fe-jobs-inputs.NY_SCH.json` it lacks (say which). **[2026-10-07] Also replace** in it, from
`fe-jobs-inputs.NY_SCH.json`, and say so: `controlm.Host` (now the **DEV** host), `controlm.MonthDaysCalendar`,
`renames.GMBOX0114D01` (an old `GMBX0NY00D03` / `GMBX0NY00D01` is superseded by `GMBX1NY00D01`), and every
`external_events` answer `KEEP` for an SLB job's event (e.g. `GMBOX0028D01-OK`) — the script now refuses KEEP of a
reference-token event and warns on an old-named one. Set `instrument`, and `target.instruments` to the
registry list **minus the `skip` instruments** (a wait on a skipped instrument's job is then suggested `DROP`).

**Step 3 — the reference branch for this instrument, and its chain.** Which onboarded branch runs it:

```bash
python3 scripts/find_jobs.py runs/_reference/tier1-prod/ --product <instrument> --side FE --references
```

A **forced** `reference` in the plan → use it (still show the counts; 0 BOX FE jobs there → say the build will refuse).
Else propose **SLB** if it has FE jobs for the instrument, else the branch that has (e.g. Madrid for an instrument SLB
does not run). **None has** → propose `skip`: "no onboarded branch runs <instrument> BOX FE jobs (not in BOX yet)"; on the
operator's yes, set the plan row to `skip` with that reason and source, and stop for this instrument (nothing built,
nothing asked). The operator confirms the reference; write it and `in progress` into the plan. Not SLB → rewrite `reference.*` from
the chosen branch's registry row: `token`, `branch_const` (`dbconf_branch_const`), `wrapper_owner`, `display`,
`controlm_json` (`<fe_controlm_repo>/projects/<fe_controlm_repo>.json`), `controlm_other` (`acc_controlm_repo`),
`descriptor_dir` (`runs/_reference/external/cib-auki-aukicnfgsrvc/<fe_controlm_repo>`), `books_csv` (its J-R3b, Step 4),
`template_book` (re-proposed). Then the chain (skill `find-box-jobs`), shown to the operator:

```bash
python3 scripts/find_jobs.py runs/_reference/tier1-prod/ --side FE --product <instrument> --branch <reference> \
    --controlm <its FE folder repo> --out runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/01-evidence/reference-chain
```

Check the paths in the inputs exist: the FE / ACC / load-prices repos attached, `reference.dml_repos` (the two DB
repos), the copies under `runs/_reference/external/` (`descriptor_dir`, `prerequisites[0].descriptor_dir`,
`datalake.*`); `target.env_folder` = `runs/_reference/tier2-pre` (its `db.conf` is there since 2026-10-07) — run
`python3 scripts/parse_job_confs.py runs/_reference/tier2-pre/` first if `jobs-inventory.csv` is missing or older than
`db.conf` or than `scripts/parse_job_confs.py` (it now also reads the core call `p_ExecuteGroup`); commit it.
Also re-run it on `runs/_reference/tier1-prod/` when its inventory is older than the parser, and check its counts
(job lines, BOX / GBO rows, executed bindings) are the same as before — the 2026-10-07 change only adds a `time`
column and the `p_ExecuteGroup` decoding. It refuses a generated name NY already runs and proposes NY's GBO look-alikes.
A missing one: say so and ask. Propose the template book (the first book with the full chain; not an extra book like
SLB's `99`) and ask the operator to confirm.

**Step 4 — the two queries** — skip a query whose CSV is already in `01-evidence/` (an earlier run), say so; **J-E4 is
the same for every instrument and J-R3b for every instrument with the same reference** — copy them from another
instrument's `01-evidence/` when there — one at a time (catalogue `docs/reference/queries/box-jobs-queries.md`):
**J-R3b in Tier 1** (the reference's labels, `&&REF_LABEL_PREFIX = X<token>`: `XLB` SLB, `XES` Madrid) →
`01-evidence/J-R3b-reference-books.csv`;
**J-E4 in Tier 2** (the `PGT_NY` wrapper's constants) → `01-evidence/J-E4-wrapper-TGT.csv`. From J-E4 fill
`target.constants` (each `CST_…` the SLB lines use → its `PGT_NY` name, or `SAME`) and confirm `wrapper_args`.

**Step 5 — run, ask, run again:**

```bash
python3 scripts/build_fe_jobs.py runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/
```

Each `REFUSED` line names an input: ask the operator **that one question**, write the answer, run again. For
`rename-missing` and `external-event-unmapped` the script writes `runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/pending-questions.md`:
ask its rows **one at a time**, each with its row (who emits the event, folder, what it is, side · product · level)
and its suggested answer — the operator decides; a suggestion is never written unasked. Never edit `out/`.
Also in that file: **Data Lake books** (a NY book whose description has no Data Lake job — the closest are listed;
answer goes to `datalake.book_map`) and, for a **GBO** event, what the GBO job runs and NY's look-alike job when
`target.env_folder` is set (INFERRED — ranked by function name, then first argument by value; the operator confirms).
Expected for NY: GMGB1420D01/D02 are pre-answered; the PRE wait `GMGB1575D01-OK` (index load) is asked with its
look-alike. The descriptors' **review** lines name what is missing per environment (e.g. NY's load-prices PRO activation
date `controlm.env.pro.json.StartDate`; `ControlmServer` / `OrderMethod` copied from SLB "to confirm").

**Any time — "what does job X do?"** Run skill `explain-box-job`
(`python3 scripts/explain_job.py runs/_reference/tier1-prod/ <JOB> --controlm <the FE, ACC and load-prices folder repos>
--dml <the two DB repos>`; a PRO-only wait is in `pro.json`, not in its card), answer with its card, then **repeat the pending question**. Deeper (an event's entries) → say it is
`box-batch-jobs-agent` EXPLAIN depth `event`.

**Step 5b — Initial Accounting and Unix package** `[2026-10-08]`. Ask (once) for `acc.folder_name`,
`acc.Application` (NY's ACC folder; leave `<ask>` if the operator does not know yet — the draft keeps it) and
`unix.etc_dir` (where `add_new_jobs.ksh` is on Tier 2). Check in the report: one Initial Accounting job per instrument
(`GMBX<n>NY00D02`, its `db.conf` line), the books' `D02` waiting for them, `acc-handoff.json`, and `unix/job_unix.sh`
(one `cp` + `chmod` per `db.conf` line). `OrderMethod`: PRE `ON DEMAND`, PRO `JAC1400` in both folders' descriptors.

**Step 6 — finish:** show `out/report.md` and say: the reference branch used, the load-prices jobs, the Data Lake
waits per book, target jobs per level, the descriptor
entries written per folder and environment and each **review** / **confirm** line, the other instruments' jobs whose
waits were inherited, the `db.conf` core-call note (branch PK on every line, time argument), the Initial Accounting jobs and the hand-off
to `box-acc-jobs-agent`, the Unix package, external events
and hand-offs, and that the files are a proposal for the BOX team.
Set the plan row to `done` (exit 0) or leave `in progress` (exit 4, OPEN lines). Commit the run folder and the plan to
the automation repo only.
