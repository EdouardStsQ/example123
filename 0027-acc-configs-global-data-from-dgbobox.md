# 0027. BOX ACC configs: global (.65) static data is created in DGBOBOX and imported in each target; the ACC SQL runs as BOX_ACC

Date: 2026-11-16
Status: accepted — supersedes, for global objects, ADR 0018's "`.65` PK from a range the BOX team agrees, or
`next-free` in DEV" (ADR 0018's other points stand: topics by `CODE`, a missing topic or standard historic created as
global)

## Context

NY_SCH's ACC gap run in PRE-PARALELO (IGBOUSIB, `gap_20261112_1`) found 54 GBO topics with no BOX `CODE` twin — the
same 54 created in DGBOUS (DEV) as `1237.65`–`1290.65` with `next-free`, a DEV-only shortcut. Outside DEV the renderer
asked for a `.65` range agreed with the BOX team (ADR 0018, open item 4zx). The run also found that `BOX_ADMIN`, the
BOX account first used in PRE-PARALELO, sees none of `BOX_ACC`'s sequences.

## Decision

1. **Global static data is created in the global installation and copied** `[BOX ACC expert via operator,
   2026-11-13]`: "the .65 global static data should be created in the DGBOBOX (BOX DEV) environment (using the sequence
   from that environment and where auth code is .65) and then take the inserts from DGBOBOX and insert them in the
   target env" — accounting topics and standard historics alike. DGBOBOX has `BOX_ACC` and `BOX_FE` users. So:
   - a **global run** in DGBOBOX (`global_only: true`, auth code 65): its precheck, rehearsal and config create the
     missing topics with DGBOBOX's own sequence (`global_pk.<table>.start` = `"sequence"`) and `p_TopicsPreCommit`;
   - its **export** (`render_acc_sql.py <global run> --export`, run in DGBOBOX) prints each global row's INSERT **as it
     is stored** — every column, what BOX set on save included, for every global row of the values (by `CODE`: created now or already in DGBOBOX). `p_TopicsPreCommit` only UPDATEs the topic row itself
     (`ALL_SOURCE` of `PKG_ACCTPRECOMMIT`, IGBOUSIB, operator 2026-11-16), so a topic is one row of
     `T_BOX_ACCT_TOPICS_S`;
   - each **target** imports them (`--import <export output>`: a rehearsal, then the import, with the same `.65` PKs;
     a PK or `CODE` already used by another row stops it) **before** its own precheck; the target's values say
     `"imported"` for those rows — its SQL never creates them, its precheck requires them present.
2. **DGBOUS is left as it is** `[operator, 2026-11-16]`: NY's 54 topics there (`1237.65`–`1290.65`, `next-free`) were
   made before this ruling. Topics are always found by `CODE` in each environment, so nothing links DGBOUS's PKs to
   another environment's. Known difference: DGBOBOX's sequence may give those numbers to other topics — DGBOBOX's
   export must never be imported into DGBOUS without checking (the import stops on a PK or `CODE` clash anyway).
3. **The ACC SQL runs as `BOX_ACC`** in every environment `[operator, 2026-11-16]`: in IGBOUSIB `BOX_ACC` sees all 31
   `SPK_T_BOX_*` sequences (owner `BOX_ACC`; `SPK_T_BOX_ACCT_GLTA_S` at 16758); neither `BOX_ADMIN` nor `pgtadmin`
   does. The gap run's `TGT` queries may run as `BOX_ADMIN` or `BOX_ACC`; `GBO` queries as `pgtadmin`. The gap run's
   A-P5 "GLTA PK generation not visible" finding was the account, not a missing sequence.

## Consequences

- `scripts/render_acc_sql.py`: `global_only` runs (refusals `global-only-auth`, `global-only-mixed`); `"sequence"`
  (global installation only, `global-pk-sequence`) and `"imported"` (targets only, `global-pk-imported`) starts;
  `--export`, `--import <file>` (refusals `export-not-ok`, `export-line`, `export-duplicate`, `import-missing`),
  `--import-rollback`. Tests.
- Kickoffs: the gap run lists the global objects "to create in DGBOBOX" (no `.65` question any more); the SQL step
  runs the global run in DGBOBOX, the export, then the target's import, before the target's precheck. Charter, matrix
  template, values example, catalogue.
- Open item 4zx closed; the BOX team's GLTA question of `gap_20261112_1` withdrawn.

## Alternatives considered

- A `.65` range agreed per environment (ADR 0018): rejected — one installation hands out `.65` PKs, every other
  environment gets the same rows.
- Creating the topics in each target with `next-free`: rejected — the same topic would have different PKs across
  environments (DGBOUS already differs).
- Granting `BOX_ADMIN` on the sequences: not needed — `BOX_ACC` is available in IGBOUSIB.
