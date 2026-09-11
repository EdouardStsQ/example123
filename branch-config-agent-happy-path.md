# Case: NY_SCH FE + ACC config mined and proposed

Covers: branch-config-agent
Type: happy path

**Supersedes** `box-fe-expert-happy-path.md` and `box-acc-expert-happy-path.md` — those two agents were folded into `branch-config-agent` (see `docs/reference/branch-config/agent-architecture.md`'s "The three agents" section); this single case covers what the two separate cases would have.

**Pending** — blocked on Tier 2 DB access. No GBO Tier 2 fixture exists yet.

## Given (input state)

GBO Tier 2's existing FE-equivalent configuration for NY_SCH (across the eight SIGOM-equivalent areas) and ACC-equivalent configuration (portfolio properties, topic vocabulary, GL account mapping, branch-group resolution).

## When (action)

Agent runs `mine-fe-branch-config` and `mine-branch-config` against GBO Tier 2, then `propose-branch-config` over both results.

## Then (expected outcome)

One complete, SME-reviewable decision matrix (Markdown + JSON) covering all eight FE tabs and all ACC objects, with every dependency status-tagged (`CONFIRMED_PRESENT` / `CONFIRMED_ABSENT` / `PROPOSED` / `SME_DECISION_REQUIRED` / `EXTERNAL_CHECK_REQUIRED` / `EVIDENCE_REQUIRED`). Any tab or object lacking a GBO equivalent is explicitly flagged rather than defaulted, and every GL account value is either sourced from GBO or flagged as an open question — never invented or copied from another branch.
