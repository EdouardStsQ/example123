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
| 0c | **Blocked** — instrument scope from a named SME, chosen from BOX's live catalogue |
| 0d | **Unresolved — symbolic-PK mode.** Q-G3 returned ten PK columns with empty `DATA_DEFAULT`, no triggers, and seven sequences with no mapping to the walk tables. PKs are emitted as `&PK_nn_*` substitution variables, never literals |
| 0e | Evaluated against **Tier 1**, where access exists — can pass here normally |

## Open diagnostic — the PK format lead

Every observed PK has the form `<integer>.<authcode>` (`141.35`, `20007.4`, `4.21`, `64408.35`), and a
bare sequence cannot produce that suffix. While Tier 1 access exists, pull `ALL_SEQUENCES` for
`BOX_FE`, `MAX(<pk>)` and `TRUNC(MAX(<pk>))` per walk table, and `DATA_SCALE` per PK column, then
answer: does any sequence's `LAST_NUMBER` track the integer part of any table's `MAX(PK)`? If yes and
`DATA_SCALE` is 2, the mechanism is sequence-for-the-integer plus application or import tooling for the
suffix — which resolves gate 0d.

## Preflight

Every query batch in this run opens with the visibility preflight (`USER`, `DB_NAME`, visible `BOX_FE`
and `DEVENG` object counts). A CSV whose preflight was not run is not evidence — see hard rule 8.

## Outstanding queries

None requested yet.
