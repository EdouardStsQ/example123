# BOX_ACC — Add-Product Checklist & IRS Implementation Footprint

> **⚠ Partially superseded (2026-07-23).** The BOX team's **universal engine** now onboards a
> product's accounting **config-only, with zero new PL/SQL per product** — see
> `box-acc-universal-engine` and the `box-accounting-matrix-contract`. The `software_plsql` /
> `new_code` (per-product `PKG_<P>ACCT`) parts of this page are **obsolete**: prefer the universal
> `PKG_ACCTGENERIC` configured from the Accounting Matrix. The **SIGOM / config surfaces** below
> (Net Contract, Cross Account Config, Local/Portfolio Properties, Topics, Events, Instrument Type,
> grants, FE deps) remain relevant as the objects the matrix ultimately configures.

How a **new product's accounting** is onboarded into BOX_ACC (Stage 4), reverse-engineered from the
**IRS** implementation in `cib-boxacc-dbboxacc` and mapped to the BOX "Add Product" guide (Section 3,
BOX Accounting Engine). This is the reusable *what-must-exist* checklist; the concrete IRS artifacts
below are the exemplars a new product (CCS, BRS, …) is patterned on.

> **Config-first (BOX team rule):** BOX_ACC must **not gain new code unless strictly needed**. A new
> product is onboarded primarily by **configuration** + **reuse of the generic engine**
> (`PKG_ACCTGENERIC.p_get_mov`, which generalised the per-product `PKG_IRSACCT` logic at r0.0.36). A
> dedicated `PKG_<P>ACCT` is the **exception**, only when the generic engine cannot express the
> product's movements. `status: inferred` — structural, repo-verified; confirm framing with the BOX team.

## 1. The Add-Product checklist (Section 3)

| # | Area | BOX_ACC object(s) | Config source (legacy) |
|---|------|--------------------|--------------------------|
| 3.1 | **Net Contract** — which trades net together | `T_BOX_NETCONTRACT_S` (+ `obj_box-netcontract`, `wf_netcontract`) | GBO Madrid\Trading\Neto Contrato Partenon |
| 3.2 | **Config for Revaluation Accounts** | `T_BOX_CROSS_ACCTCONF_S` (+ `obj_box-crossaccountconfig`) — 3 account types: *Posición Vencida* (matured), *Posición Viva* (live), *Balance de Posición Viva* | GBO Madrid\Account\Revaluation Accounts |
| 3.3 | **Software PL/SQL** | reuse `PKG_ACCTGENERIC.p_get_mov`; per-product `PKG_<P>ACCT` only if needed; product-code map in `PKG_BATCHPROCESS_MBJ`; topic constants in `PKG_ACCTCONST` | — (code) |
| 3.4 | **Config Local Properties** | `T_BOX_CONF_LO_PROP_S` (+ `obj_box-configlocproperty`, `obj_box-condportfolio`) | GBO\SYS\Accounting\Config Local Properties |
| 3.5 | **Portfolio Properties** — topic → GL account | resolved at runtime by `Pkg_AcctGeneral.f_GetAcctNo(branch, properties, topic)`; stored in `T_BOX_ACCT_PORT_PROP_S` / `T_BOX_ACCT_GLTA_S` | GBO\Accounting\General\Portfolio Properties |

Plus: **product-code plumbing** (`PKG_BATCHPROCESS_MBJ`, `PKG_ACCTGENERAL.P_CREATEDOC` doc-type
support), **accounting events** (§4), **instrument type** (`T_BOX_CONF_INSTRUM_TYPE_S`), and the
**Sigom/GOM screen objects** (§5). The Sigom objects are *screen/metadata definitions* — the actual
account data is entered by users / migrated from GBO, not committed as repo data.

## 1.0 Label Config status

`[confirmed: SIGOM UI trace + DB]` `PGT_SYS.PGT_DOMAINS` is the physical table behind the Label Config
screen and directly owns active FE Label PKs. The 27-AUG-26 join proves active `FK_LABEL` values from
`T_BOX_CONF_BY_BOOK_S`, `T_BOX_DATADEAL_S` and `T_BOX_MTM_DATA_S` equal `PGT_DOMAINS.PK`, which supplies
the label code and description. Examples include `1006.21 → XES54 / OPCIONES_FX_LATAM`,
`3743.21 → XLB08 / SLB RATES VOL` and `3744.21 → XLB07 / SLB Rates`. `T_BOX_CONF_BY_BOOK_S` has a unique
constraint containing `FK_LABEL`, confirming label is part of the Book configuration key. The
cross-environment PK consistency rule remains open until the same labels are compared in another tier.

## 1.1 Confirmed Tier 1 configuration profile

`[confirmed: DB]` `T_BOX_CROSS_ACCTCONF_S` is branch × instrument configuration: the supplied
population has rows for Madrid and London across MM, CCS, IRS, OTC Option, Cap/Floor, FRA, CFM and
Commodity Swap. Counts differ sharply by branch/product, so revaluation-account treatment must never
be copied as a branch-wide default.

`[confirmed: DB]` `T_BOX_NETCONTRACT_S` is branch × instrument configuration in the supplied
population. It has Madrid rows for all observed products, including FRA, but no London rows in the
full grouped extract. Its exact past-due netting runtime role and branch applicability remain open.

## 2. Product identity & constants (IRS exemplar)

| Item | IRS value | Source |
|------|-----------|--------|
| Instrument PK | `20092.4` | BOX_FE `PKG_ENGGN` |
| Instrument type PK | `10146.4` | BOX_FE |
| Product code (2-char) | `'IR'` | mapped in `PKG_BATCHPROCESS_MBJ` |
| Number of legs | 2 (Asset + Liability) | product spec |
| Sigom instrument label | `SWAP` | naming convention |
| DocName prefix / DocDescr | `IRSBOX…` / `Interest Rate Swap BOX` | naming convention |

## 3. Software PL/SQL — `PKG_IRSACCT` procedures (exemplar)

| Procedure | Purpose |
|-----------|---------|
| `p_GetAcctNetSwapValues` | Nets AssetGain vs LiabLoss (and vice versa); returns net side + transferred amount |
| `p_GetPYGSwapAccount` | Maps P&L topics (ASSETGAIN/ASSETLOSS/LIABGAIN/LIABLOSS) → GL accounts via `f_GetAcctNo` |
| `p_GetNominalSWAPAccount` | Maps the 4 nominal/off-balance topics (both legs) → GL accounts |
| `p_GetSwapAdjustNominalNew` | Nominal adjustment: `Adjust = |MIS_Nominal| - |Accounting_Balance|`; FX handling |

Generalised at r0.0.36 into `PKG_ACCTGENERIC.p_get_mov` (same 6-step nominal-adjust algorithm).

## 4. Accounting events (DML in `PGT_PRC`) — the bulk of the work

IRS required 20+ events in `T_PGT_EVE_S`, added across r0.0.9-r0.0.30. Each event = source tables +
aliases, output columns, filter conditions (e.g. `FK_STATUS = 96.4` VBO), procedure calls, update
statements, and group membership.

| Event PK | Name | First version |
|----------|------|----------------|
| 3658.65 | BOX Swap Contratacion - Tomado y Prestado (initial booking) | r0.0.9 |
| 3608.65 | BOX SWAP Nominal Adjust (daily) | r0.0.9 |
| 3609.65 | BOX SWAP Interest Adjust Local Anti Natura | r0.0.9 |
| 3611.65 | BOX Swap Premium - Rec Local | r0.0.9 |
| 3614.65 | BOX Swap Premium - Pay Local | r0.0.9 |
| 3616.65 | BOX SWAP Premium Cancelations Local | r0.0.9 |
| 3617.65 | BOX Swap Interest - DeadPosition | r0.0.9 |
| 3619.65 | BOX SWAP Event Revaluation Balance | r0.0.12 |
| 3620.65 | BOX SWAP Event Revaluation - Patrimonial Position | r0.0.12 |
| 3621.65 | BOX SWAP Event Netting Dead Position | r0.0.12 |
| 3677.65 | BOX NEW SWAP Mark to Market | r0.0.10 |
| 3678.65 | BOX NEW SWAP Mark to Market -Criterial MtM- | r0.0.10 |
| 3817.65 | BOX SWAP Camara Mark to Market (clearing house) | r0.0.11 |
| 4157.65 | BOX SWAP Load camara MTM table from GBO file | r0.0.17 |
| 4217.65 | STM Instrument Type Update | r0.0.17 |
| 4280.65 | BOX SWAP Premium Cancelations Local NDC | r0.0.16 |
| 4297.65 | BOX SWAP Neteo Ctas PyG Valoracion (P&L netting) | r0.0.17 |
| 4298.65 | BOX SWAP Reclasificacion Saldos ContraNatura MTM | r0.0.17 |
| 4397.65 | BOX SWAP Load camara MTM (Swap-Agent) | r0.0.20 |
| 4619.65 | BOX SWAP Premium Cancelations Reclasification - NDC | r0.0.26 |
| 4960.65 | BOX SWAP - Annual shutting, P&L accounts (year-end) | r0.0.28 |

**Event groups** (`T_PGT_BR_EVE_S`): `2735.65` (Accounting General Local wFE No Reval-BM),
`2755.65` (Mark to Market CorteH Reval), `3055.65` (Load Clearing House Data).

## 5. Sigom / GOM configuration objects

| Sigom object | Table | Purpose |
|--------------|-------|---------|
| BOX - Net Contract | `T_BOX_NETCONTRACT_S` | contract netting rules |
| BOX - Cross Account Config | `T_BOX_CROSS_ACCTCONF_S` | revaluation account mapping |
| BOX - Config Local Properties | `T_BOX_CONF_LO_PROP_S` | local property config |
| BOX - Condition Port Properties | `T_BOX_CONDPAR_PROP_S` | condition parameters |
| BOX - Acct Topics | `T_BOX_ACCT_TOPICS_S` | topic definitions |
| BOX - MBJ Properties | `T_BOX_MBJ_PROPERTIES_S` | batch job config |
| BOX - Portfolio Properties | via `f_GetAcctNo` | topic → account mapping |

## 6. BOX_FE dependencies (Stage 3 → Stage 4)

| Dependency | What BOX_ACC needs |
|------------|---------------------|
| `T_BOX_IRDATADEAL_S` | IRS deal data (event source table) |
| `V_BOX_CAMIRFINAN_S` | MIS financial-status view (nominal adjustment) |
| Instrument PK `20092.4` | all IRS filtering |
| Instrument type `10146.4` | `T_BOX_CONF_INSTRUM_TYPE_S` |
| MIS nominal values | `p_GetSwapAdjustNominalNew` |
| DEVENG schema | FE MIS tables via dynamic SQL |

## 7. Reusable identifiers (fidelity — keep the concrete lists)

### 7.1 Topic constants (`PKG_ACCTCONST`, `.65` PKs)

| Constant | PK | Kind |
|----------|----|----|
| `TOPIC_ASSETNOCIONAL` | 179.65 | IRS nominal (balance sheet) |
| `TOPIC_ASSETCONTRCTASORDEN` | 180.65 | IRS off-balance (contra ctas orden) |
| `TOPIC_LIABNOCIONAL` | 181.65 | IRS nominal |
| `TOPIC_LIABCONTRCTASORDEN` | 182.65 | IRS off-balance |
| `CST_TOPIC_ASSETGAIN` | 196.65 | shared P&L |
| `CST_TOPIC_ASSETLOSS` | 197.65 | shared P&L |
| `CST_TOPIC_LIABGAIN` | 198.65 | shared P&L |
| `CST_TOPIC_LIABLOSS` | 199.65 | shared P&L |
| `TOPIC_ASSETACCRUAL` | 166.65 | shared accrual |
| `TOPIC_LIABACCRUAL` | 172.65 | shared accrual |
| `TOPIC_ASSETACCRUALNEG` | 194.65 | shared accrual (AntiNatura) |
| `TOPIC_LIABACCRUALPOS` | 195.65 | shared accrual (AntiNatura) |
| `CST_OWNER_PORTFOLIO` | 35000194.65 | Sigom object reference |
| `CST_EXT_PORTFOFIO` | 35001818.65 | Sigom extension reference |

### 7.2 Shared package dependencies & helpers

- **Shared packages:** `PKG_BOXACCGENERAL`, `PKG_ACCTUTILS`, `Pkg_AcctGeneral`, `Pkg_AcctConst`,
  `Pkg_Acct_Trg`, `PGT_PRG.Pkg_PGTGeneral`, `PKG_ENGGNSUPPORT`, `p_acctgeneral`.
- **Nominal-adjust helpers:** `f_GetAcctKey`, `p_Get_GLTA_Bal` (balance retrieval),
  (FX conversion), `f_TreatCurrencyAmount` (per-currency rounding). Variables: `MIS_CCY`, `MIS_Loc`,
  `Balance_CCY`, `Balance_Loc`.
- **DEVENG MIS naming:** `PKG_ENGGNSUPPORT.f_traduce_instmdr_shortname` → `DEVENG.T_PGT_<short>DATAMIS_S`.

### 7.3 BOX_FE MTM hook (Software PL/SQL step 3.3)

`PKG_FE_MTM_CALCULATION`: if the product has >1 leg → add to `p_Insert_Missing_Mtm_Data`; if 1 leg →
`p_Missing_Mtm_Dir_Agnostic`; and add family/group/type in `p_Import_Mtm_Data`.

### 7.4 Product-code mapping (in `PKG_BATCHPROCESS_MBJ`)

```sql
ELSIF po_trputmov.p_instrument = 20092.4  -- SWAP
  THEN po_trputmov.p_PROD := 'IR';
```

Postings invoked via `pkg_irsacct_body` procedures (or the generic engine).

### 7.5 Config-table columns

- **`T_BOX_NETCONTRACT_S`:** `FK_BRANCH`, `FK_INSTRUMENT`, `FK_CURRENCY`, `FK_FOLDER`, `FK_SECURITY`,
  `FK_SOURCE_DEAL`, `CONTRACT` (loaded from the `net_contract` GBO migration).
- **`T_BOX_CROSS_ACCTCONF_S`:** `FK_BRANCH`, `FK_CURRENCY`, `FK_INSTRUMENT`, `FK_ENTITY`, `FK_TOPIC`,
  `FK_ACCOUNT`, `ACC_TYPE`.

### 7.6 Event source/filter fields & DocName

Events read `T_BOX_IRDATADEAL_S` (alias NewDeal) filtered by `FK_LABEL = #LABEL#`,
`DDATE = '#EV_DATE#'`, `FK_STATUS = 96.4` (VBO), with `DEAL_ID`, `FK_ACCTDOC`, `FK_DIRECTION`.
`DocName = 'IRSBOX' || DEAL_ID || '_' || TradeDate_YYYYMMDD`.

### 7.7 Sigom workflows & typedef

`wf_netcontract_3500017865`, `wf_crossaccountconfig_3500014365`, `wf_configlocalproperties_3500015165`,
`wf_conditionportproperties_3500016065`; typedef `Type_InstrumentBOX` (value `20092.4`, label `SWAP`);
Sigom project on `.65` authcode; screens under `GOM_GLB_SYS`.

### 7.8 Infrastructure conventions

- **Grants:** `BOX_ACC_RD`, `BOX_ACC_WR`, `PGT_PRG`.
- **Tablespaces:** `BOX_ACC_DATA` (data), `BOX_ACC_IDX` (index).
- **Liquibase contexts:** ACC (code, `20_Packages` / `25_Grants`), PRC (events), `GOM_GLB_SYS` (Sigom).
- **PK / authcode:** `.65` for the BOX environment.

## 8. Applying to a new product — BRS

- **Reuse first (config).** Product-code (`PKG_BATCHPROCESS_MBJ`), Net Contract, Cross Account
  Config, Local/Portfolio Properties, Topics, and Events are **configuration** patterned on the IRS
  exemplars above — no new code by default.
- **Financing leg** → analogue to IRS interest legs (reuse `PKG_ACCTGENERIC` / IRS procedures).
- **Performance leg (net-new).** `inferred` — no migrated BOX product implements a bond
  price-return / total-return leg (IRS = interest-rate, CCS = cross-currency). BRS's performance leg
  (bond price return + coupon pass-through) has **no BOX analogue**; it is the **core build risk** and
  the one place a **justified `new_code`** item (or a generic-engine extension) may be needed. The
  Dr/Cr treatment must come from the accounting-SME spec + a named accounting-user sign-off — never
  invented, and never copied from the known-buggy Calypso behaviour.

**Sources:** `box-acc-irs-inputs`, `box-database-reference`, `box-accounting-exec-summary`
