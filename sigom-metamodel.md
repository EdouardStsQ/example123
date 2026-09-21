# The SIGOM metamodel — ask the system, don't infer it

**One page, one claim:** SIGOM describes itself. Which tables exist, which screen owns them, what every
field points at, and what runs on save are all **declared** in `GOM_GLB_SYS`. Most of this repo's join
defects came from inferring facts the system states outright.

`[confirmed: DB via Edouard, 2026-09-18]` unless marked otherwise.

## Why this page exists

Five query defects in four days. Every one was a relationship the database declares:

| Defect | What we inferred | What is declared |
|---|---|---|
| Q-05c joined `FK_INSTRUMENT` to Processed Instruments | a guess | `AccrualConfig.pInstrument → T_PGT_SUB_PRODUCT_S` |
| Q-04 filtered an `_X` bridge on `FK_BS` | a pattern | `apQuoteReference`, kind `4.1` — a link array |
| Q-07 mined without a parent filter | an omission | `amFixing_by_instrument`, kind `3.1` — an owned collection |
| The draft copied GBO's `FK_OWNER_OBJ` | "it's a module id" | the screen the row is edited through |
| Gate 0f blocked on a source-object PK | a misreading | — |

This page is the antidote. **Before asserting any relationship in BOX FE or GBO, query the metamodel.**

---

## 1. Where it lives

`GOM_GLB_SYS` — 96 tables. Two of them carry almost everything this project needs:

| Table | Holds |
|---|---|
| **`T__OBJ_DEF_S`** | One row per SIGOM **object** — a screen or entity. Names its physical storage |
| **`T__EXT_DEF_S`** | One row per **field/extension** of an object. Names what each field points at |

Also confirmed present and already used elsewhere: `T__CORE_INFO_S` (the auth code behind
`F___SEQUENCE`) and `T___SEQUENCE` — three underscores, matching the function's name.

`T__OBJ_DEF_S` is self-describing: `PK = 1.1` is the object `_OBJ_DEF`, whose `BASIC_STORAGE` is
`T__OBJ_DEF_S`. A bootstrapping metamodel, so it is authoritative rather than documentation that drifted.

## 2. The object model

An object owns **several physical tables**, named in its own columns:

| Column | Meaning |
|---|---|
| `PK_NAME` | the object's name — `BOX_ENG_Config`, `BOX - Limit Error Assign` |
| `BASIC_STORAGE` | the main table |
| `EXT_STORAGE` | the `_X` bridge, where one exists |
| `LANG_STORAGE`, `FILE_STORAGE` | translations, file attachments |
| `FK_PARENT` | the owning **module** — *not* a row in this table, see §7 |
| `FK_CONNECTION` | the connection/schema — *not* a row in this table, see §7 |
| `PRE_COMMIT_PROC`, `FK_PRECOMMIT`, `PSAVDLL`, `PSAVFUNC` | code that runs on save — see §5 |

### The BOX modules

`[confirmed: DB, 2026-09-21]` 130 modules exist; **twelve contain BOX storage**. The seven that matter:

| Module | Objects | What it is | Inferred from |
|---|---|---|---|
| **`35000005.65`** | 80 | **BOX FE** — 15 walk tables + one view; the rest runtime and domain | membership |
| **`35000006.65`** | 31 | **BOX ACC configuration** — the ACC agent's scope | membership |
| `35000007.65` | 16 | Settlement | membership |
| `30000000.65` | 31 | Deal / transaction data | membership |
| `30000003.65` | 19 | Platform infrastructure | membership |
| `774.66` / `795.66` | 24 / 2 | Account & SSI standing data; product masters | membership |
| `35000009.65` | 4 | **AUKI migration** — `T_BOX_AUKI_CRITERIA_S`, `T_BOX_AUKI_MIG_CRITERIA_S` | membership |

⚠️ **Module names are inferred from their children, never read.** `FK_PARENT` does not resolve in this
table (§7), so no document should print "`35000006.65` = BOX ACC" as a confirmed fact.

**One table can serve many objects, and this is pervasive.** `T_BOX_ENGDOM_S` stores eight
enumerations; `T_BOX_DATADEAL_S` eleven product objects; `T_BOX_SETT_FLOW_S` four; `T_BOX_ACCT_SELECTOR_S`
three; `PGT_DOMAINS` dozens. What separates their rows is `FK_OWNER_OBJ`. It also explains why
`F___SEQUENCE` special-cases `T_BOX_ENGDOM_S` onto `SQ_BOX_FINANENG3`.

> ## The `PGT_DOMAINS` rule, which follows directly
>
> `PGT_SYS.PGT_DOMAINS` is one physical table holding many unrelated enumerations — Label Config
> (`17910.4`), SubLabel Config, Strategy, Trade Direction, Criteria Treatment, Cash Flow Status, and
> three **BOX ACC** ones (Acct Indicator, GLTA Type, Param Fixed) that store into the shared PGT table.
>
> **Joining `PGT_DOMAINS` by PK is safe. Enumerating it without `FK_OWNER_OBJ` is not.** A query that
> lists domain values without the discriminator reads across every enumeration in the system, and the
> result looks entirely plausible.
>
> Note the consequence for ACC: **BOX ACC's own enumerations live in a shared PGT schema**, so they are
> global and identical in every environment — not branch-scoped and not environment-specific.

## 3. `FK_OWNER_OBJ` and `FK_EXTENSION` — the rule

> **`FK_OWNER_OBJ` is the object whose *screen* the row is edited through. `FK_EXTENSION` is which
> field/tab within it.** Together they say "which screen, which tab".

They are **properties of the destination**, never mined from GBO — charter hard rule 9. The BOX
Financial Engine module is `35000005.65`; `35000126.65` is the *Config screen*, which is a different
thing.

**Derivation, with no `BOX_FE` read required:**

- **Base table** (an object's `BASIC_STORAGE`): `FK_OWNER_OBJ` = the object's PK, `FK_EXTENSION` = NULL.
- **Extension table**: `FK_OWNER_OBJ` = the extension's `FK_PARENT`, `FK_EXTENSION` = the extension's PK.

Validated four for four against live Tier 1 rows:

| Table | Observed | Derived |
|---|---|---|
| `T_BOX_ENGFCURVE_S` | `35000123.65` / null | base storage of FixingCurve ✅ |
| `T_BOX_ENGLKFC_X` | `35000123.65` / `35001101.65` | ext `…1101`, parent `…123` ✅ |
| `T_BOX_ENGCONF_X` | `35000126.65` / `35001566.65` | ext `…1566`, parent `…126` ✅ |
| `T_BOX_ENGACCRCONF_S` | `35000126.65` / `35001114.65` | ext `…1114`, parent `…126` ✅ |

**The Accrual case is the one that proves the rule rather than a simpler one.** `T_BOX_ENGACCRCONF_S`
is registered as the `BASIC_STORAGE` of `BOX_ENG_AccrualConfig` (`35000128.65`), yet its rows carry
`35000126.65`. Both are true: the Accrual tab is a *composition extension of the Config screen*, so the
rows belong to Config while the table has its own object definition for the detail rows. **You cannot
derive `FK_OWNER_OBJ` from `BASIC_STORAGE` alone** — `T__EXT_DEF_S` is the reconciling link.

## 4. The field type system — `T__EXT_DEF_S`

| Column | Meaning |
|---|---|
| `FK_PARENT` | the object this field belongs to |
| `FIELD` | the field's name, prefixed by kind |
| `FK_KIND` | what kind of field |
| `FK_OBJECT` | **the object it points at** — this is the declared FK target |

| `FK_KIND` | Prefix | Meaning | Physical storage |
|---|---|---|---|
| `2.1` | `p…` / bare | scalar pointer to another object | an `FK_*` column on the base table |
| `3.1` | `am…` | **owned collection** | the child object's own `_S` table, linked by `FK_PARENT` |
| `4.1` | `ap…` | **link array** to an independent object | an `_X` bridge — `FK_PARENT` up, `FK_BS` across |
| `5.1` | — | scalar literal | a plain column, no target |
| `6.1` | `u…` | flag, no target | nothing to mine |
| `11.1` | `sql…` | **screen filter parameter** — `sqlDateFrom`, `sqlManualOnly`, `sqlDealId` | **not a stored column at all** |

⚠️ **`11.1` is a trap for a generator.** These are search criteria on the screen, not columns of the
row. An agent that treats the declared field list as an INSERT column list will emit garbage unless it
excludes `11.1` (and `6.1`). Only `2.1` and `5.1` map to columns you write; `3.1` and `4.1` map to
child rows.

**This is the `_X` convention, declared.** A `4.1` link array gets a bridge table because the target
exists independently; a `3.1` owned collection does not, because its rows belong to the parent. That is
why `FK_PARENT` is the filter on both shapes and `FK_BS` only exists on the `4.1` ones.

### ⚠️ A bridge table is not one relationship — `T_BOX_LINK_ARRAY_X` is seventeen

`[confirmed: DB, 2026-09-21]` FE gives each object its own bridge (`T_BOX_ENGCONF_X`,
`T_BOX_ENGLKFC_X`). **ACC does the opposite**: one generic bridge serves nine objects and **17 distinct
relationships**, separated only by `(FK_OWNER_OBJ, FK_EXTENSION)`.

| Owning object | Link arrays | `FK_BS` targets |
|---|---|---|
| `BOX - Config LOC Property` | `apLocalTopicArray`, `apGlobalTopicArray`, `apInternalTopicArray`, `apCondArray` | `T_BOX_ACCT_TOPICS_S` ×3, `T_BOX_CONDPAR_PROP_S` |
| `BOX - Migration Criteria` | `apCounterparty`, `apPortfolio`, `apInstrumentType` | `T_PGT_ENTITY_S`, `T_PGT_FOLDER_S`, `T_PGT_INSTRUMENT_TYPE_S` |
| `BOX - Auki Criteria` | `apCounterparty`, `apPortfolio`, `apInstrumentType` | same three |
| `BOX - Filter NetPreconf` | `apFolder`, `apSettActions` | `T_PGT_FOLDER_S`, `T_BOX_SETT_FLOW_S` |
| `BOX - GLTA` | `apRefAcc` | `T_BOX_REFERENCEACC_S` |
| `BOX - Std Historic Group` | `apStandardGroup` | `T_BOX_ACCT_HISTSTD` |
| `BOX - Topic Group` | `apTopicGroup` | `T_BOX_ACCT_TOPICS_S` |
| `BOX - Filter PreConf` | `apCounterparty` | `T_PGT_ENTITY_S` |
| `BOX - External State` | `apBranch` | `T_PGT_BRANCH_S` |

**`FK_BS` in that one table points at nine different tables.** Worse, `Config LOC Property`'s first
three arrays all target the *same* table — so knowing the owner *and* the target still doesn't
disambiguate them. Only `FK_EXTENSION` does.

**Never query an `_X` table on `FK_PARENT` alone.** For a shared bridge the filter is
`(FK_OWNER_OBJ, FK_EXTENSION, FK_PARENT)`; anything less returns rows from unrelated arrays that look
entirely reasonable. `T_BOX_MOV_LINK_ARRAY_X` is a second generic bridge and should be assumed to
behave the same way until checked.

`[open-question]` `BOX - Conf Instru Type` declares `T_BOX_LINK_ARRAY_X` as its `EXT_STORAGE` but
declares **no `4.1` field** — an unused extension slot, or something the catalogue does not show.

## 5. Code that runs on save — read this before trusting any INSERT

`T__OBJ_DEF_S` declares `PRE_COMMIT_PROC` / `FK_PRECOMMIT` (and `PSAVDLL` / `PSAVFUNC`).

> **857 objects across SIGOM declare one, in 172 packages** `[confirmed: DB, 2026-09-21]`. **This is how
> SIGOM works, not a quirk of one module.** The rule is therefore: **assume an object runs code on save
> until you have checked that it does not.**

**FE: 16 objects. ACC: 10.** Between them, only **three packages** — which makes reading the source a
tractable job rather than an open-ended one:

| Object | Covers | Procedure |
|---|---|---|
| `BOX_ENG_Config` | FE steps **2, 5, 6** — and probably **7, 8, 9, 10, 11** (see below) | `PKG_ENGPRECOMMIT.p_check_Val_Curves_precommit` |
| `BOX_ENG_FixingCurve` | FE steps 3, 4 | `pkg_engPrecommit.P_ENGFixingCurve_PreCommit` |
| `BOX_ENG_Fixing_Assignment` | FE step 13 (derived, no INSERT) | `p_check_Val_Curves_precommit` |
| `BOX_ENG_Setup` | FE step 14 (not branch-scoped) | `P_FE_Parameters_PreCommit` |
| **`BOX - Acct Port Property`** | **ACC — portfolio properties** | `PKG_ACCTPRECOMMIT.p_StatusPortFolio` |
| **`BOX - Acct Topics`** | **ACC — topic catalogue** | `Pkg_AcctPrecommit.p_TopicsPrecommit` |
| **`BOX - GLTA`** | **ACC — GL accounts** | `PKG_ACCTPRECOMMIT.p_AccountPrecommit` |
| `BOX - Documents`, `BOX - Grouped Movements` | ACC | `Pkg_AcctPreCommit.p_DocumentPreCommit` |
| `BOX - Cond PortFolio` | ACC | `Pkg_SysPreCommit.p_ExistFuncPreCommit` |
| `BOX - Acct Indicator`, `GLTA Type`, `Param Fixed` | ACC enumerations in `PGT_DOMAINS` | `Pkg_SysPrecommit.p_DomainsPreCommit` |

**Nine procedures, three packages — `PKG_ENGPRECOMMIT`, `PKG_ACCTPRECOMMIT`, `PKG_SYSPRECOMMIT`** —
cover everything both agents will ever write. Note that the three most consequential ACC objects
(portfolio properties, topics, **GL accounts**) all declare one.

**Which FE steps are affected is wider than it first looks.** `p_check_Val_Curves_precommit` fires on
the `BOX_ENG_Config` *screen*, and every `am…`/`ap…` collection of Config is edited through that screen.
Confirmed for step 6 (`T_BOX_ENGACCRCONF_S` rows carry `35000126.65`); **inferred for steps 7–11** from
their declared ownership. One measurement settles it: Q-G6 across all walk tables, grouped by
`FK_OWNER_OBJ`.

⚠️ **Check both columns.** `BOX Management Status FE` and `BOX - Grouped Mov Config` have a **null**
`PRE_COMMIT_PROC` but a populated `FK_PRECOMMIT`; `BOX - Grouped Movements` has the reverse. And
`FK_PRECOMMIT` values are reused across objects (`35002256.65` appears on two), so it points at a
shared registry. Filtering on the procedure name alone under-reports.

`[open-question]` **Roughly forty of the 172 packages carry a `PKG_MAD_` prefix** — `PKG_MAD_GN_MIFID`,
`PKG_MAD_BUROFAX`, `PKG_MAD_SIU_PRECOMMIT`, `PKG_MAD_PRE_IPF_FILE`, and so on. Most read as Spain/EU
regulatory functions that would not apply to New York. **But does onboarding a branch in a new
jurisdiction require its own pre-commit packages?** If yes, that is an unscoped development workstream.
Put it to the BOX FE developer alongside the validate-or-write question. Two more worth a look:
`PKG_BRANCHCONFIG` and `PKG_PROCESSBRANCHGROUP`, one object each.

**So a raw INSERT is not the whole operation for the spine of the walk.** The package spec —
`PKG_ENGPRECOMMIT`, owner `BOX_FE`, six procedures, each `(pk IN NUMBER)`, `AUTHID DEFINER` — says each
takes the PK of a row that already exists and can only signal a problem by raising. That is the shape of
a validation gate, but it does not rule out DML. **Read the body before executing anything.**

`ALL_SOURCE` and `ALL_OBJECTS` show the spec only — `EXECUTE` privilege never reveals a package body. The
body is committed in **`cib-boxfin-dbboxfe`** `[stated: Devin via Edouard, 2026-09-18]`, which needs no
database access at all.

Two things follow, and both are charter rules now (hard rule 10):

1. **The script calls the procedure** after each affected INSERT, using the PK variable it already holds.
   If it validates, the script reproduces SIGOM's check; if it writes, the script reproduces the write.
2. **Procedure step F3 finally has a method.** In a reference environment, inside one transaction:
   snapshot → INSERT → call the procedure → re-snapshot → `ROLLBACK`. Any change beyond your own row
   means the walk is incomplete by exactly that much.

⚠️ `PRE_COMMIT_PROC` is not uniformly reliable as a string — the Data Deal objects name
`P_ES_Data_MIS_PreCommit`, which is **not in the package spec**. All four walk-relevant names match
exactly. Verify against the spec, not the column.

## 6. The declared field catalogue for the walk

The complete output of Q-G7 for the walk objects, distilled. **This supersedes every inferred FK in
this repo.**

### The three screens

The walk spans three, not one: **`BOX_ENG_Config`** (`35000126.65`), **`BOX_ENG_FixingCurve`**
(`35000123.65`) and the standalone **`BOX - Limit Error Assign`** (`35000289.65`).

`BOX_ENG_Config`'s fourteen fields map one-to-one onto the walk:

| Field | Kind | Target | Walk step |
|---|---|---|---|
| `pLocalCurrency`, `pCalendar`, `Description`, `FixingCurveMan`, `FixingCurveAcc`, `SourceFront`, `SourceBack` | 2.1 / 5.1 | Currency, Calendar, —, FixingCurve ×2, Sources ×2 | **2** — and these seven *are* the mining list |
| `apBranch` | 4.1 | `T_PGT_BRANCH_S` | **5** |
| `amAccrualConfig` | 3.1 | `T_BOX_ENGACCRCONF_S` | **6** |
| `amConfig_Accrual` | 3.1 | `T_BOX_CONFIG_ACCRUAL_S` | **7** |
| `amFixing_by_instrument` | 3.1 | `T_BOX_FIXING_BY_INSTR_S` | **8** |
| `amZeroCoupon` | 3.1 | `T_BOX_ENGZCCONF_S` | **9** |
| `amCurrencyBasis` | 3.1 | `T_BOX_ENGCURRENCYBASIS_S` | **10** |
| `amConfigByBook` | 3.1 | `T_BOX_CONF_BY_BOOK_S` | **11** |

`BOX_ENG_FixingCurve`: `Name` (5.1), `pLocalCurrency` (2.1), `apQuoteReference` (4.1 → step **4**), and
**`apYieldCurve`** (3.1 → `T_BOX_ENGFIXDISC_S`) — see §8.

**Step 2's exclusion list is no longer a judgement call.** Config declares seven fields with values;
`FK_OWNER_OBJ`, `FK_EXTENSION` and `FK_PARENT` are not fields of the object at all.

### `FK_INSTRUMENT` — six targets one way, two the other

| Object | Field | → |
|---|---|---|
| `BOX_ENG_AccrualConfig` (6) | `pInstrument` | `PGT_SYS.T_PGT_SUB_PRODUCT_S` |
| `BOX_ENG_Config_Accrual` (7) | `pInstrument` | `PGT_SYS.T_PGT_SUB_PRODUCT_S` |
| `BOX_ENG_ZeroCouponConfig` (9) | `pInstrument` | `PGT_SYS.T_PGT_SUB_PRODUCT_S` |
| `BOX - MIS Config by Book` (11) | `pInstrument` | `PGT_SYS.T_PGT_SUB_PRODUCT_S` |
| `BOX - Limit Error Assign` (12) | `pInstrument` | `PGT_SYS.T_PGT_SUB_PRODUCT_S` |
| `BOX_ENG_Days_Matured` (14) | `Instrument` | `PGT_SYS.T_PGT_SUB_PRODUCT_S` |
| **`BOX_ENG_Fixing_By_Instrum` (8)** | `pInstrument` | **`V_BOX_PROC_INSTR_S`** |
| **`BOX_ENG_Fixing_Assignment` (13)** | `Instrument` | **`V_BOX_PROC_INSTR_S`** |

Sub-Product everywhere except the two **fixing** tables. That is the whole map, and it is why Q-05c was
wrong and why Q-07 legitimately differs from its neighbours.

### The branch field — geographic, everywhere

| Object | Field | → |
|---|---|---|
| `BOX_ENG_Config` (5) | `apBranch` | `PGT_STC.T_PGT_BRANCH_S` |
| `BOX_ENG_Config_Accrual` (7) | `pBranch` | `PGT_STC.T_PGT_BRANCH_S` |
| `BOX - Limit Error Assign` (12) | `pBranch` | `PGT_STC.T_PGT_BRANCH_S` |
| `BOX - MIS Config by Book` (11) | `pBranch` | `PGT_STC.T_PGT_BRANCH_S` |

✅ **This closes the product-shaped-branch question**, open since the BOX-DEV screenshots showed
`BOX CCS` / `BOX FX` / `BOX IRS` in the Accrual Exceptions and Allowed Errors branch columns, and written
into the kickoff as a *stop the run* condition. All four declare the geographic branch master. Those
values are **rows inside `T_PGT_BRANCH_S`** — which this repo already records as overloaded, ~137 rows
including entities, SPVs, counterparties and test records. A dev environment with junk in the branch
master, not a different data model. The walk's grain is correct.

### Remaining fields, per object

| Object | Fields (kind → target) |
|---|---|
| `BOX_ENG_AccrualConfig` (6) | `pInstrument` → Sub-Product · `FeeCalcInterval`, `InterestCalcInterval` → `T_BOX_ENGDOM_S` · `InCommonBasis` (5.1) · six `u…` flags (6.1) |
| `BOX_ENG_Config_Accrual` (7) | `pBranch` · `pInstrType` → `T_PGT_INSTRUMENT_TYPE_*` · `pInstrument` → Sub-Product · `pStrategy` → `PGT_DOMAINS` · `Criterial`, `Parent` (5.1) |
| `BOX_ENG_Fixing_By_Instrum` (8) | `pInstrument` → `V_BOX_PROC_INSTR_S` · `pFixingACC`, `pFixingMAN` → `T_BOX_ENGFCURVE_S` |
| `BOX_ENG_ZeroCouponConfig` (9) | `pInstrument` → Sub-Product · `pCurrency` · `pYieldCurve` → **`T_PGT_YIELDCURVE_*`** |
| `BOX_ENG_Currency_Basis` (10) | `pMatType` → `T_BOX_ENGDOM_S` · `pCurrency` · `pBasis` → **`T_PGT_BASIS_S`** |
| `BOX - MIS Config by Book` (11) | `pBranch` · `pInstrument` → Sub-Product · `pLabel` → `PGT_DOMAINS` |
| `BOX - Limit Error Assign` (12) | `LimitError` (5.1) · `pBranch` · `pInstrument` → Sub-Product |
| `BOX_ENG_Fixing_Assignment` (13) | `pFixingACC`, `pFixingMAN` → `T_BOX_ENGFCURVE_S` · `Instrument` → `V_BOX_PROC_INSTR_S` |
| `BOX_ENG_Setup` (14) | `ParameterName`, `DateData`, `NumberData`, `StringData` — all 5.1. **No branch field** |
| `BOX_ENG_Days_Matured` (14) | `Days`, `DateToProcess` (5.1) · `Instrument` → Sub-Product. **No branch field** |

New to this repo: `T_PGT_BASIS_S`, `T_PGT_YIELDCURVE_*`, `T_PGT_INSTRUMENT_TYPE_*`, `T_BOX_ENGGRPPHASE_S`,
`T_BOX_ENGPHASE_S`.

**Step 14's `NOT_BRANCH_SCOPED` is now evidenced by declaration**, not only by a query finding no branch
column — Setup and Days_Matured declare no branch field at all.

## 6b. BOX ACC — the declared field catalogue `[confirmed: DB, 2026-09-21]`

Read before the ACC agent is written, so it inherits these rather than discovering them.
Module `35000006.65`, 31 objects, 269 declared fields.

### ⚠️ The trap: `pBranch` does not always mean branch

Twelve ACC objects declare `pBranch → PGT - Branch → T_PGT_BRANCH_S`. **Three do not:**

| Object | Field | Declared target |
|---|---|---|
| **`BOX - Acct Port Property`** | **`pBranch`** | **`PGT - Branch Group` → `T_PGT_BRANCH_GROUP_S`** |
| **`BOX - Config LOC Property`** | **`pBranch`** | **`PGT - Branch Group` → `T_PGT_BRANCH_GROUP_S`** |
| `BOX - GLTA Local Dep` | `pLocalGroup` | `T_PGT_BRANCH_GROUP_S` |

A field **named** `pBranch` pointing at the **branch group** table — on Portfolio Properties, the first
object the ACC agent configures. For NY_SCH that is `FK_LOCALGROUP = 21447.4`, **not** `BRANCH_PK =
20007.4`. Both are valid PKs; writing the wrong one fails silently.

This **corrects an over-generalisation** in the ACC charter, which reads ACC as group-keyed throughout.
It is not: **two objects are group-keyed and twelve are branch-keyed.** Assuming either way for all of
them is wrong.

### The recurring targets

| Field | → | On |
|---|---|---|
| `pInstrument` / `psubproduct` | `PGT_SYS.T_PGT_SUB_PRODUCT_S` | almost everywhere |
| `pInstrumentType` | `T_PGT_INSTRUMENT_TYPE_S` | Conf Instru Type, Net CCS PlanBS, Migration/Auki Criteria |
| `pFolder` / `apPortfolio` / `apFolder` | `PGT_STC.T_PGT_FOLDER_S` | Acct Movements, Acct Key, Net Contract, Grouped Movements, Filter NetPreconf, Migration/Auki Criteria |
| `pLabel` / `pSubLabel` | `PGT_SYS.PGT_DOMAINS` | **MBJ Properties only** |
| `pCounterparty` / `apCounterparty` / `pEntity` | `T_PGT_ENTITY_S` | Conf Instru Type, Filter PreConf, Migration/Auki Criteria |
| `pStrategy`, `pDirection`, `pDebCred`, `pReferenceType` | `PGT_DOMAINS` | several |
| `pSecurity` | `PGT_SECURITY` | Acct Movements, Grouped Movements |
| `pAccount` | `T_BOX_ACCT_GLTA_S` | Net CCS PlanBS |
| `pTopic` | `T_BOX_ACCT_TOPICS_S` | Conf Acc By StdHist |
| `pStdHist` / `pHistStdAcct` | `T_BOX_ACCT_HISTSTD` | Acct By Std Hist, Conf Acc By StdHist |

New to this repo: `T_PGT_BRANCH_GROUP_S`, `T_PGT_INSTRUMENT_TYPE_S`, `T_PGT_SETTLE_ACCOUNT_S`,
`PGT_SECURITY`, `T_PGT_BR_EVE_S`, `T_PGT_OBJ_SOURCE_S`, `V_PGT_CLEARING_S`, `T_BOX_MOV_LINK_ARRAY_X`.

### Two oddities, flagged not interpreted

- **`BOX - Net CCS PlanBS` declares `FkOwnerObj`, `FkParent`, `FkExtension` as `5.1` literals** — the
  identity columns exposed as editable fields on one screen, contradicting the general rule in §3 that
  they are not fields of an object. `[open-question]`
- **`BOX - Migration Criteria` and `BOX - Auki Criteria` are near-identical twins**, both declaring
  `pBranchOrigin` and `pBranchDestination` → `T_PGT_BRANCH_S`, selected by counterparty, folder and
  instrument type. That is **branch-to-branch trade migration machinery** under the AUKI module. Outside
  the onboarding walk, unexamined, and possibly relevant to how an onboarded branch's existing trades
  arrive. `[open-question]` — recorded as a pointer, not investigated.

## 7. What the metamodel does *not* tell you — and a near miss

`FK_PARENT` and `FK_CONNECTION` on `T__OBJ_DEF_S` **do not point at `T__OBJ_DEF_S`.** They resolve into
other `GOM_GLB_SYS` registries, unidentified `[open-question]`.

⚠️ **Read as if they did, `FK_CONNECTION = 35000007.65` resolves to `BOX - Colour Config`** — a plausible
name for something entirely unrelated. That is the same failure as `6401.4` naming two different quote
references: a PK collision across tables. `35000005.65`, the module every BOX FE object hangs off, does
not exist in `T__OBJ_DEF_S` at all. **A PK is only meaningful with its table.**

`CONNECTION_NAME` is present but null on all 41 distinct connections, so it is not the schema resolver.
Object storage names carry no schema prefix; how SIGOM resolves them is still open.

## 8. `T_BOX_ENGFIXDISC_S` — a declared tab the walk does not cover

`BOX_ENG_FixingCurve.apYieldCurve` (kind `3.1`) → `BOX_ENG_YieldCurveDiscFx` → `T_BOX_ENGFIXDISC_S`.
Steps 3 and 4 configure the curve header and its quote array and stop.

⚠️ **Not the same object as step 9's Yield Curve** (`T_BOX_ENGZCCONF_S`, which hangs off Config as
`amZeroCoupon`). Two "yield curve" objects at two levels — precisely how a step goes missing.

**Status: `EVIDENCE_REQUIRED`, parked with steps 9 and 10.** Zero rows and zero curves in Tier 1 PRE
`[confirmed: DB, 2026-09-18]`, which is not evidence it is unnecessary — the same position those two sit
in. No INSERT. Cheapest check is the one already open for them: **look in Tier 1 PRO**; one populated row
settles all three.

What has changed is that it is no longer a silent omission. Finding it is what Q-G7 is for.

## 9. Parked — real, and not on the critical path

Of `GOM_GLB_SYS`'s 96 tables, this project uses two. Recorded so nobody re-derives the list:

| Table | Might give |
|---|---|
| `T__MENU_ITEM_S` | the SIGOM navigation tree, mechanically — `sigom-reference.md` builds it from screenshots |
| `T__ENVIRONMENT_S`, `T__ENV_VAR_S` | possibly a cleaner environment/suffix registry than `PGT_SYS.T_PGT_SOURCE_S` |
| `T__QUERY_DEF_S`, `T__WHERE_PAR_S`, `T__QUERY_FIELD_S` | the predicates each screen actually uses — tantalising, given that two defects were missing `WHERE` clauses |
| `T__ALLOW_ZOOM_S`, `T__EDIT_FIELD_S`, `T__FIELD_PAR_S` | per-field screen definitions beyond `T__EXT_DEF_S` |
| `T__AUDIT_EVT_KIND_S` | whether SIGOM audits on save |
| `T__KEYS_S`, `T__PARKEYS_S` | possibly declared key/FK constraints |

Also seen and unexplained: suffixes **`.95`** (`101.95`) and **`.66`** (`10162.66`) alongside `.1`, `.4`,
`.21`, `.35`, `.44`, `.65`. The environment space is wider than the repo's model — Q-G5 matters more, not
less.

## 10. How to use this

- **Before writing any join** → §6, or run Q-G7 for the object.
- **Before writing any INSERT** → §3 for the identity columns, §5 for what runs on save.
- **Before trusting the walk is complete** → Q-G7 across the screens; an extension with no walk step is
  the next Allowed Errors.
- **Before resolving a PK** → §7. A PK without its table is not an identifier.

## 11. The queries, module-agnostic

**This page is not owned by any one agent.** The FE agent's catalogue
([`queries/fe-config-mining.md`](queries/fe-config-mining.md)) carries **Q-G5**, **Q-G6** and **Q-G7**
with the FE module hard-coded; a future ACC catalogue will carry its own. The forms below are the
parameterised originals — **substitute your own module and nothing else.**

```sql
-- 1. Find your module. Enumerate and pick; never guess a PK.
SELECT FK_PARENT AS module_pk, COUNT(*) AS objects,
       COUNT(CASE WHEN BASIC_STORAGE LIKE 'T\_BOX\_%' ESCAPE '\' THEN 1 END) AS box_storages,
       MIN(PK_NAME) AS name_a, MAX(PK_NAME) AS name_z
FROM   GOM_GLB_SYS.T__OBJ_DEF_S
GROUP  BY FK_PARENT ORDER BY objects DESC;

-- 1b. Or locate it from tables you already know
SELECT PK, PK_NAME, FK_PARENT, BASIC_STORAGE, EXT_STORAGE
FROM   GOM_GLB_SYS.T__OBJ_DEF_S
WHERE  BASIC_STORAGE IN (<tables you already know>) OR EXT_STORAGE IN (<same>);

-- 2. The module's objects: storages, and what runs on save
SELECT PK, PK_NAME, BASIC_STORAGE, EXT_STORAGE, LANG_STORAGE,
       PRE_COMMIT_PROC, FK_PRECOMMIT, PSAVDLL, PSAVFUNC, NOT_SIGOM
FROM   GOM_GLB_SYS.T__OBJ_DEF_S
WHERE  FK_PARENT IN (&&MODULE_PK) ORDER BY PK;

-- 3. Every declared field, with its declared target
SELECT o.PK_NAME AS owning_screen, e.PK AS fk_extension_value, e.FK_PARENT AS fk_owner_obj_value,
       e.FIELD, e.FK_KIND, t.PK_NAME AS target_object, t.BASIC_STORAGE AS target_table
FROM        GOM_GLB_SYS.T__EXT_DEF_S e
JOIN        GOM_GLB_SYS.T__OBJ_DEF_S o ON o.PK = e.FK_PARENT
LEFT JOIN   GOM_GLB_SYS.T__OBJ_DEF_S t ON t.PK = e.FK_OBJECT
WHERE       e.FK_PARENT IN (SELECT PK FROM GOM_GLB_SYS.T__OBJ_DEF_S WHERE FK_PARENT IN (&&MODULE_PK))
ORDER  BY   e.FK_PARENT, e.PK;

-- 4. Everything hiding in a shared bridge table
SELECT o.PK AS fk_owner_obj, o.PK_NAME AS owning_object, e.PK AS fk_extension,
       e.FIELD, e.FK_KIND, t.PK_NAME AS target_object, t.BASIC_STORAGE AS target_table
FROM        GOM_GLB_SYS.T__OBJ_DEF_S o
JOIN        GOM_GLB_SYS.T__EXT_DEF_S e ON e.FK_PARENT = o.PK
LEFT JOIN   GOM_GLB_SYS.T__OBJ_DEF_S t ON t.PK = e.FK_OBJECT
WHERE       o.EXT_STORAGE = '&&BRIDGE_TABLE'
ORDER  BY   o.PK, e.PK;
```

**Read out of them, in this order:** the identity constants per target table (§3); the declared target
of every FK the walk writes (§4, §6); the pre-commit procedures (§5); and a **completeness diff** —
any extension with no step in your walk is a candidate missing step.

None of this needs `BOX_FE` or `BOX_ACC` grants. `GOM_GLB_SYS` is readable on its own.
