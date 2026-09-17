# Procedure — adding a new Book

The operational runbook for onboarding a **new Book**, end to end: the Data-Lake/Control-M jobs that
feed it, then its configuration in BOX FE and BOX ACC.

**Source:** an internal Confluence page maintained by the team that actually performs this work
`[stated: team runbook, imported 2026-09-15]`. Parts of the original are in Spanish; the prose here is
translated, while **literal field values are kept exactly as they must be typed** (`Diaria`, `lo
dejamos vacío`, and similar). Nothing below has been independently verified against a system by this
repo — it is a faithful record of a procedure people follow, which is a different kind of evidence
from a DB read, and is tagged accordingly.

**Why this is its own document.** Everything else in this repo is organised around the **branch** axis
(onboard NY_SCH) or the **product** axis ([acc-add-product-checklist](checklists/acc-add-product-checklist.md)).
This is the **Book** axis, and it cuts across both: a book belongs to a branch, carries instruments,
and needs work in three separate systems. It is also the first procedure in this repo written by the
people who run it rather than reverse-engineered from code — so where it disagrees with a
reverse-engineered doc, that disagreement is itself a finding (see *Discrepancies* at the end).

**Scope boundary.** This is a Book procedure, not a branch procedure. Onboarding a *branch* will
require books, so this runbook is a dependency of
[branch-onboarding-checklist](checklists/branch-onboarding-checklist.md) item 1.3 — but running it
does not onboard a branch, and it assumes the branch already exists in every system it touches.

---

## Part 1 — ADD BOOK LAKE (Data Lake / Control-M)

Creating the load jobs for a new book in **Supra**.

### 1.1 Job count and shape

**Four jobs per book:**

| Data type | Jobs | Note |
|---|---|---|
| Deal data | **2** | one depends on `trade_details_sql`, the other does not |
| Flow data | 1 | |
| Market data | 1 | |

> ⚠️ This contradicts [control-m-batch-layer](../reference/job-chains/control-m-batch-layer.md) §3,
> which reverse-engineered **six** jobs per book (4 Deal-data flavors — base/`OTC`/`SQL`/`OTCSQL` —
> plus Flow and Market) from the `diaria.json` repo. See *Discrepancies* below. Do not silently pick
> one number.

### 1.2 In-conditions — the upstream Data-Lake loads each job waits for

| Job | Waits on the load jobs for |
|---|---|
| Deal data (1st) | `cd_gcb_financial_formalised_contracts.trade_details`, `cd_gcb_financial_formalised_contracts.pnl_leg` |
| Deal data (2nd) | the **1st Deal job's own name**, plus `cd_gcb_financial_formalised_contracts.trade_details_sql` |
| Flow data | `cd_gcb_financial_formalised_contracts.trade_details`, `…past_flows`, `…future_flows` |
| Market data | `cd_gcb_financial_formalised_contracts.trade_details`, `…position`, `cd_sensibilidades.pnl` |

These are the schema-qualified names of the sources
[fe-raw-data-stage](../reference/fe-raw-data-stage.md) already recorded unqualified
(`trade_details_current`, `murex_past_flows_current`, `position`, `murex_pnl_current`) — the two
records corroborate each other. `trade_details_sql` and the `cd_sensibilidades` schema are new here.

Note the **serial dependency**: the second Deal job waits on the first. The four jobs are not four
independent parallel loads.

### 1.3 Job naming

All jobs follow one shape, where `<BOOK-ABBREV>` is *"algo identificativo del libro"* — **something
that identifies the book**, chosen by the person creating the job:

| Data type | Pattern | Worked example (book `CROSS LATAM`) |
|---|---|---|
| Deal data (1st) | `PAUKIDD<BOOK-ABBREV>001D` | `PAUKIDDCROSSLT001D` |
| Deal data (2nd) | `PAUKIDD<BOOK-ABBREV>SQL001D` | `PAUKIDDCROSSLTSQL001D` |
| Flow data | `PAUKIFD<BOOK-ABBREV>001D` | `PAUKIFDCROSSLT001D` |
| Market data | `PAUKIMD<BOOK-ABBREV>001D` | `PAUKIMDCROSSLT001D` |

**Two things worth noticing.** First, there is **no region token** in these names — the existing
Control-M doc records Europe jobs carrying `SCIB` (`PAUKISCIBDDCREBSMAD001D`) and LatAm-local jobs
embedding a country letter. These have neither. Second, the book named `CROSS LATAM` is configured
with `Country → ES` and `Source system → Mx3EU`, so **a book's name does not tell you its country or
Murex instance**. Both points go in *Discrepancies*.

This also effectively answers a long-standing open question: `<BOOK-ABBREV>` is a **hand-made
contraction of the book name**, not a value looked up from a table. See the correction in
[control-m-batch-layer](../reference/job-chains/control-m-batch-layer.md) §4.

### 1.4 The Control-M request template

Filled in and attached to a planning request. Template: *Planificacion SCIB
SGT-Plantilla_Procesos_Control-M NEW_Auki_v3.xlsx*.

| Field | Value |
|---|---|
| `JOBNAME` | the job name being created (§1.3) |
| `FILE PATH` | `/initiatives_share/ext_complex/` |
| `FILE NAME` | deal / flow / market → `Ext_complex_lambda_auki_tabla_pais_book_source_pnl_stat_sp3.sh`<br>the `trade_details_sql`-dependent deal job → `Ext_complex_lambda_auki_tabla_pais_book_source_pnl_sql_sp3.sh` |
| `HOST/HOST GROUP` | `PRO-HDP-COR-BTH-OHE` |
| `RUN AS` | `ueext_complex` |
| `ID TECNICO ORBIS` | `800014823` |
| `GROUP NAME` | `EXT_COMPLEX` |
| `PRIORITY` | *lo dejamos vacío* (leave empty) |
| `CALENDAR` | `LVM25Y1` |
| `PERIOCITY` | `Diaria` (daily) |
| `IN CONDICION` | the in-condition jobs per §1.2, each suffixed `-OK` |
| `OUT CONDICION` | two: the job's own name + `-OK`, and the same prefixed `G010014-`. e.g. `PAUKIDDCROSSLT001D-OK` and `G010014-PAUKIDDCROSSLT001D-OK` |
| `UNIT` | *lo dejamos vacío* |
| `QUANTITATIVE RESOURCES NAME` | `PRO-HDP-COR-BTH-OHE` → 1, `PRO-HDP-COR-BTH-EXTCOM` → 1 |
| `CONTROL RESOURCES NAME` | *lo dejamos vacío* |
| `CRITICITY / ACTIONS ON ERROR` | *lo dejamos vacío* |
| `IN CASE OF JOB UNSCHEDULING…` | *lo dejamos vacío* |
| `OBSERVATIONS` | `YYYY-MM-DD` ⇒ date format for `$ODATE` |

`CALENDAR = LVM25Y1` matches what
[control-m-batch-layer](../reference/job-chains/control-m-batch-layer.md) §2 already recorded from the
repo — an independent confirmation.

#### Job parameters

Shown for the worked example; the per-book variables are `Country`, `Book`, `Source system`.

| Parameter | Deal 1st | Deal 2nd | Flow | Market |
|---|---|---|---|---|
| `Entorno` | `PRO` | `PRO` | `PRO` | `PRO` |
| Json to execute | `auki_deal_data_all` | `auki_deal_data_all` | `auki_flow_data_all` | `auki_market_data_all` |
| jceks name | `uappproextscib.jceks` | `uappproextscib.jceks` | `uappproextscib.jceks` | `uappproextscib.jceks` |
| `Country` | `ES` | `ES` | `ES` | `ES` |
| `Book` | `CROSS LATAM` | `CROSS LATAM` | `CROSS LATAM` | `CROSS LATAM` |
| `Source system` | `Mx3EU` | `Mx3EU` | `Mx3EU` | `Mx3EU` |
| `Pnl_type` | `EOD` | `EOD` | `EOD` | `EOD` |
| `Validation_status` | `-1` | `-1` | `-1` | `-1` |
| `Native_validation_Status` | `BOValidated` | `BOValidated` | `BOValidated` | `BOValidated` |
| `Data_execution_type` | — | `OTHER` | — | — |
| `Data_date_part` | `$ODATE` | `$ODATE` | `$ODATE` | `$ODATE` |

`Data_execution_type = OTHER` is present **only** on the second (SQL-dependent) Deal job — the one
parameter that distinguishes the two Deal jobs beyond their script and in-conditions.

> ⚠️ **`Native_validation_Status = BOValidated` is a template default, and it is wrong for a branch
> still live in GBO.** This is the same trap recorded in
> [control-m-batch-layer](../reference/job-chains/control-m-batch-layer.md) §2: `BOValidated` is the
> AUKI status, so running this template unchanged against a not-yet-migrated branch's data selects no
> rows and fails silently. For NY_SCH specifically, resolve this value per branch rather than copying
> the template.

### 1.5 Request, verify, and wire into the DUMMY jobs

4. Open the request in **ServiceNow** with the completed template attached so the jobs get created.
   Precedent request: `RITM017296271`.
5. Once created, open Control-M and check the jobs are correct, then raise a **self-service** request
   to run them and confirm they work.
6. Once the new jobs run correctly and automatically, add them to the **DUMMY jobs** used for Calypso
   extractions:

   | DUMMY job | For |
   |---|---|
   | `PAUKIDDESDUMMY001D` | ES Deal data jobs |
   | `PAUKIDDLBDUMMY001D` | LB Deal data jobs |
   | `PAUKIMDESDUMMY001D` | ES Market data jobs |
   | `PAUKIMDLBDUMMY001D` | LB Market data jobs |

   This uses a second template (*…Plantilla_Procesos_Control-M MOD_Auki_dummy.xlsx*) for a
   modification rather than a creation, raised as its own ServiceNow request (precedent:
   `RITM017321558`), then verified.

> **Relevant to NY_SCH:** the DUMMY jobs exist for **ES and LB only** — there is no US/NY family, and
> none for Flow data on either. A NY book needing Calypso extraction would need a new DUMMY job family
> created, which is not in this runbook. `[open-question]`

---

## Part 2 — ADD BOOK BOX FE and ACC

### 2.1 Create the job meshes

Work from an existing book's meshes as the template. The runbook's reference example is the book
*Supply Chain Financing Notes - GTB Spain*, whose meshes live in
`JACD-T1MDSCFNGTBES-BOXFE-100068124` and `JACD-T1MDSCFNGTBES-BOXAC-100068125`. Jobs already created
are documented on the *Flow Run* page, on each instrument's sub-page.

| Item | Convention |
|---|---|
| Mesh/folder names | `JACD-T1MD<ABBREV>-BOXFE-100068124` and `JACD-T1MD<ABBREV>-BOXAC-100068125`, where `<ABBREV>` identifies the book |
| Job description | must name the new **book, branch and instrument** |
| Job names | `GMBX<n>ES<label>D<nn>` — `<n>` is the number associated with the **instrument** (`0` = generic jobs), `ES<label>` is the next label in the list |

Two mesh families per book, one for **BOXFE** and one for **BOXAC** — mirroring the FE/ACC split the
rest of this repo follows.

#### Deploy descriptors

| Environment | BOXAC | BOXFE |
|---|---|---|
| **PRE** | nothing to modify — rename the file to `JACD-T1MD<ABBREV>-BOXAC-100068125pre` | nothing to modify — rename to `JACD-T1MD<ABBREV>-BOXFE-100068124pre` |
| **PRO** | rename to `JACD-T1MD<ABBREV>-BOXAC-100068125pro` | **more involved** — in the *Add PRO prerequisites* section, point the path at `JACD-T1MD<ABBREV>-BOXFE-100068124` and change the job to `ES<label>`; the lake jobs that come out must then be replaced with the ones the Data-Lake team specifies for that book; rename the file to `JACD-T1MDX<ABBREV>-BOXFE-100068124pro` |

Note the PRO BOXFE file name gains an `X` (`JACD-T1MD**X**<ABBREV>-…`) that the others don't. Recorded
as written; whether that is meaningful or a typo in the source is unverified. `[open-question]`

The PRO step is also where **Part 1 and Part 2 meet**: the lake jobs referenced here are the Control-M
jobs created in Part 1, and they are supplied by the Data-Lake team rather than derived.

### 2.2 Modify flags

Existing meshes that must be edited to know about the new book. `ES<label>` below is the new book's
label; `<nn>` job suffixes are as written in the source.

| Mesh | Instrument | Job to edit | In-condition to add |
|---|---|---|---|
| `JACD-T1MDFINANCIALCHECK-BOXFE-100068124` | depos | `GMBOX0113D01` | `GMBX1ES<label>D06-OK` |
| `JACD-T1MDFINANCIALCHECK-BOXFE-100068124` | IRS | `GMBX3ES00D04` | `GMBX3ES<label>D06-OK` |
| `JACD-T1MDACCCCHECK-BOXAC-100068125` | depos | `GMBOX1ES00D05` | `GMBX1ES<label>D08-OK` |
| `JACD-T1MDACCCCHECK-BOXAC-100068125` | IRS | `GMBX3ES00D05` | `GMBX3ES<label>D09-OK` |
| `JACD-T1MDFXFWD-BOXFE-100068124` | — | `GMBX3ES00D08` | `GMBX0ES<label>D03-OK` |
| `JACD-T1MDALMFIELDS-BOXFE-100068124` | — | `GMBOXES00D07` | `GMBX0ES<label>D10-OK` |

For `JACD-T1MDALMFIELDS-BOXFE-100068124` there is an extra step: **create** job
`GMBX0ES<label>D10` based on an existing one (the example given is `GMBX0ES49D10`), putting the new
book in the description and substituting the new label everywhere the template has `ES49` — then add
the in-condition above.

The `FINANCIALCHECK` mesh is almost certainly the FE→ACC completion barrier that
[agent-architecture](../reference/branch-config/agent-architecture.md) lists under *Deliberately not
built yet* as "the `mdfinancialcheck`-style barrier between FE and ACC batch". `[inferred]` — the
name matches and the position in the flow matches, but nothing here proves it.

### 2.3 Unix jobs

Add the jobs to `db.conf`. Each line binds a Control-M job name to an Oracle batch-process call:

```text
########## BOX - FE and ACC ##########
GMBX0ES50D01:T:F:PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup(2628.65, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_BRANC_MAD, to_date('$ODATE','YYYYMMDD'), …
GMBX0ES50D02:T:F:PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup(2629.65, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_BRANC_MAD, to_date('$ODATE','YYYYMMDD'), …
…
```

Three things this exposes:

- **The batch entry point is `PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup`**, taking a *group PK* as its
  first argument (`2628.65`, `2629.65`, `2630.65`, `2632.65`, `2631.65`, `2389.65`, `2835.65`,
  `2407.65`, `2408.65`, `2735.65`, `2875.65`, `2755.65`, `3015.65` across the example's 16 lines).

  **Identified, 2026-09-16, then named the same day.** These are **event-group PKs**, and
  `db.conf` is the binding between a Control-M job name and the event group it executes. Seven of the
  fifteen lines can now be named outright, from the FE batch sequence in
  [fe-batch-event-groups](../reference/job-chains/fe-batch-event-groups.md):

  | Job | Group PK | Event group |
  |---|---|---|
  | `GMBX0…D01` | `2628.65` | Calc Raw Flow StartDate And EndDate BOX |
  | `GMBX0…D02` | `2629.65` | Import Deal Data And Flow Data BOX |
  | `GMBX0…D03` | `2630.65` | Update current values and amountlocal BOX |
  | `GMBX1…D04`, `GMBX3…D04` | `2632.65` | Import Mtm Data BOX |
  | `GMBX1…D05` | `2631.65` | **Insert BOX MM Deal Data** |
  | `GMBX3…D05` | `2835.65` | **Insert BOX IRS Deal Data** |
  | `GMBX1…D06`, `GMBX3…D06` | `2389.65` | ENG GN Main Dia Queue By Book BOX |

  The remaining six (`2407.65`, `2408.65`, `2735.65`, `2875.65`, `2755.65`, `3015.65`) are **not** in
  the FE sequence — and two of them, `2735.65` and `2755.65`, are listed in
  [acc-add-product-checklist](checklists/acc-add-product-checklist.md) §4 as `T_PGT_BR_EVE_S` event
  groups on the **accounting** side ("Accounting General Local wFE No Reval-BM", "Mark to Market CorteH
  Reval"). So a single book's `db.conf` block spans **both the FE and ACC batches**, which is why the
  section header reads "BOX - FE and ACC".

  **`<n>` in `GMBX<n>` is an instrument index, and it is not the Processed Instruments PK.** §2.2 of
  this runbook states directly that `GMBX1` jobs are *depos* and `GMBX3` jobs are *IRS*, and the group
  names above agree (`GMBX1…D05` → Insert **MM**, `GMBX3…D05` → Insert **IRS**). But the Processed
  Instruments catalogue gives Deposit & Loan PK `1.65`, **Swap `2.65`** and Commodity Swap `3.65`
  ([box-data-model](../reference/box-data-model.md#box-fe-processed-instruments-catalogue)) — so `1`
  lines up and `3` does not. Treat `GMBX<n>` as its own local numbering and read it from the job
  descriptions, not derived from an instrument PK. `[open-question]`

  The `.65` suffix these share is **semantically load-bearing** rather than cosmetic: the
  cross-reference scripts guard their deletes on it explicitly (see
  [`../reference/tables/t-box-cross-ref-s.md`](../reference/tables/t-box-cross-ref-s.md), *Gotchas*).
  **✅ Resolved 2026-09-17:** it is the **environment's auth code**, added as a fractional part by the
  `F___SEQUENCE` PK function — `65 → +0.65`. So `.65` marks rows allocated in the BOX-DEV environment,
  and the delete guards are scoping to that environment's data. See
  [`../reference/sigom-reference.md`](../reference/sigom-reference.md), *What the auth code actually is*.
- **The branch is a package constant, not a parameter**: `PGT_ES.PKG_GMBATCHPROCESS.CST_PK_BRANC_MAD`
  — `MAD` for Madrid. A different branch would need its own `CST_PK_BRANC_<x>` constant, which means
  **adding a branch here is a code change, not configuration**. That is directly relevant to branch
  onboarding and is not captured anywhere else in this repo. `[inferred]` from the naming.
- The schema is `PGT_ES` — a GBO-family schema, not `BOX_FE`/`BOX_ACC`, despite the section being
  headed "BOX - FE and ACC". `[open-question]`

Then generate the job scripts from the template and register them:

```sh
sh -x /appl/gm/etc/delete_jobsBX.ksh  db.conf /appl/gm/etc/db_delete.txt
sh -x /appl/gm/etc/add_new_jobs.ksh   db.conf /appl/gm/etc/db_nuevo.conf

cp /appl/gm/scripts/templates/db_job /appl/gm/scripts/GMBX0ES50D01
…                                                    # one cp per job
chmod 755 /appl/gm/scripts/GMBX0ES50D01
…                                                    # one chmod per job
```

### 2.4 Label config

Add the new book in the SIGOM screen `GBO \ SYS \ Process \ Batch \ Label Config \ Label Config`, and
assign it the **Label BOX** code listed for the corresponding branch on the *BOOKS* page.

Then **export the label config** to insert it into the environments.

This is the label side of the book identity — the same `CODE - DESCRIPTION` pairing this repo has
confirmed in `PGT_SYS.PGT_DOMAINS` (e.g. `XLB01 - HPE FIXED INCOME SLB`), reached from
`T_BOX_CONF_BY_BOOK_S.FK_LABEL`. See [box-data-model](../reference/box-data-model.md).

### 2.5 MIS book

Add the new book to the SIGOM screen `BOX - Financial Engine \ Control \ Configuration \ MIS`, for the
corresponding branch, **in the Book tab**, and assign the new instrument book to it.

Then **export the book configuration file with dynamic pk** to insert it into the environments.

**This is the operational how-to for `T_BOX_CONF_BY_BOOK_S`** — the Book tab of the MIS aggregate,
step 11 of the FE config walk
([fe-branch-configuration](../reference/branch-config/fe-branch-configuration.md) §2, "Book"). Two
things follow, and both matter:

> 🔑 **"Export … with dynamic pk" is a direct lead on the FE walk's biggest blocker.** Gate 0d
> ([03-fe-sigom-config-procedure](03-fe-sigom-config-procedure.md), query `Q-G3`) asks how primary keys
> are allocated for the tables the walk writes to, and that question has blocked the agent from
> emitting a single `INSERT`. This sentence suggests the sanctioned path is **configure in SIGOM, then
> export a configuration file carrying a dynamic PK, then import into the target environment** — not a
> hand-written `INSERT` at all. If that is right, the agent's deliverable shape may be wrong for this
> object. Chase this before building SQL generation. `[open-question]` — one sentence in a runbook is
> a lead, not a mechanism; find the exporter and see what it actually emits.

The runbook confirms from the operational side what a BOX FE Developer confirmed functionally: a book
must be **registered per branch in the Book tab** before it is processed. Nothing here contradicts the
"no GBO analogue" finding for this table.

---

## Discrepancies with reverse-engineered docs

The Control-M layer was previously documented by reading the `cib-auki-aukictrlmcntrm` repo. This
runbook is written by the people who operate it. Where they disagree, **neither automatically wins** —
the repo evidence is what *exists*, the runbook is what people *do now*, and one may simply be newer.

| # | Reverse-engineered doc says | This runbook says | Status |
|---|---|---|---|
| 1 | **6 jobs per book** (Deal base/OTC/SQL/OTCSQL + Flow + Market), reconciling to 444 = 74 × 6 | **4 jobs per book** (2 Deal + Flow + Market) | Unresolved. Plausible that OTC flavors apply only to books trading OTC products — but the repo's own arithmetic applies 4 Deal flavors to *all* 74 books, so that reconciliation does not fit cleanly. `[open-question]` |
| 2 | Job names carry a region token (`SCIB` for Europe) or an embedded country letter (LatAm-local) | Job names carry **neither** — `PAUKIDD<ABBREV>001D` | Unresolved. Possibly a newer convention, possibly a third job family. `[open-question]` |
| 3 | Jobs launch `APILaunchProcessAirflow.sh` → Airflow DAG `auki_bo_sql_generic`; `RunAs uappproauki`, host pool `AIRFLOW_PRO`, `SubApplication AUKI_PRO` | Jobs launch `Ext_complex_lambda_auki_…_sp3.sh`; `RUN AS ueext_complex`, host `PRO-HDP-COR-BTH-OHE`, group `EXT_COMPLEX` | Looks like **two different job families**, not a contradiction — but which one a new NY book needs is unanswered. `[open-question]` |
| 4 | `<BOOK-ABBREV>` scheme unknown, no lookup table found | `<BOOK-ABBREV>` is *"algo identificativo del libro"* — chosen by hand from the book name | **Effectively resolved**: it is a convention, not a lookup. Correction applied in [control-m-batch-layer](../reference/job-chains/control-m-batch-layer.md) §4 |
| 5 | `status_vr`/`Native_validation_Status = BOValidated` described as boilerplate | Same value, same template-default position | **Consistent** — and both are wrong for a branch still on GBO, per the correction already recorded |

## What this runbook does not cover

- **Creating the book itself** — this procedure assumes the book exists as a concept and has a name,
  a branch and instruments. Where a book is first created, and by whom, is not described.
- **A branch that does not already exist** in Control-M, `db.conf` or the batch package constants. The
  `CST_PK_BRANC_MAD` observation in §2.3 suggests a new branch is a prerequisite with its own
  (code-level) work, not something this runbook handles.
- **Tier 2 / NY specifics.** Every concrete value here is Tier 1 (`ES`/`Mx3EU`/Madrid, with LB
  appearing only in the DUMMY jobs). Treat the whole document as a Tier 1 record until a Tier 2 book
  has actually been added.
- **Rollback.** Nothing describes undoing any of this.

## Sources

Internal Confluence runbook, imported 2026-09-15, partly Spanish
`[stated: team runbook, not independently verified]`. A named individual referenced in the original as
the Data-Lake contact has been replaced with "the Data-Lake team" per this repo's no-real-names rule.
Cross-referenced against [control-m-batch-layer](../reference/job-chains/control-m-batch-layer.md),
[fe-raw-data-stage](../reference/fe-raw-data-stage.md),
[fe-branch-configuration](../reference/branch-config/fe-branch-configuration.md),
[box-data-model](../reference/box-data-model.md).
