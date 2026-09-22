# Devin kickoff — NY_SCH, Tier 2 PRE, full run

**The first end-to-end execution of this agent.** Supersedes `tier2-gate-verification.md`, which was
split out only while access was pending.

**What "full" means here.** The agent runs the whole walk and mines every step. How much SQL comes out
depends on **`SME_IN_SESSION`**: with an authorised SME present, gate 0c can close in the session and
steps 6, 7, 8, 11 and 12 are emitted too; without one, the run emits **steps 1–5**, mines the rest, and
holds them at `SME_DECISION_REQUIRED`. **A run that stops there with its gaps reported passes.** See *What a passing run looks like* at the end
before you judge the output.

---

## Before you paste: setting up the session

| | |
|---|---|
| **Repos** | this automation repo (**read/write**). ✅ **`cib-boxfin-dbboxfe` is NOT needed for this run** — the one thing it was wanted for, `P_ENGFixingCurve_PreCommit`'s body, was already read on 2026-09-21 and is recorded in the charter and this run folder. Attach it only if the agent raises a source question mid-run and asks for it |
| ⚠️ **Database** | **Devin gets no connection.** You hold the read-only accounts and run every query yourself — `DB_ACCESS_MODE = assisted`. Devin states the SQL and the output filename; you return the CSV |
| **Which database** | **Tier 2 PRE** (`DEVENG` + `BOX_FE`) for everything, except **four Tier 1** SLB reference reads in phase 3 |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or local edit on `cib-boxfin-dbboxfe`, ever. A defect there is a finding, not a fix |
| **Expected** | ~25 queries in **four batches**, so four rounds of back-and-forth, not twenty-five |
| ⛔ **Before you start** | **Archive the previous run.** `RUN_FOLDER` is a fixed path, so this run overwrites `02-findings.md`, `01-evidence/`, `03-sql/` and `99-open-items.md`. See `runs/README.md` |

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
| `DB_ACCESS_MODE` | ⚠️ **`assisted`. You have NO database connection.** Edouard holds the read-only Tier 2 account and runs every query. You state the query, he returns the CSV. **Never attempt to connect to Oracle** |
| `SOURCE_ACCESS_MODE` | `direct`, **read-only** — the repos you *can* read yourself |
| `RUN_FOLDER` | `runs/NY_SCH/tier2-pre/` — the existing folder. This is the real run |
| `PRODUCT_BOOK_SCOPE` | **Partial.** Instruments confirmed (six, below); the rest of gate 0c is open |
| `SME_IN_SESSION` | **Fill this in before you paste.** The name and role of whoever is in the session and may decide product scope, accrual values, error limits and book scope — or `none`. It decides whether gate 0c closes here or waits |

### ⛔ How you get data: you ask, a human runs it

**There is no Oracle connection in this session and there will not be one.** Do not probe for one, do
not install a driver, do not wait on one. `DB_ACCESS_MODE = assisted`, per the charter's *Evidence*
section, and the contract there binds you:

1. State the **query ID**, its purpose, **which database** (Tier 2, or Tier 1 for the three SLB
   reference reads), and the parameter values already resolved.
2. Give the **SQL ready to run**, placeholders substituted where their values are known.
3. State the **exact output path and filename** — `01-evidence/Q-05-accrual-gbo.csv` — and the row
   count you expect.
4. **Stop and wait.** Do not proceed on an assumed result.
5. On receiving the CSV, **check it matches the expected shape** before using it. A CSV that doesn't is
   a re-run request, not data to interpret creatively.

**Ask in dependency batches — four rounds, not twenty-five requests.** A human is running these by
hand, and batching wrongly is the main way this run wastes his afternoon:

| Batch | Contents | Why it is its own round |
|---|---|---|
| **1** | The preflight, **alone** | Everything else is meaningless until it returns non-zero |
| **2** | The five release gates | Independent of each other; any failure stops the run, so asking for mining queries now risks wasting them |
| **3** | Steps 1–5 mining **+ all C2 reads** | The bulk of the run. Only ask once every gate has passed |
| **4** | The four **Tier 1** SLB reference queries | Different database — keep them together so he connects once |

You **can** run `python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/` yourself — that is a
script in the repo you have, not a database query. Run it before you finish.

### Two things the environment now settles for you

1. **Source and target are the same environment.** Gate 0f does not arise, and no mined value has a
   portability question. `[stated: Edouard, 2026-09-22]`
2. **This is no longer a deferred-verification run.** That shape existed only because `BOX_FE` could
   not be read. Run the C2 reads normally (phase 2) and **remove the draft headers** from anything the
   run folder already carries, noting that you did.

**The accounts running your queries are read-only**, so hard rule *"never writes to a database"* is
enforced by the environment as well as by this charter. That is a backstop, not a licence: every
statement you produce goes to a file for a human to review and run later. **Never ask for a query that
writes**, and never present your SQL as something to execute now.

---

## Phase 1 — Preflight and release gates. **Hard stop if any fails.**

### ⛔ Batch 1 — the preflight, asked alone

**Your first action in this session is to print this query and ask for its result.** Nothing else, and
no attempt to run it yourself.

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

### Batch 2 — the release gates, once the preflight comes back non-zero

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

## Phase 2 — Batch 3: mine and emit steps 1–5

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
- 📝 **Open every walk step with a header block** — see the charter's *Outputs*. What · Source · Findings
  row + status · Depends on · **If wrong**. One block per step, one for step 4's whole quote-reference
  set. The `If wrong` line is not decoration: someone debugging a failed load reads this file to decide
  where to look, and a step whose consequence you cannot state in one line is one you do not understand
  well enough to emit.
- **Step 5 is not optional.** If it cannot be emitted that is run-stopping, not a line item.
- ⛔ **Steps 2–4 are insert-then-update.** The header's `FK_CURVEMAN`/`FK_CURVEACC` point **at** the
  curve, so: insert the header with those columns **NULL**, insert the curve, insert its quote array,
  then **`UPDATE` the header** to set both to the curve's `F___SEQUENCE` variable. **Never a literal
  there** — a mined `FK_CURVEMAN` is the *GBO* curve's PK in `DEVENG.T_PGT_ENGFCURVE_S` and means
  nothing as a key into `BOX_FE.T_BOX_ENGFCURVE_S` (hard rule 13). Whether the two columns take the
  same curve or different ones is mined from the branch's own GBO header.
- ⛔ **`FK_OWNER_OBJ` / `FK_EXTENSION` are the Q-G6 constants**, emitted as literals. **Never
  `SELECT … WHERE ROWNUM = 1`** — that samples an arbitrary existing row, which is the `MIN(PK)`
  defect in a new costume.
- **For every FK you emit, name the table it points into and the schema that table is in.** If the
  answer is `DEVENG`, the value is wrong.
- ⛔ **Call `P_ENGFixingCurve_PreCommit` after steps 3–4.** Its body was read on 2026-09-21 and is
  recorded: **no DML**, it validates that if any currency has a yield curve, every currency in the
  quote reference has one. Safe as a plain gate, and the 2026-09-22 run omitted it entirely. You do
  **not** need the repo to confirm this — it is `[confirmed: source via Devin, 2026-09-21]`. **Do not call `p_check_Val_Curves_precommit`**: it
  writes to step 8's table and issues a `COMMIT`, and step 8 is out of scope this run (hard rules 10, 11).
- **Pre-check `DESCRIPTION` before emitting it.** `T_BOX_ENGCONF_S.DESCRIPTION` and
  `T_BOX_ENGFCURVE_S.DESCRIPTION` carry **global** unique indexes — not per-branch. A collision is a
  hard INSERT failure, and quietly adjusting the mined value to dodge one is a fabricated literal.

---

### Step 6, when gate 0c releases it — values come from NY's own GBO row

**Mine `DEVENG.T_PGT_ENGACCRCONF_S` for NY** (`WHERE FK_PARENT = <NY's GBO MIS header>`), and show
SLB's values **alongside** in the findings, never instead. Where they agree the SME confirms; where
they differ, **the difference is the finding.** They do differ — SLB has `INTERVAL = 370` for Forward
Rate Agreement against NY's `377`. Proposing SLB's values when NY's own row exists is hard rule 6.

## Phase 3 — Status what you could not write, and prepare the sign-off

**Run batch 4 first.** The Tier 1 reference reads inform every decision below — in particular
**Q-05d**, without which nobody can answer the accrual question, whoever is in the room.

### Batch 4 — the four Tier 1 queries, SLB reference only

**Ask for these as one batch** so the human connects to Tier 1 once. Label every row with the
environment it came from.

| # | Query | For |
|---|---|---|
| 1 | **Q-13** — SLB's `LIMIT_ERRORS` per instrument | Step 12's proposal, [ADR 0004](../../../docs/decisions/0004-step12-limits-from-reference-branch.md) |
| 2 | The four accrual values on SLB's configuration | Question 2 of the sign-off pack — confirms the `FK_FEEFIRSTDAYSEL` ↔ `FeeCalcInterval` mapping and gives the SME real values to react to |
| 3 | Q-05c against SLB, `LEFT JOIN` form | Cross-check the instrument identities |
| 4 | **Q-05d** — SLB's **GBO** row against SLB's **BOX** row, both Tier 1 | ⛔ **Settles whether GBO→BOX transforms accrual values.** Until it runs, no step-6 value may be `PROPOSED` — see the charter's step-6 note. You need SLB's GBO MIS header PK (Q-G2 level 1 against Tier 1); its BOX side is `FK_PARENT = 333105.21` |

⛔ **Nothing read from Tier 1 may enter the SQL as a mined value.** These are **proposal aids only**
(hard rule 6). A Tier 1 `LIMIT_ERRORS` becomes a **`PROPOSED`** number awaiting sign-off; a Tier 1 FK is
never INSERTed anywhere. Say "Tier 1" beside every one of these values in the findings table.

**Then fill in `00-gate-0c-signoff-request.md`** — its Question 2 table and its Question 3a limits
table — so it becomes a document an SME can sign rather than a form asking them to invent numbers.



### If `SME_IN_SESSION` names an authorised person — put the decisions to them

**This is the intended path, not a shortcut.** Take them **one at a time**, and for each state: what is
being decided · which walk steps it releases · your proposal **with the evidence behind it** · what goes
wrong if it is wrong. Then wait.

On an answer: record `[stated: <full name>, <role>, 2026-09-22]` — **never `[stated: user]`** — close
gate 0c, and **emit the SQL for steps 6, 7, 8, 11 and 12** in this run. The decisions, in order:

1. **The four accrual values per instrument** (6 instruments × 4 = 24). ⚠️ **Q-05d must have run
   first** — it settles whether GBO→BOX transforms these columns, which is a *fact*, not a decision.
   Nobody can answer question 1 before it. If Q-05d has not run, hold step 6 regardless of who is present.
2. **`LIMIT_ERRORS` per instrument** — propose SLB's per ADR 0004; CDS has no SLB row, so it needs its
   own answer.
3. **The book list** — and say plainly that **no query can verify it is complete**; there is no
   BOOK↔FOLDER mapping. This one rests entirely on their judgement, and they should know that.

**If they decline, defer, or are not authorised for one of the three**, that decision alone stays
`SME_DECISION_REQUIRED` — the others still close. Partial closure is normal; record which is which.

### If `SME_IN_SESSION` is `none`

**Steps 6, 11, 12** → `SME_DECISION_REQUIRED`, blocked on gate 0c. **No SQL.**
**Steps 4b, 9, 10** → `EVIDENCE_REQUIRED`, parked. **Step 13** → `CONFIRMED_PRESENT`, verify only.
**Step 14** → **`NOT_BRANCH_SCOPED`** — that status exists for exactly this; do not use
`CONFIRMED_PRESENT` for it.

⚠️ **Steps 7 and 8 must be mined, not skipped.** The 2026-09-22 run blocked both and was wrong on each:

- **Step 7** was blocked on unresolved `FK_BRANCH` semantics. **Mine it anyway** —
  `WHERE FK_PARENT = <the GBO config PK>` returns the rows regardless; the semantics are a verification
  item on the *values*. *Cannot mine* and *mined, needs sign-off* are different statuses, and a blocker
  with no rows behind it gives the reviewer nothing to disagree with.
- **Step 8** was recorded `CONFIRMED_ABSENT` because the table is empty **in Tier 1**. That is a
  cross-environment inference about NY, and `Q-07` never ran. **Mine NY's own
  `DEVENG.T_PGT_FIXING_BY_INSTR_S`.** Absent on the BOX side is the precondition for writing, never the
  reason to skip.

Both may still end `SME_DECISION_REQUIRED` once mined — but with rows attached.

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


---

## What to produce

`RUN_FOLDER/` per the charter's *Outputs*: `00-inputs.md` (written first), `01-evidence/` one CSV per
query, `02-findings.md` one statused row per walk step citing its evidence, `03-sql/` (steps 1–5, plus 6, 7,
8, 11, 12 **only if** gate 0c closed in-session), `05-source-questions.md`, `99-open-items.md`, and the filled-in gate 0c pack.

**Run `python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/` and paste the output.** A run with
FAILs is not finished, whatever your write-up says.

## What a passing run looks like

Judge it against this, not against "did it produce a complete configuration":

- ✅ The preflight ran first and is quoted.
- ✅ Every release gate has a result citing an evidence file.
- ✅ Steps 1–5 have SQL; every PK is an `F___SEQUENCE` call; every INSERT has an explicit column list.
- ✅ Steps 6, 11, 12 are **either** `SME_DECISION_REQUIRED` with no SQL (`SME_IN_SESSION = none`), **or**
  closed with `[stated: <full name>, <role>, <date>]` and their SQL emitted. **Never `[stated: user]`,
  and never closed on a question that was not put.**
- ✅ Steps 7 and 8 were **mined** (rows attached) even though they emit no SQL. A blocker with no rows
  behind it is a fail.
- ✅ Gate 0c is **still open**. Marking it closed on an in-session answer is a fail.
- ✅ The validator reports **0 FAIL**.
- ✅ Open items name who each is blocked on.
- ❌ Any invented value, literal PK, DDL, or step-6 row emitted on a guessed scope — **fail**, however
  good the rest looks.

**If something is unclear, ask a source question or record an open item. Do not reason your way to an
answer** — the 2026-09-21 source round overturned two rules that had been reasoned into place, and
reasoning was the failure mode.
