# 0005 — BOX FE expert review of run 3: seven rules adopted

**Status:** adopted 2026-09-23 · one point (3) partly open pending Q-04c
**Context:** `sigom-box-fe-configs-agent`, run 3's `NY_SCH-tier2-pre-steps-1-to-11.sql`, reviewed with a
BOX FE expert using the reviewer's guide. Seven points came back, plus some of the BOX FE team's own
product-onboarding inserts, sent **as reference, not as a template** `[stated: Edouard, 2026-09-23]`.

**No objection was raised to the walk order**, to steps 2–4 being insert-then-update, or to where the
two pre-commit procedures sit. (Insert-then-update turned out to be wrong anyway — see *Found by checking
these changes*.)

## The seven points and what each changed

| # | The expert said | Was the repo wrong? | Adopted as | Enforced by |
|---|---|---|---|---|
| 1 | *"In the PK generation, are you adding the auth code? … extremely important. If not, add it and make sure it's part of the verification script."* | **No — but invisibly right.** `F___SEQUENCE(…,'X')` adds it (Q-G3's function body). Nothing in the file showed or checked it, and there was no verification script | Q-G3c records the target's auth code; the config script asserts it before the first INSERT and on every PK; verify V1 checks every row created | `auth-code-not-asserted`, `pk-not-checked`, `auth-code-mismatch`, `verify-no-auth-check` |
| 2 | `FK_SOURCE_BACK` is always `586.4` (BOX is always the back source); `FK_SOURCE_FRONT` depends on the Murex instance — NY uses Murex 3 Latam `513.4` | **Yes.** Both were copied from GBO (`9.4`/`11.4`) | Step 2 mines three columns, not seven; `SOURCE_FRONT` is an input; Q-02c | `source-column-wrong` |
| 3 | Don't list the quote references in the file — pick them with `SELECT DISTINCT PK FROM DEVENG.T_PGT_ENGLKFC_X WHERE FK_PARENT = 1.35` — *"not sure the values … were correct"* | **Yes on listing them.** **Open on the column** — the expert's query copies `PK`, the repo's confirmed join copies `FK_BS` | Step 4 reads the set in-script with a count guard; verify V4 compares both ways; **Q-04c decides the column and blocks step 4 until it runs** | `quote-refs-typed`, `runtime-set-no-guard` |
| 4 | One GBO MIS configuration (`64408.35`) carries accrual exceptions for more than one branch; the expert's query identifies NY's | **Yes.** GBO's `FK_BRANCH` there is a branch *config*; run 3 copied `141.35` into BOX, which wants the branch | Step 7 filters through `T_PGT_BRANCH_CONFIG_S` to the branch, keeps approved instruments, writes `BRANCH_PK`, copies `CRITERIAL` | `branch-fk-copied`, `branch-fk-not-branch` |
| 5 | `T_BOX_CONF_BY_BOOK_S` needs two rows per instrument: each book, plus the dummy book (Tier 1 label `26391.4`) | **Yes** — the dummy row was unknown | Step 11 is `(books + 1) × instruments`; Q-10c verifies the label in the target | `conf-by-book-no-dummy` |
| 6 | Days Matured: check the instruments the branch needs; add missing ones configured like the reference branch | **Yes** — step 14 said "global, nothing to do" | Step **14a**: insert per missing instrument, `NUM_DAYS` from Tier 1, `PROPOSED` | findings row 14a; `instrument-out-of-scope` covers it |
| 7 | Nothing to configure in `T_BOX_ENGSETUP_S` | No — confirms the repo | Step **14b**, `NOT_BRANCH_SCOPED` | `insert-for-no-insert-step` |

**Two more defects surfaced by the review, not raised as points:** step 12 was left unwritten because
`T_BOX_ERRORS_FE_S` is empty in Tier 2 — the identity comes from the metamodel derivation, which needs
no row; and run 3's `LIMIT_ERRORS = 0` ×6 (NY's GBO values, a test decision) is the value step 12 exists
to prevent. ADR 0004 stands.

## Found by checking these changes — not raised by the expert

An independent review of this change set, run before release, found three things the expert did not
raise and this repo had wrong:

1. **Steps 2–4's insert-then-update fails on its first INSERT.** `FK_CURVEMAN`/`FK_CURVEACC` are
   `NOT NULL` `[confirmed: DDL]`, so inserting the header with NULL curves raises ORA-01400. Run 3 was
   written that way and never applied, so nobody saw it. **Replaced by allocate-first:** allocate the
   curve's PK before the header, insert the header pointing at it, then the curve. No UPDATE. Safe
   because there are no FK constraints (hard rule 12) and it is one block. New check `curve-fk-null`.
2. **The rollback could delete rows it did not create.** Steps 12 and 14a have no parent, so they are
   found by branch or by instrument. The config script now **aborts if such rows already exist**, and the
   rollback **keeps 14a's** Days Matured rows: the table is global and another branch may rely on them.
3. **The validator failed an honest partial run.** Any open SME decision anywhere failed the whole run,
   although steps 1–5 are legitimately emitted while gate 0c is open. It is now per step.

## A generalisation worth keeping: re-keyed columns

Points 2 and 4 are the same mistake. A column with the **same name in GBO and BOX pointing into
different tables** — `FK_BRANCH` (branch config vs branch), `FK_SOURCE_*` (GBO's sources vs BOX's) —
looks like a reference FK and is not. Hard rule 13 gains a fourth kind, **re-keyed**, and its test gains
a second half: name the table the *GBO* column points into, not just the BOX one.

## What the reference inserts were used for — and not

They confirmed row shapes (`T_BOX_ERRORS_FE_S` and `T_BOX_ENGDAYS_MATURED_S` have no `FK_PARENT` or
`FK_EXTENSION`), that `FK_BRANCH` holds the branch PK, and several Tier 1 identity constants — all as
cross-checks. **Not adopted:** one block per row, literal FKs, and `F___SEQUENCE(…,1) + 0.21` — a typed
auth code is right in one environment and silently wrong in the next.

## Alternatives considered

- **Adopt the expert's `SELECT DISTINCT PK` literally for step 4.** Rejected *for now*, not dismissed: it
  contradicts a join confirmed by a BOX lead and a convention seen on three tables, and if it is right
  then `_X` rows take no allocated PK — which changes hard rule 3. That is too large to adopt on one
  query without running it. Q-04c runs it, side by side with the alternative.
- **Switch to the team's explicit `+ <fraction>` form** to make the auth code visible. Rejected: the
  assertions give the same visibility without typing a value that differs per environment.

## Consequences

- `03-sql/` is three files, built from `agents/sigom-box-fe-configs-agent/templates/`.
- Sets mined from GBO (steps 4, 7) are read inside the script, so **the applying account must be able to
  read `DEVENG`**. If it cannot, the block fails to compile and nothing is inserted — safe, but a question
  for the BOX FE team before run 4's SQL is applied.
- Every point is a validator check with a regression test (`scripts/tests/`); prose alone did not hold
  in runs 1–3.
- Four new run inputs: `SOURCE_FRONT`, `DUMMY_BOOK_LABEL`, `TARGET_AUTH_CODE` (recorded), and
  `BRANCH_PK` written out for the checks.
