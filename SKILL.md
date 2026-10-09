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

**Script:** `scripts/fe_reconcile.py` (folder: `scripts/new_run.py`). **Reference:**
[`gbo-box-fe-field-map.csv`](../../docs/reference/gbo-box-fe-field-map.csv).

## The rules

| Rule | Source |
|---|---|
| NY_SCH: BOX in the PRE Paralelo environment **IGBOUSIB**; the GBO environment and the period are asked | operator, 2026-10-09 |
| The population is the branch's, by a filter per side (`gbo_filter`, `box_filter`), never a trade list | basics |
| Each date's CSVs in `01-evidence/<YYYY-MM-DD>/`; `compare` reconciles every date present | basics |
| `04-breaks.csv`: each break (key, area, field) with first / last date seen, days, state `NEW` (today only), `OPEN` (still there), `RESOLVED` (gone) | basics |
| Sign-off criteria (no `OPEN` break? a threshold? days in a row?) - asked, OPEN until the operator decides | OPEN |

## How to run

```bash
python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env preparalelo --area tests/parallel --name depos
cp runs/NY_SCH/tier2-preparalelo/tests/parallel/parallel-test-inputs.NY_SCH.json <run>/parallel-test-inputs.json
python3 scripts/fe_reconcile.py pack <run>/
# every day: the operator returns 01-evidence/<YYYY-MM-DD>/gbo-<area>.csv and box-<area>.csv
python3 scripts/fe_reconcile.py compare <run>/     # 03-recon/, 03-results.md, 04-breaks.csv
python3 scripts/fe_reconcile.py compare <run>/ --date <YYYY-MM-DD>   # one day only
```

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
