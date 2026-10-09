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
| The RAW tables (`BOX_FE.T_BOX_RAW_DEAL_DATA_S`, `…_FLOW_DATA_S`, `…_MARKET_DATA_S`) are loaded only in PROD; the test trades' rows are extracted there as INSERTs and run in DEV | operator, 2026-10-09 |
| The test date is set first - every query and the Run Batch use it | operator |
| Static data is matched by **ALIASCODE for one source**: an alias of the RAW value under the source `c_Deal` uses (folder: GER 279.4); an alias under another source does not count | operator (Folder Alias tab query), c_Deal r0.0.49 |
| The online flow (Murex / Camunda → BOX API → `BOX_TRD.T_BOX_DEAL_S`) is bypassed **in DEV only**: before 2629.65 the join of `p_Import_Deal_Data` to `BOX_TRD.T_BOX_DEAL_S` becomes a LEFT join; before the instrument's insert group `FK_PORTPROP` and `REFERENCE_ACCOUNTING` are set on `T_BOX_DEAL_DATA_S` (any existing value) | operator, 2026-10-09 |
| The package patch is made from the package **as deployed in DEV** (exported), with its rollback; `cib-boxfin-dbboxfe` stays read-only | hard rule |
| The event groups run from SIGOM **GBO > SYS > Process > Batch > Run Batch**, in the Financial Process order; the instrument's insert group at step 7 (deposits: 2631.65 Insert BOX MM Deal Data) | operator, 2026-10-09 |
| The scheduling monitor (2935.65) must have filled the branch process calendar (`BOX_FE.T_BOX_BRPROCCAL_S`) for the test month | BOX job expert, 2026-10-09 |

## How to run

```bash
python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env <dev env> --area tests/technical --name depos
cp skills/box-fe-technical-test/tech-test-inputs.example.json <run>/tech-test-inputs.json   # then fill it
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
| the label's book ≠ the RAW `BOOK` | - | `p_Import_Deal_Data` will not select the trade |

## Never

- Run anything on a database, or ask for credentials. Change `cib-boxfin-dbboxfe`. Leave DEV without the rollback.
- Guess a column name the plan marks INFERRED: confirm it with the operator's first output.

## Eval cases

[`evals/cases/box-fe-technical-test.md`](../../evals/cases/box-fe-technical-test.md).
