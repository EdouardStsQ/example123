## Schema Overview

| Schema | Purpose | Key Table Prefixes |
|--------|---------|--------------------|
| BOX_TRD | Trade processor persistence | T_BOX_FXSPOT_S, T_BOX_CONTRACT_S, T_BOX_PARAMETER_S |
| DEVENG | Financial Engine production | T_FE_DEAL_DATA_S, T_FE_FLOW_DATA_S, T_FE_DEAL_STATUS_S |
| DEVENG_RAW | Financial Engine staging | T_FE_DEAL_DATA_RAW, T_FE_FLOW_DATA_RAW, T_FE_MTM_DATA_RAW |
| BOX_ACC | Accounting | T_BOX_ACCT_DOC_S, T_BOX_ACCT_MOV_S, T_BOX_ACCT_PORT_PROP_S |
| BOX_SYS | BOX system/configuration dictionaries — cross-system value translation. Not covered by the `sigom-box-fe-configs-agent` walk, which is `BOX_FE`-scoped | T_BOX_CROSS_REF_S (see [tables/t-box-cross-ref-s.md](tables/t-box-cross-ref-s.md)) |
| GOM_GLB_SYS | Global static data | T_GOM_BRANCH_S, T_GOM_CURRENCY_S, T_GOM_COUNTERPARTY_S |
| PGT_MRK | Market data — **shared by BOX and GBO**, not module-owned; one copy read the same way from either side `[confirmed: DB via BOX Lead]` | T_PGT_MARKET_PRICE_S, T_PGT_FX_RATE_S, T_PGT_QUOTE_REFERENCE_S, T_PGT_QUOTE_SOURCE_S |
| PGT_TRD | Trade static data | T_PGT_INSTRUMENT_S, T_PGT_TYPOLOGY_S |
| PGT_PRC | Process configuration | (process config tables) |
| PGT_PRG | Program configuration | (program config tables) |
| PGT_STC | Static configuration. **Shared — identical rows in every environment** `[stated: Edouard, 2026-09-18]` | T_PGT_BRANCH_S, T_PGT_CURRENCY_S, T_PGT_ENTITY_S, T_PGT_CURR_PAIR_S (currency pairs, `SHORTNAME`) |
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

### `T_BOX_MBJ_PROPERTIES_S` — the batch job binding `[confirmed: DB extract, 2026-09-16]`

Listed thinly above as "MBJ batch properties". It deserves more, because it is **the table that ties a
Control-M job to the work it does** — and therefore the table a branch onboarding has to write rows
into for the batch to run at all.

It is the maintenance target of SIGOM `BOX - Accounting > MBJ Config`
([sigom-reference](sigom-reference.md)), and it binds each configured `JOB_NAME` to:

| Bound to | Notes |
|---|---|
| **Branch** | e.g. Madrid `22.21` |
| **Instrument** | e.g. CCS `20.4`, OTC `20111.4` |
| **MBJ process group** | e.g. `3375.65` — the event group the job dispatches into |
| Worker / concurrency settings | |
| Monitoring and recovery flags | |
| Label, sub-label, calendar | matching `f_ExecuteGroup`'s later arguments |
| MIC settings | including `MIC_FLOW_MODE` — observed as `On-Line` on an OTC job |

**`JOB_NAME` is unique in the table**, so the binding is one job → one (branch, instrument, group)
triple. Worked examples and the surrounding Control-M topology are in
[job-chains/box-fe-acc-batch-runtime.md](job-chains/box-fe-acc-batch-runtime.md).

Two things to carry forward:

**The three-suffix pattern is visible in one row here.** Branch `.21`, instrument `.4`, MBJ group
`.65` — the cleanest evidence yet for what those PK suffixes mean. See
[tables/t-box-cross-ref-s.md](tables/t-box-cross-ref-s.md).

**`MIC_FLOW_MODE = On-Line` appears on a *batch* job row.** `[open-question]` The repo's standing gap
is that the online (CROSS_REF) arrival path has no document and no confirmed mechanism
([topic-index](../topic-index.md)). A batch-job configuration table carrying an explicit online flow
mode is a lead worth chasing: the online path may be partly expressed as MBJ configuration rather than
existing solely in Camunda/TIBCO. Not evidence that it *is* — just the first place the two ideas touch.

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

## Folders — branch-keyed GBO static data

`[confirmed: DB via BOX FE Developer, 2026-09-15]` — `PGT_STC.T_PGT_FOLDER_S`, maintained through SIGOM
at `GBO > Static Data > Environment > Config > Folders`.

**Folder is branch-keyed**, which makes it structurally relevant to branch onboarding in a way most
static data isn't: `FK_BRANCH` → `PGT_STC.T_PGT_BRANCH_S.PK`. Whether a *new* branch requires its own
Folder rows is **not established** — see the flagged item in
[`../process/checklists/branch-onboarding-checklist.md`](../process/checklists/branch-onboarding-checklist.md).

### The query `[confirmed: DB]`

Lists the folders configured for one branch (Madrid, `22.21`, as the worked example):

```sql
SELECT T1.PK, T1.CODE,
       T1.DESCRIPTION, T2.PK,
       T2.DESCRIPTION, T3.PK, T3.DESCRIPTION,
       T1.COVERAGEIND, T4.PK, T4.DESCRIPTION,
       T1.COSTCENTER, T1.STATUS
FROM   PGT_STC.T_PGT_FOLDER_S T1,
       PGT_STC.T_PGT_BRANCH_S T2,
       PGT_SYS.PGT_DOMAINS    T3,
       PGT_SYS.PGT_DOMAINS    T4
WHERE  T1.FK_BRANCH       = T2.PK(+)
AND    T2.PK              = 22.21   -- branch PK; Madrid in this example
AND    T1.FK_COVERAGETYPE = T3.PK(+)
AND    T1.FK_COVERAGELIST = T4.PK(+)
ORDER  BY T1.CODE
```

`PGT_DOMAINS` is joined **twice**, aliased `T3` and `T4`, resolving two different coverage attributes
on the same folder row — the clearest single demonstration yet that this table is a general-purpose
enumeration rather than anything domain-specific.

**One caveat if you reuse this for another branch.** The Oracle legacy outer joins (`(+)`) on
`FK_BRANCH` are *neutralised* by the hard `T2.PK = 22.21` predicate: filtering on the outer-joined
table's own PK turns that join back into an inner join. So this query returns folders **assigned to
that branch** and cannot return folders with a null `FK_BRANCH` (global/unassigned, if such rows
exist). Don't read an empty result as "this branch has no folders" without first checking whether
folders are branch-assigned at all in that environment. The `(+)` on the two `PGT_DOMAINS` joins is
genuine and does work — a folder with no coverage type still returns.

### What a Folder is, and what it is not

`Folder` is the **portfolio-side** dimension. [`fe-raw-data-stage.md`](fe-raw-data-stage.md) already
established the distinction from the other direction, tracing a Murex trade into RAW: *"RAW Flow Book
comes from the joined trade-details Book context, separately from the trade-details portfolio used as
the Deal/FOLDER context."* So:

- **Folder** ≈ the Murex portfolio context, mastered here in `T_PGT_FOLDER_S`.
- **Book** ≈ the BOX/Data-Lake processing dimension, mastered in `PGT_SYS.PGT_DOMAINS` and registered
  for batch execution in `T_BOX_CONF_BY_BOOK_S` (see the Financial Engine Configuration Tables above).

These are different dimensions that both travel with a deal, and conflating them is an easy mistake —
`FOLDER` and `BOOK` both appear as columns on RAW Deal and on `T_BOX_DATADEAL_S`.

**BOX-side folder master is unidentified.** `BOX_ACC.T_BOX_NETCONTRACT_S` carries an `FK_FOLDER`
column (`../process/checklists/acc-add-product-checklist.md`), so BOX consumes the folder dimension —
but whether it points at this same `PGT_STC.T_PGT_FOLDER_S` (shared, like `PGT_MRK`/`PGT_DOMAINS`) or
at an unnamed `T_BOX_FOLDER_S` twin has not been established. `[open-question]` — one `ALL_TABLES`
lookup settles it.

---

## Financial Status surfaces: GBO vs BOX FE

`[confirmed: DB via BOX FE Developer, 2026-09-15]` — the per-product data surface behind each system's `Financial Engine > Financial Status` SIGOM menu.
Screen-by-screen table names, the full per-product lists, and the GBO structural exceptions (ETD, SCF)
live in [`sigom-reference.md`](sigom-reference.md); this section holds the **structural comparison**,
because it is where the two systems diverge most sharply and where a naive mapping does real damage.

### The shapes are not the same

| Row | GBO (`DEVENG`) | BOX FE (`BOX_FE`) |
|---|---|---|
| **Deal Data** | `T_PGT_<CODE>DATAMIS_S` — **one table per product** | `T_BOX_DATADEAL_S` — **one shared table for all 11 products** |
| **Financial Data** | `T_PGT_<CODE>FINANCST_S` — per product | `T_BOX_<CODE>FINANCST_S` — per product |
| **Marketvalue / MtM** | `T_PGT_<CODE>RISK_S` — a **table**, per product | `V_BOX_ENG<CODE>DATAMIS_S` — a **view**, per product. No per-product `RISK` table exists |
| **MIS-MDR Interface** | `V_PGT_ENG<CODE>DATAMIS_S` — a view, some products | *(no equivalent row in the BOX menu)* |

Only the **Financial Data** row maps cleanly between the two. The other three do not:

**Deal Data collapses from many tables to one.** BOX routes every product's Deal Data screen through the
single `T_BOX_DATADEAL_S`, presumably filtered by product/instrument type. This is independently
confirmed twice over — the developer stated it as a blanket rule, and
[`fe-raw-data-stage.md`](fe-raw-data-stage.md) separately sampled the table and found IRS and CCS rows
coexisting in it. Any code or query that assumes a `T_BOX_<CODE>DATADEAL_S` per product is wrong.

> ✅ **Resolved, 2026-09-16 — they are the same kind of object after all.** The add-a-product runbook
> ([`../process/05-add-product-procedure.md`](../process/05-add-product-procedure.md)) instructs that
> the SIGOM object created for the BOX view be named **`BOX_ENG_Interfaz <product> MIS-MDR`**. So the
> BOX object *is* a MIS-MDR interface, exactly as GBO labels its equivalent; only the **menu label**
> differs (BOX's Financial Status menu calls the leaf "MtM Data"). The warning below is kept because
> the labelling trap is real and still visible in the menus — but the underlying objects correspond,
> and a GBO↔BOX mapping across this row is now justified rather than assumed. What each view actually
> *returns* is still unverified.

**⚠️ `V_*_ENG<CODE>DATAMIS_S` is a false friend.** The identical naming convention carries a *different
label* on each side: **MIS-MDR Interface** in GBO, **MtM Data** in BOX. GBO's actual MtM/risk equivalent
is the separate `T_PGT_<CODE>RISK_S` table. Treating the two views as counterparts because the names
match is the single most likely way to mis-map this surface. `[open-question]` — functional
equivalence has not been tested.

### Product-set divergence — BOX FE covers far less than GBO

GBO's Financial Status lists ~28 products; BOX FE's lists **11**. The gap is not cosmetic:

| Relationship | Products |
|---|---|
| **Same code both sides** `[confirmed]` | Cap&Floor `CF` · LoanDeposit/Depo `MM` · Swap `IR` |
| **Corresponds, different code** `[inferred]` | GBO CFM `IF` → BOX CFM `CFM` · GBO FRAS `FR` → BOX FRA `FRA` · GBO Credit Derivatives `CD` → BOX CDS `CDS` · GBO CS (Currency Swap) `SW` → BOX CCS (Cross Currency Swap) `CCS` |
| **Many GBO → one BOX** `[inferred]` | GBO `SP`+`NDS`+`FP`+`FM` (4 FX products) → BOX `FX` · GBO `OB`+`OE`+`OF`+`OI`+`OS` (5 OTC sub-products) → BOX `OTC` |
| **BOX-only, no GBO counterpart** | BRS (Bond Return Swap) · CES (**= Commodity Swap**, identified 2026-09-16) |
| **GBO-only, no BOX counterpart** | EQFW · EQLE · EQRP · EQSP · ES · ETD · FIFW · FISP · Futures · Lending · Repo · SCF |

Everything in the middle three rows is `[inferred]` from code and product-name similarity — **no query
has confirmed that a GBO product's rows actually land in the BOX product suggested here.** The
consolidations especially (4 FX → 1, 5 OTC → 1) are structural claims that should be verified against
data before anything depends on them.

**Why the last row matters for branch onboarding.** A branch trading a GBO-only product has no BOX FE
Financial Status home for it at all. That is a scope constraint on `PRODUCT_BOOK_SCOPE` — the blocking
input to `sigom-box-fe-configs-agent` — not a configuration gap to be closed by mining harder. See
[`../examples/ny-sch-branch-onboarding.md`](../examples/ny-sch-branch-onboarding.md).

> **Sharpened 2026-09-16.** `[stated: BOX Developer via Edouard]` A branch is onboarded with **all, or
> an SME-chosen subset of, the instruments already created and live in BOX** — the branch's GBO
> instrument configuration is not what decides this. So the "GBO-only, no BOX counterpart" row above
> isn't a gap to close, it's out of scope by construction, and the **BOX FE Processed Instruments
> catalogue below is the menu** `PRODUCT_BOOK_SCOPE` is chosen from. (This concerns instrument scope
> only — the MIS configuration and Fixing Curve are still mined from GBO.)
>
> **↳ Corrected 2026-09-17 — the catalogue is the menu, not the branch's selection.**
> `[confirmed: DB via Edouard, 2026-09-17]` The sentence above is right that the catalogue below is
> where instruments are *chosen from*, and wrong if read as the place to look up what a branch *has*.
> Those are two tables:
>
> | Question | Table |
> |---|---|
> | What does **this branch** have? — **the selection** | `BOX_FE.T_BOX_ENGACCRCONF_S`, the MIS configuration's **Accrual tab**. One row per instrument |
> | What is each one **called**? — the label | `PGT_SYS.T_PGT_SUB_PRODUCT_S` — what `FK_INSTRUMENT` points at `[confirmed: DB, 2026-09-18]` |
> | What does BOX **process** at all? — a different catalogue | `T_BOX_ENGINSTRUMENTS_S`, below. Global, 18 rows, no branch dimension, **and a different key space** |
>
> **↳ Corrected again 2026-09-18.** An earlier version of this block called the Processed Instruments
> catalogue below "the menu `PRODUCT_BOOK_SCOPE` is chosen from," and a query was written joining the
> Accrual tab to it. That join is wrong: `T_BOX_ENGACCRCONF_S.FK_INSTRUMENT` resolves to
> **`T_PGT_SUB_PRODUCT_S.PK`** — observed SLB values `20111.4`, `20.4`, `2.4` — while Processed
> Instruments PKs are `1.65`, `2.65`, `3.65`. Different spaces. The catalogue below remains a real and
> useful object; it is not the lookup for the Accrual tab. See Q-05c in
> [`queries/fe-config-mining.md`](queries/fe-config-mining.md), including the two SLB instruments an
> inner join silently dropped.
>
> Observed directly for **SLB in Tier 1**: nine Accrual rows — OTC Option, Cross Currency Swap, Swap,
> Cash Flow Matching, Deposit & Loan, Credit Derivatives, Forward Rate Agreement, Caps And Floors,
> Bond Return Swap. So a branch's instrument set is a **query**, not an assumption, and gate 0c can be
> put to an SME as a concrete enumeration rather than a phrase. See
> [`sigom-box-fe-configs-agent/AGENT.md`](../../agents/sigom-box-fe-configs-agent/AGENT.md), *Reading a
> branch's instrument set*.

**`CES` is Commodity Swap** `[confirmed: DB via team page, 2026-09-16]` — from the Processed
Instruments catalogue below, and independently from the runbook's PL/SQL examples naming
`T_BOX_CESFINANCST_S` and `V_BOX_ENGCESDATAMIS_S` alongside the MM and IR equivalents. Note GBO's
Financial Status has no Commodity Swap product, yet `fe-raw-data-stage.md` observes Commodity Swap rows
in Tier 1 RAW Deal data and in Days Matured config — so the product exists on both sides but only BOX
gives it a Financial Status surface. `BRS` remains BOX-only in the ordinary sense (new development).

**BOX-only products are the reverse case:** BRS and CES exist in BOX with no GBO source to mine,
structurally the same situation as `T_BOX_CONF_BY_BOOK_S` in the config surface — new BOX
functionality, not a missing mapping. (BRS = Bond Return Swap, a current AUKI development workstream.)

### BOX FE Processed Instruments catalogue

`[confirmed: DB via team page, 2026-09-16]` — `BOX_FE.T_BOX_ENGINSTRUMENTS_S`, read off the
`Static IT Data \ Processed Instruments` screen in BOX-DEV. **This is the instrument catalogue, and it
is broader than the Financial Status product set above.**

| Instrument | Code | Financial Status folder? |
|---|---|---|
| Caps And Floors | `CF` | ✅ C&F |
| Cash Flow Matching | `CFM` | ✅ CFM |
| Commodity Swap | `CES` | ✅ CES |
| Credit Derivatives | `CD` | ✅ as CDS — **code differs**, see below |
| Cross Currency Swap | `CCS` | ✅ CCS |
| Customized | `CU` | ❌ |
| Deposit & Loan | `MM` | ✅ Depo |
| Equity Spot | `EQP` | ❌ |
| Equity Swap | `EQS` | ❌ |
| FX Deliverable Forward | `FWD` | ⚠️ folded into the single `FX` folder |
| FX Deliverable Spot | `SPT` | ⚠️ folded into the single `FX` folder |
| Fixed Income Repo | `FIR` | ❌ |
| Fixed Income Spot (Bonds) | `BON` | ❌ |
| Forward Rate Agreement | `FRA` | ✅ FRA |
| Interest Bearing | `INT` | ❌ |
| Margin Call | `MRG` | ❌ |
| OTC Option | `OTC` | ✅ OTC |
| Swap | `IR` | ✅ Swap |

**This refines the "BOX covers 11 products vs GBO's ~28" framing above.** BOX FE *recognises* at least
18 instruments; only 11 have Financial Status screens. So "no BOX counterpart" in the product-set table
means **no Financial Status surface**, not "BOX has never heard of it" — Equity Spot, Equity Swap and
Fixed Income Repo all appear here while being listed as GBO-only above. For NY_SCH's product scope that
is a meaningful softening: a product in this catalogue but without a Financial Status screen is a
different (and probably smaller) problem than one absent entirely. Which of the two matters for a given
product is unestablished. `[open-question]`

Three other things to note:

- **`CD` here vs `CDS` in Financial Status.** The catalogue calls it "Credit Derivatives / `CD`" — which
  matches *GBO's* code — while the Financial Status folder is `CDS` with table `T_BOX_CDSFINANCST_S`.
  So the instrument code and the Financial Status product code are not guaranteed to agree; look both
  up rather than deriving one from the other.
- **FX is split here, merged there.** `FWD` and `SPT` are distinct instruments with one shared `FX`
  Financial Status folder — a more precise statement of the consolidation noted above.
- **PK ranges differ sharply.** Deposit & Loan is `1.65`, Swap `2.65`, Commodity Swap `3.65`; everything
  else sits in the 18-million range. Consistent with a few founding instruments getting hand-assigned
  low PKs and later ones being generated — relevant to the PK-mechanism question, which
  [`queries/fe-config-mining.md`](queries/fe-config-mining.md) Q-G3 now asks per table. `[inferred]`

### ⚠️ Unresolved discrepancy with this document's own Production Tables list

The *Financial Engine Tables → Production Tables* table above lists **`T_BOX_IRDATADEAL_S`** ("IRS-specific
deal data") and **`T_BOX_MMDATADEAL_S`** ("Money Market deal data") — i.e. *per-product* BOX Deal Data
tables, which the shared-`T_BOX_DATADEAL_S` finding appears to contradict.

Both can be true: those tables may exist as internal/legacy processing objects while the Financial Status
*screens* all read the shared table. Or the rows may be stale. Note also that neither matches GBO's
`DATAMIS` naming, so they are not simply mirrored GBO entries.

**Not reconciled here on purpose** — resolving it needs a real query (`ALL_TABLES` for
`BOX_FE.T_BOX_%DATADEAL%`, plus row counts), not a judgment call between two documents. Until then,
treat the shared `T_BOX_DATADEAL_S` as the confirmed Financial Status surface and these two rows as
unexplained. `[open-question]`

---

## Financial Engine Configuration Tables

| Table | Purpose |
|-------|---------|
| T_BOX_ENGCONF_S | Financial engine configuration |
| T_BOX_ENGACCRCONF_S | Accrual configuration |
| T_BOX_ENGDAYS_MATURED_S (CST_OBJ_BOX_DAY_MATURED) | Days to maturity tracking |
| T_BOX_ENGDOM_S | Domain/codes configuration — backs **several** SIGOM `Static IT Data` codes screens (e.g. Deal Status types), not one screen each. GBO twin `DEVENG.T_PGT_ENGDOM_S` `[confirmed: DB via BOX FE Developer, 2026-09-15]`. **Not** the same table as the shared `PGT_SYS.PGT_DOMAINS` — this one is module-owned, one copy per side |
| T_BOX_ENGFCURVE_S | Forward curve configuration |
| T_BOX_ENGFIXDISC_S | Fixing discount configuration |
| T_BOX_ENGFPRICE_S | Forward price configuration |
| T_BOX_ENGHISTMDATA_S | Historic market data |
| T_BOX_ENGINSTRUMENTS_S | Instrument configuration — SIGOM `Static IT Data > Processed Instruments`. GBO twin `DEVENG.T_PGT_ENGINSTRUMENTS_S` `[confirmed: DB via BOX FE Developer, 2026-09-15]`. Possible relationship to the `V_BOX_PROC_INSTR_S` view used by Fixing Exceptions is `[open-question]` — see `sigom-reference.md` |
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
| T_PGT_FOLDER_S (`PGT_STC`) | Folder master — **branch-keyed**; SIGOM `GBO > Static Data > Environment > Config > Folders`. See the dedicated section below | PK, CODE, FK_BRANCH (→ `T_PGT_BRANCH_S.PK`), FK_COVERAGETYPE / FK_COVERAGELIST (→ `PGT_SYS.PGT_DOMAINS.PK`), COVERAGEIND, COSTCENTER, STATUS |
| T_PGT_INSTRUMENT_S (CST_OWN_INSTRUMENT) | Instrument master | FK_INSTRUMENT, num_fk_instrument |
| T_PGT_FAMILY_S (`PGT_SYS`) | Product family — top of the three-level classification | PK |
| T_PGT_PRODUCT_S (`PGT_SYS`) | Product — middle level | PK, FK_PARENT (→ `T_PGT_FAMILY_S.PK`) |
| T_PGT_SUB_PRODUCT_S (`PGT_SYS`) | Sub-product — bottom level | PK, FK_PARENT (→ `T_PGT_PRODUCT_S.PK`) |
| T_PGT_QUOTE_REFERENCE_S (`PGT_MRK`) | Quote reference — the array of quotes a fixing curve linkage row points at. **A tuple of (currency pair, quote source, quote type)**, not an opaque id — see [confirmed-joins](confirmed-joins.md) | PK, FK_QUOTEINSTRUMENT (→ `PGT_STC.T_PGT_CURR_PAIR_S.PK`, **new 2026-09-18**), FK_QUOTESOURCE (→ `T_PGT_QUOTE_SOURCE_S.PK`), FK_QUOTETYPE (→ `PGT_SYS.PGT_DOMAINS.PK`), FK_QUOTEDIRECTION / FK_MATURITY / FK_PARENT (targets `[open-question]`) |
| T_PGT_QUOTE_SOURCE_S (`PGT_MRK`) | Quote source master (the market-data feed) | PK |
| PGT_DOMAINS (`PGT_SYS`) | Generic domain/enumeration values — **four unrelated uses now observed** (see below), confirming it is a general-purpose lookup, not specific to any one of them | PK |
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

## `PGT_SYS.PGT_DOMAINS` — four confirmed uses

Each use was found independently, in unrelated parts of the system, and each resolves through
`FK_<something> → PGT_DOMAINS.PK`:

| # | Consumer | Column | What the domain row holds | Confirmed |
|---|---|---|---|---|
| 1 | `PGT_MRK.T_PGT_QUOTE_REFERENCE_S` | `FK_QUOTETYPE` | Quote type | 2026-09-10 |
| 2 | `BOX_FE.T_BOX_CONF_BY_BOOK_S` | `FK_LABEL` | Book code + description (e.g. `XLB01 - HPE FIXED INCOME SLB`) | 2026-09-11 |
| 3 | `PGT_STC.T_PGT_FOLDER_S` | `FK_COVERAGETYPE` | Folder coverage type | 2026-09-15 |
| 4 | `PGT_STC.T_PGT_FOLDER_S` | `FK_COVERAGELIST` | Folder coverage list | 2026-09-15 |

Uses 3 and 4 sit on the **same row** of the same table (the Folders query joins `PGT_DOMAINS` twice,
aliased), which is the strongest single demonstration that this is a general-purpose enumeration table
keyed only by PK, with no intrinsic meaning of its own.

Four unrelated consumers across three different schemas (`PGT_MRK`, `BOX_FE`, `PGT_STC`) also
reinforces that `PGT_DOMAINS` is **shared between BOX and GBO** rather than module-owned — the same
conclusion the Schema Overview records for `PGT_MRK`. Practical consequence for mining: a `PGT_DOMAINS`
row read from either side is the same row; there is no "BOX version" to look for. Still not proven to
back *every* enumeration in `PGT_SYS`, only these four. `[open-question]`

Do not confuse it with `T_BOX_ENGDOM_S` / `T_PGT_ENGDOM_S`, which are module-owned FE codes tables —
see the Financial Engine Configuration Tables above.

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

**Confirmed real consumers.** `T_BOX_CONF_BY_BOOK_S.FK_INSTRUMENT` (the Book batch-execution table,
above) references `T_PGT_SUB_PRODUCT_S.PK` directly `[confirmed: DB, 2026-09-11]`, and so does
**`T_BOX_ENGACCRCONF_S.FK_INSTRUMENT`** (the Accrual tab) `[confirmed: DB, 2026-09-18]`. Two of the
walk's fourteen steps key off the **Sub-Product** level of this hierarchy specifically, rather than any
generic "instrument" table.

> The warning that used to end this paragraph — *"an 'instrument' FK is not self-evidently pointing at
> the same table every time"* — was written on 2026-09-11 and then **not heeded on 2026-09-17**, when
> Q-05c was written joining the Accrual tab's `FK_INSTRUMENT` to `T_BOX_ENGINSTRUMENTS_S` instead. The
> confirmed answer was in this paragraph the whole time. Before assuming an instrument join anywhere in
> the walk, check here first.

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
| FK_OWNER_OBJ | Owner object table | **The owning SIGOM module** — a per-table constant, not row data. `35000126.65` on BOX FE tables, `12198.4` on GBO FE tables `[confirmed: DB, 2026-09-18]`. Never copied across a GBO→BOX INSERT |
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
| FK_EXTENSION | Extension table | **The table/screen within the owning module** — also a per-table constant. Tier 1 BOX FE: `35001114.65` Accrual, `35001566.65` branch bridge. Read from the destination (Q-G6), never mined |
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
