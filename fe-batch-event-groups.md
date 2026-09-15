# BOX FE batch — the event-group sequence

What the Oracle dispatcher actually runs inside BOX_FE once a scheduled job fires: the ordered event
groups, their PKs, and the procedures inside two of them.

> **Read this alongside [`box-fe-acc-batch-runtime.md`](box-fe-acc-batch-runtime.md), not instead of
> it.** The two documents are different layers of one stack and were written from different evidence:
>
> | | `box-fe-acc-batch-runtime.md` | **this doc** |
> |---|---|---|
> | Layer | **Scheduler** — Control-M job topology | **Inside Oracle** — what one job's dispatcher call does |
> | Scope | BOX_FE **and** BOX_ACC | BOX_FE only |
> | Evidence | `[confirmed: repository configuration]` + `[confirmed: database extracts]` | `[stated: team Confluence page]`, not independently verified |
>
> **The seam between them is `f_ExecuteGroup`.** That doc records the dispatcher signature
> `PGT_ES.PKG_GMBATCHPROCESS.f_ExecuteGroup(group, branch, process-date, instrument, mode, label,
> sub-label)` and flags `[open-question: current dispatch/wrapper]` — it has the function but not the
> `group` values. **This doc is the list of those `group` values.** Each document supplies the other's
> missing half, so a finding here that contradicts one there should be resolved in favour of the
> repository/DB evidence, not this page.

**Source:** an internal Confluence overview of the Financial (batch) Process, imported 2026-09-16.
Event-group names and PKs are quoted as given; nothing here has been independently verified against a
running system by this repo.

Upstream of all of this is [control-m-batch-layer](control-m-batch-layer.md), which covers the
Data-Lake feed that lands rows in the RAW tables before any of the groups below run.

---

## 1. Before the batch — two prerequisite processes

Both are `ENG GN` processes that populate **Historical Data** from **Configuration**. They must run
before the FE batch proper.

### 1.1 Load foreign exchange rate

| | |
|---|---|
| **Event group** | `ENG GN - Main Captura de las curvas de fixing BOX` (**`2387.65`**) |
| **Configuration read** | `BOX - Financial Engine \ Control \ Configuration \ Fixing Curve` |
| **Result written** | `BOX - Financial Engine \ Control \ Historical Data \ Fixing Curve` |

**Upstream prerequisite:** *PGT Quote Prices* (`GBO \ Market Data \ Quote Prices \ Currency Pair`)
must be inserted **before** the fixing batch executes.

Observed Process Calendar entry: Event `Fixing Catching`, Process `Fixing Program.`, with a named
Fixing Curve selected and status `Pending`.

> 🔑 **This resolves a trap flagged in the query catalogue.** `Fixing Curve` appears as a SIGOM leaf
> under **both** `Control > Configuration` and `Control > Historical Data`, and
> [fe-config-mining](../queries/fe-config-mining.md) Q-03 warns to "confirm which population you're
> reading before comparing" without being able to say which is which. Now settled:
> **Configuration is the input the batch reads; Historical Data is the output the batch writes.** So
> the config walk mines *Configuration*, and a populated *Historical Data* is evidence the batch has
> run — not a second place to configure.

### 1.2 Relation fixing with CIB Entity (Branch)

| | |
|---|---|
| **Event group** | `ENG GN - Main Captura datos mercado for config BOX` (**`2388.65`**) |
| **Configuration read** | `BOX - Financial Engine \ Control \ Configuration \ MIS` |
| **Result written** | `BOX - Financial Engine \ Control \ Historical Data \ Market Data` **and** `… \ Historical Data \ Branch - MIS` |

Observed Process Calendar entry: Event `Get Configuration Market Data`, Process `Mktdata Program`,
against a named Eng Configuration, status `Pending`.

**Two things follow.** First, the MIS configuration aggregate — the eight tabs the FE config walk
builds — is **read by this process**, which is what turns configuration into the market data the batch
then uses. Second, **`Branch - MIS` exists on the BOX side as a batch *result***. This repo previously
flagged GBO's `T_PGT_BRANCH_MIS_S` (Branch MIS ↔ Branch MDR mapping) as a branch-keyed table with no
known BOX counterpart ([sigom-reference](../sigom-reference.md)). There is one — but it is
**generated**, not configured, which is why it never appeared in the config surface. `[inferred]` —
the screen exists under Historical Data; that it is the same population as GBO's table is not proven.

---

## 2. The FE batch — nine event groups in order

`[stated: team page, 2026-09-16]`

| Order | Event group | PK |
|---:|---|---|
| 1 | ENG GN - Main Captura de las curvas de fixing BOX | `2387.65` |
| 2 | ENG GN - Main Captura datos mercado for config BOX | `2388.65` |
| 3 | Calc Raw Flow StartDate And EndDate BOX | `2628.65` |
| 4 | Import Deal Data And Flow Data BOX | `2629.65` |
| 5 | Update current values and amountlocal BOX | `2630.65` |
| 6 | Import Mtm Data BOX | `2632.65` |
| 7 | **Insert `<product>` Deal Data** — eight parallel groups, one per product (below) | various |
| 8 | Create Process Queues by Book BOX | `2608.65` |
| 9 | ENG GN Main Dia Queue By Book BOX | `2389.65` |

Steps 1–2 are the prerequisites from §1 — so the "before batch" processes are the first two members of
the same ordered sequence, not a separate mechanism.

### Step 7 — per-product Deal Data inserts

| Product | Event group | PK |
|---|---|---|
| MM (Deposit & Loan) | Insert BOX MM Deal Data | `2631.65` |
| CES (Commodity Swap) | Insert BOX CES Deal Data | `2490.65` |
| IRS (Swap) | Insert BOX IRS Deal Data | `2835.65` |
| CCS | Insert BOX CCS Deal Data | `3255.65` |
| CFM | Insert BOX CFM Deal Data | `3479.65` |
| FRA | Insert BOX FRA Deal Data | `3661.65` |
| FX | Insert BOX FX Deal Data | `3155.65` |
| OTC | Insert BOX OTC Deal Data | `3803.65` |

**Eight products, and they are exactly the product codes this repo documents** for BOX FE Financial
Status (see [box-data-model](../box-data-model.md#financial-status-surfaces-gbo-vs-box-fe)) — minus
`BRS`, `C&F` and `CDS`, which have Financial Status screens but no Deal Data insert group listed here.
Whether those three are genuinely absent from the batch or simply omitted from this overview is
unstated. `[open-question]`

This step is also **the concrete meaning of "adding a product needs a new batch group"**: the
add-a-product runbook's PL/SQL step 4 (create a process on `PKG_FE_DATADEAL_LOAD`) is what one of these
groups executes — see [05-add-product-procedure](../../process/05-add-product-procedure.md).

### Step 8 — a temporary condition, flagged at source

`Create Process Queues by Book BOX` (`2608.65`) carries an explicit note on the source page:

> *Temporary: this batch should be executed with a Monitor record in 'Programmed' process.*

Worth carrying forward because it is a known deviation with an expiry implied but no date, and because
it touches the queue-maker — the same machinery
[fe-branch-configuration](../branch-config/fe-branch-configuration.md) §5 describes resolving
`T_BOX_CONF_BY_BOOK_S` by `(FK_BRANCH, FK_INSTRUMENT)`. `[open-question]` — what replaces the temporary
arrangement, and when.

---

## 3. Procedure execution order inside groups 4 and 5

`[stated: team page, 2026-09-16]` — the packages each event group drives, in order.

### `Import Deal Data And Flow Data BOX` (`2629.65`)

| # | Procedure |
|---:|---|
| 1 | `BOX_FE.PKG_FE_DEAL_CALCULATION.p_Import_Deal_Data` |
| 2 | `BOX_FE.PKG_FE_FLOW_CALCULATION.p_Import_Flow_Data` |
| 3 | `BOX_FE.PKG_FE_PROPAGATION_DATA.p_PropagLastIncorporation` |
| 4 | `BOX_FE.PKG_FE_PROPAGATION_DATA.p_PropagWhenZeroFlows` |
| 5 | `BOX_FE.PKG_FE_PROPAGATION_DATA.p_PropagationAlways` |

### `Update current values and amountlocal BOX` (`2630.65`)

| # | Procedure |
|---:|---|
| 6 | `BOX_FE.PKG_FE_FLOW_CALCULATION.p_Update_Interest_EOM` |
| 7 | `BOX_FE.PKG_FE_FLOW_CALCULATION.p_Default_Deal_Flows` |
| 8 | `BOX_FE.PKG_FE_DEAL_CALCULATION.p_update_current_values` |
| 9 | `BOX_FE.PKG_FE_FLOW_CALCULATION.p_Adjust_Flows` |
| 10 | `BOX_FE.PKG_FE_FLOW_CALCULATION.p_update_amountlocal` |
| 11 | `BOX_FE.PKG_FE_DEAL_CALCULATION.p_update_alm_amounts` |

**Procedure 2 is already documented in this repo, and now has a position.**
[fe-raw-data-stage](../fe-raw-data-stage.md) records `[confirmed: code + DB]` that
`PKG_FE_FLOW_CALCULATION.p_Import_Flow_Data` merges RAW Flow into `T_BOX_FLOW_DATA_S`. It is step 2 of
event group `2629.65`, immediately after the Deal equivalent.

**Procedure 1 names something that was an open question.** That same doc flags "no same-date RAW Deal →
DATADEAL row-level join has yet been supplied" — `PKG_FE_DEAL_CALCULATION.p_Import_Deal_Data` is the
procedure performing that transformation. Reading its source is the direct route to closing that gap.

**A third package family appears here:** `PKG_FE_PROPAGATION_DATA`, with three distinct propagation
strategies (last incorporation, when zero flows, always). `PROPAGATION` appears as a *column* on
processed Flow in `fe-raw-data-stage.md`; this is the logic that sets it. Not otherwise documented.
`[open-question]`

---

## 4. Runtime observation — the Process Calendar runs per (branch, instrument)

The observed Process Calendar row for the FE batch:

| Field | Value |
|---|---|
| Date | (a business date) |
| Branch | `BOX COMMODITIES` |
| Reference | `BR: BOX COMMODITIES - COMM_SWAP` |
| Process | `Generation of Financial Status` |
| Status | `Pending` |

This is `T_BOX_BRPROCCAL_S` territory — which
[fe-config-mining](../queries/fe-config-mining.md) Q-11 already characterises as "runtime activity, NOT
configuration selection".

> ⚠️ **This materially strengthens the product-shaped-branch question.** The Accrual Exceptions and
> Allowed Errors *configuration* screens show `Branch` values like `BOX CCS` and `BOX FX`
> ([fe-branch-configuration](../branch-config/fe-branch-configuration.md) §2). Here the same shape
> appears in the **runtime queue**: the batch is scheduled against branch `BOX COMMODITIES` for
> instrument `COMM_SWAP`, and the reference string is built from that pair. So the product-shaped
> branch is not a config-screen artifact — **it is the unit the batch actually processes**. That makes
> "is this a dev convention?" a weaker explanation than it was, and raises the stakes on reading
> `PGT_STC.T_PGT_BRANCH_S` in BOX-DEV before the FE walk relies on a geographic-branch model.
> `[open-question]`

---

## Reconciled against the scheduler doc `[2026-09-16]`

An earlier draft of this page carried four *Still pending* items written before
[`box-fe-acc-batch-runtime.md`](box-fe-acc-batch-runtime.md) was available here. Three of the four are
answered there. Recorded as a reconciliation rather than silently deleted, because *what closed each
one* matters.

| Was pending here | Status | Where it's answered |
|---|---|---|
| The BOX_ACC batch topology | **Closed** | That doc §3 — repos `cib-boxacc-t1mdesac` (initial accounting, accounting, MTM/revaluation, ruler updates) and `cib-boxacc-t1mdacccheck` (barriers), under the `ACCOUNTING` subapplication |
| The FE→ACC completion-event contract | **Closed** | That doc §4 — FE completion events are declared dependencies of the accounting jobs. FE and ACC are **separate Oracle batch layers joined through Control-M events**, not one continuous chain |
| Which event groups a *new branch* needs | **Sharpened, not closed** | That doc's `T_BOX_MBJ_PROPERTIES_S` extract binds each job to a **(branch, instrument)** pair, so the unit of "what a new branch needs" is now a known shape even though the list for NY_SCH isn't derived |
| Failure and restart behaviour | **Still open** | Open in both documents |

### Two structural findings from putting the two side by side

**1. FE event groups and ACC MBJ groups look like one numbering space, not two.** `[inferred]` The ACC
groups recorded there are `3275.65` (General Accounting, 18 ordered events) and `3375.65`
(MTM/Revaluation, 8 events). The FE groups on this page run from `2387.65` to `3803.65` and include
`3255.65` and `3479.65` — the ACC values fall *inside* that range and interleave with it. The
straightforward reading is that FE event groups and ACC MBJ groups are **the same entity type in one
table**, distinguished by which engine consumes them rather than by a separate registry. If that
holds, the ACC half of a branch walk is minable the same way the FE half is — worth one query to
confirm before anyone builds two separate mining paths.

**2. CES has an FE Deal Data group but no ACC accounting.** That doc reports CES observed in FE for
Madrid but **absent from the current ACC MBJ catalogue**, and flags it as an open question rather than
a no-accounting conclusion. This page independently lists `Insert BOX CES Deal Data` (`2490.65`) as one
of the eight FE groups. The two agree, and together they establish a real **FE/ACC product asymmetry**:
a product can be fully processed by the Financial Engine and still have no accounting configured. Any
"is this product supported?" check therefore has to be asked **per engine**, not once.

Its "eight active instruments span fifteen product/branch pairs" also matches the **eight** per-product
Deal Data groups listed above — probably the same eight, though neither source names the set the other
way round. `[inferred]`

## Sources

Internal Confluence overview of the Financial (batch) Process, imported 2026-09-16
`[stated: team page, not independently verified]`. Reconciled against
[`box-fe-acc-batch-runtime.md`](box-fe-acc-batch-runtime.md) (Devin, from Control-M repository
configuration and DB extracts). Cross-referenced against
[control-m-batch-layer](control-m-batch-layer.md), [fe-raw-data-stage](../fe-raw-data-stage.md),
[fe-branch-configuration](../branch-config/fe-branch-configuration.md),
[fe-config-mining](../queries/fe-config-mining.md),
[04-add-book-procedure](../../process/04-add-book-procedure.md),
[05-add-product-procedure](../../process/05-add-product-procedure.md).
