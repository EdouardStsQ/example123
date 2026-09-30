# Devin kickoff — `box-batch-jobs-agent`, GAP mode — NY_SCH into BOX, Tier 2 PRE (run 1)

**What this run produces:** how the reference branch's BOX jobs work in Tier 1, and what must be set up
for NY_SCH's BOX jobs to run in Tier 2 — a gap report and a proposed job matrix for the BOX team to sign
off. **No configuration is written** (that is phase 2).

## Before you paste

| | |
|---|---|
| **Repos** | this automation repo (**read/write**); `cib-boxacc-dbboxacc`, `cib-boxfin-dbboxfe` and the Tier 1 Control-M folder repos `cib-boxfin-t1mdesfe`, `cib-boxacc-t1mdesac`, `cib-boxacc-t1mdacccheck`, `cib-boxfin-t1mdalmfields`, `cib-boxfin-mdfinancialcheck` (**read-only**) |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or local edit on any repo except this automation repo, ever |
| **Database** | Devin gets no connection (`DB_ACCESS_MODE = assisted`). You run each query in the environment it names and export the CSV |
| **Unix** | you run the `grep` extracts of `db.conf` (J-R1 in Tier 1, J-T5 in Tier 2) |
| **People to have reachable** | the BOX team (checkpoints 1, 2, 4), the BOX Lead (checkpoint 3) |
| **Already collected** | `runs/NY_SCH/tier2-pre/jobs/02-environment-profile.md` holds what was established on 2026-09-29 (from screenshots). Devin re-asks only what is marked 🆕 or `screenshot` |

---

You are running as the `box-batch-jobs-agent`, mode **GAP**.

**Step 0 — find the repo root.** Same search as every kickoff (the charter may arrive as `agent.md`):

```bash
find / -ipath '*/automation/agents/box-batch-jobs-agent/agent.md' -not -path '*/archive/*' 2>/dev/null | head -5
```

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

- **One query at a time**, by J-ID, naming the environment (Tier 1 or Tier 2) — wait for its CSV.
- Owners differ per environment: Tier 1 wrapper `PGT_ES`, Tier 2 wrapper `PGT_NY`, catalog `PGT_PRC` in
  both (J-E1/J-E2, already collected). Never put a Tier 1 value in a Tier 2 row.
- **Checkpoint 1** (reference branch) and **checkpoint 2** (which of the reference's groups and
  instruments NY needs) are decision cards to the BOX team; record answers in `00-decisions.md`.
- **Checkpoint 3 — one card to the BOX Lead**, with the evidence from `02-environment-profile.md`:
  *Tier 2's `PGT_NY.PKG_GMBATCHPROCESS.f_executegroup` takes 5 arguments; Tier 1's `PGT_ES` version takes
  7 (`P_LABEL`, `P_SUBLABEL`). BOX's "by Book" events filter on `#LABEL#`. How will NY BOX jobs in Tier 2
  pass the book: an upgraded `PGT_NY` wrapper, a BOX-owned wrapper, `T_BOX_MBJ_PROPERTIES_S`, or
  something else?* Run J-E6 before putting it.
- The job matrix derives every row from a named SLB job. Job names: the SLB job's name with its label
  token replaced by the NY book's label code without the `X` (`GMBX3ES02D07` ↔ `GMBX3NY02D07`)
  `[stated: operator, 2026-09-30]`. Never invent a constant, group or label.
- Book codes stay in the run folder only.

**Step 4 — finish** with a 10-line summary: what the reference runs (counts per instrument), what the
target has, the blockers with their owners, and the open checkpoints.
