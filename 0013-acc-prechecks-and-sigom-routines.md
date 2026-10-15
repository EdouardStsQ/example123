# 0013. BOX ACC configs: structural pre-checks, GBO-production usage, and SIGOM's own routines for phase 2

Date: 2026-10-14
Status: accepted

## Context

Before the first run of `sigom-box-acc-configs-agent` (phase 1, ADR 0011), the operator ran structural queries in
PRE-PROD (GBO D1–D2, BOX B1–B4, metamodel M1–M3), and Devin read `PKG_ACCTPROP`, `PKG_ACCTPRECOMMIT`,
`PKG_SIGOM_COV` and the Liquibase layout in `cib-boxacc-dbboxacc` (read-only). Together they showed:

- the database enforces almost nothing: no foreign keys, three unique keys, no defaults;
- the topic and condition lists are extensions of the portfolio-property object, three topic lists told apart only
  by `FK_EXTENSION`; the catalogue's list queries mixed them;
- `f_GenTopicCond` never sets the account, and in older package versions reads global / internal topics from another
  place;
- PKs come from `F_GetPK` with the installation's `AUTH_CODE` fraction, while the repo's Liquibase data hard-codes PKs
  and some sequences lag behind their data;
- negative owner objects mark test / deleted rows `[operator]`; optimizer statistics are years old;
- what is *configured* in GBO is not what is *used*: GBO holds 2,476 portfolio properties, BOX 71.

All of it is in [`box-acc-model.md`](../reference/box-acc-model.md).

## Decision

1. **Pre-checks before any screen query** (A-P1–A-P6): readable tables and live counts, identity values against the
   expected constants, negative owners listed, PK generation will not collide, the deployed `PKG_ACCTPROP` version.
   A failure is the run's result — never "missing → create" on an unconfirmed structure.
2. **Usage in GBO production** (A-U0–A-U5, new environment tag `GBO-PROD`): the target's configuration, what it posts
   (movements by instrument × portfolio property × topic × account, over a window the operator chooses), what holds a
   balance, configured vs used per list. The gap matrix proposes **what is in use**; configured-but-unused rows are
   asked. Aggregates only, no names.
3. **Reading rules** in every query: owner + extension, never `FK_PARENT` alone; negative owners excluded;
   `COUNT(*)`, never `NUM_ROWS`.
4. **Phase 2 creates rows the way SIGOM does**: `P_SETHEADER` / `F_GetPK`, then `f_GenTopicCond`, then the lists'
   accounts, then `p_StatusPortFolio`, in one transaction, every INSERT guarded by the agent's natural key, a verify
   that every reference resolves. No hard-coded PK.
5. Runs are versioned (`scripts/new_run.py --area acc-configs`), like the other agents'.

## Alternatives considered

- **Copy GBO's configuration as it is.** Brings thousands of unused portfolio properties and every GBO topic; BOX
  consolidates them.
- **Liquibase changesets with hard-coded PKs** (the repo's convention for seed data). PKs differ per environment and
  some sequences lag; no branch has been configured that way. Kept as an option for the BOX team to choose (open), not
  the default.
- **Trust the database to reject bad rows.** It does not: no foreign keys.

## Consequences

- One more round of queries per run (pre-checks, usage), in exchange for a matrix limited to what NY uses and runs
  that stop on a wrong environment, schema or package version instead of proposing wrong rows.
- GBO production is read (read-only, aggregates) — the operator's access to it is a prerequisite.
- Phase 2 depends on the BOX team's choice of delivery form and on the topic mapping; its call sequence is known.
