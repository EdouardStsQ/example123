# Devin kickoff — NY_SCH, Tier 2 PRE, full run

**The first end-to-end execution of this agent.** Supersedes `tier2-gate-verification.md`, which was
split out only while access was pending.

**What "full" means here.** The agent runs the whole walk. **Gate 0c is open**, so steps 6, 7, 8, 11
and 12 cannot be written — the run mines and emits **steps 1–5** and statuses the rest honestly. A run
that stops there with its gaps reported **passes**. See *What a passing run looks like* at the end
before you judge the output.

---

## Before you paste: setting up the session

| | |
|---|---|
| **Repos** | this automation repo (**read/write**) · `cib-boxfin-dbboxfe` (**read-only**) |
| **Primary DB** | **Tier 2 PRE**, read-only — `DEVENG` **and** `BOX_FE` |
| **Secondary DB** | **Tier 1**, read-only — **SLB reference reads only.** Three queries, listed in phase 3 |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or local edit on `cib-boxfin-dbboxfe`, ever. A defect there is a finding, not a fix |
| **Expected** | one long session, ~25 queries |

---

You are running as this repo's `sigom-box-fe-configs-agent`
(`agents/sigom-box-fe-configs-agent/AGENT.md`). **Read that charter in full before anything else**, then
`docs/process/03-fe-sigom-config-procedure.md` and
`docs/reference/queries/fe-config-mining.md`. Every hard rule binds you without exception.

## Run inputs

| Input | Value |
|---|---|
| `RUN_MODE` | `normal` |
| `BRANCH_CODE` | `NY_SCH` |
| `TARGET_ENV` | **Tier 2 PRE** |
| `GBO_SOURCE` | **Tier 2** — same environment as the target |
| `DB_ACCESS_MODE` | `direct`, **read-only** |
| `SOURCE_ACCESS_MODE` | `direct`, **read-only** |
| `RUN_FOLDER` | `runs/NY_SCH/tier2-pre/` — the existing folder. This is the real run |
| `PRODUCT_BOOK_SCOPE` | **Partial.** Instruments confirmed (six, below); the rest of gate 0c is open |

### Two things the environment now settles for you

1. **Source and target are the same environment.** Gate 0f does not arise, and no mined value has a
   portability question. `[stated: Edouard, 2026-09-22]`
2. **This is no longer a deferred-verification run.** That shape existed only because `BOX_FE` could
   not be read. Run the C2 reads normally (phase 2) and **remove the draft headers** from anything the
   run folder already carries, noting that you did.

Your account is read-only, so hard rule *"never writes to a database"* is enforced by the environment.
That is a backstop, not a licence: still emit SQL to a file, never attempt execution.

---

## Phase 1 — Preflight and release gates. **Hard stop if any fails.**

### ⛔ Query 1, before every other query

```sql
SELECT USER,
       SYS_CONTEXT('USERENV','DB_NAME')                        AS db,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER='BOX_FE')  AS boxfe_visible,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER='DEVENG')  AS deveng_visible
FROM   DUAL;
```

**On 2026-09-16 this project reported Tier 2 PRE as missing many `BOX_FE` tables. That was wrong** — an
account with no grants measuring *visibility*, not existence. It was withdrawn. **`BOXFE_VISIBLE = 0`
means blind, not empty**, and is an **access escalation**: stop, report, produce no schema diff and no
DDL. Write it to `01-evidence/Q-G4-preflight.csv` and quote it at the top of your report. A result set
whose preflight was not run is not evidence (hard rule 8).

### Then the release gates, in order

| Gate | Query | Failure means |
|---|---|---|
| 0e | **Q-G4** | Provisioning artifact in `04-provisioning/` with DDL **sourced and cited** from `cib-boxfin-dbboxfe`, then **block**. Never author DDL |
| 0d | **Q-G3b** | `F___SEQUENCE` not callable by this account → **stop**; every INSERT depends on it |
| 0a | **Q-G1** | Re-confirm `BRANCH_PK` in this session. A mismatch against `20007.4` is a **stop** |
| 0b | **Q-G2 level 1** | Re-confirm `FK_MISCONFIG` → the GBO MIS header. **Stop** if unresolved |
| 0g | **Q-G7** + **Q-G6** | Metamodel read against Tier 2's `GOM_GLB_SYS`, and identity constants from the **Tier 2** target tables |

⚠️ **Q-G6: do not reuse Tier 1's identity constants.** `35000126.65` / `35001566.65` were resolved in
Tier 1 and are the *destination's* own identity. Read them from Tier 2. **Expect exactly one row per
table** — more than one means the constant model is wrong for that table and is a **stop**, not a value
to choose between. They are **not one constant across the walk**: it spans three screens. Derive per
object, never hard-code.

**Report the gate results before continuing.** If every release gate passes, proceed to phase 2 in the
same session.

---

## Phase 2 — Mine and emit steps 1–5

Gate 0c is a **scope gate**: it blocks only its dependent steps. Steps 1–5 do not consume instrument
scope and proceed normally.

| Step | What | Query |
|---|---|---|
| 1 | Does an FE configuration already cover NY_SCH? **A read, not a write** | Q-01 |
| 2 | MIS Generic header | Q-02 |
| 3 | Fixing Curve header | Q-03 |
| 4 | Curve → quote-reference array | Q-04 |
| 5 | **Branch association row** — ties the configuration to the branch | Q-01c |

**Run the C2 read for every step**, including 6–14, even where the step is blocked: *does a BOX-side row
already exist?* **Finding nothing is the precondition for this job, not a problem** — and you may now
write `CONFIRMED_ABSENT`, because the preflight proves a row could have been seen.

If step 1 finds an existing configuration covering the branch, **stop and report**: the run forks from
"build new" to "adapt existing", which is a human decision.

**Emitting the SQL — the rules that have bitten this project before:**

- **Every PK is `F___SEQUENCE('<TABLE>','X')`** assigned to a declared variable; children reference
  their parent's variable. **No literal PK, ever.**
- **Explicit column list on every INSERT.** For each column say whether it is **mined** (name the GBO
  row), **allocated**, or **structural**. A column you cannot classify is a finding, not a column to
  copy. `INSERT … SELECT … FROM DEVENG` is forbidden — it silently carries identity columns across.
- **`FK_OWNER_OBJ` / `FK_EXTENSION` come from Q-G6 against Tier 2**, never from the GBO row.
- **Filter `_X` bridges on `FK_PARENT`, join on `FK_BS`** — never the reverse.
- **Pre-commit procedures: classify before calling.** `P_ENGFixingCurve_PreCommit` does no DML and is a
  safe gate. **`p_check_Val_Curves_precommit` writes to step 8's table and `COMMIT`s** — it must not sit
  in a block you describe as reversible. The rollback `DELETE`s are the undo; the trailing `ROLLBACK`
  is not.
- **`DESCRIPTION` is globally unique** on `T_BOX_ENGCONF_S` and `T_BOX_ENGFCURVE_S`. Check before
  emitting; a collision is a hard failure and quietly altering the mined value is a fabricated literal.
- **Step 5 is not optional.** If it cannot be emitted that is run-stopping, not a line item.

---

## Phase 3 — Status what you could not write, and prepare the sign-off

**Steps 6, 7, 8, 11, 12** → `SME_DECISION_REQUIRED`, blocked on gate 0c. **No SQL for any of them.**
**Steps 4b, 9, 10** → `EVIDENCE_REQUIRED`, parked. **Steps 13, 14** → verify only, never INSERT.

⛔ **Do not treat gate 0c as closed because the instruments are known.** It also needs the four
`NOT NULL` accrual values per instrument, the error limit, and the book list.

**Confirmed instruments** `[stated: <SME_NAME>, via Edouard, 2026-09-21]` — **six**: Swap, Deposit &
Loan, Cross Currency Swap, OTC Option, Caps And Floors, CDS (Credit Derivatives). Six of SLB's nine;
**do not reinstate the "same set as SLB" assumption.**

✅ **All six instruments exist in `PGT_SYS.T_PGT_SUB_PRODUCT_S`. Expect six rows to resolve.**
`[confirmed: DB via Edouard, 2026-09-22]` **Credit Derivatives is PK `20313.4`, CODE `Credit`** —
`FK_OWNER_OBJ 1451.4`, `FK_EXTENSION 10507.4`, `FK_PARENT 20326.4`. The table holds 50 rows.

> **Correction — an earlier instruction here was wrong.** This prompt previously said CDS had no
> Sub-Product row and that at most five of six could resolve. **Both are withdrawn.** The 2026-09-18
> evidence was an `INNER JOIN` from `T_BOX_ENGACCRCONF_S` that dropped two of SLB's nine rows; that
> shows **the join did not match**, not that the instrument is absent. The absence was inferred and
> wrongly tagged `[confirmed]`. See [`confirmed-joins.md`](../../../docs/reference/confirmed-joins.md).

⚠️ **The real open question, and it is cheap to settle in this session.** Why did that join drop SLB's
Credit Derivatives row? Read SLB's accrual row for it and **compare its `FK_INSTRUMENT` against
`20313.4`**. Three candidates, and the answer changes what step 6 writes:

1. The accrual row's `FK_INSTRUMENT` holds a value other than `20313.4` — then *what* does it hold?
2. The join was written on the wrong column.
3. `FK_INSTRUMENT` genuinely points into a different key space for some instruments — the only one of
   the three that is a data-model finding, and the only one that would block anything.

Report which. Use Q-05c's **`LEFT JOIN`** form plus the unjoined `COUNT(*)` regardless — a row that
cannot be labelled is a finding, never a row to drop.

⚠️ **And test one hypothesis, without assuming it.** The rejected 2026-09-18 draft listed an instrument
PK of **`20314.4`** — one away from Credit Derivatives' actual `20313.4`. If the draft mis-keyed it by
one, that is an independent defect of the fabricated-literal class. Check; do not conclude.

### The three Tier 1 queries — SLB reference only

Run these against **Tier 1**, and label every row with the environment it came from.

| # | Query | For |
|---|---|---|
| 1 | **Q-13** — SLB's `LIMIT_ERRORS` per instrument | Step 12's proposal, [ADR 0004](../../../docs/decisions/0004-step12-limits-from-reference-branch.md) |
| 2 | The four accrual values on SLB's configuration | Question 2 of the sign-off pack — confirms the `FK_FEEFIRSTDAYSEL` ↔ `FeeCalcInterval` mapping and gives the SME real values to react to |
| 3 | Q-05c against SLB, `LEFT JOIN` form | Cross-check the instrument identities |

⛔ **Nothing read from Tier 1 may enter the SQL as a mined value.** These are **proposal aids only**
(hard rule 6). A Tier 1 `LIMIT_ERRORS` becomes a **`PROPOSED`** number awaiting sign-off; a Tier 1 FK is
never INSERTed anywhere. Say "Tier 1" beside every one of these values in the findings table.

**Then fill in `00-gate-0c-signoff-request.md`** — its Question 2 table and its Question 3a limits
table — so it becomes a document an SME can sign rather than a form asking them to invent numbers.

---

## What to produce

`RUN_FOLDER/` per the charter's *Outputs*: `00-inputs.md` (written first), `01-evidence/` one CSV per
query, `02-findings.md` one statused row per walk step citing its evidence, `03-sql/` for steps 1–5
only, `05-source-questions.md`, `99-open-items.md`, and the filled-in gate 0c pack.

**Run `python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/` and paste the output.** A run with
FAILs is not finished, whatever your write-up says.

## What a passing run looks like

Judge it against this, not against "did it produce a complete configuration":

- ✅ The preflight ran first and is quoted.
- ✅ Every release gate has a result citing an evidence file.
- ✅ Steps 1–5 have SQL; every PK is an `F___SEQUENCE` call; every INSERT has an explicit column list.
- ✅ Steps 6–8, 11, 12 are `SME_DECISION_REQUIRED` with **no SQL** — stopping here is correct behaviour.
- ✅ The validator reports **0 FAIL**.
- ✅ Open items name who each is blocked on.
- ❌ Any invented value, literal PK, DDL, or step-6 row emitted on a guessed scope — **fail**, however
  good the rest looks.

**If something is unclear, ask a source question or record an open item. Do not reason your way to an
answer** — the 2026-09-21 source round overturned two rules that had been reasoned into place, and
reasoning was the failure mode.
