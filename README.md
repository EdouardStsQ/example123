# Run log — NY_SCH, Tier 1 rehearsal, BOX FE config

Agent: `sigom-box-fe-configs-agent` · Kickoff: `agents/sigom-box-fe-configs-agent/prompts/kickoff-ny-sch.md`
(see its *Active mode, 2026-09-16* section)

**Status:** active. **Purpose: validate that the walk emits correct, ordered, well-formed SQL** —
nothing here is deployable.

> ⚠️ **Tier 1 rehearsal.** Every value produced in this folder is a **Tier 1** value. Structure is
> validated here; values are not, and **must not be carried to Tier 2**. When a Tier 2 account with
> `BOX_FE` grants exists, regenerate against Tier 2 — do not edit these files into Tier 2 ones.

## Why this run exists

The Tier 2 run (`../tier2-pre/`) is paused: the available Tier 2 account reads GBO (`DEVENG`) but has
no grants on `BOX_FE`. Rather than sit blocked, the walk runs against Tier 1, where access exists, to
prove the agent produces the right SQL. The working assumption — **stated, not confirmed** — is that
`BOX_FE` table structures are identical between Tier 1 and Tier 2 and differ only in content. That
assumption stays untested until someone with Tier 2 grants runs the Q-G4 diff.

## Gate state for this run

| Gate | State |
|---|---|
| 0a | Satisfied — `BRANCH_PK` resolved in Tier 1 |
| 0b | Satisfied — level 1 only (narrowed 2026-09-16); `FK_MISCONFIG` → GBO MIS header |
| 0c | **Blocked on the SME, but now concrete.** A branch's instrument set is its Accrual tab (`T_BOX_ENGACCRCONF_S`), one row per instrument. SLB in Tier 1 has **nine**. Run Q-05c, put that list to the SME as *"these nine, or which subset?"* |
| 0d | ✅ **RESOLVED 2026-09-17** — `F___SEQUENCE(<table>,'X')`: `SQ_BOX_FINANENG1.NEXTVAL` + the environment's auth code as a fraction. Emit the function call assigned to a declared variable; symbolic `&PK_nn_*` placeholders convert one-to-one |
| 0e | Evaluated against **Tier 1**, where access exists — can pass here normally |

## ✅ PK mechanism — resolved, no longer a diagnostic

`[confirmed: source via BOX FE Developer, 2026-09-17]` PKs come from `F___SEQUENCE(TABLE_NAME,
seq_range)`: `NEXTVAL` from **`SQ_BOX_FINANENG1`** for every walk table, plus — with
`seq_range = 'X'` — `auth_code / 10^length(auth_code)`, where `auth_code` is a single global row in
`gom_glb_sys.t__CORE_INFO_S`. The inferred "shared sequence plus environment suffix" hypothesis
recorded here on 2026-09-17 was correct: SLB's `24.095.416,21` is `SQ_BOX_FINANENG1.NEXTVAL + 0.21`.

**What the rehearsal emits now:** `v_pk := F___SEQUENCE('T_BOX_ENGCONF_S','X');` assigned to a declared
variable, with children referencing the variable. The `&PK_nn_*` placeholders already produced convert
one-to-one — convert, don't regenerate. A literal PK, or a bare `SQ_BOX_FINANENG1.NEXTVAL` without the
fraction, are both failures.

**Still worth one query here:** confirm `F___SEQUENCE` exists and is `VALID` in the target environment,
and note its owning schema so the script references it correctly.

## Preflight

Every query batch in this run opens with the visibility preflight (`USER`, `DB_NAME`, visible `BOX_FE`
and `DEVENG` object counts). A CSV whose preflight was not run is not evidence — see hard rule 8.

## Outstanding queries

None requested yet.
