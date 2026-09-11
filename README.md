# Examples

Concrete, worked job sequences — a trace of one real (or realistic) onboarding run, start to finish. These illustrate `process/02-target-state.md`; they don't redefine it. If an example and the process doc disagree, the process doc is wrong and needs updating — don't let examples become a shadow spec.

## vs. reference/

Everything under `reference/` (queries, job-chains, tables, APIs) is generic and reusable — true for any entity, any run. An example is the opposite: one specific, lived-through case, with actual values and an actual outcome. An example should *link to* the reference material it exercised (which query, which job chain, which checklist) rather than re-explaining it — e.g. "ran `../reference/queries/list-entity-static-data.sql`, got back: ..." rather than pasting the query's own docs in. If you find yourself writing something that's true regardless of which entity it's about, that content belongs in `reference/`, not here.

This also makes examples a natural source for eval fixtures (`../../evals/cases/`) — a good example is often just an eval case with more narrative around it.

Use placeholder identifiers only (`ENTITY_A`, `CPTY_X`) — never real entity, counterparty, or portfolio names, even when the example is transcribed from a real run.

Name files by what the example demonstrates, not by date: `entity-onboarding-happy-path.md`, `entity-onboarding-missing-static-data.md`.
