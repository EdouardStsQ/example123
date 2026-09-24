# Devin kickoff — adversarial review of a completed run

**Run this in a FRESH session, never the one that produced the run.** The point is context the
generating session does not have: a reviewer that did not make the decisions is the only one who can
see them as decisions rather than as facts.

**This closes the half of the eval case a script cannot check.** `validate_run_output.py` is the
mechanical half and must already be clean before you start. What follows needs judgement.

---

**Step 0 — find the repo root.** This automation repo is the `automation/` subfolder of the
`cib-box-auki-nbranch` checkout. The charter may arrive as `agent.md` (lower case) — treat both as the
same file and search case-insensitively:

```bash
find / -ipath '*/automation/agents/sigom-box-fe-configs-agent/agent.md' -not -path '*/archive/*' 2>/dev/null | head -5
```

`cd` into the folder that **contains `agents/`** (it ends in `/automation`) and treat every path below
as relative to it. Never report a file missing before running this search; never recreate it.

## Setup

| | |
|---|---|
| **Repo** | this automation repo (**read-only** — you are reviewing, not fixing) |
| **Database** | none. Every fact you need is in the run folder |
| **Input** | `RUN_FOLDER` — e.g. `runs/NY_SCH/tier2-pre/` |

---

You are reviewing a completed run of `sigom-box-fe-configs-agent` against its own rules. **You did not
produce this run and you have no stake in it passing.**

Read, in this order: `agents/sigom-box-fe-configs-agent/AGENT.md` ·
`evals/cases/sigom-box-fe-configs-agent-walk.md` · then the run folder — `02-findings.md`,
**`03-sql/values.json` and `03-sql/render-report.md`**, `00-decisions.md`, `99-open-items.md`,
`01-evidence/`. Since 2026-09-24 the `.sql` files are **rendered** from `values.json` by
`scripts/render_sql.py` (ADR 0006): review the **values and their sources**; the SQL's structure is the
templates' job, and the validator proves the files were not edited.

**First, confirm the mechanical half is clean:** run
`python3 scripts/validate_run_output.py <RUN_FOLDER>` and paste the output. **If it reports any FAIL,
stop and report that** — the run is not ready for review.

## What to check, in descending order of what it costs to miss

### 1. Did a set shrink?

For every step that emits more than one row, **compare the evidence CSV's row count against the number
of INSERTs**. A curve with 1 of 38 quote references is not partly configured, it is wrong. Count the
CSV yourself; do not trust a stated count.

### 2. Does every value trace to something?

Take **every value in `values.json`** (and so every literal in the SQL) and name where it came from: a named evidence CSV, a named SME, a
documented constant, or a stated derivation rule. **A literal you cannot place is the finding.**

Two specific traps, both of which have occurred:
- **A GBO PK in a BOX column** — for each FK, name the table it points into and the schema that table
  is in. If the answer is `DEVENG`, it is wrong (hard rule 13).
- **An invented schema or package qualifier** — check every procedure call against the name the repo
  records, not against what looks plausible.

### 3. Is the reasoning behind each status sound — and is it the reasoning the evidence supports?

Read each findings row's rationale as an argument and ask whether the evidence carries it. Three
failure shapes seen so far:
- **An absence concluded without a control** that could have returned rows.
- **A cross-environment inference** — concluding something about this branch from another environment.
- **A finding used to justify its opposite.** A query showing GBO and BOX differ was used to justify
  preferring *another branch's* BOX values. Ask of every citation: *does this evidence support this
  conclusion, or merely sit near it?*

### 4. Whose decision was it?

Every gate closure needs a **named person**, **authority for that specific decision**, and **a question
that was actually put**. `[stated: user]` is not attribution. A role that does not match the decision
type is not authority. An interpretation of a vague answer — *"same as London"* — is not a decision;
the sign-off pack says so in its opening line.

### 5. Does the run overstate itself?

A step statused ready with no SQL, a gate marked closed with its dependent steps unemitted, an open
item that asks for something impossible — these are not tidiness issues. **A status that overstates
what the run did is worse than a blocked step honestly reported**, because it is the one thing a
reviewer cannot detect by reading the SQL.

## How to report

For each finding: **what is wrong · where (file and line) · which rule · what it would cause · how
confident you are.** Ranked, worst first.

⛔ **Do not fix anything.** You are producing a review, not a revision. If you find nothing in a
category, say so explicitly — a review that silently omits a category is indistinguishable from one
that did not look.

**End with a verdict**: *accept* · *accept with the listed corrections* · *reject and regenerate*. Say
which single finding drove it.

⚠️ **Being unable to fault a run is a legitimate outcome and you should say so plainly.** Do not invent
findings to look thorough — a false finding costs a real round trip. But the base rate so far is two
rejected runs out of two, so look hard before concluding it is clean.
