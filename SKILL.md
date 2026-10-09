---
name: box-fe-technical-test
description: Prepares and records the BOX FE technical test of one instrument in a DEV environment - the PROD extracts of the test trades (RAW deal / flow / market data, QR prices), the DEV static-data check by alias, the DEV-only bypass of the online flow, the run card of the event groups in order, the checks and the results. Use when the operator wants to run or follow the FE technical test.
---

# BOX FE technical test

`[operator, 2026-10-09]` The first of three tests of a new branch's BOX FE (then the "Y" test GBO vs BOX, then the
parallel test): **the FE configuration (SIGOM) and the FE jobs work end to end in a DEV environment** for a couple of
trades. No agent touches a database: the skill writes the queries, the scripts and the run card; the operator runs
them and returns each output as a CSV; the skill records the result. A value it does not have is an **OPEN point**
in `01-plan.md`, asked to the operator - never guessed.

**Script:** `scripts/fe_tech_test.py` (folder: `scripts/new_run.py`). **Reference:**
[`box-fe-static-aliases.csv`](../../docs/reference/box-fe-static-aliases.csv) (the aliases `c_Deal` /
`p_Import_Deal_Data` resolve).

## The rules

| Rule | Source |
|---|---|
| The RAW tables (`BOX_FE.T_BOX_RAW_DEAL_DATA_S`, `…_FLOW_DATA_S`, `…_MARKET_DATA_S`) are loaded in PROD; the test trades' rows are extracted there as INSERTs and run in DEV - unless they are already in DEV (`raw_in_dev: true`, NY_SCH DGBOUS 24/09/2026): then only a presence check. The market data rows are the trades' (`FRONT_ID`) unless `raw_market_data_filter` says otherwise | operator, 2026-10-09 |
| The test date is set first - every query and the Run Batch use it | operator |
| Static data is matched by **ALIASCODE for one source**: an alias of the RAW value under the source `c_Deal` uses (folder: GER 279.4); an alias under another source does not count | operator (Folder Alias tab query), c_Deal r0.0.49 |
| The online flow (Murex / Camunda → BOX API → `BOX_TRD.T_BOX_DEAL_S`) is bypassed **in DEV only**: before 2629.65 the join of `p_Import_Deal_Data` to `BOX_TRD.T_BOX_DEAL_S` becomes a LEFT join; before the instrument's insert group `FK_PORTPROP` and `REFERENCE_ACCOUNTING` are set on `T_BOX_DEAL_DATA_S` | operator, 2026-10-09 |
| `FK_PORTPROP` is the PK of a portfolio property (`BOX_ACC.T_BOX_ACCT_PORT_PROP_S`, SIGOM Portfolio Properties): `FK_BRANCH` = the branch **group** (`PGT_STC.T_PGT_BRANCH_GROUP_S`; NY_SCH 21447.4), not the branch; `FK_INSTRUMENT` = the sub-product (`PGT_SYS.T_PGT_SUB_PRODUCT_S`: depos 2.4, IRS 20092.4); `DESCRIPTION` = Trading / Hedging + counterparty sector; `STATUS` Valid. The candidates are those of the target's group and instrument; the one matching the trade's `FK_STRATEGY` is preferred (for FE any Valid one works). None in DEV: an OPEN point (create it in DEV, or the operator says which to use) | operator's Tier 1 queries, 2026-10-09 |
| `REFERENCE_ACCOUNTING`: the Tier 1 London (SLB) trades carry their own `DEAL_ID`, the Madrid trades an external contract reference - asked; the answer `DEAL_ID` sets each trade's own | operator's Tier 1 queries, 2026-10-09 |
| `p_Import_Deal_Data` (read): MERGE into `BOX_FE.T_BOX_DEAL_DATA_S` on `FRONT_ID` + `SOURCESYSTEM` + `DIRECTION` (one row per leg); `DEAL_ID` = `FRONT_ID` `.` the SOURCESYSTEM alias's `FK_PARENT` (`.0` = alias missing); filters: process date, `UPPER(BOOK)` = the label's book, `DATA_EXECUTION_TYPE` = `BOOK`, maturity + days matured + 5 ≥ date - no status filter. The bypass leaves NULL every column taken from `BOX_TRD.T_BOX_DEAL_S` (`FK_PORTPROP`, `REFERENCE_ACCOUNTING`, `FK_INSTRUMTYPE`, `FK_TRDSUBTYPE`, `FK_MICROHEDGE`, `FK_STRATEGY`, `FK_DEALTREAT`, `FK_ACCTDOC`, `UTI`, `NOMINAL_SETTLEMENT`, `COMPOUND_FREQ`): `sql/50` sets the two always and `bypass.extra_fields` on request; a re-run of 2629.65 resets them - `sql/50` again | operator (package screenshots, Tier 1 query), 2026-10-09 |
| NY_SCH's DEV database: **DGBOUS** | operator, 2026-10-09 |
| QR prices: `PGT_MRK.T_PGT_QUOTE_PRICES_S` (PK, FK_OWNER_OBJ, FK_PARENT, FK_EXTENSION, FK_QUOTETYPE, FK_QUOTESERIE, PUBLISHDATE, EXPIREDATE, SETTLEDATE, MATURITYDATE, PUBLISHPRICE, DAILYMULTFACTOR, ACUMMULTFACTOR, GUID, REPLICIND, DIRTYPRICE) - the date column is asked (both counted until given); an insert refused in DEV (ORA-00001 / ORA-02291) is recorded, never forced | operator, 2026-10-09 |
| The join is checked first: already LEFT in DEV (`bypass.join: already-left`, NY_SCH DGBOUS) → nothing to deploy or restore. Otherwise the patch is made from the package **as deployed in DEV** (exported), with its rollback, **for the operator to run** - no agent touches a database; `cib-boxfin-dbboxfe` stays read-only | hard rule / operator, 2026-10-09 |
| The portfolio property is found by queries (`sql/50`: the group + sub-product's Valid ones; what the group has; the reference group's shape to create in DEV); the operator returns the CSV, the agent proposes the PK | operator, 2026-10-09 |
| The event groups run from SIGOM **GBO > SYS > Process > Batch > Run Batch**, in the Financial Process order; the instrument's insert group at step 7 (deposits: 2631.65 Insert BOX MM Deal Data) | operator, 2026-10-09 |
| The scheduling monitor (2935.65) must have filled the branch process calendar (`BOX_FE.T_BOX_BRPROCCAL_S`: `FK_BRANCH` = the branch PK, `DATETOPROCESS`) for the test date | BOX job expert / operator, 2026-10-09 |

## How to run

```bash
python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env dev --area tests/technical --name depos
# the branch's inputs when they exist (NY_SCH: DGBOUS, 24/09/2026, the 2 ALCO trades), else the template:
cp runs/NY_SCH/tier2-dev/tests/technical/tech-test-inputs.NY_SCH.json <run>/tech-test-inputs.json
#   cp skills/box-fe-technical-test/tech-test-inputs.example.json <run>/tech-test-inputs.json
python3 scripts/fe_tech_test.py <run>/
```

Re-run the script after each answer: it rewrites the plan, the run card and the SQL (never `03-results.md` once it
exists). A frozen run (`new_run.py --freeze`) is refused - a new attempt is a new version.

## Steps

1. **Ask, one at a time:** the DEV environment, the test date, the instrument, the 2 trades (FRONT_ID and label - e.g.
   one loan and one deposit, different currencies), and the box-fe-jobs-agent run of that instrument (its
   `db.conf.proposal` gives the run card's labels and instruments). Write them in `tech-test-inputs.json`.
2. Run the script; show `01-plan.md` and ask its **OPEN points** one at a time (re-run after each).
3. Give the operator the files in the plan's order (PROD first, then DEV). For each, ask for the output as a CSV in
   `01-evidence/`, read it, record the step in `03-results.md` (expected / result / evidence) and say what it means
   - e.g. a `MISSING` alias: which static to create in DEV, for which source, before going on.
4. The run card: one line at a time; after each, the checks of `sql/60-DEV-checks.sql`; a step that fails stops the
   test (record it, with the batch log the operator gives).
5. End: the rollback (`sql/49-…`) and its check; `03-results.md` complete; freeze the run.

## Output - `runs/<BRANCH>/<tier>-<env>/tests/technical/<name>_<YYYYMMDD>_<n>/`

`tech-test-inputs.json`, `01-plan.md` (steps + OPEN), `02-run-card.md`, `sql/10-PROD-raw-extract.sql`,
`sql/20-PROD-quote-prices.sql`, `sql/30-DEV-static-check.sql`, `sql/40-DEV-bypass-join.sql`,
`sql/49-DEV-bypass-rollback.sql`, `sql/50-DEV-accounting-attrs.sql`, `sql/60-DEV-checks.sql`, `01-evidence/`,
`03-results.md`.

## Failure modes

| Symptom | Code | Meaning |
|---|---|---|
| refused before writing | `inputs-missing` | no `tech-test-inputs.json` in the run folder - copy the template |
| refused before writing | `run-frozen` | the run is finished - a new attempt is a new version (`new_run.py`) |
| the patch is not written | `join-not-found` | the DEV export of `PKG_FE_DEAL_CALCULATION` has not exactly one join to `BOX_TRD.T_BOX_DEAL_S` in `p_Import_Deal_Data` - check the export (whole body?) |
| a field `MISSING` in `30-static-check.csv` | - | the static (or its alias for that source) is not in DEV: create it before the run |
| `CHECK` on the folder's branch | - | the folder exists but belongs to another branch |
| `MISSING` on the process calendar | - | 2935.65 has not run for the branch and date: run it first (run card, step 0) |
| `NO PORTPROP` / `OTHER GROUP` / `OTHER INSTRUMENT` / `NOT VALID` (sql/50, query 5) | - | the `FK_PORTPROP` set is not a portfolio property, or not a Valid one of the target's group and the instrument |
| 2629.65 ends in ORA-20001 `Error in procedure p_Import_Deal_data` under the bypass | - | first suspects: `f_GetAdditionalInfo(BO_CODE, 'UTI')` / `f_getCRDataByType('Notional Settle Type', ..)` called with NULL |
| `DEAL_ID` ending `.0` | - | the SOURCESYSTEM alias (1341.4 / 110862.4 / 577.4) is missing in DEV |
| ORA-00001 / ORA-02291 on an insert in DEV | - | the PK / GUID is already used in DEV, or the static it points to is missing - record it, ask |
| the label's book ≠ the RAW `BOOK` | - | `p_Import_Deal_Data` will not select the trade |

## Never

- Run anything on a database, or ask for credentials. Change `cib-boxfin-dbboxfe`. Leave DEV without the rollback.
- Guess a column name the plan marks INFERRED: confirm it with the operator's first output.

## Eval cases

[`evals/cases/box-fe-technical-test.md`](../../evals/cases/box-fe-technical-test.md).
