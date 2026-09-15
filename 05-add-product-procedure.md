# Procedure — adding a new Product (instrument)

The team's runbook for onboarding a **new product/instrument** into BOX, across three subsystems:
the Accounting API, the Financial Engine, and the Accounting Engine.

**Source:** an internal Confluence page, **explicitly marked `DOC IN PROGRESS` on every section**
`[stated: team page, imported 2026-09-16]`. Treat gaps as unwritten, not as "nothing required" — this
is the most important caveat on the whole document. Nothing here has been independently verified
against a system by this repo.

**Relationship to the existing product checklist.** This repo already has
[acc-add-product-checklist](checklists/acc-add-product-checklist.md) — a *reverse-engineered*
what-must-exist checklist for the **BOX_ACC** half, derived from the IRS implementation. This page is
different in three ways: it is **written by the people who do the work**, it covers **all three
subsystems** rather than ACC alone, and it is a **sequence** rather than a coverage list. Neither
supersedes the other; where they disagree, that is recorded rather than resolved away.

**Its first step is a document this repo already holds.** The BOX API section's "Product" step is
simply *"check BDP - Configure Instrument Mappings"* — the cross-reference page written up in
[t-box-cross-ref-s](../reference/tables/t-box-cross-ref-s.md). So the five cross-reference rows per
instrument documented there are **step one of adding a product**, confirming that table's placement on
the product axis.

**Axis note.** [04-add-book-procedure](04-add-book-procedure.md) is the Book axis; this is the
**Product axis**; [branch-onboarding-checklist](checklists/branch-onboarding-checklist.md) is the
Branch axis. The three intersect — in particular, several objects below are *branch-keyed config that
needs a new row per product*, so adding a product touches branch configuration.

---

## Part 1 — BOX Accounting: API

### Product

Configure the instrument's cross-reference mappings first —
[t-box-cross-ref-s](../reference/tables/t-box-cross-ref-s.md). Five rows minimum: one `Instrument`,
two `Direction`, two `Direction - Leg`.

### Instrument-Type

1. Modify `BOX_TRD.PKG_BOX_DEAL_LITE_DATA_API.f_CalculateInstrumentType` in `DGBOBOX` to accommodate
   the new instrument-type.
2. **Inform Camunda** of all possible instrument-types — this information is relevant for **UltData**.

Two things worth pulling out. First, this is a **code change**, in a package
[branch-onboarding-checklist](checklists/branch-onboarding-checklist.md) item 2.2 already names as the
place effective instrument type is resolved ("configured priority lookup versus product fallback"). So
the "product fallback" half of that item is *this function*, and it is not config.

Second, `UltData` is a new term in this corpus, and the Camunda notification is a **cross-team
handoff with no owner named here**. `[open-question]`

---

## Part 2 — BOX Financial Engine

Every SIGOM step below is performed on the **BOX-DEV environment (`.65` authcode)**.

> 🔑 **This names the `.65` suffix.** The corpus has repeatedly flagged the `<integer>.<integer>` PK
> format as an unexplained convention, and
> [t-box-cross-ref-s](../reference/tables/t-box-cross-ref-s.md) showed scripts *asserting* the `.65`
> fractional part in their delete guards. The page calls `.65` an **authcode**, tied to an
> environment. See that doc's *Gotchas* for what this does and does not settle.

### Days Matured

1. SIGOM screen `BOX - Financial Engine \ Control \ Configuration \ Days Matured`.
2. Create the config for the new instrument.

Observed rows (BOX-DEV): Swap, Commodity Swap and Deposit & Loan each with **2 days**.

> ⚠️ **Differs from the Tier 1 record.** [fe-raw-data-stage](../reference/fe-raw-data-stage.md) records
> `T_BOX_ENGDAYS_MATURED_S` holding **30 days** for every observed configured instrument in the full
> Tier 1 extract. BOX-DEV shows 2. Most likely an environment difference rather than a contradiction —
> but it means **`NUM_DAYS` is not a constant**, and neither value should be copied into a new
> environment as if it were. `[open-question]`

### MIS — Accrual and Accrual Exceptions

1. SIGOM screen `BOX - Financial Engine \ Control \ Configuration \ MIS`.
2. In the **Accrual** tab, add the Instrument config needed for the accrual calculation.
3. If the product is configured **not** to calculate accrual, add the Instrument config in the
   **Accrual Exceptions** tab instead.

Observed Accrual columns: internal ID, fee-calculation interval, interest interval, instrument,
several yes/no selectors, trigger, basis and a commission field — matching the grain
[fe-branch-configuration](../reference/branch-config/fe-branch-configuration.md) §2 records for
`T_BOX_ENGACCRCONF_S` ("configuration × instrument: fee/interest first-day selectors, common basis,
trigger/residual, interval, basis"). Observed values pair `Actual/365` with intervals of 377 or 370.

The screenshot also shows the tab bar in full — **Generic, Yield Curve, Accrual, Fixing Exceptions,
Accrual Exceptions, Currency Basis, Branch, Book** — an independent confirmation of the eight-tab
aggregate this repo has documented from other evidence.

**The important structural point:** Accrual and Accrual Exceptions are **per instrument**, inside a
configuration that is otherwise branch-scoped. Adding a product therefore requires touching the MIS
config of every branch that will trade it — product-axis work landing in branch-axis objects.

> ⚠️ **The `Branch` column does not hold geographic branches here.** Observed Accrual-Exception rows
> carry Branch values of the form `BOX C&F`, `BOX COMMODITIES`, `BOX CCS`, `BOX FX`, `BOX FRA`,
> `BOX OTC`, `BOX IRS` — one per *product*, not Madrid/London/NY. The same pattern appears in Allowed
> Errors below (`BOX CDS`, `BOX CFM`, `BOX DEPOSITOS`). This repo's whole FE model assumes FE config is
> keyed to a geographic branch (`T_BOX_ENGCONF_X.FK_BS → T_PGT_BRANCH_S.PK`), so either BOX-DEV uses
> product-shaped pseudo-branches as a development convention, or "branch" in these child tables means
> something broader than the branch master. **This is the most consequential open question on this
> page** — it bears directly on `sigom-box-fe-configs-agent`'s branch-keyed walk. Do not resolve it by
> assumption; read `T_PGT_BRANCH_S` in BOX-DEV and see what is actually in it. `[open-question]`

### Allowed errors

For each new instrument, define `BOX - Financial Engine \ Process Management \ Allowed Errors`.

Grain: internal ID, **Limit Errors** (a count), Instrument, Branch. Observed limits are `20` for most
instruments and `100` for Credit Derivatives — so the limit is per-instrument judgement, not a
constant. The table behind this screen is not named on the page; `Allowed Errors` is listed as a leaf
in [sigom-reference](../reference/sigom-reference.md) with no table recorded. `[open-question]`

### Processed Instruments

Insert the new instrument in `BOX - Financial Engine \ Static IT Data \ Processed Instruments`
(`BOX_FE.T_BOX_ENGINSTRUMENTS_S`) if not already present.

The observed catalogue is reproduced in
[box-data-model](../reference/box-data-model.md#box-fe-processed-instruments-catalogue) — **18
instruments, which is broader than the 11 products that have Financial Status screens.** That
distinction matters and is explained there.

### Software PL/SQL

| # | Step |
|---|---|
| 1 | Create the Financial Data table `T_BOX_<product>FINANCST_S` (e.g. `T_BOX_MMFINANCST_S`, `T_BOX_IRFINANCST_S`, `T_BOX_CESFINANCST_S`) |
| 2 | Create the MtM view `V_BOX_ENG<product>DATAMIS_S` (e.g. `V_BOX_ENGMMDATAMIS_S`, `V_BOX_ENGIRDATAMIS_S`, `V_BOX_ENGCESDATAMIS_S`) |
| 3 | Create a new constant on `BOX_FE.PKG_ENGGN` holding the new instrument's PK |
| 4 | Create a process on `BOX_FE.PKG_FE_DATADEAL_LOAD` to import data into the Deal Data table, following the existing per-instrument processes |
| 5 | Adapt `BOX_FE.PKG_ENGMAIN_OPTZ.execute_queue_optz` and `.main_backward_optz` (back process) with an `elsif` clause for the new instrument, following the IRS or CES implementations |
| 5.1 | Create package `BOX_FE.Pkg_engmain<product>_optz`, granting execute to `BOX_FE_RD` and `BOX_FE_WR` |
| 5.2 | Create package `BOX_FE.Pkg_eng<product>_optz`, same grants |

Steps 1 and 2 **confirm the Financial Status naming rules** this repo derived from the SIGOM menus
(per-product `FINANCST` table, per-product `DATAMIS` view) — now from the build side rather than the
read side. And because Deal Data gets no per-product table in this list, they confirm the shared
`T_BOX_DATADEAL_S` finding as well.

`BOX_FE_RD` / `BOX_FE_WR` are new to this corpus — read and write roles on the `BOX_FE` schema.

*(Source wording note: step 4 says "the Deal Data table created at step 1", but step 1 creates the
`FINANCST` table. Read as loose wording in the source rather than a fourth table.)*

### SIGOM

On BOX-DEV (`.65` authcode), inside SIGOM project `BOX - Financial Engine` (PK `35000005.65`):

**Typedefs tab** — add the instrument to typedef `Type_InstrumentBOX` (PK `35000079.65`):

| Field | Meaning |
|---|---|
| `Value` | the instrument's **description as received from the Data Lake** |
| `Label` | the name shown in the instrument filter on the *BOX Deal Data* / *BOX Flow Data* screens |

Observed pairs: `Loan / Depos` → `Deposit & Loan`; `IRS` → `Swap`; `Commodity Swap` → `Commodity
Swap`. **This is a fourth naming layer**, and its `IRS → Swap` agrees with the cross-reference table's
`IRS → SWAP` instrument mapping — two independent mechanisms translating the same pair.

**Objects tab** — create three objects, one per artifact from the PL/SQL steps above, placed under
`BOX - Financial Engine \ Financial Status \ <product> \`:

- `BOX - <product> Data Deal`
- `BOX - <product> Financial Data`
- `BOX_ENG_Interfaz <product> MIS-MDR`

> 🔑 **This resolves the "false friend" question.** [box-data-model](../reference/box-data-model.md)
> flagged that `V_*_ENG<CODE>DATAMIS_S` is labelled *MIS-MDR Interface* in GBO but *MtM Data* in BOX,
> warning against assuming they play the same role. The SIGOM object is named
> `BOX_ENG_Interfaz <product> **MIS-MDR**` — so on the BOX side too the object *is* a MIS-MDR
> interface. The menu label differs; the object does not.

**Unique Alias** — for each new instrument add a Unique Alias for source `BOX`, against object
`PGT - Instrument`. The alias code **must match the instrument description received from the Data
Lake** (the same value used as `Value` in the typedef). Observed alias parents are GBO instrument PKs
in the `.4` space — including `20092.4`, which
[acc-add-product-checklist](checklists/acc-add-product-checklist.md) already records as the IRS
instrument PK.

---

## Part 3 — BOX Accounting Engine

Three of these steps are **adaptations from an existing GBO screen**, which makes this section the
clearest statement so far of how ACC config is actually produced: read GBO, transform, write BOX.

### Net contract

Copy from GBO `Madrid \ Trading \ Neto Contrato Partenon` to BOX `Accounting \ Data \ Net Contract`,
using the page's attached `net_contract.sql` script.

Grain observed: branch × instrument × currency × portfolio × contract, with maintenance user and
timestamps — consistent with the `T_BOX_NETCONTRACT_S` columns
[acc-add-product-checklist](checklists/acc-add-product-checklist.md) records (`FK_BRANCH`,
`FK_INSTRUMENT`, `FK_CURRENCY`, `FK_FOLDER`, `FK_SECURITY`, …). Observed branch `22.21` (Madrid) and
instrument `20111.4` (OTC Option) match PKs already in this corpus.

**That a script exists is itself notable** — this is the second sanctioned config-migration script
found (after `cib-box-cntdblite`'s cross-reference DML), reinforcing that BOX config moves as versioned
SQL rather than by hand.

### Config for revaluation accounts

Adapt from GBO `Madrid \ Account \ Revaluation Accounts` to BOX `Accounting \ Config. \ Cross Account
Config` (`T_BOX_CROSS_ACCTCONF_S`).

**Only three account types are adapted:** *Posición Vencida*, *Posición Viva*, *Balance de Posición
Viva* (matured position, live position, live-position balance). The GBO screen holds more; the rest
are deliberately not carried over.

### Software PL/SQL

1. **Leg count decides which procedure to extend.** A product with **more than one leg** goes in
   `BOX_FE.PKG_FE_MTM_CALCULATION.p_Insert_Missing_Mtm_Data` (which propagates MTM when it isn't
   received); a **single-leg** product goes in `p_Missing_Mtm_Dir_Agnostic` instead.
2. In `BOX_FE.PKG_FE_MTM_CALCULATION.p_Import_Mtm_Data`, add the **family, group and type** for the new
   product so its MTM can be imported from LAGO.

The observed `elsif` branches map a `PKG_ENGGN` instrument constant to three strings:

| Constant | family | group | instrument |
|---|---|---|---|
| `cinstrument_if` | `IRD` | `IRS` | `CFM` |
| `cinstrument_fr` | `IRD` | `FRA` | `FRA` |
| `cinstrument_otc` | `CURR` | `OPT` | `OTC` |

Two corroborations fall out of this. `cinstrument_**if**` resolving to instrument `CFM` **confirms the
GBO code `IF` for CFM** that this repo derived from the Financial Status menus — an odd,
non-obvious code, now confirmed twice. And the `CURR` / `OPT` pair is exactly the `mfamily` / `mgroup`
values [control-m-batch-layer](../reference/job-chains/control-m-batch-layer.md) §2 records for the
OTC job variant — so the family/group vocabulary here is **the same one the Data-Lake extraction jobs
use**, which is what makes the import line up.

Note this section sits under "BOX Accounting Engine" but every package named is in **`BOX_FE`**. The
page's section headings track workstreams, not schema ownership.

### Config. Local Properties

Adapt from GBO `SYS \ Accounting \ Config. Local Properties` to BOX `Accounting \ Config. \ Config.
Local Properties`.

**BOX's version is more extensive than GBO's** because topics are divided into sections. To adapt,
read a GBO Portfolio Property and add each topic into its respective section.

> **Topics and conditions are created as `.65`.** Missing topics are created in
> `BOX - Accounting \ Data \ Accounting Topics` (`T_BOX_ACCT_TOPICS_S`); missing conditions in
> `BOX - Accounting \ Config. \ Condition Port Properties` (`T_BOX_CONDPAR_PROP_S`). The `.65`
> instruction is the same environment authcode as the FE steps.

### Portfolio Properties

Adapt from GBO `Accounting \ General \ Portfolio Properties` to BOX `Accounting \ Config. \ Portfolio
Properties` (`T_BOX_ACCT_PORT_PROP_S`).

Grain observed: branch × instrument × initial date × status × description, with branch values for both
Spain and London and PKs in the `.21` space. *(Descriptions are not reproduced here — they carry
portfolio naming, which this repo excludes.)*

> **Not a 1:1 copy, and the page says so explicitly:** *"not all PPs must be adapted. A previous
> analysis must be done to see if we can consolidate GBO PPs in a smaller number of BOX PPs, since the
> relationship between topics and accounts is the same, or if we need fewer portfolio conditions."*
>
> This is a direct instruction that **portfolio-property migration requires a consolidation analysis**,
> not mechanical transcription — and it belongs to whoever owns the ACC side
> ([sigom-box-acc-configs-agent](../../agents/sigom-box-acc-configs-agent/AGENT.md), currently
> deferred). It also corroborates
> [branch-config-madrid-london-diff](../reference/branch-config/branch-config-madrid-london-diff.md)'s
> finding that portfolio properties do not transfer between branches: if GBO→BOX needs analysis rather
> than copying, branch→branch certainly does.

---

## What this page does not cover

Marked `DOC IN PROGRESS` throughout, so absence means unwritten. Specifically missing:

- **Any BOX ACC accounting-event or topic→GLTA work** beyond the local-properties note — the substance
  of [acc-add-product-checklist](checklists/acc-add-product-checklist.md) §4.
- **Testing and validation.** No step confirms the product actually processes end to end.
- **Promotion beyond BOX-DEV.** Every SIGOM step says BOX-DEV / `.65`; how the config reaches PRE and
  PRO is not described here (the Book runbook's "export with dynamic pk" is the nearest analogue).
- **Rollback**, and **who performs which step** — several steps are plainly developer work and others
  plainly configuration, with no owner named.

## Discrepancies and open questions

| # | Item | Status |
|---|---|---|
| 1 | `Branch` column holding `BOX <PRODUCT>` values in Accrual Exceptions and Allowed Errors | **Most consequential.** Contradicts the geographic-branch model the FE agent assumes. Read `T_PGT_BRANCH_S` in BOX-DEV before concluding. `[open-question]` |
| 2 | Days Matured = 2 in BOX-DEV vs 30 across Tier 1 | Probably environmental; proves `NUM_DAYS` is not constant. `[open-question]` |
| 3 | "Zero new PL/SQL per product" (the universal-engine claim on `acc-add-product-checklist`) | **Holds for ACC accounting only.** BOX FE demonstrably needs per-product packages — see that page's qualified note |
| 4 | The table behind `Allowed Errors` | Not named anywhere. `[open-question]` |
| 5 | `UltData`, and who owns informing Camunda | New term, no owner. `[open-question]` |

## Sources

Internal Confluence page *Adding a Product to BOX*, imported 2026-09-16, marked `DOC IN PROGRESS`
`[stated: team page, not independently verified]`. Portfolio-property descriptions and contract
identifiers visible in the source screenshots are deliberately not reproduced. Cross-referenced against
[t-box-cross-ref-s](../reference/tables/t-box-cross-ref-s.md),
[acc-add-product-checklist](checklists/acc-add-product-checklist.md),
[fe-branch-configuration](../reference/branch-config/fe-branch-configuration.md),
[box-data-model](../reference/box-data-model.md), [fe-raw-data-stage](../reference/fe-raw-data-stage.md),
[control-m-batch-layer](../reference/job-chains/control-m-batch-layer.md).
