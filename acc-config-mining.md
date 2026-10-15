# Query catalogue — BOX ACC branch config (the BOX - Accounting SIGOM screens)

The queries [`sigom-box-acc-configs-agent`](../../../agents/sigom-box-acc-configs-agent/AGENT.md) runs (or hands to
the operator) in its **gap run**. Branch-agnostic: every query is parameterised. Its own IDs (`A-…`); it does not
read the FE catalogue ([`fe-config-mining.md`](fe-config-mining.md)) or the jobs one.

**Source of the screen queries** `[read: SIGOM traces via operator, Confluence "Sigom BOX ACC configurations"
checklist, 2026-10-07]`: each `A-0n` below starts from the query SIGOM itself runs when the screen opens (GBO and
BOX side), with explicit column aliases added so the CSV headers are unambiguous, and the branch / instrument
filters added. **Columns not in a trace are not assumed** — those queries say `SELECT *`.

`[2026-10-14]` The full column lists of both systems, the identity values, keys, sequences and code behaviour are now
known ([`box-acc-model.md`](../box-acc-model.md)); added: the **pre-checks** (`A-P1`–`A-P6`, the structure is what the
agent expects), the **usage in GBO production** (`A-U0`–`A-U5`, what the target has configured and uses), concrete
`A-04e` / `A-10b` / `A-10c` / `A-10d`, owner and list-extension filters on every list read, the A-11 rulings.

**Order in a run:** gate (A-G…) → pre-checks (A-P…) → usage in GBO production (A-U…) → the screens (A-0…, A-10, A-11).

## Conventions

Placeholders `&&NAME` (SQL Developer substitution). Results: `01-evidence/<ID>-<short-name>[-REF|-TGT].csv`.

| Placeholder | Meaning | From |
|---|---|---|
| `&&TARGET_BRANCH_PK` | the target branch (`T_PGT_BRANCH_S`) | inputs (NY_SCH `20007.4`) |
| `&&TARGET_GROUP_PK` | its branch **group** (`FK_LOCALGROUP`) | **A-G1** in the target tier — never typed |
| `&&REFERENCE_BRANCH_PK` | the reference branch | inputs (SLB `20087.4`) |
| `&&REFERENCE_GROUP_PK` | its group | **A-G1** in the reference tier |
| `&&INSTRUMENT_PKS` | the approved instruments, comma list (`T_PGT_SUB_PRODUCT_S`) | inputs (registry `instruments` → PKs) |
| `&&GROUP_PKS` | the reference's ACC event groups | **A-08a** |
| `&&ACCOUNT_CODES` | the target's GBO account codes in use | A-03a + A-04e, kept to those in use (A-U2 / A-U3) |
| `&&REFERENCE_ACCOUNT_CODES` | the reference's BOX account codes | A-03b + A-04b |
| `&&USAGE_FROM`, `&&USAGE_TO` 🆕 | the usage window (`YYYY-MM-DD`, `TO` exclusive) | asked — default the last full quarter |

| Env tag | Where |
|---|---|
| `REF` | the reference branch's tier (SLB: **Tier 1**) — every query naming a `REFERENCE_*` value |
| `TGT` | the target tier (NY_SCH: **Tier 2**) — its BOX target **and** its GBO (the branch's GBO data lives there) |
| `both` | run in each, two CSVs (`-REF`, `-TGT`), compared |
| `GBO-PROD` 🆕 | **GBO production** — what the target branch has configured and **uses** today (pre-checks `A-U…`, `[operator, 2026-10-14]`) |

**Three reading rules** `[2026-10-14]` ([`box-acc-model.md`](../box-acc-model.md) §2–3), in every query below:
1. **Owner + extension, always.** A row is the configuration only with the exact positive `FK_OWNER_OBJ` (and
   `FK_EXTENSION` for lists and arrays). The topic and condition lists are extensions of the **portfolio-property**
   object; the link-array tables are shared by many objects.
2. **Negative owners are test / deleted rows** `[operator, 2026-10-14]`: excluded, counted (A-P4), never compared or
   copied.
3. **`COUNT(*)`, never `NUM_ROWS`** — the optimizer statistics are years old on several tables.

**Owner objects and extensions** `[read: SIGOM traces, 2026-10-07; confirmed: metamodel M1 + rows M2 / M3, DB
PRE-PROD, 2026-10-14]` — an `A-P2` / `A-P3` result that disagrees wins:

| Screen | BOX `FK_OWNER_OBJ` | GBO `FK_OWNER_OBJ` |
|---|---|---|
| Condition Port Properties | `35000197.65` | `12638.4` |
| Config. Local Properties | `35000194.65` — arrays in `T_BOX_LINK_ARRAY_X`: local topics `35001814.65`, global topics `35003724.65`, internal topics `35003725.65`, conditions `35001818.65` | `12642.4` — `PGT_SYS.T_PGT_LINK_ARRAY_X`: **one** topic array `38192.4`, conditions `38196.4` |
| Portfolio Properties | `35000170.65` — lists: global `35001510.65`, local `35001513.65`, internal `35001518.65` (`T_BOX_ACCT_LIST_TOPIC_S`), conditions `35001514.65` (`…_LIST_COND_S`) | `12646.4` — lists `38249.4`, `38329.4`, `38422.4`; conditions `38335.4` |
| Cross Account Config | `35000189.65` | `18051.4` |
| Accounting Topics | `35000179.65` | `11980.4` |
| Standard Historic | `35000180.65` | `11873.4` |
| Global Accounts | `35000169.65` (date rules: `T_BOX_ACCT_PARENT_DATE_S`, same owner, extension `35001497.65`) | `11910.4` |
| Event Grouping (shared `PGT_PRC`) | `12709.4` | — |
| Event Config (shared `PGT_PRC`) | `12713.4` | — |
| MBJ Properties | `35000182.65` (J-T8) | — |
| Net Contract | **null** on every row (copied by a PL) | — |
| Conf Instru Type / Net CCS PlanBS (A-11) | `35000292.65` / `35000348.65` | — |

The add-product checklist's `PKG_ACCTCONST.CST_OWNER_PORTFOLIO = 35000194.65` is the **local-properties** object;
`PKG_ACCTPROP` names it `CST_OWN_CONF_LOCAL` and the portfolio-property object `CST_OWN_PORTFOLIO = 35000170.65`
`[read: code, 2026-10-14]`.

---

## Gate

### A-G1 — The branch and its group `Env: both`

```sql
SELECT b.PK AS branch_pk, b.DESCRIPTION AS branch, b.FK_LOCALGROUP AS group_pk, g.DESCRIPTION AS branch_group
FROM   PGT_STC.T_PGT_BRANCH_S b
LEFT   JOIN PGT_STC.T_PGT_BRANCH_GROUP_S g ON g.PK = b.FK_LOCALGROUP
WHERE  b.PK = &&BRANCH_PK;          -- TGT: &&TARGET_BRANCH_PK ; REF: &&REFERENCE_BRANCH_PK

-- (b) TGT: every branch of the target's group — a group shared with a branch already in BOX may need no rows
SELECT PK AS branch_pk, DESCRIPTION AS branch FROM PGT_STC.T_PGT_BRANCH_S WHERE FK_LOCALGROUP = &&TARGET_GROUP_PK;
```

### A-G2 — The ACC objects, owners, extensions, pre-commits `Env: TGT` (GOM_GLB_SYS — no BOX grant needed)

The module-parameterised queries 2 and 3 of [`sigom-metamodel.md`](../sigom-metamodel.md) §11 with
`&&MODULE_PK = 35000006.65`; then the four local-properties link arrays:

```sql
SELECT e.PK AS fk_extension, e.FIELD, t.PK_NAME AS target_object, t.BASIC_STORAGE AS target_table
FROM   GOM_GLB_SYS.T__EXT_DEF_S e
LEFT   JOIN GOM_GLB_SYS.T__OBJ_DEF_S t ON t.PK = e.FK_OBJECT
WHERE  e.FK_PARENT = 35000194.65 ORDER BY e.PK;     -- expect apLocalTopicArray, apGlobalTopicArray, apInternalTopicArray, apCondArray
```

### A-G3 — The GBO accounting objects `Env: TGT`

```sql
SELECT PK, PK_NAME, BASIC_STORAGE, EXT_STORAGE, PRE_COMMIT_PROC
FROM   GOM_GLB_SYS.T__OBJ_DEF_S
WHERE  PK IN (12638.4, 12642.4, 11980.4, 11873.4, 11910.4)
   OR  BASIC_STORAGE IN ('T_PGT_ACCT_PORT_PROP_S', 'T_PGT_CROSS_ACCTCONF_S')
   OR  BASIC_STORAGE LIKE 'T\_PGT\_ACCT\_LIST%' ESCAPE '\';
```

Gives the GBO portfolio-properties object and **its topic / condition list tables** (A-04e needs them — not assumed).
`[2026-10-14]` Known: `T_PGT_ACCT_LIST_TOPIC_S` / `T_PGT_ACCT_LIST_COND_S`, rows owned by `12646.4` with the
extensions above.

---

## Pre-checks — the structure is what the agent expects `[2026-10-14]`

Run after the gate, before any screen query, in **each** tier the run reads (`-REF`, `-TGT`). A failure stops the
run with the finding — never "missing → create" on a structure the run has not confirmed. Values expected:
[`box-acc-model.md`](../box-acc-model.md).

### A-P1 — The ACC tables are readable, with live counts `Env: both`

```sql
SELECT 'PORT_PROP' AS tbl, COUNT(*) AS n FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S
UNION ALL SELECT 'LIST_TOPIC',     COUNT(*) FROM BOX_ACC.T_BOX_ACCT_LIST_TOPIC_S
UNION ALL SELECT 'LIST_COND',      COUNT(*) FROM BOX_ACC.T_BOX_ACCT_LIST_COND_S
UNION ALL SELECT 'CONF_LO_PROP',   COUNT(*) FROM BOX_ACC.T_BOX_CONF_LO_PROP_S
UNION ALL SELECT 'LINK_ARRAY_X',   COUNT(*) FROM BOX_ACC.T_BOX_LINK_ARRAY_X
UNION ALL SELECT 'CROSS_ACCTCONF', COUNT(*) FROM BOX_ACC.T_BOX_CROSS_ACCTCONF_S
UNION ALL SELECT 'CONDPAR_PROP',   COUNT(*) FROM BOX_ACC.T_BOX_CONDPAR_PROP_S
UNION ALL SELECT 'TOPICS',         COUNT(*) FROM BOX_ACC.T_BOX_ACCT_TOPICS_S
UNION ALL SELECT 'HISTSTD',        COUNT(*) FROM BOX_ACC.T_BOX_ACCT_HISTSTD
UNION ALL SELECT 'GLTA',           COUNT(*) FROM BOX_ACC.T_BOX_ACCT_GLTA_S
UNION ALL SELECT 'PARENT_DATE',    COUNT(*) FROM BOX_ACC.T_BOX_ACCT_PARENT_DATE_S
UNION ALL SELECT 'CONF_INSTRUM_TYPE', COUNT(*) FROM BOX_ACC.T_BOX_CONF_INSTRUM_TYPE_S
UNION ALL SELECT 'NETCCS_BSPLAN',  COUNT(*) FROM BOX_ACC.T_BOX_NETCCS_BSPLAN_S
UNION ALL SELECT 'NETCONTRACT',    COUNT(*) FROM BOX_ACC.T_BOX_NETCONTRACT_S;
```
**Check:** no ORA-00942 (a missing grant is a stop, asked for by name: `BOX_ACC_RD`); topics, conditions and standard
historic > 0 in both tiers (empty global catalogues mean the wrong schema or no grant, not "to create").

### A-P2 — The identity values the rows carry `Env: both`

```sql
SELECT 'PORT_PROP' AS tbl, FK_OWNER_OBJ, FK_EXTENSION, COUNT(*) AS n FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL SELECT 'LIST_TOPIC',     FK_OWNER_OBJ, FK_EXTENSION, COUNT(*) FROM BOX_ACC.T_BOX_ACCT_LIST_TOPIC_S GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL SELECT 'LIST_COND',      FK_OWNER_OBJ, FK_EXTENSION, COUNT(*) FROM BOX_ACC.T_BOX_ACCT_LIST_COND_S  GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL SELECT 'CONF_LO_PROP',   FK_OWNER_OBJ, FK_EXTENSION, COUNT(*) FROM BOX_ACC.T_BOX_CONF_LO_PROP_S    GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL SELECT 'LINK_ARRAY_X',   FK_OWNER_OBJ, FK_EXTENSION, COUNT(*) FROM BOX_ACC.T_BOX_LINK_ARRAY_X      GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL SELECT 'CROSS_ACCTCONF', FK_OWNER_OBJ, FK_EXTENSION, COUNT(*) FROM BOX_ACC.T_BOX_CROSS_ACCTCONF_S  GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL SELECT 'GLTA',           FK_OWNER_OBJ, FK_EXTENSION, COUNT(*) FROM BOX_ACC.T_BOX_ACCT_GLTA_S       GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL SELECT 'PARENT_DATE',    FK_OWNER_OBJ, FK_EXTENSION, COUNT(*) FROM BOX_ACC.T_BOX_ACCT_PARENT_DATE_S GROUP BY FK_OWNER_OBJ, FK_EXTENSION
ORDER  BY 1, 2, 3;
```
**Check:** every pair is in the owner table above (an unknown pair → stop and ask); negative owners → A-P4.

### A-P3 — The metamodel declares the same objects and extensions `Env: TGT`

[`sigom-metamodel.md`](../sigom-metamodel.md) §11 query 3 with `&&MODULE_PK = 35000006.65`, kept to the objects
`35000169.65, 35000170.65, 35000189.65, 35000194.65, 35000197.65, 35000179.65, 35000180.65, 35000292.65,
35000348.65`. **Check:** the extension PKs and targets of the owner table; the pre-commit procedures of
`box-acc-model.md` §5.

### A-P4 — Negative owners (test / deleted rows) `Env: both`

A-P2's rows with `FK_OWNER_OBJ < 0`, plus the GBO tables the run reads (`GBO-PROD`):
```sql
SELECT 'GBO TOPICS' AS tbl, COUNT(*) AS n FROM PGT_ACT.T_PGT_ACCT_TOPICS_S WHERE FK_OWNER_OBJ < 0
UNION ALL SELECT 'GBO GLTA',      COUNT(*) FROM PGT_ACT.T_PGT_ACCT_GLTA_S      WHERE FK_OWNER_OBJ < 0
UNION ALL SELECT 'GBO PORT_PROP', COUNT(*) FROM PGT_ACT.T_PGT_ACCT_PORT_PROP_S WHERE FK_OWNER_OBJ < 0
UNION ALL SELECT 'GBO CROSS',     COUNT(*) FROM PGT_SYS.T_PGT_CROSS_ACCTCONF_S WHERE FK_OWNER_OBJ < 0;
```
**Check:** listed in the matrix's evidence; excluded from every comparison.

### A-P5 — PK generation will not collide `Env: TGT`

```sql
SELECT 'PORT_PROP' AS tbl, (SELECT MAX(TRUNC(PK)) FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S) AS max_pk,
       (SELECT LAST_NUMBER FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = 'BOX_ACC' AND SEQUENCE_NAME = 'SPK_T_BOX_ACCT_PORT_PROP_S') AS seq_next,
       (SELECT NEXT_VAL FROM BOX_ACC.T___SEQUENCE WHERE PK_NAME = 'T_BOX_ACCT_PORT_PROP_S') AS counter_next FROM dual
UNION ALL SELECT 'CONF_LO_PROP', (SELECT MAX(TRUNC(PK)) FROM BOX_ACC.T_BOX_CONF_LO_PROP_S),
       (SELECT LAST_NUMBER FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = 'BOX_ACC' AND SEQUENCE_NAME = 'SPK_T_BOX_CONF_LO_PROP_S'),
       (SELECT NEXT_VAL FROM BOX_ACC.T___SEQUENCE WHERE PK_NAME = 'T_BOX_CONF_LO_PROP_S') FROM dual
UNION ALL SELECT 'LINK_ARRAY_X', (SELECT MAX(TRUNC(PK)) FROM BOX_ACC.T_BOX_LINK_ARRAY_X),
       (SELECT LAST_NUMBER FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = 'BOX_ACC' AND SEQUENCE_NAME = 'SPK_T_BOX_LINK_ARRAY_X'),
       (SELECT NEXT_VAL FROM BOX_ACC.T___SEQUENCE WHERE PK_NAME = 'T_BOX_LINK_ARRAY_X') FROM dual
UNION ALL SELECT 'CROSS_ACCTCONF', (SELECT MAX(TRUNC(PK)) FROM BOX_ACC.T_BOX_CROSS_ACCTCONF_S),
       (SELECT LAST_NUMBER FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = 'BOX_ACC' AND SEQUENCE_NAME = 'SPK_T_BOX_CROSS_ACCTCONF_S'),
       (SELECT NEXT_VAL FROM BOX_ACC.T___SEQUENCE WHERE PK_NAME = 'T_BOX_CROSS_ACCTCONF_S') FROM dual
UNION ALL SELECT 'GLTA', (SELECT MAX(TRUNC(PK)) FROM BOX_ACC.T_BOX_ACCT_GLTA_S),
       (SELECT LAST_NUMBER FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = 'BOX_ACC' AND SEQUENCE_NAME = 'SPK_T_BOX_ACCT_GLTA_S'),
       (SELECT NEXT_VAL FROM BOX_ACC.T___SEQUENCE WHERE PK_NAME = 'T_BOX_ACCT_GLTA_S') FROM dual
UNION ALL SELECT 'PARENT_DATE', (SELECT MAX(TRUNC(PK)) FROM BOX_ACC.T_BOX_ACCT_PARENT_DATE_S),
       (SELECT LAST_NUMBER FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = 'BOX_ACC' AND SEQUENCE_NAME = 'SPK_T_BOX_ACCT_PARENT_DATE_S'),
       (SELECT NEXT_VAL FROM BOX_ACC.T___SEQUENCE WHERE PK_NAME = 'T_BOX_ACCT_PARENT_DATE_S') FROM dual
UNION ALL SELECT 'LIST_TOPIC', (SELECT MAX(TRUNC(PK)) FROM BOX_ACC.T_BOX_ACCT_LIST_TOPIC_S),
       (SELECT LAST_NUMBER FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = 'BOX_ACC' AND SEQUENCE_NAME = 'SPK_T_BOX_ACCT_LIST_TOPIC_S'),
       (SELECT NEXT_VAL FROM BOX_ACC.T___SEQUENCE WHERE PK_NAME = 'T_BOX_ACCT_LIST_TOPIC_S') FROM dual
UNION ALL SELECT 'LIST_COND', (SELECT MAX(TRUNC(PK)) FROM BOX_ACC.T_BOX_ACCT_LIST_COND_S),
       (SELECT LAST_NUMBER FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = 'BOX_ACC' AND SEQUENCE_NAME = 'SPK_T_BOX_ACCT_LIST_COND_S'),
       (SELECT NEXT_VAL FROM BOX_ACC.T___SEQUENCE WHERE PK_NAME = 'T_BOX_ACCT_LIST_COND_S') FROM dual;
```
**Check:** for each table the run will write, the next number (sequence or counter — whichever mode `F_GetPK` uses)
is above `max_pk`; a missing sequence (`SPK_T_BOX_CONF_LO_PROP_S` has no file in the repo) is reported. Seed data with
hard-coded PKs makes some sequences lag (conditions, topics, standard historic in PRE-PROD).

### A-P6 — The package versions deployed `Env: both`

```sql
SELECT ORDEREXECUTED, ID, FILENAME, DATEEXECUTED, EXECTYPE
FROM   BOX_ACC.DATABASECHANGELOG
WHERE  LOWER(FILENAME) LIKE '%pkg_acctprop%' OR LOWER(FILENAME) LIKE '%pkg_acctprecommit%'
   OR  LOWER(FILENAME) LIKE '%pkg_sigom_cov%'
ORDER  BY ORDEREXECUTED DESC;
```
**Check:** the latest `PKG_ACCTPROP` is **r0.0.8** — only then do global and internal topics come from the local
property (`box-acc-model.md` §4). An older version → the run says so and the screen-2 / screen-4 reading changes
(global / internal topics at instrument level); asked, not assumed.

---

## Usage in GBO production — what the target has configured and uses `[2026-10-14]`

`Env: GBO-PROD`, read-only, aggregates only — **no portfolio, counterparty or entity names**, no raw movement rows.
`&&USAGE_FROM` / `&&USAGE_TO`: the window, asked (default: the last full quarter, so month-ends are in). A product
with no trade in the window shows nothing — **no movement is not "not needed"** (A-U3 covers open balances).

### A-U0 — The movements table is read by its partition `Env: GBO-PROD`

```sql
SELECT 'PARTITION KEY' AS kind, k.NAME AS table_name, CAST(NULL AS VARCHAR2(128)) AS index_name, k.COLUMN_POSITION, k.COLUMN_NAME
FROM   ALL_PART_KEY_COLUMNS k WHERE k.OWNER = 'PGT_ACT' AND k.OBJECT_TYPE = 'TABLE' AND k.NAME IN ('T_PGT_ACCT_MOV_S', 'T_PGT_ACCT_RULER')
UNION ALL
SELECT 'INDEX', i.TABLE_NAME, i.INDEX_NAME, i.COLUMN_POSITION, i.COLUMN_NAME
FROM   ALL_IND_COLUMNS i WHERE i.TABLE_OWNER = 'PGT_ACT' AND i.TABLE_NAME IN ('T_PGT_ACCT_MOV_S', 'T_PGT_ACCT_KEY_S')
ORDER  BY 2, 1, 3, 4;
```
**Check:** the movements table is partitioned on `REGDATE` (expected). Another key → A-U2 / A-U4 filter on it; the
window query is never run without a partition or index filter (1.1 bn rows).

### A-U1 — The target's configuration, per instrument and list `Env: GBO-PROD`

```sql
-- (a) portfolio properties and their topic -> account lists, per list (FK_BRANCH: group or branch - both listed)
SELECT pp.FK_BRANCH, pp.FK_INSTRUMENT, sp.DESCRIPTION AS instrument, pp.STATUS, lt.FK_EXTENSION AS list_ext,
       COUNT(DISTINCT pp.PK) AS n_port_prop, MAX(pp.INIVALPCDATE) AS latest_inivalpcdate,
       COUNT(lt.PK) AS n_topic_rows, COUNT(DISTINCT lt.FK_TOPIC) AS n_topics,
       COUNT(DISTINCT lt.FK_GLTA) AS n_accounts, COUNT(lt.PK) - COUNT(lt.FK_GLTA) AS rows_without_account
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp
LEFT   JOIN PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S lt
       ON lt.FK_PARENT = pp.PK AND lt.FK_OWNER_OBJ = 12646.4 AND lt.FK_EXTENSION IN (38249.4, 38329.4, 38422.4)
LEFT   JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = pp.FK_INSTRUMENT
WHERE  pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
GROUP  BY pp.FK_BRANCH, pp.FK_INSTRUMENT, sp.DESCRIPTION, pp.STATUS, lt.FK_EXTENSION
ORDER  BY instrument, pp.STATUS, list_ext;

-- (b) the conditions they use (counts only - no portfolio / counterparty values)
SELECT pp.FK_INSTRUMENT, lc.FK_CONDITION, cp.NOM_FUNC, cp.DESCRIPTION AS cond, COUNT(*) AS n,
       COUNT(lc.FK_PORTFOLIO) AS with_portfolio, COUNT(lc.FK_COUNTERPARTY) AS with_counterparty,
       COUNT(lc.FK_INSTRUMTYPE) AS with_instrtype, COUNT(lc.FK_STRATEGY) AS with_strategy,
       COUNT(lc.VALUE_FUNC) AS with_value_func
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp
JOIN   PGT_ACT.T_PGT_ACCT_LIST_COND_S lc ON lc.FK_PARENT = pp.PK AND lc.FK_OWNER_OBJ = 12646.4 AND lc.FK_EXTENSION = 38335.4
LEFT   JOIN PGT_SYS.T_PGT_CONDPAR_PROP_S cp ON cp.PK = lc.FK_CONDITION
WHERE  pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
GROUP  BY pp.FK_INSTRUMENT, lc.FK_CONDITION, cp.NOM_FUNC, cp.DESCRIPTION
ORDER  BY 1, 2;

-- (c) local properties and their arrays (GBO: one topic array 38192.4, conditions 38196.4)
SELECT lp.PK AS lo_prop_pk, lp.FK_BRANCH, lp.FK_INSTRUMENT, sp.DESCRIPTION AS instrument, lp.INIVALPCDATE,
       x.FK_EXTENSION, COUNT(x.FK_BS) AS n_linked
FROM   PGT_SYS.T_PGT_CONF_LO_PROP_S lp
LEFT   JOIN PGT_SYS.T_PGT_LINK_ARRAY_X x ON x.FK_PARENT = lp.PK AND x.FK_OWNER_OBJ = 12642.4
LEFT   JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = lp.FK_INSTRUMENT
WHERE  lp.FK_OWNER_OBJ = 12642.4 AND lp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
GROUP  BY lp.PK, lp.FK_BRANCH, lp.FK_INSTRUMENT, sp.DESCRIPTION, lp.INIVALPCDATE, x.FK_EXTENSION
ORDER  BY instrument, lp.INIVALPCDATE, x.FK_EXTENSION;

-- (d) Cross Account Config rows: the target's, and every branch's count (GBO had 17 rows in all, PRE-PROD)
SELECT 'TARGET' AS scope, INSTRUMENT, COUNT(*) AS n FROM PGT_SYS.T_PGT_CROSS_ACCTCONF_S
WHERE  FK_OWNER_OBJ = 18051.4 AND BRANCH = &&TARGET_BRANCH_PK GROUP BY INSTRUMENT
UNION ALL
SELECT 'ALL BRANCHES', BRANCH, COUNT(*) FROM PGT_SYS.T_PGT_CROSS_ACCTCONF_S WHERE FK_OWNER_OBJ = 18051.4 GROUP BY BRANCH
ORDER  BY 1, 2;
```
**Check:** (a) says whether GBO keys portfolio properties on the group (expected) or the branch; (d) whether the
target has any Cross Account Config in GBO — none → screen 3 has no GBO source (asked).

### A-U2 — What the target posted, per instrument × portfolio property × topic × account `Env: GBO-PROD`

```sql
SELECT m.FK_BRANCH, m.FK_INSTRUMENT, sp.DESCRIPTION AS instrument, m.FK_PROPERTIES,
       MAX(CASE WHEN pp.PK IS NULL THEN 'N' ELSE 'Y' END) AS is_port_prop,
       t.CODE AS topic_code, t.DESCRIPTION AS topic, a.CODE AS account_code,
       COUNT(*) AS n_mov, MIN(m.REGDATE) AS first_date, MAX(m.REGDATE) AS last_date
FROM   PGT_ACT.T_PGT_ACCT_MOV_S m
LEFT   JOIN PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp ON pp.PK = m.FK_PROPERTIES AND pp.FK_OWNER_OBJ = 12646.4
LEFT   JOIN PGT_ACT.T_PGT_ACCT_TOPICS_S    t  ON t.PK  = m.FK_TOPIC
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S      a  ON a.PK  = m.FK_GLTA
LEFT   JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S    sp ON sp.PK = m.FK_INSTRUMENT
WHERE  m.FK_BRANCH IN (&&TARGET_BRANCH_PK, &&TARGET_GROUP_PK)
AND    m.REGDATE >= DATE '&&USAGE_FROM' AND m.REGDATE < DATE '&&USAGE_TO'
GROUP  BY m.FK_BRANCH, m.FK_INSTRUMENT, sp.DESCRIPTION, m.FK_PROPERTIES, t.CODE, t.DESCRIPTION, a.CODE
ORDER  BY instrument, m.FK_PROPERTIES, topic_code;
```
Run one month first; the quarter if it is fast. **Gives:** the instruments that post (vs the approved ones), the
**distinct GBO topics used** (the short list for the topic mapping), the **account codes used** (A-10a / A-10b).
`is_port_prop` mostly `Y` confirms `FK_PROPERTIES` = the portfolio property (metamodel `pPropPos`).

### A-U3 — Portfolio properties × topics still holding a balance `Env: GBO-PROD`

```sql
SELECT k.FK_BRANCH, k.FK_INSTRUMENT, k.FK_PROPERTIES, t.CODE AS topic_code, COUNT(*) AS n_keys,
       SUM(CASE WHEN NVL(k.AMOUNT_LOC, 0) <> 0 OR NVL(k.AMOUNT_CCY, 0) <> 0 THEN 1 ELSE 0 END) AS n_keys_open,
       MAX(k.MAXDATE) AS last_maxdate
FROM   PGT_ACT.T_PGT_ACCT_KEY_S k
LEFT   JOIN PGT_ACT.T_PGT_ACCT_TOPICS_S t ON t.PK = k.FK_TOPIC
WHERE  k.FK_BRANCH IN (&&TARGET_BRANCH_PK, &&TARGET_GROUP_PK)
GROUP  BY k.FK_BRANCH, k.FK_INSTRUMENT, k.FK_PROPERTIES, t.CODE
HAVING SUM(CASE WHEN NVL(k.AMOUNT_LOC, 0) <> 0 OR NVL(k.AMOUNT_CCY, 0) <> 0 THEN 1 ELSE 0 END) > 0
ORDER  BY 2, 3, 4;
```
`AMOUNT_CCY` / `AMOUNT_LOC` read as the key's balance — INFERRED, confirmed with the first result. Covers what is in
use without a movement in the window (maturities, revaluation at month-end).

### A-U4 — Configured vs used, per list `Env: GBO-PROD`

```sql
WITH used AS (
  SELECT m.FK_PROPERTIES, m.FK_TOPIC, m.FK_GLTA, COUNT(*) AS n
  FROM   PGT_ACT.T_PGT_ACCT_MOV_S m
  WHERE  m.FK_BRANCH IN (&&TARGET_BRANCH_PK, &&TARGET_GROUP_PK)
  AND    m.REGDATE >= DATE '&&USAGE_FROM' AND m.REGDATE < DATE '&&USAGE_TO'
  GROUP  BY m.FK_PROPERTIES, m.FK_TOPIC, m.FK_GLTA),
conf AS (
  SELECT pp.PK AS prop_pk, lt.FK_EXTENSION AS list_ext, lt.FK_TOPIC, lt.FK_GLTA
  FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp
  JOIN   PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S lt
         ON lt.FK_PARENT = pp.PK AND lt.FK_OWNER_OBJ = 12646.4 AND lt.FK_EXTENSION IN (38249.4, 38329.4, 38422.4)
  WHERE  pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK))
SELECT status, list_ext, COUNT(*) AS combinations, SUM(n) AS movements
FROM  (SELECT CASE WHEN c.prop_pk IS NULL THEN '1 used, not configured'
                   WHEN u.FK_PROPERTIES IS NULL THEN '4 configured, not used'
                   WHEN NVL(c.FK_GLTA, -1) = NVL(u.FK_GLTA, -1) THEN '2 used = configured'
                   ELSE '3 used, other account' END AS status, c.list_ext, u.n
       FROM   used u
       FULL   OUTER JOIN conf c ON c.prop_pk = u.FK_PROPERTIES AND c.FK_TOPIC = u.FK_TOPIC)
GROUP  BY status, list_ext ORDER BY status, list_ext;
```
**Reading:** many "used, not configured" → GBO resolves some accounts by another route (Cross Account Config, an
NY-specific table): understood before any account is proposed. "Configured, not used" → asked before it is copied.

### A-U5 — GBO production vs the tier the run reads `Env: GBO-PROD` and `TGT`

A-U1 (d) and the counts of A-U1 (a) / (c) in both: the gap run reads GBO in the target tier; a difference with
production is reported (production wins for "what is used").

---

## The screens

### 1. Condition Port Properties — global, verify

**A-01 `Env: both`** — the catalogue (BOX trace):
```sql
SELECT T1.PK AS cond_pk, T1.TYPE_COND, T1.NOM_FUNC, T2.PK AS param_pk, T2.DESCRIPTION AS param,
       T1.DESCRIPTION AS cond, T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   BOX_ACC.T_BOX_CONDPAR_PROP_S T1, PGT_SYS.PGT_DOMAINS T2
WHERE  T1.FK_PARAMFIELD = T2.PK(+) AND T1.FK_OWNER_OBJ = 35000197.65;
```
**Check:** every condition the reference's local properties use (A-02b, `apCondArray`) is in **A-01-TGT** (same PK
and `NOM_FUNC`). Missing → the gap matrix says so; a new condition is a BOX team request, never inserted here.

### 2. Config. Local Properties — branch-group keyed, copy from the reference

**A-02a `Env: REF`** — the reference group's rows for the instruments (BOX trace + filters):
```sql
SELECT T1.PK AS lo_prop_pk, T2.PK AS instrument_pk, T2.DESCRIPTION AS instrument, T3.PK AS group_pk,
       T3.DESCRIPTION AS branch_group, T1.INIVALPCDATE, T1.DESCRIPTION, T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   BOX_ACC.T_BOX_CONF_LO_PROP_S T1, PGT_SYS.T_PGT_SUB_PRODUCT_S T2, PGT_STC.T_PGT_BRANCH_GROUP_S T3
WHERE  T1.FK_INSTRUMENT = T2.PK(+) AND T1.FK_BRANCH = T3.PK(+) AND T1.FK_OWNER_OBJ = 35000194.65
AND    T1.FK_BRANCH = &&REFERENCE_GROUP_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
ORDER  BY T2.DESCRIPTION, T1.INIVALPCDATE;
```
**A-02b `Env: REF`** — their four arrays (`T_BOX_LINK_ARRAY_X`, filtered on owner **and** extension — never
`FK_PARENT` alone, metamodel §4):
```sql
SELECT x.FK_PARENT AS lo_prop_pk, x.FK_EXTENSION, x.FK_BS AS linked_pk,
       tp.CODE AS topic_code, tp.DESCRIPTION AS topic, cp.NOM_FUNC AS cond_func, cp.DESCRIPTION AS cond
FROM   BOX_ACC.T_BOX_LINK_ARRAY_X x
LEFT   JOIN BOX_ACC.T_BOX_ACCT_TOPICS_S  tp ON tp.PK = x.FK_BS
LEFT   JOIN BOX_ACC.T_BOX_CONDPAR_PROP_S cp ON cp.PK = x.FK_BS
WHERE  x.FK_OWNER_OBJ = 35000194.65
AND    x.FK_PARENT IN (SELECT PK FROM BOX_ACC.T_BOX_CONF_LO_PROP_S
                       WHERE FK_BRANCH = &&REFERENCE_GROUP_PK AND FK_INSTRUMENT IN (&&INSTRUMENT_PKS))
ORDER  BY x.FK_PARENT, x.FK_EXTENSION, x.FK_BS;
```
(`FK_EXTENSION` → array: local topics `35001814.65`, global topics `35003724.65`, internal topics `35003725.65`,
conditions `35001818.65` `[confirmed: M1 / M2, 2026-10-14]`. A topic **and** a condition joining the same `FK_BS` is
possible — the extension says which one is meant. `f_GenTopicCond` (r0.0.8) turns them into the portfolio
property's lists global → `35001510.65`, local → `35001513.65`, internal → `35001518.65`, conditions →
`35001514.65` — [`box-acc-model.md`](../box-acc-model.md) §4.)

**A-02c `Env: TGT`** — the same two queries with `&&TARGET_GROUP_PK`: what the target's group already has (expected
none, unless the group is shared — A-G1 (b)).

**A-02d `Env: TGT`** — the target's GBO local properties (GBO trace), for comparison only. GBO local properties have
**one** topic array (`38192.4`) and conditions (`38196.4`); BOX has three topic arrays — GBO's cannot be translated,
the reference's BOX rows are the source `[confirmed: M1, 2026-10-14]`:
```sql
SELECT T1.PK AS lo_prop_pk, T2.PK AS instrument_pk, T2.DESCRIPTION AS instrument, T3.PK AS group_pk,
       T3.DESCRIPTION AS branch_group, T1.INIVALPCDATE, T1.DESCRIPTION
FROM   PGT_SYS.T_PGT_CONF_LO_PROP_S T1, PGT_SYS.T_PGT_SUB_PRODUCT_S T2, PGT_STC.T_PGT_BRANCH_GROUP_S T3
WHERE  T1.FK_INSTRUMENT = T2.PK(+) AND T1.FK_BRANCH = T3.PK(+) AND T1.FK_OWNER_OBJ = 12642.4
AND    T1.FK_BRANCH = &&TARGET_GROUP_PK;
```

### 3. Cross Account Config — branch keyed, from GBO (translated)

**A-03a `Env: TGT`** — the target branch's GBO rows (GBO trace + filter):
```sql
SELECT T1.PK, T2.PK AS branch_pk, T2.DESCRIPTION AS branch, T3.PK AS instrument_pk, T3.DESCRIPTION AS instrument,
       T4.PK AS currency_pk, T4.SHORTNAME AS currency, T5.PK AS entity_pk, T5.DESCRIPTION AS entity,
       T6.PK AS account_pk, T6.CODE AS account_code, T7.PK AS topic_pk, T7.CODE AS topic_code
FROM   PGT_SYS.T_PGT_CROSS_ACCTCONF_S T1, PGT_STC.T_PGT_BRANCH_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3,
       PGT_STC.T_PGT_CURRENCY_S T4, PGT_STC.T_PGT_ENTITY_S T5, PGT_ACT.T_PGT_ACCT_GLTA_S T6,
       PGT_ACT.T_PGT_ACCT_TOPICS_S T7
WHERE  T1.BRANCH = T2.PK(+) AND T1.INSTRUMENT = T3.PK(+) AND T1.CURRENCY = T4.PK(+) AND T1.ENTITY = T5.PK(+)
AND    T1.ACCOUNT = T6.PK(+) AND T1.TOPIC = T7.PK(+) AND T1.FK_OWNER_OBJ = 18051.4
AND    T1.BRANCH = &&TARGET_BRANCH_PK AND T1.INSTRUMENT IN (&&INSTRUMENT_PKS);
```
**A-03b `Env: REF`** — **how the reference translated GBO into BOX**: the same GBO query with
`&&REFERENCE_BRANCH_PK`, and the BOX trace with the same filter:
```sql
SELECT T1.PK, T2.PK AS branch_pk, T3.PK AS instrument_pk, T3.DESCRIPTION AS instrument, T4.SHORTNAME AS currency,
       T5.PK AS entity_pk, T6.PK AS account_pk, T6.CODE AS account_code, T7.PK AS topic_pk, T7.CODE AS topic_code,
       T1.ACC_TYPE
FROM   BOX_ACC.T_BOX_CROSS_ACCTCONF_S T1, PGT_STC.T_PGT_BRANCH_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3,
       PGT_STC.T_PGT_CURRENCY_S T4, PGT_STC.T_PGT_ENTITY_S T5, BOX_ACC.T_BOX_ACCT_GLTA_S T6,
       BOX_ACC.T_BOX_ACCT_TOPICS_S T7
WHERE  T1.FK_BRANCH = T2.PK(+) AND T1.FK_INSTRUMENT = T3.PK(+) AND T1.FK_CURRENCY = T4.PK(+)
AND    T1.FK_ENTITY = T5.PK(+) AND T1.FK_ACCOUNT = T6.PK(+) AND T1.FK_TOPIC = T7.PK(+) AND T1.FK_OWNER_OBJ = 35000189.65
AND    T1.FK_BRANCH = &&REFERENCE_BRANCH_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS);
```
Compared row by row (instrument, currency, entity, account **code**): is the BOX account the GBO account (same code,
same PK?), which BOX topic replaced each GBO topic, and how `ACC_TYPE` was set — the GBO screen has no `ACC_TYPE`.
`ACC_TYPE` is a plain number: `0` Posición Vencida, `1` Posición Viva, `2` Balance de Posición Viva `[read: code,
2026-10-14]`. That pattern is the translation rule; what it does not explain is a question. ⚠️ GBO had **17** Cross
Account Config rows for all branches (PRE-PROD): the target may have none (A-U1 d) — then screen 3 has no GBO source
and is asked.

**A-03c `Env: TGT`** — the BOX trace with `&&TARGET_BRANCH_PK`: rows already there (expected none).

### 4. Portfolio Properties — branch-group keyed; never copied from GBO

**A-04a `Env: REF`** — the reference group's portfolio properties (BOX trace + filters):
```sql
SELECT T1.PK AS port_prop_pk, T2.PK AS group_pk, T2.DESCRIPTION AS branch_group, T3.PK AS instrument_pk,
       T3.DESCRIPTION AS instrument, T1.INIVALPCDATE, T1.STATUS, T1.DESCRIPTION
FROM   BOX_ACC.T_BOX_ACCT_PORT_PROP_S T1, PGT_STC.T_PGT_BRANCH_GROUP_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3
WHERE  T1.FK_BRANCH = T2.PK AND T1.FK_INSTRUMENT = T3.PK AND T1.FK_OWNER_OBJ = 35000170.65
AND    T1.FK_BRANCH = &&REFERENCE_GROUP_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
ORDER  BY T3.DESCRIPTION, T1.INIVALPCDATE;
```
**A-04b `Env: REF`** — their generated lists (topic → account per list; conditions). The lists are **extensions
of the portfolio-property object** (owner `35000170.65`): global `35001510.65`, local `35001513.65`, internal
`35001518.65`, conditions `35001514.65` — filtered and reported per list `[confirmed: M2, 2026-10-14]`:
```sql
SELECT l.FK_PARENT AS port_prop_pk, l.FK_EXTENSION AS list_ext,
       CASE l.FK_EXTENSION WHEN 35001510.65 THEN 'global' WHEN 35001513.65 THEN 'local'
                           WHEN 35001518.65 THEN 'internal' END AS list_name,
       tp.CODE AS topic_code, tp.DESCRIPTION AS topic, a.CODE AS account_code
FROM   BOX_ACC.T_BOX_ACCT_LIST_TOPIC_S l
LEFT   JOIN BOX_ACC.T_BOX_ACCT_TOPICS_S tp ON tp.PK = l.FK_TOPIC
LEFT   JOIN BOX_ACC.T_BOX_ACCT_GLTA_S   a  ON a.PK  = l.FK_GLTA
WHERE  l.FK_OWNER_OBJ = 35000170.65 AND l.FK_EXTENSION IN (35001510.65, 35001513.65, 35001518.65)
AND    l.FK_PARENT IN (SELECT PK FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S
                       WHERE FK_OWNER_OBJ = 35000170.65
                       AND FK_BRANCH = &&REFERENCE_GROUP_PK AND FK_INSTRUMENT IN (&&INSTRUMENT_PKS))
ORDER  BY l.FK_PARENT, l.FK_EXTENSION, tp.CODE;

SELECT c.FK_PARENT AS port_prop_pk, c.FK_CONDITION, cp.NOM_FUNC, c.VALUE_FUNC, c.FK_INSTRUMTYPE, c.FK_DEALTREAT,
       c.FK_COLLATERALIND, c.FK_STRATEGY, c.STRUCTIND, c.FK_STRUCTYPE, c.FK_MICROTYPE, c.FK_TRDSUBTYPE,
       CASE WHEN c.FK_PORTFOLIO    IS NULL THEN 'N' ELSE 'Y' END AS has_portfolio,      -- value not extracted
       CASE WHEN c.FK_COUNTERPARTY IS NULL THEN 'N' ELSE 'Y' END AS has_counterparty    -- value not extracted
FROM   BOX_ACC.T_BOX_ACCT_LIST_COND_S c
LEFT   JOIN BOX_ACC.T_BOX_CONDPAR_PROP_S cp ON cp.PK = c.FK_CONDITION
WHERE  c.FK_OWNER_OBJ = 35000170.65 AND c.FK_EXTENSION = 35001514.65
AND    c.FK_PARENT IN (SELECT PK FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S
                       WHERE FK_OWNER_OBJ = 35000170.65
                       AND FK_BRANCH = &&REFERENCE_GROUP_PK AND FK_INSTRUMENT IN (&&INSTRUMENT_PKS))
ORDER  BY c.FK_PARENT, c.FK_CONDITION;
```
A condition selecting by portfolio or counterparty needs the target's own value (its folders / counterparties) — a
question per condition, never the reference's value.
**A-04c `Env: TGT`** — A-04a / A-04b with `&&TARGET_GROUP_PK`: already there (expected none).

**A-04d `Env: TGT`** — the target's **GBO** portfolio properties (GBO trace + filter) — for its **accounts** only:
```sql
SELECT T1.PK AS port_prop_pk, T2.PK AS group_pk, T3.PK AS instrument_pk, T3.DESCRIPTION AS instrument,
       T1.INIVALPCDATE, T1.STATUS, T1.DESCRIPTION
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S T1, PGT_STC.T_PGT_BRANCH_GROUP_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3
WHERE  T1.FK_BRANCH = T2.PK AND T1.FK_INSTRUMENT = T3.PK AND T1.FK_OWNER_OBJ = 12646.4
AND    T1.FK_BRANCH = &&TARGET_GROUP_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS);
```
**A-04e `Env: TGT`** — its topic → account lists, per list (GBO: owner `12646.4`, extensions `38249.4` global,
`38329.4` local, `38422.4` internal — paired with BOX's by field name) `[confirmed: M1 / M3, 2026-10-14]`:
```sql
SELECT l.FK_PARENT AS port_prop_pk, l.FK_EXTENSION AS list_ext,
       CASE l.FK_EXTENSION WHEN 38249.4 THEN 'global' WHEN 38329.4 THEN 'local' WHEN 38422.4 THEN 'internal' END AS list_name,
       tp.CODE AS gbo_topic_code, a.CODE AS account_code
FROM   PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S l
LEFT   JOIN PGT_ACT.T_PGT_ACCT_TOPICS_S tp ON tp.PK = l.FK_TOPIC
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S   a  ON a.PK  = l.FK_GLTA
WHERE  l.FK_OWNER_OBJ = 12646.4 AND l.FK_EXTENSION IN (38249.4, 38329.4, 38422.4)
AND    l.FK_PARENT IN (SELECT PK FROM PGT_ACT.T_PGT_ACCT_PORT_PROP_S
                       WHERE FK_OWNER_OBJ = 12646.4
                       AND FK_BRANCH = &&TARGET_GROUP_PK AND FK_INSTRUMENT IN (&&INSTRUMENT_PKS))
ORDER  BY l.FK_PARENT, l.FK_EXTENSION, tp.CODE;
```
GBO **topics** never enter BOX: each GBO topic goes through the GBO → BOX topic mapping (open), and only its
**account** is kept. With A-U2 / A-U4, only the topics and accounts **in use** are taken forward.

### 5. Net Contract — Madrid real only

**A-05 `Env: TGT`** — rows for the target (expected none; the screen is not configured for any other branch):
```sql
SELECT T1.PK, T1.FK_BRANCH, T1.FK_INSTRUMENT, T1.FK_CURRENCY, T1.FK_FOLDER, T1.FK_SOURCE_DEAL, T1.FK_SECURITY,
       T1.CONTRACT
FROM   BOX_ACC.T_BOX_NETCONTRACT_S T1 WHERE T1.FK_BRANCH = &&TARGET_BRANCH_PK ORDER BY T1.PK;
```
For Madrid real the rows are copied from GBO `PGT_ES.T_MAD_NETOHOSTCONTRACT_S` by a PL `[stated: Confluence]` —
not this agent.

### 6. Accounting Topics — global, verify

**A-06 `Env: both`** (BOX trace):
```sql
SELECT T1.PK AS topic_pk, T1.CODE, T1.DESCRIPTION, T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   BOX_ACC.T_BOX_ACCT_TOPICS_S T1 WHERE T1.FK_OWNER_OBJ = 35000179.65 ORDER BY T1.CODE;
```
**Check:** every topic of A-02b and A-04b is in A-06-TGT (same PK and `CODE`).

### 7. Standard Historic — global, verify

**A-07 `Env: both`** (BOX trace):
```sql
SELECT T1.PK, T1.HISTDESCR, T1.HISTCODE, T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   BOX_ACC.T_BOX_ACCT_HISTSTD T1 WHERE T1.FK_OWNER_OBJ = 35000180.65 ORDER BY T1.HISTDESCR;
```
**Check:** REF and TGT hold the same `(PK, HISTCODE)` set; a difference is reported, not fixed.

### 8. Event Grouping — global (shared `PGT_PRC`); verify, then ask

**A-08a `Env: REF`** — the reference's ACC event groups for the instruments (its MBJ rows):
```sql
SELECT DISTINCT m.FK_GROUP AS group_pk, g.GROUPDESCRIP, m.FK_INSTRUMENT AS instrument_pk
FROM   BOX_ACC.T_BOX_MBJ_PROPERTIES_S m
JOIN   PGT_PRC.T_PGT_BR_EVE_S g ON g.PK = m.FK_GROUP
WHERE  m.FK_BRANCH = &&REFERENCE_BRANCH_PK AND m.FK_PARENT IS NULL AND m.FK_OWNER_OBJ = 35000182.65
AND    m.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
ORDER  BY g.GROUPDESCRIP;
```
**A-08b `Env: both`** — those groups (trace) and their events in order:
```sql
SELECT T1.PK AS group_pk, T1.GROUPDESCRIP, T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   PGT_PRC.T_PGT_BR_EVE_S T1 WHERE T1.FK_OWNER_OBJ = 12709.4 AND T1.PK IN (&&GROUP_PKS);

SELECT x.FK_PARENT AS group_pk, x.ORDERTOEXECUTE, x.EVENTCODE
FROM   PGT_PRC.T_PGT_BR_EVE_EXT_S x WHERE x.FK_PARENT IN (&&GROUP_PKS) ORDER BY x.FK_PARENT, x.ORDERTOEXECUTE;
```
**Check:** every group and its events (same order) is in TGT. **Ask** (charter): keep the global groups, or a
**branch copy** — same events and order, the branch's own PK and name — per group.

### 9. Event Config — global, verify

**A-09 `Env: both`** (trace), for the events of A-08b:
```sql
SELECT T1.PK AS event_pk, T1.NAME, T2.PK AS instrument_pk, T2.DESCRIPTION AS instrument, T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   PGT_PRC.T_PGT_EVE_S T1, PGT_SYS.T_PGT_SUB_PRODUCT_S T2
WHERE  T1.FK_INSTRUMENT = T2.PK(+) AND T1.FK_OWNER_OBJ = 12713.4
AND    T1.PK IN (SELECT EVENTCODE FROM PGT_PRC.T_PGT_BR_EVE_EXT_S WHERE FK_PARENT IN (&&GROUP_PKS))
ORDER  BY T1.NAME;
```
A branch copy of a group reuses these events — they are never copied.

### 10. Global Accounts — from GBO

**A-10a `Env: TGT`** — the GBO accounts the target's GBO configuration uses (A-03a `account_code` + A-04e
`account_code`), as GBO has them (GBO trace + filter):
```sql
SELECT T1.PK AS account_pk, T1.CODE, T1.SHORTNAME, T1.DESCRIPTION, T2.PK AS gltatype_pk, T2.DESCRIPTION AS gltatype,
       T3.PK AS direction_pk, T3.DESCRIPTION AS direction, T1.LOC_CODE, T1.FXADJUSTIND, T1.HOSTINTERFIND
FROM   PGT_ACT.T_PGT_ACCT_GLTA_S T1, PGT_SYS.PGT_DOMAINS T2, PGT_SYS.PGT_DOMAINS T3
WHERE  T1.FK_GLTATYPE = T2.PK(+) AND T1.FK_DIRECTION = T3.PK(+) AND T1.FK_OWNER_OBJ = 11910.4
AND    T1.CODE IN (&&ACCOUNT_CODES);
```
**A-10b `Env: TGT`** — the same codes in BOX: present / missing, and duplicates (no unique key on `CODE`):
```sql
SELECT T1.CODE, COUNT(*) AS n_rows, MIN(T1.PK) AS account_pk, MAX(T1.FK_BRANCHGROUP) AS branchgroup,
       MAX(T2.CODE) AS gltatype_code, MAX(T3.CODE) AS direction_code
FROM   BOX_ACC.T_BOX_ACCT_GLTA_S T1, PGT_SYS.PGT_DOMAINS T2, PGT_SYS.PGT_DOMAINS T3
WHERE  T1.FK_GLTATYPE = T2.PK(+) AND T1.FK_DIRECTION = T3.PK(+) AND T1.FK_OWNER_OBJ = 35000169.65
AND    T1.CODE IN (&&ACCOUNT_CODES)
GROUP  BY T1.CODE ORDER BY T1.CODE;
```
**A-10c `Env: REF`** — **how the reference's accounts went from GBO to BOX**: the reference's BOX accounts used by
A-03b / A-04b, joined by `CODE` to the GBO table:
```sql
SELECT b.CODE, b.PK AS box_pk, g.PK AS gbo_pk,
       CASE WHEN TRUNC(b.PK) = TRUNC(g.PK) THEN 'Y' ELSE 'N' END AS same_pk_number,
       CASE WHEN NVL(b.SHORTNAME, '~') = NVL(g.SHORTNAME, '~') THEN 'Y' ELSE 'N' END AS same_shortname,
       CASE WHEN NVL(b.DESCRIPTION, '~') = NVL(g.DESCRIPTION, '~') THEN 'Y' ELSE 'N' END AS same_description,
       b.FXADJUSTIND AS box_fxadj, g.FXADJUSTIND AS gbo_fxadj, b.FK_BRANCHGROUP AS box_bg, g.FK_BRANCHGROUP AS gbo_bg,
       bt.CODE AS box_gltatype, gt.CODE AS gbo_gltatype, bd.CODE AS box_direction, gd.CODE AS gbo_direction,
       LENGTH(g.CODE) AS len_code, LENGTH(g.SHORTNAME) AS len_short, LENGTH(g.DESCRIPTION) AS len_desc
FROM   BOX_ACC.T_BOX_ACCT_GLTA_S b
JOIN   PGT_ACT.T_PGT_ACCT_GLTA_S g ON g.CODE = b.CODE AND g.FK_OWNER_OBJ = 11910.4
LEFT   JOIN PGT_SYS.PGT_DOMAINS bt ON bt.PK = b.FK_GLTATYPE
LEFT   JOIN PGT_SYS.PGT_DOMAINS gt ON gt.PK = g.FK_GLTATYPE
LEFT   JOIN PGT_SYS.PGT_DOMAINS bd ON bd.PK = b.FK_DIRECTION
LEFT   JOIN PGT_SYS.PGT_DOMAINS gd ON gd.PK = g.FK_DIRECTION
WHERE  b.FK_OWNER_OBJ = 35000169.65 AND b.CODE IN (&&REFERENCE_ACCOUNT_CODES)
ORDER  BY b.CODE;
```
GLTA type and direction are `PGT_DOMAINS` values owned by BOX's **Acct Indicator** (`35000173.65`) / **GLTA Type**
(`35000174.65`) and by GBO's own objects: translated **by `CODE`** — the pattern this query shows decides how a
missing account is created. **Lengths:** BOX `CODE` / `SHORTNAME` / `DESCRIPTION` hold 20 / 20 / 50 characters — a
GBO value longer than that is a finding, never truncated. An account is **one row** (+ an optional date rule,
`T_BOX_ACCT_PARENT_DATE_S`) — `p_AccountPrecommit` reads nothing else `[read: code, 2026-10-14]`.

**A-10d `Env: TGT`** — the target's GBO date rules for those accounts (copied only if they exist):
```sql
SELECT a.CODE, d.VALDATE, d.CODELOC, d.HOSTINTERF, p.CODE AS parent_account_code
FROM   PGT_ACT.T_PGT_ACCT_PARENT_DATE_S d
JOIN   PGT_ACT.T_PGT_ACCT_GLTA_S a ON a.PK = d.FK_PARENT AND a.FK_OWNER_OBJ = 11910.4
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S p ON p.PK = d.ACCT_PARENT
WHERE  d.FK_OWNER_OBJ = 11910.4 AND a.CODE IN (&&ACCOUNT_CODES)
ORDER  BY a.CODE, d.VALDATE;
```

### 11. MBJ Config — not this agent

The ACC jobs (`shell.conf`, Control-M, MBJ rows) belong with the planned `box-acc-jobs-agent`. The reference's rows
are J-R2 in [`box-jobs-queries.md`](box-jobs-queries.md).

---

## Not in the Confluence checklist — rule in or out

**A-11 `Env: REF`** — for each object of A-G2 keyed on `pBranch` / `pLocalGroup` and **not** in the walk above:
`SELECT COUNT(*)` of its `BASIC_STORAGE` for the reference branch (or group). Rows for the reference and none
expected to be transactional → a candidate step, asked; transactional (movements, documents) → out, with the reason.

**Rulings so far** `[2026-10-14]` ([`box-acc-model.md`](../box-acc-model.md) §8):

| Object | Ruling |
|---|---|
| Conf Instru Type (`T_BOX_CONF_INSTRUM_TYPE_S`, branch + instrument + `CODE` / `VALUE` / `TYPE`) | **candidate** — counted for the reference, asked (BOX team) |
| Net CCS PlanBS (`T_BOX_NETCCS_BSPLAN_S`, branch + account) | **candidate** for CCS — asked (BOX team) |
| GLTA Local Dep (`T_BOX_GLTA_LOCAL_S`, group) | check GBO's 2 rows (`T_PGT_GLTA_LOCAL_S`): one for the target's group? |
| Conf Acc By StdHist, Acct By Std Hist | 0 rows in PRE-PROD — out unless the reference has rows |
| Acct Key, Acct Key Group, Documents, Grouped Movements, Grouped Mov Config | runtime — out |
| Topic Group, Std Historic Group, Std Historic Source | global — verify |
| GBO ConcMis Balances / Mov (`15493.4` / `15494.4`) | no BOX table — BOX team (GBO ↔ MIS reconciliation replaced?) |
| GBO `PGT_NY.T_PGT_TOPICS_RR` (NY topic per instrument × buy/sell × near/far) | no BOX screen — BOX team |
