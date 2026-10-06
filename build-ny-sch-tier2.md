# Devin kickoff — `box-fe-jobs-agent` — NY_SCH BOX FE jobs, from SLB (Tier 1) to Tier 2 PRE

> **How to start — nothing to paste.** Open a Devin session with the repos in the table below attached, and type:
> **`Run automation/agents/box-fe-jobs-agent/prompts/build-ny-sch-tier2.md`**
> Devin reads this file and asks you for anything it needs, one question at a time (with a default you can accept).

**What this run produces:** for **one instrument**, NY_SCH's BOX FE `db.conf` lines and Control-M folder JSON,
copied from SLB's chain — proposal files in `runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/out/`. Nothing deployed.

## Before you start

| | |
|---|---|
| **Repos** | this automation repo `cib-box-auki-nbranch` (**read/write**); `cib-boxfin-t1mdslbfe` (SLB's FE Control-M folder) and `cib-boxfin-dbboxfe` (group names) — **read-only** |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or edit on any repo except this automation repo, ever |
| **Database** | Devin gets no connection. You run two queries: **J-R3b** (Tier 1) and **J-E4** (Tier 2), and return the CSVs |
| **Already there** | `runs/_reference/tier1-prod/` (SLB's `db.conf` + `jobs-inventory.csv`); `runs/NY_SCH/tier2-pre/books/books-register.csv` (22 books) |
| **Already given** `[operator, 2026-10-06]` | NY's Control-M folder values in `fe-jobs-inputs.NY_SCH.json`: folder `JACD-T2USNYFE-BOXFE-100068124`, server, site standard, `Host` (PRE), `FilePath /gmny/scripts`, `RunAs gmny`, application, calendar `CALC-USA`, documentation file. PRO host applied by `cib-auki-aukicnfgsrvc` |
| ✏️ **Devin asks** | the instrument, `CreatedBy` (the job-owner ID), then the renames, external events and constants the script asks for — one at a time |

---

**If you were pointed at this file**, it is your task prompt: skip the table above, check the repos are attached
(say which are missing), and start.

You are running as the `box-fe-jobs-agent`.

**Step 0 — repo root.** The folder containing `agents/` of the `cib-box-auki-nbranch` checkout's `automation/`
folder; every path below is relative to it. Not found → ask the operator for the path.

**Step 1 — read in full:** `agents/box-fe-jobs-agent/AGENT.md`, `skills/find-box-jobs/SKILL.md`,
`docs/reference/job-chains/box-batch-chain.md` (L1, L2), the header of `scripts/build_fe_jobs.py`.

**Step 2 — ask the instrument** (default `depos`). Folder: `runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/`. If it has
no `fe-jobs-inputs.json`, copy `runs/NY_SCH/tier2-pre/fe-jobs/fe-jobs-inputs.NY_SCH.json` there (NY's known values
are filled in) and set `instrument`.

**Step 3 — the reference chain** (skill `find-box-jobs`), shown to the operator:

```bash
python3 scripts/find_jobs.py runs/_reference/tier1-prod/ --side FE --product <instrument> --branch SLB \
    --controlm <path of cib-boxfin-t1mdslbfe> --out runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/01-evidence/reference-chain
```

Set `reference.controlm_json` to that repo's `projects/cib-boxfin-t1mdslbfe.json`. Propose the template book (the
first SLB book with the full chain; not `99`, SLB's extra book) and ask the operator to confirm.

**Step 4 — the two queries**, one at a time (catalogue `docs/reference/queries/box-jobs-queries.md`):
**J-R3b in Tier 1** (SLB's labels, `&&REF_LABEL_PREFIX = XLB`) → `01-evidence/J-R3b-reference-books.csv`;
**J-E4 in Tier 2** (the `PGT_NY` wrapper's constants) → `01-evidence/J-E4-wrapper-TGT.csv`. From J-E4 fill
`target.constants` (each `CST_…` the SLB lines use → its `PGT_NY` name, or `SAME`) and confirm `wrapper_args`.

**Step 5 — run, ask, run again:**

```bash
python3 scripts/build_fe_jobs.py runs/NY_SCH/tier2-pre/fe-jobs/<instrument>/
```

Each `REFUSED` line names an input: ask the operator **that one question**, write the answer, run again. For
`rename-missing` propose `GMBX<n>NY00D<ss>` with the old job's description; for `external-event-unmapped` show who
waits for it and propose `KEEP` for a shared/GBO job event, otherwise ask. Never edit `out/`.

**Step 6 — finish:** show `out/report.md` and say: target jobs per level, OPEN lines (expected while `PGT_NY` takes
5 arguments — checkpoint 3), external events and hand-offs, and that the files are a proposal for the BOX team.
Commit the run folder to the automation repo only.
