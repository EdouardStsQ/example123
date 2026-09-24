# Devin kickoff — NY_SCH **dry-run** for BOX FE expert review

Paste the block below the line into a Devin session. For another branch, copy this file and change only
the input table.

**What this is for.** A BOX FE expert reviews what the agent *would* do, without anyone running a query.
Expect one sitting, not a week.

---

## Before you paste: setting up the session

| | |
|---|---|
| **Repos to attach** | this automation repo (**read/write** — the run folder is written here) · `cib-boxfin-dbboxfe` (**read-only**) · `cib-boxacc-dbboxacc` (**read-only**, optional for FE) |
| **Database** | **none needed.** Nothing is executed |
| ⛔ **Write protection** | Devin can propose changes on any attached repo. Set the two BOX repos read-only where the tooling allows; the prompt below forbids it regardless. **Check the session's opening report names which repos were attached and in which mode** |

---

**Step 0 — find the repo root.** This automation repo is the `automation/` subfolder of the
`cib-box-auki-nbranch` checkout. The charter may arrive as `agent.md` (lower case) — treat both as the
same file and search case-insensitively:

```bash
find / -ipath '*/automation/agents/sigom-box-fe-configs-agent/agent.md' -not -path '*/archive/*' 2>/dev/null | head -5
```

`cd` into the folder that **contains `agents/`** (it ends in `/automation`) and treat every path below
as relative to it. Never report a file missing before running this search; never recreate it.

You are running as this repo's `sigom-box-fe-configs-agent`
(`agents/sigom-box-fe-configs-agent/AGENT.md`). Read that charter in full first, then
`docs/process/03-fe-sigom-config-procedure.md` and `docs/reference/queries/fe-config-mining.md`.

## Run inputs

| Input | Value |
|---|---|
| `RUN_MODE` | **`dry-run`** — state the whole plan, execute nothing. See the charter's *Dry-run mode* |
| `BRANCH_CODE` | `NY_SCH` |
| `TARGET_ENV` | Tier 2 **PRE** |
| `GBO_SOURCE` | GBO **Tier 2** |
| `DB_ACCESS_MODE` | **n/a** — no database in this session |
| `SOURCE_ACCESS_MODE` | **`direct`, read-only** — see the prohibition below |
| `RUN_FOLDER` | `runs/NY_SCH/dry-run-01/` |
| `PRODUCT_BOOK_SCOPE` | **Instruments: partially supplied.** `[stated: <SME_NAME>, via Edouard, 2026-09-21]` — **six**: Swap, Deposit & Loan, Cross Currency Swap, OTC Option, Caps And Floors, CDS (Credit Derivatives). ⛔ **The four mandatory accrual values, `LIMIT_ERRORS` and book scope are NOT supplied** — gate 0c is still open. Do not invent them; say what you need. ✅ **All six resolve**; Credit Derivatives is `T_PGT_SUB_PRODUCT_S` `20313.4` `[confirmed: DB via Edouard, 2026-09-22]`. An earlier note here said CDS had no row and blocked steps 6/11/12 — **withdrawn**, it was inferred from an inner join that failed to match |

## ⛔ Read-only on the BOX repos — absolute

**No commit, no branch, no push, no pull request, no draft PR, no local edit** to
`cib-boxfin-dbboxfe` or `cib-boxacc-dbboxacc`. Not even to fix something you are certain is wrong. A
defect you find there is a **finding** — `05-source-questions.md`, with file:line — and an escalation.

You may write freely in **this** automation repo, inside `RUN_FOLDER` only.

**Your first output is a one-line confirmation** naming every repo attached and the mode you are
treating each as. If a BOX repo is attached writable, say so — then behave as read-only anyway.

## What to produce

Your audience is a **BOX FE developer who does not know this repo, and has not been briefed.** Organise
by **decision**, not by query — a query log is unreviewable by someone who hasn't read the catalogue —
and **orient him before you start** (next section). Every term this repo invented is a term he has
never seen.

Write `RUN_FOLDER/DRY-RUN-REVIEW.md`.

### It opens with an introduction — write this first, and keep it under one page

**He has not read this repo and did not ask for this agent.** If the document starts at walk step 1 he
has no idea what he is looking at or why his time is being spent. Open with five short sections, in
plain language, **no repo jargon** — no "gate", "walk", "Q-05c" or status vocabulary until after it:

1. **What this agent is for.** One paragraph. Configuring a new branch in BOX FE by hand means creating
   the same configuration objects a live branch already has, in the right order, without getting a
   single reference wrong — and a wrong one fails silently, later, in a batch. The agent does that
   derivation and shows its work.
2. **How it works, in three sentences.** A branch live in GBO already has its Financial Engine
   configuration there as real rows. The agent reads those and produces the SQL that creates the
   equivalent rows in BOX FE, in dependency order. Every value is read from a GBO row, given by a named
   expert, a documented constant, or explicitly derived with the rule written down.
3. **What it will never do** — and be concrete, because this is the reassurance he actually needs:
   it never writes to any database; it never invents a value or a primary key; it never writes DDL; it
   **never commits, branches or raises a pull request against his repos**; the output is a file a human
   reviews and runs.
4. **What this document is.** Not a result — a **plan**, written before anything runs, so he can catch
   a wrong assumption now rather than after it reaches an environment. Say plainly that nothing in it
   has been executed.
5. **What you need from him, and how long.** Name the two or three decisions up front, say it should
   take one sitting, and say that "that's wrong" is the most useful thing he can give you.

Then, for **each of the 15 walk steps**, in walk order:

| | |
|---|---|
| **What I will insert** | target table, expected row count, and *why that count* |
| **Where each value comes from** | classified per column: **mined** (name the GBO row), **allocated** (`F___SEQUENCE`), **structural** (from the target object), **`DERIVED`** (state the rule and its source) |
| **What I'm unsure about** | in his language, not the repo's |
| **What I need from him** | a specific question, or "nothing" |

Then three short sections:

1. **What cannot be verified at all** — say this loudly, not in a footnote. Book scope has no
   completeness check. Gate 0c's four accrual values are an SME decision, not a lookup.
2. **The open questions for him**, ranked — `PKG_MAD_*` for a new jurisdiction; `num_counterror`'s
   scope; whether `f_GetBookByLabel` returns one book or many.
3. **Gate state, honestly.** Gate 0c is unsigned and 0e is deferred. Do not present a gate as passing
   because the plan looks sound — saying so is the point of the exercise.

Also emit the SQL **skeleton** to `RUN_FOLDER/03-sql/`, headed
`-- DRY-RUN — NOT EXECUTABLE. Illustrative shape only.` It must still pass
`python3 scripts/validate_run_output.py runs/NY_SCH/dry-run-01/` — run it yourself and paste the output.

## Rules that still bind you, in full

Everything in the charter applies. The four that matter most here, because a dry-run has no CSV behind
it and nothing downstream will catch a mistake:

- **Every claim carries its evidence tag** — `[confirmed: DB]`, `[stated: who, date]`, `[inferred]`,
  `[open-question]`. An unsourced assertion is indistinguishable from a guess.
- **Never invent a value, a PK, or DDL.** "I would read this from Q-05" is a fine answer. Inventing a
  plausible instrument list is not.
- **Hard rules 9–12** shape the output: identity columns come from the target not from GBO
  (and differ across the walk's **three** screens); the step-2 pre-commit **writes to step 8's table and
  `COMMIT`s**, so step 8 carries its curve values at INSERT time and the trailing `ROLLBACK` is not an
  undo; **there are no FK constraints anywhere**, so a wrong FK inserts cleanly and fails silently later.
- **Read the source when you're unsure** rather than reasoning — that is what `SOURCE_ACCESS_MODE =
  direct` is for. Cite file:line.

## During the review session

The expert will ask **consequence** questions, not query questions. Have the answers ready:

| If he asks | The answer |
|---|---|
| "What if a step-12 row is missing?" | `LIMIT_ERRORS` defaults to `0` — the first failed deal aborts the whole load for that instrument |
| "What if a step-11 row is missing?" | that (branch, instrument, book) combination is never queued — silently, no error |
| "What if step 5 is missing?" | the queue builder joins `T_BOX_ENGCONF_X`; nothing is scheduled at all |
| "Why not just copy London?" | the set can be copied, the values cannot — hard rule 6. NY is USD/New York |
| "Would SIGOM have done this?" | two pre-commit procedures; one validates, one writes to another table and commits. Explain how each is handled |

**Answer in his terms and stop.** Don't recite the catalogue. If you don't know, say so and record it as
a source question or an open item — that is a good outcome for this session, not a failure.

## When he gives you an answer

Record it as `[stated: <name>, <date>]` against the specific walk step in `DRY-RUN-REVIEW.md`, and list
every answer in `RUN_FOLDER/99-open-items.md` with what it unblocks. **Do not silently absorb a
correction** — the corrected claim and the original both stay, per this repo's evidence discipline.
