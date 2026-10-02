# Devin kickoff — `box-batch-jobs-agent`, GAP mode — NY_SCH into BOX, Tier 2 PRE (run 1)

> **How to start — nothing to paste.** Open a Devin session with the repos in the table below attached, and type:
> **`Run automation/agents/box-batch-jobs-agent/prompts/gap-ny-sch-tier2.md`**
> Devin reads this file and asks you for anything it needs, one question at a time (with a default you can accept).

**What this run produces:** how the reference branch's BOX jobs work in Tier 1, and what must be set up
for NY_SCH's BOX jobs to run in Tier 2 — a gap report and a proposed job matrix for the BOX team to sign
off. **No configuration is written** (that is phase 2).

## Before you start

| | |
|---|---|
| **Repos** | this automation repo (**read/write**); `cib-boxacc-dbboxacc`, `cib-boxfin-dbboxfe` and the Tier 1 Control-M folder repos `cib-boxfin-t1mdesfe`, `cib-boxacc-t1mdesac`, `cib-boxacc-t1mdacccheck`, `cib-boxfin-t1mdalmfields`, `cib-boxfin-mdfinancialcheck`, `cib-boxfin-mdschedulmonitor` (**read-only**) |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or local edit on any repo except this automation repo, ever |
| **Database** | Devin gets no connection (`DB_ACCESS_MODE = assisted`). You run each query in the environment it names and export the CSV |
| **Unix** ⛔ | **Required before starting:** Tier 1 PROD `db.conf` and `shell.conf` copied unchanged into `runs/_reference/tier1-prod/` (see its README; `mbjbox.sh` already there). Tier 2's into `runs/_reference/tier2-pre/` when available |
| **People to have reachable** | the BOX team (checkpoints 1, 2, 4), the BOX Lead (checkpoint 3) |
| **Already collected** | `runs/NY_SCH/tier2-pre/jobs/02-environment-profile.md` (2026-09-29 → 10-01) and `jobs/01-evidence/` (J-R2 Madrid shape, J-T8 ✅). Devin re-asks only what is marked 🆕 or `screenshot` |

---

**If you were pointed at this file** (`Run automation/…/gap-ny-sch-tier2.md`), it is your task prompt: nothing to
fill in — check the repos in the table are attached (say which are missing) and start.

You are running as the `box-batch-jobs-agent`, mode **GAP**.

**Step 0 — find the repo root.** Run both searches (case-insensitive; the first hit wins):

```bash
for d in ~/repos/cib-box-auki-nbranch/automation "$PWD" "$PWD/automation" \
         "$(git rev-parse --show-toplevel 2>/dev/null)/automation"; do
  if [ -f "$d/agents/box-batch-jobs-agent/AGENT.md" ] || [ -f "$d/agents/box-batch-jobs-agent/agent.md" ]; then echo "REPO_ROOT=$d"; break; fi
done
find / -path /proc -prune -o -type f -ipath '*/agents/box-batch-jobs-agent/agent.md' -not -path '*/archive/*' -print 2>/dev/null | head -5
```

**Nothing found → ask the operator for the path of the `cib-box-auki-nbranch` checkout** (do not stop, never
recreate the charter).

`cd` into the folder containing `agents/`. Every path below is relative to it.

**Step 1 — read, in full:** the charter `agents/box-batch-jobs-agent/AGENT.md`, the mechanism
`docs/reference/job-chains/box-batch-chain.md`, the queries `docs/reference/queries/box-jobs-queries.md`,
the worked example `docs/examples/gmbx3es02d07-trace.md`, the team's book runbook
`docs/process/04-add-book-procedure.md` Part 2, and the run folder `runs/NY_SCH/tier2-pre/jobs/`.

**Step 2 — inputs** (write `runs/NY_SCH/tier2-pre/jobs/00-inputs.md` first):

| Input | Value |
|---|---|
| `TARGET_BRANCH` | NY_SCH, `20007.4` |
| `TARGET_ENV` | Tier 2 PRE |
| `REFERENCE_BRANCH` | **proposal:** SLB London, `20087.4`, Tier 1 — the last branch onboarded into BOX and the FE agent's reference branch. Confirm at checkpoint 1 |
| `SCOPE` | instruments: `APPROVED_INSTRUMENTS` from the FE run (`runs/NY_SCH/tier2-pre/00-inputs.md`, or the FE kickoff). **Books: the register of skill `set-up-book-labels`, `runs/NY_SCH/tier2-pre/books/books-register.csv`** (22 books, labels `XNY01`…`XNY22`; a book whose label is still `to_create` stays `OPEN` in the matrix). **Every book × every approved instrument** `[stated: operator, 2026-09-30]` |
| `DB_ACCESS_MODE` | assisted |
| `SOURCE_ACCESS_MODE` | direct (read-only) |
| `RUN_FOLDER` | `runs/NY_SCH/tier2-pre/jobs/` |

**Step 3 — run the charter's GAP steps 0–9 in order.** Rules for this run:

- **Start the inventory from the job confs:** `python3 scripts/parse_job_confs.py runs/_reference/tier1-prod/`.
  BOX jobs are not all named `GMBX…` (old `GMBOX…` names exist) — use the `family` / `box_reason` columns.
  Inventory **product chains and generic jobs** separately, each with its level; propose only new-convention
  names for NY.
- **One query at a time**, by J-ID, naming the environment (Tier 1 or Tier 2) — wait for its CSV.
- Owners differ per environment: Tier 1 wrapper `PGT_ES`, Tier 2 wrapper `PGT_NY`, catalog `PGT_PRC` in
  both (J-E1/J-E2, already collected). Never put a Tier 1 value in a Tier 2 row.
- **Checkpoint 1** (reference branch) and **checkpoint 2** (which of the reference's groups and
  instruments NY needs) are decision cards to the BOX team; record answers in `00-decisions.md`.
- **Two kinds of BOX job, two set-ups** `[stated: BOX dev, 2026-10-01]`:
  - **ACC jobs: `shell.conf` → `mbjbox.sh`** (`MBJBOXACC.jar` reads the job's `T_BOX_MBJ_PROPERTIES_S` row, then calls
    `PKG_BATCHPROCESS_MBJ` — no wrapper). A `db.conf` line for the same job is **legacy, not executed**
    (`executed = N-legacy`) — never copy it for NY. Each NY ACC job needs its `shell.conf` line **and** its MBJ row (shape:
    J-R2 + `jobs/01-evidence/J-R2-mbj-properties-madrid-REF.md`; `INSTANZE = 'AUKI'`, `FK_PARENT` NULL,
    `FK_OWNER_OBJ = 35000182.65`, which J-T8 found in Tier 2). Run J-E9 (`PKG_BATCHPROCESS_MBJ` in both tiers).
  - **FE jobs: `db.conf`** (`f_ExecuteGroup` through the branch wrapper, no MBJ). Only these meet the wrapper problem.
    Classify each reference job FE / ACC by its group's name (J-C1), not by the file alone; an ACC group still run
    from `db.conf` is reported in `05-source-questions.md`.
- **Checkpoint 3 — one card to the BOX Lead**, for the **FE "by Book" `db.conf` jobs** NY needs,
  with the evidence from `02-environment-profile.md`: *Tier 2's `PGT_NY.PKG_GMBATCHPROCESS.f_executegroup`
  takes 5 arguments; Tier 1's `PGT_ES` version takes 7 (`P_LABEL`, `P_SUBLABEL`). These `db.conf` jobs
  (list) run "by Book" groups whose events filter on `#LABEL#`. Upgrade `PGT_NY`, a BOX-owned wrapper, or
  something else? (MBJ is ACC-only.)* Also ask the BOX team: is `GBOCL_MBJBATCH` installed on Tier 2's Unix server, pointing
  at Tier 2 (open item 4b)?
- The job matrix derives every row from a named SLB job. Job names: the SLB job's name with its label
  token replaced by the NY book's label code without the `X` (`GMBX3ES02D07` ↔ `GMBX3NY02D07`)
  `[stated: operator, 2026-09-30]`. Never invent a constant, group or label.
- Book codes stay in the run folder only.

**Step 4 — finish** with a 10-line summary: what the reference runs (counts per instrument), what the
target has, the blockers with their owners, and the open checkpoints.
