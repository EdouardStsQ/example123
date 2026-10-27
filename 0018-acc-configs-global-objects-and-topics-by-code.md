# 0018. BOX ACC configs: topics by CODE; missing topics and standard historics created as global (.65), to review

Date: 2026-10-27
Status: accepted — amends ADR 0014 (global screens verify-only) and the agent's hard rules 2 and 3

## Context

The BOX ACC expert reviewed the first Tier 2 gap matrix (`acc-configs/gap_20261023_1`). It asked how GBO topics map to
BOX's (54 GBO topics of the in-scope lists have no BOX `CODE` twin), what to do with GBO properties without a branch
condition, with GBO objects that have no BOX screen, and flagged a PK collision (A-P5) on the account date rules.

## Decision

`[BOX ACC expert via operator, 2026-10-27]`

1. **GBO → BOX topics by `CODE`, always.** Never by description, never asked.
2. **Missing topics and standard historics are created as global objects**: the global **`.65` PK**, not the
   installation's; flagged **"global — to review"** in the matrix and the report. A `.65` PK created in a lower
   environment (PRE) may clash with production's — said on every such row; the BOX team agrees the PK range before
   the SQL runs. The 54 NY topics with no BOX twin: `create (global .65)`, to review `[operator, 2026-10-27]`.
3. Conditions, event groups and events stay **verify-only**: a new branch uses the existing ones.
4. Phase 2: the global rows are in the main rollback **and** in a separate `global_pk_rollback.sql`.
5. GBO portfolio properties with a **blank branch condition or no branch row are out of scope** — not asked.
6. **`T_PGT_TOPICS_RR` and GBO ConcMis are out** — nothing to do.
7. **A-P5 compares within the installation's PK fraction**: rows of another fraction (`.65` seed data) never collide;
   `(d)` reads one table in detail. NY's `T_BOX_ACCT_PARENT_DATE_S` warning was a false alarm (next `2`; rows `1.44`
   and `2.65`; no counter row).

## Consequences

- Charter hard rules 2–3, screens 6–7, kickoff Step 7 (no topic-mapping question) and Step 8 rules, matrix template
  (a *Global objects — to review* section), catalogue (A-U7 keeps only properties with a branch value classified in;
  screens 6–7; A-11 rulings; A-P5 (d)), eval case, NY inputs.
- Still open: the PK range for global objects created outside production (BOX team).
