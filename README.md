# Run log — NY_SCH BOX FE config, Tier 2 PRE

Agent: `sigom-box-fe-configs-agent` · Kickoff: `agents/sigom-box-fe-configs-agent/prompts/kickoff-ny-sch.md`

**Status: ACTIVE — full run, no longer deferred.** `[stated: Edouard, 2026-09-22]` `BOX_FE` is now
readable in Tier 2 PRE on a **read-only** account, so the deferred-verification shape is **retired** —
it existed only because the target could not be read. This is the **real run against the real target**,
and the kickoff is
[`prompts/tier2-full-run.md`](../../../agents/sigom-box-fe-configs-agent/prompts/tier2-full-run.md).

> ## ▶ Next: run 4 — after the BOX FE expert's review of run 3 (2026-09-23)
>
> Seven points, all adopted — [ADR 0005](../../../docs/decisions/0005-box-fe-expert-review-run-3.md).
> The kickoff was rewritten for them. **Before pasting it:**
>
> | | Who |
> |---|---|
> | Archive run 3 to `archive/run-03/` — step 4's review compares against its SQL | operator |
> | Fill `SME_IN_SESSION` in the kickoff | operator |
> | Replace `<SME_NAME>` where the instrument scope is attributed | operator |
>
> **What run 4 will do differently:** three SQL files (config, verify, rollback); auth code asserted and
> verified; step 2 with `586.4` / `513.4`; step 4 read from `DEVENG` once **Q-04c** settles `PK` vs
> `FK_BS`; step 7 filtered to NY and written with `20007.4`; step 11 with the dummy book (12 rows);
> step 12 with SLB's limits and its identity from the metamodel; step 14a Days Matured for missing
> instruments.

**All queries run in Tier 2**, except three **SLB reference** reads that stay in Tier 1 (see *Shape*
below). Gate 0c remains the one thing limiting scope: steps 1–5 proceed, 6–8/11/12 wait on it.

> **Supersedes the split-tier rehearsal** (`../tier1-pre-rehearsal/`), which wrote to Tier 1 PRE. That
> approach is withdrawn: substituting the target made every mined FK a portability question, blocked
> step 4 on quote references that are local to Tier 2, and produced SQL that was never executable
> anywhere.

## Shape of this run

| | |
|---|---|
| `GBO_SOURCE` | **GBO Tier 2** — NY_SCH is live here |
| `TARGET_ENV` | **Tier 2 PRE** — the real target |
| Readable | ✅ **`DEVENG`, `PGT_*` and `BOX_FE`, all in Tier 2**, read-only `[stated: Edouard, 2026-09-22]` |
| Tier 1 | **SLB reference only** — three proposal-aid queries (Q-13 limits, SLB's four accrual values, Q-05c instrument identities). ⛔ **No Tier 1 value enters the SQL as mined**; each becomes `PROPOSED` and is labelled with its environment |
| Gate 0f | **Not applicable** — source and target are the same environment |

Because source and target share an environment, every mined FK is native. There is no cross-environment
portability question, and **`PGT_MRK` quote references resolve natively** — so step 4, which the earlier
rehearsal could not cover, is fully in scope.

## The working assumption

**`BOX_FE` in Tier 2 PRE has the same tables and columns as `BOX_FE` in Tier 1 PRE.** `[stated:
Edouard, 2026-09-18]` — an assumption, not a finding.

It has a validated structural reference: the 2026-09-18 Tier 1 PRE run confirmed **all 15 walk tables
plus `V_BOX_PROC_INSTR_S` present**, 80 `BOX_FE` objects visible to `BOX_ADMIN`. Use Tier 1's `BOX_FE`
**structure** — column names and types — where the shape of a target table is needed.

⚠️ **Structure, never values.** Reading Tier 1's column list is fine. Reading a Tier 1 *row* and
carrying it into NY's configuration is hard rule 6.

Discharged by one Q-G4 run against Tier 2 when access arrives.

## ~~What is deferred~~ — nothing, as of 2026-09-22

The deferred set was procedure step **C2** (*"does a row already exist on the BOX side?"*) and **gate
0e**. **Both are now runnable in Tier 2**, so:

- **Run the C2 reads normally.** A BOX-side status may now be `CONFIRMED_ABSENT` — the preflight is what
  earns that, by proving a row could have been seen.
- **Remove the draft header** (*"Draft — generated before BOX-side verification"*) from anything the
  folder already carries, and say in the report that you did. The SQL itself does not change.
- Gate 0e is evaluated against Tier 2 directly, which also discharges the structural assumption below.

## Gate state

| Gate | State |
|---|---|
| 0a | ✅ `BRANCH_PK = 20007.4`, entity `31398.4`, currency `159.4`, calendar `83.4` |
| 0b | ✅ Level 1 — `bc.PK = 141.35` → `FK_MISCONFIG = 64408.35` → "Configuracion -NY" |
| 0c | 🟡 **Partially answered 2026-09-21 — still blocked.** ✅ **Q1, instruments: six** — Swap, Deposit & Loan, Cross Currency Swap, OTC Option, Caps And Floors, CDS (Credit Derivatives) `[stated: <SME_NAME>, via Edouard, 2026-09-21]`. **Six of SLB's nine**, so the "same set as SLB" hypothesis is disproven — assuming it would have created three unrequested instruments. ✅ **CDS resolves after all** — `T_PGT_SUB_PRODUCT_S` PK `20313.4`, CODE `Credit` `[confirmed: DB via Edouard, 2026-09-22]`. The earlier "no Sub-Product row" claim is **withdrawn**: it was inferred from an inner join that failed to match. **Nothing is blocked by it**; what stays open is only why that join missed. ⛔ Q2 (24 mandatory accrual values) and Q3 (`LIMIT_ERRORS`, book scope) **still open** — and Q2 still needs its reference query run first. See [`00-gate-0c-signoff-request.md`](00-gate-0c-signoff-request.md) |
| 0d | ✅ `F___SEQUENCE(<table>,'X')`. Tier 2 grant confirmation deferred with the rest |
| 0e | 🔓 **Access landed 2026-09-22 — now evaluable, not yet evaluated.** `BOX_FE` is readable in Tier 2 PRE. Run [`prompts/tier2-full-run.md`](../../../agents/sigom-box-fe-configs-agent/prompts/tier2-full-run.md). ⚠️ **Preflight first** — the 2026-09-16 reading of this gate was wrong because the account had no grants |
| 0f | — Not applicable |
| 0g | ✅ **Passed 2026-09-18** — Q-G7 run against `GOM_GLB_SYS`. 80 objects, 68 declared fields. Identity constants derived, FK targets declared, one uncovered extension found (`T_BOX_ENGFIXDISC_S`), five pre-commit procedures found |

## Release procedure — ✅ access landed 2026-09-22, this is now the live plan

> `[stated: Edouard, 2026-09-22]` Both `DEVENG` and `BOX_FE` are readable in Tier 2 PRE. Steps 1–6 below
> are packaged as a session prompt:
> [`prompts/tier2-full-run.md`](../../../agents/sigom-box-fe-configs-agent/prompts/tier2-full-run.md).
>
> **This run is no longer deferred-verification** once step 5 completes — the shape existed only because
> the target could not be read.

1. Run the visibility preflight; confirm non-zero `BOXFE_VISIBLE`.
2. **Q-G4** against Tier 2 → closes gate 0e and discharges the structural assumption in one step.
3. **Q-G3b** → confirm `F___SEQUENCE` is reachable by the executing account.
4. **Q-G6** → resolve `&&OWNER_OBJ` and `&&EXT_<table>` from the Tier 2 target tables. *(Added
   2026-09-18. Expect one row per table; more than one means the constant model is wrong for that
   table and is a stop.)*
5. Run the deferred **C2** reads, one per walk step; update each BOX-side status from
   `EVIDENCE_REQUIRED` to what the data says.
6. If everything reads as expected, **remove the draft header**. The SQL is unchanged — no regeneration.

Step 5 is the point of running against the real target. Any step whose C2 read comes back unexpectedly
(a row that already exists) is a finding to resolve before that statement runs, not a reason to discard
the run.

## Known blockers

| Blocker | Gate | Owner |
|---|---|---|
| ~~No Tier 2 account with `BOX_FE` grants~~ | 0e | ✅ **CLEARED 2026-09-22** — read-only access granted. Q-G3b (`F___SEQUENCE` callable) still needs confirming in-session; it normally comes with the same grant set, but confirm rather than assume |
| **Gate 0c: the four accrual values, the error limit, the book list** | 0c | Named SME. Instruments ✅ answered 2026-09-21; **these three are not**. Blocks steps 6, 7, 8, 11, 12 |
| ~~CDS `FK_INSTRUMENT` does not resolve~~ | — | ✅ **WITHDRAWN 2026-09-22.** Credit Derivatives is `T_PGT_SUB_PRODUCT_S` `20313.4`. Not a blocker; never was. **Open question only:** why did the 09-18 inner join miss it? Compare SLB's accrual `FK_INSTRUMENT` against `20313.4` |
| **`<SME_NAME>` placeholder** | 0c | Edouard. **8 files** carry it, in 11 places — 8 are attributions to replace, 3 are references *to* the placeholder and must be left alone. An unnamed sign-off does not satisfy gate 0c |

**Withdrawn 2026-09-16:** *"Tier 2 PRE missing BOX_FE tables"* — a permissions artifact. An account
without grants sees no rows in `ALL_TABLES`, indistinguishable from absence.

## Preflight

Every query batch opens with the visibility preflight (`USER`, `DB_NAME`, visible `BOX_FE` and `DEVENG`
object counts). A CSV whose preflight was not run is not evidence — hard rule 8.

## Draft review — `NY_SCH-tier2-pre-draft.sql`, 2026-09-18

First end-to-end draft produced. **Rejected — regenerate.** Reviewed by Edouard and this repo; five
defects, three of them structural, plus one thing the draft got right.

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | `INSERT … SELECT` carried GBO's `FK_OWNER_OBJ` (`12198.4`) and `FK_EXTENSION` into `BOX_FE.T_BOX_ENGCONF_S`, whose own rows all carry `35000126.65` | ⛔ **wrong rows** | Hard rule 9 + Q-G6. Explicit column lists; identity columns from the target |
| 2 | Q-07 mined fixing exceptions with **no `FK_PARENT` filter**, narrowed by a `MIN(PK)` subquery | ⛔ **wrong rows** | `WHERE FK_PARENT = 64408.35` — Q-07 corrected |
| 3 | **Step 5 blocked** — `T_BOX_ENGCONF_X` "requires BOX-specific values not in the GBO evidence" | ⛔ **incomplete config** | Those values never come from GBO. Q-01c: `35000126.65` / `35001566.65` |
| 4 | **Q-06 blocked** on unresolved `FK_BRANCH` semantics | ⚠️ over-blocking | Mine it; status `EVIDENCE_REQUIRED` with the question attached |
| 5 | Six instruments treated as SME-confirmed scope; `LIMIT_ERRORS` 115/100 attributed to "User decision" | ⚠️ attribution | Gate 0c is still ⛔. Name the SME and the date, or status `SME_DECISION_REQUIRED` |

**What it got right, and it is the important part:** every PK is a `F___SEQUENCE(<table>,'X')` call
assigned to a declared variable, children reference their parents' variables, and the draft header is
present. The PK mechanism — the gate that was open longest — works end to end.

⚠️ *The draft also wrapped everything in `ROLLBACK`, which was listed here as a virtue. As of 2026-09-21
that is **not** a safety property: a pre-commit procedure in this walk COMMITs, so the trailing
`ROLLBACK` cannot undo what preceded it. Charter hard rule 11.*

**The pattern across defects 1–3.** All three are the same failure: **the draft assumed a BOX row is a
GBO row re-addressed.** It is not. Three kinds of column behave differently in the copy — mined,
allocated, structural — and the draft only modelled two of them, which is why it copied `FK_OWNER_OBJ`
and then, correctly but for the wrong reason, blocked `T_BOX_ENGCONF_X` for needing a value it had been
silently fabricating elsewhere. **That internal inconsistency was in the draft itself and is the clearest
signal in it.** Hard rule 9 now names the three kinds.

**Blocks 8, 9, 11 and 12 stand** — steps 9/10 are parked by the developer, step 13 is derived, step 14
is not branch-scoped. Those are correct.

### Actions before the next generation

1. Run **Q-G5** (`PGT_SYS.T_PGT_SOURCE_S`) — one query, any environment, no `BOX_FE` access needed.
   Closes the `.44` question and moves the suffix model from `[inferred]` to `[confirmed]`.
2. Re-run **Q-07** with the `FK_PARENT` filter and its unjoined count.
3. Re-run **Q-06** with `FK_PARENT = 64408.35`.
4. Add **Q-G6** to the deferred release list — it is a `BOX_FE` read.
5. Regenerate with explicit column lists throughout, and `&&OWNER_OBJ` / `&&EXT_<table>` as unresolved
   substitution variables so the draft stays honest about what it does not yet know.

## Metamodel run — 2026-09-18, and what it settled

`GOM_GLB_SYS` was interrogated directly. **No `BOX_FE` access was needed for any of it**, so all of this
is available to the run today. Full record: [`../../../docs/reference/sigom-metamodel.md`](../../../docs/reference/sigom-metamodel.md).

| Question | Status before | After |
|---|---|---|
| Product-shaped `Branch` on Accrual Exceptions / Allowed Errors | ⛔ open since 2026-09-11; a *stop the run* condition in the kickoff | ✅ **Closed.** Both declare `pBranch → PGT_STC.T_PGT_BRANCH_S`. The walk's grain is correct |
| `FK_OWNER_OBJ` / `FK_EXTENSION` semantics | wrong model recorded 2026-09-18 | ✅ Corrected; derivation validated 4/4 against Tier 1 |
| Q-08 / Q-09 `FK_PARENT` | `[open-question]`, unvalidatable against empty tables | ✅ **Confirmed** — declared owned collections of `BOX_ENG_Config` |
| `FK_INSTRUMENT` targets across the walk | inferred, one incident at a time | ✅ Declared: Sub-Product ×6, `V_BOX_PROC_INSTR_S` ×2 |
| `_X` bridge convention | `[inferred]` | ✅ `[confirmed]` — it is `FK_KIND 4.1` |
| Step 11 / step 12 column lists | partly unknown | ✅ Declared in full |
| Does a raw INSERT equal what SIGOM does? (procedure F3) | no method | ⚠️ **Five walk objects declare a pre-commit procedure** — see below |
| Is the walk complete? | asserted from screenshots + one developer answer | ⚠️ One declared tab has no step — see below |

### Two things this opened

**1. Pre-commit procedures on steps 2–6.** `BOX_ENG_Config` and `BOX_ENG_FixingCurve` both declare one
(`PKG_ENGPRECOMMIT.p_check_Val_Curves_precommit`, `P_ENGFixingCurve_PreCommit`). The spec shows
`(pk IN NUMBER)`, `AUTHID DEFINER` — the shape of a validation gate, but the **body has not been read**
(`ALL_SOURCE` and `ALL_OBJECTS` show the spec only; `EXECUTE` never reveals a body). It is committed in
`cib-boxfin-dbboxfe` `[stated: Devin, 2026-09-18]`.

⛔ **The draft stays non-executable on this ground alone**, independently of gate 0e.

> ✅ **Both bodies were read on 2026-09-21 — see the source-code round below.** The answer was not the
> reassuring one, and it invalidates the second action proposed here: **`p_check_Val_Curves_precommit`
> COMMITs**, so the snapshot-INSERT-call-rollback test cannot be run against it — that test would commit
> itself. `P_ENGFixingCurve_PreCommit` does no DML and can be tested that way safely.

**2. `T_BOX_ENGFIXDISC_S` — walk step 4b.** `BOX_ENG_FixingCurve.apYieldCurve` is a declared owned
collection with no walk step. Zero rows in Tier 1 PRE, so parked with steps 9 and 10 as
`EVIDENCE_REQUIRED`, no INSERT. Not step 9's Yield Curve — a different object at a different level.

## Source-code round — 2026-09-21

Eight questions put to the `cib-boxfin-dbboxfe` and `cib-boxacc-dbboxacc` repos via Devin. Full record
in [`../../../docs/reference/sigom-metamodel.md`](../../../docs/reference/sigom-metamodel.md) §5, §6c,
§6d. What changed for this run:

| Finding | Effect |
|---|---|
| ⛔ **`p_check_Val_Curves_precommit` writes to step 8's table and `COMMIT`s** | The draft's trailing `ROLLBACK` is **not a safety net**. New charter hard rule 11. Step 8 now emits populated curve values so the procedure is a no-op |
| ⛔ **No `FOREIGN KEY` constraints anywhere** | A wrong FK inserts cleanly and fails silently in a batch. The metamodel is the *only* join-graph source — gate 0g is load-bearing, not optional |
| ⚠️ **`DESCRIPTION` is globally unique** on `T_BOX_ENGCONF_S` and `T_BOX_ENGFCURVE_S` | New pre-flight before steps 2 and 3; a collision is a hard failure. Added to the deferred C2 set |
| ⚠️ **Step 12: `LIMIT_ERRORS` defaults to `0` when the row is missing** | First failed deal aborts the load. One row per in-scope instrument is **mandatory**, not advisory |
| ⚠️ **Step 6 has four `NOT NULL` accrual *values*** | Gate 0c's sign-off is "which instruments **and** these four values per instrument" — a bigger ask than recorded |
| ✅ **Steps 9, 10 and 4b are SIGOM-UI configuration**, not derived or batch-populated | Question sharpens from "what are these?" to "does NY need them?" — answerable by an SME |
| ✅ **Step 11 proven from source** (`CIBAUKI-4704`) | One book, one queue. And the queue builder joins `T_BOX_ENGCONF_X`, so **step 5 is a runtime prerequisite** |
| ✅ **Grants named**: `BOX_FE_RD` / `BOX_FE_WR` | The access blocker now has a precise ask — see below |
| ✅ **No triggers on any FE walk table** | One fewer divergence path |
| ✅ **`P_ENGFixingCurve_PreCommit` is validation-only** | Safe to call as a gate after steps 3/4. It also reads `T_BOX_ENGFIXDISC_S`, which is how step 4b's purpose was resolved |

**Still not executable**, and now for a better-understood reason: the draft must be regenerated to
populate step 8's curves, bind the step-2/3 description pre-flight, and carry the procedure calls in the
right places.

### Gate 0g added

The metamodel read is now a gate (Q-G7). It produces the identity constants, the declared FK targets and
a completeness diff, and it needs no `BOX_FE` grants — so **it runs before the walk, not after a
defect**.

## Outstanding queries

Resume the walk from Q-01 against GBO Tier 2, treating every `Q-nnb` BOX-side read as deferred.
