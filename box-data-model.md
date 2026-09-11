## Schema Overview

| Schema | Purpose | Key Table Prefixes |
|--------|---------|--------------------|
| BOX_TRD | Trade processor persistence | T_BOX_FXSPOT_S, T_BOX_CONTRACT_S, T_BOX_PARAMETER_S |
| DEVENG | Financial Engine production | T_FE_DEAL_DATA_S, T_FE_FLOW_DATA_S, T_FE_DEAL_STATUS_S |
| DEVENG_RAW | Financial Engine staging | T_FE_DEAL_DATA_RAW, T_FE_FLOW_DATA_RAW, T_FE_MTM_DATA_RAW |
| BOX_ACC | Accounting | T_BOX_ACCT_DOC_S, T_BOX_ACCT_MOV_S, T_BOX_ACCT_PORT_PROP_S |
| GOM_GLB_SYS | Global static data | T_GOM_BRANCH_S, T_GOM_CURRENCY_S, T_GOM_COUNTERPARTY_S |
| PGT_MRK | Market data — **shared by BOX and GBO**, not module-owned; one copy read the same way from either side `[confirmed: DB via BOX Lead]` | T_PGT_MARKET_PRICE_S, T_PGT_FX_RATE_S, T_PGT_QUOTE_REFERENCE_S, T_PGT_QUOTE_SOURCE_S |
| PGT_TRD | Trade static data | T_PGT_INSTRUMENT_S, T_PGT_TYPOLOGY_S |
| PGT_PRC | Process configuration | (process config tables) |
| PGT_PRG | Program configuration | (program config tables) |
| PGT_STC | Static configuration | T_PGT_BRANCH_S, T_PGT_CURRENCY_S, T_PGT_ENTITY_S |
| PGT_SYS | System configuration; also holds the Family/Product/Sub-product classification hierarchy and at least one generic domain/enum table (`PGT_DOMAINS`) observed used identically from both BOX and GBO queries — not yet confirmed as schema-wide `[open-question]` | T_PGT_TABLE_S, T_PGT_COLS_S, T_PGT_UPDATE_S, T_PGT_FAMILY_S, T_PGT_PRODUCT_S, T_PGT_SUB_PRODUCT_S, PGT_DOMAINS |

---

## Constraint metadata — no declared foreign keys `[confirmed: DB]`

The BOX/GBO schemas declare only **primary key (`P`)** and **check (`C`)** constraints (per
`ALL_CONSTRAINTS`). **No foreign key (`R`) constraints exist anywhere in this schema family.**
Referential integrity between tables is not enforced at the database level at all — every `FK_*`
relationship documented in this repo (and every join in
[fe-config-mining.md](queries/fe-config-mining.md)) lives only in application logic, never in schema
metadata.

**Why this matters for the mining work:** a join column name that looks right (`FK_INSTRUMENT`,
`FK_BRANCH`, …) is a naming convention and an observed-in-practice relationship, not something
`ALL_CONSTRAINTS` can confirm or rule out. There is no `DBA_CONSTRAINTS`/`ALL_CONS_COLUMNS` query that
settles an assumed join the way there would be in a schema with declared FKs — it can only be
confirmed by data (a query that returns matching rows) or by a person who knows the application logic.
This is the underlying reason the query catalogue's "Coverage check" table exists and why a zero-row
result is never treated as confirmed absence when the join itself is unconfirmed (`sigom-box-fe-configs-agent`
hard rule, [AGENT.md](../../agents/sigom-box-fe-configs-agent/AGENT.md)) — the schema itself gives no
independent way to check the join, only the data does.

---

## BOX_ACC Accounting Tables

### Core Accounting Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| T_BOX_ACCT_DOC_S | Accounting documents | num_Doc, num_Branch, FK_INSTRUMENT, FK_PORTFOLIO_PROPERTIES, FK_ACCT_STRATEGY, ACCOUNTING_REF, EXTERNAL_ID |
| T_BOX_ACCT_MOV_S | Accounting movements | num_doc, p_acctno, CCY_CREDIT, CCY_DEBIT, VAL_CREDIT, VAL_DEBIT, LOC_CODE, FK_DECRIND, FK_DIRECTION |
| T_BOX_ACCT_PORT_PROP_S (T_PORTFOLIO_PROPERTIES_S) | Portfolio properties | num_PKPortProp, FK_BRANCHGROUP, FK_INSTRUMENT, FK_REGISTRY, FK_PROPERTIES |
| T_BOX_ACCT_KEY_S | Accounting keys | FK_TOPIC, FK_OWNER_OBJ |
| T_BOX_ACCT_KEY_GROUP_S | Accounting key groups | (key group fields) |
| T_BOX_ACCT_HISTSTD (T_BOX_ACCT_BY_STD_HIST_S) | Historic standard accounting | FK_HISTSTDACCT, num_StdHistoric |
| T_BOX_REFERENCEACC_S | Accounting references | (reference fields) |
| T_BOX_MBJ_PROPERTIES_S | MBJ batch properties | FK_PROPERTIES |
| T_BOX_ACCT_GLTA_S | GLTA (GL account) mapping | FK_GLTA, FK_GLTATYPE, GLTA_CODE |
| T_BOX_ACCT_GROUP_S | Accounting groups | (group fields) |
| T_BOX_ACCT_HIST_SOURCE_S | Historic source mapping | FK_SOURCE |
| T_BOX_ACCT_LIST_COND_S | List conditions | FK_TOPIC, CST_EXT_LIST_COND |
| T_BOX_ACCT_LIST_TOPIC_S | List topics | FK_TOPIC, CST_EXT_INS_TOPIC |
| T_BOX_ACCT_PARENT_DATE_S | Parent date tracking | PARENT_ACCOUNT, FK_PARENT |
| T_BOX_ACCT_RULER | Accounting ruler configuration | (ruler fields) |
| T_BOX_ACCT_RULER_GROUP | Accounting ruler groups | (ruler group fields) |
| T_BOX_ACCT_TOPICS_S | Accounting topics | FK_TOPIC |
| T_BOX_AC_BSPLAN | Balance sheet plan | (balance sheet fields) |
| T_BOX_GLTA_LOCAL_S | Local GLTA mapping | GLTA_CODE, LOC_CODE |

### Configuration Tables

| Table | Purpose |
|-------|---------|
| T_BOX_CONDPAR_PROP_S | Conditional parameter properties |
| T_BOX_CONFIG_ACCRUAL_S | Accrual configuration |
| T_BOX_CONF_ACCSTDHIST_S | Accounting standard historic config |
| T_BOX_CONF_INSTRUM_TYPE_S | Instrument type configuration |
| T_BOX_CONF_LO_PROP_S | Local properties configuration |
| T_BOX_CROSS_ACCTCONF_S | Cross accounting configuration |
| T_BOX_TOPICS_GROUP_S | Topics group configuration |
| T_BOX_ST_HIST_GROUP_S | Standard historic group configuration |

---

## Financial Engine Tables

### Production Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| T_FE_DEAL_DATA_S (T_BOX_DEAL_DATA_S) | Deal master data | deal_id, FK_BRANCH, FK_INSTRUMENT, FK_CURRENCY, FK_ENTITY, FK_PORTFOLIO, trade_date, FK_CREATEUSER, FK_CANCELUSER |
| T_FE_FLOW_DATA_S (T_BOX_FLOW_DATA_S) | Cash flow data | FK_BRANCH, FK_CURRENCY, FK_DIRECTION, FK_SETTHEADER, num_SettHeader, FK_SETTLEACCOUNT |
| T_FE_DEAL_STATUS_S (T_BOX_DEAL_S) | Deal-level financial status | box_deal_data, clast_financial, AUX_STATUS |
| T_FE_FLOW_STATUS_S | Flow-level financial status | (flow status fields) |
| T_BOX_IRDATADEAL_S | IRS-specific deal data | rec_IR_DataDeal_IN |
| T_BOX_IRFINANCST_S | IRS-specific financial status | rec_FinancSt_IN, rec_FinancSt_OUT |
| T_BOX_MMDATADEAL_S | Money Market deal data | (MM deal fields) |
| T_BOX_MMFINANCST_S | Money Market financial status | (MM status fields) |

### Staging Tables

| Table | Purpose |
|-------|---------|
| T_FE_DEAL_DATA_STAGING_S | Deal data staging |
| T_FE_FLOW_DATA_STAGING_S | Flow data staging |
| T_FE_DEAL_POINTER_S | Deal pointer/index |

### RAW Tables (Data Lake Import)

| Table | Purpose |
|-------|---------|
| T_FE_DEAL_DATA_RAW (T_BOX_RAW_DEAL_DATA_S) | RAW deal data from Data Lake |
| T_FE_FLOW_DATA_RAW (T_BOX_RAW_FLOW_DATA_S) | RAW flow data from Data Lake |
| T_FE_MTM_DATA_RAW (T_BOX_RAW_MARKET_DATA_S) | RAW MTM/market data from Data Lake |

### MTM Tables

| Table | Purpose |
|-------|---------|
| T_BOX_MTM_1_S (CST_OBJ_BOX_MTM_DATA) | MTM data for instrument type 1 |
| T_BOX_MTM_84_S | MTM data for instrument type 84 (FX Spot) |
| T_BOX_MTM_91_S | MTM data for instrument type 91 |

---

## Financial Engine Configuration Tables

| Table | Purpose |
|-------|---------|
| T_BOX_ENGCONF_S | Financial engine configuration |
| T_BOX_ENGACCRCONF_S | Accrual configuration |
| T_BOX_ENGDAYS_MATURED_S (CST_OBJ_BOX_DAY_MATURED) | Days to maturity tracking |
| T_BOX_ENGDOM_S | Domain configuration |
| T_BOX_ENGFCURVE_S | Forward curve configuration |
| T_BOX_ENGFIXDISC_S | Fixing discount configuration |
| T_BOX_ENGFPRICE_S | Forward price configuration |
| T_BOX_ENGHISTMDATA_S | Historic market data |
| T_BOX_ENGINSTRUMENTS_S | Instrument configuration |
| T_BOX_ENGLOGCONF_S | Logging configuration |
| T_BOX_ENGPROCQUEUES_S | Process queue configuration |
| T_BOX_ENGQUEUES_EXEC_S | Queue execution tracking |
| T_BOX_ENGSETUP_S | Engine setup configuration |
| T_BOX_FIXING_ASSIGNMENT_S | Fixing assignment |
| T_BOX_FIXING_BY_INSTR_S | Fixing by instrument |
| T_BOX_FIXING_CURVE_S | Fixing curve data |
| T_BOX_INTERPCURVE_S | Interpolation curve |
| T_BOX_INTERPPOINT_S | Interpolation points |
| T_BOX_FX_LIQUID_S | FX liquidity data |
| T_BOX_BRPROCCAL_S | Branch process calendar |
| T_BOX_BRPROCCAL_QUEUE_S_OPTZ | Optimized branch process calendar queue |
| T_BOX_CONF_BY_BOOK_S | Book batch-execution registration — new BOX functionality, **no GBO analogue** `[stated: BOX FE Developer, 2026-09-11]`. Confirmed keys: `FK_BRANCH` → `PGT_STC.T_PGT_BRANCH_S.PK`, `FK_INSTRUMENT` → `PGT_SYS.T_PGT_SUB_PRODUCT_S.PK` (the Sub-Product level of the [Product classification hierarchy](#product-classification-hierarchy-confirmed-db) below), `FK_LABEL` → `PGT_SYS.PGT_DOMAINS.PK` (book code + description, e.g. `XLB01 - HPE FIXED INCOME SLB`). See `branch-config/fe-branch-configuration.md`'s "Book" section for the full join and its confirmed tie to the Data-Lake Book dimension |

---

## Settlement and Netting Tables

| Table | Purpose |
|-------|---------|
| T_BOX_NETCONTRACT_S | Netting contracts |
| T_BOX_NETCCS_BSPLAN_S | CCS netting balance sheet plan |

---

## Utility and Audit Tables

| Table | Purpose |
|-------|---------|
| T_BOX_FLAG_S | Feature flags |
| T_BOX_LOGERROR_S | Error logging |
| T_BOX_MIGRA_S | Migration tracking |
| T_BOX_MBJ_FIELDS_S | MBJ field definitions |
| T_BOX_KEY_UPDATE_GROUP_S | Key update groups |
| T_BOX_LINK_ARRAY_X | Link array (cross-reference) |
| T_BOX_TMP_BALANCE_DEAL | Temporary balance by deal |
| T_BOX_TMP_BALANCE_INSTRUM_S | Temporary balance by instrument |

---

## PGT Static Data Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| T_PGT_BRANCH_S | Branch master data | FK_BRANCH, branch_id_in |
| T_PGT_CURRENCY_S | Currency master data | FK_CURRENCY |
| T_PGT_ENTITY_S | Entity master data | FK_ENTITY |
| T_PGT_CALENDAR_S | Calendar data | FK_CALENDAR |
| T_PGT_FOLDER_S | Folder/portfolio data | FK_FOLDER |
| T_PGT_INSTRUMENT_S (CST_OWN_INSTRUMENT) | Instrument master | FK_INSTRUMENT, num_fk_instrument |
| T_PGT_FAMILY_S (`PGT_SYS`) | Product family — top of the three-level classification | PK |
| T_PGT_PRODUCT_S (`PGT_SYS`) | Product — middle level | PK, FK_PARENT (→ `T_PGT_FAMILY_S.PK`) |
| T_PGT_SUB_PRODUCT_S (`PGT_SYS`) | Sub-product — bottom level | PK, FK_PARENT (→ `T_PGT_PRODUCT_S.PK`) |
| T_PGT_QUOTE_REFERENCE_S (`PGT_MRK`) | Quote reference — the array of quotes a fixing curve linkage row points at | PK, FK_QUOTESOURCE (→ `T_PGT_QUOTE_SOURCE_S.PK`), FK_QUOTETYPE (→ `PGT_SYS.PGT_DOMAINS.PK`) |
| T_PGT_QUOTE_SOURCE_S (`PGT_MRK`) | Quote source master (the market-data feed) | PK |
| PGT_DOMAINS (`PGT_SYS`) | Generic domain/enumeration values — quote type is one observed use, not quote-specific itself | PK |
| T_PGT_TABLE_S | Table metadata | table_name |
| T_PGT_COLS_S | Column metadata | (column fields) |
| T_PGT_COND_S | Condition definitions | (condition fields) |
| T_PGT_EVE_S | Event definitions | FK_TRADEEVENT |
| T_PGT_EVLOG_EVENT_S | Event log | (event log fields) |
| T_PGT_EXP_EXT_S | Export extension | (export fields) |
| T_PGT_OBJSRC_INPUT_S | Object source input | CST_EXT_OBJSRC_INPT_SOURCE |
| T_PGT_OBJ_SOURCE_S | Object source | FK_SOURCE, SOURCE_SYSTEM |
| T_PGT_UPDATE_S | Update tracking | (update fields) |

---

## Product classification hierarchy `[confirmed: DB]`

Products in GBO/BOX are classified in three levels, all in the `PGT_SYS` schema, chained by
`FK_PARENT`:

```text
PGT_SYS.T_PGT_FAMILY_S           top level — e.g. FX, PK 3.4
        PK
        |
        | FK_PARENT
        ▼
PGT_SYS.T_PGT_PRODUCT_S          middle level — e.g. FX SPOT, FX SWAP (both FK_PARENT = 3.4)
        PK
        |
        | FK_PARENT
        ▼
PGT_SYS.T_PGT_SUB_PRODUCT_S      bottom level — e.g. FX NDS, FX SPOT (both FK_PARENT = 8.4,
                                  the FX SPOT product's own PK)
```

Confirmed example: Family `FX` (`PK=3.4`) is the `FK_PARENT` for products `FX SPOT` and `FX SWAP`.
Sub-products `FX NDS` and `FX SPOT` in turn share `FK_PARENT=8.4` — the PK of the `FX SPOT` product
row. Note the naming overlap this reveals: "FX SPOT" exists as both a Product and, separately, as a
Sub-product of itself — the two are distinct rows with distinct PKs, not a duplicate.

**Confirmed real consumer, 2026-09-11:** `T_BOX_CONF_BY_BOOK_S.FK_INSTRUMENT` (the Book
batch-execution table, above) references `T_PGT_SUB_PRODUCT_S.PK` directly — the first table in this
repo confirmed to key off the **Sub-Product** level of this hierarchy specifically, rather than a
generic "instrument" table. Worth keeping in mind elsewhere in the walk: an "instrument" FK is not
self-evidently pointing at the same table every time.

**Likely relevance, not yet confirmed as such:** `branch-trading-readiness.md` §2 ("Effective
instrument type is conditional") observes that several products with no row in
`BOX_ACC.T_BOX_CONF_INSTRUM_TYPE_S` still resolve an effective instrument type, and attributes this
to "product fallback logic" without naming a mechanism. This three-level hierarchy is a plausible
candidate for that mechanism — a missing Sub-product-level override could fall back to its parent
Product or Family — but that link is inferred from shape alone, not DB-witnessed. Treat it as an
open question until a fallback read/query is actually traced through these tables.

---

## Common Foreign Key Fields

| FK Field | References | Purpose |
|----------|-----------|---------|
| FK_BRANCH | T_PGT_BRANCH_S | Branch identifier |
| FK_BRANCHGROUP | Branch group table | Branch group identifier |
| FK_CURRENCY | T_PGT_CURRENCY_S | Currency identifier |
| FK_ENTITY | T_PGT_ENTITY_S | Entity identifier |
| FK_INSTRUMENT | T_PGT_INSTRUMENT_S | Instrument type identifier |
| FK_PORTFOLIO | Portfolio table | Portfolio identifier |
| FK_PORTFOLIO_PROPERTIES | T_BOX_ACCT_PORT_PROP_S | Portfolio properties identifier |
| FK_ACCT_STRATEGY | Accounting strategy table | Accounting strategy identifier |
| FK_REGISTRY | Registry table | Registry identifier |
| FK_PROPERTIES | Properties table | Properties identifier |
| FK_OWNER_OBJ | Owner object table | Owner object identifier |
| FK_TOPIC | Topic table | Topic identifier |
| FK_DIRECTION | Direction table | Direction (buy/sell) identifier |
| FK_DECRIND | Debit/Credit indicator table | Debit/Credit indicator |
| FK_GLTA | GLTA table | GL account identifier |
| FK_GLTATYPE | GLTA type table | GL account type identifier |
| FK_SETTHEADER | Settlement header table | Settlement header identifier |
| FK_SETTLEACCOUNT | Settlement account table | Settlement account identifier |
| FK_CALENDAR | T_PGT_CALENDAR_S | Calendar identifier |
| FK_FOLDER | T_PGT_FOLDER_S | Folder/portfolio identifier |
| FK_TRADEEVENT | T_PGT_EVE_S | Trade event identifier |
| FK_SOURCE | T_PGT_OBJ_SOURCE_S | Source system identifier |
| FK_EXT_SOURCESYSTEM | External source system table | External source system identifier |
| FK_CREATEUSER | User table | User who created the record |
| FK_CANCELUSER | User table | User who cancelled the record |
| FK_EXTENSION | Extension table | Extension identifier |
| FK_PARENT | Parent record table | Parent record identifier |
| FK_HISTSTDACCT | Historic standard accounting table | Historic standard accounting identifier |

---

## Settlement Processing Flags

| Flag | Purpose |
|------|---------|
| NOTIONAL_PROCESSED | Indicates notional has been processed in netting |
| PRINCIPAL_PROCESSED | Indicates principal has been processed in netting |
| AMOUNT_PROCESSED | Indicates amount has been processed |
| CURRENCY_PROCESSED | Indicates currency has been processed |
| BASIS_PROCESSED | Indicates basis has been processed |

---

## Object Source Constants

| Constant | Purpose |
|----------|---------|
| CST_OWN_CONF_GLOBAL | Global configuration owner |
| CST_OWN_CONF_LOCAL | Local configuration owner |
| CST_OWN_INSTRUMENT | Instrument owner |
| CST_OWN_PORTFOLIO | Portfolio owner |
| CST_SOURCE_LAKE | Data Lake source identifier |
| CST_OBJ_BOX_DEAL_DATA | Deal data object identifier |
| CST_OBJ_BOX_FLOW_DATA | Flow data object identifier |
| CST_OBJ_BOX_MM_DATA_DEAL | Money Market deal data object identifier |
| CST_OBJ_BOX_MTM_DATA | MTM data object identifier |
| CST_OBJ_BOX_DAY_MATURED | Days matured object identifier |
| CST_EXT_INS_TOPIC | Instrument topic extension |
| CST_EXT_LINK_GL | GL link extension |
| CST_EXT_LINK_LO | Local link extension |
| CST_EXT_LIST_COND | List condition extension |
| CST_EXT_LIST_GL | GL list extension |
| CST_EXT_LIST_LO | Local list extension |
| CST_EXT_OBJSRC_INPT_SOURCE | Object source input extension |

---

## Data Tier Separation

| Tier | Purpose | Tables |
|------|---------|--------|
| Data_OnlyDEVCore | Core development data | (core tables) |
| Data_OnlyTier1MD | Tier 1 master data | (tier 1 tables) |
| Data_OnlyTier2US | Tier 2 user-specific data | (tier 2 tables) |
| 05_Static | Static reference data | (static tables) |
| 20_Packages | Package definitions | (package tables) |

---

## Key Procedure Parameters

| Parameter | Type | Purpose |
|-----------|------|---------|
| num_Doc | NUMBER | Document identifier |
| num_Branch | NUMBER | Branch identifier |
| num_Event | NUMBER | Event identifier |
| num_SettHeader | NUMBER | Settlement header identifier |
| num_StdHistoric | NUMBER | Standard historic identifier |
| num_Direction | NUMBER | Direction identifier |
| num_fk_instrument | NUMBER | Instrument FK |
| num_owdoc | NUMBER | Owner document |
| num_pkdoc | NUMBER | Document PK |
| num_settheader | NUMBER | Settlement header |
| num_reallocate_yn | NUMBER | Reallocate yes/no flag |
| branch_id_in | VARCHAR2 | Branch ID input |
| deal_id | VARCHAR2 | Deal identifier |
| trade_date | DATE | Trade date |
| process_date | DATE | Process date |
| owner_obj_out | NUMBER | Owner object output |
| pk_out | NUMBER | PK output |
| str_docname | VARCHAR2 | Document name |
| str_docdescr | VARCHAR2 | Document description |
| str_prod_family | VARCHAR2 | Product family |
| table_name | VARCHAR2 | Table name |
| rec_DataDeal_IN | RECORD | Deal data input record |
| rec_FinancSt_IN | RECORD | Financial status input record |
| rec_FinancSt_OUT | RECORD | Financial status output record |
| rec_IR_DataDeal_IN | RECORD | IRS deal data input record |
| p_AccountingRef | VARCHAR2 | Accounting reference |
| p_Instrument (P_Instrument) | NUMBER | Instrument parameter |
| p_Label (P_Label) | VARCHAR2 | Label parameter |
| p_ProcessDate (P_ProcessDate) | DATE | Process date parameter |
| p_br | NUMBER | Branch parameter |
| p_doc | NUMBER | Document parameter |
| p_dreg | NUMBER | Registry parameter |
| p_setheader | NUMBER | Settlement header parameter |
| p_topic | NUMBER | Topic parameter |
| p_properties | NUMBER | Properties parameter |
| p_createdoc | NUMBER | Create document parameter |
| p_put_mov | NUMBER | Put movement parameter |
| p_getacctno | VARCHAR2 | Get account number parameter |
| p_GltaCode | VARCHAR2 | GLTA code parameter |
| p_GetFinancialData | RECORD | Get financial data parameter |
| p_GetAcctAddCashRegistry | RECORD | Get accounting additional cash registry parameter |
| p_GetValAddCashRegistry | RECORD | Get value additional cash registry parameter |
| p_MainBackwardOptz | PROCEDURE | Main backward optimization procedure |
| gn_ownersource | NUMBER | Global owner source |
| clast_financial | VARCHAR2 | Last financial classification |
| box_deal_data | VARCHAR2 | BOX deal data |
| load_accrue_parameters | PROCEDURE | Load accrual parameters procedure |
| main_backward_optz | PROCEDURE | Main backward optimization procedure |

---

## Package Body References

| Package Body | Purpose |
|--------------|---------|
| pkg_enggncompute_optz_body | Accrual computation package body |
| pkg_engmain_optz_body | Main dispatcher package body |
| pkg_engmainir_optz_body | IRS financial status package body |
| pkg_fe_deal_calculation_body | Deal calculation package body |
| pkg_fe_flow_calculation_body | Flow calculation package body |
| pkg_fe_mtm_calculation_body | MTM calculation package body |
| pkg_fe_propagation_data_body | Data propagation package body |
| pkg_fe_raw_review_body | RAW review package body |
| pkg_import_box_fe_body | Import package body |
| pkg_acct_trg | Accounting trigger package |
| pkg_enggnget | Generic get package |
| pgt_prg | Program configuration package |
| Pkg_Acctgeneral | Accounting general package |
| Pkg_EngIR_Optz | IRS optimization package |
| Pkg_Enggncompute_Optz | Generic compute optimization package |
| Pkg_Enggnget | Generic get package |
| Pkg_Enggnreval | Generic revaluation package |
| PKG_CURRGENERAL | Currency general package |
| PKG_PGTUTILITY | PGT utility package |
| PKG_ENGMAINCES_OPTZ | Commodities financial status package |
| PKG_ENGMAINCFM_OPTZ | Cash Flow Matching financial status package |
| PKG_ENGMAINCF_OPTZ | Caps/Floors financial status package |

---

## Settlement Pipeline Constants

| Constant | Purpose |
|----------|---------|
| UPDATE_EXCLUSION_FLAG | Netting step 1: Update exclusion flag |
| INCLUDE_IN_AUTOMATIC_NETTING | Netting step 2: Include in automatic netting |
| CHECK_UNFIXED_FLOWS | Netting step 3: Check unfixed flows |
| UPDATE_AMOUNT_MEDUSA_NET_FLOW | Netting step 4: Update Medusa net flow amount |
| CHECK_GROSS_FLOW_IS_NETTED | Netting step 5: Check gross flow is netted |
| MERGE_ACTIVATED | Flag: Merge netting rules into single operation |
| NUM_ITER_FOR_COMMIT | Number of iterations before commit |
| MC_CANCEL | Margin Call cancellation flag |
| BOXMedusaFlowService | Service for Medusa flow management |
| BOXMedusaFlowCreator | Creator for Medusa flow entities |
| BOX_DEAL_PROPERTIES | Deal properties configuration |
| IRSBOX12345_65_20240315 | Example IRS BOX identifier |
| CENTER_SUB | Center sub-account field |
| COMPLEM_CODE | Complement code field |
