---
name: box-fe-parallel-test
description: Prepares and follows the BOX FE parallel test of a new branch - GBO and BOX running side by side in the PRE Paralelo environment over a period, the whole branch reconciled every day with the breaks followed from day to day until sign-off. Use when the operator wants to run or follow the parallel (full) test.
---

# BOX FE parallel test (full test)

`[operator, 2026-10-09]` The third of three tests of a new branch's BOX FE (after the
[technical test](../box-fe-technical-test/SKILL.md) and the [Y test](../box-fe-y-test/SKILL.md)): **the whole branch,
every day of a period, GBO and BOX give the same results**. Basics only, to be completed after the Y test
`[operator, 2026-10-09]`. Same mechanics as the Y test - the same script and field map - on the whole population
(no trade list: the branch's filter per side) and several dates, with the breaks followed day to day.

**Script:** `scripts/fe_reconcile.py` (folder: `scripts/new_run.py`). **Where to look:** [`box-fe-test-lookups.md`](../../docs/reference/box-fe-test-lookups.md) - a break that is a trade
missing in BOX is traced and diagnosed as in the Y test. **Reference:**
[`gbo-box-fe-field-map.csv`](../../docs/reference/gbo-box-fe-field-map.csv).

## The rules

| Rule | Source |
|---|---|
| NY_SCH: BOX in the PRE Paralelo environment **IGBOUSIB**; the GBO environment and the period are asked | operator, 2026-10-09 |
| The products the operator chooses (`products`); the population is the branch's, by a filter per side (`gbo_filter`, `box_filter`, also per product), never a trade list | basics / operator, 2026-10-13 |
| Each date's CSVs in `01-evidence/<YYYY-MM-DD>/` (`gbo-<product>-<area>.csv`, `box-<product>-<area>.csv`); `compare` reconciles every date present | basics |
| `04-breaks.csv`: each break (key, area, field) with first / last date seen, days, state `NEW` (today only), `OPEN` (still there), `RESOLVED` (gone) | basics |
| **The trade key is the GBO `DEAL_ID`**: BOX's `DEAL_ID` through the AUKI migration crosswalk `BOX_MIG.T_BOX_AUKI_MIG_DEALS_S` (`FK_AUKI_ID` → `REGISTRY`) for the branch (input `gbo_branch`); never `FRONT_ID` (it differs between the systems). `sql/05-crosswalk-checks.sql` runs first - a GBO deal with no crosswalk row can only be ONLY_GBO, and that is reported as such, not as a BOX defect | operator, 2026-11-24 - [ADR 0029](../../docs/decisions/0029-gbo-box-trade-key-auki-migration-crosswalk.md) |
| `03-results.md` counts duplicate keys per side (a key twice in one CSV: only its first row compared) - a duplicate means the key misses a column (e.g. the leg) | ADR 0029 |
| **The standard assessment** [ADR 0030]: the pack's files are run once per date as they are - no improvised query; `fe_assess.py` builds the CLEAN set (same legs, deal data, current interest flow, inputs), compares it and classes every difference by [`fe-recon-rules.csv`](../../docs/reference/fe-recon-rules.csv); deals left out are missing data, counted per reason, never mixed with calculation differences | operator, 2026-11-25 |
| Only `DIFF - unexplained` needs work: explain it **from the code first** - BOX in `cib-boxfin-dbboxfe` (read-only: the package that writes the column, file:line), GBO on the data (its engine bodies are not readable); a confirmed explanation is proposed as a rule (a PR to the rules file, with its source) | operator, 2026-11-25 |
| Trade-level output (the xlsx, details, CSV exports) stays in the run's git-ignored `local/` or outside the repo; the repo gets `03-assessment.md` (counts) | ADR 0028 / 0030 |
| Sign-off criteria (no `OPEN` break? a threshold? days in a row?) - asked, OPEN until the operator decides | OPEN |

## How to run

```bash
python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env preparalelo --area tests/parallel --name depos
cp runs/NY_SCH/tier2-preparalelo/tests/parallel/parallel-test-inputs.NY_SCH.json <run>/parallel-test-inputs.json
python3 scripts/fe_reconcile.py pack <run>/          # inputs: products, dates, gbo_branch, raw_source
# the operator runs, per date, exporting each result as CSV with header (Export, not the grid - 5,000-row limit):
#   sql/05-crosswalk-checks.sql   BOX_ADMIN  counts (one id each way; how many deals map)  -> 01-evidence/05-*.csv
#   sql/10-GBO-<p>-financial.sql  pgtadmin   -> 01-evidence/<date>/gbo-<p>-financial.csv
#   sql/20-BOX-<p>-financial.sql  BOX_ADMIN  -> 01-evidence/<date>/box-<p>-financial.csv
#   sql/10-GBO-<p>-deal.sql       pgtadmin   -> 01-evidence/<date>/gbo-<p>-deal.csv
#   sql/20-BOX-<p>-deal.sql       BOX_ADMIN  -> 01-evidence/<date>/box-<p>-deal.csv
#   sql/12-BOX-flows-<p>.sql      BOX_ADMIN  -> 01-evidence/<date>/box-<p>-flows.csv
#   sql/06-BOX-import-funnel-<p>.sql BOX_ADMIN  counts - diagnostic for missing data
python3 scripts/fe_assess.py <run>/                   # 03-assessment.md (counts) + local/<date>-<p>-assessment.xlsx
python3 scripts/fe_reconcile.py compare <run>/        # optional: every key / field, 04-breaks.csv day to day
```

**The answer to the operator** (from `03-assessment.md` and the xlsx): the funnel; the headline (full match on the
clean set, and leaving aside the functional differences); the Issues table with one example per type; then only the
`DIFF - unexplained` rows, each explained from the code or handed to its owner with the example.

## Failure modes

| Symptom | Code | Meaning |
|---|---|---|
| refused before writing | `inputs-missing` | no `parallel-test-inputs.json` in the run folder |
| refused before writing | `run-frozen` | the period is closed - a new version |
| refused | `map-missing` | the field map file is not where the inputs say |
| `compare` refused | `evidence-missing` | no `01-evidence/<YYYY-MM-DD>/` folder |
| `compare` refused | `key-missing` | the key column of the map is not in a CSV (or still OPEN) |

## Never

- Run anything on a database. Close a break without its explanation in `03-results.md`.

## Eval cases

[`evals/cases/box-fe-parallel-test.md`](../../evals/cases/box-fe-parallel-test.md).
