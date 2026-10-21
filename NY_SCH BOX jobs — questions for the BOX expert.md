# NY\_SCH BOX jobs — questions for the BOX expert

Oct 21, 2026 · @Edouard

## How to use this

20 questions, 8 of them blocking: without those answers NY's ACC jobs cannot be delivered and the FE PRs cannot be opened. Each question gives the context, what the agents did meanwhile, and the exact answer we need (with the input it goes to).

**What was built** (proposals only: nothing deployed, no SQL run):

| Run (automation repo) | Agent | Content | State |
| --- | --- | --- | --- |
| `runs/NY_SCH/tier2-pre/fe-jobs/all_20261021_1` | box-fe-jobs-agent | NY's FE folder + load-prices folder: 355 jobs, 360 `db.conf` lines, 18 books (XNY07 / 09 / 18 / 19 excluded), 5 Initial Accounting jobs handed to the ACC agent; descriptors; Unix package | Frozen; PR #90. No PR on NY's FE repos yet |
| `runs/NY_SCH/tier2-pre/acc-jobs/all_20261021_1` | box-acc-jobs-agent | NY's ACC folder `JACD-T2USNYAC-BOXAC-100068125`: 209 jobs (depos, IRS, OTC, CAP), 201 `shell.conf` lines (`mbjbox.sh`), 4 `db.conf` ruler updates, 201 MBJ rows as 4 SQL files | **TEST - not deliverable**: calendar and PK call are test values, CCS left out. PR #91 |

Each run's `out/report.md` is the summary to start from. **How to answer:** reply under the question (or comment on it), with the value and its source; "don't know, ask X" is a useful answer too.

## Blocking questions

B1–B8 must be answered before a deliverable ACC run and before any PR on NY's Control-M repos.

### B1 — Is "every per-book ACC step through `shell.conf` + an MBJ row" the right pattern for a new branch? (BOX expert)

- **Context:** SLB is mixed. Depos, OTC, CAP and books 14 / 15 run their ACC steps through `mbjbox.sh` (`shell.conf`). IRS books 01–03, 05, 06, 09, 11, 13, 99, CCS D07 / D09 in most books and **every CCS D08** run from `db.conf` only. Depos books 03–12 have both a `db.conf` and a `shell.conf` line.
- **Meanwhile:** we decided (2026-10-21) that NY runs every per-book step (D07 / D08 / D09 / D12) and the MIC step 00D13 through `shell.conf` + one MBJ row. Branch-level ruler updates and Initial Accounting stay in `db.conf` (core call `PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup`).
- **We need:** yes, or the list of steps that must stay in `db.conf` for a new branch (and why). This also answers who builds CCS D07 / D09 (open item 4zi).

### B2 — Which calendar goes in NY's MBJ rows (`FK_CALENDAR`)? (BOX expert, 4zl)

- **Context:** every SLB MBJ row has `FK_CALENDAR = 1.21` (PROCESOS - ESPAÑA), not SLB's branch calendar `84.4` (TARGET). NY's branch calendar is `83.4` (New York). Same values in Tier 1 and Tier 2.
- **Meanwhile:** the test run used `1.21`, marked as a test value.
- **We need:** (a) what MBJ uses this calendar for (e.g. skipping non-processing days); (b) the PK for NY: `1.21`, `83.4`, or another processing calendar (which one).

### B3 — How should a script allocate a PK in `BOX_ACC.T_BOX_MBJ_PROPERTIES_S`? (BOX dev, 4zn)

- **Context:** the SQL never types a PK. It calls a function per row and checks that the PK carries the installation's fraction (Tier 2 PRE auth code 44 → `.44`); otherwise it stops and keeps nothing.
- **Meanwhile:** test value `BOX_ACC.F_GetPK('T_BOX_MBJ_PROPERTIES_S')` (from our notes on SIGOM's `PKG_SIGOM_COV.P_SETHEADER` / `F_GetPK`). Not confirmed: the SQL refuses to run until it is.
- **We need:** the exact call (owner, package, function, arguments); whether `P_SETHEADER` must run first; whether PKs taken in a rehearsal that is rolled back are lost (gaps acceptable?).

### B4 — CCS D08 has no MBJ row anywhere in SLB: what are its values? (BOX expert, 4zq)

- **Context:** SLB's `GMBX4LB<book>D08` (CCS, group `3555.65`, needed by D09) runs from `db.conf` only; SLB's MBJ rows (J-R2) have no row for it in any book. Under B1 NY's D08 needs one.
- **Meanwhile:** CCS was left out of the test run. The agent now accepts `mbj.missing_rows.GMBX4LB15D08`.
- **We need one of:** (a) an SLB CCS job whose row to copy (e.g. `GMBX4LB15D09`); the group stays `3555.65`; (b) the values: `WORKERS`, `TASKS_PER_WORKER`, `WORKERS_BY_EVENTS`, `CONCURRENT_EVENTS`, `RETURN_DATA`, `RECOVER_*`, `MIC_SENDER_TYPE` / `MIC_FILE_TYPE` / `MIC_EOD` / `MIC_FLOW_MODE`, `MONITOR_*`; (c) "keep D08 in `db.conf`" (then B1's answer changes).

### B5 — Control-M server of NY's FE and ACC folders, per environment (BOX team, 4zg)

- **Context:** NY's ACC steps wait for NY's FE events (each book's D07 waits for its FE D06, D08 / D09 for FE D04). We assume the two folders must be on the same server in each environment for those events to be seen.
- **Meanwhile:** DEV `GCB.GCB-D-D023` for both folders. PRO proposed `GCB.GCB-P-D012` (NY GBO's server, where NY's BOX FE sees `GMNY0011D01_PR-OK` / `GMNY0012D01-OK_PR`). PRE unknown: there is no NY PRE GBO folder to read it from.
- **We need:** the server for DEV, PRE and PRO (FE, load prices, ACC); and whether the same-server assumption is right.

### B6 — MBJ engine in Tier 2: package and Unix side (BOX expert / BOX team, 4b)

- **Context:** `BOX_ACC.PKG_BATCHPROCESS_MBJ` (repo `cib-boxacc-dbboxacc`, header r0.0.36, body r0.0.38, grants r0.0.16) is not deployed in Tier 2; only GBO's `PGT_PRG` package of the same name is there. You said you would deploy it. Never checked: `GBOCL_MBJBATCH` + `MBJBOXACC.jar` on Tier 2's Unix server, with `conf/BOX` pointing to Tier 2.
- **Meanwhile:** files built; the report says the jobs cannot run until it is deployed. The verify SQL (V2) checks the package.
- **We need:** the date and version deployed; whether the Unix side is in place (or who installs it).

### B7 — What should `CreatedBy` be in NY's Control-M folders? (BOX team)

- **Context:** the folder JSONs go into NY's repos (`cib-boxfin-t2usnyfe`, `cib-boxfin-t2nyloadprices`, `cib-boxacc-t2usnyac`). The test runs carry a personal user ID. SLB's folders carry developer IDs, which we never copy.
- **We need:** `omit` (no field), a team / service ID, or the deployer's ID.

### B8 — Sign-off of the FE run before the PRs on NY's FE repos (BOX expert, 4y)

- **Context:** run `fe-jobs/all_20261021_1` (depos, IRS, CCS, OTC, CAP in one run, template and shared-jobs book 15). The PR on `cib-boxfin-t2usnyfe` / `cib-boxfin-t2nyloadprices` was declined until you review it.
- **We need:** "OK to open the PRs", or the corrections. After a yes, the agent builds a new run from the same answers (identical files, checked by the regression script) and opens the PRs from a new branch; it never merges.

## FE jobs questions

Run `fe-jobs/all_20261021_1`. These are answered as `DROP-REVIEW` or left out for now: the run works, but each one may change NY's chain.

### F1 — Does NY need the CCS clearing-house job? (BOX expert, 4zh)

- **Context:** SLB's `GMBX4LB00D08` (group `3557.65`, SwapAgent clearing-house MtM) waits for the SwapAgent loads `GMGB4436D02` / `GMGB4465D02`; SLB's 13 CCS D05 jobs wait for it. NY has no SwapAgent: its MtM comes from the Data Lake, per book.
- **Meanwhile:** both SwapAgent waits answered `DROP-REVIEW`.
- **We need:** keep or remove the job for NY. If NY clears CCS: where does BOX take the clearing-house MtM from?

### F2 — The PRE index-load wait `GMGB1575D01-OK` (BOX expert, with the GBO team)

- **Context:** in SLB, a FE job waits for GBO's index load `GMGB1575D01` in PRE. NY's look-alike `GMNY2055D01` exists only as a conf line, with no Control-M job; NY loads Madrid's indices from the Data Lake file.
- **Meanwhile:** `DROP-REVIEW`.
- **We need:** "drop it", or the NY job (and its exact event name) to wait for.

### F3 — SLB conf lines that no Control-M folder schedules (BOX team, 4zj)

- **Context:** IRS `GMBX3LB00D08` (group `3055.65`), `GMBX3LB<book>D08` ×15 (group `2875.65`) and OTC `GMBX7LB00D08` have an executed `db.conf` line, but no job in about 200 Control-M folder repos.
- **Meanwhile:** not copied (reported `dbconf-only`).
- **We need:** unused (to clean up in SLB), or scheduled elsewhere (which folder)? If NY needs them: where in the chain.

### F4 — CDS stays out of NY for now? (BOX expert, 4i)

- **Context:** NY's plan has CDS as `skip` (no branch ran BOX CDS jobs when it was set). Tier 1 now has `GMBX9…` jobs (package of 22/09/2026). SLB's CDS Initial Accounting `GMBX9LB00D02` has a Control-M job but no conf line.
- **Meanwhile:** CDS not built; the FE wait on `GMBX9LB00D02-OK` answered `DROP-REVIEW`.
- **We need:** keep CDS out (and drop that wait), or bring it into scope: then which branch is the reference and how its Initial Accounting runs.

### F5 — Labels with no jobs (BOX expert, 4l b)

- **Context:** XNY07, XNY09, XNY18 and XNY19 keep their SIGOM labels but get no job.
- **We need:** are they harmless for branch-level groups that loop over every label (e.g. the queue group `2608.65`)? Or must they be excluded somewhere else too?

### F6 — Environment values in the descriptors (BOX team, 4m a)

- **Context:** the PRE / PRO descriptors carry `OrderMethod` PRE `ON DEMAND` and PRO `JAC1400` (your 2026-10-08 review). `ControlmServer` is copied from SLB and marked "to confirm" (B5). Still open: NY's load-prices PRO activation date (`StartDate`), and the scheduling monitor's NY folder name and repo.
- **We need:** the `StartDate`, the monitor folder name and repo, and a yes on `OrderMethod`.

## ACC jobs questions

Test run `acc-jobs/all_20261021_1`. These shape NY's chain and MBJ rows. The agent asks them again on every run, so a written answer saves a guess each time.

### A1 — MIC end-of-day steps per instrument (BOX expert, 4zm)

- **Context:** in SLB, depos, OTC and CAP have a per-book D12 (`MIC_EOD = 1`) and a branch 00D13 (MIC end-of-day revaluation, after the ruler update). IRS and CCS have none, although IRS has D12 MBJ rows with no conf line. Every copied row keeps SLB's `MIC_SENDER_TYPE` (`lastly` for depos / OTC / CAP, `none` for IRS / CCS).
- **Meanwhile (test answers):** keep D12 + 00D13 for depos, OTC and CAP; none for IRS and CCS; sender type as SLB.
- **We need, per instrument:** keep or drop D12 + 00D13; should IRS / CCS have them in NY; `MIC_SENDER_TYPE` `lastly` or `none`.

### A2 — SLB's MBJ rows and conf files disagree: which is right? (BOX expert, 4zk)

- **Context:** the MBJ rows (query J-R2) come from Tier 1 PRE; the conf files from Tier 1 PROD. `mbjbox.sh` jobs without a row: OTC 28, CAP 33, depos 9, CCS 8. Rows without a conf line: IRS 23, CCS 1. CAP has rows for book 10 only.
- **Meanwhile:** a job without its own row takes the values of the same step in another book, and the report says so. All 54 CAP rows (D07 / D09 / D12) copy book 10's.
- **We need:** are book 10's CAP values right for every CAP book? Can J-R2 be run in Tier 1 PROD (then we rebuild from PROD's rows)?

### A3 — Groups and parallelism copied from SLB (BOX expert)

- **Context:** each row copies SLB's global event group (e.g. depos D07 `2407.65`; MIC steps have none) and its sizing: `WORKERS` 8, `TASKS_PER_WORKER` 1, `WORKERS_BY_EVENTS` `{1, 8, …}`, monitor `FILE` with 100 days and `./logs/…json`.
- **Meanwhile:** copied as they are; no NY copy of any group (`mbj.group_map` empty).
- **We need:** are SLB's global groups right for NY (no branch copy needed)? Is SLB's sizing right for NY's volumes, or do some steps need other values?

### A4 — Ruler updates: name and form (BOX expert)

- **Context:** each instrument's branch-level ruler update (group `2855.65`, "BOX MBJ Update Ruler Group") waits for every book's last step; 00D13 waits for it. SLB's depos one is old-named (`GMBOX0028D04`); the others are `GMBX<n>LB00D03`.
- **Meanwhile:** depos renamed `GMBX1NY00D03` (the others `GMBX3NY00D03`, `GMBX7NY00D03`, `GMBX8NY00D03`); all four run from `db.conf` as the core call with group `2855.65` and NY's branch PK `20007.4`.
- **We need:** the name is OK; staying in `db.conf` (not MBJ) is OK.

### A5 — NY's ACC folder values and descriptors (BOX team, 4zo / 4zp)

- **Context (DEV):** folder `JACD-T2USNYAC-BOXAC-100068125`, site standard `SCIB-SSJAC_D_GR_ALMNXTGN_CIB-BOXACC` (SLB's ACC value), Application `G-GBMSA-D-100068125_Des`, host `bvmnglapgbod101.nngg.corp` (NY's FE DEV host), run-as `gmny`, `/gmny/scripts`, calendar `CALC-USA`, OrderMethod `Manual`.
- **Meanwhile:** the agent does not write the ACC folder's PRE / PRO descriptors yet (SLB's ACC descriptors are not copied in the repo).
- **We need:** a yes or corrections per value; the PRE and PRO values (host, server, OrderMethod), or SLB's ACC descriptor files (`cib-auki-aukicnfgsrvc/cib-boxacc-t1mdslbac/{pre,pro}.json`) to translate.

### A6 — Running the MBJ SQL (BOX team)

- **Context:** four files, run in order: 1 rehearsal (rolls back), 2 config (commits), 3 verify (read-only), 4 rollback (only to undo 2). Config stops if the auth code is not 44, the calendar is missing, a row already exists or a book label (XNY..) is missing. It currently stops at its first line: the run has test values.
- **We need:** who runs them, in which environment and when (after B2, B3, B6); whether you want to review the rows first (verify query V4 lists label, group, calendar and owner per job).

## Review checklist of the files

All under each run's `out/`.

| File | What to check |
| --- | --- |
| FE `report.md` | Per instrument the template book (15), the `DROP-REVIEW` waits (F1, F2, F4), the decisions to review, the Initial Accounting hand-off |
| FE `JACD-T2USNYFE-BOXFE-100068124.json` | A few books' D01–D11: waits on the same book, the Data Lake waits, no SLB name or host left |
| FE `db.conf.proposal` | Core-call lines: group, branch PK `20007.4` on every line, label per book, time `to_char(sysdate,'RRRR-mm-DD HH24:MI:SS')` |
| FE descriptors (`pre.json` / `pro.json`) | OrderMethod, `ControlmServer`, `StartDate` (F6, B5) |
| ACC `report.md` | The per-instrument table (steps, branch steps, MIC), the rows taken from another book (A2) |
| ACC `JACD-T2USNYAC-BOXAC-100068125.json` | D07 waits for Initial Accounting and the same book's FE D06; D08 / D09 for FE D04; ruler update for every book's last step; 00D13 for the ruler update |
| ACC `shell.conf.proposal` | 201 lines `<JOB>:Y:bin:mbjbox.sh <JOB> $ODATE 0000` |
| ACC `db.conf.proposal` | The 4 ruler updates (A4) |
| ACC `sql/*-mbj-config.sql` | Per row: label by code, group, calendar, MIC fields against SLB's (B2, A1, A3) |
| Both `unix/job_unix.sh` | `delete_jobsBX.ksh` + `add_new_jobs.ksh` lines, one `cp` + `chmod 755` per job |
