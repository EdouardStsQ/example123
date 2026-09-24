# Devin kickoff — NY_SCH, Tier 2 PRE, full run (run 6)

**Rewritten 2026-09-23 after the BOX FE expert's review of run 3** — seven points, all in
[ADR 0005](../../../docs/decisions/0005-box-fe-expert-review-run-3.md). Run 3's mechanics were clean;
what the expert found was **domain rules the repo did not have**: which header columns are BOX's own,
how GBO keys the branch on accrual exceptions, the dummy book, Days Matured. This prompt also drops four
instructions that contradicted the charter (steps 4b/9/10 "parked", "do not call
`p_check_Val_Curves_precommit`", "gate 0c must stay open", the `20314.4` hypothesis).

**Revised 2026-09-24 after run 4** ([review](../../../runs/NY_SCH/tier2-pre/03-sql/REVIEW-run-04.md)):
the repo root is found before anything else; Q-04c no longer blocks (the quote reference is `FK_BS`);
decisions are asked **one at a time, as decision cards**; the dummy book is discovered in Tier 2 and
put to a person, never waived.

**Revised 2026-09-24 after run 5** ([review](../../../runs/NY_SCH/tier2-pre/03-sql/REVIEW-run-05.md)):
the charter search ignores case (it arrives as `agent.md` on some checkouts); queries are asked **one
at a time**; `REFERENCE_BRANCH_PK` is an input (SLB `20087.4`) so Q-13 (b) cannot pick up another PK;
and the config script must **compile** — no procedure calls inside `VALUES`, no guard that cannot fire.

**Revised 2026-09-24 again — the SQL is now rendered, not written**
([ADR 0006](../../../docs/decisions/0006-render-sql-from-values.md)). Five runs hand-wrote the SQL and
each broke its structure somewhere new. From run 6 you write **`03-sql/values.json`** — every value with
its source — and run **`python3 scripts/render_sql.py runs/NY_SCH/tier2-pre/`**, which writes the four
SQL files from the templates and runs the validator. **You never write or edit a `.sql` file.** The
operator runs the **rehearsal** file first: it executes everything and rolls back.

**What "full" means.** The agent runs the whole walk. How much SQL comes out depends on
**`SME_IN_SESSION`**: with an authorised person present, gate 0c closes in the session and every step
is emitted; without one, the decided steps (6, 11, 12, 14a) stay `SME_DECISION_REQUIRED` and the
rendered files are a **DRAFT** (the config file refuses to run; the rehearsal still proves the rest).
Both pass if the gaps are reported honestly.

---

## Before you paste: setting up the session

| | |
|---|---|
| **Repos** | this automation repo (**read/write**). `cib-boxfin-dbboxfe` is not needed — attach it only if the agent raises a source question and asks for it |
| ⚠️ **Database** | **Devin gets no connection.** You run every query on your read-only accounts — `DB_ACCESS_MODE = assisted` |
| **Which database** | **Tier 2 PRE** (`DEVENG` + `BOX_FE` + `GOM_GLB_SYS`) for everything, except the **Tier 1** reference reads in order 4 |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or local edit on `cib-boxfin-dbboxfe` or `cib-boxacc-dbboxacc`, ever |
| **Expected** | ~35 queries, **asked one at a time** — you run each and return its CSV before the next is asked |
| ⛔ **Before you start** | **Archive run 5** to `runs/NY_SCH/tier2-pre/archive/run-05/` (see `runs/README.md`). The next run overwrites the run folder |
| 📁 **Repo layout** | `cib-box-auki-nbranch/automation/` — the automation repo is the **`automation/` subfolder**. Every path in this prompt is relative to it |
| 🔠 **`AGENT.md` casing** | If GitHub shows `agent.md`, fix it once — see `runs/README.md` *Charter file casing*. The prompt copes either way |
| ✏️ **Fill in** | `SME_IN_SESSION` below |
| ▶️ **Applying** | The operator runs, in order: `…-rehearsal.sql` (last line must be `REHEARSAL OK`) → `…-config.sql` (`DONE - committed`) → `…-verify.sql` on the read-only account (every query's `Expect`). `…-rollback.sql` only to undo |

---

You are running as the `sigom-box-fe-configs-agent`.

**Step 0 — find the repo root before anything else.** The checkout is `cib-box-auki-nbranch`, and this
automation repo is its **`automation/` subfolder**: the charter should be at
`cib-box-auki-nbranch/automation/agents/sigom-box-fe-configs-agent/AGENT.md`. **The file name may arrive
in lower case (`agent.md`)** — treat the two as the same file. Search case-insensitively, from the top
of your workspace:

```bash
find / -ipath '*/automation/agents/sigom-box-fe-configs-agent/agent.md' -not -path '*/archive/*' 2>/dev/null | head -5
```

The folder containing `agents/` is **`REPO_ROOT`** (it ends in `/automation`) — `cd` into it. **Every
path in this prompt, the charter and the scripts is relative to `REPO_ROOT`**, and wherever they say
`AGENT.md` read whichever casing exists. If `find` returns nothing, say so and stop; if more than one,
list them and ask which. **Never report the charter missing without running this search**, never
recreate it, and never ask the operator which case it is in.

Then **read the charter** (`agents/sigom-box-fe-configs-agent/AGENT.md`, or `agent.md`) **in full**, then
`docs/reference/fe-walk-notes.md` (its first block is the 2026-09-23 expert review),
`docs/reference/queries/fe-config-mining.md`, and `agents/sigom-box-fe-configs-agent/templates/`.
Every hard rule binds you without exception.

## Run inputs — write these into `00-inputs.md` first, one `NAME: value` per line

| Input | Value |
|---|---|
| `RUN_MODE` | `normal` |
| `BRANCH_CODE` | `NY_SCH` |
| `BRANCH_PK` | `20007.4` — **re-confirm with Q-G1**; a mismatch is a stop |
| `REFERENCE_BRANCH_PK` | **`20087.4`** — SLB, `CODE = LND BRANCH` ([`confirmed-joins.md`](../../../docs/reference/confirmed-joins.md) *Branch identity*). **The only branch PK any reference query uses.** Never a label, a config or a curve PK — run 5 sent `26391.4` (Tier 1's dummy book label) as `FK_BRANCH` |
| `TARGET_ENV` / `GBO_SOURCE` | **Tier 2 PRE**, both — same environment |
| `DB_ACCESS_MODE` | ⚠️ **`assisted`. You have NO database connection.** You state the query; the operator returns the CSV. **Never attempt to connect** |
| `SOURCE_ACCESS_MODE` | `direct`, **read-only** |
| `RUN_FOLDER` | `runs/NY_SCH/tier2-pre/` |
| `APPROVED_INSTRUMENTS` | `20092.4, 2.4, 20.4, 20111.4, 20213.4, 20313.4` — Swap, Deposit & Loan, Cross Currency Swap, OTC Option, Caps And Floors, Credit Derivatives `[stated: <SME_NAME>, via Edouard, 2026-09-21]` |
| `SOURCE_FRONT` | `513.4` — Murex 3 Latam `[stated: BOX FE expert via Edouard, 2026-09-23]`. Q-02c proves it exists |
| `DUMMY_BOOK_LABEL` | ⛔ **Not known for Tier 2.** Tier 1's `26391.4` does not exist there (run 4). Found by **Q-10d**, then put to a person as a decision card. **Never a real book's label** |
| `BOOKS` | The branch's real book labels — **a decision card** (run 4 used `NY001` = `23958.44`, test-signed) |
| `TARGET_AUTH_CODE` | **from Q-G3c** — never typed. Record the fraction too: `TARGET_PK_FRACTION` |
| `QUOTE_REF_COLUMN` | `FK_BS` — `[stated: operator, BOX Dev, 2026-09-24]`: `T_PGT_ENGLKFC_X.FK_BS = T_PGT_QUOTE_REFERENCE_S.PK`, as Q-04 already recorded. **Not a question any more** |
| `SME_IN_SESSION` | **✏️ Fill in before pasting:** name and role of whoever may decide accrual values, error limits, books and Days Matured — or `none` |

### ⛔ How you get data: one query at a time, and a human runs it

`[stated: operator, 2026-09-24]` **Ask for exactly one query per message.** The "orders" below are the
*order*, not the packaging. For each query:

1. State the **query ID**, purpose, **which database** (Tier 2, or Tier 1), and every parameter value
   it uses **with where that value came from** (`BRANCH_PK 20007.4 — Q-G1`). A value you cannot source
   is a question, not a placeholder to fill.
2. Give the **SQL ready to run** — one statement, or the few statements of one query ID.
3. State the **exact filename** — `01-evidence/Q-05-accrual-gbo.csv` — and the row count you expect.
4. **Stop and wait.** Never proceed on an assumed result, and never ask the next query in the same message.
5. Check the CSV's shape before using it. A wrong shape is a re-run request.

You **can** run `python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/` yourself. Do.

---

## Order 1 — the preflight

```sql
SELECT USER,
       SYS_CONTEXT('USERENV','DB_NAME')                        AS db,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER='BOX_FE')  AS boxfe_visible,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER='DEVENG')  AS deveng_visible
FROM   DUAL;
```

`BOXFE_VISIBLE = 0` means **blind, not empty** — stop and report. → `01-evidence/Q-G4-preflight.csv`.
**Never copy the account name from this result into any document leaving the run folder.**

## Order 2 — release gates, one query at a time. Any failure stops the run.

| Gate | Query | Failure means |
|---|---|---|
| 0e | **Q-G4** | Provisioning artifact with DDL **sourced and cited**, then block. Never author DDL |
| 0d | **Q-G3b** (a)–(d) | `F___SEQUENCE` or `PKG_ENGPRECOMMIT` not callable, or not `VALID` → stop. **Record both owners** — `values.json` `environment` |
| 0d | 🆕 **Q-G3c** | The target's auth code. `core_info_rows ≠ 1` → stop. **Record `TARGET_AUTH_CODE` and `TARGET_PK_FRACTION` in `00-inputs.md`** |
| 0d | 🆕 **Q-G3d** (a)(b)(c)(e) | What the called code and the target tables do. A `COMMIT`/`ROLLBACK`/`AUTONOMOUS_TRANSACTION` in `F___SEQUENCE` or `P_ENGFixingCurve_PreCommit`, a `COMMIT` in `p_check_Val_Curves_precommit` that is **not reached when there are no step-8 rows**, or a trigger that writes elsewhere → stop, source question. **(e) → `01-evidence/Q-G3d-columns.csv`**: the renderer checks every column against it |
| 0a | **Q-G1** | `BRANCH_PK ≠ 20007.4` → stop |
| 0b | **Q-G2 level 1** | `FK_MISCONFIG` → the GBO MIS header (NY: `64408.35`). Unresolved → stop |
| 0g | **Q-G7** + **Q-G6** | Identity per destination table. ⚠️ **An empty target table is not a missing identity** — use the Q-G7 derivation. Run 3 left step 12 unwritten because `T_BOX_ERRORS_FE_S` is empty in Tier 2; the derivation needs no row. Tier 1 reference values in Q-G6 are a cross-check, never the source |

## Order 3 — Tier 2 mining, one query at a time

| Step | Query | Note |
|---|---|---|
| 1 | Q-01 | Existing configuration for NY? If yes, **stop** — "adapt existing" is a human decision |
| 2 | Q-02 + 🆕 **Q-02c** | Mine `DESCRIPTION`, `FK_CALENDAR`, `FK_CURRENCY` only. **Sources are not mined** — see rules |
| 3 | Q-03 | + the `DESCRIPTION` collision pre-check |
| 4 | **Q-04c** (a) **and** (b) — the step-4 set and its counts, saved as `Q-04c-quote-ref-column-gbo.csv` and `Q-04c-quote-ref-column-counts.csv` (the renderer reads both) | The quote reference is **`FK_BS`**. Q-04c's joined count must equal its unjoined count — a quote ref that does not resolve is a finding, not a row to drop. **Do not test `PK` against the quote-reference table**: a bridge row's PK matching some quote ref is a numeric coincidence (run 4 stopped on `87.35`) |
| 5 | Q-01c | Branch association — run-stopping if it cannot be emitted |
| 6 | Q-05 | NY's GBO accrual rows, per instrument |
| 7 | **Q-06 — the expert's query**, then **Q-06c** | Q-06 shows every branch's exceptions under `64408.35`, with the branch named; Q-06c is the same set with aliased columns, saved as `Q-06c-accrual-exceptions-emit.csv` — the renderer reads it and lists what it filters out |
| 8 | Q-07 | + the hard-rule-8 control |
| 4b, 9, 10 | Q-G7, Q-08, Q-09 — BOX side | **Verify absent** in `BOX_FE`. Status `CONFIRMED_ABSENT`, no SQL |
| 11 | Q-10 + **Q-10c (a)(c)** + 🆕 **Q-10d** | Tier 1's dummy label is absent in Tier 2 (run 4). **Q-10d** reads what the Tier 1 dummy *is* and lists Tier 2 candidates — then **a decision card** |
| 12 | Q-13 (a) | Columns of `T_BOX_ERRORS_FE_S` — expect `PK, FK_OWNER_OBJ, FK_BRANCH, FK_INSTRUMENT, LIMIT_ERRORS` |
| 13 | Q-11 | Verify only |
| 14a | 🆕 **Q-12 (a)** | Which approved instruments already have a Days Matured row in Tier 2 |
| 14b | Q-12 columns | Evidence for `NOT_BRANCH_SCOPED` |

Plus the **C2 read** for every step: does a BOX-side row already exist for NY?

## Order 4 — Tier 1 reference reads (proposal aids only), one at a time

| # | Query | For |
|---|---|---|
| 1 | **Q-13 (b)** — SLB's `LIMIT_ERRORS` per instrument, **`FK_BRANCH = REFERENCE_BRANCH_PK` (`20087.4`)** | Step 12's proposal ([ADR 0004](../../../docs/decisions/0004-step12-limits-from-reference-branch.md)) |
| 2 | **Q-05d** — SLB's GBO row vs SLB's BOX row | ⛔ Whether GBO→BOX transforms accrual values. **No step-6 value is `PROPOSED` until it has run** |
| 3 | SLB's four accrual values | Question 2 of the sign-off pack |
| 4 | 🆕 **Q-12 (b)** — Days Matured for the instruments Q-12 (a) found missing | Step 14a's proposal |
| 5 | 🆕 **Q-10c (b)** — Madrid's dummy-book rows | Shows the two-row pattern to the SME |
| 6 | **Q-10d (a)** — what Tier 1's dummy label `26391.4` is (`CODE`, `DESCRIPTION`, domain) | So Q-10d (b) can look for its Tier 2 equivalent |

⛔ **Nothing from Tier 1 enters the SQL as a mined value.** Say "Tier 1" beside every such value.

---

## The SQL: write `values.json`, render, never edit

⛔ **You never write or edit a `.sql` file** — not to fix a defect, not to add a comment. The four files
are produced by `scripts/render_sql.py` from `03-sql/values.json`; the validator re-renders them and
FAILs any byte that differs (`sql-edited-by-hand`) and any `.sql` file it did not produce.

1. **Copy `agents/sigom-box-fe-configs-agent/templates/values.example.json` to
   `runs/NY_SCH/tier2-pre/03-sql/values.json`** and replace every `<…>`. Every value is
   `{"value": …, "source": …}`; a source names the query (`Q-02`), the input (`00-inputs.md
   SOURCE_FRONT`) or the decision (`decision 3` = row 3 of `00-decisions.md`). Every walk step has an
   entry whose `status` is **the same as its row in `02-findings.md`**. A held step names `waits_on`.
2. **Run `python3 scripts/render_sql.py runs/NY_SCH/tier2-pre/`.** It either REFUSES — each problem with
   its JSON path and the fix — or writes `…-rehearsal.sql`, `…-config.sql`, `…-verify.sql`,
   `…-rollback.sql` and `render-report.md`, then runs the validator.
3. **Fix refusals in `values.json` or the evidence, never around them.** A refusal you believe is wrong:
   say so and stop — the same rule as the validator.
4. If the **rendered SQL** looks wrong, it is a **template defect**: report it with the file and line,
   and stop. Do not work round it.

**What `values.json` must say — the domain rules, which are still yours:**

1. **Auth code** (point 1) — `environment.target_auth_code` from **Q-G3c**, the same as `00-inputs.md`.
   The rendered block checks the fraction on every PK before the first INSERT; verify V1 re-checks.
2. **Owners** — `environment.sequence_function_owner` / `precommit_package_owner` from **Q-G3b (b)/(d)**.
3. **Identity** — nine constants from the **Q-G7 derivation** (Q-G6 as cross-check), one per destination
   object. **Four different owners**: Config, FixingCurve, Limit Error Assign, Days Matured (run 4 wrote
   the Config owner on Days Matured — now refused).
4. **Step 2** (point 2) — `DESCRIPTION`, `FK_CALENDAR`, `FK_CURRENCY` exactly as mined (Q-02). Sources
   are not in `values.json` at all: `FK_SOURCE_FRONT = branch.source_front` (`513.4`), `FK_SOURCE_BACK =
   586.4`, always. **Step 3** — `DESCRIPTION`, `FK_CURRENCY` as mined (Q-03).
5. **Step 4** (point 3) — only `expected_count` = Q-04c (b) `N_FK_BS`. The set is read from the CSV.
6. **Step 6** — one row per approved instrument, **every column present** (`null` for an empty one —
   run 5 dropped `FK_BASIS`), the values of decision card 1, which says which values and why (NY's GBO,
   or SLB's BOX after Q-05d).
7. **Step 7** (point 4) — only `expected_count`: Q-06c filtered to `20007.4` and the approved
   instruments. The renderer filters, writes `FK_BRANCH = 20007.4`, copies `CRITERIAL`, and lists every
   row it dropped in `render-report.md` — copy that list into the findings. Never GBO's `141.35`.
8. **Step 11** (point 5) — `books` (card 2) and `dummy_book` (card 3, **BOX FE team**, cited as
   `decision 3`); the dummy is **never a real book's label**. Also write `DUMMY_BOOK_LABEL: <value>` into
   `00-inputs.md` once decided.
9. **Step 12** — one row per approved instrument, **SLB's** `LIMIT_ERRORS` (card 4, ADR 0004). A whole
   number > 0: `0` is refused.
10. **Step 14a** (point 6) — `already_present` = what Q-12 (a) found; `rows` = the missing instruments
    with `NUM_DAYS` from Q-12 (b) (card 5); `ddate` = `SYSDATE` or `TRUNC(SYSDATE)` (card 5 — see Q-12's
    `ddate_time_part`). All present → `CONFIRMED_PRESENT`. **Step 14b** `NOT_BRANCH_SCOPED` (point 7).
11. **Steps 1, 4b, 8, 9, 10** — `CONFIRMED_ABSENT`. Anything else is refused: step 1 present means an
    existing configuration (a human decision), 8/9/10 rows need repo support first.
12. **`DESCRIPTION` collisions** — Q-02/Q-03 pre-checks; never adjust a mined value to dodge one. (The
    rendered block re-checks at run time.)

**What the renderer guarantees, so you do not re-check it by hand** (each one a past defect): PKs from
`F___SEQUENCE(…,'X')` on their own line, `chk_pk` never inside `VALUES`; allocate-first for the header
and curve; cursor fields match their aliases; step 4 in a loop over the generated list; step 11 rows
carry `FK_PARENT`; guards that read the table; the curve pre-commit after the array; the Config
pre-commit last; every step's full header; `BOX_FE` only; ASCII only; the verify file V1–V12; the
rollback. **If you find one of these wrong in the output, it is a template defect — report it.**

---

## Decisions — one card at a time, never a list at the end

**Run 4 finished by listing three blockers and stopping.** With a decision-maker in the session, that
wastes the session. From now on:

**Whenever the run reaches something only a person can decide, stop and put ONE decision card**, then
wait for the answer before the next. Never end the session with open decisions you have not put.

```text
DECISION 3 of 5 — Step 11: dummy-book label for Tier 2
Why it matters : every instrument needs a (dummy book × instrument) row; without it step 11 cannot run
Releases       : step 11 (12 rows)
Evidence       : Q-10d — Tier 1 dummy is 26391.4 '<CODE> - <DESCRIPTION>'; not in Tier 2.
                 Tier 2 candidates: 12345.44 '<CODE>' used by 4 branches × all instruments
Options        : A) use 12345.44   B) another label: ____   C) must be created in Tier 2 first (blocks step 11)
Recommendation : A — same CODE as Tier 1's dummy, and every Tier 2 branch uses it
If wrong       : that (book, instrument) is never scheduled by the FE batch — silently
Authority      : BOX FE team (technical), not the product SME
Please reply   : decision (A/B/C + value), your name, your role — or the name and role of the person who decided
```

**Record every answer** in `RUN_FOLDER/00-decisions.md` — one row: number · decision · value · name ·
role · date · evidence — and cite it from the findings as `[stated: <name>, <role>, <date>]` (**never
`[stated: user]`**, and never `[confirmed: …]`, which is for query results). The validator reads it.

**Authority, not presence.** Each card names who may decide it. If the person in the session is not that
authority, they may relay a named person's answer (`[stated: <name>, <role>, via <operator>]`), or say
"defer". A deferred card leaves its step `SME_DECISION_REQUIRED` with no SQL; the others still close.

**The cards, in this order** — only those the evidence actually raises:

| # | Decision | Authority | Proposal from |
|---|---|---|---|
| 1 | Step 6 — accrual values per instrument, **after Q-05d** (a fact to establish first, not a vote) | product SME | NY's GBO, SLB's BOX shown alongside |
| 2 | Step 11 — **the branch's real books** (say plainly no query proves the list complete) | product SME | Q-10, Data-Lake books |
| 3 | Step 11 — **the Tier 2 dummy-book label** | **BOX FE team** | Q-10d candidates |
| 4 | Step 12 — `LIMIT_ERRORS` per instrument: **SLB's** (ADR 0004); an instrument SLB lacks is its own card. **Never propose NY's GBO zeros** | product SME | Q-13 (b) |
| 5 | Step 14a — `NUM_DAYS` per missing instrument, and `DDATE`: `SYSDATE` or `TRUNC(SYSDATE)` (show Q-12's `ddate_time_part`) | product SME | Q-12 (b) |
| 6 | Steps 9 / 10 — **only if** new evidence reopens Question G (e.g. NY's currency-basis rows); otherwise they stay `CONFIRMED_ABSENT` | BOX FE team | Q-08, Q-09 |

**If `SME_IN_SESSION` is `none`:** put no cards; steps 6, 11, 12, 14a → `SME_DECISION_REQUIRED`, and the
cards go into `00-gate-0c-signoff-request.md` for signature.

**Either way:** steps 7 and 8 are **mined**, with rows attached. Steps 4b, 9, 10 → `CONFIRMED_ABSENT`
(Question G, closed 2026-09-22) unless card 6 reopened them. Step 13 → verify only. Step 14b →
`NOT_BRANCH_SCOPED`.

---

## What to produce

`RUN_FOLDER/`: `00-inputs.md` (first), **`00-decisions.md`** (one row per card answered), `01-evidence/` one CSV per query, `02-findings.md` one statused row
per walk step **including 14a and 14b**, `03-sql/values.json` **and the four files rendered from it**
(plus `render-report.md`), `05-source-questions.md`, `99-open-items.md` naming who each item waits on,
and the gate 0c pack.

**Open questions to carry into `05-source-questions.md`** — for the BOX FE team, not to reason about:
what `DDATE` means on Days Matured; any quote reference in Q-04c that does not resolve.

## ⛔ The validator is a gate — iterate until it is clean

1. `python3 scripts/render_sql.py runs/NY_SCH/tier2-pre/` — renders, then runs the validator.
2. Fix every REFUSED and every FAIL **in `values.json`, the evidence or the findings**. Run again. Repeat
   until **0 REFUSED, 0 FAIL**.
3. **Paste the final output as the last thing you produce**, and the "Rows per step" table of
   `render-report.md`.

If a check looks wrong, **say so and leave it failing** — never reshape the SQL to slip past it.

## What a passing run looks like

- ✅ Preflight first and quoted; every release gate cites an evidence file (Q-G3b (d) and **Q-G3d**
  included); `TARGET_AUTH_CODE` recorded.
- ✅ `03-sql/values.json`, every value with a source; **no `.sql` file touched by hand**.
- ✅ `render_sql.py`: 0 REFUSED; four files and `render-report.md` written; validator **0 FAIL**, pasted.
- ✅ Step 2 mined values; step 4 count = Q-04c (b); step 7 count and dropped rows copied from the render
  report; step 11 books + a **real** dummy label; step 12 SLB's limits; step 14a missing instruments only.
- ✅ Every decision was put as a card and is in `00-decisions.md` with a name and role, and every
  decided value cites it (`decision N`).
- ✅ Every closed decision names a person with authority for it; every open one says who it waits on.
- ❌ Any invented value, a `.sql` file written or edited by hand, a refusal worked round, GBO
  `FK_BRANCH` or source system in a BOX row, `LIMIT_ERRORS = 0`, or a step emitted on a guessed scope —
  **fail**, however good the rest looks.

**If something is unclear, ask a source question or record an open item. Do not reason your way to an
answer** — six of the expert's seven points were rules this repo did not have, and no amount of
reasoning over the data would have produced them.
