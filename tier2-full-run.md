# Devin kickoff — NY_SCH, Tier 2 PRE, full run (run 4)

**Rewritten 2026-09-23 after the BOX FE expert's review of run 3** — seven points, all in
[ADR 0005](../../../docs/decisions/0005-box-fe-expert-review-run-3.md). Run 3's mechanics were clean;
what the expert found was **domain rules the repo did not have**: which header columns are BOX's own,
how GBO keys the branch on accrual exceptions, the dummy book, Days Matured. This prompt also drops four
instructions that contradicted the charter (steps 4b/9/10 "parked", "do not call
`p_check_Val_Curves_precommit`", "gate 0c must stay open", the `20314.4` hypothesis).

**What "full" means.** The agent runs the whole walk. How much SQL comes out depends on
**`SME_IN_SESSION`**: with an authorised person present, gate 0c closes in the session and every step
is emitted; without one, the run emits steps 1–5 and holds the rest at `SME_DECISION_REQUIRED`. Both
pass if the gaps are reported honestly.

---

## Before you paste: setting up the session

| | |
|---|---|
| **Repos** | this automation repo (**read/write**). `cib-boxfin-dbboxfe` is not needed — attach it only if the agent raises a source question and asks for it |
| ⚠️ **Database** | **Devin gets no connection.** You run every query on your read-only accounts — `DB_ACCESS_MODE = assisted` |
| **Which database** | **Tier 2 PRE** (`DEVENG` + `BOX_FE` + `GOM_GLB_SYS`) for everything, except the **Tier 1** reference reads in batch 4 |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or local edit on `cib-boxfin-dbboxfe` or `cib-boxacc-dbboxacc`, ever |
| **Expected** | ~30 queries in **four batches** |
| ⛔ **Before you start** | **Archive run 3** to `runs/NY_SCH/tier2-pre/archive/run-03/` (see `runs/README.md`). Run 4 overwrites the run folder — and step 4 needs run 3's SQL to compare against (Q-04c) |
| ✏️ **Fill in** | `SME_IN_SESSION` below |

---

You are running as this repo's `sigom-box-fe-configs-agent`
(`agents/sigom-box-fe-configs-agent/AGENT.md`). **Read that charter in full before anything else**, then
`docs/reference/fe-walk-notes.md` (its first block is the 2026-09-23 expert review),
`docs/reference/queries/fe-config-mining.md`, and `agents/sigom-box-fe-configs-agent/templates/`.
Every hard rule binds you without exception.

## Run inputs — write these into `00-inputs.md` first, one `NAME: value` per line

| Input | Value |
|---|---|
| `RUN_MODE` | `normal` |
| `BRANCH_CODE` | `NY_SCH` |
| `BRANCH_PK` | `20007.4` — **re-confirm with Q-G1**; a mismatch is a stop |
| `TARGET_ENV` / `GBO_SOURCE` | **Tier 2 PRE**, both — same environment |
| `DB_ACCESS_MODE` | ⚠️ **`assisted`. You have NO database connection.** You state the query; the operator returns the CSV. **Never attempt to connect** |
| `SOURCE_ACCESS_MODE` | `direct`, **read-only** |
| `RUN_FOLDER` | `runs/NY_SCH/tier2-pre/` |
| `APPROVED_INSTRUMENTS` | `20092.4, 2.4, 20.4, 20111.4, 20213.4, 20313.4` — Swap, Deposit & Loan, Cross Currency Swap, OTC Option, Caps And Floors, Credit Derivatives `[stated: <SME_NAME>, via Edouard, 2026-09-21]` |
| `SOURCE_FRONT` | `513.4` — Murex 3 Latam `[stated: BOX FE expert via Edouard, 2026-09-23]`. Q-02c proves it exists |
| `DUMMY_BOOK_LABEL` | `26391.4` — **the Tier 1 value**. Q-10c proves it holds in Tier 2 before step 11 uses it |
| `TARGET_AUTH_CODE` | **from Q-G3c** — never typed. Record the fraction too: `TARGET_PK_FRACTION` |
| `QUOTE_REF_COLUMN` | **from Q-04c** — `FK_BS` if outcome A. The column step 4's list is generated from |
| `SME_IN_SESSION` | **✏️ Fill in before pasting:** name and role of whoever may decide accrual values, error limits, books and Days Matured — or `none` |

### ⛔ How you get data: you ask, a human runs it

1. State the **query ID**, purpose, **which database**, and the parameter values already resolved.
2. Give the **SQL ready to run**, placeholders substituted where known.
3. State the **exact filename** — `01-evidence/Q-05-accrual-gbo.csv` — and the row count you expect.
4. **Stop and wait.** Never proceed on an assumed result.
5. Check the CSV's shape before using it. A wrong shape is a re-run request.

You **can** run `python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/` yourself. Do.

---

## Batch 1 — the preflight, alone

```sql
SELECT USER,
       SYS_CONTEXT('USERENV','DB_NAME')                        AS db,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER='BOX_FE')  AS boxfe_visible,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER='DEVENG')  AS deveng_visible
FROM   DUAL;
```

`BOXFE_VISIBLE = 0` means **blind, not empty** — stop and report. → `01-evidence/Q-G4-preflight.csv`.
**Never copy the account name from this result into any document leaving the run folder.**

## Batch 2 — release gates. Any failure stops the run.

| Gate | Query | Failure means |
|---|---|---|
| 0e | **Q-G4** | Provisioning artifact with DDL **sourced and cited**, then block. Never author DDL |
| 0d | **Q-G3b** | `F___SEQUENCE` not callable → stop |
| 0d | 🆕 **Q-G3c** | The target's auth code. `core_info_rows ≠ 1` → stop. **Record `TARGET_AUTH_CODE` and `TARGET_PK_FRACTION` in `00-inputs.md`** |
| 0a | **Q-G1** | `BRANCH_PK ≠ 20007.4` → stop |
| 0b | **Q-G2 level 1** | `FK_MISCONFIG` → the GBO MIS header (NY: `64408.35`). Unresolved → stop |
| 0g | **Q-G7** + **Q-G6** | Identity per destination table. ⚠️ **An empty target table is not a missing identity** — use the Q-G7 derivation. Run 3 left step 12 unwritten because `T_BOX_ERRORS_FE_S` is empty in Tier 2; the derivation needs no row. Tier 1 reference values in Q-G6 are a cross-check, never the source |

## Batch 3 — Tier 2 mining, all steps

| Step | Query | Note |
|---|---|---|
| 1 | Q-01 | Existing configuration for NY? If yes, **stop** — "adapt existing" is a human decision |
| 2 | Q-02 + 🆕 **Q-02c** | Mine `DESCRIPTION`, `FK_CALENDAR`, `FK_CURRENCY` only. **Sources are not mined** — see rules |
| 3 | Q-03 | + the `DESCRIPTION` collision pre-check |
| 4 | Q-04 + 🆕 **Q-04c (a)(b)**, and **(c)** if Tier 2 `BOX_FE` has any curve | ⛔ **Q-04c decides which column is the quote reference.** Outcome B or C → step 4 is `EVIDENCE_REQUIRED` **and steps 2, 3 and 5 are held with it** — a curve without its array is incomplete, and step 5 depends on 2–4 |
| 5 | Q-01c | Branch association — run-stopping if it cannot be emitted |
| 6 | Q-05 | NY's GBO accrual rows, per instrument |
| 7 | **Q-06 — the expert's query**, then **Q-06c** | Q-06 shows every branch's exceptions under `64408.35`, with the branch named; Q-06c is the same set with aliased columns — the file step 7 is generated from |
| 8 | Q-07 | + the hard-rule-8 control |
| 4b, 9, 10 | Q-G7, Q-08, Q-09 — BOX side | **Verify absent** in `BOX_FE`. Status `CONFIRMED_ABSENT`, no SQL |
| 11 | Q-10 + 🆕 **Q-10c (a)(c)** | Dummy label exists in Tier 2, and some Tier 2 branch already uses it |
| 12 | Q-13 (a) | Columns of `T_BOX_ERRORS_FE_S` — expect `PK, FK_OWNER_OBJ, FK_BRANCH, FK_INSTRUMENT, LIMIT_ERRORS` |
| 13 | Q-11 | Verify only |
| 14a | 🆕 **Q-12 (a)** | Which approved instruments already have a Days Matured row in Tier 2 |
| 14b | Q-12 columns | Evidence for `NOT_BRANCH_SCOPED` |

Plus the **C2 read** for every step: does a BOX-side row already exist for NY?

## Batch 4 — Tier 1 reference reads (proposal aids only)

| # | Query | For |
|---|---|---|
| 1 | **Q-13 (b)** — SLB's `LIMIT_ERRORS` per instrument | Step 12's proposal ([ADR 0004](../../../docs/decisions/0004-step12-limits-from-reference-branch.md)) |
| 2 | **Q-05d** — SLB's GBO row vs SLB's BOX row | ⛔ Whether GBO→BOX transforms accrual values. **No step-6 value is `PROPOSED` until it has run** |
| 3 | SLB's four accrual values | Question 2 of the sign-off pack |
| 4 | 🆕 **Q-12 (b)** — Days Matured for the instruments Q-12 (a) found missing | Step 14a's proposal |
| 5 | 🆕 **Q-10c (b)** — Madrid's dummy-book rows | Shows the two-row pattern to the SME |
| 6 | 🆕 **Q-04c (c)** on SLB's curve — only if Tier 2 had no BOX curve to test | Settles the `_X` column question on the BOX side |

⛔ **Nothing from Tier 1 enters the SQL as a mined value.** Say "Tier 1" beside every such value.

---

## The rules for emitting SQL — the first four are new, from the expert

**Build the three files from `templates/`**: `NY_SCH-tier2-pre-config.sql`, `-verify.sql`,
`-rollback.sql`. Replace every placeholder with the recorded value; provenance goes in the step header
or the constant's comment. No `&&`, no leftover placeholder, no `IF 1 = 0`.

⛔ **The config script touches `BOX_FE` only** `[assumed: Edouard, 2026-09-23]` — the account that
applies it cannot read `DEVENG`, `PGT_*` or `GOM_GLB_SYS`. Any reference to those schemas in the config
file is a FAIL. Comparisons with GBO belong in the verify script, which the operator runs on his
read-only account.

1. 🆕 **Auth code — visible and asserted** (point 1). `F___SEQUENCE(…,'X')` adds it; the script
   declares `c_expected_fraction` = `TARGET_PK_FRACTION` from Q-G3c and calls `chk_pk()` after **every**
   `F___SEQUENCE` — the first before any INSERT, so a script in the wrong environment stops having
   written nothing. Verify **V1** re-checks every created row against `t__CORE_INFO_S`. **Never add a
   typed fraction to a PK** (the team's own `F___SEQUENCE(…,1) + 0.21` is right in one environment
   only); the fraction appears only as the expectation being checked.
2. 🆕 **Step 2 sources are BOX's** (point 2). `FK_SOURCE_BACK = 586.4`, always. `FK_SOURCE_FRONT =
   SOURCE_FRONT` (`513.4`). Show GBO's `9.4`/`11.4` in the findings **for comparison only**.
3. 🆕 **Step 4 is generated, not typed** (point 3). Run
   `python3 scripts/evidence_to_sql.py list 01-evidence/Q-04c-quote-ref-column-gbo.csv <column>` on the
   column **Q-04c** proved (record it as `QUOTE_REF_COLUMN` in `00-inputs.md`) and paste its output as
   `v_quote_refs`. The script guards the count; the validator checks the list equals the CSV; verify
   **V4** checks BOX equals GBO both ways. In the findings, **say which column run 3's 38 values came
   from** — the expert doubted them.
4. 🆕 **Step 7 — NY's rows, written with NY's branch** (point 4). From Q-06: keep rows whose branch
   config resolves to `20007.4`; keep approved instruments; **list every row dropped and the branch it
   belongs to**. Write `FK_BRANCH = BRANCH_PK` — never GBO's `141.35`, which is a branch *config*. Copy
   `CRITERIAL` from the GBO row. Generate the rows from **Q-06c**:
   `python3 scripts/evidence_to_sql.py rows 01-evidence/Q-06c-accrual-exceptions-emit.csv
   FK_INSTRUMENT,FK_STRATEGY,FK_INSTRTYPE,CRITERIAL --where BRANCH_PK=20007.4 --in
   FK_INSTRUMENT=<approved>`. Validator checks SQL = CSV; verify **V10** checks BOX = GBO.
5. 🆕 **Step 11 — `(books + 1) × instruments`** (point 5). Every instrument gets its book rows **and**
   a dummy-book row. NY, one book: **12 rows**.
6. 🆕 **Step 14a — Days Matured, missing instruments only** (point 6). Present → `CONFIRMED_PRESENT`, no
   SQL. Missing → insert, `NUM_DAYS` from Tier 1 for that instrument, `DDATE = SYSDATE` proposed and
   asked. **Step 14b** — `T_BOX_ENGSETUP_S`: nothing, `NOT_BRANCH_SCOPED` (point 7).
7. **Every PK is `F___SEQUENCE('<TABLE>','X')`** on a variable; children reference the parent's variable.
8. **Explicit column list on every INSERT**; every column classified — mined, allocated, structural,
   intra-config, **re-keyed**, or signed. For every FK, name the table it points into — and the table
   GBO's column points into. Different tables → re-keyed → never copied.
9. **Identity columns are literals** from the Q-G7 derivation, each with its source comment. Never
   `SELECT … INTO` from a table, never `&&`.
10. **Steps 2–4: allocate the curve's PK before the header.** `FK_CURVEMAN`/`FK_CURVEACC` are `NOT NULL`, so
    the earlier "NULL, then UPDATE" fails with ORA-01400. Allocate both PKs, insert the header pointing at
    `v_curve_pk`, then the curve, then its array. No UPDATE.
11. **Pre-commits:** `P_ENGFixingCurve_PreCommit(v_curve_pk)` after step 4 — no DML.
    **`p_check_Val_Curves_precommit(v_conf_pk)` last** — it writes and **COMMITs**, so nothing may follow
    it and the rollback file is the undo. With no step-8 rows it should find nothing to do.
12. **Every instrument-keyed step is filtered to `APPROVED_INSTRUMENTS`** — 6, 7, 8, 11, 12, 14a. Report
    what you filtered out.
13. **Open every step with its header block** — What · Source · Findings row + status · Depends on ·
    **If wrong**. The template has them.
14. **Guards before inserting** where the rollback keys by branch or instrument — steps 11, 12, 14a abort
    if rows already exist (template). The rollback then deletes only this run's rows, and **keeps 14a's**.
15. **`DESCRIPTION` is globally unique** on the header and the curve — pre-check; never adjust a mined
    value to dodge a collision.

---

## Decisions — who may take them

**If `SME_IN_SESSION` names an authorised person**, put these **one at a time** — what is decided ·
which steps it releases · your proposal **and its evidence** · what goes wrong if it is wrong — and wait:

1. **Step 6 — the four `NOT NULL` accrual values × 6 instruments.** Only after Q-05d. If Q-05d shows GBO
   and BOX differ for SLB, say whether NY's values need the same transformation — that is a fact to
   establish, not a vote.
2. **Step 12 — `LIMIT_ERRORS` per instrument: propose SLB's** (ADR 0004). ⚠️ NY's GBO holds `0` for all
   six; **do not propose it** — run 3's operator used it as a test decision. An instrument SLB lacks is
   its own question.
3. **Step 11 — the book list.** Say plainly that no query can prove it complete.
4. **Step 14a — `NUM_DAYS` for each missing instrument**, and `DDATE = SYSDATE`.

Record each answer as `[stated: <full name>, <role>, <date>]` — **never `[stated: user]`**. Partial
closure is normal: a declined or out-of-authority decision stays `SME_DECISION_REQUIRED`, the others
close and their steps are emitted.

**If `SME_IN_SESSION` is `none`:** steps 6, 11, 12, 14a → `SME_DECISION_REQUIRED`, no SQL. Fill in
`00-gate-0c-signoff-request.md` with the evidence so it can be signed.

**Either way:** steps 7 and 8 are **mined**, with rows attached. Steps 4b, 9, 10 → `CONFIRMED_ABSENT`
(Question G, closed 2026-09-22). Step 13 → verify only. Step 14b → `NOT_BRANCH_SCOPED`.

---

## What to produce

`RUN_FOLDER/`: `00-inputs.md` (first), `01-evidence/` one CSV per query, `02-findings.md` one statused row
per walk step **including 14a and 14b**, `03-sql/` **the three files**, `05-source-questions.md`,
`99-open-items.md` naming who each item waits on, and the gate 0c pack.

**Open questions to carry into `05-source-questions.md`** — for the BOX FE team, not to reason about:
Q-04c's outcome if it is B or C; what `DDATE` means on Days Matured.

## ⛔ The validator is a gate — iterate until it is clean

1. `python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/`
2. Fix every FAIL. Run again. Repeat until **0 FAIL**.
3. **Paste the final output as the last thing you produce.**

If a check looks wrong, **say so and leave it failing** — never reshape the SQL to slip past it.

## What a passing run looks like

- ✅ Preflight first and quoted; every release gate cites an evidence file; `TARGET_AUTH_CODE` recorded.
- ✅ Three SQL files. The config asserts the auth code; verify has V1–V9 with expected results.
- ✅ Step 2: `586.4` / `513.4`. Step 4: read from `DEVENG` on the Q-04c column, or honestly blocked.
  Step 7: only NY's rows, `FK_BRANCH = 20007.4`, dropped rows listed. Step 11: 12 rows incl. dummy.
  Step 12: SLB's limits proposed, identity from the derivation. Step 14a: missing instruments only.
- ✅ Every closed decision names a person with authority for it; every open one says who it waits on.
- ✅ Validator **0 FAIL**, pasted.
- ❌ Any invented value, typed quote list, GBO `FK_BRANCH` or source system in a BOX row, `LIMIT_ERRORS = 0`
  proposed, or step emitted on a guessed scope — **fail**, however good the rest looks.

**If something is unclear, ask a source question or record an open item. Do not reason your way to an
answer** — six of the expert's seven points were rules this repo did not have, and no amount of
reasoning over the data would have produced them.
