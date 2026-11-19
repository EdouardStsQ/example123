# Query catalogue — rebuilding a GBO report in BOX (`box-report-migration-agent`)

`[2026-11-18 — ADR 0028]` The queries the agent asks the operator to run, by ID. All **read-only**. Text as written:
only the `&&` parameters are substituted (SQL\*Plus / SQL Developer: `&&name.` before a `.` — e.g.
`&&gbo_schema..T_PGT_TOPICS_RR`). Each result is saved as it arrives as `01-evidence/<ID>-<short name>.csv`, except
where a query says **local**: trade-level results go to the run's `local/` folder (git-ignored, ADR 0028).

`Env`: **BOX** = the target environment, with the BOX account the run uses (`report-inputs.json` `accounts.box`;
it must reach `BOX_FE`, `BOX_ACC`, `BOX_TRD` and the shared schemas — R-P1 shows it); **GBO** = the GBO account
(`accounts.gbo`). A query that fails is reported with its error and the account — never rewritten against another
schema to make it pass.

## Pre-checks — can the account reach what the report needs?

### R-P1 — The objects the report reads `Env: BOX`

```sql
SELECT o.OWNER, o.OBJECT_NAME, o.OBJECT_TYPE, o.STATUS
FROM   ALL_OBJECTS o
WHERE  (o.OWNER, o.OBJECT_NAME) IN (
         ('BOX_FE', 'T_BOX_DATADEAL_S'), ('BOX_FE', 'T_BOX_DEAL_DATA_S'), ('BOX_FE', 'T_BOX_FLOW_DATA_S'),
         ('BOX_FE', 'T_BOX_MTM_DATA_S'), ('BOX_TRD', 'T_BOX_DEAL_S'),
         ('BOX_ACC', 'T_BOX_ACCT_LIST_TOPIC_S'), ('BOX_ACC', 'T_BOX_ACCT_GLTA_S'), ('BOX_ACC', 'T_BOX_ACCT_TOPICS_S'),
         ('BOX_ACC', 'T_BOX_ACCT_PORT_PROP_S'),
         ('PGT_PRG', 'PKG_CALENDAR'), ('PGT_PRG', 'PKG_PGTGENERAL'),
         ('PGT_STC', 'T_PGT_CURRENCY_S'), ('PGT_STC', 'T_PGT_CURR_PAIR_S'), ('PGT_MRK', 'T_PGT_QUOTE_REFERENCE_S'),
         ('PGT_SYS', 'PGT_DOMAINS'), ('PGT_SYS', 'T_PGT_EVENT_DEF_S'))
   OR  (o.OWNER = 'BOX_FE' AND (o.OBJECT_NAME LIKE 'T\_BOX\_%FINANCST\_S' ESCAPE '\'
                             OR o.OBJECT_NAME LIKE 'V\_BOX\_ENG%DATAMIS\_S' ESCAPE '\'
                             OR o.OBJECT_NAME LIKE 'T\_BOX\_%DATADEAL\_S' ESCAPE '\'))
   OR  o.OBJECT_NAME = 'PKG_ACCTGENERAL'
ORDER  BY 1, 2, 3;
```

A row missing = not visible to this account (or absent): named in the gap report, never assumed.

### R-P2 — The signatures of the shared functions `Env: BOX`

```sql
SELECT OWNER, PACKAGE_NAME, OBJECT_NAME, OVERLOAD, POSITION, ARGUMENT_NAME, DATA_TYPE, IN_OUT
FROM   ALL_ARGUMENTS
WHERE  PACKAGE_NAME IN ('PKG_CALENDAR', 'PKG_PGTGENERAL', 'PKG_ACCTGENERAL')
AND    OBJECT_NAME IN ('F_GOWORKDAYS', 'F_ISWORKDAY', 'P_GETCURRPAIRSPOTDATE', 'P_GETMATURITYDATE', 'F_GETACCTNO')
ORDER  BY 1, 2, 3, 4, 5;
```

## BOX — the columns and sample deals

### R-B1 — The columns of the BOX deal, flow, financial and MTM objects `Env: BOX`

Parameters: the slice's product tables (decision D2) — e.g. `&&financst_tables` = `'T_BOX_MMFINANCST_S',
'T_BOX_IRFINANCST_S'`, `&&mtm_views` = `'V_BOX_ENGMMDATAMIS_S', 'V_BOX_ENGIRDATAMIS_S'`, `&&datadeal_tables` =
`'T_BOX_MMDATADEAL_S', 'T_BOX_IRDATADEAL_S'` (codes: [`gbo-box-product-tables.csv`](../gbo-box-product-tables.csv)).

```sql
SELECT OWNER, TABLE_NAME, COLUMN_ID, COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
FROM   ALL_TAB_COLUMNS
WHERE  (OWNER = 'BOX_FE' AND (TABLE_NAME IN ('T_BOX_DATADEAL_S', 'T_BOX_DEAL_DATA_S', 'T_BOX_FLOW_DATA_S', 'T_BOX_MTM_DATA_S')
                           OR TABLE_NAME IN (&&financst_tables)
                           OR TABLE_NAME IN (&&mtm_views)
                           OR TABLE_NAME IN (&&datadeal_tables)))
   OR  (OWNER = 'BOX_TRD' AND TABLE_NAME = 'T_BOX_DEAL_S')
ORDER  BY 1, 2, 3;
```

### R-B2 — Sample deals, every column `Env: BOX` — written from R-B1

The agent writes the column list from R-B1 (saved in the run as `01-evidence/R-B2-<product>.sql` before it is run):
every column of `BOX_FE.T_BOX_DATADEAL_S`, **except** a text column whose name contains `FOLDER`, `PORTFOLIO`,
`COUNTERP` or `CPTY`, selected as `ORA_HASH(<column>) AS <column>_H` (no portfolio or counterparty name is ever
extracted). At most five deals per product, picked by the operator.

```sql
SELECT <columns from R-B1, names hashed as above>
FROM   BOX_FE.T_BOX_DATADEAL_S
WHERE  DEAL_ID IN (SELECT DEAL_ID FROM BOX_FE.T_BOX_DEAL_DATA_S WHERE FRONT_ID IN (&&front_ids))
ORDER  BY DEAL_ID;
```

The same for `T_BOX_DEAL_DATA_S` (one row per leg), `T_BOX_<CODE>FINANCST_S` and `V_BOX_ENG<CODE>DATAMIS_S` on the
same `DEAL_ID`s, for one process date.

### R-B3 — Where BOX records a cancellation or a decrease (field 21) `Env: BOX`

```sql
SELECT OWNER, TABLE_NAME
FROM   ALL_TABLES
WHERE  OWNER IN ('BOX_TRD', 'BOX_FE', 'BOX_ACC')
AND    (TABLE_NAME LIKE '%DATE%DEP%' OR TABLE_NAME LIKE '%CANCEL%' OR TABLE_NAME LIKE '%TERMIN%'
        OR TABLE_NAME LIKE '%EVENT%' OR TABLE_NAME LIKE '%STATUS%')
ORDER  BY 1, 2;
```

**R-B3b** — the code that speaks of it (capped at 500 lines, any 500 — a lead, not a census):

```sql
SELECT OWNER, NAME, TYPE, LINE, SUBSTR(TRIM(TEXT), 1, 200) AS TEXT
FROM   ALL_SOURCE
WHERE  OWNER IN ('BOX_TRD', 'BOX_FE', 'BOX_ACC')
AND    (UPPER(TEXT) LIKE '%CANCELATION%' OR UPPER(TEXT) LIKE '%EARLY%TERMIN%' OR UPPER(TEXT) LIKE '%DECREASE%')
AND    ROWNUM <= 500;
```

### R-B4 — The values a BOX status / direction / type column holds `Env: BOX` — written from R-B1

For each BOX column the matrix maps a GBO decode to (status, direction, strategy, option class, payout, instrument
type…): `SELECT <column>, COUNT(*) FROM <table> WHERE <branch column> = &&branch_pk GROUP BY <column> ORDER BY 1;`
saved as `01-evidence/R-B4-<table>-<column>.csv`. The `decodes.csv` `box_value` is filled from it.

### R-B5 — The event definitions field 21 tests, from BOX's account `Env: BOX`

```sql
SELECT PK, DESCRIPTION, FK_EVENTTYPE, FK_OWNER_OBJ, FK_EXTENSION
FROM   PGT_SYS.T_PGT_EVENT_DEF_S
WHERE  FK_EVENTTYPE IN (&&event_types) OR DESCRIPTION IN ('Cancelation', 'Decrease')
ORDER  BY PK;
```

## GBO — the report's own configuration and the common key

### R-G0 — The GBO columns the specification names `Env: GBO`

```sql
SELECT OWNER, TABLE_NAME, COLUMN_ID, COLUMN_NAME, DATA_TYPE, DATA_LENGTH
FROM   ALL_TAB_COLUMNS
WHERE  (OWNER = 'DEVENG' AND (TABLE_NAME IN (&&gbo_financst_tables) OR TABLE_NAME IN (&&gbo_mtm_views)
                           OR TABLE_NAME IN (&&gbo_datamis_tables)))
   OR  (OWNER = 'PGT_TRD' AND TABLE_NAME = 'T_PGT_TRADE_HEADER_S')
ORDER  BY 1, 2, 3;
```

Compared with R-B1 column by column (the status logic reads named financial columns: same name, same meaning?).

### R-G1 — The report's topic table, by topic `CODE` `Env: GBO`

```sql
SELECT r.FK_INSTRUMENT, r.COMPRAVENTA, NVL(r.NEARFAR, 'NONE') AS NEARFAR, r.FK_TOPICPK,
       t.CODE AS TOPIC_CODE, t.DESCRIPTION AS TOPIC_DESCRIPTION
FROM   &&gbo_schema..T_PGT_TOPICS_RR r
LEFT   JOIN PGT_ACT.T_PGT_ACCT_TOPICS_S t ON t.PK = r.FK_TOPICPK
ORDER  BY r.FK_INSTRUMENT, r.COMPRAVENTA, 3, t.CODE;
```

**R-G1b** — the topics a report hard-codes (e.g. a deposit's opposite record):
`SELECT PK, CODE, DESCRIPTION FROM PGT_ACT.T_PGT_ACCT_TOPICS_S WHERE PK IN (&&topic_pks) ORDER BY PK;`

The agent writes the report folder's copy (`topics-rr.csv`: `instrument, compraventa, nearfar, topic_code,
topic_description, source`) from R-G1 — decision D3's default; a row with no `CODE` is OPEN.

### R-G2 — The trade id → common key crosswalk `Env: GBO` — **local**

The id as the GBO file prints it (field 1) against `FRONT_ID`, the key GBO and BOX share
([`box-fe-test-lookups.md`](../box-fe-test-lookups.md)). Per product deal table (R-G0 shows its columns first):

```sql
SELECT DISTINCT TO_CHAR(d.DEAL_ID * 100) AS ID, d.FRONT_ID AS KEY
FROM   DEVENG.&&gbo_datamis_table d
WHERE  d.FK_BRANCH = &&gbo_branch_pk;
```

Saved to `local/gbo-ids.csv` (columns `id,key`) — trade-level, never in the run folder. **R-G2c** — before it is used,
five of its `DEAL_ID`s are shown to be trade header PKs:
`SELECT COUNT(*) FROM PGT_TRD.T_PGT_TRADE_HEADER_S WHERE PK IN (&&five_deal_ids);` → 5 (saved, counts only).

### R-T1 — The BOX twins of the GBO topics, by `CODE` `Env: BOX`

```sql
SELECT PK, CODE, DESCRIPTION
FROM   BOX_ACC.T_BOX_ACCT_TOPICS_S
WHERE  CODE IN (&&topic_codes)
ORDER  BY CODE;
```

A GBO topic with no BOX twin → OPEN (the report cannot select an account for it).

## The files themselves — not queries

- **The GBO file** for a process date: the operator copies it from the GBO server's directory (the specification
  names it) into the run's `local/`.
- **The BOX file**: the build's SELECT spooled (`04-sql/<report>-box-select.sql`) into `local/`.
- Both are checked with `scripts/check_fixed_width.py` and compared with `scripts/compare_fixed_width.py`; only their
  reports enter the run.
