# Configuring a new branch in BOX FE — what the agent does, and what we still need from you

**For review by a BOX FE developer.** First case: **NY_SCH**. Rev. 9 — 2026-09-23.

We have built an agent that produces the **reviewed, runnable SQL** to configure a branch in BOX FE. It
does not write to any database: a human runs the SQL after sign-off.

> **Rev. 7 rewrites this document rather than amending it.** The previous revisions accumulated
> corrections until the summary contradicted itself in three places. This one is written from the
> current state, and the revision history now lives in `CHANGELOG.md` where it belongs.
>
> **Rev. 9 — your review of run 3 is in.** Seven points, all adopted, and the walk table below
> carries them: the header's two source columns are BOX's own (`586.4`, and the branch's Murex
> instance), step 7 keeps only this branch's exceptions and writes the branch itself, step 11 adds a
> dummy-book row per instrument, and step 14 is split — Days Matured gets a row for any approved
> instrument missing one. The one point still open is which column of `T_*_ENGLKFC_X` holds the quote
> reference, `PK` or `FK_BS`: a query now decides it before step 4 is written.
>
> **One change you did not ask for:** steps 2–4 no longer insert the header with NULL curves and update
> it afterwards. Both curve columns are `NOT NULL`, so that would have failed on the first INSERT. The
> curve's PK is now allocated first and the header inserted pointing at it.
> [ADR 0005](../decisions/0005-box-fe-expert-review-run-3.md).
>
> **The big change since rev. 6: we read your source code.** Eight questions to `cib-boxfin-dbboxfe`
> and `cib-boxacc-dbboxacc` answered things no query could, and **two of them overturned rules we had
> reasoned our way to.** Those are sections 4 and 5, and they are the parts most worth your attention.

---

## 1. The method, in one paragraph

A branch that is live in GBO already has its Financial Engine configuration there as real rows. The
agent **reads those rows and creates the equivalent rows in `BOX_FE`**, one configuration object at a
time, in FK-dependency order. Every value it emits is one of four things: **read** from a GBO row,
**given** by a named SME, a **documented constant**, or explicitly **derived** with its rule written
down. There is no fifth source, and "it looked like London's" is not one of them.

Finding nothing for the branch in `BOX_FE` is the **precondition** for the job, not a problem.

---

## 2. The walk — 15 configuration objects, in dependency order

| # | Object | Table | Source |
|---|---|---|---|
| 1 | FE configuration association — **read** | `T_BOX_ENGCONF_X` | — (the fork: reuse or build new) |
| 2 | MIS Generic header | `T_BOX_ENGCONF_S` | `DEVENG.T_PGT_ENGCONF_S` — except `FK_SOURCE_BACK = 586.4` and `FK_SOURCE_FRONT` = the branch's Murex instance |
| 3 | Fixing Curve header | `T_BOX_ENGFCURVE_S` | `DEVENG.T_PGT_ENGFCURVE_S` |
| 4 | Curve → quote-reference array | `T_BOX_ENGLKFC_X` | `DEVENG.T_PGT_ENGLKFC_X` — the list **generated from the query result and checked against it**, never typed |
| 4b | Curve → yield-curve collection | `T_BOX_ENGFIXDISC_S` | ✅ **not needed for NY — verify only** |
| 5 | Branch association — **write** | `T_BOX_ENGCONF_X` | branch PK |
| 6 | Accrual defaults *(and the instrument set)* | `T_BOX_ENGACCRCONF_S` | `DEVENG.T_PGT_ENGACCRCONF_S` |
| 7 | Accrual Exceptions | `T_BOX_CONFIG_ACCRUAL_S` | `DEVENG.T_PGT_CONFIG_ACCRUAL_S` — **this branch's rows only**, `FK_BRANCH` = the branch |
| 8 | Fixing Exceptions | `T_BOX_FIXING_BY_INSTR_S` | `DEVENG.T_PGT_FIXING_BY_INSTR_S` |
| 9 | Yield Curve | `T_BOX_ENGZCCONF_S` | ✅ **not needed for NY — verify only** |
| 10 | Currency Basis | `T_BOX_ENGCURRENCYBASIS_S` | ✅ **not needed for NY — verify only** |
| 11 | Book — batch partitioning | `T_BOX_CONF_BY_BOOK_S` | no GBO twin; SME + Data-Lake books, **plus a dummy-book row per instrument** |
| 12 | Allowed Errors | `T_BOX_ERRORS_FE_S` | **reference branch, proposed** — not GBO *(see §5)* |
| 13 | Derived — **verify, never insert** | `T_BOX_FIXING_ASSIGNMENT_S`, `T_BOX_BRPROCCAL_S` | — |
| 14a | Days Matured — **a row per approved instrument; insert only the missing ones** | `T_BOX_ENGDAYS_MATURED_S` | reference branch's environment, proposed |
| 14b | FE Parameters — **nothing to configure** | `T_BOX_ENGSETUP_S` | — |

**We no longer take this list on trust.** SIGOM declares its own objects and fields in `GOM_GLB_SYS`,
so the agent now reads the catalogue and **diffs it against the walk**. That is how step 4b was found —
a declared tab of the Fixing Curve screen with no step against it. It is also how we would find the
next one, mechanically, instead of by someone noticing.

---

## 3. Seven gates — no SQL is written until they pass

| Gate | What it checks | State for NY_SCH |
|---|---|---|
| 0a | Branch exists in GBO; `BRANCH_PK` resolved | ✅ `20007.4` |
| 0b | `FK_MISCONFIG` → the GBO MIS header | ✅ `64408.35` |
| **0c** | **Instrument scope + four accrual values + error limit + book scope, from a named SME in writing** | 🟡 **instruments answered 2026-09-21 — the rest still open.** See §5 |
| 0d | How primary keys are allocated | ✅ `F___SEQUENCE(<table>,'X')` |
| 0e | Target `BOX_FE` schema complete in the run environment | ✅ **read-only Tier 2 access granted 2026-09-22**; evaluated in-run |
| 0f | Cross-environment reference check | — not applicable (same-environment run) |
| **0g** | **The metamodel read** — declared objects, field targets, pre-commit procedures, and a completeness diff on the walk | ✅ passed 2026-09-21 |

Gate 0g is new and needs no `BOX_FE` access, which is why it could run while everything else waited.

---

## 4. ⛔ What your source code told us — and why it changed our design

Two findings we could not have reasoned our way to. **These are the parts we would most like you to
confirm we have read correctly.**

### 4a. `p_check_Val_Curves_precommit` writes to a different table, and commits

Passed the **step 2** header PK, it UPDATEs **step 8's** `T_BOX_FIXING_BY_INSTR_S WHERE fk_parent =
pk_in`, back-filling null `fk_fixingcurve_acc` / `fk_fixingcurve_man` from the header's defaults — and
issues an explicit **`COMMIT`** after each of its three conditional UPDATEs.

Two consequences, both of which changed what we generate:

- **A raw INSERT set that skips it produces a genuinely different end state.** So the walk has to
  account for it rather than hope.
- **Our script's trailing `ROLLBACK` is not a safety net.** A commit inside the procedure commits every
  INSERT outstanding. We had been describing the run as "execute, inspect, roll back". That was wrong.

**What we do now:** emit step 8's rows with their curve values already populated — filling any GBO null
from the header and labelling it `DERIVED` with your source cited — **and then call the procedure.**
With no nulls left its UPDATEs never fire, so it commits nothing, and **its finding nothing to do is
our evidence that the INSERT set matched what SIGOM would have produced.**

> **Question A — is that the right way to handle it?** Specifically: is calling the procedure directly
> from a script the sanctioned pattern, or does SIGOM do something else around it that we would be
> bypassing?

`P_ENGFixingCurve_PreCommit`, by contrast, does no DML — it validates that if any currency has a yield
curve, every currency in the quote reference has one. We call it as a plain gate.

### 4b. There are no foreign key constraints anywhere

Across all thirteen tables we checked: **no `FOREIGN KEY`, no `CHECK`, no `DEFAULT`.** Every `FK_*`
column is a plain `NUMBER`; referential integrity is entirely in the application layer.

We are not asking you to change that — it is clearly deliberate. We are flagging what it means for us:
**a wrong FK inserts cleanly and fails silently later, in a batch, far from the cause.** Nothing rejects
it. So the declared field catalogue in `GOM_GLB_SYS` is not a convenience for us, it is the only defence
there is, and we treat a join asserted without it as a defect.

> **Question B — is there anywhere else we should be validating against** that we have not found?

---

## 5. What we need from you

Ranked. The first is worth more than the rest combined.

### 🟡 Gate 0c — instruments confirmed, three answers still needed

> **✅ Instruments, 2026-09-21** `[stated: <SME_NAME>, via Edouard]` — NY_SCH gets **six**: Swap,
> Deposit & Loan, Cross Currency Swap, OTC Option, Caps And Floors, CDS (Credit Derivatives). That is
> **six of SLB's nine**; Cash Flow Matching, Forward Rate Agreement and Bond Return Swap are out.
> Our working assumption had been "the same set as SLB", and it was wrong — acting on it would have
> configured three instruments nobody asked for.
>
> ✅ **A correction we owe you.** We told you Credit Derivatives had no
> `PGT_SYS.T_PGT_SUB_PRODUCT_S` row and would block three walk steps. **That was wrong and is
> withdrawn** — it is `20313.4`, CODE `Credit`. Our evidence had been an `INNER JOIN` that failed to
> match, which shows the join did not match, not that the instrument is absent. **All six instruments
> resolve and nothing is blocked by this.**
>
> What remains is a smaller question: why that join missed. We compare SLB's accrual `FK_INSTRUMENT`
> against `20313.4` in the next run.

The gate is **not released**. It was never only "which instruments":
`T_BOX_ENGACCRCONF_S` has **four `NOT NULL` columns** — `FK_FEEFIRSTDAYSEL`, `FK_INTFIRSTDAYSEL`,
`INTCOMMONBASIS`, `BYTRIGGER` — which cannot be left blank pending a later decision. **Every instrument
needs all four**, so with six instruments confirmed that is **24 values**, plus the `LIMIT_ERRORS`
figure per instrument and the book list.

⚠️ **And we cannot yet state what they mean.** The metamodel declares the *screen* fields as
`FeeCalcInterval`, `InterestCalcInterval`, `InCommonBasis`; the DDL gives the physical column names
above. The mapping is plausible but unconfirmed — `FEEFIRSTDAYSEL` reads more like "fee first day
selection" than "fee calculation interval". **We will not ask an SME to sign values whose meaning we
cannot state**, so we have a query prepared to resolve them against a live branch first.

> **Question C — do those four physical columns correspond to the screen fields we think they do?**
> One sentence from you saves us a round trip.

There is a signable request prepared at `runs/NY_SCH/tier2-pre/00-gate-0c-signoff-request.md`.

### 🆕 Three questions from your review of run 3 *(2026-09-23)*

> **Question I — `T_*_ENGLKFC_X`: is the quote reference in `PK` or in `FK_BS`?** Your query selects
> `PK`; our confirmed join (`FK_BS = T_PGT_QUOTE_REFERENCE_S.PK`) says `FK_BS`. If it is `PK`, bridge
> rows take no sequence PK and we have a rule to change. We will run both side by side (Q-04c) — but if
> you know, it saves a round.
>
> **Question J — we assume the account that applies the script sees `BOX_FE` only.** So the script
> references nothing else: GBO's sets travel as literals generated from our query results, and every
> comparison with GBO (auth code, quote array, exceptions) is in a separate verification script we run on
> a read-only account. **If that assumption is wrong in either direction, tell us** — in particular, if
> `F___SEQUENCE` or `PKG_ENGPRECOMMIT` are not callable by that account.
>
> **Question K — Days Matured `DDATE` (`DateToProcess`).** Your insert writes `SYSDATE`. Is that the rule
> for a new instrument row, or should it be a specific date?

### Three questions the code could not answer

> **Question D — `PKG_MAD_*`.** Roughly forty of the 172 pre-commit packages carry that prefix, and most
> read as Spain/EU regulatory functions. **Does onboarding a branch in a new jurisdiction require its own
> pre-commit packages?** If yes, that is a development workstream nobody has scoped.
>
> **Question E — `num_counterror`.** Is it procedure-local or package-level? It decides whether step 12's
> `LIMIT_ERRORS` count resets per instrument or spans a whole load session — which changes what a value
> like "100" actually means.
>
> **Question F — `f_GetBookByLabel`.** Does one process label resolve to one book or several? The body is
> in `BOX_SYS`, which we could not read. If several, the process label sits above the trading book and
> our mental model of "the desk" is one level off.

### Two things we have parked, and would rather you decided

> ✅ **Question G — ANSWERED 2026-09-22.** `[stated: Edouard Sintes]` **NY does not need steps 9, 10
> or 4b.** `T_BOX_ENGZCCONF_S`, `T_BOX_ENGCURRENCYBASIS_S` and `T_BOX_ENGFIXDISC_S` are empty in
> Tier 1 PRE, nothing in either repo writes them, and Madrid and London run without them. They stay in
> the walk as verify-only steps — absence confirmed with evidence, never an INSERT.
>
> **Question H — Book scope.** A row in `T_BOX_CONF_BY_BOOK_S` per (branch, instrument, book) is what
> creates a processing queue, and a missing one means that work is **silently never scheduled**. There is
> no mapping in BOX between books and folders, so **we cannot verify that a book list is complete** —
> there is no query that proves it. We can derive the *observed* pairs from deal data on a live branch,
> which is a coverage check, not a guarantee. **Is there a better source we have missed?**

---

## 6. Two things worth knowing about how this runs

**A missing row is not a missing setting — it is silent non-processing.** We learned this from your
code and it changed how we rank the steps:

| Missing row | Consequence |
|---|---|
| Step 12 (`T_BOX_ERRORS_FE_S`) | `LIMIT_ERRORS` defaults to **`0`** — the first failed deal aborts the whole load for that instrument |
| Step 11 (`T_BOX_CONF_BY_BOOK_S`) | that (branch, instrument, book) is never queued. No error |
| Step 5 (`T_BOX_ENGCONF_X`) | the queue builder joins it, so **nothing is scheduled at all** |

**The output is checked by a script, not just by reading it.** `scripts/validate_run_output.py` runs
mechanical checks encoding every defect this project has produced — literal PKs, GBO columns copied into
BOX rows, missing walk steps, a committing procedure inside a block framed as reversible, INSERT
ordering. Against the draft we rejected in September it reports 17 failures. A run with failures is not
finished, whatever the write-up says.

---

## 7. What the agent will never do

It never invents a value: every one is read, SME-given, a documented constant, or explicitly `DERIVED`
with its rule attached — and a `DERIVED` value is never recorded as confirmed and needs its own
sign-off. It never fabricates a primary key: it calls `F___SEQUENCE` and lets the database allocate. It
never writes DDL — if a table is missing it locates the authoritative `CREATE` in `cib-boxfin-dbboxfe`
and cites the path. **It never commits, branches or raises a pull request against your repos**; it reads
them, and a defect it finds there is a finding it escalates, never a fix it proposes. It never copies
values from another branch because the shape matches — Madrid and London share calendar, currency and
both source systems yet use different curves, and NY is USD/New York unlike either. It never writes to a
database. And it treats a zero-row result as a question rather than an answer: several "absences" in
this project turned out to be a broken join, a missing grant or an inner join dropping rows.

---

*Corrections are the most useful thing you can give us — "that table is wrong", "that join is X not Y",
"you're missing Z". Every previous round of your feedback produced a missing walk step or closed a gate.
Corrections are recorded against the specific claim with attribution, never silently absorbed.*
