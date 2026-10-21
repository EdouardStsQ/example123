# SLB (Tier 1) as a reference branch — its BOX ACC chains

What we know about SLB's BOX ACC jobs when `box-acc-jobs-agent` copies them for a new branch. Branch facts only; the
mechanism is in [`box-batch-chain.md`](box-batch-chain.md) (L2, *The ACC chain*), the agent's rules in its
[charter](../../../agents/box-acc-jobs-agent/AGENT.md); SLB's FE side: [`reference-slb-fe.md`](reference-slb-fe.md).

**Sources:** Devin read-only audit (2026-10-21) of `runs/_reference/tier1-prod/{db,shell}.conf` (Tier 1 **PROD**),
`cib-boxacc-t1mdslbac.json` (ACC folder `JACD-T1MDSLBAC-BOXAC-100068125`) and `cib-boxfin-t1mdslbfe.json`, file:line in
`runs/NY_SCH/tier2-pre/acc-jobs/00-discovery.md`; SLB's MBJ rows (J-R2, 145 rows, operator 2026-10-21 — environment to
record: see *Conf files vs MBJ rows*); the calendar and package queries (operator, 2026-10-21).

## The ACC folder

| | |
|---|---|
| Folder | `JACD-T1MDSLBAC-BOXAC-100068125` (repo `cib-boxacc-t1mdslbac`): `SimpleFolder`, DEV server `GCB.GCB-D-D023`, site standard `SCIB-SSJAC_D_GR_ALMNXTGN_CIB-BOXACC`, `OrderMethod Manual` |
| Every job | `Job:Script`, `SubApplication ACCOUNTING`, `FilePath /appl/gm/scripts`, `FileName` = the job, `RunAs gm`, application `G-GBMSA-D-100068125_Des`, its own DEV host, calendar `LVM25Y1-VS` |
| Descriptors | `cib-auki-aukicnfgsrvc/cib-boxacc-t1mdslbac/{pre,pro}.json` — **not copied** under `runs/_reference/external/` yet |

## The chain per instrument

| Instrument | Branch level | Per book | Branch level after the books |
|---|---|---|---|
| depos (`2.4`) | Initial Accounting `GMBOX0028D01` (old name) | books 01–12 old-named `GMBOX00nnD02` (accounting, `2407.65`) → `D03` (reval, `2408.65`) → `GMBX1LB<bk>D12`; books 13 / 14 / 15 / 99 `GMBX1LB<bk>D07` → `D08` → `D12` | ruler update `GMBOX0028D04` (`2855.65`, old name, waits every book's D12) → `GMBX1LB00D13` |
| IRS (`20092.4`) | Initial Accounting `GMBX3LB00D02` | `D07` (`2735.65`) → `D09` (`2755.65`) | ruler update `GMBX3LB00D03` |
| CCS (`20.4`) | Initial Accounting `GMBX4LB00D02` | `D07` (`3275.65`) → `D08` (MtM / Camara) → `D09` (`3375.65`) | ruler update `GMBX4LB00D03` |
| OTC (`20111.4`) | Initial Accounting `GMBX7LB00D02` | `D07` (`3821.65`) → `D09` (`3801.65`) → `D12` | ruler update `GMBX7LB00D03` → `GMBX7LB00D13` |
| CAP (`20213.4`) | Initial Accounting `GMBX8LB00D02` | `D07` (`3965.65`) → `D09` (`3986.65`) → `D12` | ruler update `GMBX8LB00D03` → `GMBX8LB00D13` |

- **Waits on the FE folder:** each per-book D07 waits for the book's FE `D06`; D08 (depos, CCS) / D09 waits for the FE
  `D04`. The ACC steps of other instruments' families are not waited for.
- **The FE folder waits for ACC:** every book's FE "Import Deal Data And Flow Data" `D02` waits for every Initial
  Accounting job (`GMBOX0028D01-OK`, `GMBX3..9LB00D02-OK`).
- **MIC end of day** (MBJ `MIC_EOD = 1`, no group): `D12` per book (the end-of-day accounting file), `00D13` (the
  end-of-day reval file, the tail — nothing waits for it). **IRS and CCS have none** in the ACC folder (IRS has D12 /
  00D13 MBJ rows with no conf line).
- **Old names:** depos books 01–12 and depos' branch jobs; book `n` → ACC `GMBOX00(26+2n)D02 / D03`, FE shared jobs
  `GMBOX00(25+2n)D02 / D03`.

## How each job runs (Tier 1 PROD conf files)

| Job | Runs from |
|---|---|
| Initial Accounting (`GMBOX0028D01`, `GMBX3..8LB00D02`) | **`db.conf` only** (group `2409.65`) — no `mbjbox.sh` line; `GMBOX0028D01`'s MBJ row is not used. `GMBX9LB00D02` (CDS) has **no conf line at all** (JSON only) |
| Ruler updates (`GMBOX0028D04`, `GMBX<n>LB00D03`) | `db.conf` only |
| Per-book D07 / D08 / D09 / D12, branch D13 | **mixed**: `shell.conf` (`mbjbox.sh`) for depos new-named, OTC, CAP, books 14 / 15 everywhere; **`db.conf` only** for IRS books 01–03 / 05 / 06 / 09 / 11 / 13 / 99, CCS D07 / D09 in most books and **every CCS D08**; both files (the `db.conf` line legacy) for depos books 03–12, IRS 04 / 07 / 08 / 10 / 12, CCS 04 / 07 / 08 / 12 |
| Not in the ACC folder (orphans in `shell.conf`) | `GMBX1LB00D08`, `GMBX7LB00D08` |

A new branch runs **every per-book step through `shell.conf` + an MBJ row** `[operator, 2026-10-21]`.

## The MBJ rows (J-R2, 145 rows)

- Constant on every row: `INSTANZE AUKI`, `FK_OWNER_OBJ 35000182.65`, no parent, no sub-label, monitor file pattern
  `./logs/${job}-instance_${instance}-branch_${branch}-instrument_${instrument}-group_${group}-${date}-${executionNumber}.json`,
  `MIC_FLOW_MODE File`, `MONITOR_TYPES FILE`, `RETURN_DATA 1` (`0` for CFM), recover flags `0`.
- `FK_CALENDAR = 1.21` on every row = **PROCESOS - ESPAÑA** (a processing calendar, in both tiers) — not SLB's branch
  calendar `84.4` (TARGET Settlement Day).
- Per job: workers (8), tasks (1), `WORKERS_BY_EVENTS` (one entry per event of the group), `MIC_SENDER_TYPE`
  (`lastly`, or `none` on books 14 / 15 of IRS / CCS / CFM and some others), `MIC_FILE_TYPE`, `MONITOR_FILE_MAX_DAYS`
  (7 for old depos jobs, 100 otherwise).
- **Defects:** `GMBX1LB12D12` and `GMBX6LB12D12` carry label `XLB14`; `GMBX4LB16D07` carries `XLB10`.
- Rows by instrument: depos 35, IRS 37, CCS 5, CFM 4, FRA 11, OTC 10 (books 10 / 14 / 15), CAP 4 (book 10), CDS 37,
  BRS 2.

## Conf files vs MBJ rows

The two sources disagree (the conf files are Tier 1 PROD; the environment of the J-R2 run is to record):
`shell.conf` `mbjbox.sh` jobs **without** an MBJ row — OTC 28, CAP 33, depos 9, CCS 8; MBJ rows **without** a conf
line — IRS 23 (every D12, several D07 / D09, `00D13`), CCS 1 (`GMBX4LB16D07`). The agent copies the rows of the CSV it is
given; a step with no row of its own takes the same step's row of another book (warned).

## The MBJ engine

`BOX_ACC.PKG_BATCHPROCESS_MBJ` — defined only in `cib-boxacc-dbboxacc` (`08-BOX_ACC`, header r0.0.36, body r0.0.38,
grants r0.0.16 to `BOX_ACC_RD`, `BOX_ACC_WR`, `PGT_PRG`), in Tier 1 (17-JUN-26). A `PGT_PRG.PKG_BATCHPROCESS_MBJ` exists
in both tiers and is not BOX's (no BOX repo defines or calls it).
