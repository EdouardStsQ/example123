# Query catalogue — BOX ACC branch config (the BOX - Accounting SIGOM screens)

The queries [`sigom-box-acc-configs-agent`](../../../agents/sigom-box-acc-configs-agent/AGENT.md) runs (or hands to
the operator) in its **gap run**. Branch-agnostic: every query is parameterised. Its own IDs (`A-…`); it does not
read the FE catalogue ([`fe-config-mining.md`](fe-config-mining.md)) or the jobs one.

**Source of the screen queries** `[read: SIGOM traces via operator, Confluence "Sigom BOX ACC configurations"
checklist, 2026-10-07]`: each `A-0n` below starts from the query SIGOM itself runs when the screen opens (GBO and
BOX side), with explicit column aliases added so the CSV headers are unambiguous, and the branch / instrument
filters added. **Columns not in a trace are not assumed** — those queries say `SELECT *`.

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

| Env tag | Where |
|---|---|
| `REF` | the reference branch's tier (SLB: **Tier 1**) — every query naming a `REFERENCE_*` value |
| `TGT` | the target tier (NY_SCH: **Tier 2**) — its BOX target **and** its GBO (the branch's GBO data lives there) |
| `both` | run in each, two CSVs (`-REF`, `-TGT`), compared |

**Owner objects** `[read: SIGOM traces, 2026-10-07]` — the screen's filter; an `A-G2` result that disagrees wins:

| Screen | BOX `FK_OWNER_OBJ` | GBO `FK_OWNER_OBJ` |
|---|---|---|
| Condition Port Properties | `35000197.65` | `12638.4` |
| Config. Local Properties | `35000194.65` | `12642.4` |
| Accounting Topics | `35000179.65` | `11980.4` |
| Standard Historic | `35000180.65` | `11873.4` |
| Global Accounts | `35000169.65` | `11910.4` |
| Event Grouping (shared `PGT_PRC`) | `12709.4` | — |
| Event Config (shared `PGT_PRC`) | `12713.4` | — |
| MBJ Properties | `35000182.65` (J-T8) | — |
| Cross Account Config, Portfolio Properties, Net Contract | *(trace has no owner filter)* | — |

⚠️ The add-product checklist names `PKG_ACCTCONST.CST_OWNER_PORTFOLIO = 35000194.65`, the owner object the trace
shows for **Config. Local Properties**. A-G2 settles which object is which.

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
(`FK_EXTENSION` → array name from A-G2. A topic **and** a condition joining the same `FK_BS` is possible — the
extension says which one is meant.)

**A-02c `Env: TGT`** — the same two queries with `&&TARGET_GROUP_PK`: what the target's group already has (expected
none, unless the group is shared — A-G1 (b)).

**A-02d `Env: TGT`** — the target's GBO local properties (GBO trace), for comparison only:
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
AND    T1.ACCOUNT = T6.PK(+) AND T1.TOPIC = T7.PK(+)
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
AND    T1.FK_ENTITY = T5.PK(+) AND T1.FK_ACCOUNT = T6.PK(+) AND T1.FK_TOPIC = T7.PK(+)
AND    T1.FK_BRANCH = &&REFERENCE_BRANCH_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS);
```
Compared row by row (instrument, currency, entity, account **code**): is the BOX account the GBO account (same code,
same PK?), which BOX topic replaced each GBO topic, and how `ACC_TYPE` (Posición Viva / Vencida / Balance de
Posición Viva) was set — the GBO screen has no `ACC_TYPE`. That pattern is the translation rule; what it does not
explain is a question.

**A-03c `Env: TGT`** — the BOX trace with `&&TARGET_BRANCH_PK`: rows already there (expected none).

### 4. Portfolio Properties — branch-group keyed; never copied from GBO

**A-04a `Env: REF`** — the reference group's portfolio properties (BOX trace + filters):
```sql
SELECT T1.PK AS port_prop_pk, T2.PK AS group_pk, T2.DESCRIPTION AS branch_group, T3.PK AS instrument_pk,
       T3.DESCRIPTION AS instrument, T1.INIVALPCDATE, T1.STATUS, T1.DESCRIPTION
FROM   BOX_ACC.T_BOX_ACCT_PORT_PROP_S T1, PGT_STC.T_PGT_BRANCH_GROUP_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3
WHERE  T1.FK_BRANCH = T2.PK AND T1.FK_INSTRUMENT = T3.PK
AND    T1.FK_BRANCH = &&REFERENCE_GROUP_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
ORDER  BY T3.DESCRIPTION, T1.INIVALPCDATE;
```
**A-04b `Env: REF`** — their generated lists (topic → account; conditions):
```sql
SELECT l.FK_PARENT AS port_prop_pk, tp.CODE AS topic_code, tp.DESCRIPTION AS topic,
       a.CODE AS account_code, a.DESCRIPTION AS account
FROM   BOX_ACC.T_BOX_ACCT_LIST_TOPIC_S l
LEFT   JOIN BOX_ACC.T_BOX_ACCT_TOPICS_S tp ON tp.PK = l.FK_TOPIC
LEFT   JOIN BOX_ACC.T_BOX_ACCT_GLTA_S   a  ON a.PK  = l.FK_GLTA
WHERE  l.FK_PARENT IN (SELECT PK FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S
                       WHERE FK_BRANCH = &&REFERENCE_GROUP_PK AND FK_INSTRUMENT IN (&&INSTRUMENT_PKS))
ORDER  BY l.FK_PARENT, tp.CODE;

SELECT * FROM BOX_ACC.T_BOX_ACCT_LIST_COND_S             -- columns not confirmed
WHERE  FK_PARENT IN (SELECT PK FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S
                     WHERE FK_BRANCH = &&REFERENCE_GROUP_PK AND FK_INSTRUMENT IN (&&INSTRUMENT_PKS));
```
**A-04c `Env: TGT`** — A-04a / A-04b with `&&TARGET_GROUP_PK`: already there (expected none).

**A-04d `Env: TGT`** — the target's **GBO** portfolio properties (GBO trace + filter) — for its **accounts** only:
```sql
SELECT T1.PK AS port_prop_pk, T2.PK AS group_pk, T3.PK AS instrument_pk, T3.DESCRIPTION AS instrument,
       T1.INIVALPCDATE, T1.STATUS, T1.DESCRIPTION
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S T1, PGT_STC.T_PGT_BRANCH_GROUP_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3
WHERE  T1.FK_BRANCH = T2.PK AND T1.FK_INSTRUMENT = T3.PK
AND    T1.FK_BRANCH = &&TARGET_GROUP_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS);
```
**A-04e `Env: TGT`** — its topic → account list: the GBO list table from **A-G3** (not assumed), joined to
`PGT_ACT.T_PGT_ACCT_TOPICS_S` (topic code) and `PGT_ACT.T_PGT_ACCT_GLTA_S` (account code). GBO **topics** never
enter BOX: each GBO topic goes through the GBO → BOX topic mapping (open), and only its **account** is kept.

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
**A-10b `Env: TGT`** — the same codes in BOX (BOX trace + `T1.CODE IN (&&ACCOUNT_CODES)`, owner `35000169.65`):
present / missing.

**A-10c `Env: REF`** — **how the reference's accounts went from GBO to BOX**: the reference's BOX accounts used by
A-03b / A-04b, joined by `CODE` to the GBO table: same PK? same `SHORTNAME`, `DESCRIPTION`, `FXADJUSTIND`? GLTA type
and direction: the same domain PK, or the same **description** under a BOX domain (GBO and BOX types are different
`PGT_DOMAINS` enumerations)? That decides how a missing account is created.

### 11. MBJ Config — not this agent

The ACC jobs (`shell.conf`, Control-M, MBJ rows) belong with the planned `box-acc-jobs-agent`. The reference's rows
are J-R2 in [`box-jobs-queries.md`](box-jobs-queries.md).

---

## Not in the Confluence checklist — rule in or out

**A-11 `Env: REF`** — for each object of A-G2 keyed on `pBranch` / `pLocalGroup` and **not** in the walk above (Acct
Key, Acct Key Group, Documents, Grouped Mov Config, Conf Instru Type, Net CCS PlanBS, Conf Acc By StdHist, GLTA Local
Dep): `SELECT COUNT(*)` of its `BASIC_STORAGE` for the reference branch (or group). Rows for the reference and none
expected to be transactional → a candidate step, asked; transactional (movements, documents) → out, with the reason.
