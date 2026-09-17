# Run log — NY_SCH, Tier 2 PRE, BOX FE config

Agent: `sigom-box-fe-configs-agent` · Kickoff: `agents/sigom-box-fe-configs-agent/prompts/kickoff-ny-sch.md`

**Status:** not started.

## Stage

| Stage | State |
|---|---|
| A — Gates | Not started. 0a and 0b (level 1) satisfied in the 2026-09-16 probe; 0e blocked on access |
| B — Provisioning | **No longer expected.** The "Tier 2 PRE missing BOX_FE tables" finding was withdrawn 2026-09-16 — a permissions artifact, not a schema gap |
| C — Mining | Blocked on A |
| D — Findings review | Blocked on C |
| E — SQL generation | Blocked on D, and on gates 0d + 0e |
| F — Apply and verify | Blocked on E |

## Known blockers before the run starts

| Blocker | Gate | Owner |
|---|---|---|
| **No Tier 2 account with `BOX_FE` grants** | 0e | Edouard / DBA. **This is the live blocker for this run.** The Tier 2 account available reads GBO (`DEVENG`) but has no privileges on `BOX_FE` — which is why Q-G4 appeared to show missing tables on 2026-09-16 |
| Instrument scope not supplied | 0c | Named SME — chosen from BOX's live catalogue, not from GBO. **Now a concrete question:** a branch's set is its Accrual tab (`T_BOX_ENGACCRCONF_S`); SLB shows nine, of which seven resolve to a Sub-Product row. Run Q-05c's corrected `LEFT JOIN` form and put the list to the SME |
| ~~PK generation mechanism unknown~~ ✅ **RESOLVED 2026-09-17** | 0d | `F___SEQUENCE(<table>,'X')` — `SQ_BOX_FINANENG1.NEXTVAL` plus the environment's auth code as a fraction. No longer a blocker |

**Withdrawn 2026-09-16:** *"Tier 2 PRE missing BOX_FE tables (gate 0e, Release/DBA)"* — a permissions
artifact. An account without grants sees no rows in `ALL_TABLES`, which is indistinguishable from
absence. Nothing is known about Tier 2 PRE's schema completeness; the related question of whether
`BOX_FE` was ever deployed to Tier 2 at all is **stood down**, not open.

## Outstanding queries

None from this folder. The Tier 2 run is paused pending `BOX_FE` access; work has moved to
`runs/NY_SCH/tier1-rehearsal/` (see the kickoff's *Active mode* section). Every future batch here
opens with the visibility preflight — a CSV whose preflight was not run is not evidence.
