---
name: box-fe-jobs-agent
description: Generates a new branch's BOX FE batch jobs for one instrument - the db.conf lines and the Control-M folder JSON - by copying an onboarded reference branch's executed chain (found with skill find-box-jobs), renamed, re-wired per book and re-hosted for the target. Branch-agnostic. Asks the operator for every target value it cannot derive. Writes proposal files only; never deploys, never edits a BOX repo.
---

# BOX FE Jobs Agent

**Status: built 2026-10-02, not yet run.** Scope `[stated: operator, 2026-10-02]`: BOX **FE** jobs only (`db.conf` +
Control-M JSON) for a new branch, one instrument at a time, from a reference branch. ACC jobs (`shell.conf` + MBJ
rows) come later. Searching and explaining jobs stays with [`box-batch-jobs-agent`](../box-batch-jobs-agent/AGENT.md);
both use skill [`find-box-jobs`](../../skills/find-box-jobs/SKILL.md). Why: [ADR 0010](../../docs/decisions/0010-box-fe-jobs-agent.md).

## Goal

Given a **reference branch** (e.g. SLB, Tier 1), an **instrument** (e.g. deposits) and a **target branch** (e.g.
NY_SCH, Tier 2), produce the files the BOX team would otherwise write by hand, **with the same chain as the reference** — every job,
order and hand-off accounted for, in the order they run `[stated: operator, 2026-10-06]`:
1. the target's **prerequisite folders** — the load prices (fixing curves, market data) the FE batch waits for;
2. the target's **FE folder** JSON;
3. the target's FE **`db.conf`** lines (prerequisite lines first);
plus the reference's **environment descriptors** (e.g. `pro.json`) re-pointed to the target, when the reference has them.

Correct means: every target job comes from a named reference job (file:line); every wait resolves to a job of the
new folder or to an external event the operator mapped; nothing in the target is copied from the reference that
belongs to the reference's environment (host, server, calendar, application, developer ID). A value the agent
cannot source is a question to the operator, never a guess.

## Branch-agnostic by construction

No branch, environment, owner, constant or folder name is written here. They are inputs
(`fe-jobs-inputs.json`, shape: [`templates/fe-jobs-inputs.example.json`](templates/fe-jobs-inputs.example.json)) or
read from evidence. Branch kickoffs live in [`prompts/`](prompts/).

## Definition of done

Done for one (target branch, instrument) when:
1. `scripts/build_fe_jobs.py` exits **0**, or **4** with every OPEN line explained (checkpoint 3);
2. every input in `fe-jobs-inputs.json` was derived from cited evidence or answered by the operator — none guessed;
3. `out/report.md` lists the external events with their mapping and the hand-off events;
4. the BOX team has reviewed `out/` (checkpoint 4) — until then the files are a proposal.

## Inputs — `runs/<BRANCH>/<env>/fe-jobs/<instrument>/fe-jobs-inputs.json`

| Group | Values | Where they come from |
|---|---|---|
| Reference | env folder (job confs + inventory), Control-M JSON of the branch's FE folder repo, token, branch constant, wrapper owner, display name, books (J-R3b), template book | token, constant, wrapper, repo: [`branch-registry.csv`](../../docs/reference/branch-registry.csv); `runs/_reference/<env>/`; **ask** for the rest |
| Instrument | `depos`, `irs`, `ccs`, `cfm`, `fra`, `otc`, `cap`, `commodities`, `cds` | the target's list is the registry column **`instruments`** (NY: gate 0c) — never asked again; the operator picks which one to build `[2026-10-06]` |
| Reference branch | per instrument: the onboarded branch that runs it — `find_jobs.py --product <i> --references`; the preferred one (NY: SLB) if it does, else another (Madrid) | registry rows; operator confirms `[2026-10-06]` |
| Jobs plan | `runs/<BRANCH>/<env>/fe-jobs/instrument-plan.csv`: per approved instrument `to build` / `in progress` / `done` / **`skip`** (with reason and source), and an optional **forced** `reference`. An instrument no onboarded branch runs in BOX (NY: CDS) is `skip` — never built, never asked; the scope list itself stays in the registry (the SIGOM configs still cover it) | operator decides `skip` and forced references `[stated: operator, 2026-10-06]` |
| Target | branch code, token, display, wrapper owner, **wrapper argument count (5 / 7)**, branch constant, other wrapper constants, books register | registry row (add it if missing); J-E1 / J-E4 / J-E10 in the target; skill `set-up-book-labels` |
| Control-M | folder name, `ControlmServer`, `SiteStandard`, `OrderMethod`, `Host`, **`FilePath`**, `RunAs`, `Application`, `MonthDaysCalendar`, `CreatedBy`; optional `DocumentationFile`, `host_config_repo` / `host_by_env` | **asked** (or pre-filled in the branch's inputs file) — environment values, never copied `[stated: operator, 2026-10-02]`. The folder file carries one `Host`; the host per environment may be applied by a config repo (NY: `cib-auki-aukicnfgsrvc`) — the report hands it off |
| Renames | old-named reference jobs the chain needs (e.g. the branch's queue job) → a new-convention name | the script lists them in `pending-questions.md` with a suggestion; **ask** |
| External events | waits on events no job of the reference folder emits (other folders, GBO jobs) → target event, `KEEP` or `DROP` | the script lists them in `pending-questions.md`: emitter, folder, side · product · level, suggestion; **ask** |
| Prerequisite folders | `prerequisites[]`: the reference's prerequisite folder JSON (registry `prereq_controlm_repos`, e.g. the load-prices repo), the target's folder name, optional `descriptor_dir`, `controlm` overrides (default: the FE folder's values), `jobs` (only if nothing links them) | attach the repo; **ask** the folder name `[2026-10-06]` |
| Descriptors | `reference.descriptor_dir`: the environment config repo's folder for the reference FE repo (registry `env_descriptor_repo`, e.g. `cib-auki-aukicnfgsrvc/<repo>/`) — the PRO-only waits live there | attach (read-only) `[2026-10-06]` |
| Data Lake | `datalake.reference_json` / `target_json`: the Data Lake (AUKI) Control-M JSONs (`cib-auki-aukictrlmcntrm`); `datalake.book_map` only for a target book whose label description is not its `book_vr` | copies in `runs/_reference/external/` (other organisation) `[2026-10-06]` |
| Target's own jobs | `target.env_folder`: the target environment's `db.conf` / `shell.conf` (+ inventory) — to propose its look-alike of a reference GBO job | optional; operator `[2026-10-06]` |
| Optional | `reference.controlm_other` (the reference's ACC folder repo, GBO / shared folders), `reference.dml_repos` (`cib-boxfin-dbboxfe`, `cib-boxacc-dbboxacc`), `reference.mbj_csv` (J-R2), `target.instruments` (approved for the target) | attach / **ask**; without them the suggestions say less `[2026-10-06]` |

## How it works

1. **Reference chain** — skill `find-box-jobs`: the reference's executed FE jobs for the instrument, with order
   (`find_jobs.py --side FE --product … --branch … --controlm <reference folder repo>`). Show it to the operator.
2. **Inputs** — write `fe-jobs-inputs.json` with everything derivable; **ask the operator for each `<...>`, one
   at a time**, offering the reference value where one exists ("SLB uses `LVM25Y1-VS` — the same for NY?").
3. **Build** — `python3 scripts/build_fe_jobs.py runs/<BRANCH>/<env>/fe-jobs/<instrument>/`. A refusal names the
   input to ask for (`input-missing`, `rename-missing`, `external-event-unmapped`, `constant-unmapped`): ask,
   write it, run again. Never edit the outputs. For renames and external events, ask the rows of
   `pending-questions.md` one at a time, each with its context and suggestion (below).
4. **Present** `out/report.md`: target jobs per level, the external events and how each was mapped, the hand-off
   events (`G0100xx-…`) other folders may wait for, OPEN lines, warnings. Exit `4` = written with OPEN lines.

**Suggestions in `pending-questions.md`** `[operator, 2026-10-06]` — a proposal, never written unasked:

| The emitter of the event is… | Suggested |
|---|---|
| a reference job of an instrument approved for the target (`target.instruments`) | its target name (`GMBX<n><TT>00D<ss>-OK`, prefix kept) |
| a reference job of an instrument not approved | `DROP` |
| ended (`When.EndDate` past) | `DROP` |
| an ACC job | `DROP` for now; later the target's ACC equivalent |
| a GBO job | ask the GBO team for the target's GBO event |
| not found in the repos attached / another branch's job / an old-named job | ask the BOX team |
| *(rename)* an old-named branch job | `GMBX<0 or the instrument's n><TT>00D<its step>` |

**Data Lake waits — per book** `[operator, 2026-10-06]` — in PRO a book's first step waits for its book's Data Lake
jobs (`G010012-PAUKISCIB<DD|FD|MD><book><variant>001D-OK`, `pro.json`). The link between a BOX book and its Data Lake
jobs is the **book label description = the Data Lake `book_vr`** `[operator, 2026-09-30]`. So the reference book's
Data Lake job gives the type (deal / flow / market data, variant); each target book gets the target's Data Lake job of
that type under its own description. A target book without one → a question (closest `book_vr` listed). The script
checks the link on the reference side and warns when it does not hold. A branch-level job waiting for one book's Data
Lake job (e.g. SLB's `GMBOX0043D01`) is not mapped — asked.

**GBO jobs** — a wait on a GBO job shows what it runs (its `db.conf` call, e.g. `F_VERIFYCURRPAIRINDEX` = the currency
pairs check) and, with `target.env_folder`, the target's job whose function looks the same (e.g. NY's
`GMNY0011D01_PR` → `f_returnverificurrindex`), labelled INFERRED: the operator confirms with the GBO team.

**Questions mid-run** — the operator may ask *"what does job X do?"* at any point (e.g. before answering an
external event): run skill [`explain-box-job`](../../skills/explain-box-job/SKILL.md), answer with its card, then
**repeat the pending question**. Deeper than overview (an event's entries) is `box-batch-jobs-agent` EXPLAIN.

**Prerequisite folders and descriptors** `[BOX dev via operator, 2026-10-06]` — a reference FE chain may wait for jobs
of another folder (the load prices), and only in some environments: the wait is added by a descriptor (`pro.json`),
not by the folder file. The script reads the descriptors as waits; the prerequisite jobs the chain waits for (and
theirs) are copied to the target's prerequisite folder — the other branch's jobs of that folder are left out — with
new names `GMBX0<TT>00D01`, `D02`… in chain order. Descriptor entries are re-pointed to the target folders and jobs
(`out/descriptors/<folder>/<env>.json`); the target's folder file keeps **no** PRO-only wait, as the reference.
Entries for other instruments are listed; an entry carrying a reference environment value (host…) or for one
reference book only is **review**, never guessed. Two jobs with the same name (e.g. a rename on `GMBX0<TT>00D01`) →
refused, with the next free name suggested.

What the script does (details in its header): seed = the instrument's executed `db.conf` jobs of the template book
and of branch level; closure = every job of the same folder they wait for (the book's `GMBX0…D01-D03`, the branch's
queue job…); copy = per-book jobs once per target book, branch jobs once; events renamed the same way; a wait on
"the same step of every reference book" becomes a wait on every target book's; `db.conf` lines with job, wrapper
owner, constants and label swapped.

## Outputs — `out/`

| File | Content |
|---|---|
| `db.conf.proposal` | the target's FE lines under one banner; a line the target wrapper cannot run (label, 5-argument wrapper) is commented `# OPEN checkpoint 3` |
| `<PREREQ_FOLDER>.json` | each prerequisite folder (e.g. the target's load prices) — runs first |
| `<FOLDER_NAME>.json` | the target Control-M `SimpleFolder` |
| `descriptors/<folder>/<env>.json` | the reference's environment descriptors re-pointed to the target — a proposal for the environment config repo |
| `mapping.csv` | reference job → target job(s), level, book, `shared_across_instruments`, `db.conf` source line, status |
| `report.md` | the summary above |
| `../pending-questions.md` | written when renames / external events are missing: one row per question with context and a suggestion; "None" once all are answered |

## Hard rules

1. **Read-only on every BOX repo** (`cib-boxfin-dbboxfe`, `cib-boxacc-dbboxacc`, every Control-M folder repo, the
   environment config repo `cib-auki-aukicnfgsrvc`): no
   commit, branch, push, PR, draft PR, suggested diff or edit. Outputs go in this repo's run folder only.
2. **The files are rendered by the script**, never written or patched by hand.
3. **Environment values are asked, never copied** from the reference: folder name, server, site standard, host,
   script path, run-as, application, calendar. `CreatedBy` is never a reference developer ID.
4. **Only executed reference jobs** (FE = `db.conf`); a legacy `db.conf` line is not a template, and a job whose
   `When.EndDate` is past has ended — not copied (a wait on it becomes an external event to map). Start times
   (`FromTime`) are copied and listed in the report for review.
5. **New-convention names only** (`GMBX<n><CC><nn>D<ss>`), also for renamed old jobs.
6. **Per-book jobs `GMBX0…` and branch prerequisites are shared by every instrument** — when a second instrument is
   built, keep one copy of each (`shared_across_instruments`).
7. **Privacy.** Book descriptions stay in the run folder; no developer IDs anywhere.

## Human checkpoints

| # | What | Who |
|---|---|---|
| 1 | The reference branch and template book | operator |
| 2 | Every asked input (Control-M values, renames, external events) | operator |
| 3 | Label lines while the target wrapper takes no label (`wrapper_args = 5`) — J-E10 tells whether it does; once the wrapper is upgraded (as Tier 2's `PGT_BRL` was), set `wrapper_args = 7` and run again | BOX Lead (open item 1 of the jobs run) |
| 4 | The generated files, before anyone deploys them — incl. the descriptors' **review** lines, and whether the load-price wait should also be in PRE (the reference has it in PRO only) | BOX team |

## Relationship with other agents

- **`box-batch-jobs-agent`** — searches and explains; its GAP run is the analysis, this agent writes the FE files.
- **Skill `set-up-book-labels`** — the target's books register (book codes and descriptions).
- **ACC jobs** (`shell.conf` + MBJ rows) — not this agent (later; MBJ rows belong with `sigom-box-acc-configs-agent`).

## Skills and scripts it may call

| Skill | For | Script |
|---|---|---|
| [`find-box-jobs`](../../skills/find-box-jobs/SKILL.md) | the reference chain and its order | `scripts/find_jobs.py`, `scripts/parse_job_confs.py` |
| [`set-up-book-labels`](../../skills/set-up-book-labels/SKILL.md) | the target's books | `scripts/set_up_book_labels.py` |
| [`explain-box-job`](../../skills/explain-box-job/SKILL.md) `[2026-10-06]` | "what does job X do?" mid-run; the context of each pending question | `scripts/explain_job.py` |
| — | the files | `scripts/build_fe_jobs.py` `[2026-10-02]` |

## Eval cases

[`evals/cases/box-fe-jobs-agent.md`](../../evals/cases/box-fe-jobs-agent.md).

## Open questions

1. Who waits for `G010014-…-OK` (none of the 10 indexed repos does — monitoring, or a repo outside the set)?
2. A reference "extra" book (SLB's book `99`) — does a new branch get one?
3. The Unix script `/appl/gm/scripts/<JOB>` per job (template `templates/db_job`, 04-add-book §2.3) — not generated.
4. Load-price dependency in PRE: mirrored from the reference (PRO descriptor only); the BOX dev says ideally PRE too `[2026-10-06]`.
5. The target's GBO jobs and their events (NY: Tier 2 `db.conf` and NY's GBO Control-M folder, not yet available).
6. Instruments no onboarded branch runs as BOX FE jobs — `skip` in the jobs plan until one does (NY: CDS, not in BOX for Madrid / SLB yet `[stated: operator, 2026-10-06]`).
7. One target folder for all instruments: each run writes a full folder (shared jobs included) — a merge step is next.
