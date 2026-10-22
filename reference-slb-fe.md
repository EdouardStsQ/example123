# SLB (Tier 1) as a reference branch — its BOX FE chains

What we know about SLB's BOX FE jobs when `box-fe-jobs-agent` copies them for a new branch. Branch facts only; the
mechanisms are in [`box-batch-chain.md`](box-batch-chain.md), the agent's rules in its
[charter](../../../agents/box-fe-jobs-agent/AGENT.md). Moved here from the charter on 2026-10-20 (it must stay
branch-agnostic); first used for NY_SCH (`runs/NY_SCH/tier2-pre/fe-jobs/README.md`).

**Sources:** Devin read-only on `cib-boxfin-t1mdslbfe`, `cib-boxacc-t1mdslbac`, `cib-boxfin-t1mdloadprices`,
`cib-boxfin-mdschedulmonitor`, the descriptors `runs/_reference/external/cib-auki-aukicnfgsrvc/cib-boxfin-t1mdslbfe/
{pre,pro}.json` and `runs/_reference/tier1-prod/` (`db.conf`, `shell.conf`, `jobs-inventory.csv`), 2026-10-02 → 10-20;
the BOX job expert's reviews (2026-10-07 / 08 / 09).

## Identity

| | |
|---|---|
| Token | `LB` (jobs `GMBX<n>LB<bk>D<ss>`), labels `XLB<bk>` |
| Branch constant / wrapper | `CST_PK_BRANC_LND` / `PGT_ES` (7-argument `f_ExecuteGroup`, label included) |
| Repos | FE `cib-boxfin-t1mdslbfe`, ACC `cib-boxacc-t1mdslbac`, load prices `cib-boxfin-t1mdloadprices` (Madrid + SLB), scheduling monitor `cib-boxfin-mdschedulmonitor` (folder `JACD-T1MDSCHEDULMONITOR-BOXFE-100068124`, Madrid + SLB) |
| Control-M servers | the folder files in the repos carry **DEV** `GCB.GCB-D-D023`; PRE / PRO set at deployment (the copies used so far: PRE `GCB.GCB-I-D015`, PRO `GCB.GCB-P-D010`, unconfirmed). SLB's BOX waits for SLB GBO's plain events → same server as SLB's GBO |
| Families | `0` shared per book, `1` depos, `3` IRS, `4` CCS, `5` FRA, `6` CFM, `7` OTC, `8` CAP, `9` CDS |

## Books

- 16 books with FE jobs; books **01, 02, 13, 99 ended** for IRS (book 01's IRS jobs ended — never take "the first
  book" as template); CCS / OTC / CAP run in 12–13 books.
- **Books 03–12 carry old names** (`GMBOX0031D02` … `GMBOX0049D03`), recognised by label (`f_getPKByLabel('XLB03')`)
  and group (`GMBOX0031D02` 2629.65 ~ `GMBX0LB15D02`). Books 14 and 15 are new-named; their shared jobs are identical.
- **Defect**: `GMBOX0031D02` (book 03) waits for book 04's `GMBOX0033D01`, not its own D01 — never copied; book 03 is
  not a shared-jobs candidate (open item 4x, NY).
- **Template / shared-jobs book: 15** for every instrument (full chains: OTC D11, CAP / CCS D05 wait
  `GMBX0LB15D02` / `D03`).
- Book `99`: an extra book — whether a new branch gets one is open.

## Branch-level jobs and dependencies

| Job | What | Notes |
|---|---|---|
| `GMBX<n>LB00D01` (depos: old `GMBOX0114D01`, `FromTime 2200`, no waits) | queue job, group `2608.65` | every book's D06 waits for it. Renamed for a target from its new-named siblings (`GMBOX0114D01` ~ `GMBX3LB00D01`) |
| `GMBX<n>LB00D02` (depos: old `GMBOX0028D01`) | Initial Accounting, group `2409.65` | in the ACC folder, run from `db.conf`; every book's D02 waits for the 8 of them (`GMBOX0028D01` + `GMBX3..9LB00D02`) — CDS's `GMBX9LB00D02` is another group ("without attributes") |
| `GMBX<n>LB00D06` | scheduling monitor, local group `39073.21` (a new branch runs the global `2935.65`) | chained by instrument: depos → IRS → CCS → FRA → OTC → CAP; `MonthDays D1`, `FromTime 1300` |
| `GMBOX0026D03` / `D04` | load prices (prerequisite folder) | a new branch's `GMBX0<TT>00D01` / `D02` |
| `GMBOX0043D01` | a branch-level job waiting for one book's Data Lake job | not mapped — asked |

**Descriptor waits** (`cib-auki-aukicnfgsrvc/cib-boxfin-t1mdslbfe`):

| Environment | Every family's queue job waits | Each book's instrument first step (D04) waits |
|---|---|---|
| PRO (`pro.json`) | `GMGB1420D01-OK` (GBO curve-prices check, `F_VERIFYCURRPAIRINDEX`, `CST_CURR_PAIR` = 0) + `GMBOX0026D04-OK` (load prices) | `G010012-PAUKISCIBMD<feed>001D-OK` (Data Lake market data); D01 waits the deal / flow events `…DD<desk>001D`, `…DD<desk>OTC001D`, `…FD<desk>001D` |
| PRE (`pre.json`) | `GMGB1575D01-OK` (Madrid index prices, legacy file `INDEXMAD` via `p_ImportIndexes`) | `IAUKI…` variants |

Market-data feeds per book (PRO): LB01 `MDFIXINSLB`, LB02 `G010014-PAUKIMDHPSTMSLB` (another prefix), LB03 `MDSLBACPM`,
LB04 `MDSLBCRETR`, LB05 `MDSLBFXTRA`, LB06 `MDSLBGDF`, LB07 `MDSLBRATES`, LB08 `MDSLBRAVOL`, LB09 `MDSLBSTMBK`, LB10
`MDSLBSTMTR`, LB11 `MDTREASSLB`, LB12 `MDSLXVA`, LB14 `MDSLBFHBANK`, LB15 `MDSLBSCFBAN`; none for LB13 / LB99.
`GMGB1575D01` → `GMGB1420D01` → `GMGB1420D02` (`db.conf:80`): in PRO the index load is waited for through 1420. SLB also
runs the Data Lake index loads (`GMGB3731D01` `D_INDEXMAD`, `GMGB4655D01` `D_INDEXMAD0200`), not waited for.

## Per product (steps D01–D13, how they run)

Bindings for CCS / OTC / CAP checked one by one (`jobs-inventory.csv`, 2026-10-20); depos / IRS from their chains
("not checked" = present in the chain, binding not listed).

| Step | Depos (GMBX1 / GMBOX) | IRS (GMBX3) | CCS (GMBX4) | OTC (GMBX7) | CAP (GMBX8) |
|---|---|---|---|---|---|
| `00D01` / `00D02` / `00D03` | queue / IA (`GMBOX0114D01`, `GMBOX0028D01`); `GMBOX0028/0030D02/D03` are ACC (books 01 / 02) | queue / IA; `GMBX3LB00D03` is the **ACC** ruler update | `db.conf` | `db.conf` | `db.conf` |
| D04 (2632.65, merge deal + flow data) | per book ×16 | per book ×16 | `db.conf` ×13 | `db.conf` ×12 | `db.conf` ×12 |
| D05 | per book ×16 (2631.65), waits the shared D03 | per book ×16 (2835.65) | `db.conf` ×13 — also waits `GMBX4LB00D08` | `db.conf` ×12 (3803.65) | `db.conf` ×12 (3922.65) |
| D06 | per book | per book | `db.conf` ×14 | `db.conf` ×13 | `db.conf` ×13 |
| D07 | not checked | not checked | **`db.conf` ×11 + MBJ (`shell.conf`) ×6** (books 04 / 07 / 08 / 12 / 14 / 15) | MBJ ×12 | MBJ ×12 |
| D08 | ACC (per book, new-named books) | **conf lines only** (`GMBX3LB00D08` 3055.65, `GMBX3LB<nn>D08` ×15 2875.65): no Control-M job in any repo | `GMBX4LB00D08` FE (clearing house); per-book D08 are **ACC** (MtM / Camara, ACC folder, `db.conf`) | MBJ ×1 (`GMBX7LB00D08`, no Control-M job) | — |
| D09 | — | not checked | **`db.conf` ×11 + MBJ ×6** | MBJ ×12 | MBJ ×12 |
| D10 | ALM fields (3015.65) ×13, waits `GMBX3–8LB<nn>D06` | — | — | — | — |
| D11 | — | — | — | `db.conf` ×12 (3862.65), waits the shared D02 | — |
| D12 | MBJ ×10 (ACC per book) | — | — | MBJ ×12 | MBJ ×12 |
| D13 | `GMBX1LB00D13` | — | — | MBJ ×1 | MBJ ×1 |

- **Shared jobs** wait chains: the instruments' D05 (and OTC D11) wait the shared per-book `D02` / `D03`
  (`GMBOX0027–0049D03` odd, `GMBX0LB13/14/15/99D03`).
- **Cross-instrument waits**: shared `GMBX0LB15D03` waits FRA / OTC `GMBX6/7LB15D11`; depos D10 waits every
  instrument's D06 of the book; monitors chained.
- **CCS clearing house**: `GMBX4LB00D08` runs `f_ExecuteGroup(3557.65, LND, $ODATE, CCS)` — "BOX CCS Load Clearing
  House Data", first event `4397.65` "BOX SWAP Load camara MTM table from GBO file (Swap-Agent)"; it waits the
  SwapAgent loads `GMGB4436D02` / `GMGB4465D02` (`CargaSTM.sh`, ExternalMTM files 91 and 1) and the shared D03s; only
  the 13 per-book CCS D05s wait for it.
- **CDS**: the BOX team deployed `GMBX9ES…` / `GMBX9LB…` jobs (package of 22/09/2026); SLB's CDS Initial Accounting
  is `GMBX9LB00D02`.
- **Corrected 2026-10-21** (ACC audit, [`reference-slb-acc.md`](reference-slb-acc.md)): D07 / D09 / D12 / D13 and
  CCS's per-book D08 are ACC jobs (ACC folder), whatever file they run from.
- `dbconf-only` warnings expected for IRS's D08s and ended jobs (`GMBOX0027/29`, `GMBX1LB13/99`, `GMBOXLB01-12D10`).
  The ACC folder's jobs with a `db.conf` line (Initial Accounting, CCS D08 …) are `dbconf-only-other-folder` when the
  ACC repo is attached (`reference.controlm_other`) — box-acc-jobs-agent's, not a question (2026-10-21).

## Look-alike evidence used

- The wrapper constants resolved per environment (`J-E4b-*.csv`): e.g. SLB passes `3557.65` where a target may pass
  a constant (NY: `CST_PK_FINAC`).
- The Tier 1 Unix packages (e.g. CDS's) are the layout `unix_package.py` follows (`delete_jobsBX.ksh`,
  `add_new_jobs.ksh`, `db_job` template).
- Another branch seen: Mexico's `db.conf` uses the core call `p_ExecuteGroup` — taken as the format, with two
  corrections by the BOX job expert (the branch PK on per-book lines, where Mexico passes NULL; `P_TIME` =
  `to_char(sysdate, …)`, where Mexico repeats the date; its colons built with `CHR(58)` since 2026-10-22: the job runner
  keeps field 4 of a `db.conf` line).
