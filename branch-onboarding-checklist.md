# BOX — New-Branch Onboarding Checklist

The governed **what-must-exist-or-be-checked** after a new branch/entity is created in **GBO** and
must be onboarded into BOX — the **backbone** the `branch-config-agent` works from. GBO owns branch
creation; BOX_FE adaptation is the agent's first downstream surface, followed by batch and BOX_ACC.
It is the **B-axis analogue** of the product-side [box-acc-add-product-checklist](acc-add-product-checklist.md) (F(P,B): product ×
bank/branch).

Structured to mirror the BOX team's own (self-described "high-level, not 100% sure") list. Every item
carries a **status** (`confirmed` = code/DB/SoR · `inferred` = structural · `open-question` = needs
SME/external) and an **automation class**:

- 🟢 **automate** — the agent can deterministically generate/propose it (by analogy to an existing branch).
- 🟡 **assist** — the agent proposes structure but a value is SME/SoR-owned.
- 🔴 **check/flag** — external system / human; the agent verifies presence and flags gaps, never invents.

> **Golden rule (unchanged):** propose + flag, SME-gated, never invent. GL-account values, platform PKs
> and external-system state are `open-question` by construction. The agent never commits config to BOX.

**Reference branches** (confirmed, from `T_PGT_BRANCH_S`, see [box-branch-config-surface](../../reference/branch-config/branch-config-surface.md) §6):
**Madrid** `22.21` (`MADRID`, entity `31434.4`, localgroup `269.4`) · **London/SLB** `20087.4`
(`LND BRANCH`, entity `31077.4`, localgroup `21462.4`). These are the two analogues to pattern a new
branch on.

## How this maps to the six agreed workstreams

This checklist is organised by **system layer** (infrastructure → TRD → ACC → FE). The NY_SCH scoping
meeting (`[stated: BOX Lead, 2026-09-10]`, recorded in
[ny-sch-branch-onboarding](../../examples/ny-sch-branch-onboarding.md) §1) decomposed the same project
by **work type**. Different axes, same project — this table is the join, so neither document has to be
rewritten into the other's shape:

| Workstream | Covered by layers here | Coverage |
|---|---|---|
| **W1** Software (instrument-type logics, local PP conditions) | 2.2, 3.2 partially | **Partial** — this checklist treats instrument type as *config*; W1 treats the local logic behind it as *code to migrate*. Both are true and they are different work |
| **W2** SIGOM configs (FE + ACC) | 3.3–3.5, 4.1–4.3 | **Full** — the best-covered workstream, and the only one with a built agent |
| **W3** Jobs (FE/ACC job-as-code + MBJ, Data Lake feeds) | 1.3, 3.6, 4.4 | **Full** for Control-M/Data-Lake; MBJ config appears only in the ACC agent's scope table |
| **W4** Reporting (adapt SLB reports to NY) | — | **None.** No layer, no item, no reference doc |
| **W5** GL integration (Equation, as SLB) | 3.1 (MIC) | **Partial** — MIC is named as the pre-ledger gateway; the Equation integration itself is not described |
| **W6** FDH integration | — | **None.** FDH is not mentioned anywhere in this repo |

Layers with no workstream: **1.1/1.2/1.4/1.5** (GBO branch creation, country, MDR replication) are
prerequisites the meeting treated as given rather than as workstreams, and **2.1/2.3** (BOX_TRD trade
arrival) sit on the unresolved online-scope question — see the checklist item 2.1 note below.

---

## Layer 1 — General / Infrastructure & static data

| # | Item | BOX object / system | Status | Class |
|---|------|----------------------|--------|-------|
| 1.1 | **GBO branch** — profile an existing branch or propose creation of a new one | GBO-owned `T_PGT_BRANCH_S` + `FK_LOCALGROUP` + attributes (`FK_ENTITY`, `FK_CURRENCY`, `FK_CALENDAR`); agent prepares the new-branch handoff but never writes it | `confirmed` | assist / gate |
| 1.2 | Identify **country** (from Data Lake) | `country_code_vr` (ES/LB/…) — drives the batch payload + feeds | `inferred` | 🔴 check |
| 1.3 | Review **Books**; for new Books generate config + **Control-M** to load BU (deal/flow/market) | [box-branch-batch-controlm](../../reference/job-chains/control-m-batch-layer.md) — 6 jobs/book (DD×4, FD, MD) | `confirmed` | 🟢 automate |
| 1.4 | Is **local static data** available in **MDR**? | MDR = reference/master-data golden source (`LSTMNTSOURCE = MDR-*`); currency/calendar/entity/counterparties | `inferred` | 🔴 check |
| 1.5 | **API selective replication MDR → Infrastructure** | replicate static data into the BOX platform (`T_PGT_*`/GOM) | `open-question` | 🔴 check |

## Layer 2 — BOX_TRD trade-arrival readiness

| # | Item | BOX object / system | Status | Class |
|---|------|----------------------|--------|-------|
| 2.1 | **Source trade arrival** — prove source/BO-code → target branch/instrument persistence | Murex/P37/adapter → Camunda → Kafka → Trade Processor → `BOX_TRD.T_BOX_DEAL_S` | `open-question` (online sources absent) — **for *testing*, this is no longer blocking**: a branch already live in GBO has its trades in the Data Lake and can feed RAW manually, with status and simulated-online-entry caveats (see note below) | check/flag |
| 2.2 | **Effective instrument type** — determine configured priority lookup versus product fallback | `BOX_TRD.PKG_BOX_DEAL_LITE_DATA_API` + `BOX_ACC.T_BOX_CONF_INSTRUM_TYPE_S` | `confirmed` (conditional baseline) | assist / SME gate |
| 2.3 | **TRD → FE handoff** — validate the selected product's branch/instrument/deal correlation | `BOX_TRD.T_BOX_DEAL_S` → product `BOX_FE.T_BOX_*FINANCST_S` | `confirmed` (schema) / `open-question` (NY execution) | validate post-build |

> **Note on 2.1 — testing does not require booking trades in Murex** `[stated: BOX Lead, 2026-09-10]`
>
> For a branch already live in GBO, its trades are already in the Data Lake tables and can be loaded
> into `T_BOX_RAW_{DEAL|FLOW|MARKET}_DATA_S` by hand for technical tests. This separates two things
> this row previously conflated: **online trade arrival as a production capability** (still
> `open-question`, still gated on whether CROSS_REF is in scope) and **getting test data into BOX**
> (solved). Two caveats carry real weight — the trade status will not be `BOValidated`, which the
> standard extraction job filters on ([box-branch-batch-controlm](../../reference/job-chains/control-m-batch-layer.md)
> §2 correction), and the online entry, which is what validates accounting attributes, has to be
> simulated. Whether that simulation is a test harness or evidence that the online path is genuinely in
> scope is **undecided and changes the size of the project** —
> [ny-sch-branch-onboarding](../../examples/ny-sch-branch-onboarding.md) §2.

## Layer 3 — BOX Accounting

| # | Item | BOX object / system | Status | Class |
|---|------|----------------------|--------|-------|
| 3.1 | New integration via **MIC** (no files to Equation/local GLs) | MIC pre-ledger gateway ([box-overview](../../reference/system-overview.md)); Equation = SLB local GL | `inferred` | 🔴 check |
| 3.2 | **Instrument type** (conditional) | `T_BOX_CONF_INSTRUM_TYPE_S` (carries `FK_BRANCH`); active product paths can instead use BOX_TRD calculated fallback | `confirmed` (conditional) | assist / SME gate |
| 3.3 | **PP conditions** (differ per **strategy**) | `T_BOX_CONDPAR_PROP_S` / `T_BOX_CONF_LO_PROP_S` + `FK_ACCT_STRATEGY` | `confirmed` | 🟡 assist (scope) |
| 3.4 | **Accounts** — create user (GL) accounts | `T_BOX_ACCT_GLTA_S` (`CODE`, `LOC_CODE`) | `confirmed` (object) / `open-question` (values) | ◆ values-flag |
| 3.5 | **Generate PP** (Portfolio Properties = product ↔ user-account link) | `T_BOX_ACCT_PORT_PROP_S` + `T_BOX_ACCT_LIST_TOPIC_S` (topic→GLTA) — see [box-branch-config-surface](../../reference/branch-config/branch-config-surface.md) | `confirmed` | ◆ scope / 🔴 values (see [box-branch-config-madrid-london-diff](../../reference/branch-config/branch-config-madrid-london-diff.md)) |
| 3.6 | **Control-M Accounting Batch** by instrument & book | `T_BOX_BRPROCCAL_S` / `_QUEUE_S_OPTZ` + `box-fe-acc-batch-runtime` | `confirmed` | 🟢 automate |

## Layer 4 — BOX FE

| # | Item | BOX object / system | Status | Class |
|---|------|----------------------|--------|-------|
| 4.1 | **Select/reuse or create the BOX_FE configuration** (eight SIGOM tabs) | `T_BOX_ENGCONF_S` Generic + `T_BOX_ENGCONF_X` Branch + Book/Accrual/curve/exception children; see [box-fe-branch-configuration](../../reference/branch-config/fe-branch-configuration.md) | `confirmed` (core) | assess / propose |
| 4.2 | **Branch association** (bind GBO branch to FE configuration) + **Book batch-execution registration** (per branch × instrument — no GBO analogue; confirmed 2026-09-11 that a missing row here means the batch never runs for that combination, not that it defaults) | `T_BOX_ENGCONF_X.FK_BS` + `T_BOX_CONF_BY_BOOK_S` | `confirmed` | Branch: propose. Book: **SME decision** — nothing to mine from GBO |
| 4.3 | **QR FX** — config FX quote rates per currency; if a QR is missing, request file from **Asset Control** | and load market-data tables (`T_BOX_FX_RATE_S`, `T_BOX_ENGFCURVE_S`, fixings/curves); Asset Control = external vendor | `inferred` | check/flag |
| 4.4 | Create **Control-M Financial Batch** by instrument & book (FE side) | `T_BOX_BRPROCCAL_S` + `box-fe-acc-batch-runtime` | `confirmed` | automate |

## Automation summary (what the agent produces vs flags)

| Target | Layer refs | Class | Produced from |
|---|---|---|---|
| **GBO creation handoff / existing-branch profile** | 1.1 | propose / read-check | new branch: proposed GBO package → `GBO-created` gate; existing branch: profile read-only |
| **BOX_TRD entity readiness** | 2.1–2.3 | check / validate | source arrival + effective instrument type/fallback + TRD→FE correlation, per selected product |
| **BOX_FE configuration association/aggregate** | 4.1, 4.2 | assess / propose | GBO branch profile → `T_BOX_ENGCONF_X` → analogous FE configuration; no cross-environment copying. **Exception:** Book (`T_BOX_CONF_BY_BOOK_S`, part of 4.2) has no GBO source at all — SME decision, existing BOX branches for shape only |
| **Data-Lake Control-M batch** (`diaria.json`, 6 jobs/book) | 1.3 | automate | (country, source-system, books) + analogue folder |
| **BOX_FE/ACC runtime batch** | 3.6, 4.4 | assist / check | analogue job families and completion events; wrapper→Oracle binding remains open |
| **Instrument-type config** | 2.2, 3.2 | assist / SME gate | product-specific priority lookup or calculated fallback; do not create blindly |
| **BOX_ACC config SCOPE** | 2.3, 2.5 | ◆ scope-automate | the `(instrument, topic)` matrix to cover — superset analogue (Madrid ⊇ London) |
| **BOX_ACC config VALUES** | 2.4, 2.5 | 🔴 values-flag | GL accounts + counterparty-sector property breakdown — **SME/GBO**: values-flag (accounts/properties don't transfer — see [box-branch-config-madrid-london-diff](../../reference/branch-config/branch-config-madrid-london-diff.md)) |
| **GBO branch master** | 1.1 | propose / read-check | GBO-owned: propose the new-branch package and wait for evidence; never write it |
| **Country / MDR replication / Asset Control FX / MIC** | 1.2, 1.4, 1.5, 3.1, 4.3 | check/flag | verify presence; flag gaps (external) |

> **Key data finding** ([box-branch-config-madrid-london-diff](../../reference/branch-config/branch-config-madrid-london-diff.md)): between Madrid & London, portfolio
> properties share **0** and GL accounts share only **11** — concrete BOX_ACC config **does not transfer**
> between branches. What transfers is the **structure** (topic vocabulary + `(instrument, topic)` coverage,
> London ⊆ Madrid). So the agent proposes **scope** from an analogue; **values** are always SME/GBO. And
> because config is group-keyed, a branch joining an existing group inherits it (no new config needed).

## Open-questions (branch-wide)

- Which branch PK the live BOX_ACC config keys to — operational (`22.21`/`20087.4`) vs migration
  (`AUKI_MIGMD 156.21` / `AUKI_MIGLB 157.21`) — resolved by the §5 mining extracts in
  [box-branch-config-surface](../../reference/branch-config/branch-config-surface.md).
- The `<BOOK-ABBREV>` naming scheme + exact `eventsToWaitFor` per Data-Lake feed (learn from analogue).
- MDR→Infrastructure replication, Asset Control QR-file process, and MIC integration are external —
  scope/ownership to be confirmed with the BOX team + SME.
- Whether every item is required for *all* new branches or is product/entity-triggered — confirm by
  diffing the two real branches (Madrid vs London).

**Sources:** [box-branch-config-surface](../../reference/branch-config/branch-config-surface.md), [box-branch-batch-controlm](../../reference/job-chains/control-m-batch-layer.md),
[box-acc-add-product-checklist](acc-add-product-checklist.md), `box-database-reference`, [box-overview](../../reference/system-overview.md); BOX-team onboarding
list (2026-08-24, high-level, SME to confirm).
