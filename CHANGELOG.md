# Changelog

## Unreleased

### 2026-09-16 (later) — instrument scope comes from BOX, not GBO

`[stated: BOX Developer via Edouard, 2026-09-16]` **A narrow but load-bearing correction to
`sigom-box-fe-configs-agent`.**

**What changes:** do not look up which *instruments* are configured for a branch in GBO. A branch is
onboarded in BOX with instruments chosen from **what is already created and live in BOX** — all of
them, or an SME-chosen subset. The branch's GBO instrument configuration is neither the source for
that choice nor a prerequisite for it.

**What does not change, and this is most of it.** The MIS configuration and the Fixing Curve are still
mined from their GBO (`DEVENG.T_PGT_*`) equivalents. The walk's GBO source column is still the input.
`GBO_SOURCE` is still a required input. Correctness still means the branch behaves like its GBO
counterpart. The hard rules, walk order, other gates, outputs and definition of done are untouched.
Jobs, BOX ACC config, Reporting, GL and FDH are all outside this and unaffected.

**Applied as:**

- **Gate 0b / Q-G2 narrowed to level 1, not withdrawn.** Level 1 resolves `FK_MISCONFIG` to the GBO MIS
  header — precisely the thing still being mined — so the gate stays and is load-bearing. Levels 2–3
  (`T_PGT_BRANCH_INST_S`, `T_PGT_BRANCH_INS_CONFIG_S`) are the *branch-instrument* tree and drop out.
- **`PRODUCT_BOOK_SCOPE` re-sourced:** instruments chosen from BOX's live catalogue by a named SME. The
  menu is the BOX FE Processed Instruments catalogue in `box-data-model.md`, which makes that table more
  operationally important than it looked.

**A useful coincidence:** the two levels that drop are exactly the two that were broken. The first live
NY_SCH run returned level 1 only — and levels 2–3 return nothing for **Madrid** too (`bc.PK = 4.21`,
absent from every populated `FK_PARENT` value), which is unambiguously live and fully configured. So
the join `T_PGT_BRANCH_INST_S.FK_PARENT = T_PGT_BRANCH_CONFIG_S.PK` is wrong, and the empty result was
a query defect, not a finding about NY_SCH. **An earlier entry in this session concluded "confirmed
real absence" — that is retracted.** What `FK_PARENT` actually references is recorded as open; it can't
be recovered from constraint metadata because this schema declares no foreign keys at all. Level 1
worked correctly throughout and is the level that stays.

**The generic lesson, now written into the catalogue:** always run a **known-good control** before
recording `CONFIRMED_ABSENT`. Requiring a Madrid run alongside the target branch would have surfaced
the broken join in one round instead of three.

**NY_SCH identity corrected from the live Q-G1 run** `[confirmed: DB Tier 2, 2026-09-16]`: `20007.4` is
the **branch PK**, not the entity as this repo previously recorded. Full row: `FK_ENTITY = 31398.4`,
`FK_CURRENCY = 159.4`, `FK_CALENDAR = 83.4`, `FK_LOCALGROUP = 21447.4` — that localgroup differs from
Madrid's `269.4`, a real input to the branch-group open question. NY_SCH's GBO branch-config row
(`141.35`) and FE/MIS header (`64408.35`, "Configuracion -NY") both exist and resolve.

### 2026-09-17 — filename collision resolved, and the auth-code question closed

**A name clash, caught by Edouard.** `docs/reference/job-chains/box-fe-acc-batch-runtime.md` was carried
as *pending — not yet imported* in eight places across this repo. That marker meant "this doc exists in
Devin's wiki, we haven't pulled it in here yet" — the filename was **reserved for a specific existing
document**. It was subsequently imported into the real repo. This scaffold, which never had it, wrote a
*different* document (built from the team's Confluence batch-process page) into that reserved name. Had
the scaffold been copied over the repo wholesale, Devin's document would have been overwritten.

**Resolution: keep both, under distinct names.** They are two layers of one stack, not duplicates, and
they were written from different evidence — merging them would flatten `[confirmed: repository
configuration]` together with `[stated: team page]`.

- `box-fe-acc-batch-runtime.md` (Devin's, **unchanged, not in this scaffold**) — the **scheduler**
  layer: Control-M job families, subapplications, the `T_BOX_MBJ_PROPERTIES_S` binding, FE→ACC handoff.
  Covers FE *and* ACC.
- **Renamed:** the scaffold's doc → `fe-batch-event-groups.md` — the **inside-Oracle** layer: the nine
  ordered FE event groups and the procedures inside two of them. FE only.
- **The seam between them:** Devin's doc records the dispatcher signature `f_ExecuteGroup(group, branch,
  process-date, instrument, mode, label, sub-label)` and flags the `group` values as an open question.
  The renamed doc is the list of those values. Each is the other's missing half; both now say so.

**Three of the renamed doc's four *Still pending* items are closed by Devin's**, and are recorded as a
reconciliation table rather than silently deleted: the BOX_ACC batch topology, the FE→ACC completion
contract (FE and ACC are separate Oracle batch layers joined through **Control-M events**), and the
shape of per-branch scoping. Only failure/restart behaviour stays open in both.

**🔑 `.21` is Madrid's auth-code — and the PK suffix and the SIGOM status bar are the same number.**
`sigom-reference.md` has carried "*is `Current auth-code` a fixed numeric code per branch (Madrid = 21)?*"
open since the first screen walk. Devin's `T_BOX_MBJ_PROPERTIES_S` extract records Madrid's branch as PK
**`22.21`**, matching the `Current auth-code: 21 - Madrid` shown on six separate Madrid-filtered screens.
His job-to-MBJ table is also the first place all three suffixes appear as typed columns of one row —
branch `22.21`, instrument `20.4`, MBJ group `3375.65`. New `[inferred]` hypothesis recorded: the
auth-code marks **which installation owns the row**, not which environment it lives in, which is the
first reading that explains one row carrying three different suffixes. **NY_SCH's auth-code is now a
Phase 0 question** — a PK written under the wrong one would be invisible to the delete-guard pattern.

**Correction logged, not overwritten.** `sigom-reference.md`'s MBJ Config note concluded the decimal
part was "not a meaningful separate code… a documentation formatting artifact". The European-number
reading was right; that inference was wrong. Both are now on the page, with the error marked.

**Two more structural findings** from putting the two docs side by side, both `[inferred]`: FE event
groups and ACC MBJ groups interleave in one numbering space (so the ACC half of a branch walk may be
minable the same way as FE — worth one query before building two paths); and **CES has an FE Deal Data
group but no ACC accounting**, so "is this product supported?" has to be asked per engine, not once.

**`MIC_FLOW_MODE = On-Line` on a batch job row** — flagged as a lead, not a finding. The online
(CROSS_REF) arrival path still has no document; this is the first place batch configuration and the
online idea touch.

**Five repos upgraded from hearsay to evidence.** `cib-boxfin-t1mdesfe`, `cib-boxfin-t1mdalmfields`,
`cib-boxfin-mdfinancialcheck`, `cib-boxacc-t1mdesac`, `cib-boxacc-t1mdacccheck` were tagged
`[stated: BOX Developer, not yet doc-evidenced]`. Now `[confirmed: repository configuration]`, and the
BOX Developer's descriptions survived contact with the repos. New open question in their place: job
configs name scripts under `/appl/gm/scripts`, and **none of the five repos contains that path**.

### 2026-09-11 — BOX Lead scoping meeting intake (2026-09-10)

- `docs/examples/ny-sch-branch-onboarding.md` restructured around the **six agreed workstreams**
  (Software · SIGOM configs · Jobs · Reporting · GL · FDH) and promoted to the main reference for what's
  done. Repo coverage and work status tracked as separate columns.
- **Testing does not require booking trades in Murex** — a branch live in GBO has its trades in the Data
  Lake and can feed RAW manually. Documented in `fe-raw-data-stage.md` and `system-overview.md`; checklist
  item 2.1 updated to separate "online as a production capability" from "getting test data in".
- **Correction:** `status_vr = BOValidated` was recorded as batch-job boilerplate in
  `control-m-batch-layer.md`. It is the AUKI status — for a branch still on GBO the standard job selects
  no rows. Now flagged as a per-branch parameter, not a constant to copy from the analogue.
- **New:** an existing GBO→BOX **Topics mapping tool** recorded in `sigom-box-acc-configs-agent`; changes
  that agent's topic work from derive-and-propose to apply-and-verify.
- NY_SCH's GL confirmed as **Equation** (same as SLB) in `system-overview.md`; **FDH registered as a
  documentation gap** — it appeared nowhere in the repo before this.
- Scope reconciliation: workstream↔layer mapping added to the master checklist; coverage note added to
  `branch-onboarding-orchestrator` recording that four of six workstreams have no delegate.

### 2026-09-16 (later still) — the FE batch process overview

- **New doc: `docs/reference/job-chains/box-fe-acc-batch-runtime.md`** — a file **eight other documents
  already cited as "pending — not yet imported"**. The **FE half** is now filled: nine event groups in
  order with their PKs, the two before-batch prerequisites, the eight per-product Deal Data inserts, and
  the procedure-by-procedure execution order inside groups `2629.65` and `2630.65`. The **ACC half and
  the FE→ACC barrier remain undocumented**, and the doc says so rather than implying completeness.
- **Upgraded an inference to named facts.** Two turns ago the add-book runbook's `f_ExecuteGroup(<pk>,…)`
  arguments were `[inferred]` to be event-group PKs from two coincidental matches. Seven of the fifteen
  `db.conf` lines can now be named outright, and it's confirmed that one book's block spans **both** the
  FE and ACC batches.
- **Resolved the Fixing Curve two-location trap** (Q-03): `Control > Configuration` is the batch's
  **input**, `Control > Historical Data` is its **output**. Mine Configuration; an empty Historical Data
  on a new branch means the batch hasn't run, not that config is missing.
- **Named the RAW Deal → DATADEAL transformer:** `PKG_FE_DEAL_CALCULATION.p_Import_Deal_Data`, step 1 of
  group `2629.65`. Doesn't close that open question but shortens it to "read this procedure".
- **Placed `p_Import_Flow_Data` in sequence** (step 2 of the same group) and surfaced a third package
  family, `PKG_FE_PROPAGATION_DATA`, which is what sets the `PROPAGATION` column already observed on
  processed Flow.
- ⚠️ **The product-shaped-branch question got materially stronger.** The runtime **Process Calendar**
  schedules against Branch `BOX COMMODITIES` / instrument `COMM_SWAP`, so product-shaped branches are
  **the unit the batch processes**, not a config-screen label. The "harmless dev convention" reading is
  now the weaker one. Still unresolved; still one query away.
- Partially answered an earlier lead: a BOX-side **`Branch - MIS`** exists under `Control \ Historical
  Data` — it is **generated** by event group `2388.65`, which is why it never appeared in the config
  surface.

### 2026-09-16 (later) — the add-a-product runbook

- **New doc: `docs/process/05-add-product-procedure.md`** — the **Product axis**, completing the set
  alongside Book (04) and Branch (the master checklist). Covers BOX API, BOX FE and BOX ACC. Marked
  `DOC IN PROGRESS` at source, so absences are recorded as unwritten rather than as "not required".
- 🔑 **The `.65` PK suffix is an "authcode".** BOX-DEV is the `.65` authcode, and topics/conditions are
  created "as `.65`". Names a convention this corpus has flagged as unexplained for weeks. Recorded with
  what it still doesn't settle — `.65` PKs appear in production-copy extracts too, and branches carry
  both `.21` and `.4`.
- **`CES` identified as Commodity Swap**, closing a BOX-only unknown in the Financial Status product set.
- **"False friend" resolved.** The SIGOM object for the BOX MtM view is named
  `BOX_ENG_Interfaz <product> MIS-MDR` — so BOX's object *is* a MIS-MDR interface like GBO's; only the
  menu label differs. A GBO↔BOX mapping across that row is now justified.
- ⚠️ **Open question raised against the branch-keyed FE model.** BOX-DEV's Accrual Exceptions and
  Allowed Errors screens show `Branch` values like `BOX CCS`, `BOX FX`, `BOX IRS` — **product-shaped,
  not geographic**. Three possible readings recorded, none chosen; flagged in
  `fe-branch-configuration.md` and added to the NY_SCH kickoff prompt as an early check, since it could
  change the shape of the FE walk.
- **New reference table:** the full 18-instrument Processed Instruments catalogue with codes, which
  **refines** the earlier "BOX covers 11 products vs GBO's ~28" framing — BOX recognises more
  instruments than it gives Financial Status screens to.
- **Qualified the universal-engine "zero new PL/SQL" claim** on `acc-add-product-checklist.md`: true for
  ACC accounting logic, but BOX FE demonstrably needs per-product packages and the API needs a function
  change.
- **Flagged:** Days Matured is 2 in BOX-DEV against the documented 30 across Tier 1 — `NUM_DAYS` varies
  by environment and shouldn't be carried as a default.
- Corroborations worth noting: `cinstrument_if → CFM` confirms GBO's odd `IF` code for CFM a second
  time; the MTM import's `CURR`/`OPT` family/group pair matches Control-M's `mfamily`/`mgroup` exactly.

### 2026-09-16 — `T_BOX_CROSS_REF_S` and instrument mappings

- **New doc: `docs/reference/tables/t-box-cross-ref-s.md`** — the **first real per-table deep-dive**,
  filling a folder `docs/README.md` described as "none written yet". Covers the five `MAP_TYPE`s,
  column names `[confirmed: DML]`, the IC→GBO instrument mappings, the five-rows-per-instrument
  checklist, and the `cib-box-cntdblite` script convention.
- **Reframing flagged, not forced.** The repo names a topic category "Online arrival (CROSS_REF)" and
  treats this table as part of the real-time path. The team's page documents its purpose as
  **Integrity Check → GBO Static-Data** translation. Qualified in `topic-index.md` and
  `branch-trading-readiness.md`; the Known-gap note now says Online research has **two** open
  questions where it implied one.
- **Open question resolved:** `fe-raw-data-stage.md` flagged the Pay/Receive → Loan/Borrower
  transformation as unexplained. It is configured here as `Direction` mappings
  (`RECEIVE→BOR`, `PAY→LOA`), instrument-filtered — configuration, not hardcoded logic.
- **Open question resolved:** the add-book runbook's unexplained `f_ExecuteGroup(<pk>, …)` arguments
  are `T_PGT_BR_EVE_S` event-group PKs — two of them (`2735.65`, `2755.65`) appear verbatim in
  `acc-add-product-checklist.md` §4's independently-sourced event-group list.
- 🔑 **A second PK mechanism, contradicting any single answer to gate 0d.** These scripts assign PKs as
  **hand-written literals** in versioned SQL, where the Book tab exports a file with a *dynamic* PK.
  Q-G3 guidance updated: answer the PK question **per table**, not once for the walk.
- **First hard evidence that the `<int>.<int>` PK suffix is load-bearing**: the scripts' delete guard
  `trunc(PK)=sign(PK)*(abs(PK)-.65)` is an assertion that the fractional part is exactly `.65`. What it
  denotes is still open, but it is relied on by code.
- Added the **`BOX_SYS` schema** to the Schema Overview (it was entirely absent) and the
  **`cib-box-cntdblite`** repo to `repo-index.md` under a new *Configuration-as-code repos* section.

### 2026-09-15 (later still) — the add-a-book runbook

- **New doc: `docs/process/04-add-book-procedure.md`** — the team's own Confluence runbook for adding a
  Book, imported and translated from Spanish. Two parts: Data-Lake/Control-M job creation, then BOX FE +
  ACC configuration. This is the repo's **third axis** (branch / product / book) and the first procedure
  written by the people who run it rather than reverse-engineered from code.
- 🔑 **Lead on the FE walk's biggest blocker.** The runbook's MIS-book step says to *"export the book
  configuration file with dynamic pk to insert it into the environments"* — an export/import path, not
  an `INSERT` path. If it generalises, hand-written INSERTs are the wrong deliverable shape for at least
  some config objects. Flagged in the agent charter, Q-G3, and the Book section of
  `fe-branch-configuration.md`; **not** treated as settled.
- **Retraction.** The 2026-09-11 hypothesis that `PGT_SYS.PGT_DOMAINS` might be the missing
  `<BOOK-ABBREV>` lookup table is **withdrawn**. The runbook shows the two live at different layers:
  `PGT_DOMAINS` holds the book's label code + description; the Control-M abbreviation is an informal
  hand-made contraction of that description. They correspond by shared ancestry, not by lookup.
- **`<BOOK-ABBREV>` open question resolved** the other way — it is a convention chosen by the job's
  creator, so there was never a table to find.
- **Three unresolved discrepancies recorded** between `control-m-batch-layer.md` (repo-derived) and the
  runbook (practice): 6 vs 4 jobs per book, region token present vs absent in job names, and two
  apparently different job families. Recorded as contested rather than reconciled by picking one.
- New findings for branch onboarding: the batch package binds the branch as a **compile-time constant**
  (`CST_PK_BRANC_MAD`), suggesting a new branch is a code change here; and the Calypso DUMMY jobs exist
  for ES/LB only, with no US family.

### 2026-09-15 (later) — Folders, and two more GBO↔BOX equivalents

- **New table surfaced: `PGT_STC.T_PGT_FOLDER_S`** (SIGOM `GBO > Static Data > Environment > Config >
  Folders`). It was already listed in `box-data-model.md` as "Folder/portfolio data" with no schema and
  no detail; now has its schema, branch-keying, columns, and a working query. **Folder is branch-keyed**,
  so it is flagged as candidate item **1.6** on the onboarding checklist — `open-question`, not a
  confirmed requirement.
- Recorded the **Folder vs Book** distinction explicitly (portfolio-side vs Data-Lake processing-side);
  both travel with a deal and are easy to conflate.
- **Two more naming-rule confirmations:** `T_BOX_ENGINSTRUMENTS_S` ↔ `T_PGT_ENGINSTRUMENTS_S` and
  `T_BOX_ENGDOM_S` ↔ `T_PGT_ENGDOM_S`.
- **`ENGDOM` backs several codes screens at once**, not one per screen — the same many-screens-one-table
  shape as `T_BOX_DATADEAL_S`. Also recorded that it is **not** `PGT_SYS.PGT_DOMAINS` (module-owned vs
  shared), since both are "domain" tables.
- **`PGT_DOMAINS` now has four confirmed, unrelated uses** (quote type, book label, folder coverage type,
  folder coverage list) across three schemas — two of them on the same folder row. Documented as its own
  section.
- **Flagged for confirmation:** the supplied `ENGDOM` screenshot has its two schemas swapped relative to
  every other confirmed mapping. Recorded in corrected orientation with the reasoning stated, pending one
  word from the developer.
- Partially expanded GBO's `Static Data` tree branch, previously recorded as wholly unexplored.

### 2026-09-15 — Financial Status surfaces, GBO and BOX FE

- **Resolved a standing caveat:** `sigom-reference.md` had confirmed only CCS's Financial Status tables
  by name, with the other ten products derived from a stated pattern. All 11 BOX products are now
  confirmed by name, along with a **correction** — the table code is not always the folder label
  (`C&F`→`CF`, `Depo`→`MM`, `Swap`→`IR`), so the previously written rule would have produced three wrong
  table names.
- **New:** GBO's Financial Status product list and per-product triad (`DATAMIS`/`FINANCST`/`RISK`,
  plus the `MIS-MDR Interface` view) — previously an undocumented folder. Also GBO's `Static MIS Data`
  tables, including the branch-keyed `T_PGT_BRANCH_MIS_S`, flagged as a possible gap in the FE walk.
- **Structural finding:** GBO has one Deal Data table per product; BOX routes all 11 products through the
  single shared `T_BOX_DATADEAL_S` — a second, independent confirmation of what `fe-raw-data-stage.md`
  had concluded from row sampling alone.
- **Trap recorded:** `V_*_ENG<CODE>DATAMIS_S` is labelled *MIS-MDR Interface* in GBO but *MtM Data* in
  BOX. Same naming convention, different stated role.
- **Scope-qualified the GBO↔BOX FE naming rule** in `fe-branch-configuration.md`: confirmed for the
  configuration surface, does not generalise to Financial Status data tables.
- **Product-set divergence** (BOX 11 vs GBO ~28, with FX and OTC consolidated and a dozen GBO products
  having no BOX counterpart) recorded as a hard constraint on `PRODUCT_BOOK_SCOPE` in the NY_SCH record.
- **Flagged, not reconciled:** `box-data-model.md`'s existing `T_BOX_IRDATADEAL_S` / `T_BOX_MMDATADEAL_S`
  rows appear to contradict the shared-DATADEAL finding. Needs a query, not a judgment call.

### Earlier

- Repo scaffold created: docs/skills/agents/evals structure.
