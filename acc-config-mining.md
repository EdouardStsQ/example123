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

`[2026-10-22]` The BOX ACC expert's review ([ADR 0014](../../decisions/0014-box-acc-expert-review-1.md)): Cross
Account Config is read from **`<GBO schema>.T_MAD_REVAL_ACCOUNTS`** (A-03, rewritten); the GBO portfolio properties
read are **`Valid`** only (A-U7, A-04d / A-04e); **A-P7** compares a GBO table's columns with its BOX counterpart
before any copy; **A-12** Conf Instru Type from the reference; screens 1 and 8 are verify-only (nothing asked);
local properties start on 01/01/1900.

**Order in a run:** gate (A-G…) → pre-checks (A-P…) → the target's GBO configuration in scope (A-U1, A-U7) → the
screens (A-0…, A-10, A-11, A-12).

`[2026-10-28]` **Portfolio properties imported from GBO one by one** ([ADR 0020](../../decisions/0020-portfolio-properties-imported-from-gbo.md)):
one BOX property per `Valid` in-scope GBO property, its conditions that have a BOX twin (the **condition map**, A-01 +
A-04g + A-04h), its own accounts; local properties built from the same GBO properties; clashes reported. New: A-04f,
A-04g, A-04h.

`[2026-10-29]` **NY's first DEV run** (`gap_20261029_1`, DGBOUS, GBO source PRE PARALELO —
[ADR 0023](../../decisions/0023-acc-configs-lessons-of-the-first-dev-run.md)): *Where each table lives* and the grants
seen (rule 4); A-P2 / A-P7 owners; A-P5 read per fraction; A-02c / A-04c without the group table; A-04i (b) and the
GBO-source dependence; A-04h reads `NOM_FUNC`; a condition value with no BOX translation → OPEN; which accounts screen
10 creates (§10); A-10a with the type / direction codes, new A-10e; Net CCS accounts from the reference's BOX rows.

`[2026-10-22]` **No usage window** ([ADR 0015](../../decisions/0015-acc-configs-scope-from-configuration.md)): what is
built comes from configuration (the `Valid` GBO portfolio properties of the target's branch, full lists), so the
windowed queries (A-U0, A-U2, A-U2b, A-U3, A-U4, A-U4b, A-U6) are **optional diagnostics**, run only when the BOX team
asks. **One GBO source per run** (env tag `GBO`), asked once.

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
| `&&ACCOUNT_CODES` | the target's GBO account codes in scope | A-U7b (the in-scope lists' real accounts) + A-03a `[2026-10-22]` — screen 10 creates only those the carried configuration uses (§10, 2026-10-29) |
| `&&REFERENCE_ACCOUNT_CODES` | the reference's BOX account codes | A-03b + A-04b |
| `&&USAGE_FROM`, `&&USAGE_TO` | the usage window (`YYYY-MM-DD`, `TO` exclusive) — **optional diagnostics only** (ADR 0015) | asked only when a windowed query is run |
| `&&BRANCH_COND_PKS` 🆕 | the target's **branch conditions** (condition PKs whose function returns the trade's branch) | **A-U1 (b)** — NY: `24.35, 29.35, 33.35, 35.35` |
| `&&BRANCH_CODE`, ~~`&&OTHER_BRANCH_CODES`~~ | the value the branch condition returns for the target (and, until 2026-10-23, the group's other branches — now `&&OUT_BRANCH_CODES`) | **A-U1 (e)** — NY: `NY_SCH` |
| `&&GROUP_BRANCH_PKS` 🆕 | every branch of the target's group | **A-G1 (b)** |
| `&&TARGET_GBO_SCHEMA`, `&&REFERENCE_GBO_SCHEMA` 🆕 | the branch's GBO schema of `T_MAD_REVAL_ACCOUNTS` | the inputs file's `target.gbo_schema` / `reference.gbo_schema` (= registry `wrapper_owner`: NY `PGT_NY`; **SLB and Madrid `PGT_ES`**) `[BOX ACC expert, 2026-10-22]`. **Never built from the branch code** — there is no `PGT_SLB` `[operator, 2026-10-23]` |
| `&&OUT_BRANCH_CODES` 🆕 `[2026-10-23]` | the branch-condition values **classified out** of the target's scope (other branches of the group, …) | **A-U1 (g)** — each value with its evidence; replaces `&&OTHER_BRANCH_CODES` in A-U7 |

| Env tag | Where |
|---|---|
| `REF` | the reference branch's tier (SLB: **Tier 1**) — every query naming a `REFERENCE_*` value |
| `TGT` | the target tier (NY_SCH: **Tier 2**) — its **BOX** target |
| `GBO` 🆕 `[2026-10-22]` | the run's **GBO source** — where the target's GBO configuration is read: the target environment by default, or a fresher copy of production the operator names (NY: PRE PARALELO possible). **Asked once per run** (`gbo_source.env`); every query on the target's GBO tables runs there. CSVs `-GBO` |
| `both` | run in each, two CSVs (`-REF`, `-TGT`), compared |
| ~~`GBO-PROD`~~ / ~~`GBO-PREPAR`~~ | replaced by `GBO` (2026-10-22). The optional usage diagnostics run in production when accessible, else in the run's GBO source |

**How a query is run** `[operator, 2026-10-23]` — after the NY gap run of 2026-10-23 (queries with invented columns
and schema):
1. **The catalogue's text, as it is** — only the `&&` values substituted (from the inputs file or an earlier CSV,
   named). Never a column, table or schema the catalogue does not write. A query that fails (ORA-00904 / ORA-00942):
   **A-P8** for that table, then fix only the name the error gives, and say so in the matrix.
2. **One system per query.** The operator's accounts are per system — a GBO account (`PGT_ACT`, the wrapper schemas
   `PGT_ES` / `PGT_NY`) and a BOX account (`BOX_ACC`). A comparison of the two (A-03b, A-10c) is **two extracts**
   (`-GBO` / `-BOX` suffix), joined by the agent on the key the query names. The shared SIGOM schemas (`PGT_SYS`,
   `PGT_STC`, `PGT_PRC`, `GOM_GLB_SYS`) are read from either.
3. **Find before asking.** A PK the run meets (a branch, a group, an instrument, a condition…) is resolved with
   **A-L1**, never asked; a branch-condition value is classified with **A-U1 (g)**. The operator is asked only what
   no query can answer — with the evidence and a proposal.
4. **Every table in the schema the table below gives** `[operator, 2026-10-29]` — NY's DEV gap run `gap_20261029_1`
   sent three queries on tables that do not exist (`PGT_NY.T_PGT_ACCT_PORT_PROP_S`, `PGT_SYS.T_MAD_REVAL_ACCOUNTS`,
   `PGT_ACT.T_PGT_TOPICS_S`) — each an ORA-00942 and a round trip for the operator. Before a query is handed over,
   each `schema.table` in it is checked against this table; a table not in it → A-P8 first. An improvised query (one
   the catalogue does not hold) says why the catalogue's does not do, and is written from A-P8's columns only.

**Where each table lives** `[2026-10-29]` — the GBO accounting tables are in `PGT_ACT` for every branch; the
branch's wrapper schema (`target.gbo_schema`: NY `PGT_NY`, SLB / Madrid `PGT_ES`) holds only the branch's own
tables (here `T_MAD_REVAL_ACCOUNTS`):

| Schema | Tables the catalogue reads | Never (do not exist) |
|---|---|---|
| `PGT_ACT` (GBO accounting) | `T_PGT_ACCT_PORT_PROP_S`, `T_PGT_ACCT_LIST_TOPIC_S`, `T_PGT_ACCT_LIST_COND_S`, `T_PGT_ACCT_TOPICS_S`, `T_PGT_ACCT_GLTA_S`, `T_PGT_ACCT_PARENT_DATE_S` | `T_PGT_TOPICS_S` (the topics table is `T_PGT_ACCT_TOPICS_S`) |
| `&&TARGET_GBO_SCHEMA` / `&&REFERENCE_GBO_SCHEMA` (NY `PGT_NY`, SLB `PGT_ES`) | `T_MAD_REVAL_ACCOUNTS` | `PGT_NY.T_PGT_ACCT_*` (accounting tables are `PGT_ACT`'s); `PGT_SLB` (no such schema) |
| `PGT_SYS` (shared) | `PGT_DOMAINS`, `T_PGT_SUB_PRODUCT_S`, `T_PGT_CONDPAR_PROP_S`, `T_PGT_CONF_LO_PROP_S`, `T_PGT_LINK_ARRAY_X`, `T_PGT_CROSS_ACCTCONF_S`, `T_PGT_INSTRUMENT_TYPE_S`, `T_PGT_SOURCE_S` | `PGT_SYS.T_MAD_REVAL_ACCOUNTS` (it is the wrapper schema's) |
| `PGT_STC` (shared) | `T_PGT_BRANCH_S`, `T_PGT_BRANCH_GROUP_S`, `T_PGT_CURRENCY_S`, `T_PGT_ENTITY_S` | — |
| `BOX_ACC` | every `T_BOX_…` table, `DATABASECHANGELOG`, the `SPK_…` sequences | — |
| `GOM_GLB_SYS`, `PGT_PRC`, `PGT_TRD` | `T__CORE_INFO_S`, `T__OBJ_DEF_S`, `T__EXT_DEF_S` · `T_PGT_EVE_S`, `T_PGT_BR_EVE_S` · `T_PGT_OBJ_SOURCE_S` | — |

**Grants seen** `[operator, 2026-10-29]`: in **DGBOUS** (Tier 2 DEV) the `BOX_ACC` account reads
`PGT_STC.T_PGT_BRANCH_S` but **not** `PGT_STC.T_PGT_BRANCH_GROUP_S` (ORA-00942; `DEVENG` has a synonym of
`T_PGT_BRANCH_S` only). So a `TGT` query run as `BOX_ACC` never joins `T_PGT_BRANCH_GROUP_S`: the group is
`FK_BRANCH` itself (A-02c, A-04c below); A-G1 and A-L1 run in the GBO account. Rule 2's "shared schemas are read from
either account" holds for every other table seen so far.

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
| Conf Instru Type (screen 12) / Net CCS PlanBS (screen 13) | `35000292.65` / `35000348.65` | — |

The add-product checklist's `PKG_ACCTCONST.CST_OWNER_PORTFOLIO = 35000194.65` is the **local-properties** object;
`PKG_ACCTPROP` names it `CST_OWN_CONF_LOCAL` and the portfolio-property object `CST_OWN_PORTFOLIO = 35000170.65`
`[read: code, 2026-10-14]`.

---

## Gate

### A-G1 — The branch and its group `Env: both`

Run in each tier's **GBO account** (`BOX_ACC` cannot read `T_PGT_BRANCH_GROUP_S` in DGBOUS — *Grants seen* above).

```sql
SELECT b.PK AS branch_pk, b.DESCRIPTION AS branch, b.FK_LOCALGROUP AS group_pk, g.DESCRIPTION AS branch_group
FROM   PGT_STC.T_PGT_BRANCH_S b
LEFT   JOIN PGT_STC.T_PGT_BRANCH_GROUP_S g ON g.PK = b.FK_LOCALGROUP
WHERE  b.PK = &&BRANCH_PK;          -- TGT: &&TARGET_BRANCH_PK ; REF: &&REFERENCE_BRANCH_PK

-- (b) TGT: every branch of the target's group — a group shared with a branch already in BOX may need no rows
SELECT PK AS branch_pk, DESCRIPTION AS branch FROM PGT_STC.T_PGT_BRANCH_S WHERE FK_LOCALGROUP = &&TARGET_GROUP_PK;
```

### A-G4 — Is the target's group already in BOX? `Env: TGT` (BOX_ACC) 🆕 `[2026-10-15]`

```sql
SELECT 'CONF_LO_PROP' AS tbl, FK_BRANCH, COUNT(*) AS n FROM BOX_ACC.T_BOX_CONF_LO_PROP_S
WHERE  FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK) AND FK_OWNER_OBJ > 0 GROUP BY FK_BRANCH
UNION ALL
SELECT 'PORT_PROP', FK_BRANCH, COUNT(*) FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S
WHERE  FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK) AND FK_OWNER_OBJ > 0 GROUP BY FK_BRANCH
UNION ALL
SELECT 'CROSS_ACCTCONF', FK_BRANCH, COUNT(*) FROM BOX_ACC.T_BOX_CROSS_ACCTCONF_S
WHERE  FK_BRANCH IN (&&GROUP_BRANCH_PKS) GROUP BY FK_BRANCH;
```
**The real checkpoint-1 answer** (A-G1 b only lists the group's branches): no row → the target is the **first branch
of its group in BOX** and creates every group-level row; rows → screens 2 and 4 may already exist — stop and ask.
NY SCH: 0 rows in Tier 2 PRE `[2026-10-15]`.

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

### A-L1 — What a PK is `Env: the tier where the PK was seen` 🆕 `[2026-10-23]`

Any PK met in a CSV and not in the inputs file (e.g. a second `FK_BRANCH` value on the reference's rows): resolved
here, **never asked** — NY run 2026-10-23: `269.4` on SLB's rows was asked; it is a branch group (Madrid). Run in
the tier's GBO account (it reads `T_PGT_BRANCH_GROUP_S`).
```sql
SELECT 'BRANCH GROUP' AS kind, PK, DESCRIPTION, NULL AS group_pk FROM PGT_STC.T_PGT_BRANCH_GROUP_S WHERE PK IN (&&PKS)
UNION ALL SELECT 'BRANCH', PK, DESCRIPTION, FK_LOCALGROUP FROM PGT_STC.T_PGT_BRANCH_S WHERE PK IN (&&PKS)
UNION ALL SELECT 'INSTRUMENT', PK, DESCRIPTION, NULL FROM PGT_SYS.T_PGT_SUB_PRODUCT_S WHERE PK IN (&&PKS)
ORDER  BY 2, 1;
```
A PK in none of them: `GOM_GLB_SYS.T__OBJ_DEF_S` (`BASIC_STORAGE` of the column's target object, metamodel §11).
**Reading:** a value that is not the reference's (or the target's) group / branch is **another branch's row** —
reported with what it is, left out of the comparison, not a question.

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
A-P2 reads `BOX_ACC` only. A count of the GBO side (e.g. the GBO portfolio properties) is read in **`PGT_ACT`**, as
A-P4 does — never in the branch's wrapper schema (`PGT_NY.T_PGT_ACCT_PORT_PROP_S` does not exist; asked in NY's run
of 2026-10-29) `[operator, 2026-10-29]`.

### A-P3 — The metamodel declares the same objects and extensions `Env: TGT`

[`sigom-metamodel.md`](../sigom-metamodel.md) §11 query 3 with `&&MODULE_PK = 35000006.65`, kept to the objects
`35000169.65, 35000170.65, 35000189.65, 35000194.65, 35000197.65, 35000179.65, 35000180.65, 35000292.65,
35000348.65`. **Check:** the extension PKs and targets of the owner table; the pre-commit procedures of
`box-acc-model.md` §5.

### A-P4 — Negative owners (test / deleted rows) `Env: both`

A-P2's rows with `FK_OWNER_OBJ < 0`, plus the GBO tables the run reads (`GBO`):
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
```sql
-- (b) 🆕 [2026-10-23] the installation's auth code (the PK fraction F_GetPK appends) and the max PK WITH that fraction
SELECT AUTH_CODE FROM GOM_GLB_SYS.T__CORE_INFO_S;
SELECT 'PORT_PROP' AS tbl, MAX(TRUNC(PK)) AS max_pk_this_fraction, COUNT(*) AS n
FROM   BOX_ACC.T_BOX_ACCT_PORT_PROP_S WHERE PK - TRUNC(PK) = &&PK_FRACTION      -- auth code / 10^digits (44 -> .44)
UNION ALL SELECT 'CONF_LO_PROP', MAX(TRUNC(PK)), COUNT(*) FROM BOX_ACC.T_BOX_CONF_LO_PROP_S WHERE PK - TRUNC(PK) = &&PK_FRACTION
UNION ALL SELECT 'LINK_ARRAY_X', MAX(TRUNC(PK)), COUNT(*) FROM BOX_ACC.T_BOX_LINK_ARRAY_X WHERE PK - TRUNC(PK) = &&PK_FRACTION
UNION ALL SELECT 'CROSS_ACCTCONF', MAX(TRUNC(PK)), COUNT(*) FROM BOX_ACC.T_BOX_CROSS_ACCTCONF_S WHERE PK - TRUNC(PK) = &&PK_FRACTION
UNION ALL SELECT 'GLTA', MAX(TRUNC(PK)), COUNT(*) FROM BOX_ACC.T_BOX_ACCT_GLTA_S WHERE PK - TRUNC(PK) = &&PK_FRACTION
UNION ALL SELECT 'PARENT_DATE', MAX(TRUNC(PK)), COUNT(*) FROM BOX_ACC.T_BOX_ACCT_PARENT_DATE_S WHERE PK - TRUNC(PK) = &&PK_FRACTION
UNION ALL SELECT 'LIST_TOPIC', MAX(TRUNC(PK)), COUNT(*) FROM BOX_ACC.T_BOX_ACCT_LIST_TOPIC_S WHERE PK - TRUNC(PK) = &&PK_FRACTION
UNION ALL SELECT 'LIST_COND', MAX(TRUNC(PK)), COUNT(*) FROM BOX_ACC.T_BOX_ACCT_LIST_COND_S WHERE PK - TRUNC(PK) = &&PK_FRACTION
UNION ALL SELECT 'CONF_INSTRUM_TYPE', MAX(TRUNC(PK)), COUNT(*) FROM BOX_ACC.T_BOX_CONF_INSTRUM_TYPE_S WHERE PK - TRUNC(PK) = &&PK_FRACTION;

-- (c) 🆕 which mode F_GetPK uses for the applying connection (counter T___SEQUENCE or SPK_ sequence, model §6):
--     the table's owner first, then its rows (columns not assumed beyond USE_SEQ_PROCEDURE / USE_SIG_SEQ)
SELECT OWNER, TABLE_NAME FROM ALL_TABLES WHERE TABLE_NAME = 'T__REMCONN_S';
SELECT * FROM &&REMCONN_OWNER.T__REMCONN_S;
```
**Check:** for each table the run will write, the next number **of the mode (c) shows** (sequence or counter) is
above (b)'s `max_pk_this_fraction`; (a)'s `max_pk` across every fraction is shown too (PKs of another installation do
not collide). A missing sequence (`SPK_T_BOX_CONF_LO_PROP_S` has no file in the repo) is reported. Seed data with
hard-coded PKs makes some sequences lag (conditions, topics, standard historic in PRE-PROD).

```sql
-- (d) 🆕 [2026-10-27] one table in detail (a warning of (a) / (b)): its sequence, its rows per fraction, the SIGOM
--     counter, triggers and code that set its PK
SELECT LAST_NUMBER, INCREMENT_BY, CACHE_SIZE FROM ALL_SEQUENCES
WHERE  SEQUENCE_OWNER = 'BOX_ACC' AND SEQUENCE_NAME = 'SPK_&&TABLE';
SELECT PK - TRUNC(PK) AS fraction, COUNT(*) AS n, MAX(TRUNC(PK)) AS max_pk FROM BOX_ACC.&&TABLE GROUP BY PK - TRUNC(PK);
SELECT * FROM BOX_ACC.T___SEQUENCE WHERE PK_NAME = '&&TABLE';
SELECT TRIGGER_NAME, TRIGGERING_EVENT, STATUS FROM ALL_TRIGGERS WHERE TABLE_OWNER = 'BOX_ACC' AND TABLE_NAME = '&&TABLE';
```
**Reading (d):** the next value (no cache: `LAST_NUMBER`; a counter row → its `NEXT_VAL`) against the highest PK
**of the installation's fraction** only — rows of another fraction (`.65` seed data) never collide. Tier 2 PRE,
`T_BOX_ACCT_PARENT_DATE_S` `[operator, 2026-10-27]`: next `2`, rows `1.44` and `2.65`, no counter row → **no
collision** (the earlier warning compared across fractions). DGBOUS, `T_BOX_ACCT_GLTA_S` `[operator, 2026-10-29]`:
(a) said `MAX_PK` 16699 > next 16368 — but the `.44` rows are 20, max `105` → **no collision**; the same mistake
twice, so: **a warning of (a) is never reported before (d)** for that table. Compare the fraction as
`PK - TRUNC(PK) = 0.44` (as (b) / (d) do) — never `PK LIKE '%.44'` (a number read as text) — and the number part as
`TRUNC(PK)`.

**A collision is a finding, not a stop** `[2026-10-23]`: phase 1 writes nothing, so the reading goes on; the matrix
lists each table behind (next value, max PK, the mode) with a **proposal for the BOX team** — the sequence (or the
`T___SEQUENCE` counter) moved above the max PK plus a margin, run by them — and phase 2 refuses to render that
table's SQL until A-P5 shows it clear. Why A-P5 only reads, where the FE pre-step P1 draws a PK: `F_GetPK` in counter
mode **updates** `T___SEQUENCE` — a write, not allowed in phase 1; phase 2's renderer will carry the P1-style check
(draw, check the fraction, stop) in its own script.

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

### A-P7 — GBO vs BOX columns of every table copied `Env: TGT` (and `REF`) 🆕 `[2026-10-22]`

GBO and BOX tables are similar, not identical: a column may be added, removed or renamed (BOX ACC expert, ADR 0014).
Run once per pair copied — `&&GBO_OWNER.&&GBO_TABLE` ↔ `BOX_ACC.&&BOX_TABLE`: `&&TARGET_GBO_SCHEMA.T_MAD_REVAL_ACCOUNTS`
↔ `T_BOX_CROSS_ACCTCONF_S`; `PGT_ACT.T_PGT_ACCT_GLTA_S` ↔ `T_BOX_ACCT_GLTA_S`; `PGT_ACT.T_PGT_ACCT_PARENT_DATE_S` ↔
`T_BOX_ACCT_PARENT_DATE_S`; `PGT_ACT.T_PGT_ACCT_PORT_PROP_S` ↔ `T_BOX_ACCT_PORT_PROP_S`;
`PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S` ↔ `T_BOX_ACCT_LIST_TOPIC_S`. CSV `A-P7-<BOX table>-TGT.csv`.

| Pair | `&&GBO_OWNER` | `&&GBO_TABLE` | `&&BOX_TABLE` |
|---|---|---|---|
| Cross Account Config | **`&&TARGET_GBO_SCHEMA`** (NY `PGT_NY`; SLB `PGT_ES`) — **never `PGT_SYS`** (NY's run of 2026-10-29 asked `owner = 'PGT_SYS'`: no row, nothing compared) `[operator, 2026-10-29]` | `T_MAD_REVAL_ACCOUNTS` | `T_BOX_CROSS_ACCTCONF_S` |
| Global Accounts | `PGT_ACT` | `T_PGT_ACCT_GLTA_S` | `T_BOX_ACCT_GLTA_S` |
| Account date rules | `PGT_ACT` | `T_PGT_ACCT_PARENT_DATE_S` | `T_BOX_ACCT_PARENT_DATE_S` |
| Portfolio properties | `PGT_ACT` | `T_PGT_ACCT_PORT_PROP_S` | `T_BOX_ACCT_PORT_PROP_S` |
| Topic lists | `PGT_ACT` | `T_PGT_ACCT_LIST_TOPIC_S` | `T_BOX_ACCT_LIST_TOPIC_S` |

An empty `GBO only` / `both` side means the owner or the table name is wrong (or not visible to the account) — never
"the GBO table has no columns": check the owner against *Where each table lives* and re-run.
`ALL_TAB_COLUMNS` lists only what the account can see: if one account does not see both owners, run it in each
account (`-GBO` / `-BOX`) and join on `COLUMN_NAME` `[2026-10-23]`.
```sql
SELECT NVL(g.column_name, b.column_name) AS column_name,
       CASE WHEN g.column_name IS NULL THEN 'BOX only' WHEN b.column_name IS NULL THEN 'GBO only' ELSE 'both' END AS presence,
       g.data_type || '(' || NVL(g.data_precision, g.data_length) || ')' AS gbo_type, g.nullable AS gbo_null,
       b.data_type || '(' || NVL(b.data_precision, b.data_length) || ')' AS box_type, b.nullable AS box_null
FROM  (SELECT column_name, data_type, data_length, data_precision, nullable FROM all_tab_columns
       WHERE  owner = '&&GBO_OWNER' AND table_name = '&&GBO_TABLE') g
FULL  OUTER JOIN
      (SELECT column_name, data_type, data_length, data_precision, nullable FROM all_tab_columns
       WHERE  owner = 'BOX_ACC' AND table_name = '&&BOX_TABLE') b
      ON b.column_name = g.column_name
ORDER BY presence, column_name;
```
**Check:** the matrix's column map per table — each BOX column filled from a named GBO column (`both`, or a rename
shown by the reference, A-03b / A-10c), a fixed value (owner, extension, `PK` from `F_GetPK`) or the reference's
pattern; a `BOX only` column with none of those → asked; a `GBO only` column → reported, not copied; a shorter BOX
type → a finding per value too long. A column BOX **sets itself** on save — the renderer's computed list: `STATUS`,
`MESSAGE`, `VALIDDATE`, `LOC_CODE`, `HOSTINTERFIND`, `PARENT_ACCOUNT`, `LSTMNTDATE`, `LSTMNTUSER`, `LSTMNTSOURCE`
(`p_AccountPrecommit`, `p_StatusPortFolio`, triggers) — is mapped **"computed — not supplied"**, even when GBO has
a column of the same name (NY's matrix of 2026-10-29 listed `LOC_CODE` / `HOSTINTERFIND` "from GBO verbatim"; the
renderer refuses them, `column-computed`). The date rule's own `CODELOC` / `HOSTINTERF` are supplied (from A-10d).

### A-P8 — The columns of a table `Env: the tier and account of the failing query` 🆕 `[2026-10-23]`

Before any query on a table the catalogue does not query yet, and after an ORA-00904 / ORA-00942:
```sql
SELECT OWNER, TABLE_NAME, COLUMN_ID, COLUMN_NAME, DATA_TYPE, NULLABLE
FROM   ALL_TAB_COLUMNS WHERE TABLE_NAME = '&&TABLE' ORDER BY OWNER, COLUMN_ID;
```
The query is then written from these columns only, and the CSV kept (`A-P8-<table>-<tier>.csv`). Known real columns
are noted under each query (e.g. A-04a).

---

## The target's GBO configuration in scope (A-U1, A-U7) — and optional usage diagnostics `[2026-10-14, 2026-10-22]`

`Env: GBO`, read-only, aggregates and codes only — **no portfolio, counterparty or entity names**, no raw movement
rows. **In the run:** A-U1 (a), (f), (g) and A-U7 (a), (b) — configuration, no window. **Optional diagnostics** (only when
the BOX team asks; ADR 0015): A-U0, A-U2, A-U2b, A-U3, A-U4, A-U4b, A-U5, A-U6 — they read movements over a window
(`&&USAGE_FROM` / `&&USAGE_TO`) and explain routes outside the configuration; they never decide what is built. NY's
July 2026 results are in [`box-acc-model.md`](../box-acc-model.md) §9.

### A-U0 — The movements table is read by its partition `Env: GBO` (optional diagnostic)

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

### A-U1 — The target's configuration, per instrument and list `Env: GBO`

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
**Check:** (a) says whether GBO keys portfolio properties on the group (expected) or the branch, and how many are
`Valid` / `InValid` (only `Valid` ones are read, ADR 0014); (d) the target's rows in GBO's own Cross Account Config —
usage evidence only: screen 3's source is `T_MAD_REVAL_ACCOUNTS` (A-03a, ADR 0014).

```sql
-- (e) 🆕 the branch condition's values, per instrument - which properties belong to which branch of the group
--     (&&BRANCH_COND_PKS from (b): the conditions whose function returns the trade's branch; never a counterparty one)
SELECT pp.FK_INSTRUMENT, sp.DESCRIPTION AS instrument, lc.FK_CONDITION, cp.NOM_FUNC, lc.VALUE_FUNC,
       COUNT(DISTINCT pp.PK) AS n_port_prop
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp
JOIN   PGT_ACT.T_PGT_ACCT_LIST_COND_S lc ON lc.FK_PARENT = pp.PK AND lc.FK_OWNER_OBJ = 12646.4 AND lc.FK_EXTENSION = 38335.4
LEFT   JOIN PGT_SYS.T_PGT_CONDPAR_PROP_S cp ON cp.PK = lc.FK_CONDITION
LEFT   JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = pp.FK_INSTRUMENT
WHERE  pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
AND    pp.FK_INSTRUMENT IN (&&INSTRUMENT_PKS) AND lc.FK_CONDITION IN (&&BRANCH_COND_PKS)
GROUP  BY pp.FK_INSTRUMENT, sp.DESCRIPTION, lc.FK_CONDITION, cp.NOM_FUNC, lc.VALUE_FUNC
ORDER  BY 2, 3, 5;

-- (f) 🆕 each portfolio property with its branch value - the screen-4 scope (blank = no branch condition)
SELECT pp.PK AS port_prop_pk, pp.FK_INSTRUMENT, sp.DESCRIPTION AS instrument, pp.STATUS,
       MAX(CASE WHEN lc.FK_CONDITION IN (&&BRANCH_COND_PKS) THEN lc.VALUE_FUNC END) AS branch_value
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp
LEFT   JOIN PGT_ACT.T_PGT_ACCT_LIST_COND_S lc ON lc.FK_PARENT = pp.PK AND lc.FK_OWNER_OBJ = 12646.4 AND lc.FK_EXTENSION = 38335.4
LEFT   JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = pp.FK_INSTRUMENT
WHERE  pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
AND    pp.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
GROUP  BY pp.PK, pp.FK_INSTRUMENT, sp.DESCRIPTION, pp.STATUS
ORDER  BY 3, 1;
```
**(e) / (f)** `[2026-10-15]`: a group shared by several branches separates them by a **branch condition** (NY:
`f_TradeBranch…`, values `NY_SCH`, `NY_IBF`, `INTERNAL`). Screen 4's scope = the properties whose value is the
target's code, plus those with no branch condition for an in-scope instrument, plus special values such as `INTERNAL`
— each **classified by (g)**, not asked first. See [`box-acc-model.md`](../box-acc-model.md) §9.3.

```sql
-- (g) 🆕 [2026-10-23] what each branch value means - run BEFORE any scope question.
-- (g1) the branch condition's function: its source (where the value it returns comes from)
SELECT OWNER, NAME, TYPE, LINE, TEXT FROM ALL_SOURCE
WHERE  OWNER = UPPER('&&FUNC_OWNER') AND NAME = UPPER('&&FUNC_PACKAGE') AND TYPE = 'PACKAGE BODY'
AND    LINE BETWEEN (SELECT MIN(LINE) FROM ALL_SOURCE WHERE OWNER = UPPER('&&FUNC_OWNER') AND NAME = UPPER('&&FUNC_PACKAGE')
                     AND TYPE = 'PACKAGE BODY' AND UPPER(TEXT) LIKE '%FUNCTION ' || UPPER('&&FUNC_NAME') || '%')
                AND (SELECT MIN(LINE) FROM ALL_SOURCE WHERE OWNER = UPPER('&&FUNC_OWNER') AND NAME = UPPER('&&FUNC_PACKAGE')
                     AND TYPE = 'PACKAGE BODY' AND UPPER(TEXT) LIKE '%FUNCTION ' || UPPER('&&FUNC_NAME') || '%') + 120
ORDER  BY LINE;
--      (&&FUNC_OWNER / _PACKAGE / _NAME from (b)'s NOM_FUNC; a standalone function: TYPE = 'FUNCTION', NAME = it)
-- (g2) the group's branches, every column - a value equal to another branch's code / short name is that branch's
SELECT * FROM PGT_STC.T_PGT_BRANCH_S WHERE FK_LOCALGROUP = &&TARGET_GROUP_PK ORDER BY PK;
-- (g3) per value: properties, instruments, Valid / InValid, the latest start date - the size of each family
SELECT v.branch_value, COUNT(*) AS n_port_prop, COUNT(DISTINCT v.FK_INSTRUMENT) AS n_instruments,
       SUM(CASE WHEN v.STATUS = 'Valid' THEN 1 ELSE 0 END) AS n_valid, MAX(v.INIVALPCDATE) AS latest_start
FROM  (SELECT pp.PK, pp.FK_INSTRUMENT, pp.STATUS, pp.INIVALPCDATE,
              MAX(CASE WHEN lc.FK_CONDITION IN (&&BRANCH_COND_PKS) THEN lc.VALUE_FUNC END) AS branch_value
       FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp
       LEFT   JOIN PGT_ACT.T_PGT_ACCT_LIST_COND_S lc
              ON lc.FK_PARENT = pp.PK AND lc.FK_OWNER_OBJ = 12646.4 AND lc.FK_EXTENSION = 38335.4
       WHERE  pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
       AND    pp.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
       GROUP  BY pp.PK, pp.FK_INSTRUMENT, pp.STATUS, pp.INIVALPCDATE) v
GROUP  BY v.branch_value ORDER BY 2 DESC;
```
**Classify each value, with its evidence** (the matrix's table "Branch values"):

| Evidence | Class |
|---|---|
| = the target's code (`&&BRANCH_CODE`) | **in** |
| = another branch of the group (g2: its code / short name), or the function maps it to another branch (g1) | **out** — that branch's |
| the function builds it from something else (a book, a folder, a counterparty attribute…) — g1 shows what | **in** if what it reads belongs to the target (the agent says why), else **out** |
| blank (no branch condition, or no branch row) | **out** — not asked `[BOX ACC expert, 2026-10-27]`; A-U7 keeps only properties with a branch value classified in |
| still unexplained after g1–g3 | **asked** — the evidence and a proposal shown, the value's PKs listed |

`&&OUT_BRANCH_CODES` = the values classified **out**; A-U7 uses it. The operator confirms the classification as a
whole (one answer), never value by value without evidence `[operator, 2026-10-23]`.

### A-U2 — What the target posted, per instrument × portfolio property × topic × account `Env: GBO` (optional diagnostic)

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

**`0` means "none"** `[2026-10-15]`: `FK_PROPERTIES = 0` = no portfolio property (technical / internal legs, mostly to
account `INTERNAL`); `FK_TOPIC = 0` = no topic (blank `topic_code`) — see A-U2b.

### A-U2b — Movements with no topic `Env: GBO` (optional diagnostic) 🆕 `[2026-10-15]`

```sql
SELECT m.FK_TOPIC, a.CODE AS account_code, m.FK_INSTRUMENT, COUNT(*) AS n_mov,
       (SELECT COUNT(*) FROM PGT_SYS.T_PGT_CROSS_ACCTCONF_S x
         WHERE x.FK_OWNER_OBJ = 18051.4 AND x.BRANCH = &&TARGET_BRANCH_PK AND x.TOPIC = m.FK_TOPIC) AS in_cross_conf
FROM   PGT_ACT.T_PGT_ACCT_MOV_S m
LEFT   JOIN PGT_ACT.T_PGT_ACCT_TOPICS_S t ON t.PK = m.FK_TOPIC
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S   a ON a.PK = m.FK_GLTA
WHERE  m.FK_BRANCH IN (&&TARGET_BRANCH_PK, &&TARGET_GROUP_PK)
AND    m.REGDATE >= DATE '&&USAGE_FROM' AND m.REGDATE < DATE '&&USAGE_TO'
AND    m.FK_INSTRUMENT IN (&&INSTRUMENT_PKS) AND t.PK IS NULL
GROUP  BY m.FK_TOPIC, a.CODE, m.FK_INSTRUMENT ORDER BY n_mov DESC;
```
NY: all `FK_TOPIC = 0`, accounts `09xxxx.xxx`, none in Cross Account Config — a route outside the configuration
screens; asked to the GBO accounting expert / BOX dev.

### A-U3 — Portfolio properties × topics still holding a balance `Env: GBO` (optional diagnostic)

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
~~`AMOUNT_CCY` / `AMOUNT_LOC` read as the key's balance~~ **Not balances** `[NY result, 2026-10-15]`: transitory
topics show tens of thousands of "open" keys. Read A-U3 as **"topic used on this property, last on `MAXDATE`"** —
it shows what a usage window misses (cancellations, year-end results, cash FX, memorandum topics), which is why
screen 4 copies **full lists**. Filter `k.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)` to keep it short.

### A-U4 — Configured vs used, per list `Env: GBO` (optional diagnostic)

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

### A-U4b — Who uses the configured combinations `Env: GBO` (optional diagnostic) 🆕 (optional cross-check)

A-U4 split by **user**: the target branch / only the group's other branches / nobody (`oth` = movements of
`&&GROUP_BRANCH_PKS` minus the target, same window). Not needed once screen 4 is scoped by the branch condition
(A-U1 f); kept to explain a large "configured, not used" count.

### A-U5 — The GBO source vs the target tier's GBO `Env: GBO` and `TGT` (optional — when the GBO source is not the target environment)

```sql
SELECT 'PORT_PROP' AS item, COUNT(*) AS n FROM PGT_ACT.T_PGT_ACCT_PORT_PROP_S
WHERE  FK_OWNER_OBJ = 12646.4 AND FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
UNION ALL
SELECT 'LIST_TOPIC rows', COUNT(*) FROM PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S lt
JOIN   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp ON pp.PK = lt.FK_PARENT AND pp.FK_OWNER_OBJ = 12646.4
WHERE  lt.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
UNION ALL
SELECT 'LIST_COND rows', COUNT(*) FROM PGT_ACT.T_PGT_ACCT_LIST_COND_S lc
JOIN   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp ON pp.PK = lc.FK_PARENT AND pp.FK_OWNER_OBJ = 12646.4
WHERE  lc.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
UNION ALL
SELECT 'CONF_LO_PROP', COUNT(*) FROM PGT_SYS.T_PGT_CONF_LO_PROP_S
WHERE  FK_OWNER_OBJ = 12642.4 AND FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
UNION ALL
SELECT 'CROSS_ACCTCONF target', COUNT(*) FROM PGT_SYS.T_PGT_CROSS_ACCTCONF_S
WHERE  FK_OWNER_OBJ = 18051.4 AND BRANCH = &&TARGET_BRANCH_PK;
```
Run in both; the usage source wins for "what is used". NY PRE PARALELO: 123 / 14,660 / 555 / 18 / 24
`[2026-10-15]`; Tier 2 PRE: Cross Account Config 17.

### A-U6 — Real accounts found outside the portfolio-property lists `Env: GBO` (optional diagnostic) 🆕 `[2026-10-15]`

```sql
WITH used AS (
  SELECT FK_INSTRUMENT, FK_PROPERTIES, FK_TOPIC, FK_GLTA, COUNT(*) AS n FROM PGT_ACT.T_PGT_ACCT_MOV_S
  WHERE  FK_BRANCH IN (&&TARGET_BRANCH_PK, &&TARGET_GROUP_PK)
  AND    REGDATE >= DATE '&&USAGE_FROM' AND REGDATE < DATE '&&USAGE_TO'
  AND    FK_INSTRUMENT IN (&&INSTRUMENT_PKS) AND FK_TOPIC <> 0
  GROUP  BY FK_INSTRUMENT, FK_PROPERTIES, FK_TOPIC, FK_GLTA),
nc AS (
  SELECT u.*,
         CASE WHEN NVL(u.FK_PROPERTIES, 0) = 0 THEN 'no portfolio property' ELSE 'topic not in its lists' END AS kind,
         CASE WHEN EXISTS (SELECT 1 FROM PGT_SYS.T_PGT_CROSS_ACCTCONF_S x
                           WHERE x.FK_OWNER_OBJ = 18051.4 AND x.BRANCH = &&TARGET_BRANCH_PK AND x.TOPIC = u.FK_TOPIC)
              THEN 'Y' ELSE 'N' END AS in_cross_conf
  FROM   used u
  WHERE  NOT EXISTS (SELECT 1 FROM PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S lt
                     WHERE lt.FK_PARENT = u.FK_PROPERTIES AND lt.FK_TOPIC = u.FK_TOPIC AND lt.FK_OWNER_OBJ = 12646.4))
SELECT sp.DESCRIPTION AS instrument, t.CODE AS topic_code, a.CODE AS account_code, nc.kind, nc.in_cross_conf,
       COUNT(*) AS combinations, SUM(nc.n) AS movements
FROM   nc
LEFT   JOIN PGT_ACT.T_PGT_ACCT_TOPICS_S  t  ON t.PK  = nc.FK_TOPIC
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S    a  ON a.PK  = nc.FK_GLTA
LEFT   JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = nc.FK_INSTRUMENT
WHERE  NVL(a.CODE, '-') NOT IN ('INTERNAL', 'INTERNAL1')
GROUP  BY sp.DESCRIPTION, t.CODE, a.CODE, nc.kind, nc.in_cross_conf ORDER BY 1, 2, 3;
```
**Gives** the routes other than the lists. NY: `EXTERNALSETTACC` → `817904-<currency>` all through Cross Account
Config (screen 3's source); two small exceptions with no route (`GENTRANSITCASH`, `FXNETLOSS`) — asked.

### A-U7 — The topics and accounts of the in-scope lists `Env: GBO` 🆕 `[2026-10-15]`

Both exclude the properties whose branch value is classified **out** by A-U1 (g) (`&&OUT_BRANCH_CODES` on
`&&BRANCH_COND_PKS`; it was `&&OTHER_BRANCH_CODES` - the group's other branches only - until 2026-10-23).

```sql
-- (a) topics: the input of the GBO -> BOX topic mapping (has_real_account = 1) and of screen 4
SELECT t.CODE AS topic_code, lt.FK_EXTENSION AS list_ext,
       COUNT(DISTINCT pp.FK_INSTRUMENT) AS n_instruments, COUNT(DISTINCT pp.PK) AS n_port_prop,
       COUNT(DISTINCT lt.FK_GLTA) AS n_accounts,
       MAX(CASE WHEN a.CODE IN ('INTERNAL', 'INTERNAL1') THEN 0 ELSE 1 END) AS has_real_account
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp
JOIN   PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S lt
       ON lt.FK_PARENT = pp.PK AND lt.FK_OWNER_OBJ = 12646.4 AND lt.FK_EXTENSION IN (38249.4, 38329.4, 38422.4)
LEFT   JOIN PGT_ACT.T_PGT_ACCT_TOPICS_S t ON t.PK = lt.FK_TOPIC
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S   a ON a.PK = lt.FK_GLTA
WHERE  pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
AND    pp.FK_INSTRUMENT IN (&&INSTRUMENT_PKS) AND pp.STATUS = 'Valid'          -- InValid never read (ADR 0014)
AND    EXISTS (SELECT 1 FROM PGT_ACT.T_PGT_ACCT_LIST_COND_S lc        -- a branch value, classified in (2026-10-27)
               WHERE lc.FK_PARENT = pp.PK AND lc.FK_OWNER_OBJ = 12646.4 AND lc.FK_EXTENSION = 38335.4
               AND lc.FK_CONDITION IN (&&BRANCH_COND_PKS) AND lc.VALUE_FUNC IS NOT NULL
               AND lc.VALUE_FUNC NOT IN (&&OUT_BRANCH_CODES))
GROUP  BY t.CODE, lt.FK_EXTENSION ORDER BY 1, 2;

-- (b) real accounts: screen 10's candidates (global accounts the target's group needs in BOX)
SELECT a.CODE AS account_code, COUNT(DISTINCT pp.PK) AS n_port_prop, COUNT(*) AS n_list_rows
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp
JOIN   PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S lt
       ON lt.FK_PARENT = pp.PK AND lt.FK_OWNER_OBJ = 12646.4 AND lt.FK_EXTENSION IN (38249.4, 38329.4, 38422.4)
JOIN   PGT_ACT.T_PGT_ACCT_GLTA_S a ON a.PK = lt.FK_GLTA
WHERE  pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
AND    pp.FK_INSTRUMENT IN (&&INSTRUMENT_PKS) AND a.CODE NOT IN ('INTERNAL', 'INTERNAL1')
AND    pp.STATUS = 'Valid'                                                     -- InValid never read (ADR 0014)
AND    EXISTS (SELECT 1 FROM PGT_ACT.T_PGT_ACCT_LIST_COND_S lc        -- a branch value, classified in (2026-10-27)
               WHERE lc.FK_PARENT = pp.PK AND lc.FK_OWNER_OBJ = 12646.4 AND lc.FK_EXTENSION = 38335.4
               AND lc.FK_CONDITION IN (&&BRANCH_COND_PKS) AND lc.VALUE_FUNC IS NOT NULL
               AND lc.VALUE_FUNC NOT IN (&&OUT_BRANCH_CODES))
GROUP  BY a.CODE ORDER BY 1;
```
NY: 65 properties in scope (58 NY_SCH + 1 INTERNAL + 6 CDS), 622 topic × list rows `[2026-10-15]` — counted before
the `Valid` filter (ADR 0014, 2026-10-22): re-run; the July usage (A-U2) only confirms them. **`'Valid'`** is written
as A-U1 (a) / (f) show the status (a different spelling there → use it).

**Running them:** the operator runs SQL with the values filled in (no `&&`) — the agent substitutes every value before
showing a query `[operator, 2026-10-15]`.

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
**Check — the condition map** `[ADR 0020]`: each GBO condition the target's in-scope properties use (A-04f, its
catalogue A-04g) is paired with its **twin in A-01-TGT**: automatically when the field domain is the same (`param_pk`,
e.g. Strategy, Instrument Type) or the description is the same text; otherwise the agent reads both functions (A-04h),
proposes the pair **and the value translation** (e.g. `SW` → `Swaption`, `PUR` → `1`) and asks the operator **once per
pair**. No twin → the GBO condition is **dropped** (listed per property). Written to
`runs/<BRANCH>/branch/acc-configs/condition-map.csv` (the same in every environment; BOX conditions recorded by
`NOM_FUNC` / domain, their PK read per environment from A-01-TGT). BOX conditions are never created or changed (ADR
0014); one the GBO property does not have is never added. **A value with no translation** `[2026-10-29]`: a kept
pair whose GBO function returns a value the BOX condition does not hold (NY: `f_GetOTCClass` → `SWAP` / `Accrual` /
`Touch2` where BOX's call/put condition holds `CALL` / `PUT` only) → those properties are **OPEN** on that condition (a
question for the BOX expert, the values listed) — the condition is never dropped for them alone (that could make new
clashes) and no value is invented.

### 2. Config. Local Properties — branch-group keyed, built from the target's GBO `[ADR 0020]`

**Build rule** `[BOX expert via operator, 2026-10-28]`: per instrument in scope, the local property holds the topics of
the target's `Valid` in-scope GBO portfolio properties (A-04e: by `CODE`, ADR 0018, each in the list — global / local /
internal — it has in GBO) and their conditions that have a BOX twin (A-04f + the condition map) — so that
`f_GenTopicCond` gives each BOX portfolio property exactly its GBO property's lists. **Check:** every in-scope GBO
property of the instrument has the same topics per list and the same conditions (NY: true for topics, rows ÷
properties is whole, [`box-acc-model.md`](../box-acc-model.md) §9.5); one that differs is a **finding** — BOX would
generate the missing rows empty and mark it `InValid`. A-02a / A-02b (the reference's) are a **comparison** only.

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
none, unless the group is shared — A-G1 (b)). The first **without** the group table (`BOX_ACC` cannot read
`T_PGT_BRANCH_GROUP_S` in DGBOUS; `FK_BRANCH` is the group) `[2026-10-29]`:
```sql
SELECT T1.PK AS lo_prop_pk, T2.PK AS instrument_pk, T2.DESCRIPTION AS instrument, T1.FK_BRANCH AS group_pk,
       T1.INIVALPCDATE, T1.DESCRIPTION, T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   BOX_ACC.T_BOX_CONF_LO_PROP_S T1, PGT_SYS.T_PGT_SUB_PRODUCT_S T2
WHERE  T1.FK_INSTRUMENT = T2.PK(+) AND T1.FK_OWNER_OBJ = 35000194.65
AND    T1.FK_BRANCH = &&TARGET_GROUP_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
ORDER  BY T2.DESCRIPTION, T1.INIVALPCDATE;
```
NY, DGBOUS, group `21447.4` `[2026-10-29]`: **0 rows** → screen 2 `create` for every instrument in scope.

**Start date:** every new local property starts on **01/01/1900** (`TO_DATE('01/01/1900','DD/MM/YYYY')`), a fixed
value, never asked `[BOX ACC expert, 2026-10-22]` — the reference's own `INIVALPCDATE` is shown, not copied.

**A-02d `Env: GBO`** — the target's GBO local properties (GBO trace), for comparison only. GBO local properties have
**one** topic array (`38192.4`) and conditions (`38196.4`); BOX has three topic arrays — the list of each topic is
read from the GBO **portfolio properties'** lists (A-04e), not from this array `[confirmed: M1, 2026-10-14; ADR 0020]`:
```sql
SELECT T1.PK AS lo_prop_pk, T2.PK AS instrument_pk, T2.DESCRIPTION AS instrument, T3.PK AS group_pk,
       T3.DESCRIPTION AS branch_group, T1.INIVALPCDATE, T1.DESCRIPTION
FROM   PGT_SYS.T_PGT_CONF_LO_PROP_S T1, PGT_SYS.T_PGT_SUB_PRODUCT_S T2, PGT_STC.T_PGT_BRANCH_GROUP_S T3
WHERE  T1.FK_INSTRUMENT = T2.PK(+) AND T1.FK_BRANCH = T3.PK(+) AND T1.FK_OWNER_OBJ = 12642.4
AND    T1.FK_BRANCH = &&TARGET_GROUP_PK;
```

### 3. Cross Account Config — branch keyed, from GBO `T_MAD_REVAL_ACCOUNTS` (translated)

`[BOX ACC expert, 2026-10-22]` The GBO source is **`<GBO schema>.T_MAD_REVAL_ACCOUNTS`** — `PGT_ES` in Tier 1 (Madrid
and SLB), `PGT_NY` for NY in Tier 2 (`&&TARGET_GBO_SCHEMA` / `&&REFERENCE_GBO_SCHEMA`) — **not**
`PGT_SYS.T_PGT_CROSS_ACCTCONF_S` (A-03d). Its columns differ from BOX's (A-P7): seen so far `PK`, `FK_BRANCH`
(→ `PGT_STC.T_PGT_BRANCH_S`), `FK_INSTRUMENT` (→ `PGT_SYS.T_PGT_SUB_PRODUCT_S`), `FK_GLTA` (→ `PGT_ACT.T_PGT_ACCT_GLTA_S`),
`TIPO`. BOX's (`T_BOX_CROSS_ACCTCONF_S`): `FK_BRANCH`, `FK_INSTRUMENT`, `FK_CURRENCY`, `FK_ENTITY`, `FK_TOPIC`,
`FK_ACCOUNT`, `ACC_TYPE`. BOX's reval package is `PKG_BOX_REVAL_ACCOUNTS` (model §7): `TIPO` is probably BOX's
`ACC_TYPE` — A-03b confirms it or not.

**A-03a `Env: GBO`** — the target branch's GBO rows (`SELECT *`: columns not assumed):
```sql
SELECT T1.*, T2.DESCRIPTION AS branch, T3.DESCRIPTION AS instrument, T4.CODE AS account_code
FROM   &&TARGET_GBO_SCHEMA.T_MAD_REVAL_ACCOUNTS T1, PGT_STC.T_PGT_BRANCH_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3,
       PGT_ACT.T_PGT_ACCT_GLTA_S T4
WHERE  T1.FK_BRANCH = T2.PK(+) AND T1.FK_INSTRUMENT = T3.PK(+) AND T1.FK_GLTA = T4.PK(+)
AND    T1.FK_BRANCH = &&TARGET_BRANCH_PK
AND    (T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS) OR T1.FK_INSTRUMENT IS NULL)
ORDER  BY T3.DESCRIPTION, T4.CODE;

-- (b) every branch's count in that table (does the target have rows? the model once read PGT_NY.T_MAD_* as empty)
SELECT T1.FK_BRANCH, T2.DESCRIPTION AS branch, COUNT(*) AS n
FROM   &&TARGET_GBO_SCHEMA.T_MAD_REVAL_ACCOUNTS T1, PGT_STC.T_PGT_BRANCH_S T2
WHERE  T1.FK_BRANCH = T2.PK(+) GROUP BY T1.FK_BRANCH, T2.DESCRIPTION ORDER BY 1;
```

**A-03b `Env: REF`** — **how the reference's GBO rows became its BOX rows**: GBO and BOX side by side by instrument and
account code (no row-level key between them). **Two extracts** — one per account (GBO, BOX), never one statement
`[operator, 2026-10-23]`; the agent joins them (full outer join on instrument + account code, `presence` both /
GBO only / BOX only):
```sql
-- A-03b-gbo-REF.csv - Tier 1 GBO account; &&REFERENCE_GBO_SCHEMA = the inputs' reference.gbo_schema (SLB: PGT_ES)
SELECT g.FK_INSTRUMENT, a.CODE AS account_code, g.TIPO, COUNT(*) AS gbo_rows
FROM   &&REFERENCE_GBO_SCHEMA.T_MAD_REVAL_ACCOUNTS g
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S a ON a.PK = g.FK_GLTA
WHERE  g.FK_BRANCH = &&REFERENCE_BRANCH_PK
GROUP  BY g.FK_INSTRUMENT, a.CODE, g.TIPO ORDER BY 1, 2, 3;

-- A-03b-box-REF.csv - Tier 1 BOX_ACC account
SELECT b.FK_INSTRUMENT, a.CODE AS account_code, b.ACC_TYPE, t.CODE AS topic_code, COUNT(*) AS box_rows,
       COUNT(DISTINCT b.FK_CURRENCY) AS n_currencies, COUNT(DISTINCT b.FK_ENTITY) AS n_entities,
       COUNT(*) - COUNT(b.FK_CURRENCY) AS no_currency, COUNT(*) - COUNT(b.FK_ENTITY) AS no_entity
FROM   BOX_ACC.T_BOX_CROSS_ACCTCONF_S b
LEFT   JOIN BOX_ACC.T_BOX_ACCT_GLTA_S   a ON a.PK = b.FK_ACCOUNT
LEFT   JOIN BOX_ACC.T_BOX_ACCT_TOPICS_S t ON t.PK = b.FK_TOPIC
WHERE  b.FK_OWNER_OBJ = 35000189.65 AND b.FK_BRANCH = &&REFERENCE_BRANCH_PK
GROUP  BY b.FK_INSTRUMENT, a.CODE, b.ACC_TYPE, t.CODE ORDER BY 1, 2, 3;
```
**Reading:** `TIPO` = `ACC_TYPE` on every `both` row → the rule `TIPO → ACC_TYPE`; otherwise `ACC_TYPE` is asked.
How BOX's currency, entity and topic are filled (one row per currency? `NULL`?) is the reference's pattern — the
column map of the matrix; what it does not explain is asked. `ACC_TYPE` is a plain number: `0` Posición Vencida, `1`
Posición Viva, `2` Balance de Posición Viva `[read: code, 2026-10-14]`. The account: by `CODE` (screen 10).

**A-03c `Env: TGT`** — the BOX trace with `&&TARGET_BRANCH_PK`: rows already there (expected none):
```sql
SELECT T1.PK, T1.FK_BRANCH, T1.FK_INSTRUMENT, T1.FK_CURRENCY, T1.FK_ENTITY, T1.FK_ACCOUNT, T1.FK_TOPIC, T1.ACC_TYPE
FROM   BOX_ACC.T_BOX_CROSS_ACCTCONF_S T1
WHERE  T1.FK_OWNER_OBJ = 35000189.65 AND T1.FK_BRANCH = &&TARGET_BRANCH_PK;
```

**A-03d `Env: GBO`** — GBO's own Cross Account Config (`PGT_SYS.T_PGT_CROSS_ACCTCONF_S`, owner `18051.4`): **not**
screen 3's source (ADR 0014). Kept as usage evidence (A-U1 d, A-U6: the target's settlement accounts by currency);
their BOX route is a question for the BOX team:
```sql
SELECT T1.PK, T2.PK AS branch_pk, T3.PK AS instrument_pk, T3.DESCRIPTION AS instrument,
       T4.SHORTNAME AS currency, T5.PK AS entity_pk, T6.CODE AS account_code, T7.CODE AS topic_code
FROM   PGT_SYS.T_PGT_CROSS_ACCTCONF_S T1, PGT_STC.T_PGT_BRANCH_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3,
       PGT_STC.T_PGT_CURRENCY_S T4, PGT_STC.T_PGT_ENTITY_S T5, PGT_ACT.T_PGT_ACCT_GLTA_S T6,
       PGT_ACT.T_PGT_ACCT_TOPICS_S T7
WHERE  T1.BRANCH = T2.PK(+) AND T1.INSTRUMENT = T3.PK(+) AND T1.CURRENCY = T4.PK(+) AND T1.ENTITY = T5.PK(+)
AND    T1.ACCOUNT = T6.PK(+) AND T1.TOPIC = T7.PK(+) AND T1.FK_OWNER_OBJ = 18051.4
AND    T1.BRANCH = &&TARGET_BRANCH_PK;
```

### 4. Portfolio Properties — branch-group keyed; one per `Valid` in-scope GBO property `[ADR 0020]`

**Build rule** `[BOX expert via operator, 2026-10-28]`: every `Valid` in-scope GBO property (A-04d, scope A-U1 f / g)
becomes one BOX property — `DESCRIPTION` as GBO's; conditions: its GBO conditions with a BOX twin (A-04f + the
condition map, values translated), the others dropped and listed; topic → account rows: its own (A-04e). **Clash
group** = in-scope properties of one instrument (same group, same start date) whose kept condition values are
identical (masked values compared by their hash) — or with no kept condition at all while another exists: BOX
refuses them (`p_StatusPortFolio`). Clash mode asked every run: **(a)** hold them for the operator's choice (default),
**(b)** create all, the clashing ones `InValid`. A-04a / A-04b (the reference's) are a comparison only.
**Duplicates** `[2026-10-29, ADR 0023]`: two GBO properties are duplicates only when **every** GBO condition value
(hashes included, A-04f) **and** every topic → account row (A-04e) are the same — shown per pair with that evidence. A
rule that keeps one of them (e.g. "keep the `.44`") is a **proposal for the BOX expert**, applied only once the
operator answers it; until then the group stays held. NY (PRE PARALELO): no `.35` / `.44` pair is a duplicate — the
OTC pairs differ on Instrument Type (`102.4`, kept → no clash), the Caps / OTC swaption pairs on Folder (`36.35`,
dropped) and their accounts.

**A-04a `Env: REF`** — the reference group's portfolio properties (BOX trace + filters):
```sql
SELECT T1.PK AS port_prop_pk, T2.PK AS group_pk, T2.DESCRIPTION AS branch_group, T3.PK AS instrument_pk,
       T3.DESCRIPTION AS instrument, T1.INIVALPCDATE, T1.STATUS, T1.DESCRIPTION
FROM   BOX_ACC.T_BOX_ACCT_PORT_PROP_S T1, PGT_STC.T_PGT_BRANCH_GROUP_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3
WHERE  T1.FK_BRANCH = T2.PK AND T1.FK_INSTRUMENT = T3.PK AND T1.FK_OWNER_OBJ = 35000170.65
AND    T1.FK_BRANCH = &&REFERENCE_GROUP_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
ORDER  BY T3.DESCRIPTION, T1.INIVALPCDATE;
```
Real columns of `BOX_ACC.T_BOX_ACCT_PORT_PROP_S` (A-P7, Tier 2 PRE, 2026-10-23): `PK`, `FK_OWNER_OBJ`, `FK_PARENT`,
`FK_EXTENSION`, `FK_BRANCH` (the **group**), `FK_INSTRUMENT`, `INIVALPCDATE`, `DESCRIPTION`, `LSTMNTDATE`,
`LSTMNTUSER`, `STATUS`, `MESSAGE` — **no `FK_GROUP`, `NAME`, `FK_INILOCPROPERTY`** (written by the NY run of
2026-10-23 instead of this query; the group is `FK_BRANCH`).

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
**A-04c `Env: TGT`** — A-04a / A-04b with `&&TARGET_GROUP_PK`: already there (expected none). A-04a's text joins
`T_PGT_BRANCH_GROUP_S` (an inner join: no grant → ORA-00942) — in the target, without it `[2026-10-29]`:
```sql
SELECT T1.PK AS port_prop_pk, T1.FK_BRANCH AS group_pk, T3.PK AS instrument_pk, T3.DESCRIPTION AS instrument,
       T1.INIVALPCDATE, T1.STATUS, T1.DESCRIPTION
FROM   BOX_ACC.T_BOX_ACCT_PORT_PROP_S T1, PGT_SYS.T_PGT_SUB_PRODUCT_S T3
WHERE  T1.FK_INSTRUMENT = T3.PK AND T1.FK_OWNER_OBJ = 35000170.65
AND    T1.FK_BRANCH = &&TARGET_GROUP_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
ORDER  BY T3.DESCRIPTION, T1.INIVALPCDATE;
```

**A-04d `Env: GBO`** — the target's **GBO** portfolio properties (GBO trace + filter) — **the source** of the BOX ones
(one each; the in-scope ones per A-U1 f / g):
```sql
SELECT T1.PK AS port_prop_pk, T2.PK AS group_pk, T3.PK AS instrument_pk, T3.DESCRIPTION AS instrument,
       T1.INIVALPCDATE, T1.STATUS, T1.DESCRIPTION
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S T1, PGT_STC.T_PGT_BRANCH_GROUP_S T2, PGT_SYS.T_PGT_SUB_PRODUCT_S T3
WHERE  T1.FK_BRANCH = T2.PK AND T1.FK_INSTRUMENT = T3.PK AND T1.FK_OWNER_OBJ = 12646.4
AND    T1.FK_BRANCH = &&TARGET_GROUP_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
AND    T1.STATUS = 'Valid';                                                    -- InValid never read (ADR 0014)
```
**A-04e `Env: GBO`** — its topic → account lists, per list (GBO: owner `12646.4`, extensions `38249.4` global,
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
                       WHERE FK_OWNER_OBJ = 12646.4 AND STATUS = 'Valid'
                       AND FK_BRANCH = &&TARGET_GROUP_PK AND FK_INSTRUMENT IN (&&INSTRUMENT_PKS))
ORDER  BY l.FK_PARENT, l.FK_EXTENSION, tp.CODE;
```
GBO → BOX topics **by `CODE`** `[BOX ACC expert, 2026-10-27 — ADR 0018]`: a GBO topic is the BOX topic of the same
`CODE`; one with no BOX twin is created as a global topic (screen 6) — the GBO list row's **account** is kept. Each BOX
property takes **its own** GBO property's rows (ADR 0020); a topic with several accounts in one GBO property (A-04i)
→ **the operator's decision** (BOX: one row per topic and list).

**A-04i `Env: GBO`** 🆕 `[2026-10-28]` — topics with several accounts in one in-scope GBO property (GBO's list table has
only `PK`, `FK_OWNER_OBJ`, `FK_PARENT`, `FK_EXTENSION`, `FK_TOPIC`, `FK_GLTA`: nothing else tells the rows apart). Run
after A-04e; no row → nothing to ask:
```sql
SELECT pp.FK_INSTRUMENT, lt.FK_PARENT AS port_prop_pk, lt.FK_EXTENSION AS list_ext, t.CODE AS topic_code,
       a.CODE AS account_code, lt.PK AS row_pk
FROM   PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S lt
JOIN   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp ON pp.PK = lt.FK_PARENT
LEFT   JOIN PGT_ACT.T_PGT_ACCT_TOPICS_S t ON t.PK = lt.FK_TOPIC
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S   a ON a.PK = lt.FK_GLTA
WHERE  lt.FK_OWNER_OBJ = 12646.4 AND lt.FK_EXTENSION IN (38249.4, 38329.4, 38422.4)
AND    pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
AND    pp.FK_INSTRUMENT IN (&&INSTRUMENT_PKS) AND pp.STATUS = 'Valid'          -- InValid never read (ADR 0014)
AND    (lt.FK_PARENT, lt.FK_EXTENSION, lt.FK_TOPIC) IN
       (SELECT FK_PARENT, FK_EXTENSION, FK_TOPIC FROM PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S
        WHERE  FK_OWNER_OBJ = 12646.4 AND FK_EXTENSION IN (38249.4, 38329.4, 38422.4)
        GROUP  BY FK_PARENT, FK_EXTENSION, FK_TOPIC HAVING COUNT(DISTINCT FK_GLTA) > 1)
ORDER  BY 1, 2, 3, 4, 6;
```
(The agent keeps only the in-scope properties — A-U1 f / g.)

**A-04i (b)** 🆕 `[2026-10-29]` — when A-04i returns **0 rows** but a case is expected (an earlier run, another GBO
source): the same properties checked by topic **`CODE`** (BOX matches topics by code — two topic PKs with one code are
one BOX topic) and counting rows **without an account** (`COUNT(DISTINCT FK_GLTA)` ignores them):
```sql
SELECT lt.FK_PARENT AS port_prop_pk, lt.FK_EXTENSION AS list_ext, t.CODE AS topic_code,
       COUNT(*) AS n_rows, COUNT(DISTINCT lt.FK_TOPIC) AS n_topic_pks,
       COUNT(DISTINCT lt.FK_GLTA) AS n_accounts, COUNT(*) - COUNT(lt.FK_GLTA) AS n_no_account,
       MIN(a.CODE) AS acc_min, MAX(a.CODE) AS acc_max
FROM   PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S lt
LEFT   JOIN PGT_ACT.T_PGT_ACCT_TOPICS_S t ON t.PK = lt.FK_TOPIC
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S   a ON a.PK = lt.FK_GLTA
WHERE  lt.FK_OWNER_OBJ = 12646.4 AND lt.FK_PARENT IN (&&PORT_PROP_PKS)
GROUP  BY lt.FK_PARENT, lt.FK_EXTENSION, t.CODE
HAVING COUNT(*) > 1
ORDER  BY 1, 2, 3;
```
`n_topic_pks` > 1 or `n_no_account` > 0 → A-04i misses that case: report it, it is decided like A-04i's.
**The cases depend on the GBO source** `[operator, 2026-10-29]`: NY's 14 cases (OTC `2485.35` / `2487.35`) were read
in GBO **PRE** (2026-10-28); in **PRE PARALELO** (2026-10-29) A-04i and (b) return none. A-04i runs in every gap run
against that run's GBO source; a decision recorded from another source is shown with it, never applied blindly. **Decision, asked** (`decisions.multi_account_topics`,
ADR 0020 point 6): the cases `INTERNAL` + exactly one real account → **one** question for all of them (keep the real
account — proposed — or `INTERNAL`); any other case → the account to keep, once per identical case (same list, topic
and accounts). Shown with both accounts and which row is newer (`row_pk`). Never chosen by the agent. The in-scope lists are taken **in full** (A-U7; no usage window, ADR 0015). **Internal-list
topics** take the internal account the reference's internal lists hold (A-04b `internal`: `INTERNAL`), never none
(ADR 0014). A-04a–A-04h are the input of `03-portfolio-properties-report.md` (the condition map, GBO → BOX per
property, the clashes).

**A-04g `Env: GBO`** 🆕 `[2026-10-28]` — the GBO conditions the in-scope properties use, every column (their type and
field domain are compared with A-01-TGT's; `&&GBO_COND_PKS` = A-U1 (b)'s `FK_CONDITION` of the instruments in scope).
Run **before** A-04f: it says which conditions return a portfolio, a counterparty or an entity:
```sql
SELECT * FROM PGT_SYS.T_PGT_CONDPAR_PROP_S WHERE PK IN (&&GBO_COND_PKS) ORDER BY PK;
```
`&&MASKED_COND_PKS` = the conditions whose function returns a portfolio, a counterparty or an entity (its name or
description; A-04h when unclear — masked when in doubt; none → `-1`).

**A-04f `Env: GBO`** 🆕 `[2026-10-28]` — each in-scope `Valid` GBO property's conditions and values (the clash check and
the BOX values). A value naming a portfolio, a counterparty or an entity is **hashed**, never extracted (hard rule 7):
```sql
SELECT pp.PK AS port_prop_pk, pp.FK_INSTRUMENT, pp.INIVALPCDATE, lc.FK_CONDITION, cp.NOM_FUNC, cp.DESCRIPTION AS cond,
       CASE WHEN lc.FK_CONDITION IN (&&MASKED_COND_PKS) AND lc.VALUE_FUNC IS NOT NULL
            THEN 'H' || ORA_HASH(lc.VALUE_FUNC) ELSE lc.VALUE_FUNC END AS value_func,
       lc.FK_INSTRUMTYPE, it.DESCRIPTION AS instrum_type, lc.FK_STRATEGY, st.DESCRIPTION AS strategy,
       CASE WHEN lc.FK_PORTFOLIO    IS NULL THEN NULL ELSE 'H' || ORA_HASH(lc.FK_PORTFOLIO)    END AS portfolio_h,
       CASE WHEN lc.FK_COUNTERPARTY IS NULL THEN NULL ELSE 'H' || ORA_HASH(lc.FK_COUNTERPARTY) END AS counterparty_h
FROM   PGT_ACT.T_PGT_ACCT_PORT_PROP_S pp
JOIN   PGT_ACT.T_PGT_ACCT_LIST_COND_S lc ON lc.FK_PARENT = pp.PK AND lc.FK_OWNER_OBJ = 12646.4 AND lc.FK_EXTENSION = 38335.4
LEFT   JOIN PGT_SYS.T_PGT_CONDPAR_PROP_S cp ON cp.PK = lc.FK_CONDITION
LEFT   JOIN PGT_SYS.PGT_DOMAINS it ON it.PK = lc.FK_INSTRUMTYPE
LEFT   JOIN PGT_SYS.PGT_DOMAINS st ON st.PK = lc.FK_STRATEGY
WHERE  pp.FK_OWNER_OBJ = 12646.4 AND pp.FK_BRANCH IN (&&TARGET_GROUP_PK, &&TARGET_BRANCH_PK)
AND    pp.FK_INSTRUMENT IN (&&INSTRUMENT_PKS) AND pp.STATUS = 'Valid'          -- InValid never read (ADR 0014)
AND    EXISTS (SELECT 1 FROM PGT_ACT.T_PGT_ACCT_LIST_COND_S lb        -- a branch value, classified in (2026-10-27)
               WHERE lb.FK_PARENT = pp.PK AND lb.FK_OWNER_OBJ = 12646.4 AND lb.FK_EXTENSION = 38335.4
               AND lb.FK_CONDITION IN (&&BRANCH_COND_PKS) AND lb.VALUE_FUNC IS NOT NULL
               AND lb.VALUE_FUNC NOT IN (&&OUT_BRANCH_CODES))
ORDER  BY pp.FK_INSTRUMENT, pp.PK, lc.FK_CONDITION;
```
The same hash is the same value: two properties with equal hashes are equal on that condition. Other columns of the
GBO condition list (BOX's has `FK_DEALTREAT`, `FK_COLLATERALIND`, `STRUCTIND`…): A-P8 on
`PGT_ACT.T_PGT_ACCT_LIST_COND_S` first; add only the names it shows.

**A-04h `Env: GBO` or `TGT`** 🆕 `[2026-10-28]` — a condition function's source, to pair a GBO condition with a BOX one
when the field domain and the description do not say it (what each returns, its values): A-U1 **(g1)**'s text with
`&&FUNC_OWNER` / `&&FUNC_PACKAGE` / `&&FUNC_NAME` from the condition's `NOM_FUNC` — GBO in the GBO account, BOX in
the BOX_ACC account (one system per query). **Owner and package are read from `NOM_FUNC`** (A-04g / A-01), never
guessed; an empty result with the right names means the source is not visible to the account (`ALL_SOURCE`), not
that the function does not exist — NY, 2026-10-29: a BOX function's source came back empty with `NOM_FUNC`'s owner
and package (visibility, not a wrong name) → read in `cib-boxacc-dbboxacc`. Run A-04h **before** proposing a pair, and read what each function **returns** for each value, not its
name: `f_IsBuyReverse` returns `0` for a buy, `f_IsBuy` `1` (NY, 2026-10-29). A BOX package body not visible there (`ALL_SOURCE` may show the spec
only) is read in `cib-boxacc-dbboxacc` (read-only). The proposal shows both functions' lines and the value
translation; the operator confirms once per pair.

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
**Check:** every topic of A-02b and A-04b is in A-06-TGT (same PK and `CODE`); every GBO topic of the in-scope
lists (A-U7a) has a BOX topic of the **same `CODE`** (the mapping — ADR 0018). A GBO topic with no BOX twin →
**`create (global .65)`, *global — to review***: `CODE` and description from GBO (`PGT_ACT.T_PGT_ACCT_TOPICS_S`), the
global `.65` PK (not the installation's), listed in the matrix's *Global objects — to review* section with the
warning that a `.65` PK created in PRE may clash with production's; phase 2 puts them in `global_pk_rollback.sql` too.
A topic of the reference's arrays (A-02b) missing in the target → the same.

### 7. Standard Historic — global, verify

**A-07 `Env: both`** (BOX trace):
```sql
SELECT T1.PK, T1.HISTDESCR, T1.HISTCODE, T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   BOX_ACC.T_BOX_ACCT_HISTSTD T1 WHERE T1.FK_OWNER_OBJ = 35000180.65 ORDER BY T1.HISTDESCR;
```
**Check:** REF and TGT hold the same `(PK, HISTCODE)` set; a difference is reported. A standard historic the
branch needs (the reference's, used by its events) and missing in TGT → **`create (global .65)`, *global — to
review*** (as screen 6, ADR 0018); one only in TGT → nothing to do.

### 8. Event Grouping — global (shared `PGT_PRC`); verify

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
**Check:** every group and its events (same order) is in TGT. The branch runs the **global** groups — no branch copy,
nothing asked `[BOX ACC expert, 2026-10-22]`.

### 9. Event Config — global, verify

**A-09 `Env: both`** (trace), for the events of A-08b:
```sql
SELECT T1.PK AS event_pk, T1.NAME, T2.PK AS instrument_pk, T2.DESCRIPTION AS instrument, T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   PGT_PRC.T_PGT_EVE_S T1, PGT_SYS.T_PGT_SUB_PRODUCT_S T2
WHERE  T1.FK_INSTRUMENT = T2.PK(+) AND T1.FK_OWNER_OBJ = 12713.4
AND    T1.PK IN (SELECT EVENTCODE FROM PGT_PRC.T_PGT_BR_EVE_EXT_S WHERE FK_PARENT IN (&&GROUP_PKS))
ORDER  BY T1.NAME;
```
Global — never copied.

### 10. Global Accounts — from GBO

**Which accounts** `[2026-10-29]`: only those the **carried** configuration uses — the in-scope portfolio
properties' lists (A-U7b / A-04e) ∪ the Cross Account Config rows (A-03a) ∪ the Net CCS rows (A-13a, when screen 13
applies) — minus the ones BOX has (A-10b). The Net CCS accounts are the **reference's BOX rows** (BOX-side technical
accounts with no GBO row — A-13a gives them; the source in the values is A-13a, not A-10a). An account no source
has (neither the target's GBO nor, for Net CCS, the reference's BOX) → **OPEN** with a question, and every portfolio
property whose list uses it is **not carried** (it would be `InValid`). GBO accounts used only by properties out of
scope or not carried are listed as not carried. NY, DGBOUS: 455 codes in the lists ∪ 293 in Cross Account Config ∪ 11
Net CCS = 466 → 464 to create (`INTERNAL` present; `9614600-982058` in no table → OPEN, its 2 properties not carried);
32 GBO accounts not carried.

**A-10a `Env: GBO`** — the GBO accounts the target's GBO configuration uses (A-03a `account_code` + A-04e
`account_code`), as GBO has them (GBO trace + filter). The type and direction **codes** are read too — the
translation to BOX is by `CODE` (A-10e) `[2026-10-29]`:
```sql
SELECT T1.PK AS account_pk, T1.CODE, T1.SHORTNAME, T1.DESCRIPTION, T2.PK AS gltatype_pk, T2.DESCRIPTION AS gltatype,
       T2.CODE AS gltatype_code, T3.PK AS direction_pk, T3.DESCRIPTION AS direction, T3.CODE AS direction_code,
       T1.LOC_CODE, T1.FXADJUSTIND, T1.HOSTINTERFIND
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
A-03b / A-04b and the GBO accounts of the same codes — **two extracts** (BOX account, GBO account), joined by the
agent on `CODE` (same PK number, same short name / description, flags, group, type and direction codes, GBO lengths):
```sql
-- A-10c-box-REF.csv - Tier 1 BOX_ACC account
SELECT b.CODE, b.PK AS box_pk, b.SHORTNAME, b.DESCRIPTION, b.FXADJUSTIND, b.FK_BRANCHGROUP,
       bt.CODE AS gltatype_code, bd.CODE AS direction_code
FROM   BOX_ACC.T_BOX_ACCT_GLTA_S b
LEFT   JOIN PGT_SYS.PGT_DOMAINS bt ON bt.PK = b.FK_GLTATYPE
LEFT   JOIN PGT_SYS.PGT_DOMAINS bd ON bd.PK = b.FK_DIRECTION
WHERE  b.FK_OWNER_OBJ = 35000169.65 AND b.CODE IN (&&REFERENCE_ACCOUNT_CODES)
ORDER  BY b.CODE;

-- A-10c-gbo-REF.csv - Tier 1 GBO account
SELECT g.CODE, g.PK AS gbo_pk, g.SHORTNAME, g.DESCRIPTION, g.FXADJUSTIND, g.FK_BRANCHGROUP,
       gt.CODE AS gltatype_code, gd.CODE AS direction_code,
       LENGTH(g.CODE) AS len_code, LENGTH(g.SHORTNAME) AS len_short, LENGTH(g.DESCRIPTION) AS len_desc
FROM   PGT_ACT.T_PGT_ACCT_GLTA_S g
LEFT   JOIN PGT_SYS.PGT_DOMAINS gt ON gt.PK = g.FK_GLTATYPE
LEFT   JOIN PGT_SYS.PGT_DOMAINS gd ON gd.PK = g.FK_DIRECTION
WHERE  g.FK_OWNER_OBJ = 11910.4 AND g.CODE IN (&&REFERENCE_ACCOUNT_CODES)
ORDER  BY g.CODE;
```
GLTA type and direction are `PGT_DOMAINS` values owned by BOX's **Acct Indicator** (`35000173.65`) / **GLTA Type**
(`35000174.65`) and by GBO's own objects: translated **by `CODE`** — the pattern this query shows decides how a
missing account is created. **Lengths:** BOX `CODE` / `SHORTNAME` / `DESCRIPTION` hold 20 / 20 / 50 characters — a
GBO value longer than that is a finding, never truncated. An account is **one row** (+ an optional date rule,
`T_BOX_ACCT_PARENT_DATE_S`) — `p_AccountPrecommit` reads nothing else `[read: code, 2026-10-14]`.

**A-10d `Env: GBO`** — the target's GBO date rules for those accounts (copied only if they exist):
```sql
SELECT a.CODE, d.VALDATE, d.CODELOC, d.HOSTINTERF, p.CODE AS parent_account_code
FROM   PGT_ACT.T_PGT_ACCT_PARENT_DATE_S d
JOIN   PGT_ACT.T_PGT_ACCT_GLTA_S a ON a.PK = d.FK_PARENT AND a.FK_OWNER_OBJ = 11910.4
LEFT   JOIN PGT_ACT.T_PGT_ACCT_GLTA_S p ON p.PK = d.ACCT_PARENT
WHERE  d.FK_OWNER_OBJ = 11910.4 AND a.CODE IN (&&ACCOUNT_CODES)
ORDER  BY a.CODE, d.VALDATE;
```

**A-10e `Env: TGT`** 🆕 `[2026-10-29]` — BOX's account-type and direction values, to translate A-10a's codes into the
PKs the new accounts carry (`FK_GLTATYPE`, `FK_DIRECTION`). `BOX_ACC` account (NY's run: `B-01`); A-10a without its
code columns needs the GBO side's too (NY's run: `B-02`, GBO account, PKs of A-10a's types and directions):
```sql
SELECT d.FK_OWNER_OBJ, d.PK, d.CODE, d.DESCRIPTION
FROM   PGT_SYS.PGT_DOMAINS d
WHERE  d.FK_OWNER_OBJ IN (35000173.65, 35000174.65)            -- BOX Acct Indicator / GLTA Type
ORDER  BY d.FK_OWNER_OBJ, d.CODE;
```
**Reading:** each GBO code → the BOX value of the same `CODE`; a GBO code with no BOX twin → listed and asked
(never the nearest one).

### 11. MBJ Config — not this agent

The ACC jobs (`shell.conf`, Control-M, MBJ rows) belong with `box-acc-jobs-agent`. The reference's rows are J-R2 in
[`box-jobs-queries.md`](box-jobs-queries.md).

### 12. Conf Instru Type — branch keyed, the reference's BOX rows as they are 🆕 `[2026-10-22]`

`[BOX ACC expert, 2026-10-22]` Not read from GBO: the reference branch's BOX rows per instrument are applied to the new
branch as they are (its branch PK only). `T_BOX_CONF_INSTRUM_TYPE_S`, owner `35000292.65`: branch (NOT NULL),
instrument, `CODE`, `VALUE`, `TYPE`, `FK_INSTRUMENT_TYPE`, optional counterparty (model §8). Columns not assumed
(`SELECT *`); a column named otherwise → the error names it.

**A-12a `Env: REF`**:
```sql
SELECT T1.*, T2.DESCRIPTION AS instrument
FROM   BOX_ACC.T_BOX_CONF_INSTRUM_TYPE_S T1, PGT_SYS.T_PGT_SUB_PRODUCT_S T2
WHERE  T1.FK_INSTRUMENT = T2.PK(+) AND T1.FK_OWNER_OBJ = 35000292.65
AND    T1.FK_BRANCH = &&REFERENCE_BRANCH_PK AND T1.FK_INSTRUMENT IN (&&INSTRUMENT_PKS)
ORDER  BY T2.DESCRIPTION, T1.PK;
```
**A-12c `Env: TGT`** — the same with `&&TARGET_BRANCH_PK` (expected none). A reference row naming a counterparty is
not copied as it is: the target's counterparty is asked (never the reference's).

### 13. Net CCS PlanBS — the CCS end-of-month netting, the reference's rows as they are 🆕 `[2026-10-26]`

What it is: [`box-acc-model.md`](../box-acc-model.md) §8.1. **First, asked every run:** does the CCS end-of-month
netting apply to the branch? No → `N/A` (the operator's answer, dated). Yes → the reference's rows are proposed **as
they are** (same instrument types, strategies, `EOM_CCS_ACTIVE` switch row and accounts, by code); the operator
changes what the branch needs `[operator, 2026-10-26]`. Columns (the load PL, Tier 1): `PK`, `FK_OWNER_OBJ`,
`FK_PARENT`, `FK_EXTENSION`, `FK_GLTA`, `FK_BRANCH`, `FK_INSTRUMENT`, `FK_INSTRUMENT_TYPE`, `FK_STRATEGY`.

**A-13a `Env: REF`** (BOX_ACC account) — the reference's rows, with the codes:
```sql
SELECT n.PK, n.FK_INSTRUMENT, n.FK_INSTRUMENT_TYPE, t.DESCRIPTION AS instrument_type, n.FK_STRATEGY,
       n.FK_GLTA, a.CODE AS account_code, a.DESCRIPTION AS account_desc
FROM   BOX_ACC.T_BOX_NETCCS_BSPLAN_S n
LEFT   JOIN BOX_ACC.T_BOX_ACCT_GLTA_S a ON a.PK = n.FK_GLTA
LEFT   JOIN PGT_SYS.T_PGT_INSTRUMENT_TYPE_S t ON t.PK = n.FK_INSTRUMENT_TYPE
WHERE  n.FK_OWNER_OBJ = 35000348.65 AND n.FK_BRANCH = &&REFERENCE_BRANCH_PK
ORDER  BY n.FK_INSTRUMENT_TYPE, n.FK_STRATEGY, a.CODE;
```
**A-13b `Env: TGT`** — the same with `&&TARGET_BRANCH_PK` (expected none).

**A-13c `Env: TGT`** — what the copy needs in the target:
```sql
-- (0) where each field of the object points (the strategy's table is not assumed)
SELECT e.PK, e.FIELD, e.FK_OBJECT, o.PK_NAME, o.BASIC_STORAGE
FROM   GOM_GLB_SYS.T__EXT_DEF_S e LEFT JOIN GOM_GLB_SYS.T__OBJ_DEF_S o ON o.PK = e.FK_OBJECT
WHERE  e.FK_PARENT = 35000348.65 ORDER BY e.PK;
-- (1) the reference's instrument types exist (same PKs), and its strategies in the table (0) gives (SELECT *)
SELECT PK, DESCRIPTION FROM PGT_SYS.T_PGT_INSTRUMENT_TYPE_S WHERE PK IN (&&REF_INSTRUMENT_TYPE_PKS) ORDER BY PK;
SELECT * FROM &&STRATEGY_TABLE WHERE PK IN (&&REF_STRATEGY_PKS);
-- (2) the reference's account codes in the target's BOX (missing -> screen 10, or the reference's BOX row proposed
--     for a BOX-only technical account such as EOM_CCS_ACTIVE - the operator decides)
SELECT CODE, COUNT(*) AS n, MIN(PK) AS account_pk FROM BOX_ACC.T_BOX_ACCT_GLTA_S
WHERE  FK_OWNER_OBJ = 35000169.65 AND CODE IN (&&REF_NETTING_ACCOUNT_CODES) GROUP BY CODE ORDER BY CODE;
-- (3) the events, standard historics, topics and the accounts the postings use (verify - global)
SELECT 'EVENT' AS kind, TO_CHAR(PK) AS id, NAME AS label FROM PGT_PRC.T_PGT_EVE_S WHERE PK IN (5210.65, 5211.65)
UNION ALL SELECT 'HISTSTD', TO_CHAR(PK), HISTDESCR FROM BOX_ACC.T_BOX_ACCT_HISTSTD
WHERE  FK_OWNER_OBJ = 35000180.65 AND UPPER(HISTDESCR) LIKE '%NETTING MTM%'
UNION ALL SELECT 'TOPIC', CODE, DESCRIPTION FROM BOX_ACC.T_BOX_ACCT_TOPICS_S
WHERE  FK_OWNER_OBJ = 35000179.65 AND CODE IN (&&NETTING_INTERNAL_TOPICS, 'NIVELACION')
UNION ALL SELECT 'ACCOUNT', CODE, DESCRIPTION FROM BOX_ACC.T_BOX_ACCT_GLTA_S
WHERE  FK_OWNER_OBJ = 35000169.65 AND CODE IN ('FFM', 'INTERNAL')
ORDER  BY 1, 2;
```
`&&NETTING_INTERNAL_TOPICS` = the translator's internal topics and the gross ones (`TGROSSDEALREVAL`,
`TGROSSDEALDEVAL`, `TCTRGROSSREVAL`, `TCTRGROSSDEVAL`) — model §8.1. **Reading:** a missing instrument type /
strategy / event / historic / topic → a finding (global objects are never created by the agent); an account the
target's CCS portfolio properties (A-04e, screen 4) do not use on a translator topic is **shown** next to its row —
the operator decides whether to keep it. Instrument types (why the reference has the ones it has): its CCS types
whose `STM` parameter (`367.4`) is not `YES` — model §8.1. **The accounts** `[2026-10-29]`: the reference's
netting accounts are BOX-side technical accounts (no GBO row): missing in the target → created from the
**reference's BOX row** (A-13a, as it is) and counted with screen 10's. An account (3) needs that neither the target's
GBO nor the reference's BOX has (NY: `FFM`, absent from SLB's `T_BOX_ACCT_GLTA_S` too) → OPEN, a question for the BOX
expert; a row that names it is not carried.

### 14. Label aliases for MIC — per book label, the GL's code 🆕 `[2026-10-27]`

What and why: [`box-acc-model.md`](../box-acc-model.md) §8.2. Inputs: the branch's `runs/<BRANCH>/branch/books/label-aliases.csv` (the GL
team's code per book — from the operator) and `label_aliases.source` (the GL source PK, confirmed with the GL team).
No codes yet → every book `OPEN` (the run writes the list of the books with jobs to send to the GL team).

**A-14a `Env: REF`** — the reference's label aliases (the pattern: one per book with ACC jobs, one source):
```sql
SELECT d.CODE AS label_code, a.ALIASCODE, a.FK_SOURCE, s.DESCRIPTION AS source
FROM   PGT_TRD.T_PGT_OBJ_SOURCE_S a JOIN PGT_SYS.PGT_DOMAINS d ON d.PK = a.FK_PARENT
LEFT   JOIN PGT_SYS.T_PGT_SOURCE_S s ON s.PK = a.FK_SOURCE
WHERE  a.FK_OWNER_OBJ = 17910.4 AND a.FK_EXTENSION = 118615.4 AND d.CODE LIKE 'X' || '&&REFERENCE_TOKEN' || '%'
ORDER  BY d.CODE;
```
**A-14b `Env: TGT`** — the target's labels and their aliases (expected none):
```sql
SELECT d.PK AS label_pk, d.CODE AS label_code, a.ALIASCODE, a.FK_SOURCE
FROM   PGT_SYS.PGT_DOMAINS d
LEFT   JOIN PGT_TRD.T_PGT_OBJ_SOURCE_S a ON a.FK_PARENT = d.PK AND a.FK_OWNER_OBJ = 17910.4 AND a.FK_EXTENSION = 118615.4
WHERE  d.FK_OWNER_OBJ = 17910.4 AND d.CODE LIKE 'X' || '&&TARGET_TOKEN' || '%'
ORDER  BY d.CODE;
```
**A-14c `Env: TGT`** — the GL source and the codes already taken under it (`UN_..._002`: one label per code and
source):
```sql
SELECT PK, SHORTNAME, DESCRIPTION FROM PGT_SYS.T_PGT_SOURCE_S WHERE PK = &&ALIAS_SOURCE_PK;
SELECT a.ALIASCODE, d.CODE AS label_code FROM PGT_TRD.T_PGT_OBJ_SOURCE_S a JOIN PGT_SYS.PGT_DOMAINS d ON d.PK = a.FK_PARENT
WHERE  a.FK_OWNER_OBJ = 17910.4 AND a.FK_SOURCE = &&ALIAS_SOURCE_PK ORDER BY a.ALIASCODE;
```
**Reading:** per book label with ACC jobs (the books register minus `books-excluded.csv`): alias present for the
source → `present`; missing with a code in `label-aliases.csv` → `create` (SIGOM label screen, *Systems Alias* tab, or
phase 2's SQL — `P_SETHEADER`, both unique keys checked first); no code → `OPEN` (GL team); a code already taken under
the source by another label → a finding. An excluded book gets no alias. The source unconfirmed → the action stays
`create` with the source marked *to confirm*.

---

## Not in the Confluence checklist — rule in or out

**A-11 `Env: REF`** — for each object of A-G2 keyed on `pBranch` / `pLocalGroup` and **not** in the walk above:
its rows for the reference branch (or group). Rows for the reference and none expected to be transactional → a
candidate step, asked; transactional (movements, documents) → out, with the reason. **Columns first** `[2026-10-23]`
— the NY run counted `T_BOX_GLTA_LOCAL_S` on a column it does not have:
```sql
-- (a) the branch / group column of each table (the metamodel field pBranch / pLocalGroup is not the column name)
SELECT TABLE_NAME, COLUMN_NAME FROM ALL_TAB_COLUMNS
WHERE  OWNER = 'BOX_ACC' AND TABLE_NAME IN ('T_BOX_GLTA_LOCAL_S', 'T_BOX_CONF_ACCSTDHIST_S')
AND   (COLUMN_NAME LIKE '%BRANCH%' OR COLUMN_NAME LIKE '%GROUP%')
ORDER  BY 1, 2;
-- (b) per table, with the column (a) gives - e.g. GLTA Local Dep, expected FK_LOCALGROUP (box-data-model.md, not
--     confirmed): &&BRANCH_COLUMN = (a)'s column, the reference GROUP for a group-keyed table, the BRANCH otherwise
SELECT '&&TABLE' AS tbl, COUNT(*) AS n_rows FROM BOX_ACC.&&TABLE WHERE &&BRANCH_COLUMN = &&REFERENCE_PK;
```
No branch or group column in (a) → the table is global (not a branch step): say so, nothing counted.

**Rulings so far** `[2026-10-14]` ([`box-acc-model.md`](../box-acc-model.md) §8):

| Object | Ruling |
|---|---|
| Conf Instru Type (`T_BOX_CONF_INSTRUM_TYPE_S`, branch + instrument + `CODE` / `VALUE` / `TYPE`) | ~~candidate~~ **screen 12** (A-12): the reference's rows as they are `[BOX ACC expert, 2026-10-22]` |
| Net CCS PlanBS (`T_BOX_NETCCS_BSPLAN_S`, branch + account) | ~~candidate~~ **screen 13** (A-13): the CCS end-of-month netting — asked whether it applies, then the reference's rows as they are `[2026-10-26]` |
| GLTA Local Dep (`T_BOX_GLTA_LOCAL_S`, group) | check GBO's 2 rows (`T_PGT_GLTA_LOCAL_S`): one for the target's group? |
| Conf Acc By StdHist, Acct By Std Hist | 0 rows in PRE-PROD — out unless the reference has rows |
| Acct Key, Acct Key Group, Documents, Grouped Movements, Grouped Mov Config | runtime — out |
| Topic Group, Std Historic Group, Std Historic Source | global — verify |
| GBO ConcMis Balances / Mov (`15493.4` / `15494.4`) | **out** — nothing to do `[BOX ACC expert, 2026-10-27]` |
| A branch's own GBO topic tables (e.g. `PGT_NY.T_PGT_TOPICS_RR`, topic per instrument × buy/sell × near/far) | **out** — nothing to do `[BOX ACC expert, 2026-10-27]` |
