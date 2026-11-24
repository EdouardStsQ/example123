# Kickoff — NY_SCH: the GBUX file (NY UME Extendida, sent to Equation) in BOX

Run [`gap-run.md`](gap-run.md), then [`build.md`](build.md), then [`parallel-run.md`](parallel-run.md), with these
parameters `[operator, 2026-11-18]`:

| Parameter | Value |
|---|---|
| Branch | `NY_SCH` (GBO branch `20007.4`) |
| Report | `gbux` — report folder `runs/NY_SCH/branch/reports/gbux/` |
| Environment | `tier2-preparalelo` (IGBOUSIB) — `python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env preparalelo --area reports --name gbux` |
| BOX account | **ask**: run R-P1 with `BOX_ADMIN` and with `BOX_ACC` and use the one that reaches `BOX_FE`, `BOX_ACC`, `BOX_TRD` and `PGT_PRG` / `PGT_STC` / `PGT_MRK` / `PGT_SYS`; if none reaches them all, report which object each misses — no workaround |
| GBO account | `pgtadmin` |
| GBO wrapper schema | `PGT_NY` (`branch-registry.csv`) — `T_PGT_TOPICS_RR` is `PGT_NY.T_PGT_TOPICS_RR` |
| First slice (D2 default) | deposits (`2.4`, BOX `MM`) and IRS (`20092.4`, BOX `IR`); comparison filter `--only 4=DEPOSIT,SWAP` |
| R-B1 parameters | `T_BOX_MMFINANCST_S`, `T_BOX_IRFINANCST_S`; `V_BOX_ENGMMDATAMIS_S`, `V_BOX_ENGIRDATAMIS_S`; `T_BOX_MMDATADEAL_S`, `T_BOX_IRDATADEAL_S` |
| R-G0 / R-G2 parameters (R-G2 only if D1 changes: by default BOX prints GBO's id, ADR 0029) | `T_PGT_MMFINANCST_S`, `T_PGT_IRFINANCST_S`; `V_PGT_ENGMMDATAMIS_S`, `V_PGT_ENGIRCMDATAMIS_S`; `T_PGT_MMDATAMIS_S`, `T_PGT_IRDATAMIS_S`; branch `20007.4` |
| R-G1b topics | `77.4`, `78.4` (the deposit's opposite record) |
| R-B5 event types | `170.4`, `50.4` |
| Dates `[operator, 2026-11-24]` | **25-Sep-2026, IRS** — the only date BOX holds NY trades in IGBOUSIB (the parallel test's); GBO's file: PROD's `GBUX260925` (IGBOUSIB's GBO data is PROD's up to 12-Nov-2026), asked from the BOX lead. Deposits wait for a BOX NY run (candidate 12-Nov-2026 with PROD's `GBUX261112`) — until then `--only 4=SWAP` |
| The GBO file | **ask**: where the operator gets GBO's `GBUX<YYMMDD>` for those dates in IGBOUSIB (the specification's directory is IGB0US's: `CRONCONCILIANYSALDOS` → `/amdrny_NAS/dat/Cron/ConciliaNY/Saldos`; event grouping `2501.35`) |
| Example file received | `GBUX261120` — **PROD**'s file for 20-Nov-2026, from the BOX lead `[operator, 2026-11-24]`; 750k+ records (the PRE sample `GBUX250318` had 262,923). Kept in `runs/NY_SCH/branch/reports/gbux/local/` (git-ignored), never sent to the agent. IGBOUSIB's GBO and BOX both stop at 12-Nov-2026: **the layout and distribution reference only**, never compared. First use, before any query: the gap run's `check_fixed_width.py` on it (`05-compare/20261120-gbo-check.md`) |
| Efficiency `[BOX lead, 2026-11-24]` | "the report is a mess and slow": same content, efficient build (hard rule 11). GBO's per-row work known from the specification (`gbo-spec/`, the lineage matrix): the `c_operaciones` cursor; per deal `P_STATUS_OP` (FINANCST tables + MTM views), `F_EARLYTERMINATOR_OP` (date-dependency tables), `PKG_PGTGENERAL.P_GETMATURITYDATE`; per record `PKG_GLTAGENERAL.P_GETACCOUNTCODE` / `PKG_ACCTGENERAL.F_GETACCTNO`; per NDF / swap ND the fixing cursors; per deposit opposite line the cash-flow check and the workday calendar — the gap report's *GBO implementation* section starts from this list |
| GBO baseline | **ask**: the elapsed time of event `4621.35` (`P_GENUME_EXT_FILE_OP`) for 20-Nov-2026 — the batch log or the scheduler's run time; `unknown` if nobody has it |

**What is already known — do not ask again:** the specification's analysis is in `gbo-spec/` (the GBO US team,
received 2026-11-18); the decisions and their defaults are in `decisions.csv` (D1–D8) and the GBO behaviours in
`deviations.csv` (DV1–DV13) — all defaults until the BOX lead answers. NY IBF (`20006.4`) is not onboarded in BOX,
BOX FX has no trades yet, CDS is out of NY's BOX scope (2026-10-27): left out by the filter (D2). The NY ACC
configuration in IGBOUSIB is the one the BOX ACC expert is reviewing — clash groups and empty-condition properties
can pick other accounts than GBO; in the comparison they are named with their portfolio property, not fixed here.
