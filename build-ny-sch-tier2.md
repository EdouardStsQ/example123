# Devin kickoff — `box-fe-jobs-agent` — NY_SCH BOX FE jobs, from SLB (Tier 1) to Tier 2 PRE

> **How to start — nothing to paste.** Open a Devin session with the repos in the table below attached, and type:
> **`Run automation/agents/box-fe-jobs-agent/prompts/build-ny-sch-tier2.md`**
> Devin reads this file and asks you for anything it needs, one question at a time (with a default you can accept).

**What this run produces:** for **one instrument**, in run order: NY_SCH's **load-prices** folder JSON
(`JACD-T2NYLOADPRICES-BOX_FE-100068124`), its BOX **FE** folder JSON, the FE **`db.conf`** lines (load prices first), and
SLB's `pro.json` re-pointed to NY — copied from SLB's chain — proposal files in `runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/out/`. Nothing deployed.

## Before you start

| | |
|---|---|
| **Repos** | this automation repo `cib-box-auki-nbranch` (**read/write**); **read-only**: `cib-boxfin-t1mdslbfe` (SLB's FE Control-M folder), `cib-boxacc-t1mdslbac` (SLB's ACC Control-M folder — who emits an ACC event), `cib-boxfin-dbboxfe` and `cib-boxacc-dbboxacc` (group and event names), **`cib-boxfin-t1mdloadprices`** (SLB's load prices — they run first) and **`santander-group-scib-gln/cib-auki-aukicnfgsrvc`** (SLB's `pro.json`: the PRO-only waits) |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or edit on any repo except this automation repo, ever |
| **Database** | Devin gets no connection. You run two queries: **J-R3b** (Tier 1) and **J-E4** (Tier 2), and return the CSVs |
| **Already there** | `runs/_reference/tier1-prod/` (SLB's `db.conf` + `jobs-inventory.csv`); `runs/NY_SCH/tier2-pre/books/books-register.csv` (22 books) |
| **Already given** `[operator, 2026-10-06]` | NY's Control-M folder values in `fe-jobs-inputs.NY_SCH.json`: folder `JACD-T2USNYFE-BOXFE-100068124`, server, site standard, `Host` (PRE), `FilePath /gmny/scripts`, `RunAs gmny`, application, calendar `CALC-USA`, documentation file. PRO host applied by `cib-auki-aukicnfgsrvc` |
| ✏️ **Devin asks** | the instrument, the instruments approved for NY, `CreatedBy` (the job-owner ID), then the renames, external events and constants the script asks for — one at a time, each with a suggestion |
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

**Step 2 — ask the instrument** (default `depos`). Folder: `runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/`. If it has
no `fe-jobs-inputs.json`, copy `runs/NY_SCH/tier2-pre/fe-jobs/fe-jobs-inputs.NY_SCH.json` there (NY's known values
are filled in) and set `instrument`. **If it already has one (an earlier run), keep it — every answer in it stays —
and add each key of `fe-jobs-inputs.NY_SCH.json` it lacks** (e.g. `prerequisites`, `reference.descriptor_dir`,
`reference.controlm_other`, `reference.dml_repos`, `target.instruments`); say which keys you added. Then ask **which instruments are approved for NY** (default: this one only) →
`target.instruments`.

**Step 3 — the reference chain** (skill `find-box-jobs`), shown to the operator:

```bash
python3 scripts/find_jobs.py runs/_reference/tier1-prod/ --side FE --product <instrument> --branch SLB \
    --controlm <path of cib-boxfin-t1mdslbfe> --out runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/01-evidence/reference-chain
```

Set `reference.controlm_json` to that repo's `projects/cib-boxfin-t1mdslbfe.json`, `reference.controlm_other` to
the `cib-boxacc-t1mdslbac` checkout and `reference.dml_repos` to the `cib-boxfin-dbboxfe` and `cib-boxacc-dbboxacc`
checkouts (a repo not attached: say so, leave it out), `reference.descriptor_dir` to the
`cib-auki-aukicnfgsrvc/cib-boxfin-t1mdslbfe` folder and `prerequisites[0].controlm_json` to
`cib-boxfin-t1mdloadprices/projects/cib-boxfin-t1mdloadprices.json` (both required for NY: the FE batch waits for the
load prices only through `pro.json`). If `cib-auki-aukicnfgsrvc` has a `cib-boxfin-t1mdloadprices` folder, set
`prerequisites[0].descriptor_dir` to it. Propose the template book (the
first SLB book with the full chain; not `99`, SLB's extra book) and ask the operator to confirm.

**Step 4 — the two queries** — skip a query whose CSV is already in `01-evidence/` (an earlier run), say so — one at a time (catalogue `docs/reference/queries/box-jobs-queries.md`):
**J-R3b in Tier 1** (SLB's labels, `&&REF_LABEL_PREFIX = XLB`) → `01-evidence/J-R3b-reference-books.csv`;
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
Expected for NY: the load prices take `GMBX0NY00D01` / `D02`, so an earlier answer renaming the queue job
`GMBOX0114D01` to `GMBX0NY00D01` comes back as a **name conflict** (suggested: the next free name) — ask it again.

**Any time — "what does job X do?"** Run skill `explain-box-job`
(`python3 scripts/explain_job.py runs/_reference/tier1-prod/ <JOB> --controlm <the FE, ACC and load-prices folder repos>
--dml <the two DB repos>`; a PRO-only wait is in `pro.json`, not in its card), answer with its card, then **repeat the pending question**. Deeper (an event's entries) → say it is
`box-batch-jobs-agent` EXPLAIN depth `event`.

**Step 6 — finish:** show `out/report.md` and say: the load-prices jobs, target jobs per level, the descriptor
entries written and each **review** line, OPEN lines (expected while `PGT_NY` takes
5 arguments — checkpoint 3), external events and hand-offs, and that the files are a proposal for the BOX team.
Commit the run folder to the automation repo only.
