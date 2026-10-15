# Devin kickoff — `sigom-box-acc-configs-agent` — NY_SCH BOX ACC gap run (Tier 2, reference SLB Tier 1)

> **How to start — nothing to paste.** Open a Devin session with this repo attached and type:
> **`Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-gap-run.md`**
> Devin reads this file and asks you for anything it needs, one question at a time.

**What this run produces:** for NY_SCH, the **pre-check results**, **what NY configures and uses in GBO production**,
and a **gap matrix** of the BOX - Accounting SIGOM screens — per screen and instrument: present / to create (and
from what) / to ask / N/A / OPEN — and your decisions, in a new versioned run folder under
`runs/NY_SCH/<tier>-<env>/acc-configs/`. **Read-only: no SQL is written or run against any database by Devin.**

## Before you start

| | |
|---|---|
| **Repos** | this automation repo `cib-box-auki-nbranch` (**read/write**); optional read-only `cib-boxacc-dbboxacc` (ACC packages: `PKG_ACCTPROP`, `PKG_ACCTPRECOMMIT`, `PKG_SIGOM_COV`) |
| ⛔ **Write protection** | No commit, branch, push, PR or edit on any repo except this automation repo; no DML anywhere |
| **Database** | Devin gets no connection. You run the queries it gives you — **Tier 1** for `REF`, the **target environment** for `TGT`, **GBO production** for `GBO-PROD` — and return each CSV with the name it says |
| **Already given** | NY_SCH branch `20007.4`; reference SLB `20087.4` (Tier 1); the six approved instruments (registry / gate 0c) — in `acc-configs-inputs.NY_SCH.json`; the expected structure in `docs/reference/box-acc-model.md` |
| ✏️ **Devin asks** | the target environment (Tier 2 PRE or DGBOUS); the usage window (default the last full quarter); per ACC event group: keep **global** or make a **NY copy**; the start date (`INIVALPCDATE`) for NY's new local / portfolio properties; that Net Contract is N/A for NY; whether the GBO → BOX topic mapping is available; per configured-but-unused GBO row: copy or not |
| **Not touched** | the FE configs agent, the jobs agents, their runs |

---

**If you were pointed at this file**, it is your task prompt: skip the table above, check the repo is attached, start.

You are running as the `sigom-box-acc-configs-agent`, **phase 1 (gap run)**.

**Step 0 — repo root.** The folder containing `agents/` of the `cib-box-auki-nbranch` checkout's `automation/` folder.

**Step 1 — read in full:** `agents/sigom-box-acc-configs-agent/AGENT.md`, `docs/reference/box-acc-model.md`,
`docs/reference/queries/acc-config-mining.md`, `docs/decisions/0011-acc-configs-agent-scope.md`,
`docs/decisions/0013-acc-prechecks-and-sigom-routines.md`, `docs/process/checklists/acc-add-product-checklist.md` §0.

**Step 2 — the run folder.** Ask the target environment (`tier2-pre` or `tier2-dev` = DGBOUS). Then
`python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env <pre|dev> --area acc-configs --name gap` — never
write over an earlier run; with an earlier run, `--from <its folder>` offers its answers one by one. Copy
`runs/NY_SCH/tier2-pre/acc-configs/acc-configs-inputs.NY_SCH.json` to the run as `acc-configs-inputs.json` (if the
script did not) and keep its answers. Evidence goes in the run's `01-evidence/`; a CSV already there is not asked
again (say so).

**Step 3 — the gate.** Ask, one at a time: **A-G1** in the target (NY) and in Tier 1 (SLB) → write
`target.group_pk`, `reference.group_pk`; A-G1 (b) in the target → if another branch of NY's group is already in BOX,
**stop and tell the operator** (checkpoint 1: screens 2 and 4 may already be configured for the group). Then **A-G2**
and **A-G3** (target).

**Step 4 — the pre-checks**, in the target and in Tier 1: **A-P1** (readable, live counts), **A-P2** (identity values
= the owner table of the catalogue), **A-P4** (negative owners), **A-P5** (target only: PK generation safe), **A-P6**
(package versions). **A-P3** in the target. A failure → stop, say what failed and what it means (a missing grant: ask
for `BOX_ACC_RD` by name; an unknown owner / extension pair; `PKG_ACCTPROP` older than r0.0.8 — global / internal
topics come from the instrument-level configuration, the screen-2 / screen-4 reading changes and is asked).

**Step 5 — usage in GBO production** (`GBO-PROD`, read-only, aggregates only): ask the window, then **A-U0**, **A-U1**
(a)–(d), **A-U2** (one month first, then the window), **A-U3**, **A-U4**, **A-U5**. Summarise: instruments that post
vs the approved ones; portfolio properties and lists in use; the distinct GBO topics used (the input for the topic
mapping); the account codes used (→ `&&ACCOUNT_CODES`); configured but unused; used but not configured; whether NY
has GBO Cross Account Config rows.

**Step 6 — the screens, in the charter's order**, one query at a time, each with its Env, the values substituted,
and the CSV name: A-06, A-07, A-01 (both) → A-08a (Tier 1), A-08b, A-09 (both) → A-03a, A-03c (target), A-03b
(Tier 1) → A-04a, A-04b (Tier 1), A-04c, A-04d, A-04e (target) → A-02a, A-02b (Tier 1), A-02c, A-02d (target) →
A-10a, A-10b, A-10d (target; `&&ACCOUNT_CODES` = the codes **in use**, from Step 5), A-10c (Tier 1) → A-05 (target) →
A-11 (Tier 1). A query that fails: show the error, fix only what the error names, ask again. **Every list read is by
owner + extension; negative owners are excluded; counts are `COUNT(*)`.**

**Step 7 — the decisions**, one at a time, written to the inputs file with the date:
- per group of A-08a: `global` (default) or `branch-copy` — say what a copy means (a new group PK and name for NY,
  same events and order; NY's ACC jobs will use it);
- `INIVALPCDATE` for NY's new local and portfolio properties (propose the reference's latest; a portfolio property's
  date must be ≥ its local property's), ask;
- Net Contract: N/A for NY (not Madrid real) — confirm;
- the GBO → BOX topic mapping: where it is, or "not yet" (then screen 4's accounts and screen 3's topics stay OPEN);
- per configured-but-unused GBO portfolio property / list row: take forward or not.

**Step 8 — the gap matrix.** Write `02-acc-gap-matrix.md` from
`agents/sigom-box-acc-configs-agent/templates/acc-gap-matrix.md.tmpl`: the pre-check results, the usage summary, then
per screen and instrument (and per list for screen 4) the reference rows, what NY has and uses, the action, the
source, the evidence file:line. Rules: a global object missing in the target → **ask** (BOX team), never "create"; a
GBO topic never appears as a BOX value; an account not in A-10a → **OPEN**, never the reference's account; a GBO value
longer than BOX's column → a finding; no reference rows for an instrument (e.g. CDS) → **N/A — no reference** (say so);
an instrument NY does not use → **N/A — not used** (say so); a condition on a portfolio or counterparty → the NY
value is asked.

**Step 9 — finish:** show the matrix summary (counts per action and screen), the open questions, and that this is a
proposal for the BOX team (checkpoint 2). Commit the run folder to the automation repo only.
