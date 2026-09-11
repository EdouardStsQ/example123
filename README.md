# Run log — NY_SCH, Tier 2 PRE, BOX FE config

Agent: `sigom-box-fe-configs-agent` · Kickoff: `agents/sigom-box-fe-configs-agent/prompts/kickoff-ny-sch.md`

**Status:** not started.

## Stage

| Stage | State |
|---|---|
| A — Gates | Not started |
| B — Provisioning | Expected to be needed (Tier 2 PRE missing BOX_FE tables) |
| C — Mining | Blocked on A |
| D — Findings review | Blocked on C |
| E — SQL generation | Blocked on D, and on gates 0d + 0e |
| F — Apply and verify | Blocked on E |

## Known blockers before the run starts

| Blocker | Gate | Owner |
|---|---|---|
| Read-only Tier 2 DB access not confirmed | — | Edouard |
| Product and book scope not supplied | 0c | Named SME |
| PK generation mechanism unknown | 0d | Q-G3 will answer, or reveal SIGOM-side allocation |
| Tier 2 PRE missing BOX_FE tables | 0e | Release/DBA — and first, establish whether BOX_FE was ever deployed to Tier 2 at all |

## Outstanding queries

None requested yet. First batch when the run starts: Q-G1, then Q-G2/Q-G3/Q-G4 once `BRANCH_PK` is resolved.
