# Run log — NY_SCH BOX FE config, Tier 2 PRE

Agent: `sigom-box-fe-configs-agent` · Kickoff: `agents/sigom-box-fe-configs-agent/prompts/kickoff-ny-sch.md`

**Status: ACTIVE — deferred-verification run.** `[stated: Edouard, 2026-09-18]` This is the **real run**
against the **real target**, executed as far as read access allows. It is not a rehearsal and not a
throwaway.

> **Supersedes the split-tier rehearsal** (`../tier1-pre-rehearsal/`), which wrote to Tier 1 PRE. That
> approach is withdrawn: substituting the target made every mined FK a portability question, blocked
> step 4 on quote references that are local to Tier 2, and produced SQL that was never executable
> anywhere.

## Shape of this run

| | |
|---|---|
| `GBO_SOURCE` | **GBO Tier 2** — NY_SCH is live here |
| `TARGET_ENV` | **Tier 2 PRE** — the real target |
| Readable | GBO Tier 2 (`DEVENG`, `PGT_*`) — everything the walk mines |
| **Not readable** | `BOX_FE` in Tier 2, pending an account with grants |
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

## What is deferred — the complete list

Procedure step **C2** (*"does a row already exist on the BOX side?"*) for every walk step, and
**gate 0e**. Nothing else.

- Mining, walk order, dependency graph, value derivation and SQL generation **all run normally**.
- **Every BOX-side finding is `EVIDENCE_REQUIRED`** until its read happens. Never `CONFIRMED_ABSENT` on
  an assumption — NY almost certainly has no `BOX_FE` rows, but near-certain is not confirmed.
- **The SQL is a marked draft.** Header on every file: *Draft — generated before BOX-side verification.
  Do not execute until gate 0e and the deferred C2 reads pass.*

## Gate state

| Gate | State |
|---|---|
| 0a | ✅ `BRANCH_PK = 20007.4`, entity `31398.4`, currency `159.4`, calendar `83.4` |
| 0b | ✅ Level 1 — `bc.PK = 141.35` → `FK_MISCONFIG = 64408.35` → "Configuracion -NY" |
| 0c | ⛔ **Blocked on the SME.** Run Q-05c against a reference branch, put the enumeration to them |
| 0d | ✅ `F___SEQUENCE(<table>,'X')`. Tier 2 grant confirmation deferred with the rest |
| 0e | ⏸ **Deferred — the release gate.** Cannot evaluate without `BOX_FE` access |
| 0f | — Not applicable |

## Release procedure — when `BOX_FE` Tier 2 access lands

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
| **No Tier 2 account with `BOX_FE` grants** | 0e | Edouard / DBA. The one access item. Ask specifically for `BOX_FE` grants — "Tier 2 access" reads as already granted, because for GBO it is |
| Instrument scope not supplied | 0c | Named SME — from BOX's live catalogue. Run Q-05c first so they confirm an enumeration, not a phrase |

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
assigned to a declared variable, children reference their parents' variables, the draft header is
present, and the whole block is wrapped in `ROLLBACK`. The PK mechanism — the gate that was open
longest — works end to end.

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

## Outstanding queries

Resume the walk from Q-01 against GBO Tier 2, treating every `Q-nnb` BOX-side read as deferred.
