# Devin kickoff — NY_SCH, Tier 2 PRE, full run (run 5)

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
| ⛔ **Before you start** | **Archive run 4** to `runs/NY_SCH/tier2-pre/archive/run-04/` (see `runs/README.md`). The next run overwrites the run folder |
| 📁 **Repo layout** | This automation repo sits in the **`automation/` subfolder** of the checkout (`cib-box-auki-nbranch/automation/`). Every path in this prompt is relative to `automation/`. The prompt tells Devin to find it — you do not need to do anything |
| ✏️ **Fill in** | `SME_IN_SESSION` below |

---

You are running as the `sigom-box-fe-configs-agent`.

**Step 0 — find the repo root before anything else.** This automation repo is usually **not** the root
of your checkout: it lives in a subfolder, normally `automation/`. Run

```bash
find . -path '*/agents/sigom-box-fe-configs-agent/AGENT.md' -not -path '*/archive/*' | head -5
```

The folder two levels above `agents/` is **`REPO_ROOT`** — `cd` into it. **Every path in this prompt,
the charter and the scripts is relative to `REPO_ROOT`.** If `find` returns nothing, say so and stop;
if it returns more than one, list them and ask which. **Never report the charter missing without
running this search first**, and never recreate it.

Then **read the charter** (`agents/sigom-box-fe-configs-agent/AGENT.md`) **in full**, then
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
| `DUMMY_BOOK_LABEL` | ⛔ **Not known for Tier 2.** Tier 1's `26391.4` does not exist there (run 4). Found by **Q-10d**, then put to a person as a decision card. **Never a real book's label** |
| `BOOKS` | The branch's real book labels — **a decision card** (run 4 used `NY001` = `23958.44`, test-signed) |
| `TARGET_AUTH_CODE` | **from Q-G3c** — never typed. Record the fraction too: `TARGET_PK_FRACTION` |
| `QUOTE_REF_COLUMN` | `FK_BS` — `[stated: operator, BOX Dev, 2026-09-24]`: `T_PGT_ENGLKFC_X.FK_BS = T_PGT_QUOTE_REFERENCE_S.PK`, as Q-04 already recorded. **Not a question any more** |
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
| 4 | **Q-04c** — the step-4 set, decoded and export-ready | The quote reference is **`FK_BS`**. Q-04c's joined count must equal its unjoined count — a quote ref that does not resolve is a finding, not a row to drop. **Do not test `PK` against the quote-reference table**: a bridge row's PK matching some quote ref is a numeric coincidence (run 4 stopped on `87.35`) |
| 5 | Q-01c | Branch association — run-stopping if it cannot be emitted |
| 6 | Q-05 | NY's GBO accrual rows, per instrument |
| 7 | **Q-06 — the expert's query**, then **Q-06c** | Q-06 shows every branch's exceptions under `64408.35`, with the branch named; Q-06c is the same set with aliased columns — the file step 7 is generated from |
| 8 | Q-07 | + the hard-rule-8 control |
| 4b, 9, 10 | Q-G7, Q-08, Q-09 — BOX side | **Verify absent** in `BOX_FE`. Status `CONFIRMED_ABSENT`, no SQL |
| 11 | Q-10 + **Q-10c (a)(c)** + 🆕 **Q-10d** | Tier 1's dummy label is absent in Tier 2 (run 4). **Q-10d** reads what the Tier 1 dummy *is* and lists Tier 2 candidates — then **a decision card** |
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
| 6 | **Q-10d (a)** — what Tier 1's dummy label `26391.4` is (`CODE`, `DESCRIPTION`, domain) | So Q-10d (b) can look for its Tier 2 equivalent |

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
3. **Step 4 is generated, not typed** (point 3). Run
   `python3 scripts/evidence_to_sql.py list 01-evidence/Q-04c-quote-ref-column-gbo.csv FK_BS` and paste
   its output as `v_quote_refs` **unchanged** — do not reorder or retype it. The script guards the
   count; the validator checks the list equals the CSV; verify **V4** checks BOX equals GBO both ways.
4. 🆕 **Step 7 — NY's rows, written with NY's branch** (point 4). From Q-06: keep rows whose branch
   config resolves to `20007.4`; keep approved instruments; **list every row dropped and the branch it
   belongs to**. Write `FK_BRANCH = BRANCH_PK` — never GBO's `141.35`, which is a branch *config*. Copy
   `CRITERIAL` from the GBO row. Generate the rows from **Q-06c**:
   `python3 scripts/evidence_to_sql.py rows 01-evidence/Q-06c-accrual-exceptions-emit.csv
   FK_INSTRUMENT,FK_STRATEGY,FK_INSTRTYPE,CRITERIAL --where BRANCH_PK=20007.4 --in
   FK_INSTRUMENT=<approved>`. Validator checks SQL = CSV; verify **V10** checks BOX = GBO.
5. **Step 11 — `(books + 1) × instruments`** (point 5). Every instrument gets its book rows **and** a
   dummy-book row. NY, one book: **12 rows**. ⛔ **The dummy row cannot be waived** — it is the BOX FE
   team's technical rule, not a scope choice. `DUMMY_BOOK_LABEL` set to a real book's label, to satisfy a
   check, is the defect run 4 produced. No Tier 2 dummy label → step 11 `EVIDENCE_REQUIRED`, no SQL.
6. 🆕 **Step 14a — Days Matured, missing instruments only** (point 6). Present → `CONFIRMED_PRESENT`, no
   SQL. Missing → insert, `NUM_DAYS` from Tier 1 for that instrument, `DDATE = SYSDATE` proposed and
   asked. **Step 14b** — `T_BOX_ENGSETUP_S`: nothing, `NOT_BRANCH_SCOPED` (point 7).
7. **Every PK is `F___SEQUENCE('<TABLE>','X')`** on a variable; children reference the parent's variable.
8. **Explicit column list on every INSERT**; every column classified — mined, allocated, structural,
   intra-config, **re-keyed**, or signed. For every FK, name the table it points into — and the table
   GBO's column points into. Different tables → re-keyed → never copied.
9. **Identity columns are literals** from the Q-G7 derivation, **one per destination object**, each with
   its source comment. Never `SELECT … INTO` from a table, never `&&`. Standalone objects have their
   **own** owner: `T_BOX_ENGFCURVE_S`/`T_BOX_ENGLKFC_X` → FixingCurve, `T_BOX_ERRORS_FE_S` → Limit Error
   Assign, `T_BOX_ENGDAYS_MATURED_S` → Days Matured. Run 4 wrote the Config owner on Days Matured.
10b. **A cursor's fields are the names its `SELECT` gives them.** `FOR r IN (SELECT 20.4 AS FK_INSTRUMENT
    …)` is read as `r.FK_INSTRUMENT`, never `r.instrument` — run 4's step 7 would not have compiled.
10. **Steps 2–4: allocate the curve's PK before the header.** `FK_CURVEMAN`/`FK_CURVEACC` are `NOT NULL`, so
    the earlier "NULL, then UPDATE" fails with ORA-01400. Allocate both PKs, insert the header pointing at
    `v_curve_pk`, then the curve, then its array. No UPDATE.
11. **Pre-commits:** `P_ENGFixingCurve_PreCommit(v_curve_pk)` after step 4 — no DML.
    **`p_check_Val_Curves_precommit(v_conf_pk)` last** — it writes and **COMMITs**, so nothing may follow
    it and the rollback file is the undo. With no step-8 rows it should find nothing to do.
12. **Every instrument-keyed step is filtered to `APPROVED_INSTRUMENTS`** — 6, 7, 8, 11, 12, 14a. Report
    what you filtered out.
13. **Open every step with the template's full header block** — What · Source · Findings row + status ·
    Depends on · **If wrong** (a consequence, not "stop and reconcile"). Run 4 cut them to one line, so a
    reviewer could no longer trace a value to its query.
13b. **Build the verify script from `templates/verify.sql.tmpl`, V1–V10, unchanged in substance.** V1 reads
    `gom_glb_sys.t__CORE_INFO_S` and checks **every** created row; V4 and V10 compare with `DEVENG` using
    `MINUS` both ways; V9 checks identity per table. A check that cannot fail (`WHERE 1=0`, `0.44 <>
    0.44`) is not a check — run 4's first verify query was one.
14. **Guards before inserting** where the rollback keys by branch or instrument — steps 11, 12, 14a abort
    if rows already exist (template). The rollback then deletes only this run's rows, and **keeps 14a's**.
15. **`DESCRIPTION` is globally unique** on the header and the curve — pre-check; never adjust a mined
    value to dodge a collision.

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
| 5 | Step 14a — `NUM_DAYS` per missing instrument, and `DDATE = SYSDATE` | product SME | Q-12 (b) |
| 6 | Steps 9 / 10 — **only if** new evidence reopens Question G (e.g. NY's currency-basis rows); otherwise they stay `CONFIRMED_ABSENT` | BOX FE team | Q-08, Q-09 |

**If `SME_IN_SESSION` is `none`:** put no cards; steps 6, 11, 12, 14a → `SME_DECISION_REQUIRED`, and the
cards go into `00-gate-0c-signoff-request.md` for signature.

**Either way:** steps 7 and 8 are **mined**, with rows attached. Steps 4b, 9, 10 → `CONFIRMED_ABSENT`
(Question G, closed 2026-09-22) unless card 6 reopened them. Step 13 → verify only. Step 14b →
`NOT_BRANCH_SCOPED`.

---

## What to produce

`RUN_FOLDER/`: `00-inputs.md` (first), **`00-decisions.md`** (one row per card answered), `01-evidence/` one CSV per query, `02-findings.md` one statused row
per walk step **including 14a and 14b**, `03-sql/` **the three files**, `05-source-questions.md`,
`99-open-items.md` naming who each item waits on, and the gate 0c pack.

**Open questions to carry into `05-source-questions.md`** — for the BOX FE team, not to reason about:
what `DDATE` means on Days Matured; any quote reference in Q-04c that does not resolve.

## ⛔ The validator is a gate — iterate until it is clean

1. `python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/`
2. Fix every FAIL. Run again. Repeat until **0 FAIL**.
3. **Paste the final output as the last thing you produce.**

If a check looks wrong, **say so and leave it failing** — never reshape the SQL to slip past it.

## What a passing run looks like

- ✅ Preflight first and quoted; every release gate cites an evidence file; `TARGET_AUTH_CODE` recorded.
- ✅ Three SQL files. The config asserts the auth code; verify has V1–V10 with expected results, none of
  them unable to fail.
- ✅ Step 2: `586.4` / `513.4`. Step 4: the generated `FK_BS` list. Step 7: only NY's rows,
  `FK_BRANCH = 20007.4`, dropped rows listed, cursor fields matching the aliases. Step 11: 12 rows
  incl. a **real** dummy label, or honestly held.
- ✅ Every decision was put as a card and is in `00-decisions.md` with a name and role.
  Step 12: SLB's limits proposed, identity from the derivation. Step 14a: missing instruments only.
- ✅ Every closed decision names a person with authority for it; every open one says who it waits on.
- ✅ Validator **0 FAIL**, pasted.
- ❌ Any invented value, typed quote list, GBO `FK_BRANCH` or source system in a BOX row, `LIMIT_ERRORS = 0`
  proposed, or step emitted on a guessed scope — **fail**, however good the rest looks.

**If something is unclear, ask a source question or record an open item. Do not reason your way to an
answer** — six of the expert's seven points were rules this repo did not have, and no amount of
reasoning over the data would have produced them.
