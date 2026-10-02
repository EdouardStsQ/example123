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
`T_BOX_MBJ_PROPERTIES_S`. **2026-10-01:** the reader is the Java program `MBJBOXACC.jar` (via `mbjbox.sh`)
`[stated: BOX dev]`, so 0 PL/SQL readers is expected; the first query still proves where the table is in each tier.

### J-E7 — Auth code `Env: both`
Reuse FE **Q-G3c** ([`fe-config-mining.md`](fe-config-mining.md)). Tier 2 = 44.

### J-E8 — Engine core versions `Env: both` 🆕
```sql
SELECT owner, name, type, COUNT(*) AS lines, MAX(line) AS last_line FROM all_source
WHERE  name IN ('PKG_BATCHPROCESS','PKG_GMBATCHPROCESS') GROUP BY owner, name, type ORDER BY owner, name, type;
```
Compare with the repo's latest copy (highest `r` folder). Different line counts = different versions; the
agent then cites the environment's copy, or says it cannot.

### J-E9 — The MBJ engine package `Env: both` 🆕
`MBJBOXACC.jar` calls **`PKG_BATCHPROCESS_MBJ`** `[stated: BOX dev via operator, 2026-10-01]` — not a branch
wrapper. Is it there, valid, and the same version in both tiers?
```sql
SELECT owner, object_name, object_type, status, last_ddl_time FROM all_objects
WHERE  object_name = 'PKG_BATCHPROCESS_MBJ' ORDER BY owner, object_type;

SELECT owner, name, type, COUNT(*) AS lines FROM all_source
WHERE  name = 'PKG_BATCHPROCESS_MBJ' GROUP BY owner, name, type;

-- branch-specific code inside it? (0 rows = branch agnostic, as far as the readable source shows)
SELECT owner, type, line, text FROM all_source
WHERE  name = 'PKG_BATCHPROCESS_MBJ' AND REGEXP_LIKE(UPPER(text), 'BRANC|CST_PK_BRA|22\.21|20087')
ORDER  BY owner, type, line;
```
Also its product-code map (`p_instrument = … THEN p_PROD := …`, [acc checklist §7.4](../../process/checklists/acc-add-product-checklist.md)):
every NY instrument must be in it.

---

## C — Catalog (groups, events, entries)

### J-C1 — BOX groups `Env: both` ✅ Tier 2 2026-09-29 (51 rows)
```sql
SELECT PK, GROUPDESCRIP FROM &&CATALOG_OWNER.T_PGT_BR_EVE_S
WHERE  UPPER(GROUPDESCRIP) LIKE 'BOX%' ORDER BY PK;
```

> **J-C queries confirm; the repo explains** `[2026-10-02]`. A group's events and an event's query and entries are
> committed in `cib-boxfin-dbboxfe` (FE) / `cib-boxacc-dbboxacc` (ACC) under `dml/03-PGT_PRC/<rX.Y.Z>/05_Static-Data/`
> (`data_groupevents_<PK>.sql`, `data_eventsheader_<PK>.sql`; newest release wins) — charter *read the repo first*.
> Use J-C2…J-C5 for what is **deployed** in one environment.

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

### J-C3g — Every entry of a group, in one query `Env: both` 🆕 (EXPLAIN *full* depth)
Replaces one J-C3 per event: a group of 7 events is **one** query, not 7.
```sql
SELECT x.ORDERTOEXECUTE, x.EVENTCODE, e.NAME AS event_name,
       u.ORDERTOEXEC, u.TXFUNCNAME, u.MC_UPDATETYPE, u.ACCT_AL_COL, u.CCY_AL_COL, u.DREG_AL_COL,
       u.VAL_AL_COL, u.VAL_CCY_AL_COL, u.MC_DRCR
FROM   &&CATALOG_OWNER.T_PGT_BR_EVE_EXT_S x
JOIN   &&CATALOG_OWNER.T_PGT_EVE_S e    ON e.PK = x.EVENTCODE
LEFT JOIN &&CATALOG_OWNER.T_PGT_UPDATE_S u ON u.FK_PARENT = x.EVENTCODE
WHERE  x.FK_PARENT = &&GROUP_PK
ORDER  BY x.ORDERTOEXECUTE, u.ORDERTOEXEC;
```

### J-C4g — Every event query of a group (FROM / WHERE / SELECT), in three queries `Env: both` 🆕
```sql
SELECT x.ORDERTOEXECUTE, t.* FROM &&CATALOG_OWNER.T_PGT_BR_EVE_EXT_S x
JOIN &&CATALOG_OWNER.T_PGT_TABLE_S t ON t.FK_PARENT = x.EVENTCODE WHERE x.FK_PARENT = &&GROUP_PK ORDER BY 1;
SELECT x.ORDERTOEXECUTE, c.* FROM &&CATALOG_OWNER.T_PGT_BR_EVE_EXT_S x
JOIN &&CATALOG_OWNER.T_PGT_COND_S  c ON c.FK_PARENT = x.EVENTCODE WHERE x.FK_PARENT = &&GROUP_PK ORDER BY 1;
SELECT x.ORDERTOEXECUTE, k.* FROM &&CATALOG_OWNER.T_PGT_BR_EVE_EXT_S x
JOIN &&CATALOG_OWNER.T_PGT_COLS_S  k ON k.FK_PARENT = x.EVENTCODE WHERE x.FK_PARENT = &&GROUP_PK ORDER BY 1;
```
Same `FK_PARENT` assumption as J-C4. Use J-C3 / J-C4 (one event) only when the question is about one event.

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
-- the SIGOM MBJ Config screen's own query [read 2026-10-01], made generic
SELECT t1.pk, t2.pk branch_pk, t2.description branch, t1.instanze, t1.job_name,
       t3.pk instr_pk, t3.description instrument, t4.pk group_pk, t4.groupdescrip,
       t5.pk label_pk, t5.code label_code, t6.pk sublabel_pk, t6.code sublabel_code,
       t1.concurrent_events, t1.concurrent_events_dependency, t1.workers, t1.tasks_per_worker,
       t1.workers_by_events, t1.mic_sender_type, t1.mic_file_type, t1.mic_eod, t1.mic_flow_mode,
       t1.monitor_types, t1.monitor_file_max_days, t1.monitor_file_pattern, t1.fk_parent, t1.fk_owner_obj,
       -- columns the screen does not show (DESCRIBE, 2026-10-01) - a new row needs them too
       t1.fk_extension, t1.return_data, t1.recover_manual_movs, t1.recover_reclassification_movs,
       t1.recover_regularization_movs, t1.fk_calendar
FROM   box_acc.t_box_mbj_properties_s t1, pgt_stc.t_pgt_branch_s t2, pgt_sys.t_pgt_sub_product_s t3,
       pgt_prc.t_pgt_br_eve_s t4, pgt_sys.pgt_domains t5, pgt_sys.pgt_domains t6
WHERE  t1.fk_branch = t2.pk(+) AND t1.fk_instrument = t3.pk(+) AND t1.fk_group = t4.pk(+)
AND    t1.fk_label = t5.pk(+) AND t1.fk_sublabel = t6.pk(+)
AND    t2.pk = &&REFERENCE_BRANCH_PK AND t1.fk_parent IS NULL AND t1.fk_owner_obj = 35000182.65
ORDER  BY t1.job_name;
```
Then the values the reference uses for the flags (what a new row copies) — and its calendars (never copied blind):
```sql
SELECT return_data, recover_manual_movs, recover_reclassification_movs, recover_regularization_movs,
       mic_eod, mic_flow_mode, mic_sender_type, mic_file_type, concurrent_events, workers, tasks_per_worker,
       COUNT(*) AS n_rows
FROM   box_acc.t_box_mbj_properties_s WHERE fk_branch = &&REFERENCE_BRANCH_PK
GROUP  BY return_data, recover_manual_movs, recover_reclassification_movs, recover_regularization_movs,
       mic_eod, mic_flow_mode, mic_sender_type, mic_file_type, concurrent_events, workers, tasks_per_worker
ORDER  BY n_rows DESC;

SELECT fk_calendar, COUNT(*) AS n_rows FROM box_acc.t_box_mbj_properties_s
WHERE  fk_branch = &&REFERENCE_BRANCH_PK GROUP BY fk_calendar;
```
Export to CSV. Label **descriptions are book names — keep them in the run folder only, never in `docs/`**
(`label_code` is enough to match `GMBX<n><CC><nn>`). Madrid (`22.21`): `SELECT COUNT(*) FROM box_acc.t_box_mbj_properties_s WHERE fk_branch = 22.21` gives the total
(SQL Developer shows 50 per fetch). MBJ rows are **ACC jobs only**. `FK_PARENT IS NULL` changes nothing
(same rows without it `[stated: operator, 2026-10-01]`); `INSTANZE` is always `AUKI` `[stated]`.
Cross-check: every `JOB_NAME` here should have a `db.conf` or `shell.conf` line (J-R1) — for `mbjbox.sh` jobs
this row is where their settings come from `[stated: BOX dev, 2026-10-01]` — read which columns hold branch,
instrument, book (`pLabel`) and group from these rows — and the reverse.

### J-R3 — The reference branch's books per instrument `Env: REF`
Reuse FE **Q-10** ([`fe-config-mining.md`](fe-config-mining.md)) with the reference branch.

### J-R3b — The reference branch's book labels (code + description) `Env: REF` 🆕
For `box-fe-jobs-agent`: the job descriptions carry the book's label description, swapped for the target book's.
```sql
SELECT CODE, DESCRIPTION FROM PGT_SYS.PGT_DOMAINS
WHERE  FK_OWNER_OBJ = 17910.4 AND CODE LIKE '&&REF_LABEL_PREFIX%'      -- SLB: XLB
ORDER  BY CODE;
```
→ `runs/<BRANCH>/<env>/fe-jobs/<instrument>/01-evidence/J-R3b-reference-books.csv`. Descriptions are book names:
run folder only.

### J-R4 — The reference branch's Control-M jobs `Env: REF` (repos — Devin)
**Use `scripts/find_jobs.py --branch <ref> --controlm <repo dirs> --out 01-evidence/J-R4-controlm-REF`** (one run
per side, FE and ACC) — it reads the JSON and orders the jobs. By hand only for what it reports missing.
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
| **J-T8** | Is the MBJ Config screen object in the target? | below, in `REF` and `TGT`, compared | same row both tiers — ✅ 2026-10-01 |

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

### J-T8 — The MBJ Config screen object `Env: both` 🆕
An empty `T_BOX_MBJ_PROPERTIES_S` says nothing about `FK_OWNER_OBJ`; the SIGOM object catalogue does
([sigom-metamodel](../sigom-metamodel.md)):
```sql
SELECT pk, pk_name, fk_parent AS module_pk, basic_storage, ext_storage,
       pre_commit_proc, fk_precommit, psavdll, psavfunc
FROM   gom_glb_sys.t__obj_def_s
WHERE  pk = 35000182.65
   OR  basic_storage = 'T_BOX_MBJ_PROPERTIES_S' OR ext_storage = 'T_BOX_MBJ_PROPERTIES_S';

-- its declared fields (count and list) - compare REF vs TGT
SELECT e.pk AS fk_extension, e.field, e.fk_kind, t.basic_storage AS target_table
FROM   gom_glb_sys.t__ext_def_s e LEFT JOIN gom_glb_sys.t__obj_def_s t ON t.pk = e.fk_object
WHERE  e.fk_parent = 35000182.65 ORDER BY e.pk;
```
**Pass:** one object row `35000182.65`, storage `T_BOX_MBJ_PROPERTIES_S`, in both tiers, same fields.
**Tier 1 vs Tier 2 run 2026-10-01: PASS** — `BOX - MBJ Properties`, module `35000006.65`, no pre-commit, 25 fields,
identical (evidence `runs/NY_SCH/tier2-pre/jobs/01-evidence/J-T8-mbj-screen-object-BOTH.md`). Read
`pre_commit_proc` too: whatever runs on save in the screen must also run (or be replayed) when rows are
inserted by script. Not found in `TGT` → the screen is not deployed there: a blocker for the BOX team.

### J-X3 — What `mbjbox.sh` does with a job name `Env: as asked` (Unix) 🆕
Not a query: the operator copies `bin/mbjbox.sh` from the Unix app tree into `runs/_reference/<env>/`.
**Tier 1 PROD read 2026-10-01** (chain doc L2): it only launches `java -jar MBJBOXACC.jar <JOB> <ODATE> 0000`
from `/appl/gm/bin/GBOCL_MBJBATCH`, config in `conf/BOX`. The binding is in the jar → J-X4.

### J-X4 — What `MBJBOXACC.jar` reads for a job `Env: as asked` (repo / Unix) 🆕
It reads `T_BOX_MBJ_PROPERTIES_S` and calls **`PKG_BATCHPROCESS_MBJ`** `[stated: BOX dev, 2026-10-01]` (J-E9).
Still to learn: **whether Tier 2's Unix server has it**, pointing at the Tier 2 database.

1. **Source** (Devin, `direct`, optional now): search the BOX repos for `MBJBOXACC`, `mbjConfDirectory`,
   `T_BOX_MBJ_PROPERTIES`, `PKG_BATCHPROCESS_MBJ`; cite file + line.
2. **Config** (operator): the **file names** in `/appl/gm/bin/GBOCL_MBJBATCH/conf/BOX` (`ls -l`). Copy a file's
   content only after removing passwords, users and connection strings (placeholders).
3. **A log** (operator): one PROD log `logs/BOX/<JOB>-<ODATE>-<date>.log` of a reference `mbjbox.sh` job —
   anonymise names; look for the table and the branch / instrument / label / group it loaded.

For Tier 2 ask:
does `/appl/gm/bin/GBOCL_MBJBATCH` exist there, and does its `conf/BOX` point at the Tier 2 database?

### J-X2 — A group by name `Env: as asked`
```sql
SELECT PK, GROUPDESCRIP FROM &&CATALOG_OWNER.T_PGT_BR_EVE_S
WHERE  UPPER(GROUPDESCRIP) LIKE UPPER('%&&TEXT%') ORDER BY PK;
```
