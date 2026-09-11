# BOX — Branch Trading-Readiness Chain

A branch is trading-ready only when a selected product can traverse the complete operational chain:

```text
source/Murex trade → BOX_TRD deal → effective instrument type → BOX_FE financial status
→ BOX_ACC document/movement → account key → portfolio property → topic → GLTA → Historic Standard
```

A GBO branch record alone does not prove any downstream stage. This page is the branch-side readiness
contract for the `branch-trd-agent` and `branch-onboarding-orchestrator`.

## 1. Product coverage is not branch-wide `[confirmed: product readiness matrix]`

The Tier 1 12-product catalogue comparison proves that Madrid and London do not share a uniform
GBO/TRD/FE/ACC footprint: CF, CES, CFM and OTC have meaningful branch differences across eligibility,
trade population, FE Books/runtime and ACC configuration. Their rows are product-specific reference
evidence, not a branch-wide NY template.

The Tier 1 `NY_SCH` zero rows are **not a target readiness conclusion**: Tier 1 contains NY static GBO
identity but NY operational configuration/live GBO trades/accounting are Tier 2-owned. The BOX Lead
confirms NY is live in GBO Tier 2, not BOX. Tier 2 must be queried before the workflow proposes any NY
GBO/FE/ACC change. The business/FO SME must still select the target NY BOX product scope explicitly; existing
Madrid/London coverage must never preselect "all products."

### Detailed baseline use rule `[confirmed: DB extracts]`

Detailed Madrid/London extracts now cover GBO branch/instrument/product rows, FE Book labels, accrual
defaults/exceptions, curve/fixing coverage, ACC branch-PK rows and local-group portfolio/topic→GL rows.
They prove the **available structural options** but not a transferable NY value: Madrid and London have
different BO/MIS config, Book label populations, FE curve IDs, accrual-exception sets and accounting
GL/property values. The workflow presents these rows/counts as per-product reference evidence to the
relevant SME; it never auto-selects or copies them into `NY_SCH`.

### GBO and BOX Financial Engine configurations are distinct `[confirmed: Tier 1]`

```text
PGT_STC.T_PGT_BRANCH_CONFIG_S.FK_MISCONFIG → DEVENG.T_PGT_ENGCONF_S   (GBO MIS)
PGT_STC.T_PGT_BRANCH_S.PK → BOX_FE.T_BOX_ENGCONF_X → BOX_FE.T_BOX_ENGCONF_S   (BOX FE MIS)
```

Both headers carry description, currency, calendar, manual/accounting fixing curves and front/back
sources, but use distinct PKs and source/curve values. `NY_SCH.FK_MISCONFIG = 2.22` does not resolve in
Tier 1 and must be inspected in Tier 2; that absence is not a missing-NY conclusion.

### Fixing curves are quote-reference arrays `[confirmed: Tier 1]`

```text
DEVENG.T_PGT_ENGCONF_S → DEVENG.T_PGT_ENGFCURVE_S → DEVENG.T_PGT_ENGLKFC_X
BOX_FE.T_BOX_ENGCONF_S → BOX_FE.T_BOX_ENGFCURVE_S → BOX_FE.T_BOX_ENGLKFC_X
```

The Madrid/SLB curves contain quote-reference links (e.g. EUR/USD spot with `ACCOUNTING RATES` in both
Tier 1 arrays). Tier 2 NY GBO curve/header/quote references must be compared with the required BOX FE
configuration before any curve value is proposed.

### Online translation boundary `[confirmed: Tier 1 schema]`

`BOX_SYS.T_BOX_CROSS_REF_S` maps `MAP_TYPE`, `MAP_FROM` and optional `FK_INSTRUMENT_FILTER` to `MAP_TO`
/ `MAP_TO_TYPE` for source, instrument and direction values. It has no branch/entity column. It supports
online value translation but does not establish NY branch routing; no accessible Oracle dependency names
it, so the online consumer remains an external Java/adapter/workflow evidence gap.

## 2. BOX_TRD readiness `[confirmed: DB schema + population]`

The core branch/product fields in `BOX_TRD.T_BOX_DEAL_S` are `FK_BRANCH`, `FK_INSTRUMENT`,
`FK_INSTRUMENT_TYPE`, `FK_PORTFOLIO_PROPERTIES`, `ACCOUNTING_REF` and `FK_ACCOUNTING_DOC`. The trade
chain continues through `T_BOX_CONTRACT_S`, `T_BOX_LEG_S`, cash-flow/fixing tables, daily attributes and
`PKG_BOX_DEAL_LITE_DATA_API`.

### Effective instrument type is conditional

Madrid/London baseline data proves a configured instrument-type row is **not universally required**:
active MM, CCS, FRA and OTC populations have no branch/instrument rows in
`BOX_ACC.T_BOX_CONF_INSTRUM_TYPE_S`; their effective instrument type may follow product fallback logic.
IR, Madrid CFM and Madrid CES have configuration rows, but several observed deal instrument types coexist
for a product and the priority/value/counterparty match remains product-specific. The workflow must never
create an instrument-type row simply because a product is selected; it asks the BOX_TRD/ACC SME to prove
whether configuration or fallback applies.

`[open-question]` `../box-data-model.md`'s "Product classification hierarchy" section documents a
confirmed three-level `PGT_SYS` classification (`T_PGT_FAMILY_S` → `T_PGT_PRODUCT_S` →
`T_PGT_SUB_PRODUCT_S`, chained by `FK_PARENT`) that is a plausible mechanism for the "product
fallback logic" referenced above — a product with no `T_BOX_CONF_INSTRUM_TYPE_S` row could be
falling back to a Family- or Product-level default. Not yet DB-witnessed as the actual fallback
path; flagged here as the natural next place to look.

### Online arrival remains open

The DB data model is evidenced, but the online source transformation remains `open-question`:

```text
Murex → P37/adapter → Camunda → Kafka → Trade Processor → BOX_TRD
```

A target branch requires evidence of the source/BO-code/branch/instrument mapping that persists a deal in
`T_BOX_DEAL_S`; absent online repositories/configuration are a blocking integration evidence gap.

## 3. BOX_FE readiness `[confirmed: schema + configuration]`

Financial-status tables expose `DDATE`, `DEAL_ID`, `FK_BRANCH` and, where product-specific,
`FK_INSTRUMENT`. The branch must have an evidenced FE configuration (`T_BOX_ENGCONF_X` →
`T_BOX_ENGCONF_S`), branch/instrument/Book-label routing (`T_BOX_CONF_BY_BOOK_S`), applicable
accrual/curve configuration and runtime process/queue evidence. A configuration must be assessed at
branch × product × Book/label grain, not copied once per branch.

The aggregated FE baseline confirms real Madrid/London output for CCS, IR, MM, FRA, CFM, CES and OTC
in their product-specific `T_BOX_<PRODUCT>FINANCST_S` tables. CES is Madrid-only in this extract; CFM
London has only three deals/six rows dated 11-FEB-26, unlike the current 27-AUG-26 populations for the
other common products. `NY_SCH` has no returned financial-status row for any measured product. This
creates a post-configuration validation requirement: target branch/product trades must generate the
corresponding FINANCST records before the branch is considered FE-ready.

## 4. BOX_ACC execution provenance `[confirmed: 27-AUG-26 witness]`

For every returned Madrid/London product in the direct daily witness, **all movement rows** joined both:

```text
T_BOX_ACCT_MOV_S.FK_PARENT    → T_BOX_ACCT_DOC_S.PK
T_BOX_ACCT_MOV_S.FK_ACCT_KEY → T_BOX_ACCT_KEY_S.PK
```

The observed movement chain carries `FK_BRANCH`, `FK_INSTRUMENT`, `FK_PROPERTIES`, `FK_TOPIC`,
`FK_GLTA`, `FK_HISTSTDACCT` and the account-key dimensions. This confirms document/movement/account-key
provenance for the existing branches. It does not establish a target NY trade until post-build execution
exists.

## 5. Required branch workflow order

```text
GBO profile → explicit product scope → GBO activation configuration → BOX_TRD source arrival
→ BOX_FE approach/design → runtime/Data Lake/Control-M inputs → BOX_ACC impact → proposed change plan
```

The change plan must be per selected product and distinguish `PROPOSED` structural work from
`REQUIRES_SME_VALUE` (known object, value not evidenced) and `EVIDENCE_REQUIRED` (insufficient proof to
propose the object). Exact GBO, BOX_TRD, BOX_FE, BOX_ACC tables and Control-M repositories accompany
all plan rows.

**Sources:** `NY_SCH_PRODUCT_READINESS_MATRIX.csv`, `NY_SCH_TRD_INSTRUMENT_TYPE_SUMMARY.csv`,
`NY_SCH_ACC_DOCUMENT_MOVEMENT_PROVENANCE.csv`, `NY_SCH_FE_ACC_EXECUTION_COLUMNS.csv` under the curated
confidential raw branch-onboarding extract batch; committed BOX_TRD/BOX_FE/BOX_ACC sources; cited pages.
