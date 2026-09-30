# 0008. A separate agent for BOX FE/ACC batch jobs — explain and gap first, generate later

Date: 2026-09-29
Status: accepted

## Context

Workstream W3 (jobs) had an owner only for the Data-Lake feeds (`box-datalake-expert`). The BOX FE/ACC
batch jobs — Control-M job, `db.conf` line, event group, events, entries — were assigned in
`02-target-state.md` to `branch-config-agent` as "reproduce a known topology", from Tier 1 evidence only.
Tracing one job end to end (GMBX3ES02D07, 2026-09-29) showed that the topology does **not** transfer as
is: Tier 2's wrapper (`PGT_NY`) has a different owner, different constants and no label argument, while
the BOX catalog is already deployed there. Two of Devin's inferences on the way were wrong (an event's
meaning, the debit/credit flag). A NY job list generated from Tier 1 would have looked right and failed.

## Decision

A new branch-agnostic agent, `box-batch-jobs-agent`, owns BOX FE/ACC batch jobs:

- **Phase 1 (built):** EXPLAIN — trace any job, group or event, with citations, in a named environment;
  GAP — compare a target branch in its environment with an onboarded reference branch, layer by layer
  (chain doc §4), ending in a gap report and a proposed job matrix signed off by the BOX team.
- **Phase 2 (not built):** PROPOSE — render `db.conf` lines, Control-M jobs and label rows from a values
  file, like the FE agent's SQL (ADR 0006), only from a signed-off matrix.
- Read-only; every value tagged with its environment; CONFIRMED / INFERRED on every claim.
- `T_BOX_MBJ_PROPERTIES_S` rows stay in `sigom-box-acc-configs-agent`'s scope; this agent lists them.
- Operator's scope (2026-09-29): *first explain how Tier 1 BOX jobs work, then propose what NY needs.*

## Alternatives considered

- **Leave it in `branch-config-agent`.** Its skills diff BOX config tables; none reads Control-M,
  `db.conf` or the batch catalog, and its FE overlap is already an open decision.
- **Generate NY's jobs straight from SLB's.** Rejected: the Tier 2 wrapper cannot take the label, and the
  Tier 2 job-name token and Control-M folders are unknown. Generating first would produce plausible,
  broken config.
- **Fold it into `sigom-box-acc-configs-agent`.** That agent is deferred, owns SIGOM ACC objects, and the
  batch spans FE and ACC.

## Consequences

- W3 now has an owner for BOX jobs; the orchestrator delegates to it.
- The first NY run is expected to end as a proposal blocked on the BOX Lead (the label argument). That is
  the intended outcome, not a failure.
- Parsers for `db.conf` and Control-M JSON are deferred until real extracts exist to test them on.
