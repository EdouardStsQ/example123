# 0007. Two pre-steps before any config SQL: the PK mechanism and the dummy label

Date: 2026-09-25
Status: accepted `[stated: BOX Lead review of run 6, via Edouard, 2026-09-25]`

## Context

The BOX Lead reviewed run 6's output: good in general, but the PK check belongs **before** the config,
not inside it — check the next values against the PKs, consider `ALTER SEQUENCE`, raise the problem and
propose the fix, and only then build the config. The dummy portfolio likewise: the user picks one, and if
none exists the agent proposes the label insert. Run 6 itself set the dummy to NY001, the branch's own
book — a label no other branch uses — and nothing stopped it. A BOX Dev had also warned that Tier 2 may
hold typed PKs.

## Decision

- **P1 — PK mechanism.** `render_sql.py --precheck` renders `<BASE>-P1-pk-precheck.sql` from the
  `environment` values alone. The applying account runs it; it draws one PK per table from `F___SEQUENCE`,
  checks the fraction, counts typed PKs at or ahead of `SQ_BOX_FINANENG1`, and prints OK or PROBLEM plus a
  proposal (move the sequence past them, or correct the rows) for the BOX FE team. The full render refuses
  until the saved output says OK. `chk_pk` in the config keeps only the auth-code check.
- **P2 — dummy label.** Card 3 picks an existing label, which must exist in the target and be used by at
  least one other branch (Q-10c), or chooses to create one: the agent then renders
  `<BASE>-P2-dummy-label-PROPOSAL.sql` (a `PGT_SYS.PGT_DOMAINS` insert modelled on the Tier 1 dummy, checked
  against the target's columns, PK from the function the BOX FE team names) and step 11 waits.
- **Hard rule 4** gains one exception: these two files may carry *proposals* (DDL printed, an insert) for
  the BOX FE team to decide and run. No file of the agent's runs them.
- **Metrics.** `scripts/run_metrics.py` counts effort (queries, decisions, renderer iterations, time) and
  data (rows per step and table, value provenance) into `06-run-metrics.md`.

## Alternatives considered

- **Keep the PK-used check inside the config** (the 2026-09-24 design). It stops safely, but only at apply
  time, with no diagnosis and no fix — the BOX Lead's point.
- **Let the agent run `ALTER SEQUENCE`.** The sequence is shared by every BOX FE table; changing it is the
  owning team's decision.

## Consequences

- The config is never built on an unresolved PK mechanism or an unshared dummy.
- Two more operator touch-points early in the run (P1, and P2 when needed), both counted in the metrics.
- The procedure is the skill [`resolve-fe-config-prechecks`](../../skills/resolve-fe-config-prechecks/SKILL.md) `[2026-09-28]`, so every branch's run follows the same steps.
