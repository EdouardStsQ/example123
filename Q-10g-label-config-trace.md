# Q-10g — what SIGOM's Label Config screen runs when a label is saved (Tier 2 PRE)

- **Source:** operator, 2026-10-02 — DB trace while saving a test label in SIGOM `PGT - Label Config` (screenshot).
- **Read:**

| Step | Statement (from the trace) |
|---|---|
| 1. PK | `BEGIN :RETURN := PGT_SYS.F___SEQUENCE(TABLE_NAME => PGT_DOMAINS, SEQ_RANGE => 1); END;` → `24044.44` (fraction = auth code 44) |
| 2. Object | `GOM_GLB_SYS.T__OBJ_DEF_S` `PK = 17910.4` (the Label Config object) |
| 3. Triggers | `GOM_GLB_RUN.T__OPTRIGGERS_S` for `'PGT - Label Config'`, `LGINSERT = 1`, `NBBEFORE = 1` (project `144.4`) → function `35006556.1` |
| 4. Insert | `insert into PGT_SYS.PGT_DOMAINS (PK, FK_OWNER_OBJ, CODE, DESCRIPTION) values (24044.44, 17910.4, 'XNY00', 'TEST NY BOOK');` |
| 5. Pre-commit | `BEGIN PGT_SYS.Pkg_SysPrecommit.p_DomainsPreCommit(PK => 24044.44); END;` |

- **Used by:** skill `set-up-book-labels`, PK rule `screen` (steps 1, 4, 5 reproduced; step 3 is how the screen
  finds step 5).
- **No side effect:** the test save was not committed — `XNY00` does not exist in Tier 2 `[stated: operator, 2026-10-02]`.

## ⚠️ Correction — run 7, 2026-10-02

The proposal built from step 1 **stopped before inserting anything**: from SQL,
`F___SEQUENCE(TABLE_NAME => 'PGT_DOMAINS', SEQ_RANGE => 1)` returned **24038**, then **24039** (fraction 0), not
`NNNNN.44` `[operator, 2026-10-02]`. So the `.44` in the trace is not produced by that call as run outside SIGOM; the
function adds the fraction for `SEQ_RANGE = 'X'` (Q-G3, the BOX_FE copy of the function). The skill now uses `'X'`,
keeps the fraction check, and also checks the PK is unused. **Confirm on `PGT_SYS`'s copy** before re-running
(Q-10h).
