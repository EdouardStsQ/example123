# BOX ACC (and GBO accounting) — the configuration model, read from the database and the code

`[2026-10-14]` One page for the accounting module: what each SIGOM accounting screen stores, how GBO and BOX
compare, the identity values every row carries, the keys the database does (not) enforce, how PKs are made, what
runs on save, and how the topic / condition lists are generated. Written for
[`sigom-box-acc-configs-agent`](../../agents/sigom-box-acc-configs-agent/AGENT.md) and for anyone touching BOX_ACC
configuration. Queries: [`queries/acc-config-mining.md`](queries/acc-config-mining.md) (pre-checks `A-P…`, usage
`A-U…`, screens `A-0…`).

**Sources.** `[operator queries, PRE PARALELO, 2026-10-15]` = the usage queries A-G4, A-U0–A-U7 for NY SCH (§9).
`[read: DB PRE-PROD, 2026-10-14]` = the operator's structural queries D1–D2 (GBO), B1–B4 (BOX), M1–M3
(metamodel and the rows' identity values), all in the **PRE-PROD** environment (which tier it is: open — its Net
Contract rows suggest Tier 1). `[read: code, 2026-10-14]` = Devin, read-only, in `cib-boxacc-dbboxacc` (latest
versions: `PKG_ACCTPROP` r0.0.8, `PKG_ACCTPRECOMMIT` r0.0.14), file:line in the answers. `[operator, 2026-10-14]` =
stated by the operator. Row counts are **live `COUNT(*)`** unless marked "stats".

---

## 1. Same model in GBO and BOX

The BOX accounting tables are near-copies of GBO's: **same column names in the same order** (D2 vs B2). Moving data
from GBO to BOX is about **values** (PKs, owner objects, domain values), not columns. The one real column mapping is
Cross Account Config. `[BOX ACC expert, 2026-10-22]` **"Similar, not identical"**: a column may still be added,
removed or renamed between GBO and BOX — every copy compares both tables' columns first (A-P7,
[ADR 0014](../decisions/0014-box-acc-expert-review-1.md)).

| Screen / role | GBO table (owner object) | BOX table (owner object) | Columns |
|---|---|---|---|
| Condition Port Properties | `PGT_SYS.T_PGT_CONDPAR_PROP_S` (`12638.4`) | `BOX_ACC.T_BOX_CONDPAR_PROP_S` (`35000197.65`) | identical |
| Config. Local Properties | `PGT_SYS.T_PGT_CONF_LO_PROP_S` (`12642.4`) | `T_BOX_CONF_LO_PROP_S` (`35000194.65`) | identical; **arrays differ** (§4) |
| Portfolio Properties | `PGT_ACT.T_PGT_ACCT_PORT_PROP_S` (`12646.4`) | `T_BOX_ACCT_PORT_PROP_S` (`35000170.65`) | identical — keyed on **`FK_BRANCH` = the branch group** |
| its topic → account lists | `PGT_ACT.T_PGT_ACCT_LIST_TOPIC_S` | `T_BOX_ACCT_LIST_TOPIC_S` | identical (`FK_PARENT`, `FK_TOPIC`, `FK_GLTA`) |
| its condition lists | `PGT_ACT.T_PGT_ACCT_LIST_COND_S` | `T_BOX_ACCT_LIST_COND_S` | identical (`FK_CONDITION`, `VALUE_FUNC`, `FK_PORTFOLIO`, `FK_COUNTERPARTY`, `FK_STRATEGY`, …) |
| Cross Account Config | ~~`PGT_SYS.T_PGT_CROSS_ACCTCONF_S`~~ — **BOX's source is `<GBO schema>.T_MAD_REVAL_ACCOUNTS`** (`PGT_ES` Tier 1, `PGT_NY` NY Tier 2; `PK`, `FK_BRANCH`, `FK_INSTRUMENT`, `FK_GLTA`, `TIPO`…) `[BOX ACC expert, 2026-10-22]`; GBO's `T_PGT_CROSS_ACCTCONF_S` (`18051.4`) compared below | `T_BOX_CROSS_ACCTCONF_S` (`35000189.65`) | vs `T_PGT_CROSS_ACCTCONF_S` **renamed**: `BRANCH` → `FK_BRANCH`, `CURRENCY`, `INSTRUMENT`, `ENTITY`, `TOPIC`, `ACCOUNT` → `FK_…`; BOX adds **`ACC_TYPE`**; every BOX column nullable (GBO: branch, topic, account NOT NULL) |
| Accounting Topics | `PGT_ACT.T_PGT_ACCT_TOPICS_S` (`11980.4`) | `T_BOX_ACCT_TOPICS_S` (`35000179.65`) | identical (BOX `CODE` 15 chars) |
| Standard Historic | `PGT_ACT.T_ACCT_HISTSTD` (`11873.4`) | `T_BOX_ACCT_HISTSTD` (`35000180.65`) | identical |
| Global Accounts (GLTA) | `PGT_ACT.T_PGT_ACCT_GLTA_S` (`11910.4`) | `T_BOX_ACCT_GLTA_S` (`35000169.65`) | identical 22 columns incl. `FK_BRANCHGROUP`, `BYKEY`, `COMPLEM_CODE` (BOX `CODE` / `SHORTNAME` / `DESCRIPTION` = 20 / 20 / 50 chars) |
| account date rules | `PGT_ACT.T_PGT_ACCT_PARENT_DATE_S` | `T_BOX_ACCT_PARENT_DATE_S` | identical |
| Movements / documents | `PGT_ACT.T_PGT_ACCT_MOV_S` (1.1 bn stats, partitioned) / `T_PGT_ACCT_DOC_S` | `T_BOX_ACCT_MOV_S` (partitioned) / `T_BOX_ACCT_DOC_S` (+ `EXTERNAL_ID`, `FK_EXT_SOURCESYSTEM`) | identical (38 movement columns) |
| Keys / balances | `T_PGT_ACCT_KEY_S`, `T_PGT_ACCT_KEY_GROUP_S`, `T_PGT_ACCT_RULER` (partitioned) | `T_BOX_ACCT_KEY_S`, `…_KEY_GROUP_S`, `T_BOX_ACCT_RULER_S` | identical |

**Size** `[read: DB PRE-PROD, 2026-10-14]`: BOX holds far fewer rows — portfolio properties 71 (GBO 2,476), local
properties 14 (60), Cross Account Config 2 (17), topics 1,090 (2,004), accounts 1,539 (6,001). GBO's portfolio
properties are **consolidated** into fewer BOX ones (BOX team, [05-add-product](../process/05-add-product-procedure.md)):
portfolio properties are an analysis, not a transcription.

**Movements carry the portfolio property** (`FK_PROPERTIES` = metamodel field `pPropPos` → Acct Port Property, both
systems), with `FK_TOPIC` and `FK_GLTA`: what a branch *uses* is read from its movements (pre-check A-U2). BOX
movements, keys and documents also point at the FE deal (`pBOXDealDataPK` / `pDealID` → `BOX_FE.T_BOX_DEAL_DATA_S`), so
a future ACC test can trace a BOX movement to its `FRONT_ID`. Because BOX consolidates portfolio properties, GBO vs
BOX movements compare at **account × topic × currency**, not per portfolio property.

## 2. Identity values — `FK_OWNER_OBJ` / `FK_EXTENSION` per table

The metamodel rule ([`sigom-metamodel.md`](sigom-metamodel.md) §3) holds in both systems, confirmed against the rows
(M2, M3): a base table carries its object's PK and a null extension; an extension table carries the **parent
object** and the extension's PK. **The topic and condition lists are extensions of the portfolio-property object** —
not rows of the "Acct Topic List" / "Acct List Cond" objects (`35000171.65` / `35000172.65`, GBO `12653.4` /
`12650.4`), which no row carries.

| BOX table | `FK_OWNER_OBJ` | `FK_EXTENSION` | Rows | GBO equivalent (owner / extension) |
|---|---|---|---|---|
| `T_BOX_ACCT_PORT_PROP_S` | `35000170.65` | null | 71 | `12646.4` / null (2,476) |
| `T_BOX_ACCT_LIST_TOPIC_S` | `35000170.65` | `amAcctList` **`35001510.65`** (3,350) · `amAcctList1` **`35001513.65`** (1,600) · `amAcctList2` **`35001518.65`** (858) | 5,808 | `12646.4` / `38249.4` (193 k) · `38329.4` (27 k) · `38422.4` (55 k) |
| `T_BOX_ACCT_LIST_COND_S` | `35000170.65` | `amCondList` **`35001514.65`** | 257 | `12646.4` / `38335.4` (16 k) |
| `T_BOX_CONF_LO_PROP_S` | `35000194.65` | null | 14 | `12642.4` / null (60) |
| `T_BOX_LINK_ARRAY_X` (local properties) | `35000194.65` | `apLocalTopicArray` **`35001814.65`** (292) · `apGlobalTopicArray` **`35003724.65`** (506) · `apInternalTopicArray` **`35003725.65`** (115) · `apCondArray` **`35001818.65`** (34) | 947 | `PGT_SYS.T_PGT_LINK_ARRAY_X` `12642.4` / **one** `apTopicArray` `38192.4` (608) · `apCondArray` `38196.4` (290) |
| `T_BOX_CROSS_ACCTCONF_S` | `35000189.65` | null | 2 | `18051.4` / null (17) |
| `T_BOX_ACCT_GLTA_S` | `35000169.65` | null | 1,539 | `11910.4` / null (6,001) |
| `T_BOX_ACCT_PARENT_DATE_S` | `35000169.65` (the account object) | `amDateDep` `35001497.65` | 2 | GBO `amDateDep` `41605.4` |
| `T_BOX_CONF_INSTRUM_TYPE_S` | `35000292.65` | null | 3 | — |
| `T_BOX_NETCCS_BSPLAN_S` | `35000348.65` | null | 66 | — |
| `T_BOX_ACCT_TOPICS_S` / `T_BOX_CONDPAR_PROP_S` / `T_BOX_ACCT_HISTSTD` | `35000179.65` / `35000197.65` / `35000180.65` | null | 1,090 / 32 / 467 | `11980.4` / `12638.4` / `11873.4` |
| `T_BOX_LINK_ARRAY_X` (others) | Std Historic Group `35000235.65` / `35003796.65` (22); Topic Group `35000236.65` / `35003798.65` (84) | | | GBO Std Historic Group `15500.4` |
| `T_BOX_NETCONTRACT_S` | **null** (all 112 rows — copied by a PL, not through SIGOM) | null | 112 | Madrid only |

**GBO vs BOX lists pair by field name** (`amAcctList` ↔ `amAcctList`, `amAcctList1` ↔ `amAcctList1`, …), so GBO and
BOX lists are compared list by list.

**Negative owners = test / deleted rows** `[operator, 2026-10-14]` (e.g. one GBO topic with `FK_OWNER_OBJ =
-11980.4`). No code creates or filters them `[read: code, 2026-10-14]` — the convention is data only. **Every read
filters on the exact positive owner**; negative-owner rows are excluded and listed as evidence, never compared or
copied.

**Shared link-array tables.** `PGT_SYS.T_PGT_LINK_ARRAY_X` (GBO) also serves User, Transaction Status, Instrument,
Listener Profile, Entity Contract Type, Economic Group, STP Status / System; `PGT_ACT.T_PGT_LINK_ARRAY_X` serves
**ConcMis Balances / ConcMis Mov** (`15493.4` / `15494.4`) and Std Historic Group (`15500.4`); BOX's serves nine objects
(metamodel §4). **Read them by owner + extension, never by `FK_PARENT` alone.** Arrays declared but unused: GLTA's
`apRefAcc` (no rows in GBO or BOX), Conf Instru Type's extension slot.

## 3. Keys, sequences, triggers — what the database enforces

`[read: DB PRE-PROD, 2026-10-14]` (B3, B4a; the repo agrees `[read: code]`).

- **No foreign key anywhere.** Every table has its `PK` constraint only, plus three unique keys:
  `T_BOX_CONF_LO_PROP_S (FK_INSTRUMENT, FK_BRANCH, INIVALPCDATE)` — one local property per group × instrument ×
  start date; `T_BOX_CONDPAR_PROP_S (FK_PARAMFIELD)`; `T_BOX_ACCT_MOV_S (PK, REGDATE)`. A wrong reference (group PK vs
  branch PK, a missing topic or account, the wrong extension) is **accepted silently**; a re-run **inserts duplicates**
  (no unique key on portfolio properties, lists, Cross Account Config, accounts' `CODE`, array rows).
- **No column has a default.** NOT NULL columns per table the agent writes: portfolio properties and local properties
  `PK`, `FK_OWNER_OBJ`, `FK_INSTRUMENT`, `FK_BRANCH`, `INIVALPCDATE`; topic list `PK`, `FK_OWNER_OBJ`, `FK_TOPIC`; condition
  list `PK`, `FK_OWNER_OBJ`, `FK_CONDITION`; accounts `PK`, `FK_OWNER_OBJ`, `CODE`, `FK_GLTATYPE`, `FK_DIRECTION`,
  `FXADJUSTIND`; link array `PK`, `FK_OWNER_OBJ`, **`FK_EXTENSION`** (BOX; `FK_BS` nullable — the reverse of GBO
  `PGT_SYS`); Cross Account Config `PK` only (the GBO rule — branch, topic, account always set — still applies).
- **Sequences:** one `SPK_<table>` per table in `BOX_ACC` (e.g. `SPK_T_BOX_ACCT_PORT_PROP_S` next 89,
  `SPK_T_BOX_CONF_LO_PROP_S` 33, `SPK_T_BOX_LINK_ARRAY_X` 2,872, `SPK_T_BOX_CROSS_ACCTCONF_S` 3,
  `SPK_T_BOX_ACCT_GLTA_S` 16,701, `SPK_T_BOX_ACCT_LIST_TOPIC_S` 107,650); runtime ones `S_BOX_ACCT_KEY`,
  `S_BOX_ACCT_MOV_PK`, … **Some lag behind their data** — conditions 8 vs 32 rows, topics 17 vs 1,090, standard
  historic 2 vs 467 — because seed data was loaded with hard-coded PKs (Liquibase, §6). `SPK_T_BOX_CONF_LO_PROP_S`
  **exists in the database but has no file in the repo** (created outside it).
- **Triggers** (BOX_ACC config tables): `G_T_BOX_ACCT_PORT_PROP_S_BIU` (sets `LSTMNTDATE`, `LSTMNTUSER`),
  `G_T_BOX_CROSS_ACCTCONF_S_BIU` (sets `INPUTDATE` / `INPUTUSER` on first write, `LSTMNTDATE` / `LSTMNTUSER` always),
  `G_BOX_ACCT_HISTSTD_BIU`, `G_T_BOX_CONDPAR_PROP_S_BD` (before delete), `G_T_BOX_NETCONTRACT_S_BIU`. **None** on local
  properties, link arrays, the lists, date rules or accounts.
- **Optimizer statistics are stale** (several tables last analyzed 2022–2025): `NUM_ROWS` is never evidence of a
  count — `COUNT(*)` only.

## 4. How a portfolio property gets its lists — `PKG_ACCTPROP.f_GenTopicCond`

`[read: code, 2026-10-14]` (`PKG_ACCTPROP` r0.0.8: `004-pkg_acctprop_hdr.sql:13-26`, `005-pkg_acctprop_body.sql`).

1. From the portfolio property's `FK_INSTRUMENT`, `FK_BRANCH` (group), `INIVALPCDATE`, it picks the local property with
   the same instrument and group and the **latest `INIVALPCDATE` ≤ the portfolio property's** (`:214-237`). So a new
   portfolio property's start date must be **≥ its local property's**.
2. It reads the four arrays of that local property (`T_BOX_LINK_ARRAY_X`, owner `35000194.65`, parent = the local
   property PK) and inserts the missing list rows:

   | Local-property array (`FK_EXTENSION`) | → portfolio-property list (`FK_EXTENSION`) |
   |---|---|
   | `apGlobalTopicArray` `35003724.65` | `amAcctList` `35001510.65` (global topics) |
   | `apLocalTopicArray` `35001814.65` | `amAcctList1` `35001513.65` (local topics) |
   | `apInternalTopicArray` `35003725.65` | `amAcctList2` `35001518.65` (internal topics) |
   | `apCondArray` `35001818.65` | `amCondList` `35001514.65` (conditions) |

3. Each row: `PK` and `FK_OWNER_OBJ` (`35000170.65`) from `PKG_SIGOM_COV.P_SETHEADER`, `FK_PARENT` = the portfolio
   property, the extension above, `FK_TOPIC` / `FK_CONDITION`; condition `141.4` also gets `STRUCTIND = 0`.
   **`FK_GLTA` is never set** (`:263-285`, `:405-466`) — the account is filled afterwards (in practice on the screen);
   no code UPDATEs it.
4. `p_ClearList` deletes list rows whose topic / condition is no longer in the local property's arrays (`:20-127`).
5. `PKG_ACCTPRECOMMIT.p_StatusPortFolio` is called at the end and writes `STATUS` / `MESSAGE` (`:479-489`).
6. **No COMMIT** in either routine: the caller commits (a whole configuration run can be rolled back).

⚠️ **Version-dependent.** In older versions (r0.0.3, r0.0.5) the global and internal arrays were read from the
**instrument-level** configuration (`CST_OWN_INSTRUMENT`, parent = the instrument; `001-pkg_acctprop_body.sql:160-178`),
not from the local property. The mapping above holds **only where r0.0.8 is deployed** — checked per environment
from `BOX_ACC.DATABASECHANGELOG` (pre-check A-P6). GBO's local properties have a single topic array: GBO probably
still works the older way (INFERRED).

## 5. What runs on save

| Object | Procedure | What it does `[read: code, 2026-10-14]` |
|---|---|---|
| Portfolio Property | `PKG_ACCTPRECOMMIT.p_StatusPortFolio` (`001-pkg_acctprecommit_body.sql:101-341`) | Sets `STATUS` / `MESSAGE` (never supplied). **InValid** when: a **global** topic row has no account ("There are some global topics without account", `:124-137`); a **local** topic row has no account (`:147-160`); a condition row has none of `VALUE_FUNC`, `FK_INSTRUMTYPE`, `FK_PORTFOLIO`, `FK_COLLATERALIND`, `FK_COUNTERPARTY`, `FK_DEALTREAT`, `STRUCTIND`, `FK_STRATEGY` (`:170-182`); another portfolio property with the same instrument / group / date has identical condition values (`:186-294`); it has no condition while a **Valid** twin exists (`:296-309`). Otherwise `Valid`. ⚠️ **Internal** topics without an account are **not** checked |
| Account (GLTA) | `PKG_ACCTPRECOMMIT.p_AccountPrecommit` (`:398-451`) | Reads the date rule (`T_BOX_ACCT_PARENT_DATE_S`, owner = account object, extension `amDateDep`, latest `VALDATE` ≤ today). **None → no error**: `VALIDDATE`, `LOC_CODE`, `HOSTINTERFIND`, `PARENT_ACCOUNT` set NULL — a date rule is **optional**. Found → raises if the parent account's balance is not zero (`PKG_ACCT_TRG.F_CHECK_BAL_ACCOUNT_IS_ZERO`), else copies those four columns. Does **not** read `T_BOX_GLTA_LOCAL_S` or `T_PGT_OBJ_SOURCE_S`: **an account is one row** (+ an optional date rule) |
| Topics | `Pkg_AcctPrecommit.p_TopicsPrecommit` | audit columns |
| Conditions | `Pkg_SysPreCommit.p_ExistFuncPreCommit` | — (global; never written by the agent) |
| Acct Indicator / GLTA Type (domain values) | `Pkg_SysPrecommit.p_DomainsPreCommit` | `PGT_DOMAINS` enumerations owned by BOX objects `35000173.65` / `35000174.65` (GBO has its own) — an account's `FK_DIRECTION` / `FK_GLTATYPE` are translated GBO → BOX **by `CODE`** |
| Documents, Grouped Mov Config | `Pkg_AcctPreCommit.p_DocumentPreCommit` | runtime, not configuration |
| Local Properties, Cross Account Config, Instrument Type, Net CCS PlanBS | none | |

## 6. PKs and delivery

**PK rule** `[read: code, 2026-10-14]` (`003-pkg_sigom_cov_body.sql:69-132`, `000-f___sequence.sql:4-52`). SIGOM
creates a row through `PKG_SIGOM_COV.P_SETHEADER(table, PK, owner)`, which fills `PK` with **`F_GetPK`** and
`FK_OWNER_OBJ` with `F_GetOwner` (from the metamodel). `F_GetPK` takes the next number in one of three modes, chosen
per connection (`T__REMCONN_S.USE_SEQ_PROCEDURE` / `USE_SIG_SEQ`): the counter table `BOX_ACC.T___SEQUENCE`
(`PK_NAME` = table, `NEXT_VAL`), or `F___SEQUENCE(table, null, 0|1)` (dynamic `SPK_<table>.NEXTVAL`), then appends
**`'.' || AUTH_CODE`** from `GOM_GLB_SYS.T__CORE_INFO_S` — the `.65` is the **installation's** code, not a constant.
`F___SEQUENCE` exists in almost every schema; the ACC one is self-contained.

**Liquibase** `[read: code, 2026-10-14]`: BOX_ACC is deployed with Liquibase (`BOX_ACC.DATABASECHANGELOG`). Data files:
`src/main/resources/dml/<NN-SCHEMA>/rX.Y.Z/<folder>/NNN-name.sql` (e.g.
`dml/04-BOX_ACC/r0.0.5/05_Static-Data/001-data_t_box_conf_lo_prop_s.sql`), `--liquibase formatted sql`,
`--changeset <schema>:<id>`, `context:` per schema (no per-environment variants), **hard-coded `….65` PKs**,
`--rollback` lines. **No changeset in the repo configures a branch** (portfolio properties, cross account config,
accounts) — branch configuration has so far been entered through the SIGOM screens.

**Consequence for the agent's phase 2:** create rows **the way SIGOM does** — `P_SETHEADER` / `F_GetPK`, then
`f_GenTopicCond`, then fill the lists' `FK_GLTA`, then `p_StatusPortFolio`, in one transaction — rather than
hard-coded PKs. Whether the BOX team wants that as a PL/SQL script or as a Liquibase changeset is open (§10).

## 7. `ACC_TYPE` (Cross Account Config)

`[read: code, 2026-10-14]` (`PKG_BOX_REVAL_ACCOUNTS`, `000-pkg_box_reval_accounts_hdr.sql:28-34, 77-80`,
`007-…_body.sql:186-191`). A plain number compared to literals — the metamodel types it as `TipoReval`
(`35000051.65`) but the code never uses domain PKs:

| `ACC_TYPE` | Meaning | Read by |
|---|---|---|
| `0` | Posición Vencida (matured position) | `p_IsRevalAccount` |
| `1` | Posición Viva (live position) | `C_KeyNetPos`, `C_KeyRevalPos` |
| `2` | Balance de Posición Viva | `C_AcctKey` |

GBO's Cross Account Config has no `ACC_TYPE`: the value per GBO row comes from the reference branch's pattern (A-03b)
or the BOX team. `[2026-10-22]` BOX's source table is GBO's `T_MAD_REVAL_ACCOUNTS` (ADR 0014) — "reval accounts", like
`PKG_BOX_REVAL_ACCOUNTS` — whose **`TIPO`** is probably `ACC_TYPE`: A-03b compares them on the reference.

## 8. Outside the eleven screens (A-11)

| Object | Keyed on | Ruling |
|---|---|---|
| **BOX - Conf Instru Type** `T_BOX_CONF_INSTRUM_TYPE_S` (3 rows) | **branch** (NOT NULL) + instrument, `CODE`, `VALUE`, `TYPE`, `FK_INSTRUMENT_TYPE`, optional counterparty | **screen 12**: the reference's BOX rows per instrument, as they are — never from GBO `[BOX ACC expert, 2026-10-22]` (A-12) |
| **BOX - Net CCS PlanBS** `T_BOX_NETCCS_BSPLAN_S` (66) | **branch** + account (NOT NULL), instrument, instrument type, strategy | **screen 13** — the CCS end-of-month netting configuration (§8.1): asked per run whether it applies; then the reference's rows as they are `[2026-10-26]` |
| BOX - GLTA Local Dep `T_BOX_GLTA_LOCAL_S` (0) | **group** + host / FX-adjust flags per account | GBO has 2 rows: check whether one is NY's group |
| BOX - Conf Acc By StdHist `T_BOX_CONF_ACCSTDHIST_S` (0) | branch | unused |
| Topic Group, Std Historic Group, Std Historic Source | — | global, verify |
| GBO **ConcMis Balances / ConcMis Mov** (`15493.4` / `15494.4`, ~2,450 array rows) | — | GBO accounting ↔ MIS reconciliation; **no BOX_ACC table** — BOX team: replaced, elsewhere, or not needed |

### 8.1 Net CCS PlanBS — the CCS end-of-month netting `[BOX ACC expert via operator, Confluence "CCS Netting and Undo EOM Process", 2026-10-26]`

**What it does.** At month end the netting event **`5210.65`** "BOX Netting CCS Mark to Market ALL" (was `4721.65`)
collects, for every live CCS deal of the branch, instrument type and strategy configured, the balances of the
configured accounts on the netting topics, and closes them into one entry; on the first day of the next month
**`5211.65`** "BOX Undo Netting CCS Mark to Market ALL" (was `4722.65`) reverses both entries.

| Step (netting) | Postings |
|---|---|
| per key / balance, currency ≠ the branch's local one | 2 levelling movements (`NIVELACION`, account `FFM`) + 1 writing off the source topic |
| per key / balance | the source topic's balance moved to its **internal topic** on the `INTERNAL` account (topic translator, below) — 2 movements, with and without the portfolio property |
| after all keys | 1 net movement in local currency on the MtM topic (`FINDEAL…` / `FINREVAL…`) |
| gross | per currency: `TGROSSDEALREVAL` / `TCTRGROSSREVAL` (amount > 0) or `TGROSSDEALDEVAL` / `TCTRGROSSDEVAL` (< 0); amount = (MtM from the Financial module − pending payable premiums) − the gross topic's balance at the latest accounted date |

Standard historics: **CCS - Market value Netting MTM**, **… (gross MTM)**; undo: **CCS - Undo Market value Netting
MTM**, **… (gross MTM)**. Topic translator (account topic → internal topic): `FINDEALREVALMTM` → `TDEALREVALMTM`,
`FINDEALDEVALMTM` → `TDEALDEVALMTM`, `DIFNEARFWD` → `TDIFNEARFWD`, `DIFNEARSPT` → `TDIFNEARSPT`, `DIFFARFWD` →
`TDIFFARFWD`, `DIFFARSPT` → `TDIFFARSPT`, `PENDRESULTNEGLI` → `TPENDPLNEGLIAB`, `PENDRESULTNEGAS` → `TPENDPLNEGASSET`,
`PENDRESULTPOSLI` → `TPENDPLPOSLIAB`, `PENDRESULTPOSAS` → `TPENDPLPOSASSET`, `PREMRECEIVED` → `TPREMRECEIVED`,
`PREMPAYED` → `TPREMPAYED`, `LIACCRUALPAGO` → `TLIACCRUALPAGO`, `ASACCRUALPAGO` → `TASACCRUALPAGO`, `PENDRESULTNEG` →
`TPENDRESULTNEG`, `PENDRESULTPOS` → `TPENDRESULTPOS`, `ASSETACCRUAL` → `TASSETACCRUAL`, `LIABACCRUAL` →
`TLIABACCRUAL`, `ASSETACCRUALNE` → `TASSETACCRUALNE`, `LIABACCRUALPOS` → `TLIABACCRUALPOS`, `FINDEALREVAL` →
`TDEALREVAL`, `FINDEALDEVAL` → `TDEALDEVAL` (the page's list, as far as the screenshots show).

**The configuration** (SIGOM *BOX - Accounting › Config. › Net EOM to CCS*, screen "BOX Net CCS PlanBS"): rows of
branch × instrument (CCS `20.4`) × instrument type × strategy × account. A row with the account **`EOM_CCS_ACTIVE`**
switches the netting on for that combination; the other rows are the accounts whose balances are netted — the
accounts the portfolio properties assign to the translator's account topics (Madrid: `D02`, `D03`, `D04`, `D08`,
`D09`, `PL1`, `PL2`, `PL3`). The page's "criterial" (Market Value: `FINDEALREVALMTM` / `FINDEALDEVALMTM`, or
`FINDEALREVAL` / `FINDEALDEVAL`) — where it is set: open (4zv).

**The load PL** (on the page; a loading help, not a process): inserts the `EOM_CCS_ACTIVE` row per CCS instrument
type whose parameter **`STM`** is not `YES`, strategy `142.4` (Trading), then copies every other account row of the
branch to each of those types. Parameter path `[operator queries, Tier 1, 2026-10-26]`: instrument type
(`PGT_SYS.T_PGT_INSTRUMENT_TYPE_S`, object `1677.4`) → `amParameters` (`118729.4`) → `PGT_STC.T_PGT_PARAMETER_S`
(object `13990.4`, `FK_PARAMETERTYPE`, `PARAMETERVALUE`) → `pParameterType` → `PGT_STC.T_PGT_PARAMETERTYPE_S`
(`13989.4`): **`367.4` = `STM` "Settle to Market"**. In Tier 1 only `11223.4` "CCS SwapAgent-STM" has it `YES` (of
24 CCS types) — settled-to-market trades have no MtM balance to net (inference). The PL hard-codes the PK fraction
`.21`, the owner `35000348.65` and its branch — never reused: phase 2 takes PKs from `F_GetPK`.

**For a new branch** `[operator, 2026-10-26]`: whether the netting applies is **asked every run**; if it does, the
**reference's rows are proposed as they are** (instrument types, strategies, accounts by code) and the operator
changes what the branch needs. Jobs: the netting / undo events run in the month-end and first-day batches — which ACC
jobs run them in the reference (MBJ or `db.conf`, groups): open (4zv), for `box-acc-jobs-agent`.

### 8.2 Label aliases for MIC `[BOX expert via operator, Tier 1 queries, 2026-10-27]`

MBJ's MIC end-of-day jobs (D12 per book, 00D13) send accounting movements to MIC (the GL interface) **by book**:
each BOX book label needs an alias in the GL's coding. Rows of `PGT_TRD.T_PGT_OBJ_SOURCE_S` (SIGOM: the label's
*Systems Alias* tab):

| Column | Value |
|---|---|
| `FK_OWNER_OBJ` | `17910.4` — the label object (`PGT_SYS.PGT_DOMAINS` rows with this owner) |
| `FK_PARENT` | the label's PK (the `FK_LABEL` of its MBJ rows) |
| `FK_EXTENSION` | `118615.4` — the label's alias list |
| `ALIASCODE` | the GL's code for the book — **given by the GL team** (Equation), never derived: SLB's are single letters A–O, G not used |
| `FK_SOURCE` | the GL source, `PGT_SYS.T_PGT_SOURCE_S` (object `1341.4`): SLB `287.4` EQUATION MADRID |

Tier 1: 14 label aliases, all SLB's books (XLB01–XLB12, XLB14, XLB15), all source `287.4` — no other branch has
any. Unique keys as for every alias (`UN_PGT_OBJ_SOURCE_S_001` one alias per label and source, `_002` one label per
code and source). The Equation sources include `629.4` EQUATION_NY (2023 family `EQUA_*`), `145.4` N.Y. EQUATION,
`287.4` EQUATION MADRID: which one a branch's labels use is confirmed with the GL team. Not needed for the FE
configuration or FE jobs.

**NY-specific GBO tables** (`PGT_NY`): `T_PGT_NY_ACCT_REVAL_S` / `_HIST_S` hold revaluation **results** (balances,
revaluation amount per property and currency) — not configuration; **`T_PGT_TOPICS_RR`** (84 rows) **is**
configuration (topic per instrument × buy/sell `COMPRAVENTA` × near/far) with no BOX screen — BOX team;
`T_PGT_USAENTPROP_S` (and `PGT_STC`'s) is US entity static data (tax and regulatory IDs) — **never extracted**, out
of the ACC agent's scope. The `PGT_NY.T_MAD_*` tables were read as empty Madrid copies — **except
`PGT_NY.T_MAD_REVAL_ACCOUNTS`**, NY's Cross Account Config source per the BOX ACC expert (2026-10-22; its rows: A-03a).

GBO's accounting engine also has its **own** event groups and events (`PGT_SYS.T_ACCT_BR_EVE` / `_EXT` /
`T_ACCT_EVE`, with conditions and expressions in `T_ACCT_COND` / `T_ACCT_EXP`), separate from the shared
`PGT_PRC` groups BOX uses — screen 8 is compared against the reference branch, not against GBO.

## 9. GBO accounting as a branch uses it — NY SCH `[operator queries, PRE PARALELO, 2026-10-15]`

Read with the usage queries A-G4, A-U0–A-U7 ([catalogue](queries/acc-config-mining.md)) in **PRE PARALELO** (GBO
data to 24-09-2026), NY SCH `20007.4`, group `21447.4`, NY's six approved instruments. Counts only — no portfolio,
counterparty or entity value was extracted. What is NY-specific is marked; the mechanisms are GBO's and apply to any
branch.

### 9.1 Where to read what a branch uses

| Environment | Use |
|---|---|
| GBO production | the reference for "what is used" — **no access** for the operator `[2026-10-15]` |
| **PRE PARALELO** | a recent copy of production `[operator, 2026-10-15]` — **the GBO source** (`Env: GBO-PREPAR`) |
| Tier 2 PRE | older: NY's Cross Account Config 17 rows (PRE PARALELO 24); portfolio-property list rows without an account (depos 115, OTC 16) that PRE PARALELO does not have |

The branch and group keys are the same in both (A-G1). A-U5 compares the two.

### 9.2 Everything is keyed on the branch group — a group can hold many branches

- NY SCH's group `21447.4` (UNITED STATES) holds **25 branches** (NY SCH, NY IBF, NY SIL, NY SIS, NY SCH PH,
  PARALLEL NY SCH, funds…). GBO keys **all** of it on the group: 18 local properties (one per instrument), 123
  portfolio properties; **none** on the branch.
- BOX keys the same way (§1). **What one branch creates serves its whole group**; the first branch of a group in BOX
  creates everything (NY SCH: A-G4 = 0 rows in Tier 2 PRE BOX `[2026-10-15]`), a later one adds only its own rows.
- **Movements are per branch** (`FK_BRANCH` = the branch), configuration per group: "configured but not used by the
  branch" is mostly **other branches' configuration**, not dead rows.
- Every NY local and portfolio property starts on `01-JAN-00` (the start date `INIVALPCDATE`).

### 9.3 How a trade finds its portfolio property — conditions, incl. the branch

Each portfolio property has a condition list (`38335.4`). NY's are **NY functions** (`VALUE_FUNC` holds the value
the function must return) plus two domains (Strategy `122.4`, Instrument Type `102.4`). **No condition is valued on a
portfolio or a counterparty** (A-U1 b).

| Instrument | Conditions (`FK_CONDITION` → function) |
|---|---|
| Depos `2.4` | `27.35` `f_AcctCustType`, `28.35` `f_InstrumentType`, **`29.35` `f_TradeBranchDL`**, Strategy |
| CCS `20.4` | `30.35` `f_TradeEntityCCS` (returns the counterparty — never extract its values), `31.22` `PGT_BOS…f_TradeEurFX` (another schema), **`33.35` `f_TradeBranchCCS`**, `36.35` `f_GetFolder`, Strategy |
| IRS `20092.4` | **`35.35` `f_TradeBranchSwap`**, `36.35` `f_GetFolder`, `38.35` `f_TradeQuoteReference`, `45.35` `f_GetIRSCCY`, Strategy |
| OTC `20111.4` | `1.35` `f_GetOTCClass`, `21.35` `Pkg_OTCMadAuxiliar.f_IsDeliveryOTC`, `23.35` `f_GetOTCUndClass`, **`24.35` `f_TradeBranch`**, `36.35` `f_GetFolder`, `533.35` `f_GetDirectionOTC`, Instrument Type, Strategy |
| CAP `20213.4` | **`24.35` `f_TradeBranch`**, `25.35` `F_GETDIRECTIONCF`, `36.35` `f_GetFolder` |
| CDS `20313.4` | `22.35` `F_GETDIRECTION`, Instrument Type, Strategy — **no branch condition** |

(Functions in `PGT_NY.PKG_NY_ACCOUNTING_CONDITIONS` unless named.) **The branch condition is what separates the
group's branches**: its `VALUE_FUNC` is the branch code — NY SCH `NY_SCH`; NY IBF `NY_IBF` (6 depos properties);
`INTERNAL` (1 IRS property, no movement or key in July). A-U1 (e) / (f) list them per property. A property with no
branch condition (CDS) serves the whole group.

### 9.4 How a topic finds its account

| Route | What it is | Seen in NY |
|---|---|---|
| **Portfolio-property lists** | topic → account rows per list: global `38249.4`, local `38329.4`, **internal `38422.4` → a technical account `INTERNAL` / `INTERNAL1`** (1–3 accounts per instrument) | the main route; a topic can have several rows (accounts) in one property **[2026-10-28: BOX holds one (Tier 1: none) — the operator decides, ADR 0020 point 6; NY: 14 OTC cases, `INTERNAL` + one real account each]**. In BOX the internal list takes the **internal account** too, as SLB / Madrid do — never empty `[BOX ACC expert, 2026-10-22]` |
| **Cross Account Config** (GBO's own, `T_PGT_CROSS_ACCTCONF_S` — not BOX's source, ADR 0014) | branch-keyed rows, account by **currency** (and entity / instrument when set) | NY SCH is the **only GBO branch** with rows: 24, no instrument; `EXTERNALSETTACC` → `817904-<ISO currency number>` (036, 124, 484, 578, 604, 752, 756, 826, 840, 978) — A-U6: every real account found outside the lists comes this way |
| Property `0` (`FK_PROPERTIES = 0`) | technical / internal legs not tied to a property | mostly to `INTERNAL`; two small exceptions with a real account and no Cross Account Config: `GENTRANSITCASH` → `916103-299919`, CAP `FXNETLOSS` → `9970241-939607` — route unknown |
| **Topic `0`** (`FK_TOPIC = 0`) | movements with **no topic**, account only | ~2,600 / month on NY's instruments (A-U2b), accounts `09xxxx.xxx` (`097487.001` most); also keys with no topic on real properties — **not** Cross Account Config, **route unknown** |

Account families seen: `9xxxxxx-xxxxxx` (P&L, revaluation, positions), `817904-xxx` (settlement per currency),
`916103-xxxxxx` (transitory cash), `9xxxxx-Xn` (nominal / counterparty positions), `TCPA` / `TCPV` (netting control),
`INTERNAL` / `INTERNAL1` (technical), `09xxxx.xxx` (no-topic postings), and four `T9…` accounts on two CCS properties
(production accounts or test copies — open).

Properties and topics carry two PK installations: `.35` (older) and `.44` (newer, e.g. `133229.44`).

### 9.5 NY SCH in numbers (PRE PARALELO, NY's six instruments)

| Instrument | Properties (NY_SCH / other) | List rows global / local / internal |
|---|---|---|
| Depos | 21 / 6 NY_IBF | 2,835 / 270 / 918 (all 27) |
| OTC | 24 / — | 1,608 / 216 / 552 |
| CCS | 6 / — | 1,182 / 48 / 396 |
| IRS | 3 / 1 INTERNAL | 368 / 40 / 184 |
| CAP | 4 / — | 260 / 32 / 104 |
| CDS | 6 (no branch condition) | 514 / 54 / 156 |

In scope for NY SCH: **58** NY_SCH properties, + IRS `INTERNAL` (to decide), + 6 CDS (if CDS is in BOX scope); their
lists: 622 topic × list rows (A-U7a). July 2026 usage: 199 distinct topics (52 always to `INTERNAL`, 4 CDS-only),
254 real accounts. All approved instruments are configured **and** post (CDS too); FRA is configured (1 property) but
not approved; FX, fixed income, ETD, index futures and repo are configured and out of BOX scope.

### 9.6 Reading rules learnt

1. **Scope by the branch condition, not by usage**: a property belongs to the branch when its branch condition is the
   branch's code (or it has none and the instrument is in scope).
2. **Copy full lists, never lists trimmed to a usage window**: keys show topics used outside one month (cancellations,
   year-end `RDOSEJERCICIO`, cash FX, memorandum `…CTASORDEN` / `…NOTIONAL`).
3. **A-U3's amounts are not balances**: transitory topics show tens of thousands of "open" keys — read A-U3 as "topic
   used on this property, last on `MAXDATE`".
4. **Topic and account lists for BOX come from the in-scope lists** (A-U7a / A-U7b), the usage only confirms them.
5. A `0` in `FK_PROPERTIES` or `FK_TOPIC` means "none" — never join it as a key.

### 9.7 From GBO NY to BOX — what is known and what is not

| | Known | Not yet known (Tier 1 BOX, SLB) |
|---|---|---|
| Structure | same tables, the four BOX arrays, `f_GenTopicCond`, save checks, keys, PKs (§1–6) | — |
| Topics | NY's in-scope topic codes (A-U7a) | whether BOX's topic codes **are** GBO's (then the "mapping" is a code match) |
| Events | BOX's event groups are shared `PGT_PRC` objects, global or copied per branch (§8) | how BOX turns an event into topics for SLB, vs GBO's own engine |
| Conditions | NY's functions and the branch condition (9.3) | which BOX conditions SLB uses; whether a BOX branch condition exists |
| Local properties | GBO: one topic array per instrument | how SLB fills BOX's four arrays per instrument (screen 2's template) |
| Cross Account Config | NY: 24 settlement rows by currency in GBO's `T_PGT_CROSS_ACCTCONF_S` — **not BOX's source** (ADR 0014) | NY's rows in `PGT_NY.T_MAD_REVAL_ACCOUNTS` (A-03a); SLB's GBO rows vs its BOX ones (Tier 1 BOX: 2,578) — `TIPO` = `ACC_TYPE`? (A-03b) |
| Accounts | NY's real accounts in scope (A-U7b) | which exist in BOX (Tier 2 PRE BOX: 1,580 accounts) |

Six Tier 1 / Tier 2 BOX queries close the right column; until then the translation rules are **proposed**, not
applied.

`[2026-10-28]` **Decided** ([ADR 0020](../decisions/0020-portfolio-properties-imported-from-gbo.md), BOX expert): one
BOX portfolio property per `Valid` in-scope GBO property (its description, its own accounts); its GBO conditions that
have a BOX twin (paired, the value translated — e.g. GBO "OTC Option underlying class" `SW` ≈ BOX "Check the type of
OTC Option" `Swaption`), the others dropped (Instrument Type, the branch function, Folder when BOX has no twin); the
local properties from the same GBO properties (every NY property of an instrument has the same topic list, §9.5);
properties that become identical in BOX (clash) are held for the user's choice or created `InValid` (asked per run).

## 10. Open

| Question | Who |
|---|---|
| Which tier "PRE-PROD" is (where D1–M3 ran); BOX_ACC read access in Tier 2 PRE and DGBOUS | operator |
| Package versions deployed per environment (`PKG_ACCTPROP` r0.0.8?) — B5 | operator |
| Delivery of a branch's ACC config: SIGOM routines in a PL/SQL script, or a Liquibase changeset (PKs fixed per environment) | BOX team |
| ~~Internal topics without an account~~ — the internal account (BOX ACC expert, 2026-10-22) | — |
| `ACC_TYPE` from `T_MAD_REVAL_ACCOUNTS.TIPO`? Its full column map to BOX (A-P7, A-03b) | A-03b / BOX team |
| The BOX route of GBO's own `T_PGT_CROSS_ACCTCONF_S` rows (NY: 24 settlement accounts by currency) | BOX team |
| `T_PGT_TOPICS_RR`, ConcMis, Net CCS PlanBS for NY (~~Conf Instru Type~~: the reference's, 2026-10-22) | BOX team |
| The portfolio properties' start date (local properties: 01/01/1900, fixed) | BOX ACC expert |
| `SPK_T_BOX_CONF_LO_PROP_S` not in the repo — present in DGBOUS? | operator (pre-check A-P5) |
| ~~GBO → BOX topic mapping~~ — **by `CODE`**; a GBO topic with no BOX twin is created as a global topic (`.65`, to review) `[BOX ACC expert, 2026-10-27 — ADR 0018]` | closed |
| A BOX condition that returns the trade's branch (GBO NY: `f_TradeBranch…`, values `NY_SCH` / `NY_IBF` / `INTERNAL`) | BOX dev |
| Postings with no topic (`FK_TOPIC = 0`, accounts `09xxxx.xxx`) — what produces them, and in BOX | GBO accounting expert / BOX dev |
| `GENTRANSITCASH` / `FXNETLOSS` real accounts with no property and no Cross Account Config | BOX dev |
| The four `T9…` accounts (CCS `133234.44` / `133235.44`): production or test | BOX / GBO team |
| CDS in BOX scope for NY (configured and posting in GBO; FE jobs plan `skip`) | operator |
| IRS `INTERNAL` property: copy or not | operator |
