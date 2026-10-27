---
name: box-acc-jobs-agent
description: Generates a new branch's BOX ACC batch jobs from a reference branch's ACC chain - the ACC Control-M folder JSON, the shell.conf lines (mbjbox.sh) of every per-book step, the db.conf core-call lines of the branch-level steps, the BOX_ACC MBJ rows as rendered SQL, the Unix package and the PR on the target's own ACC repo after the operator's yes. Never runs anything.
---

# BOX ACC Jobs Agent

Scope `[stated: operator, 2026-10-21]`: BOX **ACC** jobs (accounting, Mark to Market / reval, MIC end of day) for a
new branch, from a reference branch already in BOX: the ACC Control-M folder, `shell.conf` + one MBJ row per per-book
step, `db.conf` for the branch-level steps. The FE jobs and the Initial Accounting `db.conf` lines are
[`box-fe-jobs-agent`](../box-fe-jobs-agent/AGENT.md)'s; the BOX - Accounting SIGOM screens are
[`sigom-box-acc-configs-agent`](../sigom-box-acc-configs-agent/AGENT.md)'s. Mechanism: the batch chain doc
([`box-batch-chain.md`](../../docs/reference/job-chains/box-batch-chain.md), L2 and *The ACC chain*); the PR exception:
[ADR 0012](../../docs/decisions/0012-target-repo-pr-exception.md); history: `CHANGELOG.md`.

**Asked to run this file?** It is the charter (the rules), not the procedure: follow
[`prompts/build.md`](prompts/build.md) from Step 0 — it reads this file at Step 1.

## Goal

Given a **reference branch** (onboarded), one or more **instruments** and a **target branch**, produce the files the
BOX team would otherwise write by hand for the target's accounting batch, **with the same chain as the reference**:

1. the target's **ACC Control-M folder** JSON — the Initial Accounting jobs (handed over by the FE agent), each
   book's accounting / reval / MIC end-of-day steps, the branch-level ruler update and MIC end-of-day step;
2. **`shell.conf`** — every per-book step and branch MIC step as `mbjbox.sh <JOB>`, the way ACC runs today
   `[stated: BOX dev via operator, 2026-10-01]`, **also where the reference still runs one from `db.conf`** in some
   books `[stated: operator, 2026-10-21; confirmed: BOX expert, 2026-10-26 — ADR 0016]`;
3. **`db.conf`** — the branch-level steps the reference runs from `db.conf` (the ruler update), as the core call,
   and the per-book steps **the reference never runs through MBJ** (no MBJ row in any book), per book with the
   book's label, exactly as the reference `[BOX expert, 2026-10-26 — ADR 0016]`;
4. the **MBJ rows** (`BOX_ACC.T_BOX_MBJ_PROPERTIES_S`, one per `shell.conf` job) as SQL — precheck (the PK
   sequence), rehearsal, config, verify, rollback — for the BOX team to run;

plus the Unix package and, after the operator's yes, the PR on the target's own ACC Control-M repo.

Correct means: every target job comes from a named reference job (file:line); every wait resolves to a job of the
new folder, to the target's FE job of the same book, or to an external event the operator mapped; every MBJ value
comes from a named reference row or an asked input; nothing of the reference's environment (host, server,
application, calendar, branch, label, developer ID) is copied. A value the agent cannot source is a question.

## Branch-agnostic by construction

**No branch, environment, owner, constant, job or folder name is written here** — a test fails if one is.

| What | Where |
|---|---|
| A target branch's values and answers | its inputs file `runs/<BRANCH>/<tier>-<env>/acc-jobs/acc-jobs-inputs.<BRANCH>.json` (shape: [`templates/acc-jobs-inputs.example.json`](templates/acc-jobs-inputs.example.json)), copied into each run |
| A target branch's decisions and history | `runs/<BRANCH>/<tier>-<env>/acc-jobs/README.md`; its questions: `runs/<BRANCH>/<tier>-<env>/jobs/99-open-items.md` |
| What we know about a reference branch's ACC chain | `docs/reference/job-chains/reference-<branch>-acc.md` |
| How BOX batch works (all branches) | [`box-batch-chain.md`](../../docs/reference/job-chains/box-batch-chain.md) |
| The procedure | [`prompts/build.md`](prompts/build.md) — the same for every branch and tier; a branch's optional kickoff in [`prompts/`](prompts/) only names the branch and environment |

## Definition of done

1. `scripts/build_acc_jobs.py` exits **0** (or **4** with every OPEN line listed) on the run's inputs;
2. every refusal was answered by the operator, never guessed (`pending-questions.md` says "None");
3. the operator has seen `out/report.md` — per instrument the template book, the steps, the MIC end-of-day steps, the
   decisions to review, the readiness of the MBJ engine;
4. the BOX team has reviewed `out/` — until then the files are a proposal; the SQL is run by the BOX team, never by
   the agent.

## Inputs — `runs/<BRANCH>/<tier>-<env>/acc-jobs/<name>_<YYYYMMDD>_<n>/acc-jobs-inputs.json`

| Group | Values | Where they come from |
|---|---|---|
| Reference | env folder (`db.conf`, `shell.conf`), the ACC Control-M JSON (registry `acc_controlm_repo`), optional FE Control-M JSON, token, branch constant, wrapper owner, display, books (J-R3b), **MBJ rows (J-R2 as CSV)** and the environment they were read in, template book per instrument | registry; `runs/_reference/<env>/`; the operator's query results |
| Instruments | one or several (registry `instruments` minus `skip`) — every instrument in one run | registry, the jobs plan |
| Target | branch code, token, display, **branch PK** (the MBJ rows), **branch constant** (the `db.conf` lines), wrapper owner, books register (+ `books-excluded.csv`), **`fe_run` — required** (the FE agent's run: its `acc-handoff.json` and FE job names; it must have built every instrument of this run; **the operator says which FE run to treat as OK — frozen or not, no sign-off or PR needed** `[operator, 2026-10-26]`) `[operator, 2026-10-21]`, optional `env_folder` (name conflicts), `constants` / `constant_values` (core call) | registry; J-E4; the FE run |
| Control-M | folder name, server, site standard, order method, DEV host, file path, run-as, application, calendar, `CreatedBy`, `target_repo` | **asked** — never copied. **`ControlmServer`**: the FE run's folder server unless given (FE and ACC folders on the same server, BOX team 2026-10-26). **`CreatedBy`**: the user ID of the person running the agent, asked every run — never carried over (BOX team 2026-10-26) |
| Renames | an old-named reference job the chain needs (e.g. a branch-level ruler update) → a new-convention name | the script suggests the step its siblings of the same group use; **ask** |
| External events | waits on events no job of the ACC folder or the FE folder emits (GBO, other folders) → target event, `KEEP`, `DROP`, `DROP-REVIEW`, `<OPEN …>` | **ask**, one at a time |
| MIC end of day | **not asked** `[BOX expert, 2026-10-27 — ADR 0017]`: D12 per book and 00D13 per instrument for **every** instrument, `MIC_SENDER_TYPE` `lastly` on every row; optional `mic.eod_template` (the reference instrument whose D12 / D13 an instrument without them copies; default: the first found) | fixed |
| MBJ | `sequence` (the table's own PK sequence, `OWNER.NAME` — J-E11; `BOX_ACC.SPK_T_BOX_MBJ_PROPERTIES_S`) `[BOX dev, 2026-10-26]`, `auth_code` (the target installation's), optional `group_map` (empty: event groups stay global — ADR 0014), optional `missing_rows` (override only) | J-E11; `auth_code`: Q-G3c. **No calendar question**: `FK_CALENDAR` is not read by MBJ (it uses the branch's calendar) — the reference row's value is copied `[BOX expert, 2026-10-26]` |
| Readiness | `readiness.mbj_engine`: `deployed` / `not deployed` — `BOX_ACC.PKG_BATCHPROCESS_MBJ` in the target | the operator's check (J-E9 with owner `BOX_ACC`) |
| Unix package | `scripts_dir`, `templates_dir`, `etc_dir`, `reference_unix_dir`, `reference_etc_dir`, `existing_scripts` (already in the target's etc folder) | asked |

## Rules — the chain

**What the script does** (details in its header): per instrument family `n`, seed = the ACC folder's
`GMBX<n><RT><tb>D<ss>` of the template book and `GMBX<n><RT>00D<ss>`; closure = every job of the ACC folder they
wait for; per-book jobs once per target book (`GMBX<n><TT><bk>D<ss>`), branch jobs once.

- **Initial Accounting jobs are never rebuilt here**: they come from the FE agent's `out/acc-handoff.json` (target
  name, draft job; their `db.conf` lines are the FE agent's). A job is Initial Accounting when the hand-off names it
  or its `db.conf` group is `initial_accounting.group` (BOX's `2409.65`). **The FE run is required** `[operator,
  2026-10-21]`: refused when it is missing or is not an FE run (`fe-run-missing`), has no hand-off (`handoff-missing`),
  did not build every instrument of this run (`fe-run-instruments-missing`), does not name an instrument's Initial
  Accounting job (`ia-not-in-handoff` — never named by rule), or put the jobs in another ACC folder than this run's
  (`acc-folder-mismatch`; a hand-off without a folder is warned, `acc-folder-unchecked`). Not frozen → warned.
- **Which FE run** — the operator's, in `target.fe_run`: the agent lists the FE runs of the same environment whose
  instruments include every instrument of this run (frozen or not) and **asks which one to treat as OK**. No sign-off
  of the FE run and no PR on the target's FE repos is needed before the ACC jobs are built and tested `[operator,
  2026-10-26]` (several FE runs of one instrument only: none qualifies for a run of several instruments; the FE agent
  builds them all in one run anyway).
- **Template book** (`reference.template_book`, per instrument): not given → the book with the most ACC jobs of the
  instrument (not `00` / `99`), the highest on a tie (`template-book-chosen`, counts listed). It need not be the FE
  agent's: a reference may run an instrument's ACC steps in fewer books than its FE steps.
- **Waits**: on a copied job → the target's; on the same step of every reference book (a branch job) → every target
  book's; on an FE job (not in the ACC folder) → the target's FE job of the same book, checked against the FE run's
  `out/` when given (`fe-job-not-in-fe-run`); on a dropped job or another instrument's job not in the run → that
  job's own waits; anything else → `external_events`. A per-book job waiting on another book's job →
  `reference-cross-book-wait`, never copied.
- **How each job runs** `[BOX expert, 2026-10-26 — ADR 0016]`: per-book step → `shell.conf` + MBJ row (the
  reference's own line when it has one, else the reference's `mbjbox.sh` line pattern — listed for review) — **unless
  the reference has no MBJ row for that step in any book and runs it from `db.conf`**: then `db.conf` per book, as
  the reference (`step-in-dbconf-as-reference`, warned; `mbj.missing_rows` can still force an MBJ row); branch-level step with a `shell.conf` line → the
  same; branch-level step with only a `db.conf` line → the core call
  (`PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(group, <wrapper>.PKG_GMBATCHPROCESS.<branch constant>, date, instrument, time, vstatic, NULL, NULL)` — the branch constant, never the PK, hard rule 12).
- **MIC end-of-day ("scanning") steps are mandatory** `[BOX expert, 2026-10-27 — ADR 0017]`: they send to MIC the
  accounting movements no event grouping sends (a cancelled trade, a manual movement). **D12** per branch,
  instrument and book (`MIC_FILE_TYPE` Accounting), **00D13** per branch and instrument (Revaluation), `MIC_EOD = 1`,
  no group. The reference's are copied; an instrument the reference runs without them gets them on the pattern of one
  that has them (`eod-steps-added`): each book's D12 after that book's last step, the ruler update after every
  book's D12, 00D13 after the ruler update; its rows copy the template's values with the instrument's own
  `FK_INSTRUMENT`. A copied D12 / D13 row not `MIC_EOD 1` + Accounting / Revaluation → `eod-row-unexpected`.

## Rules — the MBJ rows

- One row per `shell.conf` job. Values from the reference row of the **same job**; none → the same step in another
  book (`mbj-row-from-other-book`, warned once per step); none in any book → the step runs from `db.conf` as the
  reference (above), so it needs no row; no row **and** no `db.conf` line → refused (`mbj-row-missing`) until
  `mbj.missing_rows.<reference job>` is answered: `from:<a job of the same instrument>` (its values; the group stays
  the step's own, from its `db.conf` line) or `<OPEN …>` (the job built, its row left out, exit 4).
- **Test values** (`test_values`): the report and every SQL file say TEST, the rehearsal and config files stop at
  their first statement, exit 4, no PR — a test run is never deliverable.
- **The target's own**: `FK_BRANCH` (branch PK), `FK_LABEL` (looked up by the target book's label code with
  `f_getPKByLabel` — never a typed PK; branch-level rows `NULL`), `MIC_SENDER_TYPE` **`lastly`** on every row
  (BOX expert, 2026-10-27), `FK_GROUP` (the reference's global group unless `mbj.group_map`).
- **Copied**: `FK_CALENDAR` (not read by MBJ — the engine uses the branch's calendar, BOX expert 2026-10-26),
  instrument (a global PK), workers, tasks, workers by events, concurrency, MIC file type / end of day /
  flow mode, monitor values and file pattern, return data, recover flags; `FK_OWNER_OBJ` `35000182.65` (BOX - MBJ
  Properties, J-T8); `FK_PARENT` `NULL`.
- A reference row whose label is not its name's book is a reference defect: listed, never copied (the target row
  takes its own book's label). A reference row with a sub-label → refused.
- **The SQL** `[BOX dev, 2026-10-26 — ADR 0016]`: a read-only **precheck** first, the counterpart of the FE configs
  agent's pre-step P1 — the sequence (`mbj.sequence`) exists and its next value is above the table's highest PK of
  this installation's fraction; otherwise `MBJ PK PRECHECK PROBLEM` and a proposal for the BOX team (move the
  sequence). Then: the installation's auth code checked; every PK = `<sequence>.NEXTVAL` + the fraction, checked
  (fraction, not already in the table); pre-flight (no row for these jobs yet, the reference rows' calendars exist,
  each label exists) and a self-check count; rehearsal ends in `ROLLBACK` (its sequence values are skipped — gaps are
  harmless), config in `COMMIT`, rollback deletes exactly its rows.

## Readiness — never blocking

The MBJ engine `BOX_ACC.PKG_BATCHPROCESS_MBJ` (only in `BOX_ACC`; a `PGT_PRG` package of the same name is not BOX's)
and the Unix side (`mbjbox.sh`, `MBJBOXACC.jar` with its `conf/BOX` pointing at the target database) must be in the
target for the jobs to run. The files are built either way; the report and verify V2 say what is missing.

## Outputs — `out/`

| File | Content |
|---|---|
| `<FOLDER_NAME>.json` | the target's ACC Control-M `SimpleFolder` |
| `shell.conf.proposal` | one `mbjbox.sh` line per per-book step and branch MIC step, one banner per instrument |
| `db.conf.proposal` | the branch-level `db.conf` steps as the core call (none for Initial Accounting) |
| `sql/<BASE>-mbj-{rehearsal,config,verify,rollback}.sql` | the MBJ rows |
| `mapping.csv` | reference job → target job(s), level, book, how it runs, the MBJ row its values came from |
| `unix/` | `job_unix.sh` (shell.conf and db.conf), `shell_nuevo.conf`, `db_nuevo.conf`, the delete lists, the target's copies of the two scripts |
| `pr/` | `scripts/stage_target_pr.py`: the folder JSON under the target ACC repo's name + `pr-summary.md` |
| `report.md` | per instrument, how they run, readiness, decisions to review, OPEN, warnings |
| `../pending-questions.md` | renames and external events still to answer, with a suggestion each |

Not generated yet: the ACC folder's environment descriptors (`pre.json` / `pro.json`) — the report says so; the
per-environment values are the BOX team's until the reference ACC descriptors are copied and a later version
translates them.

## Hard rules

1. **Read-only on every BOX repo**, with the one exception of [ADR 0012](../../docs/decisions/0012-target-repo-pr-exception.md):
   the **target branch's own** ACC Control-M repo (registry `acc_controlm_repo`), only `projects/<repo>.json`, only a
   **PR from a new branch** (never a push to the default branch, never a merge), only after the operator's **yes** on
   `out/pr/pr-summary.md`.
2. **No database.** The SQL is a proposal the BOX team runs; the agent never connects to or runs anything against an
   environment.
3. **The files are rendered by the script**, never written or patched by hand.
4. **Environment values are asked, never copied** (folder, server, site standard, host, order method, application,
   calendars, run-as); `CreatedBy` is never a reference developer ID: the user ID of the person running the
   agent, asked every run.
5. **Only executed reference jobs**, of the instruments in the run; ended jobs (past `EndDate`) not copied.
6. **New-convention names only** (`GMBX<n><CC><nn>D<ss>`), also for renamed old jobs.
7. **Every per-book ACC step runs through `shell.conf` + an MBJ row** `[operator, 2026-10-21]`.
8. **MIC end-of-day steps for every instrument, sender `lastly`** — never dropped, never asked (ADR 0017).
9. **Privacy.** Book descriptions stay in the run folder; no developer IDs anywhere.
10. **Never blocked by an optional input or a readiness gap** (the FE Control-M JSON, the MBJ engine — the jobs can be
    built and reviewed before the BOX team deploys it): the run goes on and the report says what was not checked or
    cannot run yet. The FE run is **not** optional: without it the Initial Accounting names and the FE waits would be
    guesses.
11. **Only answers the script has an input for** `[operator, 2026-10-21]` — a refusal no input answers is a script
    gap: stop and say so; never edit the script, an evidence CSV or `out/` to get past it. Values not asked in the
    session (inputs file, the FE run) are listed with their source and confirmed before the first build.
12. **No fixed values in a `db.conf` line where the target has a name for them** `[BOX team via operator, 2026-10-22]`:
    the core call's branch argument is the target wrapper's **branch constant** (`target.branch_const`, the same as the
    FE run's — `branch-const-mismatch`; checked in the FE run's J-E4 CSV — `branch-const-unknown`), never the branch
    PK typed in; the time's colons built with `CHR(58)` (`dbconf-colon`). `target.branch_pk` stays: the MBJ rows'
    `FK_BRANCH` and the checks.

## Human checkpoints

| # | What | Who |
|---|---|---|
| 1 | the reference branch and the template book per instrument | operator |
| 2 | each rename and external event; the end-of-day steps added to an instrument (`eod-steps-added`) | operator; BOX expert |
| 3 | `mbj.sequence` (J-E11) and the precheck's result (`MBJ PK PRECHECK OK`, or the BOX team moves the sequence) | operator / BOX team |
| 4 | `out/` reviewed; the SQL run (rehearsal, then config) | BOX team |
| 5 | each PR on the target's ACC repo | operator, one yes per repo |

## Relationship with other agents

- **`box-fe-jobs-agent`** — runs first: its `out/acc-handoff.json` names the Initial Accounting jobs and writes their
  `db.conf` lines; its FE folder emits the D04 / D06 events the ACC steps wait for.
- **`sigom-box-acc-configs-agent`** — the accounting screens; event groups stay **global** (no branch copy, ADR 0014),
  so `mbj.group_map` stays empty.
- **`box-batch-jobs-agent`** — explains reference jobs (EXPLAIN) and the readiness queries (J-E9, J-R2).

## Skills and scripts it may call

| Skill | For | Script |
|---|---|---|
| [`find-box-jobs`](../../skills/find-box-jobs/SKILL.md) | the reference's ACC jobs and their order (`--side ACC`) | `scripts/find_jobs.py` |
| [`explain-box-job`](../../skills/explain-box-job/SKILL.md) | "what does job X do?" mid-run; the context of each pending question | `scripts/explain_job.py` |
| — | the files | `scripts/build_acc_jobs.py`, `scripts/unix_package.py`, `scripts/stage_target_pr.py`, `scripts/new_run.py` |
| — | the regression check | `scripts/regress_fe_jobs.py` (FE and ACC runs) |

## Eval cases

[`evals/cases/box-acc-jobs-agent.md`](../../evals/cases/box-acc-jobs-agent.md) — the cases the tests cover, the
regression check and the session checklist.

## Open questions (about the agent — a branch's questions are in its open items)

1. ~~The PK allocation of `T_BOX_MBJ_PROPERTIES_S`~~ — the table's own sequence, checked by the precheck (BOX dev,
   2026-10-26, ADR 0016).
2. The ACC folder's environment descriptors: translate the reference's once its copies are available.
3. Which source is the reference's truth when its MBJ rows and its conf files disagree (they may come from different
   environments): the agent copies the MBJ rows of the CSV it is given and lists the gaps.
