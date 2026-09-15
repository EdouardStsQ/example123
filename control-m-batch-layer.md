# BOX — Branch Batch Layer (Control-M / Data-Lake BU loads)

How a branch's back-office data (**deal / flow / market value**) is loaded daily from the **Data Lake**
into AUKI BO, orchestrated by **Control-M**. This is the batch layer of branch onboarding — the
checklist's *"review current Books, for new Books generate config + Control-M jobs to load BU (deal,
flow, market value in Data Lake)"*. Reverse-engineered deterministically from the
`cib-auki-aukictrlmcntrm` repo (2026-08-24). It is the **most template-able** part of a new-branch
setup; see [box-branch-onboarding-checklist](../../process/checklists/branch-onboarding-checklist.md) for where it fits, and [box-branch-config-surface](../branch-config/branch-config-surface.md)
for the BOX_ACC config it feeds.

---

## 1. The repo `[confirmed: repo]`

`cib-auki-aukictrlmcntrm` (Maven `com.santander.scib.auki:control-m`) is the **Control-M
orchestration** ("control room") for AUKI BO.

- `doc/<process>/diaria.json` — authored Control-M job definitions per process/country (`diaria` =
  daily). e.g. `doc/auki migracion/MIG_ES_LB_diariai.json` = the **Madrid (ES) + London (LB)** batch;
  `doc/auki mexico/`, `doc/auki brasil/` = per-country sets.
- `projects/control-m.json` — the **deployable** folder set (the Maven assembly `assembly/zip.xml`
  zips **`projects/**/*.json`** only; `doc/` is the working/reference source).
- Deploy path: `mvn package` → zip → **Gluon/GitHub CI** (`.gluon/ci/properties.env`,
  `.github/workflows/`) → **Control-M server `GCB.GCB-P-D012`**.

---

## 2. The batch model `[confirmed: repo]`

Each `diaria.json` is one Control-M **`SimpleFolder`** (e.g. `JACP-AUKI-MEXICO-100057367`,
`JACP-AUKI-MIG_DIARIO-100057367`) containing **jobs** (`"Type": "Job:Script"`). Every job launches the
**same generic Airflow DAG** — `APILaunchProcessAirflow.sh` → process `auki_bo_sql_generic` — which
pulls from the **Data Lake** into AUKI BO. Job boilerplate is constant: `SubApplication AUKI_PRO`,
`Host/pool AIRFLOW_PRO`, `RunAs uappproauki`, `Application G-GBMSA-P-100057367`, calendar `LVM25Y1`.

### The branch-specific inputs (a per-job JSON payload in `Arguments`)

| Variable | Meaning | Values observed |
|---|---|---|
| `country_code_vr` | branch country (from Data Lake) | `ES`, `LB`, `MX`, `BR` |
| `source_system_vr` | the Murex instance | `Mx3EU` (Europe = ES+LB), `Mx3LT` (LatAm-local) |
| `book_vr` / `book_part` | the trading **book** | ~74 books in ES/LB (see [box-branch-config-surface](../branch-config/branch-config-surface.md)) |
| `pnl_type_vr` · `status_vr`/`status_native_vr` · `sens_description` | EOD · `BOValidated` · "P&L LEG+P&L FX" | boilerplate **for a migrated branch only** — see the correction below |
| `mfamily`/`mgroup` | (OTC variant only) e.g. `CURR`/`OPT` | currency options |

The `Arguments` also carry the target dataset (`AUKI_DEAL_DATA` / `AUKI_FLOW_DATA` /
`AUKI_MARKET_DATA`, `+OTC` for the OTC flavor) and format (`parquet`).

> **Correction — `BOValidated` is not boilerplate for a branch still on GBO** `[stated: BOX Lead, 2026-09-10]`
>
> `BOValidated` is the **AUKI** trade status. The branches this repo reverse-engineered the template
> from (Madrid, SLB) were already migrated, so every job here carries that status and it reads as
> constant. A branch that is still live in **GBO** has its Data-Lake trades under a *different* status.
>
> The consequence is concrete: **running one of these jobs unchanged against such a branch selects no
> rows**, and the failure mode is a silent empty load rather than an error. This matters immediately for
> NY_SCH, where the agreed test approach is to feed RAW from that branch's existing GBO trades in the
> Data Lake (`../fe-raw-data-stage.md`, *Manual RAW feed as a test path*).
>
> Treat `status_vr`/`status_native_vr` as a **parameter to resolve per branch**, not a constant to copy
> from the analogue — the one place in §4's otherwise-safe "pure expansion" method where copying the
> analogue's value is actively wrong. What NY's actual GBO status value is, and whether the fix is a
> parameter override, a separate test job or a direct RAW insert, is not yet decided. `[open-question]`

### Dependencies (the wiring)
- `eventsToWaitFor` — **upstream Data-Lake / Murex-datamart** completion events, e.g.
  `G012014-PDHMT_MX3FXFI_ES_L13_TRD-OK`, `G012014-PDHMT_MRGPNLLEGEOD_048D-OK`. These are the real
  per-branch/per-feed dependencies (the least-templatable part).
- `eventsToAdd` — the job's own completion events `P<job>-OK` + `G010012-P<job>-OK`.

---

## 3. The per-book job template `[confirmed: repo]`

> ⚠️ **Contested by the team's own runbook — read before relying on the counts below.**
> [04-add-book-procedure](../../process/04-add-book-procedure.md) §1.1, written by the people who
> actually create these jobs, specifies **4 jobs per book** (2 Deal + 1 Flow + 1 Market), not the 6
> this section reverse-engineered from the repo. Its job names also carry **no region token** —
> `PAUKIDD<ABBREV>001D`, where this section records `PAUKISCIBDD<ABBREV>001D` for Europe — and its jobs
> launch a different script under a different run-as and host group, which may mean two distinct job
> families coexist. Everything in this section remains accurate *as a reading of the
> `cib-auki-aukictrlmcntrm` repo*; what is unresolved is whether that repo reflects current practice.
> Do not reconcile the two by picking the more convenient number.

The ES/LB folder is **444 jobs = ~74 books × 6 jobs/book**, split **354 ES / 90 LB**. Each book
expands to a fixed set:

| Data type | Jobs per book | Name pattern (Europe) |
|---|---|---|
| **Deal Data (DD)** | 4 flavors: base, `OTC`, `SQL`, `OTCSQL` | `PAUKISCIBDD<BOOK><variant>001D` |
| **Flow Data (FD)** | 1 | `PAUKISCIBFD<BOOK>001D` |
| **Market Data (MD)** | 1 | `PAUKISCIBMD<BOOK>001D` |

Totals reconcile: DD `296` (74×4) + FD `74` + MD `74` = `444`; OTC `148`, SQL `148`.

**Naming convention** `P·AUKI·<region>·<DD|FD|MD>·<BOOK-ABBREV>·<variant>·001D`:
- Europe uses the `SCIB` region token, country carried only in the payload (`PAUKISCIBDDCREBSMAD001D`).
- LatAm-local embeds the country letter in the name (`PAUKIDDMXLFIXINDET001D`).
- `<BOOK-ABBREV>` examples: `CREBSMAD` = CREDIT BS Madrid, `GOVBSMAD` = GOVIES BS Madrid,
  `PRIBOMAD` = PRIMARY BOOK MADRID, `FIXINSLB` = HPE FIXED INCOME SLB, `FIXINDET` = Fixed Income
  Derivatives, `COLMGNT` = Collateral Management.

### Worked example (Madrid, `CREDIT BS Madrid`)
`PAUKISCIBDDCREBSMAD001D` — Deal-Data load, `country=ES`, `source=Mx3EU`, `book_vr="CREDIT BS Madrid"`,
`book_part="CREDITBSMadrid"`, waits on `G012014-PDHMT_MX3FXFI_ES_L13_TRD-OK` +
`…MRGPNLLEGEOD…`. Its OTC sibling `…DDCREBSMADOTC001D` adds `book_part="OTC-CREDITBSMadrid"`,
`mfamily=CURR`, `mgroup=OPT`, dataset `AUKI_DEAL_DATA_OTC`.

---

## 4. Onboarding a new branch (batch layer) `[inferred: structural]`

Deterministic — a **pure expansion** of `(country_code, source_system, [books])` against an analogous
branch's folder:

1. **Identify** the new branch's `country_code` (Data Lake) and `source_system` (Murex instance:
   `Mx3EU` Europe / `Mx3LT` LatAm-local).
2. **Enumerate the books** the branch will run (from Murex / the analogous branch).
3. For each book, **generate the 6 jobs** (DD base/OTC/SQL/OTCSQL + FD + MD) from the template,
   substituting `country/source/book`, the `<BOOK-ABBREV>`, and dataset names — **and resolve
   `status_vr`/`status_native_vr` for this branch rather than copying `BOValidated` from the analogue**
   (see the correction in §2; copying it is wrong for any branch not yet migrated off GBO).
4. **Wire `eventsToWaitFor`** to the branch's real upstream Data-Lake/Murex-datamart feeds — the one
   genuinely non-boilerplate step (learn from the analogue; unknown feeds → `open-question`).
5. Assemble into a `diaria.json` `SimpleFolder`, promote to `projects/`, deploy via CI.

**Automatable?** 🟢 High — everything except the exact upstream event names, the book→abbrev mapping and
the trade-status parameter is boilerplate. The first two are learnable from the analogous branch's
folder; the third is **not** (§2's correction — the analogue's value is wrong for a not-yet-migrated
branch). Genuinely-new feeds are flagged as open-questions.

**The `<BOOK-ABBREV>` scheme — resolved as a convention** `[stated: team runbook, 2026-09-15]`. The
team's own runbook for adding a book ([04-add-book-procedure](../../process/04-add-book-procedure.md)
§1.3) specifies the abbreviation as *"algo identificativo del libro"* — **something that identifies
the book, chosen by the person creating the job**. So it is a hand-made contraction of the book name,
exactly as this section originally guessed: derive it from the analogue, and there is no lookup table
to find because none exists.

> **Retraction of the 2026-09-11 candidate.** A previous revision of this section flagged
> `PGT_SYS.PGT_DOMAINS` as a likely home for the `<BOOK-ABBREV>` list, on the strength of its row
> `XLB01 - HPE FIXED INCOME SLB` matching this section's `FIXINSLB` = "HPE FIXED INCOME SLB" example by
> description. **That hypothesis is now weakened and should not be relied on.** The runbook shows the
> two are different things at different layers: `PGT_DOMAINS` holds the book's **label code and
> description** (`XLB01`, "HPE FIXED INCOME SLB"), which §2.4 of the runbook assigns through the *Label
> Config* SIGOM screen; the Control-M `<BOOK-ABBREV>` (`FIXINSLB`) is a separate, informally-derived
> contraction of that description used only in job names. They correspond because both descend from the
> same book name — not because one is looked up from the other. The description match that prompted the
> hypothesis is explained without the two being the same list. `[stated: team runbook]`

**Remaining open questions:** the exact `eventsToWaitFor` per feed still depend on the branch's
Data-Lake wiring — though the runbook's §1.2 now names the specific source tables each job type waits
on. Three genuine discrepancies between this reverse-engineered document and the team's runbook are
recorded in [04-add-book-procedure](../../process/04-add-book-procedure.md)'s *Discrepancies* section
and summarised below; none is resolved.

**Sources:** `cib-auki-aukictrlmcntrm` repo (cited inline); [box-branch-config-surface](../branch-config/branch-config-surface.md),
[box-overview](../system-overview.md), `box-database-reference`; BOX FE Developer (2026-09-11, via
[fe-branch-configuration.md](../branch-config/fe-branch-configuration.md)); the team's add-a-book
runbook (2026-09-15, [04-add-book-procedure](../../process/04-add-book-procedure.md)) — **the
operational counterpart to this document**, and the place to look first for how these jobs are created
in practice rather than how the repo describes them.
