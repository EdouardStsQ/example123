# Case: NY_SCH full onboarding, no escalations

Covers: branch-onboarding-orchestrator
Type: happy path

**Pending** — blocked on Tier 2 DB access. Cannot write a real fixture (GBO Tier 2 input state, expected BOX state) until NY_SCH can actually be queried; per this repo's own rule, we don't invent the values a real case would need.

## Given (input state)

Tier 2 access granted; NY_SCH branch group resolved (existing or new); product scope confirmed; online (CROSS_REF) confirmed out of scope for v1.

## When (action)

Orchestrator runs Phase 1 → Phase 4 with all three experts' proposals confirmed on first pass.

## Then (expected outcome)

NY_SCH's `accounting-resolution-chain.md` trace passes end to end: source arrival → instrument type → FE status → ACC movement posted.
