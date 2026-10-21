---
name: box-fe-jobs-agent
description: Generates a new branch's BOX FE batch jobs for one instrument or several - the db.conf lines, the Control-M folder JSONs (FE, prerequisite folders), the environment descriptors and the Unix package - by copying an onboarded reference branch's executed chain (found with skill find-box-jobs), renamed, re-wired per book and re-hosted for the target. Branch-agnostic. Asks the operator for every target value it cannot derive. Writes proposal files only; never deploys, never edits a BOX repo.
---

# BOX FE Jobs Agent

Scope `[stated: operator, 2026-10-02]`: BOX **FE** jobs only (`db.conf` + Control-M) for a new branch, from a reference branch already in BOX. ACC
jobs (`shell.conf` + MBJ rows) are [`box-acc-jobs-agent`](../box-acc-jobs-agent/AGENT.md)'s. Searching and explaining jobs stays with
[`box-batch-jobs-agent`](../box-batch-jobs-agent/AGENT.md); both use skill
[`find-box-jobs`](../../skills/find-box-jobs/SKILL.md). Why: [ADR 0010](../../docs/decisions/0010-box-fe-jobs-agent.md);
the PR exception: [ADR 0012](../../docs/decisions/0012-target-repo-pr-exception.md); history: `CHANGELOG.md`.

**Asked to run this file?** It is the charter (the rules), not the procedure: follow
[`prompts/build.md`](prompts/build.md) from Step 0 — it reads this file at Step 1.

## Goal

Given a **reference branch** (onboarded, Tier 1), one or more **instruments** and a **target branch** (the branch
being onboarded), produce the files the BOX team would otherwise write by hand, **with the same chain as the
reference** — every job, order and hand-off accounted for, in the order they run `[stated: operator, 2026-10-06]`:
1. the target's **prerequisite folders** — the load prices (fixing curves, market data) the FE batch waits for, and
   the scheduling monitor;
2. the target's **FE folder** JSON;
3. the target's FE **`db.conf`** lines (prerequisite lines first);
plus the reference's **environment descriptors** (`pre.json`, `pro.json`) re-pointed to the target, the Unix package,
and the hand-off of the Initial Accounting jobs to the ACC jobs agent.

Correct means: every target job comes from a named reference job (file:line); every wait resolves to a job of the
new folders or to an external event the operator mapped; nothing in the target is copied from the reference that
belongs to the reference's environment (host, server, calendar, application, developer ID). A value the agent
cannot source is a question to the operator, never a guess.

## Branch-agnostic by construction

**No branch, environment, owner, constant, job or folder name is written here** — a test fails if one is
(`scripts/tests/`). Where branch-specific content lives:

| What | Where |
|---|---|
| A target branch's values and answers | its inputs file `runs/<BRANCH>/<tier>-<env>/fe-jobs/fe-jobs-inputs.<BRANCH>.json` (shape: [`templates/fe-jobs-inputs.example.json`](templates/fe-jobs-inputs.example.json)), copied into each run |
| A target branch's decisions, history and worked example | `runs/<BRANCH>/<tier>-<env>/fe-jobs/README.md`; its questions: `runs/<BRANCH>/<tier>-<env>/jobs/99-open-items.md` |
| What we know about a reference branch's chains (books, defects, products) | `docs/reference/job-chains/reference-<branch>-fe.md` (e.g. [`reference-slb-fe.md`](../../docs/reference/job-chains/reference-slb-fe.md)) |
| How BOX batch works (all branches) | [`box-batch-chain.md`](../../docs/reference/job-chains/box-batch-chain.md) |
| The procedure | [`prompts/build.md`](prompts/build.md) — the same for every branch and tier, run directly (it asks the branch) or from a branch's optional kickoff in [`prompts/`](prompts/) that names the branch and environment and nothing else |

## Definition of done

Done for one (target branch, set of instruments) when:
1. `scripts/build_fe_jobs.py` exits **0**, or **4** with every OPEN line explained (checkpoint 3);
2. every input in `fe-jobs-inputs.json` was derived from cited evidence or answered by the operator — none guessed;
3. `out/report.md` lists the external events with their mapping, the decisions to review and the hand-off events;
4. the BOX team has reviewed `out/` (checkpoint 4) — until then the files are a proposal.

## Inputs — `runs/<BRANCH>/<tier>-<env>/fe-jobs/<name>_<YYYYMMDD>_<n>/fe-jobs-inputs.json`

| Group | Values | Where they come from |
|---|---|---|
| Reference | env folder (job confs + inventory), Control-M JSON of the branch's FE folder repo, token, branch constant, wrapper owner, display name, books (J-R3b), template book per instrument, shared-jobs book | token, constant, wrapper, repo: [`branch-registry.csv`](../../docs/reference/branch-registry.csv); `runs/_reference/<env>/`; **ask** for the rest |
| Instrument | one of `depos`, `irs`, `ccs`, `cfm`, `fra`, `otc`, `cap`, `commodities`, `cds` — **or a list: every instrument in one run** | the target's list is the registry column **`instruments`** — never asked again; the operator picks which to build |
| Reference branch | per instrument: the onboarded branch that runs it — `find_jobs.py --product <i> --references`; the preferred one if it does, else another | registry rows; operator confirms |
| Jobs plan | `runs/<BRANCH>/<env>/fe-jobs/instrument-plan.csv` (or `target.instrument_plan`): per approved instrument `to build` / `in progress` / `done` or `built` (its jobs exist for the target: another instrument's waits on them are kept) / **`skip`** (with reason and source), and an optional **forced** `reference`. An instrument no onboarded branch runs in BOX is `skip` — never built, never asked; the scope list itself stays in the registry | operator decides `skip` and forced references |
| Target | branch code, token, display, wrapper owner, **wrapper argument count (5 / 7)**, branch constant, other wrapper constants, books register; **`dbconf_format`** `wrapper` (default) or `pgt_prg` (the core call, `core_call`) with **`branch_pk`** (the branch constant's value, J-E4) and optional `core_time`; optional `constant_values` (reference and target: `CST_…` → value) | registry row (add it if missing); J-E1 / J-E4 / J-E10 in the target; skill `set-up-book-labels` |
| Control-M | folder name, `ControlmServer`, `SiteStandard`, `OrderMethod`, **`Host` = the DEV host** (a folder file is the DEV definition `[BOX expert, 2026-10-07]`), **`FilePath`**, `RunAs`, `Application`, `MonthDaysCalendar`, `CreatedBy`; **`env.<pre.json\|pro.json>`**: the target's per-environment values written into its descriptors (`Host` mandatory; `ControlmServer`, `OrderMethod`, `StartDate` = an activation date the reference adds); optional `DocumentationFile`, `host_config_repo` / `host_by_env` | **asked** (or pre-filled in the branch's inputs file) — environment values, never copied. A per-environment property not given keeps the reference's value in the descriptor and is listed **to confirm**; `Host` is never guessed |
| Renames | old-named reference jobs the chain needs (e.g. the branch's queue job) → a new-convention name | the script lists them in `pending-questions.md` with a suggestion; **ask** |
| External events | waits on events no job of the reference folders emits (other folders, GBO jobs) → target event, `KEEP`, `DROP` or `DROP-REVIEW` | the script lists them in `pending-questions.md`: emitter, folder, side · product · level, suggestion; **ask** |
| Prerequisite folders | `prerequisites[]`: the reference's prerequisite folder JSON (registry `prereq_controlm_repos`, e.g. the load-prices repo), the target's folder name, optional `descriptor_dir`, `controlm` overrides (default: the FE folder's values), `jobs` (only if nothing links them), `select: instruments` (scheduling monitor), `group_map` | attach the repo; **ask** the folder name |
| Descriptors | `reference.descriptor_dir`: the environment config repo's folder for the reference FE repo (registry `env_descriptor_repo`, e.g. `cib-auki-aukicnfgsrvc/<repo>/`) — the environment-only waits live there | attach (read-only) |
| Data Lake | `datalake.reference_json` / `target_json`: the Data Lake (AUKI) Control-M JSONs (`cib-auki-aukictrlmcntrm`); `datalake.book_map` only for a target book whose label description is not its `book_vr` | copies in `runs/_reference/external/` when the repo cannot be attached |
| Target's own jobs | `target.env_folder`: the target environment's `db.conf` / `shell.conf` (+ inventory) — a generated name already used there is refused (`target-name-exists`), and its look-alike of a reference GBO job is proposed | `runs/_reference/<tier>-<env>/` |
| Target's GBO folders | `target.gbo_folders`: `[{path, env}]` — the target's GBO Control-M folder JSON per environment, **optional, never required**: with it, every GBO event answer is checked against what the target really emits | **ask once** whether the operator can provide it; `target.gbo_event_override` for an event emitted by a folder not attached |
| Initial Accounting | `initial_accounting.group` (one group or a list), `acc.folder_name` / `acc.Application` (the target's ACC folder, for the hand-off) | `[BOX job expert, 2026-10-08]`; ACC values asked, `<ask>` kept in the draft otherwise |
| Excluded books | `books/books-excluded.csv` beside the register (or `target.books_excluded`): `code, description, scope (jobs \| all), reason, source, date` — no per-book job, no `db.conf` line, no Data Lake question; delete a row to create the book's jobs; after the build any of their jobs or labels in `out/` is refused (`excluded-book-built`) | operator |
| Run folder | **versioned, one per run:** `runs/<BRANCH>/<tier>-<env>/fe-jobs/<instrument or all>_<YYYYMMDD>_<n>/` (`scripts/new_run.py`); the environment is asked first; a new environment is created empty with what it lacks listed; answers carried over only from a run the operator names, one by one; a finished run is frozen (`.frozen`) and never written again (`run-frozen`) | operator |
| Target repos | `controlm.target_repo`, `prerequisites[].target_repo` (registry `fe_controlm_repo`, `prereq_controlm_repos`) — the PR step | registry |
| Unix package | `unix.scripts_dir` (default `controlm.FilePath`), `templates_dir` (default `<scripts>/templates`), `etc_dir` (where `add_new_jobs.ksh` is), `existing_scripts` | asked |
| Several instruments | `separate_run` (only when an instrument built in another run is deployed and its shared jobs stay valid: the reason) | operator |
| Optional | `reference.controlm_other` (the reference's ACC folder repo, GBO / shared folders), `reference.dml_repos` (`cib-boxfin-dbboxfe`, `cib-boxacc-dbboxacc`), `reference.mbj_csv` (J-R2), `target.instruments` (approved for the target), `target.local_group_suffix` | attach / **ask**; without them the suggestions say less |

## How it works

1. **Reference chain** — skill `find-box-jobs`: the reference's executed FE jobs for the instrument, with order
   (`find_jobs.py --side FE --product … --branch … --controlm <reference folder repo>`). Show it to the operator.
2. **Inputs** — write `fe-jobs-inputs.json` with everything derivable; **ask the operator for each `<...>`, one
   at a time**, offering the reference value where one exists ("the reference uses `<value>` — the same for the
   target?").
3. **Build** — `python3 scripts/build_fe_jobs.py <run folder>/`. A refusal names the input to ask for
   (`input-missing`, `rename-missing`, `external-event-unmapped`, `constant-unmapped`, `gbo-event-not-emitted`…):
   ask, write it, run again. Never edit the outputs. For renames and external events, ask the rows of
   `pending-questions.md` one at a time, each with its context and suggestion (below).
4. **Present** `out/report.md`: target jobs per level, the external events and how each was mapped, the decisions
   to review, the hand-off events (`G0…-…`) other folders may wait for, OPEN lines, warnings. Exit `4` = written with
   OPEN lines.

**Suggestions in `pending-questions.md`** `[operator, 2026-10-06]` — a proposal, never written unasked:

| The emitter of the event is… | Suggested |
|---|---|
| a reference job of an instrument approved for the target (`target.instruments`) | its target name (`GMBX<n><TT>00D<ss>-OK`, prefix kept) |
| a reference job of an instrument not approved | `DROP` |
| ended (`When.EndDate` past) | `DROP` |
| an old-named job with new-named siblings of the same group in the reference | the target's sibling name (`GMBX<n><TT>00D<ss>-OK`); for an ACC job, `DROP` until the target's ACC folder has it `[2026-10-07]` |
| an ACC job | `DROP` / `DROP-REVIEW` for now; later the target's ACC equivalent — **never `KEEP`** (it is the reference branch's own job; `KEEP` of a reference-token event is refused) |
| a GBO job | the target's look-alike in `target.env_folder` (skill `explain-box-job`, `explain_job.py --target`: same group with the wrapper constants resolved — `J-E4b-*.csv` in each environment folder —, then same script and similar parameters, then same function and first argument **by value**; below a confident match the card says **no confident match**), INFERRED; its exact event read from the target's GBO folder when given; none → ask the GBO team |
| not found in the repos attached / another branch's job / an old-named job | ask the BOX team |
| *(rename)* an old-named branch job | the step of its new-named siblings of the same group; none → `GMBX<0 or the instrument's n><TT>00D<its step>` |

**Questions mid-run** — the operator may ask *"what does job X do?"* at any point: run skill
[`explain-box-job`](../../skills/explain-box-job/SKILL.md), answer with its card, then **repeat the pending question**.
Deeper than overview (an event's entries) is `box-batch-jobs-agent` EXPLAIN.

## Rules — the chain

**What the script does** (details in its header): seed = the instrument's executed `db.conf` jobs of the template book
and of branch level; closure = every job of the same folders they wait for (the book's `GMBX0…D01-D03`, the branch's
queue job…); copy = per-book jobs once per target book, branch jobs once; events renamed the same way; a wait on
"the same step of every reference book" becomes a wait on every target book's; `db.conf` lines with job, wrapper
owner, constants and label swapped.

- **Only executed reference jobs** (hard rule 4). A conf line with **no Control-M job** in any folder repo given is not
  copied (`dbconf-only`): ask the BOX team whether the target needs it. A step run through `shell.conf` / MBJ is an
  **ACC** job: not built here; an FE job waiting for it loses that wait, recorded `DROP-REVIEW`.
- **Instrument scope** — another instrument's job (`GMBX<n>`, `n` not this instrument's and not `0`) is **never
  copied**, even when a copied job waits for it. The wait is replaced by that job's own waits — unless that instrument
  is in the run or `built` / `done` in the jobs plan: then the wait is kept, renamed to the target's job. OR-groups
  (`[{…}, {…}, "OR", …]`): an empty group goes, duplicate groups go. The report lists the inherited waits.
- **Every event is renamed**, also in `If:CompletionStatus` → `Event:Add` blocks (`<JOB>-NOK`), and counts as emitted.
- **Ended** = a past `When.EndDate` in the folder file that **no descriptor deletes**; a descriptor `Delete` of it
  means the job runs there: copied, without EndDate (listed). EndDate deletes are not copied.
- **Old-named per-book jobs of other reference books**: recognised by their `db.conf` label and matched to the
  template book's job of the **same group**: a wait on one is that step of each target book — never renamed, never
  copied.

**Reference books** `[Devin read-only check, 2026-10-15]` — two choices, both made by the script from the inputs, the reference folder and its `db.conf`
labels, and shown in `out/report.md`:

- **Template book** (per instrument, `reference.template_book`, may be `{instrument: book}`): the book whose instrument
  jobs are copied. Not given → the book with the most active jobs of that instrument (not `00` / `99`), the
  highest-numbered on a tie (`template-book-chosen` lists the counts) — never "the first book".
- **Shared-jobs book** (`reference.generic_book`, one for the run): the book whose `GMBX0<RT><bk>D01-D03` are copied for
  every target book. Candidates: complete, new-named, not `99`, no cross-book wait. Not given → the majority form (each
  step compared without book number, label, description, file name or developer; Data Lake waits by type), on a tie
  the template book's, else the highest (`generic-book-chosen`; `generic-books-differ` when the books differ → BOX
  expert). A wait on another book's shared job (also old-named, matched by label and group) is read as the chosen
  book's. A reference job waiting on **another book's** job → `reference-cross-book-wait`: that book is not a
  candidate, reported to the BOX team, never copied.
- A pattern that differs between reference books (a step FE in some books, ACC in others) follows the template book —
  say it, the BOX expert confirms.

**Several instruments, one run** `[operator, 2026-10-08]` — each instrument is built as in a one-instrument run knowing the others are built,
so their waits on each other are kept; then ONE set of outputs: each job once (a shared job built differently by two
instruments → warning), descriptors and `db.conf` lines de-duplicated. Per-instrument detail in
`out/parts/<instrument>/`. Every instrument not deployed yet is built **in the same run** (hard rule 6). Adding an
instrument later: re-run with every instrument not yet deployed; a deployed one is `deployed` in the plan and a later
run gives `separate_run`.

## Rules — waits on other folders, environments and teams

**Prerequisite folders and descriptors** `[BOX dev via operator, 2026-10-06]` — a reference FE chain may wait for jobs of another folder (the load
prices), and only in some environments: the wait is added by a descriptor (`pro.json` / `pre.json`), not by the folder
file. The script reads the descriptors as waits; the prerequisite jobs the chain waits for (and theirs) are copied to
the target's prerequisite folder — the other branch's jobs of that folder are left out — with new names
`GMBX0<TT>00D01`, `D02`… in chain order. Descriptor entries are re-pointed to the target folders and jobs
(`out/descriptors/<folder>/<env>.json`); the target's folder file keeps **no** environment-only wait, as the reference.
Every entry type, per environment and per folder: `Property` + `Replace` regex copied (site standard `_D_` →
`_I_` / `_P_`, application, folder `JACD-` → `JACI-` / `JACP-`); `Property` + `Assign` from `controlm.env`; `Add`
re-pointed (events re-wired, `StartDate` from `controlm.env`, `$.DocumentationFile` `CRITICO` copied); `Delete`
re-pointed. A Data Lake wait keeps its environment letter (`PAUKI…` PRO, `IAUKI…` PRE). Entries
for other instruments are listed; an entry carrying a reference environment value (host…) or for one reference book
only is **review**, never guessed. Missing `Host` / `ControlmServer` entry → flagged (mandatory). Two jobs with the
same name (e.g. a rename on `GMBX0<TT>00D01`) → refused, with the next free name suggested.

**Data Lake waits — per book** — in PRO a book's steps wait for its book's Data Lake jobs (`G0…-<prefix><DD|DDOTC|FD|MD>
<desk>001D-OK`: deals and flows on D01, market data on the instrument's first step). The link between a BOX book and
its Data Lake jobs is the **book label description = the Data Lake `book_vr`** `[operator, 2026-09-30]`; the desk token is the same across a
book's jobs. The reference book's Data Lake job gives the type; each target book gets the target's Data Lake job of
that type under its own description. A target book without one → a question (closest `book_vr` listed;
`datalake.book_map`). A branch-level job waiting for one book's Data Lake job is not mapped — asked.

**GBO events** — a wait on a GBO job shows what it runs (its `db.conf` call) and, with `target.env_folder`, the
target's look-alike, INFERRED: the operator confirms with the GBO team.
- **Event spellings are the target's own** (they may differ from `<JOB>-OK`, e.g. a suffix after `-OK`, emitted by If
  blocks). With `target.gbo_folders` the script refuses an answer no GBO job emits (`gbo-event-not-emitted`, closest
  names listed) and warns for a wait used only in an environment whose GBO folder is missing (`gbo-event-unchecked`);
  without it the run goes on and the report lists the answers as **not checked** (`gbo-events-not-checked`).
- **A functional equivalent can be a different pipeline** loading the same data (a legacy file vs a Data Lake file):
  the look-alike search ranks by function and arguments and will not find it — read what the job loads. A job that
  only exists as a conf line (not scheduled) emits nothing: never wait for it.
- **A target with no equivalent** (a feed the target does not have) → `DROP-REVIEW`, and the question goes to the BOX
  expert when the job behind the wait may need the data (not only the order).

**Control-M servers** — a folder file in the repos carries the **DEV** server; PRE / PRO servers are deployment
values (`controlm.env`). A plain event (`<JOB>-OK`) only reaches jobs on the **same** Control-M server; across servers
events are global, prefixed `G<6 digits>-` (convention INFERRED). So the target's BOX folders run on the server of the
GBO jobs they wait for, unless those jobs emit global events — check it per environment; a server not known for an
environment stays **to confirm**, never copied from the reference.

**External-event answers** — a target event, `KEEP` (the same shared event), `DROP`, or `DROP-REVIEW` (dropped and
listed under "Decisions to review"). A placeholder (`{…}`, `<OPEN …>`) is **OPEN** in the report (exit 4), never
delivered; `<ask …>` or empty is unanswered (refused). Use `<OPEN - what, who confirms>` for an answer still owed by
another team.

## Rules — what is generated besides the folders

**Initial Accounting** `[BOX job expert, 2026-10-08]` — the Initial Accounting group(s) (`initial_accounting.group`: BOX's `2409.65` "BOX - Initial
accounting (PP, Recla, Reval)" — events Get PP and Strategy, Reclassification, Reclassification PyG, Event
Revaluation Position Expired, Load Attributes; a list when the reference runs another such group for an instrument), one branch-level job per
instrument. The **only ACC jobs the FE chain needs**: the book's `D02` waits for them. Defined in the ACC Control-M
folder, run from **`db.conf`**. Per instrument built, the agent: names it `GMBX<n><TT>00D02`; writes its `db.conf` core
line (own banner, before the FE lines); re-wires the FE waits on it with no question (an instrument not built →
dropped, listed); hands it to **`box-acc-jobs-agent`** in `out/acc-handoff.json` (db.conf line, its group, who waits,
events to emit with their `G0…-` prefixes, a draft ACC job from the reference's with the target's values). The ACC
folder JSON is the ACC agent's.

**Scheduling monitor** `[BOX job expert, 2026-10-09]` — fills the branch process calendar (`BOX_FE.T_BOX_BRPROCCAL_S`); must have run before the FE
groups. Its own Control-M folder and repo: one branch-level job per instrument `GMBX<n><TT>00D06`, chained by
instrument; no FE job waits for it. Built as a prerequisite folder **selected by instrument** (the reference branch's
jobs of the instruments built; a wait on another instrument's → inherited); its `db.conf` lines with the global group
(BOX's global `2935.65`; `group_map` maps a reference's local group — suffix `.21` — to it;
`target.local_group_suffix` refuses an unmapped one, `local-group-unmapped`), own banner, its own descriptors and target repo (asked).

**`db.conf` format** with `dbconf_format: pgt_prg`: `<JOB>:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(P_GROUP,
P_BRANCH, P_DATE, P_INSTRUMENT, P_TIME, P_VSTATIC, P_LABEL, P_SUBLABEL);` — the group from the reference; **the
branch PK (`target.branch_pk`) on every line**, per-book ones too; the date `to_date('$ODATE','YYYYMMDD')`; the
instrument constant, **`NULL` for `CST_PK_VACIO`**; **`P_TIME` = `to_char(sysdate,'RRRR-mm-DD HH24:MI:SS')`**;
`P_VSTATIC` `0`; the book's label (`NULL` at branch level); sub-label `NULL` `[BOX Lead, 2026-10-07; BOX job expert's corrections, operator, 2026-10-07]`. Names:
`GMBX0<TT>00D01/D02` load prices, `GMBX<n><TT>00D01` queue, `GMBX<n><TT>00D02` initial accounting,
`GMBX0<TT><bk>D01-D03` shared per book.

**Unix package** `[BOX job expert, 2026-10-08]` — `out/unix/job_unix.sh` (script `scripts/unix_package.py`, shared with `box-acc-jobs-agent`; one
package per agent), laid out as Tier 1's existing BOX packages: **first** `sh -x <etc>/delete_jobsBX.ksh db.conf <etc>/db_delete.txt` removes every job line of the
package (and its banners) from the target's `db.conf`, so a re-delivery replaces lines instead of doubling them —
which is also why two separate runs overwrite each other's shared jobs; then `sh -x <etc>/add_new_jobs.ksh db.conf
<etc>/db_nuevo.conf` (`db_nuevo.conf` = `db.conf.proposal`); then per `db.conf` job `cp <templates>/db_job
<scripts>/<JOB>` and `chmod 755`. No etc folder → the line is OPEN.

## Outputs — `out/`

| File | Content |
|---|---|
| `db.conf.proposal` | the target's FE lines, one banner per folder (prerequisites first); `wrapper` format: a line the target wrapper cannot run (label, 5-argument wrapper) is commented `# OPEN checkpoint 3`; `pgt_prg` format: every group line as the core call (T:P), no OPEN line |
| `<PREREQ_FOLDER>.json` | each prerequisite folder (load prices, scheduling monitor) — runs first |
| `<FOLDER_NAME>.json` | the target Control-M `SimpleFolder` |
| `descriptors/<folder>/<env>.json` | the reference's environment descriptors re-pointed to the target — a proposal for the environment config repo |
| `mapping.csv` | reference job → target job(s), level (incl. `initial-accounting`), book, `shared_across_instruments`, `db.conf` source line, status (+ `instrument` in a several-instruments run) |
| `acc-handoff.json` | for `box-acc-jobs-agent`: the Initial Accounting jobs (db.conf line, group, ACC folder, who waits, events to emit, draft job) |
| `unix/` | for the target's etc folder: `job_unix.sh` (delete, add, `cp db_job` + `chmod 755` per job), `db_nuevo.conf` (= `db.conf.proposal`), `db_delete.txt` (its jobs and banners), the target's `delete_jobsBX.ksh` / `add_new_jobs.ksh` (the reference's, `cd` to the target's etc folder, author line out; a missing one is said) |
| `parts/<instrument>/` | several-instruments run: each instrument's own outputs, before the merge |
| `pr/` | `scripts/stage_target_pr.py`: `pr/<repo>/projects/<repo>.json` (the folder JSON under the repo's name) and `pr-summary.md` — what the PR would add, for the operator's yes / no |
| `report.md` | the summary above |
| `../pending-questions.md` | written when renames / external events are missing: one row per question with context and a suggestion; "None" once all are answered |

## Hard rules

1. **Read-only on every BOX repo** (`cib-boxfin-dbboxfe`, `cib-boxacc-dbboxacc`, every Control-M folder repo, the
   environment config repo `cib-auki-aukicnfgsrvc`): no commit, branch, push, PR, draft PR, suggested diff or edit. Outputs go in this repo's run folder.
   **One exception** ([ADR 0012](../../docs/decisions/0012-target-repo-pr-exception.md)): the **target branch's own**
   Control-M repos of the registry (`fe_controlm_repo`, `prereq_controlm_repos`), only `projects/<repo>.json`, only a
   **PR from a new branch** (never a push to the default branch, never a merge), only after the operator's **yes** on
   `out/pr/pr-summary.md`.
2. **The files are rendered by the script**, never written or patched by hand.
3. **Environment values are asked, never copied** from the reference: folder name, server, site standard, host (the
   folder file: the **DEV** host; PRE / PRO: `controlm.env`), **order method** (time zone, per environment `[BOX expert, 2026-10-08]`), script
   path, run-as, application, calendar. `CreatedBy` is never a reference developer ID.
4. **Only executed reference jobs** (FE = `db.conf`); a legacy `db.conf` line is not a template, and a job whose
   `When.EndDate` is past — and that no descriptor deletes — has ended: not copied (a wait on it becomes an external
   event to map). **Only this instrument's jobs** (and generic `GMBX0` / branch prerequisites) are copied. Start times
   (`FromTime`) are copied and listed in the report for review.
5. **New-convention names only** (`GMBX<n><CC><nn>D<ss>`), also for renamed old jobs.
6. **Per-book jobs `GMBX0…` and branch prerequisites are shared by every instrument** — one copy of each
   (`shared_across_instruments`), **from one reference book** (`reference.generic_book`), and every instrument whose
   jobs are not deployed yet is built **in the same run**: the shared jobs' waits depend on the instruments built, so a
   second run would overwrite the first's. An instrument marked `built` in the plan but not in this run → refused
   (`shared-jobs-other-run`); the operator adds it to the run or gives `separate_run` with the reason.
6b. **Every pending question carries its reference context** — the reference job(s) behind it (skill
   `explain-box-job`: what it runs, who waits for it, its events) and the reference's example of the answer, never a
   bare name.
7. **Privacy.** Book descriptions stay in the run folder; no developer IDs anywhere; a copied GBO folder JSON has its
   `CreatedBy` removed.
8. **Never blocked by an optional input** (the target's GBO folders, the reference's ACC repo, the MBJ CSV): without
   it the run goes on and the report says what was not checked.

## Human checkpoints

| # | What | Who |
|---|---|---|
| 1 | The reference branch, the template book per instrument and the shared-jobs book | operator |
| 2 | Every asked input (Control-M values, renames, external events) | operator |
| 3 | Label lines: with `dbconf_format: pgt_prg` the core call takes the label. With `wrapper` and a 5-argument wrapper they stay OPEN until the wrapper takes a label (`wrapper_args = 7`) | BOX Lead |
| 4b | The PR of `projects/<repo>.json` on each target repo — yes / no on `out/pr/pr-summary.md` | operator |
| 4 | The generated files, before anyone deploys them — incl. the descriptors' **review** lines, the decisions to review, and whether an environment-only wait (e.g. load prices in PRO only) should also be in the other environment | BOX team |

## Relationship with other agents

- **`box-batch-jobs-agent`** — searches and explains; its GAP run is the analysis, this agent writes the FE files.
- **Skill `set-up-book-labels`** — the target's books register (book codes and descriptions).
- **ACC jobs** (`shell.conf` + MBJ rows) — [`box-acc-jobs-agent`](../box-acc-jobs-agent/AGENT.md), from
  `out/acc-handoff.json`, MBJ rows included.

## Skills and scripts it may call

| Skill | For | Script |
|---|---|---|
| [`find-box-jobs`](../../skills/find-box-jobs/SKILL.md) | the reference chain and its order | `scripts/find_jobs.py`, `scripts/parse_job_confs.py` |
| [`set-up-book-labels`](../../skills/set-up-book-labels/SKILL.md) | the target's books | `scripts/set_up_book_labels.py` |
| [`explain-box-job`](../../skills/explain-box-job/SKILL.md) | "what does job X do?" mid-run; the context of each pending question | `scripts/explain_job.py` |
| — | the files | `scripts/build_fe_jobs.py`, `scripts/unix_package.py`, `scripts/stage_target_pr.py`, `scripts/new_run.py` |
| — | the regression check | `scripts/regress_fe_jobs.py` |

## Eval cases

[`evals/cases/box-fe-jobs-agent.md`](../../evals/cases/box-fe-jobs-agent.md) — the cases the tests cover, the
**regression check on a finished run** (`scripts/regress_fe_jobs.py`: same answers → same files) and the **session
checklist** for a real Devin run (what the tests cannot see).

## Open questions (about the agent — a branch's questions are in its open items)

1. Who waits for `G010014-…-OK` hand-off events (none of the indexed repos does — monitoring, or a repo outside the
   set)?
2. A reference "extra" book (e.g. book `99`) — does a new branch get one?
3. An environment-only wait in the reference (e.g. load prices in PRO only): mirrored as is; the BOX dev says ideally
   both environments — the BOX team's call per branch.
4. The `G0…-` global-event convention (which code is which server pair) — INFERRED from the repos; to confirm with the
   Control-M team, then the script can suggest the global name of a cross-server wait.
