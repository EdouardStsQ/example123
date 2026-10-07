# Devin kickoff — `sigom-box-acc-configs-agent` — NY_SCH BOX ACC gap run (Tier 2 PRE, reference SLB Tier 1)

> **How to start — nothing to paste.** Open a Devin session with this repo attached and type:
> **`Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-gap-run.md`**
> Devin reads this file and asks you for anything it needs, one question at a time.

**What this run produces:** for NY_SCH, a **gap matrix** of the BOX - Accounting SIGOM screens — per screen and
instrument: present / to create (and from what) / to ask / N/A / OPEN — and your decisions, in
`runs/NY_SCH/tier2-pre/acc-configs/`. **Read-only: no SQL is written or run against any database by Devin.**

## Before you start

| | |
|---|---|
| **Repos** | this automation repo `cib-box-auki-nbranch` (**read/write**); optional read-only `cib-boxacc-dbboxacc` (ACC packages: `PKG_ACCTPROP`, `PKG_ACCTPRECOMMIT`) |
| ⛔ **Write protection** | No commit, branch, push, PR or edit on any repo except this automation repo; no DML anywhere |
| **Database** | Devin gets no connection. You run the queries it gives you — **Tier 1** for `REF`, **Tier 2** for `TGT` — and return each CSV with the name it says |
| **Already given** | NY_SCH branch `20007.4`; reference SLB `20087.4` (Tier 1); the six approved instruments (registry / gate 0c) — in `acc-configs-inputs.NY_SCH.json` |
| ✏️ **Devin asks** | per ACC event group: keep **global** or make a **NY copy**; the start date (`INIVALPCDATE`) for NY's new local / portfolio properties; that Net Contract is N/A for NY; whether the GBO → BOX topic mapping is available |
| **Not touched** | the FE configs agent, the jobs agents, their runs |

---

**If you were pointed at this file**, it is your task prompt: skip the table above, check the repo is attached, start.

You are running as the `sigom-box-acc-configs-agent`, **phase 1 (gap run)**.

**Step 0 — repo root.** The folder containing `agents/` of the `cib-box-auki-nbranch` checkout's `automation/` folder.

**Step 1 — read in full:** `agents/sigom-box-acc-configs-agent/AGENT.md`,
`docs/reference/queries/acc-config-mining.md`, `docs/decisions/0011-acc-configs-agent-scope.md`,
`docs/process/checklists/acc-add-product-checklist.md` §0.

**Step 2 — the run folder** `runs/NY_SCH/tier2-pre/acc-configs/`. No `acc-configs-inputs.json` → copy
`acc-configs-inputs.NY_SCH.json` to it. One there → keep its answers. Evidence goes in `01-evidence/`; a CSV already
there is not asked again (say so).

**Step 3 — the gate.** Ask, one at a time: **A-G1** in Tier 2 (NY) and in Tier 1 (SLB) → write `target.group_pk`,
`reference.group_pk`; A-G1 (b) in Tier 2 → if another branch of NY's group is already in BOX, **stop and tell the
operator** (checkpoint 1: screens 2 and 4 may already be configured for the group). Then **A-G2** and **A-G3** (Tier 2).

**Step 4 — the screens, in the charter's order**, one query at a time, each with its Env (Tier 1 / Tier 2), the
values substituted, and the CSV name: A-06, A-07, A-01 (both) → A-08a (Tier 1), A-08b, A-09 (both) → A-03a, A-03c
(Tier 2), A-03b (Tier 1) → A-04a, A-04b (Tier 1), A-04c, A-04d, A-04e (Tier 2) → A-02a, A-02b (Tier 1), A-02c, A-02d
(Tier 2) → A-10a, A-10b (Tier 2; `&&ACCOUNT_CODES` = the account codes of A-03a and A-04e), A-10c (Tier 1) → A-05
(Tier 2) → A-11 (Tier 1). A query that fails: show the error, fix only what the error names, ask again.

**Step 5 — the decisions**, one at a time, written to the inputs file with the date:
- per group of A-08a: `global` (default) or `branch-copy` — say what a copy means (a new group PK and name for NY,
  same events and order; NY's ACC jobs will use it);
- `INIVALPCDATE` for NY's new local and portfolio properties (propose the reference's latest, ask);
- Net Contract: N/A for NY (not Madrid real) — confirm;
- the GBO → BOX topic mapping: where it is, or "not yet" (then screen 4's accounts and screen 3's topics stay OPEN).

**Step 6 — the gap matrix.** Write `02-acc-gap-matrix.md` from
`agents/sigom-box-acc-configs-agent/templates/acc-gap-matrix.md.tmpl`: per screen and instrument the reference rows,
what NY has, the action, the source, the evidence file:line. Rules: a global object missing in Tier 2 → **ask** (BOX
team), never "create"; a GBO topic never appears as a BOX value; an account not in A-10a → **OPEN**, never the
reference's account; no reference rows for an instrument (e.g. CDS) → **N/A — no reference** (say so).

**Step 7 — finish:** show the matrix summary (counts per action and screen), the open questions, and that this is a
proposal for the BOX team (checkpoint 2). Commit the run folder to the automation repo only.
