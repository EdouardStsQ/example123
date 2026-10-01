# Query catalogue — BOX batch jobs

The queries [`box-batch-jobs-agent`](../../../agents/box-batch-jobs-agent/AGENT.md) hands to the
operator (or runs itself), by ID. Branch-agnostic: every value is a placeholder. The mechanism they read
is in [`../job-chains/box-batch-chain.md`](../job-chains/box-batch-chain.md).

**Conventions**

- Placeholders `&&NAME`. Owners are placeholders too, because they differ per environment:
  `&&WRAPPER_OWNER` (Tier 1 `PGT_ES`, Tier 2 `PGT_NY`), `&&CATALOG_OWNER` (`PGT_PRC` in both so far).
  **Read them from J-E1 / J-E2 in each environment; never carry one over.**
- `Env`: `REF` = the reference branch's environment, `TGT` = the target environment, `both` = run in
  each and save two files.
- Save every result as `01-evidence/J-<ID>-<env>.csv` (SQL Developer: right-click the grid → *Export*
  → csv). A screenshot is not evidence when an export is possible.
- `Expect` says what a normal result looks like. Anything else is reported, not interpreted away.
- Column names are confirmed where a query has already been run (✅ with its date). Queries marked 🆕 have
  not run yet: if one fails on a column name, `DESCRIBE` the table and fix the query here.

---

## E — Environment profile (run first, in every environment)

### J-E1 — Who owns the wrapper and the engine core `Env: both` ✅ Tier 2 2026-09-29
```sql
SELECT owner, object_name, object_type FROM all_objects
WHERE  object_name IN ('PKG_GMBATCHPROCESS','PKG_BATCHPROCESS') ORDER BY owner;
```
Expect: one or more wrapper owners (one per regional instance) and the core owner(s). Tier 2:
`PGT_BOS`, `PGT_CO`, `PGT_NY` (wrapper), `PGT_PRG`, `PGT_STL` (core). **Which wrapper a branch uses is a
fact to establish** (its `db.conf` lines, or the operator), not a guess from the name.

### J-E2 — Who owns the catalog `Env: both` ✅ Tier 2 2026-09-29
```sql
SELECT owner, table_name FROM all_tables
WHERE  table_name IN ('T_PGT_BR_EVE_S','T_PGT_BR_EVE_EXT_S','T_PGT_EVE_S','T_PGT_UPDATE_S',
                      'T_PGT_TABLE_S','T_PGT_COND_S','T_PGT_COLS_S','T_PGT_BRANCH_S')
ORDER  BY table_name, owner;
```
Expect: `PGT_PRC` for the catalog tables.

### J-E3 — Can the account read the wrapper's body? `Env: both` ✅ both 2026-09-29
```sql
SELECT type, COUNT(*) FROM all_source
WHERE  owner = '&&WRAPPER_OWNER' AND name = 'PKG_GMBATCHPROCESS' GROUP BY type;
```
Expect today: `PACKAGE` only (spec). No `PACKAGE BODY` → the body's behaviour stays `[open-question]`.

### J-E4 — The wrapper spec: branches, entry points, label arguments `Env: both` ✅ Tier 2 2026-09-29
```sql
SELECT line, text FROM all_source
WHERE  owner = '&&WRAPPER_OWNER' AND name = 'PKG_GMBATCHPROCESS' AND type = 'PACKAGE'
AND   (UPPER(text) LIKE '%FUNCTION%' OR UPPER(text) LIKE '%PROCEDURE%'
    OR UPPER(text) LIKE '%P_LABEL%'  OR UPPER(text) LIKE '%_BRA%'
    OR text LIKE '%&&TARGET_BRANCH_PK%' OR text LIKE '%&&REFERENCE_BRANCH_PK%')
ORDER  BY line;
```
Read: every branch constant; every entry point and its arguments; **whether `f_executegroup` has
`P_LABEL`**. When possible also export the **full** spec (J-E4b, same query without the `AND (…)`): it is
the constants dictionary (group constants by function, product, branch).

### J-E5 — Label lookup present `Env: both` ✅ both 2026-09-29
```sql
SELECT owner, object_name, object_type, status FROM all_objects WHERE object_name = 'PKG_BOXUTILITY';
```
Expect: `BOX_SYS` (and `BOX_FE`), `VALID`.

### J-E6 — Where the MBJ properties table is, and what code names it `Env: both` 🆕
```sql
SELECT owner, table_name FROM all_tables WHERE table_name LIKE '%MBJ_PROPERTIES%';

SELECT owner, name, type, line, text FROM all_source
WHERE  UPPER(text) LIKE '%MBJ_PROPERTIES%'
ORDER  BY owner, name, type, line;
```
Why: an earlier search for `T_MBJ_PROPERTIES` returned 0 rows, but that pattern cannot match
`T_BOX_MBJ_PROPERTIES_S`. 0 rows here too → no visible PL/SQL reads it; the Unix runner may (ask the BOX
team).

### J-E7 — Auth code `Env: both`
Reuse FE **Q-G3c** ([`fe-config-mining.md`](fe-config-mining.md)). Tier 2 = 44.

### J-E8 — Engine core versions `Env: both` 🆕
```sql
SELECT owner, name, type, COUNT(*) AS lines, MAX(line) AS last_line FROM all_source
WHERE  name IN ('PKG_BATCHPROCESS','PKG_GMBATCHPROCESS') GROUP BY owner, name, type ORDER BY owner, name, type;
```
Compare with the repo's latest copy (highest `r` folder). Different line counts = different versions; the
agent then cites the environment's copy, or says it cannot.

---

## C — Catalog (groups, events, entries)

### J-C1 — BOX groups `Env: both` ✅ Tier 2 2026-09-29 (51 rows)
```sql
SELECT PK, GROUPDESCRIP FROM &&CATALOG_OWNER.T_PGT_BR_EVE_S
WHERE  UPPER(GROUPDESCRIP) LIKE 'BOX%' ORDER BY PK;
```

### J-C2 — A group's events, in order, with their size `Env: both` ✅ both 2026-09-29
```sql
SELECT x.ORDERTOEXECUTE, x.EVENTCODE, e.NAME, e.FK_INSTRUMENT,
       (SELECT COUNT(*) FROM &&CATALOG_OWNER.T_PGT_UPDATE_S u WHERE u.FK_PARENT = x.EVENTCODE) AS update_rows
FROM   &&CATALOG_OWNER.T_PGT_BR_EVE_EXT_S x
JOIN   &&CATALOG_OWNER.T_PGT_EVE_S e ON e.PK = x.EVENTCODE
WHERE  x.FK_PARENT = &&GROUP_PK
ORDER  BY x.ORDERTOEXECUTE;
```
Expect: no two rows with the same `ORDERTOEXECUTE`. Duplicates → another metamodel relationship is
mixed in: add `AND x.FK_OWNER_OBJ = … AND x.FK_EXTENSION = …` (Tier 1: `12709.4` / `39007.4`, derived
per environment).

### J-C3 — An event's entries `Env: both` ✅ Tier 1 2026-09-29 (`MC_UPDATETYPE`, `VAL_CCY_AL_COL` added since, named from the repo DML)
```sql
SELECT FK_PARENT, TXFUNCNAME, ORDERTOEXEC, MC_UPDATETYPE, ACCT_AL_COL, CCY_AL_COL, DREG_AL_COL,
       VAL_AL_COL, VAL_CCY_AL_COL, MC_DRCR
FROM   &&CATALOG_OWNER.T_PGT_UPDATE_S
WHERE  FK_PARENT = &&EVENT_PK
ORDER  BY ORDERTOEXEC;
```
Read (chain doc L5): `MC_UPDATETYPE = 'U'` rows first, then postings; `MC_DRCR` 1 = debit, 0 = credit.

### J-C4 — An event's query (FROM, WHERE, SELECT) `Env: both` 🆕
```sql
SELECT * FROM &&CATALOG_OWNER.T_PGT_TABLE_S WHERE FK_PARENT = &&EVENT_PK;
SELECT * FROM &&CATALOG_OWNER.T_PGT_COND_S  WHERE FK_PARENT = &&EVENT_PK;
SELECT * FROM &&CATALOG_OWNER.T_PGT_COLS_S  WHERE FK_PARENT = &&EVENT_PK;
```
The join column is assumed `FK_PARENT` (as in `T_PGT_UPDATE_S`) `[inferred]`; if 0 rows, `DESCRIBE` the
tables. Look for the placeholders `#BRANCH#`, `#LABEL#`, `#INSTRUMENT#`, `#EV_DATE#` in the conditions.
Until this runs, the repo snapshot `data_eventsheader_<PK>.sql` is the source (say so).

### J-C5 — Catalog fingerprint of every BOX group `Env: both` 🆕
```sql
SELECT g.PK, g.GROUPDESCRIP,
       COUNT(DISTINCT x.EVENTCODE) AS events,
       COUNT(u.FK_PARENT)          AS update_rows
FROM   &&CATALOG_OWNER.T_PGT_BR_EVE_S g
LEFT JOIN &&CATALOG_OWNER.T_PGT_BR_EVE_EXT_S x ON x.FK_PARENT = g.PK
LEFT JOIN &&CATALOG_OWNER.T_PGT_UPDATE_S     u ON u.FK_PARENT = x.EVENTCODE
WHERE  UPPER(g.GROUPDESCRIP) LIKE 'BOX%'
GROUP  BY g.PK, g.GROUPDESCRIP ORDER BY g.PK;
```
Compare `REF` and `TGT` line by line: a group missing, or with other counts, is a catalog gap.

---

## R — Reference branch (what an onboarded BOX branch runs)

### J-R1 — The reference environment's jobs: `db.conf` + `shell.conf` `Env: REF` 🆕
The operator copies both files **unchanged** into `runs/_reference/<env>/` (Tier 1 PROD:
[`runs/_reference/tier1-prod/`](../../../runs/_reference/tier1-prod/README.md)); then

```bash
python3 scripts/parse_job_confs.py runs/_reference/<env>/        # -> jobs-inventory.csv
```

Read `jobs-inventory.csv` with `family = BOX`, **whatever the name** (old `GMBOX…` jobs included; the
`box_reason` column says why each is BOX). The reference branch's jobs: its token (`LB` for SLB, `ES` Madrid),
its branch constant in `db.conf` arguments (e.g. `CST_PK_BRANC_LND`), or its banner (`SLB - FRA`). **Keep the
generic jobs** (`GMBX0…`, branch-level `GMBOX<CC>…`, check dummies, ALM, monitor): they carry no product,
and some no branch, but the target needs their equivalent too. For `mbjbox.sh` jobs the branch / product / book
come from their MBJ row (J-R2), not from the line.

### J-R2 — The reference branch's MBJ properties `Env: REF` 🆕
```sql
SELECT * FROM BOX_ACC.T_BOX_MBJ_PROPERTIES_S WHERE FK_BRANCH = &&REFERENCE_BRANCH_PK ORDER BY JOB_NAME;
```
`FK_BRANCH` / `JOB_NAME` assumed from [`box-data-model.md`](../box-data-model.md); `DESCRIBE` if it fails.
Cross-check: every `JOB_NAME` here should have a `db.conf` or `shell.conf` line (J-R1) — for `mbjbox.sh` jobs
this row is where their branch, instrument, book and group come from `[inferred]` — and the reverse.

### J-R3 — The reference branch's books per instrument `Env: REF`
Reuse FE **Q-10** ([`fe-config-mining.md`](fe-config-mining.md)) with the reference branch.

### J-R4 — The reference branch's Control-M jobs `Env: REF` (repos — Devin)
From the Control-M folder repos: every job whose name is in J-R1, with `When`, `eventsToWaitFor`,
`eventsToAdd` and its folder, as `J-R4-controlm-REF.csv` (`job, folder, file:line, when, waits_for,
emits`). Plus the check jobs whose in-conditions name one of them (04-add-book §2.2).

---

## T — Target readiness

| ID | Question | How | Expect today (NY_SCH, Tier 2) |
|---|---|---|---|
| **J-T1** | Is the target branch a wrapper constant? | J-E4 in `TGT` | ✅ `cst_pk_bra_nysch = 20007.4` (`PGT_NY`) |
| **J-T2** | Can the target's wrapper receive a book? | J-E4: `P_LABEL` in `f_executegroup` | ❌ 5 arguments — open question for the BOX Lead |
| **J-T3** | Which target BOX labels exist? | the book register (skill `set-up-book-labels`) | none yet (`XNY..` to create) |
| **J-T4** | Any MBJ properties rows for the target? | J-R2 with `&&TARGET_BRANCH_PK` in `TGT` | expect 0 |
| **J-T5** | Any BOX jobs for the target? | J-R1 on the target's `db.conf` + `shell.conf` (`runs/_reference/<target env>/`) | expect 0 (not in BOX yet) |
| **J-T6** | Are the reference's groups in the target catalog? | J-C5 in both, compared | 2735.65 ✅; the rest 🆕 |
| **J-T7** | Is the target's FE configuration in place? | the FE agent's run status (Q-01, step 11) | in progress |

### J-T3 — The target's BOX labels `Env: TGT`
**Not a query of this agent:** skill [`set-up-book-labels`](../../../skills/set-up-book-labels/SKILL.md) owns
it (FE catalogue **Q-10f**) and writes `runs/<BRANCH>/<env>/books/books-register.csv`. Read the register: a
book `exists` has its label PK; a book `to_create` stays `OPEN` in the job matrix until the BOX FE team has run
the skill's proposal.

### J-T3b — A created label resolves through the lookup the jobs use `Env: TGT` 🆕
```sql
SELECT '&&LABEL_CODE' AS code, BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('&&LABEL_CODE') AS label_pk FROM dual;
```
Must return the label's PK once it exists.

---

## X — Explain (used on demand)

### J-X1 — A package's source in an environment `Env: as asked`
```sql
SELECT line, text FROM all_source
WHERE  owner = '&&OWNER' AND name = '&&PACKAGE' AND type = 'PACKAGE BODY'
AND    line BETWEEN &&FROM_LINE AND &&TO_LINE ORDER BY line;
```
Use when the repo copy may not be what is deployed (chain doc L6). No rows → cite the repo copy and say so.

### J-X3 — What `mbjbox.sh` does with a job name `Env: as asked` (Unix) 🆕
Not a query: the operator copies `bin/mbjbox.sh` from the Unix app tree into `runs/_reference/<env>/`. Read it
for where an MBJ job's branch, instrument, book and group come from (expected: `T_BOX_MBJ_PROPERTIES_S` by
`JOB_NAME`) and what it calls in the database.

### J-X2 — A group by name `Env: as asked`
```sql
SELECT PK, GROUPDESCRIP FROM &&CATALOG_OWNER.T_PGT_BR_EVE_S
WHERE  UPPER(GROUPDESCRIP) LIKE UPPER('%&&TEXT%') ORDER BY PK;
```
